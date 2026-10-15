# Lesson 4 — Make a robot with movable parts

**Concepts:** images, coordinates, parent-child relationships, loops.

## Predict

In the game press `F2` to pause and open Pose Lab. Press `Tab` until
`head` is selected. Predict what will move when you rotate the head with
`[` and `]`. Then select `near_arm_u`. Predict what happens to the elbow
and hand when you rotate the shoulder.

## Investigate

The original SVG source is `assets/svg/player-robot-v3.svg`. The 29
individual PNG cutouts are in `assets/parts/robot/`. Inspect
`assets/rigs/robot.json`: every part binds to a `bone`, has a `pivot`, and
may have an `opacity_channel` (the sword is visible during sword clips).
The animator interpolates sampled poses in `pose.py`; the painter rotates
and blits each part in `graphics.py`.

## Modify

In the `idle` clip in `assets/rigs/robot.json`, change the first frame's
`head` rotation by five degrees. Save the JSON and start the game again.
`F2` is an interactive experiment that does not alter the source files;
editing the JSON makes a lasting change.

To modify the actual SVG shape of a blade or finger, edit the matching
part group in `assets/svg/player-robot-v3.svg` in Inkscape or an XML editor,
and rebuild its PNG:

```bash
python -m pip install -e '.[authoring]'
python tools/build_parts.py robot
```

## Explain

Why is the head part's `crop_pivot` not always the center of its PNG?
How can a parent bone rotate a child bone without rewriting the child SVG?
Why is a one-time rasterization step helpful for a game that redraws sixty
times per second?

**Challenge:** Author a new pose called `wave` by copying `idle` in the
JSON and changing the upper arm, elbow, and hand rotations. Connect it
to a key or a victory animation in `graphics.py`.
