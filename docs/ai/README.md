# docs/ai — Research Scratchpad

This folder is a working scratchpad for the research/idea-generation phase of the
Catan project. Nothing here is final or authoritative. It exists to collect and
organize what we learn before committing to a rigorous spec.

## Contents

- `variation-features.md` — The core deliverable: the *dimensions* along which
  Catan games vary (not a list of every scenario, but the knobs that scenarios
  turn). This is the document that should most directly shape the engine design.
- `map-ingestion-flow.md` — A proposed pipeline for turning the map *images* on
  sites like catancollector.com into a rigorous, machine-readable format later.
- `scenario-index.md` — A catalogue of known official games and fan scenarios,
  with whatever metadata we could extract so far.

## Important caveats (read before trusting anything here)

- The detailed hex layouts and special rules on catancollector.com are stored as
  **images**, which could not be read programmatically. Descriptions of fan maps
  are therefore incomplete and based only on page text + general knowledge.
- Descriptions of the **official** games (base, Seafarers, Cities & Knights,
  Traders & Barbarians, Explorers & Pirates) are from general knowledge of the
  published rules and should be verified against an actual rulebook before being
  encoded into data.
- Sources consulted: catan.com (official stand-alones/variants list) and
  catancollector.com (fan map index). Content was rephrased for compliance with
  licensing restrictions; catancollector material is fan-curated and not official.
