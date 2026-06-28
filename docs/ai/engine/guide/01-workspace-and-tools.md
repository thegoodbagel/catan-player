# Chapter 1 — Workspace and Tools

> ## At a glance
> - **Where you are:** You understand the central idea (facts as data, rules as functions) from Chapter 0. Nothing is installed or running yet.
> - **This chapter's goal:** Get a working, tested project skeleton — one green test — *before* writing any game code.
> - **What this chapter is NOT:** This is not game logic. You write zero Catan rules here. You are only proving the tooling (imports, test discovery, the test libraries) works. The vocabulary starts in Chapter 2.
> - **By the end you will have:** A filled-in `pyproject.toml`, `src/engine/__init__.py`, `tests/test_smoke.py`, the dev tools installed, and `python3 -m pytest` printing a line that ends in `1 passed`.
> - **Maps to:** Task 1 in `.kiro/specs/catan-engine/tasks.md`.
> - **Prerequisites:** Chapter 0. Python 3.11+ available on your machine.

**Goal in plain language.** Make the empty project *runnable* — so that when a
later chapter breaks, you know it's your code that broke, not your setup.

**Why first.** A foundation you have not tested is a foundation you do not have.
Establishing that imports resolve and tests run — while there is nothing to
break — means every later failure points at *your* code, not your setup.

---

## Project layout

A single code file is a **module**; a folder of related modules is a **package**.
We separate the engine package from the tests. Your project already has this
skeleton on disk — you are *filling it in*, not creating it from nothing:

```
catan/
├── pyproject.toml          # exists but is EMPTY — you fill it in (Step 2)
├── src/
│   └── engine/             # exists, with empty stub files (board.py, game.py, ...)
│       └── __init__.py     # you CREATE this — it makes "engine" an importable package
└── tests/
    └── test_smoke.py       # you CREATE this — a throwaway "does anything work?" test
```

> The presence of `src/engine/__init__.py` is what turns the folder into a
> package Python can import. The file can be completely empty; its mere existence
> is what matters.

---

## Straight-up setup instructions

Do these in order. After each step I say what success looks like. Everything runs
from the project root, `/Users/abrzhang/personal/catan`.

### Step 1 — Open a terminal at the project root

```bash
cd /Users/abrzhang/personal/catan
pwd                 # should print: /Users/abrzhang/personal/catan
```

If `pwd` shows anything else, `cd` to the right place before continuing — every
path below is relative to this folder.

### Step 2 — Check Python (3.11+) and, optionally, make a virtual environment

```bash
python3 --version       # need 3.11 or higher, e.g. "Python 3.12.2"
```

Optional but recommended — a **virtual environment** keeps this project's
libraries separate from your system Python:

```bash
python3 -m venv .venv          # creates a private Python in ./.venv
source .venv/bin/activate       # your prompt now shows (.venv) at the front
```

After activating, `python3` and `pip` refer to this project's private copy. Leave
it later with `deactivate`; re-enter it each session with
`source .venv/bin/activate`. Add `.venv/` to your `.gitignore` so you don't
commit it.

### Step 3 — Fill in `pyproject.toml`

`pyproject.toml` exists but is empty. Put **exactly** this in it:

```toml
[project]
name = "catan-engine"
version = "0.1.0"
requires-python = ">=3.11"

[project.optional-dependencies]
dev = ["pytest>=8.0", "hypothesis>=6.0"]

[tool.pytest.ini_options]
pythonpath = ["src"]        # so "import engine" finds code under src/engine
```

What each part does: `[project]` names the project. The `dev` list is the tools
you only need while developing (the test libraries). The line that does the magic
is `pythonpath = ["src"]` — it tells pytest to look inside `src/`, which is what
lets `import engine` work even though the code lives in `src/engine`.

### Step 4 — Create `src/engine/__init__.py`

A folder becomes an importable package when it contains a file named
`__init__.py`. Create an empty one for the engine:

```bash
touch src/engine/__init__.py
```

(There is also a `tests/__init__.py` already present — that's fine, leave it.)

### Step 5 — Write the smoke test

A **smoke test** checks the most basic signs of life. Ours just proves the test
runner and imports work. Create `tests/test_smoke.py` with exactly this content:

```python
# tests/test_smoke.py
import engine                   # fails loudly if the package isn't importable

def test_package_imports():
    assert engine is not None
```

### Step 6 — Install the tools and run the tests

```bash
python3 -m pip install -e ".[dev]"     # installs pytest + hypothesis
python3 -m pytest                       # finds and runs every test_*.py
```

What `python3 -m pip install -e ".[dev]"` means: `pip install` fetches and
installs packages; `.` means "this project, here"; `[dev]` means "also install
the optional dev tools from pyproject.toml"; `-e` ("editable") means "link to my
source so I can keep editing without reinstalling."

### What success looks like

```
collected 1 item

tests/test_smoke.py .                                            [100%]

============================== 1 passed in 0.01s ===============================
```

That single `.` and the line ending in **`1 passed`** is your one green test.
Setup is done.

---

## Troubleshooting

| You see | What it means | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'engine'` | package not found | Confirm `src/engine/__init__.py` exists **and** `pythonpath = ["src"]` is in `pyproject.toml`. This is the single most common setup error. |
| `command not found: python3` | Python isn't installed/visible | Install Python 3.11+ (python.org or `brew install python`). |
| `no tests ran` / `collected 0 items` | pytest found no `test_*.py` | Confirm the file is `tests/test_smoke.py` and the function name starts with `test_`. |
| `pytest: command not found` | tools not installed in this environment | Re-run `python3 -m pip install -e ".[dev]"`. As a quick fallback you can install the tools directly: `python3 -m pip install pytest hypothesis`. |
| prompt has no `(.venv)` | virtual env not active | Run `source .venv/bin/activate` (only if you chose to use a venv). |

> **Fallback if the editable install is fussy.** If `pip install -e ".[dev]"`
> gives you trouble (old pip, odd environment), you can get unblocked with just
> `python3 -m pip install pytest hypothesis` and still run `python3 -m pytest`.
> The `pythonpath = ["src"]` line in `pyproject.toml` is what makes imports work,
> independent of the editable install.

> **Margin notes**
> - **Module / package**: one file / a folder of files acting as a unit.
> - **Dependency**: an external library your project needs (here, the test tools).
> - **`-e` (editable install)**: installs your project so imports work while you
>   keep editing the source in place.
> - **Smoke test**: the most basic "is anything on fire?" check — it proves the
>   plumbing works, not the game logic.

## Exercises

1. **Build it.** Follow Steps 1–6 above and make `python3 -m pytest` show one
   green test.
2. **Break it on purpose.** Rename `__init__.py` temporarily and rerun pytest.
   Read the error. Restore the file. (Knowing what a *missing package* error looks
   like saves hours later.)
3. **Add a second test** asserting `1 + 1 == 2`, and confirm pytest now reports
   two passing tests. Where did pytest find it, and how?

### Hints / how to start

- **Ex. 1 (build it).** This is literally Steps 1–6 above. The only "gotcha" is
  Step 3 — copy the `pyproject.toml` block character-for-character, especially the
  `pythonpath = ["src"]` line. Stop when you see `1 passed`.
- **Ex. 2 (break it).** The point is to *recognize* a common error so it never
  scares you. Do it safely by renaming, then restoring:
  ```bash
  mv src/engine/__init__.py src/engine/__init__.py.bak   # hide the file
  python3 -m pytest                                       # observe the failure
  mv src/engine/__init__.py.bak src/engine/__init__.py   # restore it
  ```
  You should see `ModuleNotFoundError: No module named 'engine'`. That exact
  message means "Python couldn't find the package" — almost always a missing
  `__init__.py` or a wrong `pythonpath`. Now it's a known friend.
- **Ex. 3 (second test).** Add another function to `tests/test_smoke.py` (or a new
  file `tests/test_math.py`):
  ```python
  def test_arithmetic_works():
      assert 1 + 1 == 2
  ```
  A passing test here checks nothing about Catan — it checks that pytest discovers
  any function named `test_*` in any `test_*.py` file under `tests/`. Run
  `python3 -m pytest -v` to see both test names listed; that `-v` (verbose) output
  answers "where did pytest find it?".

## Run your tests

```bash
python3 -m pytest
```

You just added `tests/test_smoke.py`. A line ending in `1 passed` (or `2 passed`
after Exercise 3) means your toolchain is sound and you're ready for real code.

---

Previous: [00 — The Central Idea](00-central-idea.md) | Next: [02 — The Vocabulary of the Game](02-vocabulary.md)
