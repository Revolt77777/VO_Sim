# VO_Sim — Virtual Onsite Simulator

**An L3-L4 agentic interview conductor for coding interviews**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Overview

VO_Sim is a CLI-based AI interview agent that conducts stateful coding interviews. v1 focuses on a single problem (**LRU Cache**) and demonstrates autonomous agent behavior through deterministic evaluation, adaptive feedback, and policy-driven hint escalation.

This project showcases:
- **L3-L4 Agentic Workflows**: Observe-Decide-Act loop with state management
- **Event Sourcing**: Full session replay from append-only JSONL logs
- **Deterministic Evaluation**: Test-based grading (no LLM subjectivity)
- **Clean Architecture**: Separation of Agent, Evaluator, Persistence, and CLI

---

## Quick Start

```bash
# Start an interview session
interviewsim start

# Submit your solution
interviewsim submit --file lru_cache.py

# Get adaptive hints
interviewsim hint

# Check status
interviewsim status

# End session
interviewsim end
```

---

## What v1 Can Do

✅ Run a complete LRU Cache interview end-to-end
✅ Evaluate code deterministically using 12 test cases
✅ Classify failures (wrong answer, exception, partial pass, etc.)
✅ Provide adaptive hints with policy-driven escalation (4 levels)
✅ Persist full session history as replayable event logs
✅ Generate interview summary on completion

---

## What v1 Does NOT Do

❌ Multiple problems or problem recommendation
❌ Real LLM integration (uses MockLLM for v1)
❌ Web UI or voice interface
❌ User accounts or authentication
❌ Long-term skill modeling

**These are intentionally deferred to v2+**

---

## Architecture Highlights

```
┌─────────────┐
│  CLI Layer  │  (Click commands)
└──────┬──────┘
       │
       ▼
┌─────────────────────────┐
│   Interview Agent       │  (Observe-Decide-Act)
│  ┌─────────────────┐   │
│  │ Hint Policy     │   │  (Deterministic rules)
│  │ Feedback Engine │   │
│  └─────────────────┘   │
└──────┬──────────────────┘
       │
       ├─────────────┬────────────────┬────────────────┐
       ▼             ▼                ▼                ▼
┌────────────┐ ┌───────────┐ ┌────────────┐ ┌──────────────┐
│ Evaluator  │ │ State     │ │ Event      │ │ LLM Client   │
│ (Sandbox)  │ │ Machine   │ │ Store      │ │ (Mock v1)    │
└────────────┘ └───────────┘ └────────────┘ └──────────────┘
```

See [docs/DESIGN.md](docs/DESIGN.md) for complete architecture details.

---

## LRU Cache Contract

Your code must implement:

```python
class LRUCache:
    def __init__(self, capacity: int):
        """Initialize LRU cache with given capacity."""
        pass

    def get(self, key: int) -> int:
        """Return value if key exists, else -1. Updates recency."""
        pass

    def put(self, key: int, value: int) -> None:
        """Set/update key-value. Evicts LRU item if at capacity."""
        pass
```

---

## Example Session

```bash
$ interviewsim start
╭─────────────────────────────────────────────────────────╮
│  🎯 LRU Cache Interview Session Started                │
│  Session ID: 550e8400-e29b-41d4-a716-446655440000      │
╰─────────────────────────────────────────────────────────╯

Problem: Implement an LRU (Least Recently Used) Cache
[Problem description...]

$ interviewsim submit --file my_solution.py
🧪 Running evaluation...

╭─────────────── Evaluation Result ───────────────╮
│ Status: ❌ Failed                                │
│ Tests Passed: 5/12                               │
│ Failure Type: WRONG_ANSWER                       │
╰──────────────────────────────────────────────────╯

💬 Feedback: Your eviction logic has an issue...

$ interviewsim hint
💡 Hint (Level 1):
What data structure maintains insertion order in Python?

$ interviewsim submit --file my_solution_v2.py
✅ All tests passed! (12/12)

$ interviewsim end
╭──────────── Interview Summary ─────────────╮
│ Outcome: Success! 🎉                       │
│ Attempts: 2                                │
│ Hints Used: 1                              │
╰────────────────────────────────────────────╯
```

---

## Tech Stack

- **Python 3.11+**: Modern Python with type hints
- **Click**: CLI framework
- **Pydantic v2**: Schema validation
- **Rich**: Beautiful terminal output
- **pytest**: Testing framework

---

## Documentation

| Document | Description |
|----------|-------------|
| [DESIGN.md](docs/DESIGN.md) | Complete v1 specification (architecture, schemas, policies) |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | *(Coming soon)* System design deep-dive |
| [API.md](docs/API.md) | *(Coming soon)* Public API reference |

---

## Development Status

**Current Phase**: 🏗️ Foundation (Week 1)

- [x] High-level design complete
- [x] Detailed specification written
- [ ] Project scaffolding
- [ ] Core schemas & state machine
- [ ] Persistence layer
- [ ] Evaluation system
- [ ] Agent logic
- [ ] CLI integration
- [ ] Testing & polish

See [docs/DESIGN.md - Implementation Roadmap](docs/DESIGN.md#implementation-roadmap) for full timeline.

---

## Why This Project?

### Learning Goals
- Understand L3-L4 agentic workflows (autonomous reasoning + tool use)
- Master event sourcing and state machines
- Practice clean architecture patterns
- Build production-quality Python code

### Resume Value
This project demonstrates:
- **System Design**: Multi-component architecture with clear separation
- **AI/ML Engineering**: Agent design, policy systems, LLM integration patterns
- **Software Engineering**: Type safety, testing, CI/CD, documentation
- **Problem Solving**: Sandbox execution, deterministic evaluation, adaptive behavior

---

## Roadmap

- **v1** (Current): Single LRU Cache problem with MockLLM
- **v2**: Multiple problems, curriculum agent, real LLM integration
- **v3**: Long-term skill modeling and difficulty adaptation
- **v4**: Voice-based interviews
- **v5**: Fully autonomous interview planning

---

## License

MIT License - See [LICENSE](LICENSE) for details

---

## Contributing

This is a student learning project. Feedback and suggestions welcome via issues!

---

**Built with ❤️ to learn AI agents and ace SDE interviews**
