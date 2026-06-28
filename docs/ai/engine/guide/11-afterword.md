# Chapter 11 — Afterword & Appendices

> ## At a glance
> - **Where you are:** You've built and tested the whole engine: tools, vocabulary, board, state, bundle, `legal_moves`, `apply`, scoring, the front door, and a property suite (Chapters 1–10).
> - **This chapter's goal:** Step back — recap the layering and the transferable lesson — and give you two quick reference tables for the Python features and tools used throughout.
> - **What this chapter is NOT:** No new code and no new exercises. This is the wrap-up and reference shelf.
> - **By the end you will have:** A clear mental model of why the chapter order is what it is, and handy lookup tables (Appendix A: Python features; Appendix B: the toolchain).
> - **Maps to:** The project checkpoints — Tasks 7, 10, and 13 in `.kiro/specs/catan-engine/tasks.md` (the "stop, run everything, ask questions" points).
> - **Prerequisites:** You've worked through the chapters this summarizes.

---

## How to proceed, and what you've learned

Work chapter by chapter, implementing the matching task before moving on. The
order is not arbitrary — each layer depends on the ones beneath it:

1. **Tools and vocabulary** (Ch. 1–2) give you a language to speak.
2. **The board** (Ch. 3) is the foundation every rule queries.
3. **The state** (Ch. 4) holds what changes, copyable cheaply.
4. **The bundle** (Ch. 5) turns "the rules" into data the engine reads.
5. **legal_moves and apply** (Ch. 6–7) are the engine's two verbs.
6. **Scoring** (Ch. 8) includes the one hard algorithm — give it its due.
7. **The front door** (Ch. 9) makes it usable and reproducible.
8. **Tests** (Ch. 10) are where correctness is earned, not assumed.

After Chapter 7 you can already play a full game from the keyboard. After Chapter
10 you have a trustworthy engine ready for the bots and networking that motivated
the project.

The transferable lesson is larger than Catan. You have practiced the central
discipline of building reliable software: model your facts as plain data, express
your rules as small functions over that data, expose a narrow stable interface,
and prove the whole thing correct with tests that probe far beyond the cases you
imagined. That pattern will serve you in systems far removed from a hexagonal
island.

---

## Appendix A — Python features used in this book

| Feature | One-line purpose | Seen in |
|---|---|---|
| `@dataclass` | concise record types | Ch. 2, 4 |
| `@dataclass(frozen=True)` | immutable, hashable records (moves) | Ch. 2 |
| `Enum` | fixed sets of named values | Ch. 2 |
| type hints (`x: int`) | document and check intent | throughout |
| `Optional[T]` | "a T, or None" | Ch. 2 |
| dict as dispatch table | choose behavior by key | Ch. 5–7 |
| list/dict comprehensions | build collections concisely | Ch. 4, 8 |
| `set` operations (`|`, `in`) | track visited items in DFS | Ch. 8 |
| `raise` / custom exceptions | signal illegal states clearly | Ch. 3, 7 |

## Appendix B — The toolchain

| Tool | Role | Key command |
|---|---|---|
| Python 3.11+ | language/runtime | `python3 --version` |
| pip | install dependencies | `python3 -m pip install -e ".[dev]"` |
| pytest | run tests | `python3 -m pytest` |
| Hypothesis | property-based testing | used via `@given` |

> **Where the rest of the original appendices went.** The old single-file guide
> also had three "extra help" appendices. Their content now lives where it's most
> useful for a beginner: the step-by-step setup (old Appendix C) is the numbered
> "Straight-up setup instructions" in [Chapter 1](01-workspace-and-tools.md); the
> "what each chapter produces / what it is NOT" map (old Appendix D) is captured in
> every chapter's **"At a glance"** box and the [README index](README.md); and the
> fuller hints for the early exercises (old Appendix E) are folded into each
> chapter's **"Hints / how to start"** subsections.

---

## A closing reminder on the exercises

> Write the **test first**, watch it fail for the right reason, then make it pass.
> A test that has never failed hasn't proven anything. If you get stuck on an
> exercise for more than ~20 minutes on *mechanics* (not concept), that's a signal
> to ask — the concept is the point, not fighting syntax.

---

Previous: [10 — Proving It Works](10-testing.md) | Back to: [README — index & tools](README.md)
