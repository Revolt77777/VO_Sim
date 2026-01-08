"""Unit tests for Pydantic schemas.

Tests all enums, models, validation, and serialization.
"""

from datetime import datetime

import pytest
from pydantic import ValidationError

from vo_sim.schemas import (
    AgentContext,
    AgentDecision,
    Event,
    EventType,
    EvaluationResult,
    FailureType,
    SessionState,
    SessionSummary,
)


# ============================================================================
# Enum Tests
# ============================================================================


def test_session_state_enum() -> None:
    """Test SessionState enum values."""
    assert SessionState.IDLE == "idle"
    assert SessionState.PROBLEM_PRESENTED == "problem_presented"
    assert SessionState.EVALUATING == "evaluating"
    assert SessionState.AWAITING_ACTION == "awaiting_action"
    assert SessionState.DONE == "done"


def test_event_type_enum() -> None:
    """Test EventType enum values."""
    assert EventType.SESSION_STARTED == "SESSION_STARTED"
    assert EventType.CODE_SUBMITTED == "CODE_SUBMITTED"
    assert EventType.EVAL_RESULT == "EVAL_RESULT"
    assert EventType.HINT_REQUESTED == "HINT_REQUESTED"
    assert EventType.HINT_GIVEN == "HINT_GIVEN"
    assert EventType.AGENT_RESPONSE == "AGENT_RESPONSE"
    assert EventType.SESSION_ENDED == "SESSION_ENDED"


def test_failure_type_enum() -> None:
    """Test FailureType enum values."""
    assert FailureType.PASS == "pass"
    assert FailureType.PARTIAL_PASS == "partial_pass"
    assert FailureType.WRONG_ANSWER == "wrong_answer"
    assert FailureType.EXCEPTION == "exception"
    assert FailureType.WRONG_SIGNATURE == "wrong_signature"
    assert FailureType.IMPORT_ERROR == "import_error"


# ============================================================================
# Event Tests
# ============================================================================


def test_event_creation() -> None:
    """Test creating an Event instance."""
    event = Event(
        session_id="test-123",
        event_type=EventType.SESSION_STARTED,
        payload={"problem_id": "lru_cache"},
    )

    assert event.session_id == "test-123"
    assert event.event_type == EventType.SESSION_STARTED
    assert event.payload["problem_id"] == "lru_cache"
    assert isinstance(event.timestamp, datetime)


def test_event_json_serialization() -> None:
    """Test Event can be serialized to JSON."""
    event = Event(
        session_id="test-456",
        event_type=EventType.CODE_SUBMITTED,
        payload={"attempt": 1, "file_path": "/tmp/solution.py"},
    )

    json_str = event.model_dump_json()
    assert "test-456" in json_str
    assert "CODE_SUBMITTED" in json_str
    assert "attempt" in json_str


def test_event_json_deserialization() -> None:
    """Test Event can be deserialized from JSON."""
    json_data = """
    {
        "session_id": "test-789",
        "timestamp": "2026-01-06T12:00:00",
        "event_type": "SESSION_STARTED",
        "payload": {"test": "data"}
    }
    """

    event = Event.model_validate_json(json_data)
    assert event.session_id == "test-789"
    assert event.event_type == EventType.SESSION_STARTED
    assert event.payload["test"] == "data"


def test_event_requires_fields() -> None:
    """Test Event validation requires session_id, event_type, payload."""
    with pytest.raises(ValidationError):
        Event(event_type=EventType.SESSION_STARTED, payload={})  # Missing session_id


# ============================================================================
# EvaluationResult Tests
# ============================================================================


def test_evaluation_result_creation() -> None:
    """Test creating an EvaluationResult."""
    result = EvaluationResult(
        attempt_number=1,
        passed=False,
        failure_type=FailureType.WRONG_ANSWER,
        tests_passed=5,
        tests_failed=7,
        failing_tests=["test_eviction_order", "test_capacity_one"],
        exception=None,
        runtime_ms=145,
    )

    assert result.attempt_number == 1
    assert result.passed is False
    assert result.failure_type == FailureType.WRONG_ANSWER
    assert result.tests_passed == 5
    assert result.tests_failed == 7
    assert len(result.failing_tests) == 2
    assert result.exception is None
    assert result.runtime_ms == 145


def test_evaluation_result_with_exception() -> None:
    """Test EvaluationResult with exception traceback."""
    result = EvaluationResult(
        attempt_number=2,
        passed=False,
        failure_type=FailureType.EXCEPTION,
        tests_passed=0,
        tests_failed=12,
        failing_tests=["test_basic_get_miss"],
        exception="KeyError: 'key' at line 42",
        runtime_ms=50,
    )

    assert result.failure_type == FailureType.EXCEPTION
    assert result.exception == "KeyError: 'key' at line 42"


def test_evaluation_result_validation() -> None:
    """Test EvaluationResult validates field constraints."""
    # attempt_number must be >= 1
    with pytest.raises(ValidationError):
        EvaluationResult(
            attempt_number=0,  # Invalid!
            passed=False,
            failure_type=FailureType.WRONG_ANSWER,
            tests_passed=5,
            tests_failed=7,
            failing_tests=[],
            runtime_ms=100,
        )

    # tests_passed must be >= 0
    with pytest.raises(ValidationError):
        EvaluationResult(
            attempt_number=1,
            passed=False,
            failure_type=FailureType.WRONG_ANSWER,
            tests_passed=-1,  # Invalid!
            tests_failed=7,
            failing_tests=[],
            runtime_ms=100,
        )


def test_evaluation_result_json_round_trip() -> None:
    """Test EvaluationResult JSON serialization and deserialization."""
    original = EvaluationResult(
        attempt_number=3,
        passed=True,
        failure_type=FailureType.PASS,
        tests_passed=12,
        tests_failed=0,
        failing_tests=[],
        exception=None,
        runtime_ms=200,
    )

    # Serialize to JSON
    json_str = original.model_dump_json()

    # Deserialize back
    restored = EvaluationResult.model_validate_json(json_str)

    assert restored.attempt_number == original.attempt_number
    assert restored.passed == original.passed
    assert restored.failure_type == original.failure_type
    assert restored.tests_passed == original.tests_passed


# ============================================================================
# AgentContext Tests
# ============================================================================


def test_agent_context_creation() -> None:
    """Test creating AgentContext."""
    context = AgentContext(
        attempt_count=3,
        failure_history=[FailureType.WRONG_ANSWER, FailureType.WRONG_ANSWER],
        last_eval_result=None,
        hints_given=1,
        current_state=SessionState.AWAITING_ACTION,
    )

    assert context.attempt_count == 3
    assert len(context.failure_history) == 2
    assert context.hints_given == 1
    assert context.current_state == SessionState.AWAITING_ACTION


def test_agent_context_with_eval_result() -> None:
    """Test AgentContext with embedded EvaluationResult."""
    eval_result = EvaluationResult(
        attempt_number=2,
        passed=False,
        failure_type=FailureType.PARTIAL_PASS,
        tests_passed=7,
        tests_failed=5,
        failing_tests=["test_eviction_order"],
        runtime_ms=100,
    )

    context = AgentContext(
        attempt_count=2,
        failure_history=[FailureType.WRONG_ANSWER, FailureType.PARTIAL_PASS],
        last_eval_result=eval_result,
        hints_given=0,
        current_state=SessionState.AWAITING_ACTION,
    )

    assert context.last_eval_result is not None
    assert context.last_eval_result.failure_type == FailureType.PARTIAL_PASS


# ============================================================================
# AgentDecision Tests
# ============================================================================


def test_agent_decision_give_hint() -> None:
    """Test AgentDecision for giving a hint."""
    decision = AgentDecision(
        action="give_hint",
        hint_level=2,
        feedback_context=None,
    )

    assert decision.action == "give_hint"
    assert decision.hint_level == 2
    assert decision.feedback_context is None


def test_agent_decision_give_feedback() -> None:
    """Test AgentDecision for giving feedback."""
    decision = AgentDecision(
        action="give_feedback",
        hint_level=None,
        feedback_context={"failure_type": "wrong_answer", "primary_issue": "eviction"},
    )

    assert decision.action == "give_feedback"
    assert decision.hint_level is None
    assert decision.feedback_context["failure_type"] == "wrong_answer"


def test_agent_decision_hint_level_validation() -> None:
    """Test hint_level must be 1-4."""
    # Valid hint levels
    AgentDecision(action="give_hint", hint_level=1)
    AgentDecision(action="give_hint", hint_level=4)

    # Invalid hint levels
    with pytest.raises(ValidationError):
        AgentDecision(action="give_hint", hint_level=0)  # Too low

    with pytest.raises(ValidationError):
        AgentDecision(action="give_hint", hint_level=5)  # Too high


# ============================================================================
# SessionSummary Tests
# ============================================================================


def test_session_summary_creation() -> None:
    """Test creating a SessionSummary."""
    summary = SessionSummary(
        session_id="550e8400-e29b-41d4-a716-446655440000",
        outcome="success",
        total_attempts=3,
        final_tests_passed=12,
        final_tests_failed=0,
        hints_used=2,
        duration_seconds=900,
    )

    assert summary.outcome == "success"
    assert summary.total_attempts == 3
    assert summary.final_tests_passed == 12
    assert summary.hints_used == 2
    assert summary.duration_seconds == 900


def test_session_summary_failed_outcome() -> None:
    """Test SessionSummary for failed session."""
    summary = SessionSummary(
        session_id="test-failed",
        outcome="gave_up",
        total_attempts=5,
        final_tests_passed=5,
        final_tests_failed=7,
        hints_used=3,
        duration_seconds=1200,
    )

    assert summary.outcome == "gave_up"
    assert summary.final_tests_passed < summary.final_tests_failed