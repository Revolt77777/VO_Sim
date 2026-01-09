"""Session lifecycle management.

Manages interview sessions by coordinating:
- State machine (state transitions)
- Event storage (persistence)
- Active session tracking
"""

from pathlib import Path
from uuid import uuid4

from vo_sim.schemas import Event, EventType, SessionState
from vo_sim.session.state_machine import SessionStateMachine
from vo_sim.session.storage import EventStore


class NoActiveSessionError(Exception):
    """Raised when an operation requires an active session but none exists."""

    pass


class SessionAlreadyActiveError(Exception):
    """Raised when trying to start a new session while one is already active."""

    pass


class SessionManager:
    """Manages interview session lifecycle.

    Responsibilities:
    - Create new sessions with unique IDs
    - Track active session
    - Coordinate state machine and event storage
    - Emit events for all state changes

    Example:
        >>> manager = SessionManager()
        >>> session_id = manager.create_session()
        >>> manager.has_active_session()
        True
        >>> manager.get_current_state()
        SessionState.PROBLEM_PRESENTED
    """

    def __init__(
        self,
        storage: EventStore | None = None,
        active_session_file: Path | None = None,
    ) -> None:
        """Initialize session manager.

        Args:
            storage: EventStore instance (creates default if None)
            active_session_file: Path to file tracking active session
                                (default: ~/.vo_sim/current_session.txt)
        """
        self._storage = storage or EventStore()
        self._active_session_file = active_session_file or (
            self._storage.base_path / "current_session.txt"
        )

        # Load active session from file if exists
        self._active_session_id: str | None = self._load_active_session()
        self._state_machine: SessionStateMachine | None = None

        # If active session exists, restore state machine
        if self._active_session_id:
            self._restore_state_machine()

    def create_session(self) -> str:
        """Create a new interview session.

        Raises:
            SessionAlreadyActiveError: If a session is already active

        Returns:
            Session ID (UUID)
        """
        if self.has_active_session():
            raise SessionAlreadyActiveError(
                f"Session {self._active_session_id} is already active. "
                "End it with end_session() first."
            )

        # Generate new session ID
        session_id = str(uuid4())

        # Initialize state machine
        self._state_machine = SessionStateMachine()

        # Emit SESSION_STARTED event
        event = Event(
            session_id=session_id,
            event_type=EventType.SESSION_STARTED,
            payload={"problem_id": "lru_cache"},
        )
        self._storage.append_event(event)

        # Transition to PROBLEM_PRESENTED
        self._state_machine.transition_to(SessionState.PROBLEM_PRESENTED)

        # Set as active session
        self._active_session_id = session_id
        self._save_active_session(session_id)

        return session_id

    def end_session(self) -> None:
        """End the current interview session.

        Raises:
            NoActiveSessionError: If no session is active
        """
        if not self.has_active_session():
            raise NoActiveSessionError("No active session to end")

        # Emit SESSION_ENDED event
        event = Event(
            session_id=self._active_session_id,  # type: ignore
            event_type=EventType.SESSION_ENDED,
            payload={
                "final_state": self._state_machine.current_state.value,  # type: ignore
            },
        )
        self._storage.append_event(event)

        # Transition to DONE
        self._state_machine.transition_to(SessionState.DONE)  # type: ignore

        # Clear active session
        self._active_session_id = None
        self._state_machine = None
        self._clear_active_session()

    def has_active_session(self) -> bool:
        """Check if there is an active session.

        Returns:
            True if session is active, False otherwise
        """
        return self._active_session_id is not None

    def get_active_session_id(self) -> str:
        """Get the active session ID.

        Raises:
            NoActiveSessionError: If no session is active

        Returns:
            Active session ID
        """
        if not self.has_active_session():
            raise NoActiveSessionError("No active session")

        return self._active_session_id  # type: ignore

    def get_current_state(self) -> SessionState:
        """Get current session state.

        Raises:
            NoActiveSessionError: If no session is active

        Returns:
            Current session state
        """
        if not self.has_active_session():
            raise NoActiveSessionError("No active session")

        return self._state_machine.current_state  # type: ignore

    def transition_to(self, next_state: SessionState) -> None:
        """Transition to a new state.

        Raises:
            NoActiveSessionError: If no session is active
            InvalidTransitionError: If transition is not valid

        Args:
            next_state: Target state
        """
        if not self.has_active_session():
            raise NoActiveSessionError("No active session")

        self._state_machine.transition_to(next_state)  # type: ignore

    def emit_event(self, event_type: EventType, payload: dict) -> None:
        """Emit an event for the active session.

        Raises:
            NoActiveSessionError: If no session is active

        Args:
            event_type: Type of event
            payload: Event payload data
        """
        if not self.has_active_session():
            raise NoActiveSessionError("No active session")

        event = Event(
            session_id=self._active_session_id,  # type: ignore
            event_type=event_type,
            payload=payload,
        )
        self._storage.append_event(event)

    def get_session_events(self) -> list[Event]:
        """Get all events for the active session.

        Raises:
            NoActiveSessionError: If no session is active

        Returns:
            List of events in chronological order
        """
        if not self.has_active_session():
            raise NoActiveSessionError("No active session")

        return self._storage.load_events(self._active_session_id)  # type: ignore

    def get_state_machine(self) -> SessionStateMachine:
        """Get the state machine for the active session.

        Raises:
            NoActiveSessionError: If no session is active

        Returns:
            Active session's state machine
        """
        if not self.has_active_session():
            raise NoActiveSessionError("No active session")

        return self._state_machine  # type: ignore

    def _load_active_session(self) -> str | None:
        """Load active session ID from file.

        Returns:
            Session ID if file exists, None otherwise
        """
        if self._active_session_file.exists():
            session_id = self._active_session_file.read_text(encoding="utf-8").strip()
            # Verify session actually exists
            if session_id and self._storage.session_exists(session_id):
                return session_id
        return None

    def _save_active_session(self, session_id: str) -> None:
        """Save active session ID to file.

        Args:
            session_id: Session ID to save
        """
        self._active_session_file.parent.mkdir(parents=True, exist_ok=True)
        self._active_session_file.write_text(session_id, encoding="utf-8")

    def _clear_active_session(self) -> None:
        """Clear active session file."""
        if self._active_session_file.exists():
            self._active_session_file.unlink()

    def _restore_state_machine(self) -> None:
        """Restore state machine from event history.

        Reconstructs state by replaying events.
        """
        if not self._active_session_id:
            return

        # For now, just initialize to AWAITING_ACTION
        # (In a full implementation, we'd replay events to determine exact state)
        self._state_machine = SessionStateMachine(
            initial_state=SessionState.AWAITING_ACTION
        )

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"SessionManager(active_session={self._active_session_id}, "
            f"state={self._state_machine.current_state.value if self._state_machine else None})"
        )
