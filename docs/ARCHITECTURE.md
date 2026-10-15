# A one-page map of the game

The primary student entry point is `src/ambition_lite/settings.py`. Each
lesson names exactly one or two other files; beginners do not need to learn
what a renderer, sprite atlas or ECS is before writing an `if` statement.

```text
                 keyboard                    editable LDtk-derived JSON
                    |                                   |
                    v                                   v
         game.py (Pygame loop)  ---->  content.py (six rooms)
                    |                                   |
                    v                                   v
             InputFrame --------------> World.step()
                                            |
                             +--------------+-------------+
                             |              |             |
                        physics         ai.py          combat.py
                             |              |             |
                             +--------------+-------------+
                                            |
                                        GameEvent
                                            |
                       +--------------------+----------------+
                       |                                     |
                    audio.py                             graphics.py
              (simple WAV playback)               (puppet / tiles / HUD)
                                                             |
                                                 pose.py + PNG/SVG parts
```

## One place to advance time

`World.step(dt, InputFrame)` owns the game's motion, damage, boss and room
rules. Neither graphics nor audio changes the simulation. Tests and the
headless CLI drive the **same** code that the window uses. That is enough of
the architecture principle from `cc_templates`; this game intentionally has
no command/event-sourcing protocol, rollback, or multiplayer authority.

## Readable boundaries

- `settings.py`: numbers and a one-function enemy speed policy.
- `world.py`: dataclasses for player, enemy, boss, coconut, bolt; the one `step`.
- `ai.py`: small species grouping and chase/flier decisions.
- `combat.py`: the active hitbox as one rectangle in one time window.
- `content.py`: loads the exact authored level JSON files.
- `pose.py`: interpolates prerecorded bone worlds, and rotates one joint plus
  its descendants when an author moves it.
- `graphics.py`: transforms original SVG-part rasters around joint pivots.
- `audio.py`: one optional channel for music and pooled sound-effect playback.

## Assets are editable and attributed

Upstream Ambition has an SVG paper-doll authoring renderer that solves IK
and spline animation expressions. The one-time importer samples a **small
selection** of those clips into simple JSON worlds (position and rotation of
each joint) and copies the original SVG source. The in-repo `build_parts.py`
only splits that SVG into PNG parts, so students can inspect and modify the
part code without needing the upstream rig toolkit. SFX and music are short
self-contained Python generators. The authoring programs are not runtime
dependencies.

## Debug without a window

```bash
PYTHONPATH=src python -m ambition_lite --headless --room primeval_rookery --trace --frames 240
PYTHONPATH=src python -m pytest -q
```

The gameplay tests assert consequences (movement, jump count, damage, phases,
doors, geometry). They do **not** freeze teaching prose, HUD labels or art
pixel values. For a live visual debugging session, use `F3` for hitboxes and
`F2` for joints.
