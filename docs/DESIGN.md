# VO_Sim v1 — Complete Design Document

**Version**: 1.0
**Target**: Python 3.11+
**Author**: Student Project — AI Agent Learning & SDE Internship Prep
**Agent Level**: L3-L4 (Autonomous agent with planning, state management, and tool use)

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Learning Objectives](#learning-objectives)
3. [System Architecture](#system-architecture)
4. [Tech Stack](#tech-stack)
5. [State Machine](#state-machine)
6. [Event Schema](#event-schema)
7. [Evaluation System](#evaluation-system)
8. [Agent Decision Engine](#agent-decision-engine)
9. [LLM Interface](#llm-interface)
10. [Persistence Layer](#persistence-layer)
11. [CLI Interface](#cli-interface)
12. [Error Handling](#error-handling)
13. [Testing Strategy](#testing-strategy)
14. [Implementation Roadmap](#implementation-roadmap)

---

## Project Overview

**VO_Sim** (Virtual Onsite Simulator) is a CLI-based, stateful AI interview agent that conducts coding interviews. v1 focuses on a single problem: **LRU Cache**.

### What Makes This L3-L4 Agentic?

- **L3 Autonomy**: Agent observes, decides, and acts independently based on policy
- **L4 Capabilities**: Multi-step reasoning, state management, tool use (code evaluator)
- **Deterministic Decision Making**: Rule-based policies (testable, explainable)
- **Memory & Context**: Full session history with replay capability
- **Adaptive Behavior**: Dynamic hint escalation based on failure patterns

### Core Principles

1. **Determinism First**: Correctness judged by tests, not LLM opinion
2. **Agentic Behavior via Policy**: Explicit, rule-based, testable decisions
3. **Stateful & Replayable**: Every session is an append-only event log
4. **LLM-Optional**: Works with mock LLM (no API keys required)

---

## Learning Objectives

This project demonstrates:

- **Agent Architecture**: Observe-Decide-Act loop with persistent memory
- **State Management**: Formal state machines with event sourcing
- **Policy Design**: Deterministic decision rules for adaptive behavior
- **Code Evaluation**: Safe sandboxed execution with classification
- **Clean Architecture**: Separation of concerns (CLI, Agent, Evaluator, Persistence)
- **Modern Python**: Type hints, Pydantic validation, async-ready design
- **Production Practices**: Logging, error handling, testing, CI/CD

**Resume Value**: Showcases system design, AI agent development, and software engineering rigor.

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│                    (Click Commands)                          │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                    Interview Agent                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Observe    │─▶│    Decide    │─▶│     Act      │      │
│  │  (Context)   │  │   (Policy)   │  │  (Generate)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└────────────┬────────────────────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────────────────┐
│                  Supporting Systems                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Evaluator   │  │ Persistence  │  │  LLM Client  │      │
│  │  (Sandbox)   │  │   (JSONL)    │  │   (Mock)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

### Module Responsibilities

| Module | Responsibility | Key Classes |
|--------|---------------|-------------|
| `cli.py` | User interaction, command routing | `ClickApp` |
| `agent/interview_agent.py` | Core agent loop (observe-decide-act) | `InterviewAgent` |
| `agent/policy.py` | Decision rules, hint escalation | `HintPolicy`, `FeedbackPolicy` |
| `agent/llm.py` | LLM interface + mock implementation | `LLMClient`, `MockLLM` |
| `evaluator/runner.py` | Sandboxed code execution | `CodeRunner` |
| `evaluator/test_suite.py` | LRU Cache test cases | `LRUTestSuite` |
| `evaluator/classifier.py` | Failure type detection | `FailureClassifier` |
| `session/state_machine.py` | State transitions, validation | `SessionStateMachine` |
| `session/manager.py` | Session lifecycle management | `SessionManager` |
| `session/persistence.py` | Event storage (JSONL) | `EventStore` |
| `schemas.py` | Pydantic models for all data | `Event`, `EvaluationResult`, etc. |

---

## Tech Stack

### Core Dependencies

```toml
[tool.poetry.dependencies]
python = "^3.11"
click = "^8.1.7"          # CLI framework
rich = "^13.7.0"          # Beautiful terminal output
pydantic = "^2.5.0"       # Data validation
```

### Development Dependencies

```toml
[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-cov = "^4.1.0"
mypy = "^1.7.0"
ruff = "^0.1.6"           # Fast linter & formatter
```

### Why These Choices?

- **Click**: Industry standard, decorator-based CLI (easy to test)
- **Rich**: Makes CLI output impressive (good for demos)
- **Pydantic v2**: Type safety + validation (prevents bugs)
- **Ruff**: 10-100x faster than flake8+black (modern tooling)

---

## State Machine

### States

```python
class SessionState(str, Enum):
    IDLE = "idle"                      # No active session
    PROBLEM_PRESENTED = "problem_presented"  # Problem shown, awaiting code
    EVALUATING = "evaluating"          # Running tests
    AWAITING_ACTION = "awaiting_action"  # Tests complete, awaiting next move
    DONE = "done"                      # Session ended
```

### State Transitions

```
IDLE
  │
  │ start
  ▼
PROBLEM_PRESENTED
  │
  │ submit
  ▼
EVALUATING
  │
  │ evaluation complete
  ▼
AWAITING_ACTION
  │
  ├──submit──▶ EVALUATING
  ├──hint────▶ AWAITING_ACTION (stays in state)
  ├──status──▶ AWAITING_ACTION (no state change)
  └──end─────▶ DONE
```

### State Transition Rules

| Current State | Command | Next State | Event Emitted |
|--------------|---------|------------|---------------|
| `IDLE` | `start` | `PROBLEM_PRESENTED` | `SESSION_STARTED` |
| `PROBLEM_PRESENTED` | `submit` | `EVALUATING` | `CODE_SUBMITTED` |
| `EVALUATING` | (auto) | `AWAITING_ACTION` | `EVAL_RESULT` |
| `AWAITING_ACTION` | `submit` | `EVALUATING` | `CODE_SUBMITTED` |
| `AWAITING_ACTION` | `hint` | `AWAITING_ACTION` | `HINT_REQUESTED`, `HINT_GIVEN` |
| `AWAITING_ACTION` | `status` | `AWAITING_ACTION` | None (read-only) |
| `AWAITING_ACTION` | `end` | `DONE` | `SESSION_ENDED` |

**Invalid transitions raise**: `InvalidStateTransitionError`

---

## Event Schema

All events follow this structure:

```python
class Event(BaseModel):
    session_id: str          # UUID v4
    timestamp: datetime      # ISO-8601
    event_type: EventType    # Enum
    payload: dict[str, Any]  # Event-specific data
```

### Event Types & Payloads

#### 1. SESSION_STARTED

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-05T23:30:00.123456Z",
  "event_type": "SESSION_STARTED",
  "payload": {
    "problem_id": "lru_cache",
    "python_version": "3.11.5"
  }
}
```

#### 2. CODE_SUBMITTED

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-05T23:32:15.789012Z",
  "event_type": "CODE_SUBMITTED",
  "payload": {
    "attempt_number": 1,
    "file_path": "/home/user/lru_cache.py",
    "code_hash": "sha256:abcdef123456...",
    "line_count": 42
  }
}
```

**Note**: Full code is NOT stored in events (privacy + size). Only hash for deduplication.

#### 3. EVAL_RESULT

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-05T23:32:17.234567Z",
  "event_type": "EVAL_RESULT",
  "payload": {
    "attempt_number": 1,
    "passed": false,
    "failure_type": "WRONG_ANSWER",
    "tests_passed": 5,
    "tests_failed": 7,
    "failing_tests": [
      "test_eviction_order",
      "test_capacity_one",
      "test_update_existing"
    ],
    "exception": null,
    "runtime_ms": 145
  }
}
```

#### 4. HINT_REQUESTED

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-05T23:33:00.000000Z",
  "event_type": "HINT_REQUESTED",
  "payload": {
    "attempt_number": 1
  }
}
```

#### 5. HINT_GIVEN

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-05T23:33:01.500000Z",
  "event_type": "HINT_GIVEN",
  "payload": {
    "hint_level": 1,
    "hint_text": "What data structure maintains insertion order in Python?",
    "trigger_reason": "first_hint_request"
  }
}
```

#### 6. AGENT_RESPONSE

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-05T23:32:18.000000Z",
  "event_type": "AGENT_RESPONSE",
  "payload": {
    "response_type": "feedback",
    "message": "Your solution fails on eviction order tests. The LRU cache should remove the least recently used item when capacity is exceeded.",
    "metadata": {
      "failure_type": "WRONG_ANSWER",
      "primary_issue": "eviction_logic"
    }
  }
}
```

#### 7. SESSION_ENDED

```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2026-01-05T23:45:00.000000Z",
  "event_type": "SESSION_ENDED",
  "payload": {
    "outcome": "partial_success",
    "total_attempts": 4,
    "final_tests_passed": 10,
    "final_tests_failed": 2,
    "hints_used": 2,
    "duration_seconds": 900
  }
}
```

---

## Evaluation System

### LRU Cache Contract

User code MUST implement:

```python
class LRUCache:
    def __init__(self, capacity: int):
        """Initialize LRU cache with given capacity."""
        pass

    def get(self, key: int) -> int:
        """
        Return value for key if exists, else -1.
        Updates key as most recently used.
        """
        pass

    def put(self, key: int, value: int) -> None:
        """
        Set or update key-value pair.
        Evicts LRU item if at capacity.
        """
        pass
```

### Test Suite (12 Tests)

| Test ID | Category | Description |
|---------|----------|-------------|
| `test_basic_get_miss` | Basic | Get from empty cache returns -1 |
| `test_basic_put_get` | Basic | Put then get returns correct value |
| `test_update_existing` | Update | Updating existing key preserves order |
| `test_eviction_order_simple` | Eviction | LRU item evicted first |
| `test_eviction_order_complex` | Eviction | Multi-step eviction sequence |
| `test_get_updates_recency` | Recency | Get makes item most recent |
| `test_capacity_one` | Edge Case | Capacity of 1 works correctly |
| `test_capacity_large` | Edge Case | Capacity of 1000 |
| `test_repeated_operations` | Stress | 10,000 mixed operations |
| `test_all_same_key` | Edge Case | Repeatedly updating same key |
| `test_alternating_access` | Pattern | Access pattern: A, B, A, B... |
| `test_deterministic_random` | Randomized | Fixed seed: 100 random ops |

### Failure Classification

```python
class FailureType(str, Enum):
    PASS = "pass"                    # All tests passed
    PARTIAL_PASS = "partial_pass"    # ≥50% tests passed
    WRONG_ANSWER = "wrong_answer"    # <50% tests passed, no exceptions
    EXCEPTION = "exception"          # Runtime error during tests
    WRONG_SIGNATURE = "wrong_signature"  # Missing/incorrect methods
    IMPORT_ERROR = "import_error"    # Failed to import module
```

### Classification Rules

1. **IMPORT_ERROR**: Cannot import module or find `LRUCache` class
2. **WRONG_SIGNATURE**: Missing `__init__`, `get`, or `put` methods
3. **EXCEPTION**: Any unhandled exception during test execution
4. **PASS**: All 12 tests passed (100%)
5. **PARTIAL_PASS**: 6-11 tests passed (50-99%)
6. **WRONG_ANSWER**: 0-5 tests passed (0-49%)

### Code Execution Sandbox

**Method**: Subprocess isolation with timeout

```python
# Execution environment
- Python 3.11 subprocess
- Timeout: 10 seconds per test run
- Memory limit: 512 MB (via resource.setrlimit)
- No network access
- No file I/O (except reading user's code)
- Allowed imports: Standard library only
```

**Safety**:
- User code runs in separate process (crash-safe)
- Timeout prevents infinite loops
- No `eval()` or `exec()` in main process
- Standard library only (no `pip install` attacks)

---

## Agent Decision Engine

### The Observe-Decide-Act Loop

```python
class InterviewAgent:
    def observe(self) -> AgentContext:
        """Gather context from session history."""
        return AgentContext(
            attempt_count=self._count_attempts(),
            failure_history=self._get_failure_types(),
            last_eval_result=self._get_last_eval(),
            hints_given=self._count_hints(),
        )

    def decide(self, context: AgentContext) -> AgentDecision:
        """Apply policy to determine action."""
        return self.policy.decide(context)

    def act(self, decision: AgentDecision) -> None:
        """Execute decision (generate response, give hint, etc.)."""
        if decision.action == "give_hint":
            self._generate_and_give_hint(decision.hint_level)
        elif decision.action == "give_feedback":
            self._generate_feedback(decision.feedback_context)
```

### Hint Escalation Policy

```python
class HintPolicy:
    """Deterministic hint escalation rules."""

    def get_hint_level(
        self,
        attempt_count: int,
        failure_history: list[FailureType],
        hints_given: int,
    ) -> int:
        """
        Level 1: Socratic question (guide thinking)
        Level 2: High-level approach (data structure choice)
        Level 3: Pseudocode skeleton (algorithm outline)
        Level 4: Reference solution (full code)

        Escalation Rules:
        1. First hint request → Level 1
        2. Same failure type 2+ times → escalate one level
        3. Attempt count ≥ 3 → minimum Level 2
        4. Attempt count ≥ 5 → minimum Level 3
        5. Explicit give-up or 7+ attempts → Level 4
        """
        # Implementation in agent/policy.py
```

### Decision Examples

| Scenario | Observation | Decision | Action |
|----------|-------------|----------|--------|
| First submission fails | Attempt=1, Failure=WRONG_ANSWER | Give feedback | "Your eviction logic has an issue..." |
| User requests hint (1st time) | Attempts=1, Hints=0 | Give Level 1 hint | "What data structure tracks order?" |
| 3rd failure, same error | Attempts=3, Same failure | Give Level 2 hint | "Consider using OrderedDict..." |
| 5+ attempts | Attempts=5 | Offer Level 3 or end | "Would you like pseudocode or to try again?" |

---

## LLM Interface

### Abstract Interface

```python
class LLMClient(ABC):
    @abstractmethod
    def generate(self, prompt: str, context: dict[str, Any]) -> str:
        """Generate text given prompt and context."""
        pass
```

### Mock Implementation (v1 Default)

```python
class MockLLM(LLMClient):
    """Returns predefined responses based on pattern matching."""

    def generate(self, prompt: str, context: dict[str, Any]) -> str:
        if "hint" in prompt.lower() and context["hint_level"] == 1:
            return "What data structure maintains insertion order in Python?"
        elif "feedback" in prompt.lower():
            failure_type = context["failure_type"]
            return self._get_template_feedback(failure_type)
        # ... more patterns
```

### LLM Call Sites

| Location | Purpose | Input Context |
|----------|---------|---------------|
| Problem statement | Initial problem presentation | Problem ID |
| Feedback generation | Post-evaluation feedback | EvaluationResult, failure patterns |
| Hint generation | Adaptive hint text | Hint level, failure history |
| Final summary | End-of-session report | Full session stats |

**v1 Note**: All LLM calls use MockLLM. Real LLM (OpenAI, Anthropic) is v2+.

---

## Persistence Layer

### File System Layout

```
~/.vo_sim/                           # User home directory
├── sessions/
│   ├── 550e8400-....jsonl          # One file per session
│   ├── 661f9511-....jsonl
│   └── ...
├── current_session.txt              # Stores active session ID
└── config.json                      # User preferences (v2+)
```

**Why `~/.vo_sim/`?**
- Follows XDG Base Directory convention
- User-specific, doesn't pollute project dirs
- Easy to find for debugging

### JSONL Event Storage

Each session file is append-only JSONL:

```jsonl
{"session_id": "550e...", "timestamp": "...", "event_type": "SESSION_STARTED", "payload": {...}}
{"session_id": "550e...", "timestamp": "...", "event_type": "CODE_SUBMITTED", "payload": {...}}
{"session_id": "550e...", "timestamp": "...", "event_type": "EVAL_RESULT", "payload": {...}}
```

**Benefits**:
- Append-only (crash-safe, no corruption)
- Human-readable (easy debugging)
- Replayable (reconstruct exact session state)
- Event sourcing pattern (audit trail)

### Session Replay

```python
def replay_session(session_id: str) -> SessionState:
    """Reconstruct session state from events."""
    events = load_events(session_id)
    state_machine = SessionStateMachine()

    for event in events:
        state_machine.apply_event(event)

    return state_machine.current_state
```

---

## CLI Interface

### Command Reference

#### `interviewsim start`

Creates new interview session.

```bash
$ interviewsim start
```

**Output** (using Rich formatting):

```
╭─────────────────────────────────────────────────────────╮
│  🎯 LRU Cache Interview Session Started                │
│  Session ID: 550e8400-e29b-41d4-a716-446655440000      │
╰─────────────────────────────────────────────────────────╯

Problem: Implement an LRU (Least Recently Used) Cache

Design a data structure that follows the constraints of an LRU cache.

Your class must implement:
  • __init__(capacity: int)
  • get(key: int) -> int
  • put(key: int, value: int) -> None

[Full problem description...]

When ready, submit your solution:
  interviewsim submit --file your_solution.py
```

**State Change**: `IDLE` → `PROBLEM_PRESENTED`

---

#### `interviewsim submit --file <path>`

Submit code for evaluation.

```bash
$ interviewsim submit --file lru_cache.py
```

**Output**:

```
📥 Submitting code from: lru_cache.py
🧪 Running evaluation...

╭─────────────── Evaluation Result ───────────────╮
│ Status: ❌ Failed                                │
│ Tests Passed: 5/12                               │
│ Tests Failed: 7/12                               │
│ Runtime: 145ms                                   │
│ Failure Type: WRONG_ANSWER                       │
╰──────────────────────────────────────────────────╯

Failing Tests:
  • test_eviction_order_simple
  • test_eviction_order_complex
  • test_capacity_one

💬 Feedback:
Your solution has issues with eviction logic. When the cache
reaches capacity, it should remove the least recently used item.
Currently, it's removing items in the wrong order.

Try again or type 'interviewsim hint' for guidance.
```

**State Change**: `AWAITING_ACTION` → `EVALUATING` → `AWAITING_ACTION`

---

#### `interviewsim hint`

Request adaptive hint.

```bash
$ interviewsim hint
```

**Output** (Level 1):

```
💡 Hint (Level 1):

What data structure in Python's standard library maintains
insertion order AND allows O(1) removal of arbitrary elements?

Think about how you might combine two data structures...
```

**State Change**: `AWAITING_ACTION` → `AWAITING_ACTION` (no change)

---

#### `interviewsim status`

Show current session status.

```bash
$ interviewsim status
```

**Output**:

```
╭──────────────── Session Status ────────────────╮
│ Session ID: 550e8400-...                       │
│ Problem: LRU Cache                             │
│ Started: 2026-01-05 23:30:00                   │
│ Duration: 15m 32s                              │
├────────────────────────────────────────────────┤
│ Attempts: 3                                    │
│ Last Result: ❌ 5/12 tests passed              │
│ Hints Used: 1 (Level 1)                        │
├────────────────────────────────────────────────┤
│ Status: Awaiting next submission or hint       │
╰────────────────────────────────────────────────╯
```

**State Change**: None (read-only)

---

#### `interviewsim end`

End session and show summary.

```bash
$ interviewsim end
```

**Output**:

```
╭──────────── Interview Summary ─────────────╮
│ Session ID: 550e8400-...                   │
│ Problem: LRU Cache                         │
│ Duration: 24m 15s                          │
├────────────────────────────────────────────┤
│ Total Attempts: 4                          │
│ Final Result: ✅ 12/12 tests passed        │
│ Hints Used: 2 (Levels 1, 2)                │
├────────────────────────────────────────────┤
│ Outcome: Success! 🎉                       │
│                                            │
│ Your approach showed strong understanding  │
│ of hash map + doubly-linked list design.   │
│ The final solution is O(1) for both get   │
│ and put operations.                        │
│                                            │
│ Session log saved to:                      │
│ ~/.vo_sim/sessions/550e8400-....jsonl     │
╰────────────────────────────────────────────╯
```

**State Change**: `AWAITING_ACTION` → `DONE`

---

### Error Messages

#### No Active Session

```bash
$ interviewsim submit --file lru_cache.py
❌ Error: No active interview session.
Start a new session with: interviewsim start
```

#### Session Already Active

```bash
$ interviewsim start
❌ Error: Session already in progress (550e8400-...).
Use 'interviewsim end' to finish current session first.
```

#### Invalid State Transition

```bash
$ interviewsim hint
❌ Error: Cannot request hint in current state.
Submit code first with: interviewsim submit --file <path>
```

#### File Not Found

```bash
$ interviewsim submit --file missing.py
❌ Error: File not found: missing.py
```

---

## Error Handling

### Error Hierarchy

```python
class VOSimError(Exception):
    """Base exception for all VO_Sim errors."""
    pass

class SessionError(VOSimError):
    """Session-related errors."""
    pass

class NoActiveSessionError(SessionError):
    """No session is currently active."""
    pass

class SessionAlreadyActiveError(SessionError):
    """Cannot start session when one is active."""
    pass

class InvalidStateTransitionError(SessionError):
    """Invalid state machine transition."""
    pass

class EvaluationError(VOSimError):
    """Errors during code evaluation."""
    pass

class CodeExecutionTimeout(EvaluationError):
    """User code exceeded time limit."""
    pass

class ImportError(EvaluationError):
    """Failed to import user code."""
    pass
```

### Error Handling Strategy

| Error Type | Handling | User Message | Exit Code |
|------------|----------|--------------|-----------|
| `NoActiveSessionError` | Graceful | "No active session. Use `start` first." | 1 |
| `SessionAlreadyActiveError` | Graceful | "Session active. Use `end` to finish." | 1 |
| `InvalidStateTransitionError` | Graceful | "Cannot perform action in current state." | 1 |
| `CodeExecutionTimeout` | Classify as EXCEPTION | "Code timed out (10s limit)." | 0 |
| File not found | Graceful | "File not found: {path}" | 1 |
| Unexpected errors | Log + crash | "Internal error. Please report." | 2 |

**Philosophy**:
- User errors (wrong command) → Exit code 1, helpful message
- Code errors (timeout, exception) → Recorded in evaluation, exit code 0
- System errors (bugs) → Exit code 2, request bug report

---

## Testing Strategy

### Test Pyramid

```
        ┌───────────────┐
        │  Integration  │  (5 tests)
        │   Tests       │  End-to-end CLI workflows
        ├───────────────┤
       ┌┴───────────────┴┐
       │   Unit Tests     │  (40+ tests)
       │ Agent, Evaluator │  Component-level logic
       │ Policy, Schemas  │
       └──────────────────┘
```

### Unit Tests (pytest)

**Coverage Target**: >90% code coverage

| Module | Test Focus | Example Tests |
|--------|------------|---------------|
| `agent/policy.py` | Hint escalation rules | Test each escalation trigger |
| `evaluator/classifier.py` | Failure classification | Test all FailureType scenarios |
| `evaluator/test_suite.py` | LRU tests correctness | Verify tests catch bugs |
| `session/state_machine.py` | State transitions | Valid/invalid transitions |
| `session/persistence.py` | Event I/O | Write + replay events |
| `schemas.py` | Pydantic validation | Invalid data raises errors |

### Integration Tests

| Test | Scenario | Verification |
|------|----------|-------------|
| `test_full_interview_success` | Start → Submit (pass) → End | Session log complete |
| `test_full_interview_with_hints` | Start → Fail → Hint → Pass → End | Hint escalation correct |
| `test_multiple_submissions` | 5 failed attempts | Policy triggers correctly |
| `test_session_replay` | Create session → Replay from log | State reconstructed exactly |
| `test_timeout_handling` | Submit infinite loop code | Classified as EXCEPTION |

### Test Fixtures

```python
# tests/fixtures/lru_implementations/
├── correct_solution.py          # 12/12 tests pass
├── wrong_eviction.py            # 5/12 tests pass (eviction bugs)
├── missing_methods.py           # WRONG_SIGNATURE
├── runtime_exception.py         # EXCEPTION
├── infinite_loop.py             # Timeout → EXCEPTION
└── import_error.py              # IMPORT_ERROR
```

### CI/CD (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install poetry
      - run: poetry install
      - run: poetry run pytest --cov --cov-report=xml
      - run: poetry run mypy src/
      - run: poetry run ruff check src/
```

**Why CI?**
- Professional standard (impressive for resume)
- Catches bugs before merge
- Ensures code quality (mypy, ruff)

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)

**Goal**: Core infrastructure without agent intelligence

- [ ] Project setup (`pyproject.toml`, `ruff`, `mypy`)
- [ ] Pydantic schemas (`Event`, `EvaluationResult`, etc.)
- [ ] State machine implementation
- [ ] JSONL persistence layer
- [ ] Basic CLI commands (start, end, status)
- [ ] Unit tests for schemas + state machine

**Deliverable**: Can start/end sessions with event logging

---

### Phase 2: Evaluation System (Week 2)

**Goal**: Deterministic code evaluation

- [ ] LRU Cache test suite (12 tests)
- [ ] Code runner with subprocess sandbox
- [ ] Failure classifier
- [ ] `submit` command integration
- [ ] Unit tests for evaluator
- [ ] Integration test: full submission flow

**Deliverable**: Can submit code and get test results

---

### Phase 3: Agent Logic (Week 3)

**Goal**: Agentic observe-decide-act loop

- [ ] `InterviewAgent` class
- [ ] Hint policy implementation
- [ ] MockLLM with template responses
- [ ] `hint` command integration
- [ ] Agent decision tests
- [ ] Integration test: hint escalation

**Deliverable**: Adaptive hints based on failure patterns

---

### Phase 4: Polish & Documentation (Week 4)

**Goal**: Production-ready v1

- [ ] Rich CLI formatting (colors, tables)
- [ ] Comprehensive error handling
- [ ] Full integration test suite
- [ ] Documentation (README, ARCHITECTURE.md)
- [ ] GitHub Actions CI
- [ ] Demo video / GIF for README

**Deliverable**: Shippable v1 ready for resume

---

## Acceptance Criteria

VO_Sim v1 is **complete** when:

✅ **Functional**:
- [ ] A full LRU Cache interview can be conducted via CLI
- [ ] Multiple code submissions are supported
- [ ] Hint escalation follows the defined policy
- [ ] Session logs are replayable and deterministic

✅ **Quality**:
- [ ] >90% code coverage with pytest
- [ ] No mypy type errors
- [ ] No ruff linting errors
- [ ] CI pipeline passes

✅ **Documentation**:
- [ ] README with usage examples
- [ ] ARCHITECTURE.md explaining design
- [ ] Docstrings for all public APIs
- [ ] Demo GIF in README

✅ **Resume-Ready**:
- [ ] Clean commit history
- [ ] Professional project structure
- [ ] Deployed on GitHub with CI badge
- [ ] Can explain agent design in interviews

---

## Non-Goals (v1)

Explicitly **deferred** to future versions:

- Multiple problems or problem selection
- Real LLM integration (OpenAI, Anthropic)
- Web UI or GUI
- User accounts / authentication
- Concurrent sessions
- Voice input/output
- Performance metrics dashboard
- Deployment to cloud

Keep v1 focused and achievable!

---

## Appendix: Key Design Decisions

### Why JSONL Instead of SQLite?

- Simpler (no schema migrations)
- Human-readable (easier debugging)
- Append-only (crash-safe)
- Event sourcing pattern (better for learning)

**Trade-off**: Slower queries (but v1 has tiny data volumes)

### Why Subprocess Sandbox Instead of Docker?

- Lighter weight (no Docker dependency)
- Faster startup (ms vs seconds)
- Sufficient for v1 threat model (student code, not production)

**Trade-off**: Less isolation (but acceptable for trusted users)

### Why Mock LLM Instead of Real API?

- No API keys required (easy setup)
- Deterministic testing (reproducible)
- Fast (no network latency)
- Learn agent patterns first, LLM integration later

**Trade-off**: Less impressive demo (but v2 will have real LLM)

---

## Resources for Learning

### Agent Patterns
- [LangChain Agent Documentation](https://python.langchain.com/docs/modules/agents/)
- [ReAct: Reasoning and Acting](https://arxiv.org/abs/2210.03629)

### Event Sourcing
- [Martin Fowler: Event Sourcing](https://martinfowler.com/eaaDev/EventSourcing.html)

### State Machines
- [Python `transitions` Library](https://github.com/pytransitions/transitions)

### Modern Python
- [Real Python: Type Hints](https://realpython.com/python-type-checking/)
- [Pydantic Documentation](https://docs.pydantic.dev/)

---

**End of Design Document**

*This document is the single source of truth for VO_Sim v1 implementation.*
