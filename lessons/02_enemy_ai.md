# Lesson 2 — Dinosaur decisions

**Concepts:** `if`, `else`, `abs`, functions, return values.

## Predict

Open `src/ambition_lite/ai.py`, and read `decide_enemy_velocity`.
If the player stands 150 pixels to the left of a raptor, what sign will
the returned horizontal speed have? What happens when the player stands
500 pixels away?

## Investigate

```bash
PYTHONPATH=src python -m ambition_lite --headless --room primeval_canopy --frames 240 --trace
```

Play the same room and enable `F3` to see the hitboxes. Compare a flyer
(owl or swallow) with a walker (raptor). Only flyers receive a target
vertical speed from `ai.py`; gravity applies to walkers in `world.py`.

## Modify

Try making an enemy stop moving if it is **within 100 pixels** of the
player, instead of 32. Then give the `compsognathus` a different speed in
`settings.enemy_speed`. Which edit changes AI decisions, and which edit
changes the value returned by a speed policy?

## Explain

Why does a bird need a vertical target while a ground dinosaur does not?
What would be the consequence of giving every enemy unlimited notice range?

**Challenge:** Make `european_swallow` circle the player using sine and
cosine rather than immediately approach it. Use `elapsed` in the function.
