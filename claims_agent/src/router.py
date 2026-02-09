"""Claim routing logic based on extracted information."""

from typing import List, Tuple
from .models import ClaimData, ClaimRoute, RoutingDecision, ClaimType


class ClaimRouter:
    """Routes claims to appropriate processing queues based on analysis."""

    # Damage threshold
    FAST_TRACK_THRESHOLD = 25000  # $25,000

    # Keywords that trigger investigation
    FRAUD_KEYWORDS = ["fraud", "inconsistent", "staged", "suspicious", "fabricated"]
    INVESTIGATION_KEYWORDS = [
        "fraud",
        "inconsistent",
        "staged",
        "suspicious",
        "collision",
        "hit and run",
    ]

    def route_claim(self, claim_data: ClaimData) -> RoutingDecision:
        """
        Determine the optimal routing for a claim.

        Args:
            claim_data: Extracted claim information

        Returns:
            RoutingDecision with recommended route and reasoning
        """
        flags = []
        reasoning_parts = []

        # Check for missing mandatory fields
        missing_fields = self._identify_missing_fields(claim_data)
        if missing_fields:
            flags.append("MISSING_MANDATORY_FIELDS")
            reasoning_parts.append(f"Missing mandatory fields: {', '.join(missing_fields)}")

        # Check for fraud indicators
        fraud_flags = self._check_fraud_indicators(claim_data)
        if fraud_flags:
            flags.extend(fraud_flags)

        # Check claim type
        if claim_data.claim_type == ClaimType.BODILY_INJURY:
            flags.append("SPECIALIZATION_REQUIRED")
            reasoning_parts.append("Bodily injury claims require specialist review")

        # Check damage amount
        damage_route, damage_reasoning = self._route_by_damage(claim_data)
        if damage_reasoning:
            reasoning_parts.append(damage_reasoning)

        # Determine final route
        route, confidence = self._determine_route(claim_data, flags, missing_fields)

        final_reasoning = " | ".join(reasoning_parts) if reasoning_parts else "Standard processing route"

        return RoutingDecision(
            recommended_route=route,
            reasoning=final_reasoning,
            flags=flags,
            confidence_score=confidence,
        )

    def _identify_missing_fields(self, claim_data: ClaimData) -> List[str]:
        """Identify mandatory fields that are missing."""
        missing = []
        mandatory = {
            "policy_number": claim_data.policy_info.policy_number,
            "policyholder_name": claim_data.policy_info.policyholder_name,
            "incident_date": claim_data.incident_info.incident_date,
            "incident_location": claim_data.incident_info.incident_location,
            "incident_description": claim_data.incident_info.incident_description,
            "asset_type": claim_data.asset_details.asset_type,
            "estimated_damage": claim_data.asset_details.estimated_damage,
            "claim_type": claim_data.claim_type != ClaimType.UNKNOWN,
        }

        for field, value in mandatory.items():
            if not value:
                missing.append(field)

        return missing

    def _check_fraud_indicators(self, claim_data: ClaimData) -> List[str]:
        """Check for fraud-related keywords and patterns."""
        flags = []
        
        # Combine all text fields for analysis
        text_to_analyze = " ".join(
            [
                claim_data.incident_info.incident_description or "",
                claim_data.asset_details.damage_description or "",
                claim_data.processing_notes or "",
            ]
        ).lower()

        for keyword in self.INVESTIGATION_KEYWORDS:
            if keyword in text_to_analyze:
                if keyword in self.FRAUD_KEYWORDS:
                    flags.append("FRAUD_FLAG")
                else:
                    flags.append("INVESTIGATION_FLAG")
                break

        return flags

    def _route_by_damage(self, claim_data: ClaimData) -> Tuple[str, str]:
        """Determine routing based on damage amount."""
        if not claim_data.asset_details.estimated_damage:
            return "", ""

        damage = claim_data.asset_details.estimated_damage

        if damage < self.FAST_TRACK_THRESHOLD:
            return ClaimRoute.FAST_TRACK.value, f"Estimated damage (${damage:,.2f}) qualifies for fast-track processing"

        return "", ""

    def _determine_route(
        self, claim_data: ClaimData, flags: List[str], missing_fields: List[str]
    ) -> Tuple[ClaimRoute, float]:
        """
        Determine the final routing decision based on priority order:
        Priority 1 (4.4): Bodily injury → Specialist Queue
        Priority 2 (4.3): Fraud keywords → Investigation Queue
        Priority 3 (4.2): Missing mandatory fields → Manual Review
        Priority 4 (4.1): Damage < $25,000 → Fast-track
        Default: Standard Processing
        """
        confidence = 0.95

        # Priority 1 (Rule 4.4): Bodily injury → Specialist queue
        if claim_data.claim_type == ClaimType.BODILY_INJURY:
            confidence = 0.95
            return ClaimRoute.SPECIALIST_QUEUE, confidence

        # Priority 2 (Rule 4.3): Fraud/Investigation flags → Investigation Flag
        if "FRAUD_FLAG" in flags or "INVESTIGATION_FLAG" in flags:
            confidence = 0.90
            return ClaimRoute.INVESTIGATION_FLAG, confidence

        # Priority 3 (Rule 4.2): Missing mandatory fields → Manual review
        if missing_fields:
            confidence = 0.85
            return ClaimRoute.MANUAL_REVIEW, confidence

        # Priority 4 (Rule 4.1): Damage < $25,000 → Fast-track
        if claim_data.asset_details.estimated_damage:
            damage = claim_data.asset_details.estimated_damage
            if damage < self.FAST_TRACK_THRESHOLD:
                confidence = 0.95
                return ClaimRoute.FAST_TRACK, confidence

        # Default: Standard processing
        confidence = 0.80
        return ClaimRoute.STANDARD_PROCESSING, confidence

    def validate_routing(self, claim_data: ClaimData, route: ClaimRoute) -> bool:
        """Validate that a routing decision is appropriate."""
        # All mandatory fields present
        if not self._identify_missing_fields(claim_data):
            return True
        # If mandatory fields are missing but route is not manual review
        if self._identify_missing_fields(claim_data) and route != ClaimRoute.MANUAL_REVIEW:
            return False
        return True
