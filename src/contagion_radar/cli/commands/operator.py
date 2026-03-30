"""Operator intervention commands.

radar suppress --alert-id <id> --reason "maintenance" --duration 2h
radar override --entity <name> --severity 0.9 --duration 4h --reason "insider info"
radar reevaluate --entity <name>
radar acknowledge --alert-id <id>
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import typer
from rich.console import Console

console = Console()

_DATA_DIR = Path("./data")


def _get_knowledge_db() -> Path:
    return _DATA_DIR / "knowledge.db"


def _record_action(
    action_type: str,
    reason: str,
    target_entity: str | None = None,
    target_alert_id: str | None = None,
    parameters: dict | None = None,
    expires_at: str | None = None,
    operator_id: str | None = None,
) -> None:
    """Record an operator action in knowledge.db."""
    db_path = _get_knowledge_db()
    if not db_path.exists():
        console.print("[red]Knowledge DB not found. Run 'radar db-init' first.[/red]")
        raise typer.Exit(1)

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """INSERT INTO operator_actions
               (timestamp, action_type, target_entity, target_alert_id,
                reason, parameters, expires_at, operator_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                datetime.now(timezone.utc).isoformat(),
                action_type,
                target_entity,
                target_alert_id,
                reason,
                json.dumps(parameters or {}),
                expires_at,
                operator_id,
            ),
        )
        conn.commit()
    finally:
        conn.close()


def _parse_duration(duration: str) -> timedelta:
    """Parse duration string like '2h', '30m', '1d'."""
    unit = duration[-1].lower()
    value = float(duration[:-1])
    if unit == "h":
        return timedelta(hours=value)
    elif unit == "m":
        return timedelta(minutes=value)
    elif unit == "d":
        return timedelta(days=value)
    else:
        raise typer.BadParameter(f"Unknown duration unit: {unit}. Use h/m/d.")


def register_commands(app: typer.Typer) -> None:
    """Register operator commands on the CLI app."""

    @app.command()
    def suppress(
        alert_id: str = typer.Option(..., "--alert-id", help="Alert ID to suppress."),
        reason: str = typer.Option(..., "--reason", help="Reason for suppression."),
        duration: str = typer.Option("2h", "--duration", help="Duration (e.g., 2h, 30m, 1d)."),
    ) -> None:
        """Suppress an alert for a specified duration."""
        delta = _parse_duration(duration)
        expires = datetime.now(timezone.utc) + delta

        _record_action(
            action_type="suppress",
            reason=reason,
            target_alert_id=alert_id,
            parameters={"duration": duration},
            expires_at=expires.isoformat(),
        )
        console.print(f"[yellow]Alert {alert_id} suppressed until {expires.strftime('%Y-%m-%d %H:%M UTC')}[/yellow]")

    @app.command()
    def override(
        entity: str = typer.Option(..., "--entity", help="Entity to override."),
        severity: float = typer.Option(..., "--severity", help="Override severity (0-1)."),
        reason: str = typer.Option(..., "--reason", help="Reason for override."),
        duration: str = typer.Option("4h", "--duration", help="Duration (e.g., 4h, 1d)."),
    ) -> None:
        """Override severity for an entity."""
        delta = _parse_duration(duration)
        expires = datetime.now(timezone.utc) + delta

        _record_action(
            action_type="override",
            reason=reason,
            target_entity=entity,
            parameters={"severity": severity, "duration": duration},
            expires_at=expires.isoformat(),
        )
        console.print(f"[bold red]Override: {entity} severity={severity:.2f} until {expires.strftime('%Y-%m-%d %H:%M UTC')}[/bold red]")

    @app.command()
    def reevaluate(
        entity: str = typer.Option(..., "--entity", help="Entity to reevaluate."),
    ) -> None:
        """Force immediate reevaluation of an entity."""
        _record_action(
            action_type="reevaluate",
            reason=f"Manual reevaluation requested for {entity}",
            target_entity=entity,
        )
        console.print(f"[cyan]Reevaluation queued for {entity}.[/cyan]")

    @app.command()
    def acknowledge(
        alert_id: str = typer.Option(..., "--alert-id", help="Alert ID to acknowledge."),
    ) -> None:
        """Acknowledge an alert (mark as seen, no further action)."""
        _record_action(
            action_type="acknowledge",
            reason="Operator acknowledged",
            target_alert_id=alert_id,
        )
        console.print(f"[green]Alert {alert_id} acknowledged.[/green]")
