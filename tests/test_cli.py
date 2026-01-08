"""Basic CLI tests."""

from click.testing import CliRunner

from vo_sim.cli import cli


def test_cli_version() -> None:
    """Test --version flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_help() -> None:
    """Test --help flag."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "VO_Sim" in result.output


def test_start_command() -> None:
    """Test start command runs."""
    runner = CliRunner()
    result = runner.invoke(cli, ["start"])
    assert result.exit_code == 0
    assert "LRU Cache" in result.output
    assert "Session Started" in result.output


def test_hint_command() -> None:
    """Test hint command runs."""
    runner = CliRunner()
    result = runner.invoke(cli, ["hint"])
    assert result.exit_code == 0
    assert "Hint" in result.output


def test_status_command() -> None:
    """Test status command runs."""
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0
    assert "Session Status" in result.output


def test_end_command() -> None:
    """Test end command runs."""
    runner = CliRunner()
    result = runner.invoke(cli, ["end"])
    assert result.exit_code == 0
    assert "Summary" in result.output
