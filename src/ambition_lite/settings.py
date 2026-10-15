"""The first file for students to edit.

The core rules are ordinary Python and every number here has a visible
meaning in the game. Try changing one value, make a prediction, then play.
"""

# Movement (world pixels and seconds)
RUN_SPEED = 290.0
WALK_AXIS_CAP = 0.5  # Rust Shift+Move movement cap
JUMP_SPEED = 515.0
DOUBLE_JUMP_SPEED = 490.0
GRAVITY = 1100.0
MAX_FALL_SPEED = 790.0
DASH_SPEED = 690.0
DASH_TIME = 0.20
DASH_COOLDOWN = 0.65

# The original Primeval Trail is kept intact in assets/levels. The teaching
# version fights approximately half of its regular spawns, so a class can
# finish the level. Set to 1 for all of them, or 3 for every third one.
ENEMY_STEP = 2

PLAYER_MAX_HP = 12
TREX_MAX_HP = 44  # from Ambition's trex_boss.ron

# How far enemies can notice the player, and how hard they collide.
ENEMY_NOTICE_RANGE = 370
CONTACT_DAMAGE = 1

# The camera, HUD, and audio use these dimensions.
WINDOW_SIZE = (960, 540)
FPS = 60


def enemy_speed(kind: str) -> float:
    """Student exercise: make birds or raptors faster without touching AI."""
    if kind in {'emu', 'ostrich', 'ostrich_hen', 'cassowary'}:
        return 155.0
    if kind in {'npc_raptor_stalker', 'compsognathus'}:
        return 128.0
    if kind in {'triceratops', 'pachycephalosaurus'}:
        return 75.0
    if kind in {'kiwi', 'penguin', 'chicken', 'chicken_hen'}:
        return 76.0
    return 94.0
