# Official — CATAN: Cities & Knights

Source: official rules hub <https://www.catan.com/understand-catan/game-rules>
(Cities & Knights PDF) and <https://www.catan.com/cities-knights> /
<https://colonist.io/catan-rules/cities-and-knights> for cross-checking.
Content paraphrased for licensing compliance. Specific counts are **UNVERIFIED**
until checked against the PDF.

This is the most mechanically complex official expansion. It layers commodities,
a third die, knights, city walls, city improvements/metropolis, and a shared
**barbarian** threat. It is the variant that most stresses the engine's phase
machine and additive-state design.

## Delta from base game

### Numbers / dice (knob 3) [RULE]
- Adds a **third die, the event die** (colored), rolled every turn alongside the
  two production dice.
  - Three faces show a **barbarian ship** (advances the barbarian track one
    step).
  - Three faces show **colored symbols** (yellow/green/blue) that, combined with
    the production dice value, trigger **progress card** draws for players whose
    relevant **city improvement** level is high enough.

### Resources & commodities (knob 4) [STATE][RULE]
- Adds **3 commodities** layered on the base resources:
  - **Coin** (from mountains/ore region, upgraded),
  - **Cloth** (from pasture/wool region),
  - **Paper** (from forest/wood region).
- **Cities** produce a commodity in addition to the base resource of the
  upgraded hex; settlements do not. Commodities are a parallel inventory.

### Buildings & pieces (knob 5) [STATE][RULE]
- **Knights**: placed on the board as units with strength levels (basic /
  strong / mighty). Knights can be **activated** (costs grain), **promoted**
  (costs ore), and used to **chase the robber**, **attack other knights**, or
  **build/move** along roads. Activated knights defend against barbarians.
- **City walls**: raise a city's robber-discard hand-limit threshold.
- **City improvements**: each city player tracks three improvement tracks
  (trade/yellow, politics/blue, science/green) bought with the corresponding
  commodity. Reaching level 4 on a track earns a **metropolis** (+2 VP, and a
  fortified city).

### The robber + barbarians (knob 6) [RULE][STATE]
- Robber still exists but is initially **inactive** until the first city is
  built (**UNVERIFIED** exact trigger).
- **Barbarians**: a shared ship on a track. Each barbarian event-die face moves
  it forward; when it arrives, it **attacks**:
  - Total **activated knight strength of all players** vs. **number of cities on
    the board**.
  - If defenders win, the single strongest contributor gets a **Defender of
    Catan** VP; if defenders lose, the player(s) with the **least** knight
    strength lose a city (downgraded to settlement).
  - The barbarian then resets and advances again. This is a **cooperative/
    semi-cooperative threat** — a [HARD] mechanic.

### Turn structure (knob 7) [RULE] — extra phases
1. Roll **all three dice** (2 production + 1 event).
2. Resolve **event die**: barbarian advance **or** progress-card distribution.
3. Production (resources to settlements/cities, commodities to cities).
4. Trade / build / buy / knight actions.
The barbarian arrival is an interrupt that resolves between roll and the rest.

### Development → Progress cards (knob 9) [STATE][RULE]
- Base dev deck is **replaced** by **progress cards** in three decks
  (trade/politics/science) tied to the three city-improvement tracks. Drawn
  based on the event die + your improvement level. Effects are more varied than
  base dev cards (e.g. spy, bishop, trade monopoly, engineer, alchemist, etc.).
- **Knights are board units, not cards** here (unlike the base "knight" dev
  card). Largest Army is **replaced** by the barbarian/Defender system.

### Victory conditions (knob 10) [RULE]
- Win target is commonly **13 VP** (**UNVERIFIED**; widely cited).
- New point sources: **metropolis (+2 each, up to 3 possible across players)**,
  **Defender of Catan** VP cards, plus base settlement/city/Longest Road.
- **Largest Army is removed** (knights work differently).

## Engine notes

- Heavily additive state: `commodities[coin/cloth/paper]`, per-player
  `improvement_levels[3]`, `knights[]` with `(strength, active)`, `city_walls`,
  global `barbarian_position`, `metropolis_owner[3]`.
- The **event die + barbarian step** is the canonical example of "a variant adds
  ordered phases." Build the FSM so these slot in.
- Production becomes two-channel (resources + commodities) and city-aware.
- Combine with Seafarers in some setups; VP target then cited as ~15
  (**UNVERIFIED**, also noted in `../variation-features.md`).
