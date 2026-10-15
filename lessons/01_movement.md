# Lesson 1 — Predict a jump

**Concepts:** variables, arithmetic, conditionals, gravity and frames.

## Predict

Open `src/ambition_lite/settings.py`. `JUMP_SPEED` starts at 515
pixels/second; `GRAVITY` is 1100 pixels/second². Without running the
game, predict whether the robot rises higher if you change `JUMP_SPEED`
to 600. Predict the effect of doubling gravity.

## Investigate

Run from the repository root (no Pygame needed):

```bash
python main.py --headless --frames 160 --trace
```

The trace prints the first jump, the second jump, and the player's final
position. Read `_player_step` and `_move_solid` in `world.py`; note that
velocity is in pixels per second while `dt` is in seconds per frame.

## Modify

Set `JUMP_SPEED = 600`, rerun the same command, and compare positions.
To see it, run `python main.py` and press `Z` to jump onto the first ledge
(or `F4` to switch to the WASD/Space layout).

## Explain

What does it mean when vertical velocity changes sign from negative to
positive? Where is gravity applied? Why do we multiply both speed and
gravity by `dt` instead of adding the same distance on every frame?

**Challenge:** Only permit the second jump if the first has already reached
its highest point. Which comparison of `p.vy` would accomplish that?
