"""Event storage using JSONL format.

Events are stored as append-only JSONL files in ~/.vo_sim/sessions/
Each session has its own file: {session_id}.jsonl
"""

from pathlib import Path

from vo_sim.schemas import Event


class EventStore:
    """Manages event persistence using JSONL format.

    Storage location: ~/.vo_sim/sessions/{session_id}.jsonl

    Events are append-only - never modified or deleted.
    Full session state can be reconstructed by replaying events.

    Example:
        >>> store = EventStore()
        >>> event = Event(session_id="abc", event_type=EventType.SESSION_STARTED, payload={})
        >>> store.append_event(event)
        >>> events = store.load_events("abc")
        >>> len(events)
        1
    """

    def __init__(self, base_path: Path | None = None) -> None:
        """Initialize event store.

        Args:
            base_path: Base directory for storage. Defaults to ~/.vo_sim/
        """
        if base_path is None:
            base_path = Path.home() / ".vo_sim"

        self.base_path = base_path
        self.sessions_dir = base_path / "sessions"
        self.sessions_dir.mkdir(parents=True, exist_ok=True)

    def append_event(self, event: Event) -> None:
        """Append event to session log.

        Creates session file if it doesn't exist.
        Events are appended as JSONL (one JSON object per line).

        Args:
            event: Event to append
        """
        session_file = self._get_session_file(event.session_id)

        # Append event as JSON line
        with session_file.open("a", encoding="utf-8") as f:
            f.write(event.model_dump_json() + "\n")

    def load_events(self, session_id: str) -> list[Event]:
        """Load all events for a session.

        Args:
            session_id: Session UUID

        Returns:
            List of events in chronological order (empty list if session doesn't exist)
        """
        session_file = self._get_session_file(session_id)

        if not session_file.exists():
            return []

        events = []
        with session_file.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:  # Skip empty lines
                    events.append(Event.model_validate_json(line))

        return events

    def session_exists(self, session_id: str) -> bool:
        """Check if a session file exists.

        Args:
            session_id: Session UUID

        Returns:
            True if session file exists, False otherwise
        """
        session_file = self._get_session_file(session_id)
        return session_file.exists()

    def get_all_session_ids(self) -> list[str]:
        """Get list of all session IDs.

        Returns:
            List of session IDs (UUIDs without .jsonl extension)
        """
        session_files = self.sessions_dir.glob("*.jsonl")
        return [f.stem for f in session_files]

    def delete_session(self, session_id: str) -> None:
        """Delete a session file.

        Warning: This is destructive! Events cannot be recovered.

        Args:
            session_id: Session UUID
        """
        session_file = self._get_session_file(session_id)
        if session_file.exists():
            session_file.unlink()

    def get_event_count(self, session_id: str) -> int:
        """Get number of events in a session.

        Args:
            session_id: Session UUID

        Returns:
            Number of events (0 if session doesn't exist)
        """
        return len(self.load_events(session_id))

    def _get_session_file(self, session_id: str) -> Path:
        """Get path to session file.

        Args:
            session_id: Session UUID

        Returns:
            Path to {session_id}.jsonl
        """
        return self.sessions_dir / f"{session_id}.jsonl"

    def __repr__(self) -> str:
        """String representation."""
        return f"EventStore(base_path={self.base_path})"
