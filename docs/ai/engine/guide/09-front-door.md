# Chapter 9 — The Front Door, Privacy, and Replay

> ## At a glance
> - **Where you are:** The full rules core works — `legal_moves`, `apply`, scoring, and bonuses (Chapters 6–8). But it's all internal functions with no clean surface.
> - **This chapter's goal:** Wrap the machinery in a small, stable public interface (`Game`), add a per-player **view** that enforces hidden information, and add **replay** from the move log.
> - **What this chapter is NOT:** This is not new game logic — the rules are done. You're packaging what exists behind one narrow surface and adding privacy + reproducibility. This is also not the test suite (Chapter 10).
> - **By the end you will have:** `src/engine/game.py` with `Game.new`, the thin delegators (`legal_moves`/`apply`/`is_terminal`/`winner`), `view`/`PlayerView`, and `replay`.
> - **Maps to:** Task 11 in `.kiro/specs/catan-engine/tasks.md` (Task 10 is a checkpoint).
> - **Prerequisites:** Chapters 6–8 (the operations being wrapped) and Chapter 4 (the seedable RNG in state, which replay relies on).

**Goal in plain language.** Give every future client — UI, bot, network, a faster
rewrite — one small set of calls to use, hide secret information correctly in one
place, and make any game reconstructable from its move log.

---

## A small, stable interface

Everything so far is internal. We now expose a handful of calls — the **front
door** — that every future client uses, and nothing else:

```python
class Game:
    @staticmethod
    def new(scenario, num_players, seed): ...     # start a game
    @staticmethod
    def legal_moves(state): ...                   # Chapter 6
    @staticmethod
    def apply(state, move, in_place=False): ...   # Chapter 7
    @staticmethod
    def is_terminal(state): ...
    @staticmethod
    def winner(state): ...
    @staticmethod
    def view(state, player): ...                  # privacy filter, below
    @staticmethod
    def replay(scenario, num_players, seed, moves): ...
```

Because clients touch only this surface, the internals can be rewritten later (for
speed, even in another language) without breaking anything above.

## The view: one place for privacy

Catan has hidden information — your development cards are secret. A single **view**
function decides what one player may see: everything public, plus that player's
own cards, plus only the *counts* of opponents' hidden cards. Centralizing this
means no UI or network message can accidentally leak a hand:

```python
def view(state, player):
    return PlayerView(
        public_board=state.board,
        buildings=(state.settlements, state.cities, state.roads),
        my_cards=state.dev_cards[player],            # mine: exact
        opponent_card_counts=[count_hidden(state, q) # others: counts only
                              for q in range(state.num_players) if q != player],
        legal=legal_moves(state) if player == state.current_player else [],
    )
```

## Replay: reproducing a game from its moves

Because every move was recorded, a game is fully reconstructable by replaying its
log from the start. Combined with a **seedable** random generator (so dice and
shuffles are reproducible), this gives you save/load and exact reproduction — gold
for debugging and, later, for training bots:

```python
def replay(scenario, num_players, seed, moves):
    s = Game.new(scenario, num_players, seed)
    for i, m in enumerate(moves):
        if m not in legal_moves(s):
            raise ReplayError(f"move {i} illegal during replay: {m}")
        s = apply(s, m, in_place=True)
    return s
```

> **Margin notes**
> - **Interface / API**: the agreed set of calls outsiders use; the contract.
> - **Encapsulation**: hiding internals behind that contract so they can change
>   freely.
> - **Seedable RNG**: a random generator started from a fixed seed, so the same
>   seed reproduces the same "random" sequence.

## Exercises

1. **The view.** Implement `view` and `PlayerView`. Test that the current player
   sees their own exact cards and a non-empty legal-move list, and a non-current
   player gets an empty legal-move list.
2. **Privacy property.** Build two states that differ *only* in an opponent's
   hidden cards, and assert that a third player's `view` is identical for both.
   Why is this the precise definition of "no leak"?
3. **Replay round-trip.** Play a short scripted game, capture `state.move_log`,
   call `replay`, and assert the replayed state equals the original. What single
   piece of state, if not seeded, would break this?

### Hints / how to start

**Where the code goes.** `Game`, `PlayerView`, `view`, and `replay` go in
`src/engine/game.py` (the existing stub). `game.py` imports from `rules.py`, not
the other way round. Tests go in `tests/test_view.py` and `tests/test_replay.py`.

- **Ex. 1 (the view).** Make `PlayerView` a frozen dataclass with the fields shown
  in the chapter. The one piece of logic is the `legal=...` line: only the current
  player gets the move list. A passing test:
  ```python
  def test_view_shows_own_cards_and_gates_moves():
      s = make_main_state(current_player=0)
      v0 = Game.view(s, 0)
      assert v0.my_cards == s.dev_cards[0]     # own cards exact
      assert v0.legal                          # current player sees moves
      v1 = Game.view(s, 1)
      assert v1.legal == []                     # non-current player: empty
  ```
- **Ex. 2 (privacy property — the precise definition of "no leak").** Build two
  states identical except for an *opponent's* hidden dev cards, and assert a third
  player's view is byte-for-byte equal across both:
  ```python
  def test_view_hides_opponent_card_identity():
      s1 = make_state()
      s2 = s1.copy()
      swap_hidden_dev_cards(s2, player=1)       # change ONLY player 1's hidden hand
      assert Game.view(s1, 2) == Game.view(s2, 2)   # player 2 cannot tell them apart
  ```
  Why this is *the* definition: if a viewer's observation is identical whenever the
  only difference is information they shouldn't see, then by definition that
  information cannot leak through the view. (This becomes Property 10 in Chapter
  10.) For this to pass, `view` must expose opponents only as *counts*, never
  identities.
- **Ex. 3 (replay round-trip).** Script a handful of legal moves, keep the final
  state, then replay from the same seed and assert equality:
  ```python
  def test_replay_reproduces_game():
      s = Game.new("standard", 4, seed=123)
      for m in scripted_moves:
          s = Game.apply(s, m, in_place=True)
      replayed = Game.replay("standard", 4, seed=123, moves=s.move_log)
      assert states_equal(replayed, s)
  ```
  The answer to "what single piece of state would break this?": the **RNG seed/
  state**. Dice rolls and the steal/shuffle draw from the RNG; if it weren't seeded
  (and reproduced from the same seed), the replay would roll different numbers and
  diverge. That's why `Game.new` takes a `seed`.

## Run your tests

```bash
python3 -m pytest
```

You just added `tests/test_view.py` and `tests/test_replay.py`. The privacy
property (Ex. 2) and the replay round-trip (Ex. 3) are the two that prove the
front door is trustworthy for clients and for the Chapter 10 property suite.

---

Previous: [08 — Scoring, and the One Hard Algorithm](08-scoring.md) | Next: [10 — Proving It Works](10-testing.md)
