"""Data models for insurance claims processing."""

from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Literal
from enum import Enum
from datetime import datetime


class ClaimType(str, Enum):
    """Enumeration of claim types."""
    PROPERTY_DAMAGE = "property_damage"
    BODILY_INJURY = "bodily_injury"
    THEFT = "theft"
    COLLISION = "collision"
    COMPREHENSIVE = "comprehensive"
    LIABILITY = "liability"
    UNKNOWN = "unknown"


class ClaimRoute(str, Enum):
    """Enumeration of routing destinations."""
    FAST_TRACK = "fast_track"
    STANDARD_PROCESSING = "standard_processing"
    MANUAL_REVIEW = "manual_review"
    INVESTIGATION_FLAG = "investigation_flag"
    SPECIALIST_QUEUE = "specialist_queue"


@dataclass
class PolicyInfo:
    """Policy information fields."""
    policy_number: Optional[str] = None
    policyholder_name: Optional[str] = None
    policy_effective_date: Optional[str] = None
    policy_expiration_date: Optional[str] = None
    insurance_company: Optional[str] = None


@dataclass
class IncidentInfo:
    """Incident information fields."""
    incident_date: Optional[str] = None
    incident_time: Optional[str] = None
    incident_location: Optional[str] = None
    incident_description: Optional[str] = None
    weather_conditions: Optional[str] = None


@dataclass
class InvolvedParty:
    """Details of an involved party."""
    name: Optional[str] = None
    relationship: Optional[str] = None  # claimant, third_party, witness
    contact_phone: Optional[str] = None
    contact_email: Optional[str] = None
    address: Optional[str] = None


@dataclass
class AssetDetails:
    """Asset information fields."""
    asset_type: Optional[str] = None
    asset_id: Optional[str] = None
    asset_description: Optional[str] = None
    estimated_damage: Optional[float] = None
    damage_description: Optional[str] = None


@dataclass
class ClaimData:
    """Complete claim data structure."""
    claim_type: ClaimType = ClaimType.UNKNOWN
    policy_info: PolicyInfo = field(default_factory=PolicyInfo)
    incident_info: IncidentInfo = field(default_factory=IncidentInfo)
    involved_parties: List[InvolvedParty] = field(default_factory=list)
    asset_details: AssetDetails = field(default_factory=AssetDetails)
    initial_estimate: Optional[float] = None
    attachments: List[str] = field(default_factory=list)
    processing_notes: Optional[str] = None
    extraction_confidence: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        """Convert to dictionary format."""
        return {
            "policy_info": asdict(self.policy_info),
            "incident_info": asdict(self.incident_info),
            "involved_parties": [asdict(party) for party in self.involved_parties],
            "asset_details": asdict(self.asset_details),
            "claim_type": self.claim_type.value,
            "initial_estimate": self.initial_estimate,
            "attachments": self.attachments,
            "processing_notes": self.processing_notes,
            "extraction_confidence": self.extraction_confidence,
        }


@dataclass
class RoutingDecision:
    """Routing decision output."""
    recommended_route: ClaimRoute
    reasoning: str
    flags: List[str] = field(default_factory=list)
    confidence_score: float = 0.8


@dataclass
class ClaimProcessingResult:
    """Final output of claim processing."""
    extracted_fields: Dict
    missing_fields: List[str]
    recommended_route: str
    routing_reasoning: str
    flags: List[str] = field(default_factory=list)
    confidence_score: float = 0.8
    processing_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_json_dict(self) -> Dict:
        """Convert to JSON-serializable dictionary."""
        return {
            "extractedFields": self.extracted_fields,
            "missingFields": self.missing_fields,
            "recommendedRoute": self.recommended_route,
            "reasoning": self.routing_reasoning,
            "flags": self.flags,
            "confidenceScore": self.confidence_score,
            "processingTimestamp": self.processing_timestamp,
        }
