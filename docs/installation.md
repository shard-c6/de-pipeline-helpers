# Installation

## Requirements

- **Python ≥ 3.10** (tested on 3.10, 3.11, and 3.12)
- **pip** (or any PEP 517-compatible installer)

We strongly recommend installing inside a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate   # macOS / Linux
# .venv\Scripts\activate    # Windows
```

---

## Core Install

The core package includes the HTTP client, database manager, and structured logger:

```bash
pip install dehelpers
```

### Core Dependencies

| Package | Version | Purpose |
|---|---|---|
| `requests` | ≥ 2.28 | HTTP transport for `ResilientClient` |
| `sqlalchemy` | ≥ 2.0 | Engine and session management for `DatabaseManager` |
| `psycopg[binary]` | ≥ 3.0 | PostgreSQL driver (libpq bundled) |

---

## Optional Extras

### DataFrame Support

If you want `DatabaseManager.to_dataframe()` to return Pandas DataFrames:

```bash
pip install dehelpers[dataframe]
```

This adds `pandas ≥ 2.0` as a dependency. Pandas is **lazy-loaded** — it is only imported when you call `to_dataframe()`, so the core package stays lightweight even if the extra is installed.

### Development (Contributing)

To run the test suite and contribute:

```bash
pip install dehelpers[dev,dataframe]
```

This adds `pytest`, `pytest-cov`, `responses` (HTTP mocking), and `pytest-postgresql`.

---

## Verify Your Installation

```python
import dehelpers
print(dehelpers.__version__)
# Expected output: 0.1.0
```

You can also verify each module imports cleanly:

```python
from dehelpers import ResilientClient, DatabaseManager, get_logger
print("All imports OK")
```

---

## Next Steps

- [Getting Started](getting-started.md) — your first pipeline in under 25 lines
- [API Reference](api-reference.md) — full class and function documentation
