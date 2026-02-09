"""Unit tests for claim processing components."""

import unittest
import json
from pathlib import Path

from src.models import (
    ClaimData,
    ClaimType,
    PolicyInfo,
    IncidentInfo,
    AssetDetails,
    ClaimRoute,
)
from src.extractor import FieldExtractor
from src.router import ClaimRouter
from src.processor import ClaimProcessor


class TestFieldExtractor(unittest.TestCase):
    """Test field extraction functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.extractor = FieldExtractor()

    def test_extract_policy_number(self):
        """Test policy number extraction."""
        text = "Policy Number: POL-2024-001234"
        claim_data = self.extractor.extract_from_text(text)
        self.assertEqual(claim_data.policy_info.policy_number, "POL-2024-001234")

    def test_extract_date(self):
        """Test incident date extraction."""
        text = "Date of Loss: 01/15/2024"
        claim_data = self.extractor.extract_from_text(text)
        self.assertIsNotNone(claim_data.incident_info.incident_date)

    def test_extract_damage_amount(self):
        """Test damage amount extraction."""
        text = "Estimated Damage: $45,000"
        claim_data = self.extractor.extract_from_text(text)
        self.assertEqual(claim_data.asset_details.estimated_damage, 45000.0)

    def test_extract_claim_type_injury(self):
        """Test claim type classification for injury."""
        text = "Claim Type: Bodily Injury. Person sustained serious injuries."
        claim_data = self.extractor.extract_from_text(text)
        self.assertEqual(claim_data.claim_type, ClaimType.BODILY_INJURY)

    def test_extract_claim_type_collision(self):
        """Test claim type classification for collision."""
        text = "Type of Claim: Collision. Vehicle involved in rear-end collision."
        claim_data = self.extractor.extract_from_text(text)
        self.assertEqual(claim_data.claim_type, ClaimType.COLLISION)

    def test_normalize_text(self):
        """Test text normalization."""
        text = "Field    name:   value\n\n  next  field"
        normalized = self.extractor._normalize_text(text)
        self.assertNotIn("\n\n", normalized)
        self.assertNotIn("    ", normalized)


class TestClaimRouter(unittest.TestCase):
    """Test claim routing logic."""

    def setUp(self):
        """Set up test fixtures."""
        self.router = ClaimRouter()

    def test_fast_track_routing_low_damage(self):
        """Test fast-track routing for low damage claims."""
        claim_data = ClaimData(
            policy_info=PolicyInfo(policy_number="POL-001"),
            incident_info=IncidentInfo(incident_date="01/15/2024"),
            asset_details=AssetDetails(estimated_damage=15000),
            claim_type=ClaimType.PROPERTY_DAMAGE,
        )
        routing = self.router.route_claim(claim_data)
        self.assertEqual(routing.recommended_route, ClaimRoute.FAST_TRACK)

    def test_manual_review_missing_fields(self):
        """Test manual review routing when fields are missing."""
        claim_data = ClaimData(
            policy_info=PolicyInfo(),  # Empty policy info
            incident_info=IncidentInfo(incident_date="01/15/2024"),
            asset_details=AssetDetails(estimated_damage=15000),
        )
        routing = self.router.route_claim(claim_data)
        self.assertEqual(routing.recommended_route, ClaimRoute.MANUAL_REVIEW)
        self.assertIn("MISSING_MANDATORY_FIELDS", routing.flags)

    def test_specialist_queue_bodily_injury(self):
        """Test specialist queue routing for bodily injury."""
        claim_data = ClaimData(
            policy_info=PolicyInfo(policy_number="POL-001"),
            incident_info=IncidentInfo(incident_date="01/15/2024"),
            asset_details=AssetDetails(estimated_damage=50000),
            claim_type=ClaimType.BODILY_INJURY,
        )
        routing = self.router.route_claim(claim_data)
        self.assertEqual(routing.recommended_route, ClaimRoute.SPECIALIST_QUEUE)

    def test_investigation_flag_fraud_detection(self):
        """Test fraud detection and investigation flag."""
        claim_data = ClaimData(
            policy_info=PolicyInfo(policy_number="POL-001"),
            incident_info=IncidentInfo(
                incident_date="01/15/2024",
                incident_description="Staged accident with fraud intent",
            ),
            asset_details=AssetDetails(estimated_damage=50000),
        )
        routing = self.router.route_claim(claim_data)
        self.assertIn("FRAUD_FLAG", routing.flags)
        self.assertEqual(routing.recommended_route, ClaimRoute.INVESTIGATION_QUEUE)

    def test_manual_review_high_damage(self):
        """Test manual review for high-damage claims."""
        claim_data = ClaimData(
            policy_info=PolicyInfo(policy_number="POL-001"),
            incident_info=IncidentInfo(incident_date="01/15/2024"),
            asset_details=AssetDetails(estimated_damage=150000),
            claim_type=ClaimType.PROPERTY_DAMAGE,
        )
        routing = self.router.route_claim(claim_data)
        self.assertEqual(routing.recommended_route, ClaimRoute.MANUAL_REVIEW)


class TestClaimProcessor(unittest.TestCase):
    """Test end-to-end claim processing."""

    def setUp(self):
        """Set up test fixtures."""
        self.processor = ClaimProcessor()

    def test_process_sample_claim(self):
        """Test processing of a sample claim document."""
        sample_text = """
        Policy Number: POL-2024-001234
        Policyholder: John Smith
        Date of Loss: 01/15/2024
        Time of Loss: 14:30
        Location: 123 Main St, Springfield, IL
        Description: Vehicle collision at intersection.
        Vehicle Type: 2020 Honda Accord
        VIN: 1HGCV1F30MA123456
        Estimated Damage: $28,500
        Type of Claim: Collision
        Claimant: John Smith
        Phone: 555-0123
        """
        result = self.processor.process_document(sample_text)
        
        self.assertIsNotNone(result.extracted_fields)
        self.assertIsNotNone(result.recommended_route)
        self.assertEqual(result.recommended_route, ClaimRoute.FAST_TRACK.value)

    def test_export_result_json(self):
        """Test exporting result to JSON."""
        sample_text = "Policy Number: POL-001"
        result = self.processor.process_document(sample_text)
        json_output = self.processor.export_result(result, format="json")
        
        # Verify it's valid JSON
        parsed = json.loads(json_output)
        self.assertIn("extractedFields", parsed)
        self.assertIn("recommendedRoute", parsed)

    def test_export_result_dict(self):
        """Test exporting result to dictionary."""
        sample_text = "Policy Number: POL-001"
        result = self.processor.process_document(sample_text)
        dict_output = self.processor.export_result(result, format="dict")
        
        self.assertIsInstance(dict_output, dict)
        self.assertIn("extractedFields", dict_output)


if __name__ == "__main__":
    unittest.main()
