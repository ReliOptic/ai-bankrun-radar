"""Domain types for the Contagion Radar system."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, Field


class DataStatus(str, Enum):
    FRESH = "FRESH"
    STALE = "STALE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"


class CadenceState(str, Enum):
    NORMAL = "NORMAL"
    ELEVATED = "ELEVATED"
    CRITICAL = "CRITICAL"
    CRISIS = "CRISIS"


class HypothesisStatus(str, Enum):
    GENERATED = "generated"
    ACTIVE = "active"
    CONFIRMED = "confirmed"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"


# ── Core data types ────────────────────────────────────────────


class Signal(BaseModel):
    """A single metric observation relative to a threshold."""
    metric: str
    entity: str
    value: float
    threshold: float
    triggered: bool
    description: str = ""


class DataConfidence(BaseModel):
    """Quality assessment for a data source."""
    source: str
    status: DataStatus
    staleness_seconds: float = 0.0
    completeness_ratio: float = 1.0
    consecutive_failures: int = 0
    last_successful_fetch: Optional[datetime] = None


class RiskScore(BaseModel):
    """Output of a single engine."""
    engine: str
    value: float = Field(ge=0.0, le=1.0)
    signals: list[Signal] = Field(default_factory=list)
    data_confidence: float = Field(1.0, ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class FeatureVector(BaseModel):
    """Full system state -- passed to AI layer (never just a scalar)."""
    composite: float = Field(ge=0.0, le=1.0)
    engines: dict[str, RiskScore] = Field(default_factory=dict)
    data_quality: dict[str, DataStatus] = Field(default_factory=dict)
    gp_run_probability: Optional[float] = None
    dd_f_critical: Optional[float] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class NoveltyAssessment(BaseModel):
    """AI-generated novelty evaluation."""
    multiplier: float = Field(1.0, ge=1.0, le=1.5)
    closest_precedent: Optional[str] = None
    similarity: float = Field(0.0, ge=0.0, le=1.0)
    reasoning: str = ""


class Alert(BaseModel):
    """System alert with novelty-adjusted severity."""
    id: str = ""
    severity: float = Field(ge=0.0, le=1.0)
    level: int = Field(ge=1, le=5)
    feature_vector: FeatureVector
    novelty: Optional[NoveltyAssessment] = None
    explanation: str = ""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    suppressed: bool = False
    operator_override_severity: Optional[float] = None

    @property
    def effective_severity(self) -> float:
        if self.operator_override_severity is not None:
            return self.operator_override_severity
        base = self.severity
        mult = self.novelty.multiplier if self.novelty else 1.0
        return min(1.0, base * mult)


# ── Pre-mortem types ───────────────────────────────────────────


class DataSignal(BaseModel):
    """Concrete, measurable indicator from a hypothesis."""
    metric: str
    entity: str
    threshold: float
    direction: Literal["above", "below"]
    description: str = ""


class Evidence(BaseModel):
    """Data point supporting or contradicting a hypothesis."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metric: str
    observed_value: float
    expected_direction: str
    actual_direction: str
    supports: bool
    weight: float = 1.0
    context: str = ""


class Hypothesis(BaseModel):
    """Pre-mortem generated hypothesis about an entity failure."""
    id: str = ""
    entity_id: str
    failure_mode: str
    cause_chain: list[str] = Field(default_factory=list)
    probability: float = Field(ge=0.0, le=1.0)
    data_signals: list[DataSignal] = Field(default_factory=list)
    evidence_for: list[Evidence] = Field(default_factory=list)
    evidence_against: list[Evidence] = Field(default_factory=list)
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    confidence_trajectory: list[tuple[str, float]] = Field(default_factory=list)
    status: HypothesisStatus = HypothesisStatus.GENERATED
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    model_used: str = ""


# ── Cadence types ──────────────────────────────────────────────


class AITriggerType(str, Enum):
    CONTEXT_INTERPRETATION = "context_interpretation"
    PREMORTEM_GENERATION = "premortem_generation"
    CRISIS_ANALYSIS = "crisis_analysis"
    POST_MORTEM = "post_mortem"
    DAILY_REFRESH = "daily_refresh"


class AITrigger(BaseModel):
    """A request to invoke the AI reasoning layer."""
    type: AITriggerType
    reason: str = ""
    feature_vector: Optional[FeatureVector] = None


class CadenceDecision(BaseModel):
    """Output of the cadence controller."""
    interval_seconds: float
    ai_triggers: list[AITrigger] = Field(default_factory=list)
    state: CadenceState = CadenceState.NORMAL
