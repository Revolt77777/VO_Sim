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

console = Console()


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
    # TODO: Create session via SessionManager
    # TODO: Emit SESSION_STARTED event
    # TODO: Transition state: IDLE -> PROBLEM_PRESENTED

    console.print(
        Panel.fit(
            "[bold cyan]🎯 LRU Cache Interview Session Started[/bold cyan]\n"
            "Session ID: [dim]550e8400-e29b-41d4-a716-446655440000[/dim]",
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
    # TODO: Check session state (must be PROBLEM_PRESENTED or AWAITING_ACTION)
    # TODO: Load and validate user code
    # TODO: Run evaluator
    # TODO: Classify failure
    # TODO: Emit CODE_SUBMITTED and EVAL_RESULT events
    # TODO: Run agent to generate feedback
    # TODO: Transition state: AWAITING_ACTION -> EVALUATING -> AWAITING_ACTION

    console.print(f"📥 Submitting code from: [cyan]{file_path}[/cyan]")
    console.print("🧪 Running evaluation...\n")

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
    # TODO: Check session state (must be AWAITING_ACTION)
    # TODO: Get agent context (attempts, failure history)
    # TODO: Run hint policy to determine level
    # TODO: Generate hint via LLM
    # TODO: Emit HINT_REQUESTED and HINT_GIVEN events

    console.print(
        Panel.fit(
            "[bold yellow]💡 Hint (Level 1)[/bold yellow]\n\n"
            "What data structure in Python's standard library maintains\n"
            "insertion order AND allows O(1) removal of arbitrary elements?\n\n"
            "[dim]Think about how you might combine two data structures...[/dim]",
            border_style="yellow",
        )
    )
    console.print()


@cli.command()
def status() -> None:
    """Show current session status."""
    # TODO: Load current session
    # TODO: Get session state and statistics
    # TODO: Display summary

    table = Table(title="Session Status", border_style="blue", show_header=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="yellow")

    table.add_row("Session ID", "550e8400-...")
    table.add_row("Problem", "LRU Cache")
    table.add_row("Started", "2026-01-06 12:00:00")
    table.add_row("Duration", "15m 32s")
    table.add_row("", "")
    table.add_row("Attempts", "3")
    table.add_row("Last Result", "❌ 5/12 tests passed")
    table.add_row("Hints Used", "1 (Level 1)")
    table.add_row("", "")
    table.add_row("Status", "Awaiting next submission or hint")

    console.print(table)
    console.print()


@cli.command()
def end() -> None:
    """End the current interview session."""
    # TODO: Check session exists
    # TODO: Generate session summary
    # TODO: Emit SESSION_ENDED event
    # TODO: Transition state: * -> DONE

    console.print(
        Panel.fit(
            "[bold green]Interview Summary[/bold green]\n\n"
            "[cyan]Session ID:[/cyan] 550e8400-...\n"
            "[cyan]Problem:[/cyan] LRU Cache\n"
            "[cyan]Duration:[/cyan] 24m 15s\n\n"
            "[cyan]Total Attempts:[/cyan] 4\n"
            "[cyan]Final Result:[/cyan] ✅ 12/12 tests passed\n"
            "[cyan]Hints Used:[/cyan] 2 (Levels 1, 2)\n\n"
            "[cyan]Outcome:[/cyan] Success! 🎉\n\n"
            "[dim]Session log saved to:\n"
            "~/.vo_sim/sessions/550e8400-....jsonl[/dim]",
            border_style="green",
        )
    )
    console.print()


# Error handling helper
def error(message: str) -> None:
    """Display error message and exit."""
    console.print(f"[bold red]❌ Error:[/bold red] {message}\n", style="red")
    sys.exit(1)


if __name__ == "__main__":
    cli()
