"""Radar CLI entry point."""

import asyncio

import typer
from rich.console import Console

from contagion_radar import __version__

app = typer.Typer(
    name="radar",
    help="Systemic Contagion Radar - financial crisis early-warning CLI.",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    if value:
        console.print(f"contagion-radar {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit.",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Systemic Contagion Radar."""


@app.command()
def scan(
    entity: str = typer.Option(..., "--entity", "-e", help="Entity to scan."),
    config_dir: str = typer.Option("config", "--config", "-c", help="Config directory."),
) -> None:
    """One-shot risk analysis for a specific entity."""
    from contagion_radar.cli.commands.scan import _render_scan_result
    from contagion_radar.core.config import RadarConfig
    from contagion_radar.rule_engine.engine import RuleEngine

    try:
        config = RadarConfig.from_yaml(config_dir)
    except Exception:
        config = RadarConfig()

    engine = RuleEngine(config=config)
    console.print(f"[bold]Scanning {entity}...[/bold]")
    fv = asyncio.run(engine.tick(entity, data={}))
    _render_scan_result(entity, fv, config)


@app.command(name="db-init")
def db_init() -> None:
    """Initialize the 3 SQLite databases (metrics, corpus, knowledge)."""
    from contagion_radar.knowledge.database import init_all_databases

    init_all_databases()
    console.print("[green]Databases initialized successfully.[/green]")


@app.command()
def monitor(
    entity: str = typer.Option("USDC", "--entity", "-e", help="Entity to monitor."),
    config_dir: str = typer.Option("config", "--config", "-c", help="Config directory."),
) -> None:
    """Launch the live monitoring dashboard."""
    from contagion_radar.cli.dashboard import run_dashboard
    from contagion_radar.core.config import RadarConfig

    try:
        config = RadarConfig.from_yaml(config_dir)
    except Exception:
        config = RadarConfig()

    asyncio.run(run_dashboard(config, entity))


@app.command()
def calibrate(
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview changes without applying."),
    config_dir: str = typer.Option("config", "--config", "-c", help="Config directory."),
    data_dir: str = typer.Option("data", "--data-dir", help="Data directory."),
) -> None:
    """Recalibrate engine weights based on historical accuracy."""
    from pathlib import Path

    from contagion_radar.rule_engine.calibrator import Calibrator

    cal = Calibrator(data_dir=Path(data_dir), config_dir=Path(config_dir))
    result = cal.recalibrate(dry_run=dry_run)

    if not result.changes:
        console.print("[green]No weight changes needed.[/green]")
        return

    for change in result.changes:
        console.print(f"  {change}")

    if dry_run:
        console.print("[yellow]Dry run - no changes applied.[/yellow]")
    else:
        console.print("[green]Weights updated in engines.yaml.[/green]")


@app.command()
def premortem(
    entity: str = typer.Option(..., "--entity", "-e", help="Entity to analyze."),
    config_dir: str = typer.Option("config", "--config", "-c", help="Config directory."),
) -> None:
    """Generate pre-mortem hypotheses for an entity (offline mode)."""
    from contagion_radar.core.config import RadarConfig
    from contagion_radar.premortem.generator import PremortemGenerator
    from contagion_radar.reasoning.client import AIClient
    from contagion_radar.rule_engine.engine import RuleEngine

    try:
        config = RadarConfig.from_yaml(config_dir)
    except Exception:
        config = RadarConfig()

    engine = RuleEngine(config=config)
    fv = asyncio.run(engine.tick(entity, data={}))

    client = AIClient(config.ai)
    gen = PremortemGenerator(client)

    hypotheses = gen.generate_offline(entity, fv)

    if not hypotheses:
        console.print(f"[green]No significant risks detected for {entity}.[/green]")
        return

    console.print(f"\n[bold cyan]Pre-mortem Analysis: {entity}[/bold cyan]\n")
    for i, h in enumerate(hypotheses, 1):
        console.print(f"[bold]{i}. {h.failure_mode}[/bold] (p={h.probability:.2f}, confidence={h.confidence:.2f})")
        for step in h.cause_chain:
            console.print(f"   -> {step}")
        if h.data_signals:
            console.print(f"   Signals: {len(h.data_signals)} watch items")
        console.print()


@app.command()
def backtest(
    scenario: str = typer.Option(..., "--scenario", "-s", help="Scenario name (e.g., svb_2023)."),
    config_dir: str = typer.Option("config", "--config", "-c", help="Config directory."),
) -> None:
    """Run a historical backtest scenario."""
    from pathlib import Path

    from contagion_radar.backtest.runner import BacktestRunner
    from contagion_radar.core.config import RadarConfig

    scenario_path = Path(config_dir) / "backtest" / f"{scenario}.yaml"
    if not scenario_path.exists():
        console.print(f"[red]Scenario file not found: {scenario_path}[/red]")
        raise typer.Exit(1)

    try:
        config = RadarConfig.from_yaml(config_dir)
    except Exception:
        config = RadarConfig()

    runner = BacktestRunner(config)
    result = asyncio.run(runner.run_scenario(str(scenario_path)))
    console.print(result.report())


# Register operator commands
from contagion_radar.cli.commands.operator import register_commands
register_commands(app)


if __name__ == "__main__":
    app()
