---
name: howto-code-in-python
description: Use when writing Python code, reviewing Python implementations, or making decisions about dependencies, project structure, or type annotations - covers uv tooling, ruff linting, modern type hints, Pydantic v2 models, and FastAPI patterns
user-invocable: false
---

# Python House Style

## Overview

Python coding standards using uv for package management and ruff for linting/formatting.

**Core principles:**
- uv manages the entire project lifecycle (replaces pip, virtualenv, poetry)
- ruff replaces flake8, isort, and black in one tool
- Modern type hints throughout; no legacy `typing` imports
- Pydantic v2 for data validation and serialization
- FastAPI for HTTP APIs, with `Depends()` + `Annotated` for dependency injection
- `pyproject.toml` is the single source of truth for config
- `src/` layout for any publishable library

## Quick Self-Check (Use Under Pressure)

When under deadline pressure, STOP and verify:

- [ ] Using `list[str]` not `List[str]`; `dict[K, V]` not `Dict[K, V]`
- [ ] Using `X | None` not `Optional[X]`
- [ ] Dependencies added with `uv add`, not `pip install`
- [ ] Scripts run with `uv run`, not bare `python`
- [ ] Ran `ruff check --fix && ruff format` before commit
- [ ] All config in `pyproject.toml`; no stray `.flake8` / `setup.cfg` / `.isort.cfg`
- [ ] `uv.lock` committed to version control
- [ ] No `requirements.txt` alongside `pyproject.toml`
- [ ] Pydantic models use `model_dump()` not `.dict()`; `model_validate()` not `.parse_obj()`
- [ ] Pydantic config uses `model_config = ConfigDict(...)` not inner `class Config:`
- [ ] FastAPI deps declared as `Annotated[Type, Depends(...)]`
- [ ] FastAPI app using lifespan context manager, not deprecated `@app.on_event()`

## Tooling

### uv — Project Lifecycle

```bash
uv init my-project              # Init with pyproject.toml, .venv, .python-version
uv add requests pydantic        # Add runtime dependency
uv add --dev pytest ruff mypy   # Add dev dependency
uv remove requests              # Remove a dependency
uv run python main.py           # Run with project env (no manual activation)
uv run pytest                   # Run tests
uvx ruff check .                # Run ruff without installing globally
uv sync                         # Sync .venv to lockfile
uv lock                         # Regenerate lockfile
```

**Rule:** Never use bare `pip install` in a uv-managed project.

### ruff — Lint and Format

```bash
ruff check --fix .              # Lint and auto-fix
ruff format .                   # Format (replaces black)
ruff check --select I --fix .   # Fix imports only
```

**Standard `pyproject.toml` config:**

```toml
[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
extend-select = [
    "E",    # pycodestyle errors
    "F",    # pyflakes (on by default)
    "I",    # isort
    "UP",   # pyupgrade — modernize syntax automatically
    "B",    # bugbear — catches likely bugs
    "SIM",  # simplify
    "RUF",  # ruff-specific rules
]
ignore = ["E501"]  # line length handled by formatter

[tool.ruff.format]
quote-style = "double"
```

## Type Hints

### Use Modern Syntax (Python 3.10+)

```python
# ✅ Modern
def process(items: list[str], lookup: dict[str, int]) -> str | None:
    ...

# ❌ Legacy — avoid in new code
from typing import List, Dict, Optional, Union
def process(items: List[str], lookup: Dict[str, int]) -> Optional[str]:
    ...
```

### Structural and Callable Types

```python
from typing import Protocol, TypedDict, NotRequired
from collections.abc import Sequence, Callable

# Protocol for structural subtyping (duck typing + type safety)
class Renderable(Protocol):
    def render(self) -> str: ...

# TypedDict for typed dict shapes
class UserData(TypedDict):
    name: str
    age: int
    email: NotRequired[str]  # Optional field

# Use collections.abc, not typing, for generic abstract types
def apply(items: Sequence[int], fn: Callable[[int], bool]) -> list[int]:
    return [x for x in items if fn(x)]
```

### Dataclasses for Structured Data

```python
from dataclasses import dataclass, field

@dataclass
class Config:
    host: str
    port: int = 8080
    tags: list[str] = field(default_factory=list)
    timeout: float = 30.0
```

## Project Structure

```
my-project/
├── .python-version           # e.g., "3.12" — commit this
├── pyproject.toml            # All config lives here
├── uv.lock                   # Commit this
├── README.md
├── src/
│   └── my_project/
│       ├── __init__.py
│       └── main.py
└── tests/
    └── test_main.py
```

**Why `src/` layout:** Prevents accidentally importing the uninstalled package from the project root during development.

**Minimal `pyproject.toml`:**

```toml
[project]
name = "my-project"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["fastapi[standard]>=0.100", "pydantic>=2.0"]

[tool.uv]
dev-dependencies = ["pytest>=8.0", "ruff>=0.4", "mypy>=1.0"]

[tool.ruff]
line-length = 88
target-version = "py312"

[tool.ruff.lint]
extend-select = ["E", "F", "I", "UP", "B", "SIM"]
ignore = ["E501"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

## Pydantic v2

Use Pydantic for all data validation and serialization. Install with `uv add pydantic`.

### Models

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Annotated

class User(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: int
    name: str
    email: str | None = None
    age: Annotated[int, Field(gt=0, le=150, description="User age in years")]
```

### Validators (v2 syntax)

```python
from pydantic import BaseModel, field_validator, model_validator

class User(BaseModel):
    name: str
    password: str
    password_confirm: str

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("name cannot be empty")
        return v.strip()

    @model_validator(mode="after")
    def passwords_match(self) -> "User":
        if self.password != self.password_confirm:
            raise ValueError("passwords do not match")
        return self
```

### Serialization and Validation

```python
user = User(id=1, name="Alice")

# Serialization — v2 methods
user.model_dump()                       # -> dict
user.model_dump_json()                  # -> JSON string
user.model_dump(exclude_unset=True)     # omit fields not explicitly set

# Validation — v2 methods
User.model_validate({"id": 1, "name": "Alice"})       # from dict
User.model_validate_json('{"id": 1, "name": "Alice"}') # from JSON string
```

**v1 → v2 migration:**

| v1 (avoid) | v2 (use) |
|---|---|
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `.parse_obj(d)` | `.model_validate(d)` |
| `.parse_raw(s)` | `.model_validate_json(s)` |
| `class Config:` | `model_config = ConfigDict(...)` |

### ConfigDict

```python
from pydantic import BaseModel, ConfigDict

class StrictInput(BaseModel):
    model_config = ConfigDict(
        strict=True,      # No type coercion (e.g. "123" won't become int)
        extra="forbid",   # Reject unknown fields
        frozen=True,      # Immutable after creation
    )
    age: int
```

### Reusable Annotated Types

```python
from pydantic import Field
from typing import Annotated

PositiveInt = Annotated[int, Field(gt=0)]
EmailStr = Annotated[str, Field(pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$")]

class Product(BaseModel):
    price: PositiveInt
    seller_email: EmailStr
```

## FastAPI

Install with `uv add fastapi[standard]` (includes uvicorn).

### Route Definitions

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class Item(BaseModel):
    name: str
    price: float

# FastAPI infers: path params from URL, query params from function args, body from Pydantic models
@app.get("/items/{item_id}")
async def read_item(item_id: int, q: str | None = None) -> dict:
    return {"item_id": item_id, "q": q}

@app.post("/items/", response_model=Item)
async def create_item(item: Item) -> Item:
    return item
```

### Dependency Injection

Use `Annotated` + `Depends()` — the modern pattern (FastAPI 0.95+):

```python
from typing import Annotated
from fastapi import Depends, FastAPI, HTTPException

async def get_current_user(token: str) -> User:
    user = verify_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="invalid token")
    return user

# Type alias for reuse across routes
CurrentUser = Annotated[User, Depends(get_current_user)]

@app.get("/profile")
async def profile(user: CurrentUser) -> User:
    return user

@app.delete("/account")
async def delete_account(user: CurrentUser) -> dict:
    ...
```

### APIRouter for Organization

```python
# routers/items.py
from fastapi import APIRouter

router = APIRouter(prefix="/items", tags=["items"])

@router.get("/")
async def list_items() -> list[Item]: ...

@router.post("/")
async def create_item(item: Item) -> Item: ...

# main.py
from fastapi import FastAPI
from .routers import items

app = FastAPI()
app.include_router(items.router)
```

### Lifespan (replaces deprecated `@app.on_event`)

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: connect DB, load models, warm caches
    db_pool = await create_pool()
    yield {"db": db_pool}
    # Shutdown: release resources
    await db_pool.close()

app = FastAPI(lifespan=lifespan)
```

### Error Handling

```python
from fastapi import HTTPException

@app.get("/items/{item_id}")
async def get_item(item_id: int) -> Item:
    item = db.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="item not found")
    return item
```

### Running

```bash
uv run fastapi dev          # Development with auto-reload
uv run fastapi run          # Production
# or
uv run uvicorn app.main:app --reload
```

## Error Handling

Raise specific, informative exceptions. Chain with `from e` to preserve tracebacks.

```python
class ConfigError(ValueError):
    pass

def load_config(path: str) -> Config:
    try:
        with open(path) as f:
            return parse(f.read())
    except FileNotFoundError as e:
        raise ConfigError(f"config not found: {path}") from e
    except ParseError as e:
        raise ConfigError(f"invalid config at {path}") from e
```

**Never use bare `except:` or `except Exception: pass`** — swallowed errors cause impossible-to-debug failures.

## Common Mistakes

| Mistake | Reality | Fix |
|---------|---------|-----|
| `pip install` in uv project | Bypasses lockfile, breaks reproducibility | Use `uv add` |
| `from typing import List, Dict` | Deprecated since Python 3.9 | Use built-in `list[T]`, `dict[K, V]` |
| `Optional[X]` | Verbose, pre-3.10 style | Use `X \| None` |
| Scattered config files | `.flake8`, `setup.cfg`, `.isort.cfg` pile up | Consolidate in `pyproject.toml` |
| Missing `uv.lock` in VCS | Non-reproducible installs | Commit `uv.lock` |
| `requirements.txt` alongside `pyproject.toml` | Two sources of truth for deps | Remove `requirements.txt` |
| Bare `python script.py` | Uses system Python, not project env | Use `uv run python script.py` |
| `except Exception: pass` | Silently swallows bugs | Always handle or re-raise with context |
| Pydantic `.dict()` / `.json()` | v1 API — removed in v2 | Use `.model_dump()` / `.model_dump_json()` |
| Pydantic `.parse_obj()` | v1 API — removed in v2 | Use `.model_validate()` |
| Pydantic `class Config:` inside model | v1 pattern | Use `model_config = ConfigDict(...)` |
| FastAPI `@app.on_event("startup")` | Deprecated | Use `@asynccontextmanager` lifespan |
| FastAPI `Depends(fn)` without `Annotated` | Less readable, harder to reuse | Use `Annotated[Type, Depends(fn)]` |

## Red Flags

**Stop and fix when you see:**

- `requirements.txt` in a uv-managed project
- `from typing import List, Dict, Optional, Union` in new files
- `pip install` in the project README or Makefile
- `uv.lock` not committed to version control
- Config split across `.flake8`, `setup.cfg`, `tox.ini`
- `except Exception: pass` silently swallowing errors
- `python` invocations in scripts where `uv run` should be used
- Pydantic model calling `.dict()` or `.json()` (v1 API)
- Pydantic model with inner `class Config:` instead of `model_config = ConfigDict(...)`
- `@app.on_event("startup")` in FastAPI (deprecated — use lifespan)
- FastAPI `Depends(fn)` used without `Annotated` type wrapper
