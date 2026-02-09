"""Document extraction logic for FNOL documents."""

import re
import json
from typing import Dict, List, Optional, Tuple
from .models import (
    ClaimData,
    ClaimType,
    PolicyInfo,
    IncidentInfo,
    InvolvedParty,
    AssetDetails,
)


class FieldExtractor:
    """Extracts structured fields from unstructured claim documents."""

    # Pattern definitions for field extraction
    # Optimized for both ACORD forms and plain text documents
    PATTERNS = {
        "policy_number": [
            r"POLICY\s+NUMBER\s*\n\s*([A-Z0-9\-]{5,})",  # ACORD format
            r"(?:Policy\s*(?:Number|No\.?|#))\s*[:=]?\s*([A-Z0-9\-]+)",
            r"(?:Policy)\s+([A-Z0-9\-]{6,})",
        ],
        "policyholder_name": [
            r"Name\s+of\s+Policyholder\s*\n\s*([A-Za-z][A-Za-z\s\.\-\']+?)(?:\n)",  # ACORD format - specific label
            r"Name\s+of\s+(?:Insured|POLICYHOLDER)\s*\n\s*([A-Za-z][A-Za-z\s\.\-\']+?)(?:\n)",
            r"(?:Policyholder\s+Name|Insured(?:'s)?\s+Name|Named\s+Insured)\s*[:=]?\s*([A-Za-z\s\.\-\']+?)(?:\n)",
            r"(?:Policyholder|Insured)\s*[:=]?\s*([A-Za-z\s\.\-\']+?)(?:\n|,|;|Address)",
        ],
        "incident_date": [
            r"DATE\s+OF\s+LOSS[^\n]*\n\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|[A-Za-z]+\s+\d{1,2},\s+\d{4})",  # ACORD format - handle both formats
            r"(?:Date\s+of\s+Loss)\s*\n\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            r"(?:Date\s+of\s+(?:Loss|Occurrence|Accident))\s*[:=]?\s*([A-Za-z]+\s+\d{1,2},\s+\d{4})",
            r"(?:Date\s+of\s+(?:Loss|Occurrence|Accident))\s*[:=]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ],
        "incident_time": [
            r"TIME\s+OF\s+LOSS[^\n]*\n\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)",  # ACORD format with full label
            r"(?:Time)\s*\n\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)",
            r"(?:Time\s+of\s+(?:Loss|Occurrence))\s*[:=]?\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)",
        ],
        "incident_location": [
            r"LOCATION\s+OF\s+LOSS[^\n]*STREET:\s*\n?\s*([^\n]{5,}?)(?:\n|CITY)",  # ACORD format
            r"(?:Location\s+of\s+(?:Loss|Accident))\s*[:=]?\s*([^\n]+?)(?:\n)",
            r"(?:Location|Place)\s*[:=]?\s*([^\n]{10,150}?)(?:\n)",
        ],
        "asset_type": [
            r"Year/Make/Model\s*\n\s*([^\n]+?)(?:\n)",  # ACORD format - most specific first
            r"MAKE\s*\n\s*([A-Za-z0-9\s\-]{2,50}?)\s*(?:\n|YEAR)",  # ACORD format with Make label
            r"(?:Type\s+of\s+(?:Property|Asset))\s*[:=]?\s*([A-Za-z\s\d]+?)(?:\n|;|,)",
            r"(?:Property|Asset)\s+(?:Type)\s*[:=]?\s*([A-Za-z\s\-\d]+?)(?:\n|$)",
        ],
        "estimated_damage": [
            r"ESTIMATED\s+DAMAGE\s*\n\s*\$?\s*([\d,\.]+)",  # ACORD format with form label
            r"(?:Estimated\s+Damage\s+Amount)\s*[:=]?\s*\$?\s*([\d,\.]+)",
            r"(?:Estimated|Est\.)\s+(?:Damage|Loss)\s*[:=]?\s*\$?\s*([\d,\.]+)",
            r"Damage\s+Estimate\s*[:=]?\s*\$?\s*([\d,\.]+)",
        ],
        "claim_type": [
            r"(?:Type\s+of\s+Claim)\s*[:=]?\s*([A-Za-z\s]+?)(?:\n)",
            r"(?:Claim\s+Type)\s*[:=]?\s*([A-Za-z\s\-]+?)(?:\n|$)",
        ],
    }

    # Thresholds for confidence scoring
    CONFIDENCE_THRESHOLD = 0.6

    def __init__(self):
        """Initialize the extractor."""
        self.extraction_log = []

    def extract_from_text(self, text: str) -> ClaimData:
        """
        Extract claim information from unstructured text.

        Args:
            text: Raw text from FNOL document

        Returns:
            ClaimData object with extracted fields
        """
        # Normalize text
        normalized_text = self._normalize_text(text)

        claim_data = ClaimData()

        # Extract policy information
        claim_data.policy_info = self._extract_policy_info(normalized_text)

        # Extract incident information
        claim_data.incident_info = self._extract_incident_info(normalized_text)

        # Extract asset details
        claim_data.asset_details = self._extract_asset_details(normalized_text)

        # Extract claim type
        claim_data.claim_type = self._extract_claim_type(normalized_text)

        # Extract parties involved
        claim_data.involved_parties = self._extract_parties(normalized_text)

        # Extract damage estimate
        claim_data.initial_estimate = self._extract_damage_estimate(normalized_text)

        # Extract attachments (by looking for file references)
        claim_data.attachments = self._extract_attachments(normalized_text)

        # Calculate confidence scores
        claim_data.extraction_confidence = self._calculate_confidence_scores(
            claim_data
        )

        return claim_data

    def _normalize_text(self, text: str) -> str:
        """Normalize text for consistent extraction."""
        # Remove extra whitespace but preserve line breaks
        text = re.sub(r"[ \t]+", " ", text)  # Collapse spaces/tabs only
        text = re.sub(r"\n\s+", "\n", text)  # Remove leading whitespace on new lines
        text = re.sub(r"\n{3,}", "\n\n", text)  # Collapse multiple blank lines
        return text

    def _extract_field(
        self, text: str, patterns: List[str]
    ) -> Tuple[Optional[str], float]:
        """
        Extract a field using regex patterns.

        Args:
            text: Input text
            patterns: List of regex patterns to try

        Returns:
            Tuple of (extracted_value, confidence_score)
        """
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Confidence is higher if it matches earlier patterns
                confidence = 0.95
                return value, confidence
        return None, 0.0

    def _extract_policy_info(self, text: str) -> PolicyInfo:
        """Extract policy-related information."""
        info = PolicyInfo()

        policy_number, conf = self._extract_field(text, self.PATTERNS["policy_number"])
        info.policy_number = policy_number

        policyholder, conf = self._extract_field(
            text, self.PATTERNS["policyholder_name"]
        )
        info.policyholder_name = policyholder

        # Try to find effective dates
        effective_date_patterns = [
            r"Policy\s+Effective\s+Date\s*\n\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(?:Effective\s+Date|Policy\s+Effective)\s*[:=]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ]
        effective_date, conf = self._extract_field(text, effective_date_patterns)
        if effective_date:
            info.policy_effective_date = effective_date

        # Try to find expiration dates
        expiration_date_patterns = [
            r"Policy\s+Expiration\s+Date\s*\n\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"(?:Expiration\s+Date|Policy\s+Expir(?:es|ation))\s*[:=]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ]
        expiration_date, conf = self._extract_field(text, expiration_date_patterns)
        if expiration_date:
            info.policy_expiration_date = expiration_date

        return info

    def _extract_incident_info(self, text: str) -> IncidentInfo:
        """Extract incident-related information."""
        info = IncidentInfo()

        incident_date, conf = self._extract_field(text, self.PATTERNS["incident_date"])
        info.incident_date = incident_date

        # More flexible time extraction
        time_patterns = [
            r"(?:Time\s+of\s+(?:Loss|Occurrence))\s*[:=]?\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))",
            r"(?:Time)\s*[:=]?\s*(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm))",
        ]
        incident_time, conf = self._extract_field(text, time_patterns)
        info.incident_time = incident_time

        incident_location, conf = self._extract_field(
            text, self.PATTERNS["incident_location"]
        )
        info.incident_location = incident_location

        # Extract description (longer text block) - multiple variants
        desc_patterns = [
            r"(?:DESCRIPTION\s+OF\s+(?:LOSS|ACCIDENT|INCIDENT))\s*\n\s*([^\n]+(?:\n(?![A-Z\s]+\n)[^\n]+)*)",
            r"(?:Description\s+of\s+(?:Loss|Accident|Incident))\s*[:=]?\s*([^\n]{20,500}?)(?:\n\n|\n[A-Z])",
            r"(?:What\s+happened|Description)\s*[:=]?\s*([^\n]{20,}?)(?:\n|$)",
        ]
        description, conf = self._extract_field(text, desc_patterns)
        info.incident_description = description

        return info

    def _extract_asset_details(self, text: str) -> AssetDetails:
        """Extract asset-related information."""
        details = AssetDetails()

        asset_type, conf = self._extract_field(text, self.PATTERNS["asset_type"])
        details.asset_type = asset_type

        # Extract asset ID/VIN
        vin_patterns = [
            r"Vehicle\s+Identification\s+Number\s+\(VIN\)\s*\n\s*([A-Z0-9]{10,})",  # ACORD format
            r"(?:VIN|Asset\s+ID)\s*\n\s*([A-Z0-9\-]{6,})",  # Simple format with newline
            r"(?:VIN|Asset\s+ID)\s*[:=]?\s*([A-Z0-9\-]{6,})",  # Inline format
        ]
        asset_id, conf = self._extract_field(text, vin_patterns)
        if asset_id:
            details.asset_id = asset_id

        damage_estimate, conf = self._extract_field(
            text, self.PATTERNS["estimated_damage"]
        )
        if damage_estimate:
            try:
                # Clean and convert to float
                clean_value = damage_estimate.replace(",", "").replace("$", "")
                details.estimated_damage = float(clean_value)
            except ValueError:
                pass

        return details

    def _extract_claim_type(self, text: str) -> ClaimType:
        """Classify the claim type."""
        claim_type_str, conf = self._extract_field(text, self.PATTERNS["claim_type"])

        if not claim_type_str:
            # Infer from context
            if "injury" in text.lower() or "bodily" in text.lower():
                return ClaimType.BODILY_INJURY
            elif "theft" in text.lower():
                return ClaimType.THEFT
            elif "collision" in text.lower():
                return ClaimType.COLLISION
            elif "comprehensive" in text.lower():
                return ClaimType.COMPREHENSIVE
            elif "property" in text.lower():
                return ClaimType.PROPERTY_DAMAGE
            return ClaimType.UNKNOWN

        claim_type_lower = claim_type_str.lower()
        if "injury" in claim_type_lower:
            return ClaimType.BODILY_INJURY
        elif "theft" in claim_type_lower:
            return ClaimType.THEFT
        elif "collision" in claim_type_lower:
            return ClaimType.COLLISION
        elif "comprehensive" in claim_type_lower:
            return ClaimType.COMPREHENSIVE
        elif "property" in claim_type_lower or "damage" in claim_type_lower:
            return ClaimType.PROPERTY_DAMAGE
        elif "liability" in claim_type_lower:
            return ClaimType.LIABILITY

        return ClaimType.UNKNOWN

    def _extract_parties(self, text: str) -> List[InvolvedParty]:
        """Extract involved parties information."""
        parties = []

        # Look for claimant information with more specific patterns
        claimant_patterns = [
            r"Claimant\s+Name\s*\n\s*([A-Za-z][A-Za-z\s\.\-\']{2,50}?)(?:\n)",  # ACORD format
            r"(?:Claimant|Named\s+Insured)\s*[:=]\s*([A-Za-z\s\.\-\']+?)(?:\n|,)",
        ]
        claimant, conf = self._extract_field(text, claimant_patterns)
        if claimant:
            party = InvolvedParty(name=claimant, relationship="claimant")
            # Try to find contact info nearby
            phone_pattern = r"Contact\s+Phone\s*\n\s*([\d\-]+)"
            phone_match = re.search(phone_pattern, text, re.IGNORECASE)
            if phone_match:
                party.contact_phone = phone_match.group(1).strip()
            
            email_pattern = r"Contact\s+Email\s*\n\s*([^\n]+)"
            email_match = re.search(email_pattern, text, re.IGNORECASE)
            if email_match:
                party.contact_email = email_match.group(1).strip()
            parties.append(party)

        # Look for third party information
        third_party_patterns = [
            r"Third\s+Party\s+Driver\s+Name\s*\n\s*([A-Za-z][A-Za-z\s\.\-\']{2,50}?)(?:\n)",  # ACORD format
            r"(?:Third\s+Party|Other\s+Driver)\s+Name\s*[:=]?\s*([A-Za-z\s\.\-\']+?)(?:\n)",
        ]
        third_party, conf = self._extract_field(text, third_party_patterns)
        if third_party:
            party = InvolvedParty(name=third_party, relationship="third_party")
            # Try to find third party contact
            third_phone_pattern = r"Third\s+Party\s+(?:Telephone|Phone)\s*\n\s*([\d\-]+)"
            third_phone_match = re.search(third_phone_pattern, text, re.IGNORECASE)
            if third_phone_match:
                party.contact_phone = third_phone_match.group(1).strip()
            parties.append(party)

        return parties

    def _extract_damage_estimate(self, text: str) -> Optional[float]:
        """Extract initial damage estimate."""
        estimate_str, conf = self._extract_field(
            text, self.PATTERNS["estimated_damage"]
        )
        if estimate_str:
            try:
                return float(estimate_str.replace(",", "").replace("$", ""))
            except ValueError:
                pass
        return None

    def _extract_attachments(self, text: str) -> List[str]:
        """Extract attachment references."""
        attachments = []
        # Look for common document references
        patterns = [
            r"ATTACHMENTS\s*\n\s*([^\n]{10,})",  # ACORD format
            r"(?:Attachments?|Exhibits?|Documents?)\s*[:=]?\s*([^\n]{20,}?)(?:\n|$)",
            r"(?:Photos?|Images?|Documents?)\s+(?:attached|included)\s*[:=]?\s*([^\n]{20,}?)(?:\n|$)",
        ]
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                attachment = match.group(1).strip()
                if attachment:
                    # Split comma-separated attachments
                    if "," in attachment:
                        attachments.extend([a.strip() for a in attachment.split(",")])
                    else:
                        attachments.append(attachment)
        return list(set(attachments))  # Remove duplicates

    def _calculate_confidence_scores(self, claim_data: ClaimData) -> Dict[str, float]:
        """Calculate confidence scores for each extracted field."""
        confidence = {}
        mandatory_fields = {
            "policy_number": claim_data.policy_info.policy_number,
            "policyholder_name": claim_data.policy_info.policyholder_name,
            "incident_date": claim_data.incident_info.incident_date,
            "incident_location": claim_data.incident_info.incident_location,
            "incident_description": claim_data.incident_info.incident_description,
            "asset_type": claim_data.asset_details.asset_type,
            "estimated_damage": claim_data.asset_details.estimated_damage,
            "claim_type": claim_data.claim_type != ClaimType.UNKNOWN,
        }

        for field, value in mandatory_fields.items():
            confidence[field] = 0.95 if value else 0.0

        return confidence
