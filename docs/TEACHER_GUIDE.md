# Teacher guide — suggested four-session workshop

**Audience:** students learning introductory Python; each exercise can be
studied without requiring a production game engine or Rust.

The course follows the `cc_templates` principle of small, independently
understandable edits. It does not ask beginners to replace the engine.

- **Session 1:** variables and motion: read `settings.py`, predict new jump
  height, change one number, play, explain with a velocity sketch.
- **Session 2:** conditional decisions: have students change an enemy's
  notice radius and explain a new behavior in terms of player distance.
- **Session 3:** lists and time windows: alter a move in `combat.py`, inspect
  its yellow hitbox with F3, and discuss one-hit-per-target sets.
- **Session 4:** hierarchical geometry and assets: rotate a joint in F2,
  then change the equivalent authored `robot.json` pose. Advanced students
  can edit the SVG itself and rebuild part PNGs.

## Preparation

Run `python main.py` from the repo root on classroom machines. On first
graphical launch it installs Pygame into a local `.venv` (internet required
once); later launches reuse it. The `python main.py --headless` lesson
commands work offline with Python alone. Audio and SVG editing are optional. `pytest` is a developer dependency for regression checks,
not a requirement for an introductory lesson.

The default controls mirror Rust (Arrows + Z/X/C); `F4` cycles to WASD
for students who prefer it. Students can inspect `controls.py` to see how
physical keys become abstract actions without modifying the game rules.

Students should keep original JSON and SVG files in version control so
experiments can be reverted. The T-rex may take several tries to defeat:
teachers can reduce its HP in `settings.py` during a short class.

## What to evaluate

Ask students for their *prediction*, a before/after observation, a code
change, and a short explanation. Avoid grading exact source text or copied
solutions. The tests focus on runtime mechanics, not prose.

## Teaching boundary

The imported Primeval Trail includes original geometries and selected
character visuals, but Lite does not replicate all Ambition systems. A
lesson about simple chase AI is intentionally not a lesson about the
original Rust AI architecture or deterministic rollback.
