"""Tests for session manager."""

import tempfile
from pathlib import Path

import pytest

from vo_sim.schemas import EventType, SessionState
from vo_sim.session.manager import (
    NoActiveSessionError,
    SessionAlreadyActiveError,
    SessionManager,
)
from vo_sim.session.state_machine import InvalidTransitionError
from vo_sim.session.storage import EventStore


@pytest.fixture
def temp_manager() -> SessionManager:
    """Create SessionManager with temporary storage."""
    with tempfile.TemporaryDirectory() as tmpdir:
        storage = EventStore(base_path=Path(tmpdir))
        active_file = Path(tmpdir) / "current_session.txt"
        yield SessionManager(storage=storage, active_session_file=active_file)


def test_manager_starts_with_no_active_session(temp_manager: SessionManager) -> None:
    """Test manager has no active session initially."""
    assert temp_manager.has_active_session() is False


def test_create_session_returns_session_id(temp_manager: SessionManager) -> None:
    """Test create_session returns a session ID."""
    session_id = temp_manager.create_session()
    assert session_id is not None
    assert isinstance(session_id, str)
    assert len(session_id) > 0


def test_create_session_sets_active_session(temp_manager: SessionManager) -> None:
    """Test create_session sets the session as active."""
    session_id = temp_manager.create_session()
    assert temp_manager.has_active_session() is True
    assert temp_manager.get_active_session_id() == session_id


def test_create_session_initializes_state(temp_manager: SessionManager) -> None:
    """Test create_session initializes state to PROBLEM_PRESENTED."""
    temp_manager.create_session()
    assert temp_manager.get_current_state() == SessionState.PROBLEM_PRESENTED


def test_create_session_emits_started_event(temp_manager: SessionManager) -> None:
    """Test create_session emits SESSION_STARTED event."""
    temp_manager.create_session()
    events = temp_manager.get_session_events()

    assert len(events) == 1
    assert events[0].event_type == EventType.SESSION_STARTED
    assert events[0].payload["problem_id"] == "lru_cache"


def test_create_session_raises_if_already_active(temp_manager: SessionManager) -> None:
    """Test creating session when one is active raises error."""
    temp_manager.create_session()

    with pytest.raises(SessionAlreadyActiveError) as exc_info:
        temp_manager.create_session()

    assert "already active" in str(exc_info.value).lower()


def test_end_session_clears_active_session(temp_manager: SessionManager) -> None:
    """Test end_session clears the active session."""
    temp_manager.create_session()
    temp_manager.end_session()

    assert temp_manager.has_active_session() is False


def test_end_session_emits_ended_event(temp_manager: SessionManager) -> None:
    """Test end_session emits SESSION_ENDED event."""
    session_id = temp_manager.create_session()
    temp_manager.end_session()

    # Load events directly from storage (session is no longer active)
    storage = temp_manager._storage
    events = storage.load_events(session_id)

    assert len(events) == 2
    assert events[1].event_type == EventType.SESSION_ENDED


def test_end_session_transitions_to_done(temp_manager: SessionManager) -> None:
    """Test end_session transitions state to DONE."""
    session_id = temp_manager.create_session()

    # Get state machine before ending
    sm = temp_manager.get_state_machine()

    temp_manager.end_session()

    # State machine should be in DONE state
    assert sm.current_state == SessionState.DONE


def test_end_session_raises_if_no_active_session(temp_manager: SessionManager) -> None:
    """Test ending session when none is active raises error."""
    with pytest.raises(NoActiveSessionError) as exc_info:
        temp_manager.end_session()

    assert "no active session" in str(exc_info.value).lower()


def test_get_active_session_id_raises_if_no_session(
    temp_manager: SessionManager,
) -> None:
    """Test getting session ID when none is active raises error."""
    with pytest.raises(NoActiveSessionError):
        temp_manager.get_active_session_id()


def test_get_current_state_raises_if_no_session(temp_manager: SessionManager) -> None:
    """Test getting state when no session is active raises error."""
    with pytest.raises(NoActiveSessionError):
        temp_manager.get_current_state()


def test_transition_to_changes_state(temp_manager: SessionManager) -> None:
    """Test transition_to changes the state."""
    temp_manager.create_session()

    # Start in PROBLEM_PRESENTED
    assert temp_manager.get_current_state() == SessionState.PROBLEM_PRESENTED

    # Transition to EVALUATING
    temp_manager.transition_to(SessionState.EVALUATING)
    assert temp_manager.get_current_state() == SessionState.EVALUATING


def test_transition_to_validates_transitions(temp_manager: SessionManager) -> None:
    """Test transition_to validates state transitions."""
    temp_manager.create_session()

    # Cannot go directly from PROBLEM_PRESENTED to AWAITING_ACTION
    with pytest.raises(InvalidTransitionError):
        temp_manager.transition_to(SessionState.AWAITING_ACTION)


def test_transition_to_raises_if_no_session(temp_manager: SessionManager) -> None:
    """Test transition_to raises error if no session is active."""
    with pytest.raises(NoActiveSessionError):
        temp_manager.transition_to(SessionState.EVALUATING)


def test_emit_event_appends_event(temp_manager: SessionManager) -> None:
    """Test emit_event appends event to storage."""
    temp_manager.create_session()

    temp_manager.emit_event(
        event_type=EventType.CODE_SUBMITTED,
        payload={"attempt": 1, "file_path": "solution.py"},
    )

    events = temp_manager.get_session_events()
    assert len(events) == 2
    assert events[1].event_type == EventType.CODE_SUBMITTED
    assert events[1].payload["attempt"] == 1


def test_emit_event_raises_if_no_session(temp_manager: SessionManager) -> None:
    """Test emit_event raises error if no session is active."""
    with pytest.raises(NoActiveSessionError):
        temp_manager.emit_event(EventType.CODE_SUBMITTED, {})


def test_get_session_events_returns_all_events(temp_manager: SessionManager) -> None:
    """Test get_session_events returns all events in order."""
    temp_manager.create_session()

    # Emit multiple events
    temp_manager.emit_event(EventType.CODE_SUBMITTED, {"attempt": 1})
    temp_manager.emit_event(EventType.EVAL_RESULT, {"passed": False})

    events = temp_manager.get_session_events()
    assert len(events) == 3
    assert events[0].event_type == EventType.SESSION_STARTED
    assert events[1].event_type == EventType.CODE_SUBMITTED
    assert events[2].event_type == EventType.EVAL_RESULT


def test_get_session_events_raises_if_no_session(temp_manager: SessionManager) -> None:
    """Test get_session_events raises error if no session is active."""
    with pytest.raises(NoActiveSessionError):
        temp_manager.get_session_events()


def test_get_state_machine_returns_state_machine(temp_manager: SessionManager) -> None:
    """Test get_state_machine returns the state machine."""
    temp_manager.create_session()
    sm = temp_manager.get_state_machine()

    assert sm is not None
    assert sm.current_state == SessionState.PROBLEM_PRESENTED


def test_get_state_machine_raises_if_no_session(temp_manager: SessionManager) -> None:
    """Test get_state_machine raises error if no session is active."""
    with pytest.raises(NoActiveSessionError):
        temp_manager.get_state_machine()


def test_session_persists_across_manager_instances(
    temp_manager: SessionManager,
) -> None:
    """Test active session persists across manager instances."""
    # Create session
    session_id = temp_manager.create_session()

    # Create new manager with same storage
    storage = temp_manager._storage
    active_file = temp_manager._active_session_file
    new_manager = SessionManager(storage=storage, active_session_file=active_file)

    # Session should still be active
    assert new_manager.has_active_session() is True
    assert new_manager.get_active_session_id() == session_id


def test_full_session_lifecycle(temp_manager: SessionManager) -> None:
    """Test complete session lifecycle."""
    # Create session
    session_id = temp_manager.create_session()
    assert temp_manager.has_active_session() is True
    assert temp_manager.get_current_state() == SessionState.PROBLEM_PRESENTED

    # Transition to evaluating
    temp_manager.transition_to(SessionState.EVALUATING)

    # Emit some events
    temp_manager.emit_event(EventType.CODE_SUBMITTED, {"attempt": 1})
    temp_manager.emit_event(EventType.EVAL_RESULT, {"passed": False})

    # Transition to awaiting action
    temp_manager.transition_to(SessionState.AWAITING_ACTION)

    # Get all events
    events = temp_manager.get_session_events()
    assert len(events) >= 3

    # End session
    temp_manager.end_session()
    assert temp_manager.has_active_session() is False

    # Verify events were persisted
    storage = temp_manager._storage
    persisted_events = storage.load_events(session_id)
    assert len(persisted_events) >= 4
    assert persisted_events[-1].event_type == EventType.SESSION_ENDED


def test_repr(temp_manager: SessionManager) -> None:
    """Test string representation."""
    repr_str = repr(temp_manager)
    assert "SessionManager" in repr_str
    assert "active_session=None" in repr_str

    temp_manager.create_session()
    repr_str = repr(temp_manager)
    assert "problem_presented" in repr_str.lower()
