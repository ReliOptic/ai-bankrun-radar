"""YAML configuration loader with Pydantic validation.

All thresholds live here, never hardcoded in engine code.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field


# ── Sub-models ──────────────────────────────────────────────────


class SystemConfig(BaseModel):
    name: str = "Contagion Radar"
    version: str = "0.1.0"
    log_level: str = "INFO"
    data_dir: str = "./data"


class AIConfig(BaseModel):
    provider: str = "openrouter"
    base_url: str = "https://openrouter.ai/api/v1"
    api_key: str = ""
    model: str = "anthropic/claude-sonnet-4"
    max_tokens: int = 2000
    temperature: float = 0.3


class ApiKeysConfig(BaseModel):
    etherscan: str = ""
    twitter_bearer: str = ""
    reddit_client_id: str = ""
    reddit_client_secret: str = ""
    news_api: str = ""


# ── Engines ─────────────────────────────────────────────────────


class CompositeConfig(BaseModel):
    weights: dict[str, float] = Field(default_factory=lambda: {
        "topology": 0.35, "narrative": 0.30, "monoculture": 0.35
    })
    cross_engine_multiplier: float = 1.5
    cross_engine_threshold: float = 0.4
    gp_run_probability_weight: float = 0.4


class VulnerabilityConfig(BaseModel):
    leverage_weight: float = 0.30
    maturity_mismatch_weight: float = 0.25
    concentration_weight: float = 0.25
    centrality_weight: float = 0.20


class CascadeConfig(BaseModel):
    simulation_runs: int = 1000
    shock_magnitude_pct: float = 0.15
    failure_threshold: float = 0.50


class TopologyGraphConfig(BaseModel):
    min_edge_weight_usd: int = 1_000_000
    max_nodes: int = 500


class TopologyConfig(BaseModel):
    vulnerability: VulnerabilityConfig = Field(default_factory=VulnerabilityConfig)
    cascade: CascadeConfig = Field(default_factory=CascadeConfig)
    graph: TopologyGraphConfig = Field(default_factory=TopologyGraphConfig)


class NarrativeClassifierConfig(BaseModel):
    categories: list[str] = Field(default_factory=lambda: [
        "bank_run", "de_peg", "liquidity_crisis",
        "contagion", "confidence_loss", "regulatory_action",
    ])
    confidence_threshold: float = 0.7


class NarrativeMomentumConfig(BaseModel):
    spread_velocity_window_seconds: int = 3600
    algo_sensitivity_lookback_hours: int = 24
    liquidity_baseline_days: int = 30
    alert_threshold: float = 2.5


class NarrativeConfig(BaseModel):
    classifier: NarrativeClassifierConfig = Field(default_factory=NarrativeClassifierConfig)
    momentum: NarrativeMomentumConfig = Field(default_factory=NarrativeMomentumConfig)


class EntropyConfig(BaseModel):
    num_strategy_clusters: int = 10
    clustering_window_minutes: int = 60
    index_alert_threshold: float = 0.75


class CorrelationConfig(BaseModel):
    lookback_minutes: int = 120
    high_correlation_threshold: float = 0.85


class MonocultureConfig(BaseModel):
    entropy: EntropyConfig = Field(default_factory=EntropyConfig)
    correlation: CorrelationConfig = Field(default_factory=CorrelationConfig)


class GPModelConfig(BaseModel):
    lambda_: float = Field(0.25, alias="lambda_")
    R: float = 2.0
    risk_aversion: float = 2.0
    epsilon: float = 0.001
    alert_threshold: float = 0.30


class DDModelConfig(BaseModel):
    lambda_: float = Field(0.25, alias="lambda_")
    R: float = 2.0


class ModelsConfig(BaseModel):
    goldstein_pauzner: GPModelConfig = Field(default_factory=GPModelConfig)
    diamond_dybvig: DDModelConfig = Field(default_factory=DDModelConfig)


class EnginesConfig(BaseModel):
    composite: CompositeConfig = Field(default_factory=CompositeConfig)
    topology: TopologyConfig = Field(default_factory=TopologyConfig)
    narrative: NarrativeConfig = Field(default_factory=NarrativeConfig)
    monoculture: MonocultureConfig = Field(default_factory=MonocultureConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)


# ── Alerts ──────────────────────────────────────────────────────


class AlertLevelConfig(BaseModel):
    name: str
    color: str
    composite_threshold: float


class NoveltyMultiplierConfig(BaseModel):
    routine_max_similarity: float = 0.7
    novel_max_similarity: float = 0.3
    routine_multiplier: float = 1.0
    novel_multiplier: float = 1.5


class AlertsConfig(BaseModel):
    levels: dict[int, AlertLevelConfig] = Field(default_factory=dict)
    novelty_multiplier: NoveltyMultiplierConfig = Field(
        default_factory=NoveltyMultiplierConfig
    )


# ── Cadence ─────────────────────────────────────────────────────


class HysteresisConfig(BaseModel):
    escalation_consecutive_ticks: int = 3
    deescalation_damping: float = 0.3
    stability_window_seconds: int = 300
    min_interval_seconds: int = 10
    max_interval_seconds: int = 3600


class AITriggersConfig(BaseModel):
    context_interpretation_threshold: float = 0.5
    premortem_generation_threshold: float = 0.7
    crisis_analysis_threshold: float = 0.9
    postmortem_drop_below: float = 0.5
    postmortem_was_above: float = 0.7
    daily_refresh_below: float = 0.3
    daily_refresh_top_n: int = 5


class CadenceConfig(BaseModel):
    curve: list[list[float]] = Field(default_factory=list)
    hysteresis: HysteresisConfig = Field(default_factory=HysteresisConfig)
    ai_triggers: AITriggersConfig = Field(default_factory=AITriggersConfig)


# ── AI Budget ───────────────────────────────────────────────────


class AIBudgetConfig(BaseModel):
    daily_limits: dict[str, int] = Field(default_factory=lambda: {
        "normal": 20, "elevated": 50, "warning": 200, "critical": -1,
    })
    risk_level_thresholds: dict[str, float] = Field(default_factory=lambda: {
        "normal": 0.3, "elevated": 0.6, "warning": 0.8,
    })
    call_priorities: dict[str, int] = Field(default_factory=dict)


# ── Quality Gate ────────────────────────────────────────────────


class SourceQualityConfig(BaseModel):
    max_stale_seconds: int
    circuit_breaker_failures: int = 3
    completeness_required_fields: list[str] = Field(default_factory=list)


class QualityGateConfig(BaseModel):
    sources: dict[str, SourceQualityConfig] = Field(default_factory=dict)
    score_discounts: dict[str, float] = Field(default_factory=lambda: {
        "FRESH": 1.0, "STALE": 0.7, "DEGRADED": 0.4, "OFFLINE": 0.0,
    })


# ── Pre-mortem ──────────────────────────────────────────────────


class PremortemEntityConfig(BaseModel):
    id: str
    name: str
    type: str


class PremortemHypothesisConfig(BaseModel):
    max_active_per_entity: int = 5
    expiry_days: int = 30
    confidence_escalation_threshold: float = 0.7
    min_data_signals: int = 2


class PremortemScheduleConfig(BaseModel):
    daily_refresh_hour_utc: int = 6
    on_score_cross_up: list[float] = Field(default_factory=list)
    on_score_cross_down_from: float = 0.7
    on_score_cross_down_to: float = 0.5


class PremortemConfig(BaseModel):
    schedule: PremortemScheduleConfig = Field(default_factory=PremortemScheduleConfig)
    entities: list[PremortemEntityConfig] = Field(default_factory=list)
    hypothesis: PremortemHypothesisConfig = Field(default_factory=PremortemHypothesisConfig)


# ── Root Config ─────────────────────────────────────────────────


class RadarConfig(BaseModel):
    system: SystemConfig = Field(default_factory=SystemConfig)
    ai: AIConfig = Field(default_factory=AIConfig)
    api_keys: ApiKeysConfig = Field(default_factory=ApiKeysConfig)
    engines: EnginesConfig = Field(default_factory=EnginesConfig)
    alerts: AlertsConfig = Field(default_factory=AlertsConfig)
    cadence: CadenceConfig = Field(default_factory=CadenceConfig)
    ai_budget: AIBudgetConfig = Field(default_factory=AIBudgetConfig)
    quality_gate: QualityGateConfig = Field(default_factory=QualityGateConfig)
    premortem: PremortemConfig = Field(default_factory=PremortemConfig)

    @classmethod
    def from_yaml(cls, config_dir: str | Path) -> "RadarConfig":
        """Load and merge all YAML files from a config directory."""
        config_dir = Path(config_dir)
        merged: dict[str, Any] = {}

        file_mapping = {
            "default.yaml": None,  # top-level keys
            "engines.yaml": "engines",
            "alerts.yaml": "alerts",
            "cadence.yaml": "cadence",
            "ai_budget.yaml": "ai_budget",
            "quality_gate.yaml": "quality_gate",
            "premortem.yaml": "premortem",
        }

        for filename, key in file_mapping.items():
            path = config_dir / filename
            if not path.exists():
                continue
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}

            # Resolve environment variable references
            data = _resolve_env_vars(data)

            if key is None:
                merged.update(data)
            else:
                merged[key] = data

        return cls.model_validate(merged)


def _resolve_env_vars(data: Any) -> Any:
    """Recursively replace ${VAR} with os.environ.get(VAR, '')."""
    if isinstance(data, str) and data.startswith("${") and data.endswith("}"):
        var_name = data[2:-1]
        return os.environ.get(var_name, "")
    elif isinstance(data, dict):
        return {k: _resolve_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [_resolve_env_vars(item) for item in data]
    return data
