"""Session state machine for managing interview flow.

States: IDLE → PROBLEM_PRESENTED → EVALUATING → AWAITING_ACTION → DONE

Transitions are validated and enforced by this state machine.
"""

from vo_sim.schemas import SessionState


class InvalidTransitionError(Exception):
    """Raised when an invalid state transition is attempted."""

    pass


class SessionStateMachine:
    """Manages session state transitions.

    Valid transitions:
    - IDLE → PROBLEM_PRESENTED (start)
    - PROBLEM_PRESENTED → EVALUATING (submit)
    - EVALUATING → AWAITING_ACTION (evaluation complete)
    - AWAITING_ACTION → EVALUATING (submit again)
    - AWAITING_ACTION → AWAITING_ACTION (hint - no change)
    - any state → DONE (end)

    Example:
        >>> sm = SessionStateMachine()
        >>> sm.current_state
        SessionState.IDLE
        >>> sm.transition_to(SessionState.PROBLEM_PRESENTED)
        >>> sm.current_state
        SessionState.PROBLEM_PRESENTED
    """

    # Define valid transitions: current_state → [allowed_next_states]
    _VALID_TRANSITIONS = {
        SessionState.IDLE: [SessionState.PROBLEM_PRESENTED, SessionState.DONE],
        SessionState.PROBLEM_PRESENTED: [SessionState.EVALUATING, SessionState.DONE],
        SessionState.EVALUATING: [SessionState.AWAITING_ACTION, SessionState.DONE],
        SessionState.AWAITING_ACTION: [
            SessionState.EVALUATING,
            SessionState.AWAITING_ACTION,  # hint command
            SessionState.DONE,
        ],
        SessionState.DONE: [],  # Terminal state - no transitions allowed
    }

    def __init__(self, initial_state: SessionState = SessionState.IDLE) -> None:
        """Initialize state machine.

        Args:
            initial_state: Starting state (default: IDLE)
        """
        self._current_state = initial_state

    @property
    def current_state(self) -> SessionState:
        """Get current state."""
        return self._current_state

    def can_transition_to(self, next_state: SessionState) -> bool:
        """Check if transition to next_state is valid.

        Args:
            next_state: Target state

        Returns:
            True if transition is allowed, False otherwise
        """
        allowed_states = self._VALID_TRANSITIONS.get(self._current_state, [])
        return next_state in allowed_states

    def transition_to(self, next_state: SessionState) -> None:
        """Transition to a new state.

        Args:
            next_state: Target state

        Raises:
            InvalidTransitionError: If transition is not allowed
        """
        if not self.can_transition_to(next_state):
            raise InvalidTransitionError(
                f"Cannot transition from {self._current_state.value} "
                f"to {next_state.value}"
            )

        self._current_state = next_state

    def reset(self) -> None:
        """Reset state machine to IDLE."""
        self._current_state = SessionState.IDLE

    def is_done(self) -> bool:
        """Check if state machine is in terminal state."""
        return self._current_state == SessionState.DONE

    def can_submit_code(self) -> bool:
        """Check if code submission is allowed in current state."""
        return self._current_state in [
            SessionState.PROBLEM_PRESENTED,
            SessionState.AWAITING_ACTION,
        ]

    def can_request_hint(self) -> bool:
        """Check if hint request is allowed in current state."""
        return self._current_state == SessionState.AWAITING_ACTION

    def __repr__(self) -> str:
        """String representation."""
        return f"SessionStateMachine(state={self._current_state.value})"
