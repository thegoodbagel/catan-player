# Project Conventions

## AI provenance: the `# AI-generated` marker

Files whose initial content was authored primarily by an AI assistant carry a
marker comment as their **first line**:

```python
# AI-generated
```

This is informational provenance, not a statement of authorship or license:
ownership of all code remains with the repository owner regardless of the marker.

### Rules

- **Placement.** First line of the file. If the file needs a shebang or encoding
  line, those come first and the marker goes immediately after.
- **When to add it.** Only on files the AI created wholesale (for example, a test
  module written from scratch).
- **When not to add it.** Files with substantial human authorship — including files
  the AI scaffolded but a person then materially edited — are left untagged. Git
  history (`git blame`, `git log`) is the source of truth for mixed authorship and
  stays accurate as files evolve, so a hand-written tag would only go stale.
- **No `@author` tags.** Human authorship is tracked through git history rather than
  in-file tags, for the same staleness reason.

### Currently tagged

- `tests/test_board_data.py`
