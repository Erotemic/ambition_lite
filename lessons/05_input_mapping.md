# Optional lesson 5 — Physical keys vs game actions

**Concepts:** data tables, sets, booleans, and state across frames.

## Predict

Open `src/ambition_lite/controls.py`. Find `PRESETS`: both `X` (classic) and
`J` (WASD) are mapped to the **same** logical attack action. Predict what
happens if you change the classic attack key from `x` to `b`.

## Investigate

Run `python main.py`. Use `F4` to switch between the classic
and WASD presets. Watch how the bottom HUD and the door prompt update. Press
an attack key, hold it, release it, then press it again. Why is this
one attack per *new press*, instead of 60 attacks per second?

Read `ControlReader.sample()`: `active` describes which actions are held on
this frame and `new_actions` is the difference from the previous frame.

## Modify

Change one key in `PRESETS`, run the game and confirm that the game uses the
new binding without changes to `world.py`. Verify with `pytest -q`.

## Explain

Why is it helpful for both `KeyboardPreset` and `PadState` to produce one
`InputFrame`? When a student changes the default controls, which other code
should stay unchanged?

**Challenge:** Add a fifth keyboard preset, while keeping the same game
rules. `F4` should cycle to the new preset automatically.
