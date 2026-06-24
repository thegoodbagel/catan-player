# Fan Maps — catancollector.com "The Lost Maps"

Source: <https://catancollector.com/maps-scenarios/the-lost-maps> and individual
map pages. **This is a fan-curated, non-official, not-for-profit resource**;
"Catan" IP rests with CATAN GmbH. The site explicitly forbids commercial reuse.
Content paraphrased for licensing compliance.

## CRITICAL caveat: layouts are images

Each map page exposes **text metadata** but stores the actual board layout and
the full special rules as **JPG images** (and downloadable map images). The
hex/number/port layout therefore **cannot be read programmatically** and is
flagged below as **[LAYOUT IN IMAGE — needs manual transcription]** per
`../map-ingestion-flow.md` Stage 2.

## What the page *text* reliably gives (the schema)

Sampled pages (e.g. Gold for Catan, Eruption) show a consistent structure:
- **Title**
- **Sets Needed** (e.g. "Base Set + Seafarers"; sometimes per player-count, and
  may list extra components like "+ one number chit", "+ Volcano hex").
- **Recommended for / player count** (e.g. "3 to 4 players", or split 3-4 vs 5-6).
- Downloadable **map image(s)**, sometimes one per player count.
- **Game Instructions** as short text: usually **Victory (VP target)** and
  **"Standard + rules below"**, then the detailed special rules **as an image**.
- Optional **Introduction** (flavor text).

So machine-readable fields per map: `title, sets_needed, player_counts,
vp_target (sometimes), rules_summary (often image), image_urls`.

### Worked examples (text-extractable)

- **Gold for Catan** — Sets: Base + Seafarers. Players: 3–4. **Victory: 12 VP
  (15 with Cities & Knights).** Rules: standard + map-specific (in image).
  [LAYOUT IN IMAGE]. (Matches the "Gold-for-Catan 12, or 15 w/ C&K" note in
  `../variation-features.md`.)
- **Eruption (3/6 players)** — Sets: Base (+ Base 5/6 for the larger version),
  plus **one extra number chit** and **volcano hex(es)** (1 for 3–4, 3 for 5–6).
  Setup = standard base layout but a **volcano replaces the desert**; for 5–6, one
  pasture hex is dropped. Uses the shared **Volcano rules**. [LAYOUT IN IMAGE].

## Full catalogue (as indexed; metadata UNVERIFIED, layouts in images)

### Fan maps
Across the Wasteland · Another Catan · Apocalypse 3/4 · Apocalypse 5/6 ·
Arctic Mist · Castaways · Crater · Deadliest Catch · Diamond Seas · Drought ·
Enchanted Land · Fog Mountain · Four Kingdoms · Gold for Catan · Greater Catan ·
Krakatoa (3-4) · Lush Overgrowth · Nautilus · Oku Islands ·
One Island (5/6) · Peanut · Resource Regions · Resource Rows ·
Rohan & Gondor · Six Kingdoms · Skull Island · Small Archipelago · Ten Islands ·
The Great Plains · Tropic Mist · Twin Harbours · Undiscovered Riches · Valera ·
Wonders of Westeros · Eruption (3/6) · Archipelago · Bulls Eye · Snowflake Island

### Catan Atlas (real-world places)
Andalusia · Galapagos Affair · New Zealand · Newfoundland · North America ·
World Map · British Isles · South America

### Tournament maps
- **2025 Catan World Championship** — 4 maps (Stuttgart, April 2025).
- **2024 US National Championship** — 4 maps (Saint Paul, Sept 2024).
- Miscellaneous tournament maps: Tournament #01–#05 (e.g. Origins 2015 qualifier,
  2015 USA National final, CatanCon 2016 qualifier).

> Tournament maps are typically **fixed standard-rule layouts** (knob 1 = fixed
> placement, everything else base). They are the best candidates for early
> transcription since rules = base. **[LAYOUTS IN IMAGES.]**

## Special hex / resource rule modules (reusable across maps)

The site also publishes standalone **hex rules** that several maps share — these
map cleanly onto our "rule module" idea (knob 2/13). Rules detail is in images,
but the *concept* of each is clear:

| Hex | Concept (knob 2/13) | Notes |
|-----|---------------------|-------|
| **Volcano** | hazard hex; can erupt and affect adjacent tiles/pieces | used by Eruption, Krakatoa; [RULE], details in image |
| **Jungle** | overgrowth hex with its own production/movement rule | [RULE], details in image |
| **Iceberg** | sea hazard / movable cold hex | [RULE], details in image |
| **Earthquake** | removes/shifts number tokens or pieces | matches "earthquake removes tokens" in variation-features; [RULE][STATE] |
| **Soccer field** | themed special hex (Soccer Fever crossover) | [RULE] |

## Themes observed (for the topology/tile-type knobs)

- **Archipelago / islands**: Archipelago, Small Archipelago, Ten Islands,
  Nautilus, Oku Islands, Castaways, One Island, Twin Harbours → knob 1 (many
  disconnected landmasses), usually need Seafarers.
- **Mist/fog**: Arctic Mist, Tropic Mist, Fog Mountain → knob 2/13 (fog reveal).
- **Hazard/disaster**: Eruption, Krakatoa, Crater, Drought, Apocalypse,
  Earthquake → knob 13 (one-off scenario mechanics).
- **Resource-distribution gimmicks**: Resource Regions, Resource Rows → knob 1/2
  (deterministic resource zoning).
- **Licensed/fiction themes**: Rohan & Gondor, Wonders of Westeros, Valera,
  Four/Six Kingdoms → mostly re-themes over base/Seafarers.
- **Real geography**: the Catan Atlas set → fixed layouts shaped like real places.

## Engine notes

- Almost everything here reduces to **(a) a layout** (knob 1/2, locked in an
  image → manual/vision transcription per `map-ingestion-flow.md`) plus
  **(b) a small set of shared rule modules** (volcano/jungle/iceberg/earthquake/
  fog). Build the modules once; reuse across many maps.
- Page **text** is enough to auto-populate `meta.json` (title, sets, players,
  VP, source URL, image URLs). The **board/number/port layout and the exact
  special rules are NOT text** — do not invent them; transcribe from images and
  validate (Stage 1 validator + ASCII eyeball).
- VP targets seen in text trend to **12** for fan maps (and **15** when combined
  with Cities & Knights), consistent with `../variation-features.md`.
