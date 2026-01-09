"""CLI interface for VO_Sim using Click and Rich.

Commands:
- start: Start new interview session
- submit: Submit code for evaluation
- hint: Request a hint
- status: Show session status
- end: End session and show summary
"""

import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from vo_sim.schemas import EventType, SessionState
from vo_sim.session.manager import (
    NoActiveSessionError,
    SessionAlreadyActiveError,
    SessionManager,
)

console = Console()

# Global session manager instance
_session_manager: SessionManager | None = None


def get_manager() -> SessionManager:
    """Get or create the global session manager."""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager


def error(message: str) -> None:
    """Display error message and exit."""
    console.print(f"[bold red]❌ Error:[/bold red] {message}\n", style="red")
    sys.exit(1)


@click.group()
@click.version_option(version="0.1.0", prog_name="vo-sim")
def cli() -> None:
    """VO_Sim - Virtual Onsite Simulator.

    An AI-powered coding interview agent for LRU Cache problems.
    """
    pass


@cli.command()
def start() -> None:
    """Start a new interview session."""
    manager = get_manager()

    try:
        session_id = manager.create_session()
    except SessionAlreadyActiveError as e:
        error(
            f"Session already in progress ({manager.get_active_session_id()[:8]}...).\n"
            "Use 'vo-sim end' to finish current session first."
        )
        return

    console.print(
        Panel.fit(
            "[bold cyan]🎯 LRU Cache Interview Session Started[/bold cyan]\n"
            f"Session ID: [dim]{session_id}[/dim]",
            border_style="cyan",
        )
    )

    console.print("\n[bold]Problem:[/bold] Implement an LRU (Least Recently Used) Cache")
    console.print(
        "\nYour class must implement:\n"
        "  • [cyan]__init__(capacity: int)[/cyan]\n"
        "  • [cyan]get(key: int) -> int[/cyan]\n"
        "  • [cyan]put(key: int, value: int) -> None[/cyan]"
    )

    console.print(
        "\n[dim]When ready, submit your solution:[/dim]\n"
        "  [yellow]vo-sim submit --file your_solution.py[/yellow]\n"
    )


@cli.command()
@click.option(
    "--file",
    "-f",
    "file_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to your solution file",
)
def submit(file_path: str) -> None:
    """Submit code for evaluation."""
    manager = get_manager()

    # Check if session exists
    try:
        state = manager.get_current_state()
    except NoActiveSessionError:
        error("No active interview session.\nStart a new session with: vo-sim start")
        return

    # Check if submission is allowed in current state
    state_machine = manager.get_state_machine()
    if not state_machine.can_submit_code():
        error(
            f"Cannot submit code in current state: {state.value}\n"
            "Wait for evaluation to complete."
        )
        return

    console.print(f"📥 Submitting code from: [cyan]{file_path}[/cyan]")
    console.print("🧪 Running evaluation...\n")

    # Transition to EVALUATING
    manager.transition_to(SessionState.EVALUATING)

    # Emit CODE_SUBMITTED event
    manager.emit_event(
        EventType.CODE_SUBMITTED,
        {
            "attempt_number": len(
                [
                    e
                    for e in manager.get_session_events()
                    if e.event_type == EventType.CODE_SUBMITTED
                ]
            )
            + 1,
            "file_path": file_path,
        },
    )

    # TODO: Actually run evaluator here
    # For now, show mock results and transition back

    # Mock result display
    table = Table(title="Evaluation Result", border_style="red")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Status", "❌ Failed")
    table.add_row("Tests Passed", "5/12")
    table.add_row("Tests Failed", "7/12")
    table.add_row("Failure Type", "WRONG_ANSWER")
    table.add_row("Runtime", "145ms")

    console.print(table)

    console.print("\n[bold]Failing Tests:[/bold]")
    console.print("  • test_eviction_order_simple")
    console.print("  • test_eviction_order_complex")
    console.print("  • test_capacity_one")

    # Emit EVAL_RESULT event
    manager.emit_event(
        EventType.EVAL_RESULT,
        {
            "passed": False,
            "failure_type": "WRONG_ANSWER",
            "tests_passed": 5,
            "tests_failed": 7,
        },
    )

    # Transition to AWAITING_ACTION
    manager.transition_to(SessionState.AWAITING_ACTION)

    console.print(
        "\n💬 [bold]Feedback:[/bold]\n"
        "Your solution has issues with eviction logic. When the cache\n"
        "reaches capacity, it should remove the least recently used item.\n"
    )

    console.print(
        "[dim]Try again or type[/dim] [yellow]'vo-sim hint'[/yellow] [dim]for guidance.[/dim]\n"
    )


@cli.command()
def hint() -> None:
    """Request a hint for the current problem."""
    manager = get_manager()

    # Check if session exists
    try:
        state = manager.get_current_state()
    except NoActiveSessionError:
        error("No active interview session.\nStart a new session with: vo-sim start")
        return

    # Check if hint is allowed in current state
    state_machine = manager.get_state_machine()
    if not state_machine.can_request_hint():
        error(
            f"Cannot request hint in current state: {state.value}\n"
            "Submit code first with: vo-sim submit --file <path>"
        )
        return

    # Emit HINT_REQUESTED event
    manager.emit_event(EventType.HINT_REQUESTED, {})

    # TODO: Use hint policy to determine level
    # TODO: Generate hint via LLM

    console.print(
        Panel.fit(
            "[bold yellow]💡 Hint (Level 1)[/bold yellow]\n\n"
            "What data structure in Python's standard library maintains\n"
            "insertion order AND allows O(1) removal of arbitrary elements?\n\n"
            "[dim]Think about how you might combine two data structures...[/dim]",
            border_style="yellow",
        )
    )

    # Emit HINT_GIVEN event
    manager.emit_event(
        EventType.HINT_GIVEN,
        {"hint_level": 1, "trigger_reason": "user_request"},
    )

    console.print()


@cli.command()
def status() -> None:
    """Show current session status."""
    manager = get_manager()

    # Check if session exists
    try:
        session_id = manager.get_active_session_id()
        state = manager.get_current_state()
        events = manager.get_session_events()
    except NoActiveSessionError:
        error("No active interview session.\nStart a new session with: vo-sim start")
        return

    # Count events
    submission_count = len(
        [e for e in events if e.event_type == EventType.CODE_SUBMITTED]
    )
    hint_count = len([e for e in events if e.event_type == EventType.HINT_GIVEN])

    # Get session start time
    start_event = events[0]
    start_time = start_event.timestamp

    table = Table(title="Session Status", border_style="blue", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Session ID", f"{session_id[:8]}...")
    table.add_row("Problem", "LRU Cache")
    table.add_row("Started", start_time.strftime("%Y-%m-%d %H:%M:%S"))
    table.add_row("Current State", state.value)
    table.add_row("", "")
    table.add_row("Attempts", str(submission_count))
    table.add_row("Hints Used", str(hint_count))
    table.add_row("Total Events", str(len(events)))

    console.print(table)
    console.print()


@cli.command()
def end() -> None:
    """End the current interview session."""
    manager = get_manager()

    # Check if session exists
    try:
        session_id = manager.get_active_session_id()
        events = manager.get_session_events()
    except NoActiveSessionError:
        error("No active interview session.\nStart a new session with: vo-sim start")
        return

    # Calculate stats
    submission_count = len(
        [e for e in events if e.event_type == EventType.CODE_SUBMITTED]
    )
    hint_count = len([e for e in events if e.event_type == EventType.HINT_GIVEN])

    # Get session duration
    start_event = events[0]
    from datetime import datetime

    duration = datetime.utcnow() - start_event.timestamp
    duration_str = f"{int(duration.total_seconds() // 60)}m {int(duration.total_seconds() % 60)}s"

    # End the session
    manager.end_session()

    console.print(
        Panel.fit(
            "[bold green]Interview Summary[/bold green]\n\n"
            f"[cyan]Session ID:[/cyan] {session_id[:8]}...\n"
            "[cyan]Problem:[/cyan] LRU Cache\n"
            f"[cyan]Duration:[/cyan] {duration_str}\n\n"
            f"[cyan]Total Attempts:[/cyan] {submission_count}\n"
            f"[cyan]Hints Used:[/cyan] {hint_count}\n\n"
            "[cyan]Outcome:[/cyan] Session ended\n\n"
            "[dim]Session log saved to:\n"
            f"~/.vo_sim/sessions/{session_id}.jsonl[/dim]",
            border_style="green",
        )
    )
    console.print()


if __name__ == "__main__":
    cli()
