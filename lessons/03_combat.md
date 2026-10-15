# Lesson 3 — Moves have phases

**Concepts:** dataclasses, timing, comparisons, collision rectangles.

## Predict

Open `src/ambition_lite/combat.py`. A heavy smash takes 0.26 seconds to
start and deals 7 damage. A side slash takes 0.10 seconds to start and
deals 3. Predict which move is better if the T-rex is about to bite, and
which defeats a 6-HP dinosaur in fewer hits.

## Investigate

Run the game in the last room:

```bash
python -m ambition_lite --room primeval_tyrant_hall
```

Use `F3` while swinging (`X`, `Up` + `X`, `Down` + `X`, `A` in the
default Rust-style layout). Note that the
yellow collision rectangle only exists while the move is **active**, not
while it starts or recovers. In `world.py`, locate `_attack_step`.

## Modify

In `MOVES`, give the side slash a shorter reach but faster startup. Play
again and decide whether it feels easier or harder to land. Then change
only the heavy smash's recovery time, keeping its damage and reach intact.

## Explain

What does the set `ActiveAttack.hit_ids` prevent? Why might a sword that
stays active for three frames otherwise damage an enemy three times?

**Challenge:** Add a `poke` move in the combat table and bind it to a new
key in `controls.py` and `_start_attack` in `world.py`.
