# Setup Files Explained

You have **2 essential files** for dependencies:

---

## 1. setup.py - Package Installer

**What it does:**
- Defines your package (name, version, author)
- Lists **all dependencies** (runtime + dev)
- Creates the CLI command `vo-sim`

**When you edit it:**
- Adding new packages
- Changing version number
- Updating author info

**Contains:**
```python
install_requires=[...]        # Runtime: Click, Rich, Pydantic
extras_require={"dev": [...]} # Dev: pytest, mypy, ruff
entry_points={...}            # Creates 'vo-sim' command
```

---

## 2. pyproject.toml - Tool Configuration

**What it does:**
- Configures ruff (linter/formatter)
- Configures mypy (type checker)
- Configures pytest (test runner)

**When you edit it:**
- Changing code style rules
- Adjusting type checking strictness
- Modifying test settings

**Does NOT contain dependencies** (those are in setup.py)

---

## How to Install

```bash
# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install package + runtime dependencies
pip install -e .

# Install dev tools (pytest, mypy, ruff)
pip install -e ".[dev]"
```

---

## File Summary

| File | Purpose | Edit Often? |
|------|---------|-------------|
| `setup.py` | Package metadata + dependencies | When adding packages |
| `pyproject.toml` | Tool configuration | Rarely |
| `.gitignore` | What NOT to commit | Once at start |
| `README.md` | Project documentation | Yes |

---

## Why Not requirements.txt?

For a **package** (something with a CLI command), `setup.py` is standard.

`requirements.txt` is typically for **applications** (web apps, scripts).

We use `setup.py` because VO_Sim is a package with a CLI command (`vo-sim`).

---

## Commands You'll Use

```bash
# Install
pip install -e ".[dev]"

# Verify
vo-sim --version

# Run tests
pytest

# Check code
ruff check src/
mypy src/

# Format code
ruff format src/
```

---

That's it! Just **2 config files** to understand.
