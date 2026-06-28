# Building a Game Engine: The Catan Project — moved

*A hands-on course in designing correct, extensible software.*

> **This guide has been split into one file per chapter.**
> It used to be a single long document; it is now a folder of focused chapters,
> each enriched with beginner-friendly walkthrough pointers, exercise hints, and
> an "At a glance" summary box. Start here:
>
> ### → [guide/README.md](guide/README.md) — index, "how to use this guide", and the tools intro

## Chapter files

| File | Chapter | Maps to task |
|---|---|---|
| [guide/00-central-idea.md](guide/00-central-idea.md) | The central idea: facts vs. rules | Foundational |
| [guide/01-workspace-and-tools.md](guide/01-workspace-and-tools.md) | Workspace & tools (full setup) | Task 1 |
| [guide/02-vocabulary.md](guide/02-vocabulary.md) | The vocabulary of the game | Task 2 |
| [guide/03-board.md](guide/03-board.md) | The board as a graph | Task 3 |
| [guide/04-state.md](guide/04-state.md) | The game state and cheap copying | Task 4 |
| [guide/05-variant-bundle.md](guide/05-variant-bundle.md) | The rulebook as data | Task 5 |
| [guide/06-legal-moves.md](guide/06-legal-moves.md) | Legal-move generation | Task 6 |
| [guide/07-apply.md](guide/07-apply.md) | Applying moves | Task 8 |
| [guide/08-scoring.md](guide/08-scoring.md) | Scoring & the one hard algorithm | Task 9 |
| [guide/09-front-door.md](guide/09-front-door.md) | The front door, privacy, replay | Task 11 |
| [guide/10-testing.md](guide/10-testing.md) | Proving it works | Task 12 |
| [guide/11-afterword.md](guide/11-afterword.md) | Afterword & appendices | Checkpoints (7/10/13) |

The canonical task checklist this guide pairs with is
`.kiro/specs/catan-engine/tasks.md`.

---

*Why the split: the chapters are easier to navigate, each opens with a summary box
telling you what it is and is not, and the exercises now include step-by-step
"how to start" hints. Nothing was removed — all original prose and code examples
were preserved and redistributed across the chapter files.*
