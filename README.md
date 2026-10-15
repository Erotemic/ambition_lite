# ambition_lite

A teachable 2D platformer in **Python and Pygame**, using the robot art and
six-room **Primeval Trail** from Ambition. It is a *different repository* from
both Ambition and `cc_templates`. There is no Rust, rollback simulation,
networking, Android build, or professional audio software in the runtime.

## Start playing

Open a terminal in this repository and run:

```bash
python main.py
```

**No editable install, `PYTHONPATH`, or virtualenv activation is necessary.**
On the first graphical launch, `main.py` checks for Pygame. If it is missing,
it creates a project-local `.venv`, installs `pygame-ce` there, and starts the
game. This one-time setup requires internet access and Python 3.10+ with venv
support; later launches reuse the installation. Nothing is installed into the
system Python. On Linux, `python3 main.py` works if `python` is not defined.

Launch options use the same simple command:

```bash
python main.py --room primeval_canopy
python main.py --controls wasd
python main.py --mute
python main.py --headless --frames 360 --trace
python main.py --help
```

Headless mode and `--help` work **without Pygame or network access**. For a
screenshot, run `python main.py --screenshot screenshots/scene.png` after
creating the output folder. You can still use `python -m ambition_lite` or
`ambition-lite` after manually installing the package, but they are optional.

### Controls (Ambition's Rust defaults)

The initial keyboard layout is **Arrows + Z/X/C**, matching the first
`KeyboardPreset` in Ambition's `ambition_input/src/presets.rs`. Press `F4` to
cycle between Rust's four keyboard presets at any time. To start directly
with the WASD layout:

```bash
python main.py --controls wasd
```

| Action | Default: Arrows + Z/X/C | WASD + Space/J/K/L |
|---|---|---|
| Move / aim | Arrow keys | W/A/S/D |
| Jump / double jump | `Z` | `Space` |
| Directional sword attack / coconut | `X` | `J` |
| Dash / burst | `C` | `K` |
| Heavy smash | `A` | `L` |
| Fire bolt | `V` | `H` |
| Enter door | `F` | `E` |
| Walk | Hold either `Shift` key | Hold either `Shift` key |

Hold `Up` + attack to swing upward, or `Down` + attack to swing downward;
for example `Up+X` with the default layout. The heavy attack uses **the
Rust secondary/Blink key**, repurposed for Lite because Blink is not included.
Shift *walks* in Rust; it no longer triggers dash here. The other Rust
keyboard presets are **Arrows + Q/W/E/R** (`qwer`) and **WASD + U/I/P/O**
(`uipo`), also selectable with `--controls` or `F4`.

An SDL-mapped controller uses Ambition's default gamepad layout for shared
actions: **left stick / D-pad** move, **South/A** jump, **West/X** attack,
**Right trigger/RT** dash, **North/Y** projectile, **Right shoulder/RB** door,
**Start** pause, **Back/Select** reset. **East/B** is Lite's heavy attack in
place of the omitted Blink. Analog stick tilt allows walking. Controller
support uses Pygame's SDL mapping for standard Xbox/PlayStation-style pads;
unmapped joysticks are not assigned guessed button numbers.

`R` restarts the current room, `F2` opens the Pose Lab (`Tab` select,
`[` / `]` rotate, `R` reset pose), `F3` toggles collision boxes, and
`Esc` pauses/resumes. While paused, press `Q` to quit, or close the window.
The bottom-of-screen instructions update when you switch presets.

Defeat the T-rex in the last room. Rooms are long, and the camera scrolls.
The game uses the **actual LDtk solid/one-way collision map** for each of the
six rooms, with the original platform and doorway locations. The source level
has many enemy spawns; the teaching edition selects approximately half by
default. Change `ENEMY_STEP` in `settings.py` to restore every supported spawn
(the `willson` cameo is intentionally omitted).

## Start learning

The shortest path is:

1. `lessons/01_movement.md` — change the jump equation and predict what occurs.
2. `lessons/02_enemy_ai.md` — make a dinosaur react to the player's position.
3. `lessons/03_combat.md` — adjust slash startup, reach, and damage.
4. `lessons/04_pose_and_assets.md` — pose real articulated SVG robot limbs.
5. `lessons/05_input_mapping.md` — optional activity: map physical keys to game actions.

Read `docs/ARCHITECTURE.md` for a guided map of the code. Every exercise has a
**Predict → Investigate → Modify → Explain** loop and a concrete command. The
simulation can run without Pygame, including in a classroom autograder:

```bash
python main.py --headless --frames 360 --trace
python -m pip install pytest  # if you want to run the tests
python -m pytest -q
```

## What was retained and what was simplified

| From Ambition | In ambition_lite |
|---|---|
| Six authored Primeval Trail rooms (trailhead, run, rookery, ridge, canopy, tyrant hall) | Real LDtk collision/platform geometry and original locations in `assets/levels/*.json` |
| Player Robot V3 SVG with named body parts and pose clips | Original SVG, **29 independent sprite parts** and 20 sampled, adjustable animation clips |
| Rigged SVG T-rex | Original SVG, **31 parts**, 10 clips, 44 HP, multi-phase boss |
| Many original bird and dinosaur SVGs | 18 simplified static sprite species, straightforward chase/patrol/fly/spit behavior |
| Full Rust fighting and item systems | Side/up/down/air slashes, heavy smash, bolts, coconuts, knockback, HP |
| Complex adaptive rendered score | Two new loopable chip tunes + generated 8-bit-style SFX |
| Original regeneration suite and Qt editors | Two small SVG-to-PNG scripts, one standalone WAV generator, optional importer |

The original pelican-on-a-bicycle `willson` enemy isn't shipped in Lite (the
source archive has no matching standalone Willson SVG). The LDtk spawn remains
in JSON as a reference. Other excluded game features include shield, blink,
flight, rollback/netplay, full platform-fighter rules, interactive NPCs and
adaptive audio. The T-rex encounter is a **simplified** implementation of the
boss pattern, not a mechanically exact Rust port.

## Rebuild / modify art and audio

The game needs only Pygame. **All required PNGs and WAVs are already in the
repository.** To regenerate them after editing the included SVG files:

```bash
python -m pip install -e '.[authoring]'
python tools/build_parts.py
python tools/build_creatures.py
python tools/build_audio.py
```

You may directly edit `assets/rigs/robot.json` to change poses; the
`frames[].bones` entries give each named joint's `[x, y, degrees]`, and
`frames[].params` controls blade and face visibility. `F2` demonstrates
hierarchical posing interactively. The source SVG artwork is in
`assets/svg/`, with one cropped raster per body part in `assets/parts/`.

**Optional re-import from your own checkout of Ambition:**

```bash
python tools/import_ambition.py --ambition-root ../ambition
python tools/build_parts.py
```

This optional command needs the source repo's existing Python sprite renderer
because it samples upstream IK/spline animation clips; it is **not** needed to
play, edit Lite poses, or regenerate art from the included SVGs.

## Provenance

See [NOTICE](NOTICE) and [LICENSE](LICENSE). The supplied source archives from
Ambition and `cc_templates` are Apache-2.0. All reused SVG and level content
is attributed to Ambition; new chip-tune compositions and Python gameplay
logic are authored for this smaller educational project.
