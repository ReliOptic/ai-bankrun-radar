"""Rich Live Dashboard for real-time monitoring.

6-panel layout:
  - 3 engine scores
  - Cadence state
  - Alerts
  - Data quality + operator status
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from contagion_radar.cadence.controller import CadenceController
from contagion_radar.core.config import RadarConfig
from contagion_radar.core.types import CadenceState, FeatureVector
from contagion_radar.rule_engine.engine import RuleEngine

console = Console()


def _score_color(value: float) -> str:
    if value >= 0.7:
        return "red"
    elif value >= 0.4:
        return "yellow"
    return "green"


def _state_color(state: CadenceState) -> str:
    return {
        CadenceState.NORMAL: "green",
        CadenceState.ELEVATED: "yellow",
        CadenceState.CRITICAL: "red",
        CadenceState.CRISIS: "bold red",
    }.get(state, "white")


def _build_engine_panel(name: str, fv: FeatureVector) -> Panel:
    rs = fv.engines.get(name)
    if rs is None:
        return Panel("No data", title=name.title())

    color = _score_color(rs.value)
    lines = [f"[{color}]Score: {rs.value:.2f}[/{color}]"]

    for sig in rs.signals[:3]:
        lines.append(f"  {sig.description}")

    if not rs.signals:
        lines.append("  No signals")

    return Panel("\n".join(lines), title=f"[bold]{name.title()}[/bold]", border_style=color)


def _build_cadence_panel(state: CadenceState, interval: float) -> Panel:
    color = _state_color(state)

    if interval >= 3600:
        interval_str = f"{interval/3600:.0f}h"
    elif interval >= 60:
        interval_str = f"{interval/60:.0f}m"
    else:
        interval_str = f"{interval:.0f}s"

    return Panel(
        f"[{color}]State: {state.value}[/{color}]\nInterval: {interval_str}",
        title="[bold]Cadence[/bold]",
        border_style=color,
    )


def _build_quality_panel(fv: FeatureVector) -> Panel:
    lines = []
    status_icons = {"FRESH": "[green]OK[/green]", "STALE": "[yellow]STALE[/yellow]",
                    "DEGRADED": "[red]DEGRADED[/red]", "OFFLINE": "[bold red]OFFLINE[/bold red]"}
    for source, status in fv.data_quality.items():
        icon = status_icons.get(status.value if hasattr(status, 'value') else str(status), "?")
        lines.append(f"  {source}: {icon}")
    if not lines:
        lines.append("  No sources")
    return Panel("\n".join(lines), title="[bold]Data Quality[/bold]")


def _build_alert_panel(fv: FeatureVector) -> Panel:
    if fv.composite >= 0.9:
        level, color = 5, "bold red"
        text = f"[{color}][Level 5] CRISIS - composite {fv.composite:.2f}[/{color}]"
    elif fv.composite >= 0.7:
        level, color = 4, "red"
        text = f"[{color}][Level 4] CRITICAL - composite {fv.composite:.2f}[/{color}]"
    elif fv.composite >= 0.5:
        level, color = 3, "yellow"
        text = f"[{color}][Level 3] WARNING - composite {fv.composite:.2f}[/{color}]"
    elif fv.composite >= 0.3:
        level, color = 2, "cyan"
        text = f"[{color}][Level 2] ELEVATED - composite {fv.composite:.2f}[/{color}]"
    else:
        text = "[green][Level 1] NORMAL - monitoring[/green]"

    lines = [text]

    # Add top signals across engines
    for name, rs in fv.engines.items():
        for sig in rs.signals[:1]:
            lines.append(f"  [{name}] {sig.description}")

    return Panel("\n".join(lines), title="[bold]Alerts[/bold]")


def build_dashboard_layout(
    fv: FeatureVector,
    cadence_state: CadenceState,
    interval: float,
) -> Layout:
    """Build the 6-panel dashboard layout."""
    layout = Layout()
    layout.split_column(
        Layout(name="top", size=8),
        Layout(name="middle", size=8),
        Layout(name="bottom", size=6),
    )

    layout["top"].split_row(
        Layout(_build_engine_panel("topology", fv)),
        Layout(_build_engine_panel("narrative", fv)),
        Layout(_build_engine_panel("monoculture", fv)),
    )

    layout["middle"].split_row(
        Layout(_build_cadence_panel(cadence_state, interval)),
        Layout(_build_alert_panel(fv), ratio=2),
    )

    layout["bottom"].split_row(
        Layout(_build_quality_panel(fv)),
        Layout(Panel(
            f"Composite: {fv.composite:.3f}\n"
            f"G&P P(run): {fv.gp_run_probability:.2%}" if fv.gp_run_probability else "N/A",
            title="[bold]Summary[/bold]",
        )),
    )

    return layout


async def run_dashboard(
    config: RadarConfig,
    entity: str,
) -> None:
    """Run the live monitoring dashboard."""
    engine = RuleEngine(config=config)
    cadence = CadenceController(config.cadence)

    console.print(f"[bold cyan]Contagion Radar[/bold cyan] - Monitoring {entity}")
    console.print("Press [bold]Ctrl+C[/bold] to exit\n")

    with Live(console=console, refresh_per_second=1) as live:
        try:
            while True:
                fv = await engine.tick(entity, data={})
                decision = cadence.update(fv.composite)

                layout = build_dashboard_layout(
                    fv, decision.state, decision.interval_seconds
                )
                live.update(layout)

                await asyncio.sleep(min(decision.interval_seconds, 10))
        except KeyboardInterrupt:
            console.print("\n[yellow]Dashboard stopped.[/yellow]")
