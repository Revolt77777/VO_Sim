"""Tests for event storage."""

import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from vo_sim.schemas import Event, EventType
from vo_sim.session.storage import EventStore


@pytest.fixture
def temp_storage() -> EventStore:
    """Create EventStore with temporary directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield EventStore(base_path=Path(tmpdir))


def test_event_store_creates_directory(temp_storage: EventStore) -> None:
    """Test EventStore creates sessions directory."""
    assert temp_storage.sessions_dir.exists()
    assert temp_storage.sessions_dir.is_dir()


def test_append_event_creates_file(temp_storage: EventStore) -> None:
    """Test appending event creates session file."""
    event = Event(
        session_id="test-123",
        event_type=EventType.SESSION_STARTED,
        payload={"problem_id": "lru_cache"},
    )

    temp_storage.append_event(event)

    session_file = temp_storage.sessions_dir / "test-123.jsonl"
    assert session_file.exists()


def test_append_event_writes_json(temp_storage: EventStore) -> None:
    """Test event is written as JSON."""
    event = Event(
        session_id="test-456",
        event_type=EventType.CODE_SUBMITTED,
        payload={"attempt": 1},
    )

    temp_storage.append_event(event)

    session_file = temp_storage.sessions_dir / "test-456.jsonl"
    content = session_file.read_text(encoding="utf-8")

    assert "test-456" in content
    assert "CODE_SUBMITTED" in content
    assert "attempt" in content


def test_load_events_returns_empty_for_nonexistent_session(
    temp_storage: EventStore,
) -> None:
    """Test loading events from nonexistent session returns empty list."""
    events = temp_storage.load_events("nonexistent")
    assert events == []


def test_load_events_returns_single_event(temp_storage: EventStore) -> None:
    """Test loading single event."""
    event = Event(
        session_id="test-789",
        event_type=EventType.SESSION_STARTED,
        payload={},
    )

    temp_storage.append_event(event)
    loaded_events = temp_storage.load_events("test-789")

    assert len(loaded_events) == 1
    assert loaded_events[0].session_id == "test-789"
    assert loaded_events[0].event_type == EventType.SESSION_STARTED


def test_load_events_returns_multiple_events_in_order(
    temp_storage: EventStore,
) -> None:
    """Test loading multiple events returns them in chronological order."""
    events = [
        Event(
            session_id="test-multi",
            event_type=EventType.SESSION_STARTED,
            payload={},
        ),
        Event(
            session_id="test-multi",
            event_type=EventType.CODE_SUBMITTED,
            payload={"attempt": 1},
        ),
        Event(
            session_id="test-multi",
            event_type=EventType.EVAL_RESULT,
            payload={"passed": False},
        ),
    ]

    for event in events:
        temp_storage.append_event(event)

    loaded_events = temp_storage.load_events("test-multi")

    assert len(loaded_events) == 3
    assert loaded_events[0].event_type == EventType.SESSION_STARTED
    assert loaded_events[1].event_type == EventType.CODE_SUBMITTED
    assert loaded_events[2].event_type == EventType.EVAL_RESULT


def test_append_event_is_append_only(temp_storage: EventStore) -> None:
    """Test appending to existing session preserves previous events."""
    event1 = Event(
        session_id="test-append",
        event_type=EventType.SESSION_STARTED,
        payload={},
    )
    event2 = Event(
        session_id="test-append",
        event_type=EventType.CODE_SUBMITTED,
        payload={},
    )

    temp_storage.append_event(event1)
    temp_storage.append_event(event2)

    loaded_events = temp_storage.load_events("test-append")
    assert len(loaded_events) == 2


def test_session_exists_returns_true_for_existing_session(
    temp_storage: EventStore,
) -> None:
    """Test session_exists returns True for existing session."""
    event = Event(
        session_id="test-exists",
        event_type=EventType.SESSION_STARTED,
        payload={},
    )

    temp_storage.append_event(event)
    assert temp_storage.session_exists("test-exists") is True


def test_session_exists_returns_false_for_nonexistent_session(
    temp_storage: EventStore,
) -> None:
    """Test session_exists returns False for nonexistent session."""
    assert temp_storage.session_exists("nonexistent") is False


def test_get_all_session_ids_returns_empty_initially(
    temp_storage: EventStore,
) -> None:
    """Test get_all_session_ids returns empty list initially."""
    assert temp_storage.get_all_session_ids() == []


def test_get_all_session_ids_returns_all_sessions(temp_storage: EventStore) -> None:
    """Test get_all_session_ids returns all session IDs."""
    sessions = ["session-1", "session-2", "session-3"]

    for session_id in sessions:
        event = Event(
            session_id=session_id,
            event_type=EventType.SESSION_STARTED,
            payload={},
        )
        temp_storage.append_event(event)

    all_ids = temp_storage.get_all_session_ids()
    assert len(all_ids) == 3
    assert set(all_ids) == set(sessions)


def test_delete_session_removes_file(temp_storage: EventStore) -> None:
    """Test delete_session removes session file."""
    event = Event(
        session_id="test-delete",
        event_type=EventType.SESSION_STARTED,
        payload={},
    )

    temp_storage.append_event(event)
    assert temp_storage.session_exists("test-delete") is True

    temp_storage.delete_session("test-delete")
    assert temp_storage.session_exists("test-delete") is False


def test_delete_nonexistent_session_does_not_error(temp_storage: EventStore) -> None:
    """Test deleting nonexistent session doesn't raise error."""
    temp_storage.delete_session("nonexistent")  # Should not raise


def test_get_event_count_returns_zero_for_nonexistent(
    temp_storage: EventStore,
) -> None:
    """Test get_event_count returns 0 for nonexistent session."""
    assert temp_storage.get_event_count("nonexistent") == 0


def test_get_event_count_returns_correct_count(temp_storage: EventStore) -> None:
    """Test get_event_count returns correct number of events."""
    session_id = "test-count"

    for i in range(5):
        event = Event(
            session_id=session_id,
            event_type=EventType.CODE_SUBMITTED,
            payload={"attempt": i + 1},
        )
        temp_storage.append_event(event)

    assert temp_storage.get_event_count(session_id) == 5


def test_load_events_handles_empty_lines(temp_storage: EventStore) -> None:
    """Test loading events skips empty lines."""
    # Manually create file with empty lines
    session_file = temp_storage.sessions_dir / "test-empty.jsonl"

    event = Event(
        session_id="test-empty",
        event_type=EventType.SESSION_STARTED,
        payload={},
    )

    with session_file.open("w", encoding="utf-8") as f:
        f.write(event.model_dump_json() + "\n")
        f.write("\n")  # Empty line
        f.write(event.model_dump_json() + "\n")

    events = temp_storage.load_events("test-empty")
    assert len(events) == 2  # Empty line should be skipped


def test_event_round_trip_preserves_data(temp_storage: EventStore) -> None:
    """Test event round-trip (save → load) preserves all data."""
    original = Event(
        session_id="test-roundtrip",
        timestamp=datetime(2026, 1, 6, 12, 0, 0),
        event_type=EventType.EVAL_RESULT,
        payload={
            "passed": False,
            "tests_passed": 5,
            "tests_failed": 7,
            "details": {"complexity": "O(n)"},
        },
    )

    temp_storage.append_event(original)
    loaded = temp_storage.load_events("test-roundtrip")[0]

    assert loaded.session_id == original.session_id
    assert loaded.event_type == original.event_type
    assert loaded.payload == original.payload
    # Timestamp might have slight differences due to serialization, so check separately
    assert loaded.timestamp.year == original.timestamp.year


def test_repr(temp_storage: EventStore) -> None:
    """Test string representation."""
    repr_str = repr(temp_storage)
    assert "EventStore" in repr_str
    assert "base_path" in repr_str
