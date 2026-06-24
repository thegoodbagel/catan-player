# Map Ingestion Flow — from images to a rigorous format

## The problem

Sites like catancollector.com store their maps and special rules as **images**
(scanned rulebook pages, rendered board diagrams). The page text alone usually
gives only metadata ("Base + Seafarers, 3-4 players, 12 VP, standard rules +
[image]"). To get a machine-readable board we need to extract structure from
pictures. This document proposes a staged pipeline so we don't try to do it all
at once or by hand.

## Target format (what we are converting *to*)

A scenario should ultimately resolve to a small bundle of files (working idea,
not final):

```
scenarios/<game-title>/
  meta.json        # name, source, player counts, VP target, sets needed, credits
  board.json       # hex layout: list of tiles with axial/cube coords + type
  numbers.json     # number token per producing hex
  ports.json       # port locations + trade ratios
  rules.json       # which rule modules / variant bundle to load + parameters
```

Rationale for splitting: layout, numbers, ports, and rules vary independently, so
keeping them separate makes mixing-and-matching (and diffing) easy. They can be
merged into one file later if that proves nicer.

## Coordinate system

Use **axial or cube coordinates** for hexes (standard for hex grids). Vertices and
edges are then derived deterministically from hex coordinates and given stable
integer IDs. This keeps the board addressable by number (good for fast/copyable
state) while staying human-readable in the source files.

## Staged pipeline

### Stage 0 — Manual seed (do this first, by hand)
Hand-author ONE canonical board: the standard base-game island. This is the
reference that proves the format works and that the engine can load it. No
ingestion tooling yet.

### Stage 1 — Schema + validator
Write the JSON schema for the target format and a validator that checks:
- every producing hex has a number token,
- adjacency is consistent (no vertex referencing a missing hex),
- port count/ratios are legal,
- the scenario references a rule bundle that exists.
A loud validator makes every later (error-prone, image-derived) map trustworthy.

### Stage 2 — Assisted transcription (human-in-the-loop)
For each target map image:
1. A human (or a vision model) reads the image and fills a simple intermediate
   form: row-by-row description of tiles + numbers, port positions, special notes.
   This matches the "row-based, +/- offset per row" idea in src-notes.txt and is
   far easier to produce from an image than full coordinates.
2. A converter script turns the row form into the coordinate-based target format.
3. The Stage 1 validator checks it.
4. The engine renders it to ASCII and a human eyeballs it against the original
   image. Mismatch -> fix the row form, repeat.

The row form is the key trick: it is a compact, human-checkable middle language
between "a picture" and "rigorous coordinates."

### Stage 3 — Vision-model batch assist (optional, later)
Once the row form and validator are solid, point a vision-capable model at the
image to draft the row form automatically, then ALWAYS run validator + ASCII
eyeball. Treat the model as a first-draft transcriber, never as the source of
truth. Special rules embedded in images get summarized into `rules.json`
parameters or flagged for manual rule-module work.

## Special rules are separate from layout

Layout extraction (where tiles/numbers/ports are) is mechanical. Special *rules*
(what a volcano does, how fog reveals) are NOT — they map to rule modules in code
or parameters in `rules.json`. Keep these tracks separate: a map can reuse the
"volcano" rule module across many scenarios.

## Suggested order of work

1. Stage 0 (hand-author standard board) — needed for Part 1 anyway.
2. Stage 1 (schema + validator).
3. Stage 2 on 2-3 simple official variants to shake out the format.
4. Stage 3 only if the manual pace is too slow and the validator is trustworthy.

## Licensing note

catancollector.com content is fan-curated, royalty-free-for-non-commercial, and
not official; catan.com material is owned by Catan GmbH. Keep this project's use
non-commercial and attribute sources. Store derived data, not copied images.
