# Project Conventions

## Jargon/Tone
Please explain things in a simple, clear and concise manner, textbook-style, avoiding jargon and pretentious tones. For instance, instead of the following:

One high-level heads-up on the algorithm I'm using, since you offered to field questions: rather than the "left/top-left owner + offset table" scheme we discussed, I'm using the canonical-key-by-surrounding-hexes method, which is orientation-agnostic and provably correct without me hand-deriving an offset table. Each corner is identified by the set of (up to 3) hexes meeting there: corner(H, i) = {H, neighbor_i, neighbor_{i+1}} (two consecutive directions). Two hexes approaching the same physical corner produce the same set, so dedup is automatic, and boundary corners work because off-board phantom neighbors still go into the key. Same idea for edges ({H, neighbor_i}). I verified your six HEX_DIRECTION_OFFSETS are in proper rotational order, which is the one precondition this needs. If you'd prefer the owner+slot scheme for pedagogical reasons, say so; otherwise this is cleaner and I'll go with it.

We could revise to:

In the algorithm we using, each corner is defined by the set of hexes touching it: corner(H, i) = {H1, H2, H3}. The same physical corner produces the same set no matter which hex you approach from, so de-duplication reduces it to ID. In a similar fashion, edges are are defined with two vertices: {H1, H2}. In addition, boundary corners work because hexes off the board still have a valid representation and can be part of the set. The only requirement is that the six direction offsets go around the hex in order, which ours does.

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