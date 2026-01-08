"""Pydantic models for all data structures in VO_Sim.

This module defines:
- Enums: SessionState, EventType, FailureType
- Models: Event, EvaluationResult, and other data structures

All models use Pydantic v2 for validation and serialization.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Enums
# ============================================================================


class SessionState(str, Enum):
    """Session state machine states.

    States:
    - IDLE: No active session
    - PROBLEM_PRESENTED: Problem shown, awaiting code submission
    - EVALUATING: Running tests on submitted code
    - AWAITING_ACTION: Tests complete, awaiting next command (submit/hint/end)
    - DONE: Session ended
    """

    IDLE = "idle"
    PROBLEM_PRESENTED = "problem_presented"
    EVALUATING = "evaluating"
    AWAITING_ACTION = "awaiting_action"
    DONE = "done"


class EventType(str, Enum):
    """Event types for session logging.

    All events that can occur during an interview session.
    """

    SESSION_STARTED = "SESSION_STARTED"
    CODE_SUBMITTED = "CODE_SUBMITTED"
    EVAL_RESULT = "EVAL_RESULT"
    HINT_REQUESTED = "HINT_REQUESTED"
    HINT_GIVEN = "HINT_GIVEN"
    AGENT_RESPONSE = "AGENT_RESPONSE"
    SESSION_ENDED = "SESSION_ENDED"


class FailureType(str, Enum):
    """Classification of code evaluation failures.

    Hierarchy (from best to worst):
    - PASS: All tests passed (100%)
    - PARTIAL_PASS: 50-99% of tests passed
    - WRONG_ANSWER: 0-49% of tests passed, no exceptions
    - EXCEPTION: Runtime error during test execution
    - WRONG_SIGNATURE: Missing or incorrect methods (get, put, __init__)
    - IMPORT_ERROR: Failed to import user's code
    """

    PASS = "pass"
    PARTIAL_PASS = "partial_pass"
    WRONG_ANSWER = "wrong_answer"
    EXCEPTION = "exception"
    WRONG_SIGNATURE = "wrong_signature"
    IMPORT_ERROR = "import_error"


# ============================================================================
# Event Models
# ============================================================================


class Event(BaseModel):
    """Base event structure for session logging.

    All events are persisted as JSONL (one JSON object per line).
    Events are append-only and form a complete audit trail.

    Attributes:
        session_id: Unique session identifier (UUID)
        timestamp: When the event occurred (UTC)
        event_type: Type of event (SESSION_STARTED, CODE_SUBMITTED, etc.)
        payload: Event-specific data (varies by event type)

    Example:
        >>> event = Event(
        ...     session_id="550e8400-e29b-41d4-a716-446655440000",
        ...     event_type=EventType.SESSION_STARTED,
        ...     payload={"problem_id": "lru_cache"}
        ... )
        >>> event.model_dump_json()
    """

    session_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    event_type: EventType
    payload: dict[str, Any]

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "timestamp": "2026-01-06T12:00:00Z",
                "event_type": "SESSION_STARTED",
                "payload": {"problem_id": "lru_cache"},
            }
        }


# ============================================================================
# Evaluation Models
# ============================================================================


class EvaluationResult(BaseModel):
    """Result of code evaluation against test suite.

    Contains complete information about test execution:
    - Which tests passed/failed
    - Exception details if any
    - Performance metrics
    - Failure classification

    Attributes:
        attempt_number: Which submission attempt this is (1, 2, 3, ...)
        passed: True if all tests passed
        failure_type: Classification of failure (PASS, WRONG_ANSWER, etc.)
        tests_passed: Number of tests that passed
        tests_failed: Number of tests that failed
        failing_tests: List of test identifiers that failed
        exception: Exception traceback if any (None if no exception)
        runtime_ms: Total runtime in milliseconds

    Example:
        >>> result = EvaluationResult(
        ...     attempt_number=1,
        ...     passed=False,
        ...     failure_type=FailureType.WRONG_ANSWER,
        ...     tests_passed=5,
        ...     tests_failed=7,
        ...     failing_tests=["test_eviction_order", "test_capacity_one"],
        ...     exception=None,
        ...     runtime_ms=145
        ... )
    """

    attempt_number: int = Field(ge=1, description="Submission attempt number")
    passed: bool = Field(description="True if all tests passed")
    failure_type: FailureType = Field(description="Classification of result")
    tests_passed: int = Field(ge=0, description="Number of passing tests")
    tests_failed: int = Field(ge=0, description="Number of failing tests")
    failing_tests: list[str] = Field(
        default_factory=list, description="Test IDs that failed"
    )
    exception: str | None = Field(
        default=None, description="Exception traceback if any"
    )
    runtime_ms: int = Field(ge=0, description="Total runtime in milliseconds")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "attempt_number": 1,
                "passed": False,
                "failure_type": "wrong_answer",
                "tests_passed": 5,
                "tests_failed": 7,
                "failing_tests": ["test_eviction_order", "test_capacity_one"],
                "exception": None,
                "runtime_ms": 145,
            }
        }


# ============================================================================
# Agent Decision Models
# ============================================================================


class AgentContext(BaseModel):
    """Context gathered during the 'Observe' phase of agent loop.

    The agent observes the current session state to make decisions.

    Attributes:
        attempt_count: Total number of code submissions
        failure_history: List of FailureType from all attempts
        last_eval_result: Most recent evaluation result (None if no submissions)
        hints_given: Number of hints already provided
        current_state: Current session state
    """

    attempt_count: int = Field(ge=0)
    failure_history: list[FailureType] = Field(default_factory=list)
    last_eval_result: EvaluationResult | None = None
    hints_given: int = Field(ge=0)
    current_state: SessionState


class AgentDecision(BaseModel):
    """Decision made during the 'Decide' phase of agent loop.

    The agent decides what action to take based on observed context.

    Attributes:
        action: Action to take (give_hint, give_feedback, end_session, etc.)
        hint_level: If action is give_hint, which level (1-4)
        feedback_context: If action is give_feedback, context for LLM
    """

    action: str = Field(
        description="Action to take: give_hint, give_feedback, end_session"
    )
    hint_level: int | None = Field(
        default=None, ge=1, le=4, description="Hint level (1-4) if giving hint"
    )
    feedback_context: dict[str, Any] | None = Field(
        default=None, description="Context for feedback generation"
    )


# ============================================================================
# Session Summary
# ============================================================================


class SessionSummary(BaseModel):
    """Summary generated at end of interview session.

    Provides high-level statistics and outcome.

    Attributes:
        session_id: Session identifier
        outcome: Final outcome (success, partial_success, gave_up, etc.)
        total_attempts: Number of code submissions
        final_tests_passed: Tests passed in final attempt
        final_tests_failed: Tests failed in final attempt
        hints_used: Number of hints requested
        duration_seconds: Total session duration
    """

    session_id: str
    outcome: str = Field(description="success, partial_success, gave_up, timeout")
    total_attempts: int = Field(ge=0)
    final_tests_passed: int = Field(ge=0)
    final_tests_failed: int = Field(ge=0)
    hints_used: int = Field(ge=0)
    duration_seconds: int = Field(ge=0)
