"""Tests for session state machine."""

import pytest

from vo_sim.schemas import SessionState
from vo_sim.session.state_machine import InvalidTransitionError, SessionStateMachine


def test_initial_state_is_idle() -> None:
    """Test state machine starts in IDLE state."""
    sm = SessionStateMachine()
    assert sm.current_state == SessionState.IDLE


def test_initial_state_can_be_set() -> None:
    """Test state machine can start in a different state."""
    sm = SessionStateMachine(initial_state=SessionState.AWAITING_ACTION)
    assert sm.current_state == SessionState.AWAITING_ACTION


def test_valid_transition_idle_to_problem_presented() -> None:
    """Test valid transition: IDLE → PROBLEM_PRESENTED (start session)."""
    sm = SessionStateMachine()
    sm.transition_to(SessionState.PROBLEM_PRESENTED)
    assert sm.current_state == SessionState.PROBLEM_PRESENTED


def test_valid_transition_problem_to_evaluating() -> None:
    """Test valid transition: PROBLEM_PRESENTED → EVALUATING (submit code)."""
    sm = SessionStateMachine(initial_state=SessionState.PROBLEM_PRESENTED)
    sm.transition_to(SessionState.EVALUATING)
    assert sm.current_state == SessionState.EVALUATING


def test_valid_transition_evaluating_to_awaiting() -> None:
    """Test valid transition: EVALUATING → AWAITING_ACTION (tests complete)."""
    sm = SessionStateMachine(initial_state=SessionState.EVALUATING)
    sm.transition_to(SessionState.AWAITING_ACTION)
    assert sm.current_state == SessionState.AWAITING_ACTION


def test_valid_transition_awaiting_to_evaluating() -> None:
    """Test valid transition: AWAITING_ACTION → EVALUATING (submit again)."""
    sm = SessionStateMachine(initial_state=SessionState.AWAITING_ACTION)
    sm.transition_to(SessionState.EVALUATING)
    assert sm.current_state == SessionState.EVALUATING


def test_valid_transition_awaiting_to_awaiting() -> None:
    """Test valid transition: AWAITING_ACTION → AWAITING_ACTION (hint)."""
    sm = SessionStateMachine(initial_state=SessionState.AWAITING_ACTION)
    sm.transition_to(SessionState.AWAITING_ACTION)
    assert sm.current_state == SessionState.AWAITING_ACTION


def test_valid_transition_to_done_from_any_state() -> None:
    """Test can transition to DONE from any state (end session)."""
    # From IDLE
    sm = SessionStateMachine(initial_state=SessionState.IDLE)
    sm.transition_to(SessionState.DONE)
    assert sm.current_state == SessionState.DONE

    # From PROBLEM_PRESENTED
    sm = SessionStateMachine(initial_state=SessionState.PROBLEM_PRESENTED)
    sm.transition_to(SessionState.DONE)
    assert sm.current_state == SessionState.DONE

    # From AWAITING_ACTION
    sm = SessionStateMachine(initial_state=SessionState.AWAITING_ACTION)
    sm.transition_to(SessionState.DONE)
    assert sm.current_state == SessionState.DONE


def test_invalid_transition_idle_to_evaluating() -> None:
    """Test invalid transition: IDLE → EVALUATING (can't skip problem presentation)."""
    sm = SessionStateMachine()
    with pytest.raises(InvalidTransitionError) as exc_info:
        sm.transition_to(SessionState.EVALUATING)

    assert "idle" in str(exc_info.value).lower()
    assert "evaluating" in str(exc_info.value).lower()


def test_invalid_transition_problem_to_awaiting() -> None:
    """Test invalid transition: PROBLEM_PRESENTED → AWAITING_ACTION (must evaluate first)."""
    sm = SessionStateMachine(initial_state=SessionState.PROBLEM_PRESENTED)
    with pytest.raises(InvalidTransitionError):
        sm.transition_to(SessionState.AWAITING_ACTION)


def test_invalid_transition_from_done() -> None:
    """Test DONE is terminal state - no transitions allowed."""
    sm = SessionStateMachine(initial_state=SessionState.DONE)

    # Cannot transition to any state from DONE
    with pytest.raises(InvalidTransitionError):
        sm.transition_to(SessionState.IDLE)

    with pytest.raises(InvalidTransitionError):
        sm.transition_to(SessionState.PROBLEM_PRESENTED)


def test_can_transition_to_returns_true_for_valid() -> None:
    """Test can_transition_to returns True for valid transitions."""
    sm = SessionStateMachine()
    assert sm.can_transition_to(SessionState.PROBLEM_PRESENTED) is True


def test_can_transition_to_returns_false_for_invalid() -> None:
    """Test can_transition_to returns False for invalid transitions."""
    sm = SessionStateMachine()
    assert sm.can_transition_to(SessionState.EVALUATING) is False


def test_reset_returns_to_idle() -> None:
    """Test reset() returns state machine to IDLE."""
    sm = SessionStateMachine(initial_state=SessionState.AWAITING_ACTION)
    sm.reset()
    assert sm.current_state == SessionState.IDLE


def test_is_done_returns_true_when_done() -> None:
    """Test is_done() returns True when in DONE state."""
    sm = SessionStateMachine(initial_state=SessionState.DONE)
    assert sm.is_done() is True


def test_is_done_returns_false_when_not_done() -> None:
    """Test is_done() returns False when not in DONE state."""
    sm = SessionStateMachine()
    assert sm.is_done() is False


def test_can_submit_code_in_valid_states() -> None:
    """Test can_submit_code() returns True in PROBLEM_PRESENTED and AWAITING_ACTION."""
    sm = SessionStateMachine(initial_state=SessionState.PROBLEM_PRESENTED)
    assert sm.can_submit_code() is True

    sm = SessionStateMachine(initial_state=SessionState.AWAITING_ACTION)
    assert sm.can_submit_code() is True


def test_cannot_submit_code_in_invalid_states() -> None:
    """Test can_submit_code() returns False in other states."""
    sm = SessionStateMachine(initial_state=SessionState.IDLE)
    assert sm.can_submit_code() is False

    sm = SessionStateMachine(initial_state=SessionState.EVALUATING)
    assert sm.can_submit_code() is False

    sm = SessionStateMachine(initial_state=SessionState.DONE)
    assert sm.can_submit_code() is False


def test_can_request_hint_only_when_awaiting() -> None:
    """Test can_request_hint() returns True only in AWAITING_ACTION."""
    sm = SessionStateMachine(initial_state=SessionState.AWAITING_ACTION)
    assert sm.can_request_hint() is True

    # Other states should return False
    sm = SessionStateMachine(initial_state=SessionState.IDLE)
    assert sm.can_request_hint() is False

    sm = SessionStateMachine(initial_state=SessionState.PROBLEM_PRESENTED)
    assert sm.can_request_hint() is False


def test_full_session_flow() -> None:
    """Test complete session flow from start to end."""
    sm = SessionStateMachine()

    # Start session
    assert sm.current_state == SessionState.IDLE
    sm.transition_to(SessionState.PROBLEM_PRESENTED)

    # Submit code
    assert sm.can_submit_code() is True
    sm.transition_to(SessionState.EVALUATING)

    # Tests complete
    sm.transition_to(SessionState.AWAITING_ACTION)

    # Request hint
    assert sm.can_request_hint() is True
    sm.transition_to(SessionState.AWAITING_ACTION)  # Hint doesn't change state

    # Submit again
    sm.transition_to(SessionState.EVALUATING)
    sm.transition_to(SessionState.AWAITING_ACTION)

    # End session
    sm.transition_to(SessionState.DONE)
    assert sm.is_done() is True


def test_repr() -> None:
    """Test string representation."""
    sm = SessionStateMachine()
    repr_str = repr(sm)
    assert "SessionStateMachine" in repr_str
    assert "idle" in repr_str.lower()
