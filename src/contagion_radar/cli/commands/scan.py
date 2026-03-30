"""One-shot scan command.

radar scan --entity USDC
"""

from __future__ import annotations

import asyncio

import typer
from rich.console import Console
from rich.table import Table

from contagion_radar.core.config import RadarConfig
from contagion_radar.core.types import CadenceState
from contagion_radar.rule_engine.engine import RuleEngine

console = Console()


def register_scan(app: typer.Typer) -> None:
    """Replace the placeholder scan command with the real implementation."""

    @app.command(name="scan")
    def scan(
        entity: str = typer.Option(..., "--entity", "-e", help="Entity to scan."),
        config_dir: str = typer.Option("config", "--config", "-c", help="Config directory."),
    ) -> None:
        """One-shot risk analysis for a specific entity."""
        try:
            config = RadarConfig.from_yaml(config_dir)
        except Exception:
            config = RadarConfig()

        engine = RuleEngine(config=config)

        console.print(f"[bold]Scanning {entity}...[/bold]")

        fv = asyncio.run(engine.tick(entity, data={}))

        _render_scan_result(entity, fv, config)


def _render_scan_result(entity: str, fv, config: RadarConfig) -> None:
    """Render scan results in a structured format."""
    from datetime import datetime

    now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    # State classification
    if fv.composite >= 0.9:
        state = "[bold red]CRISIS[/bold red]"
    elif fv.composite >= 0.7:
        state = "[red]CRITICAL[/red]"
    elif fv.composite >= 0.4:
        state = "[yellow]ELEVATED[/yellow]"
    else:
        state = "[green]NORMAL[/green]"

    # Data quality summary
    fresh_count = sum(1 for s in fv.data_quality.values() if s.value == "FRESH")
    total_sources = max(len(fv.data_quality), 1)

    console.print()
    console.print(f"[bold cyan][SCAN][/bold cyan] {entity} -- {now}")
    console.print(f"Composite: [bold]{fv.composite:.2f}[/bold] ({state})    Data Quality: {fresh_count}/{total_sources}")
    console.print()

    # Engine table
    table = Table(show_header=True, header_style="bold")
    table.add_column("Engine", style="cyan", width=14)
    table.add_column("Score", justify="right", width=7)
    table.add_column("Top Signal", width=45)

    for engine_name in ["topology", "narrative", "monoculture"]:
        rs = fv.engines.get(engine_name)
        if rs is None:
            continue
        top_signal = rs.signals[0].description if rs.signals else "-"
        score_color = "red" if rs.value > 0.6 else "yellow" if rs.value > 0.3 else "green"
        table.add_row(
            engine_name,
            f"[{score_color}]{rs.value:.2f}[/{score_color}]",
            top_signal,
        )

    console.print(table)
    console.print()

    # Model outputs
    gp_str = f"{fv.gp_run_probability:.1%}" if fv.gp_run_probability is not None else "N/A"
    dd_str = f"{fv.dd_f_critical:.2f}" if fv.dd_f_critical is not None else "N/A"
    console.print(f"G&P P(run): {gp_str}    D&D f_critical: {dd_str}")
