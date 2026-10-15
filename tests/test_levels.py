from ambition_lite.content import ROOMS, load_level
from ambition_lite.world import World, InputFrame


def test_all_six_ambition_rooms_have_authored_geometry():
    assert len(ROOMS) == 6
    assert [load_level(room).width for room in ROOMS] == [1600, 3200, 2608, 3408, 2000, 1792]
    for name in ROOMS:
        level = load_level(name)
        assert level.height in (512, 704)
        assert level.platforms
        assert level.solids
        assert any(y + h >= level.height for x, y, w, h in level.solids)


def test_birds_and_dinosaurs_are_in_original_ldtk_spawns():
    kinds = {e['kind'] for name in ROOMS for e in load_level(name).enemies}
    assert {'kiwi', 'african_swallow', 'emu', 'compsognathus',
            'npc_raptor_stalker', 'dilophosaurus', 'triceratops'} <= kinds


def test_teaching_density_keeps_end_of_canopy_triceratops():
    world = World('primeval_canopy')
    assert any(e.kind == 'triceratops' for e in world.enemies)
    assert len(world.enemies) < len(world.room.enemies)


def test_doors_connect_six_rooms_in_correct_order():
    for left, right in zip(ROOMS, ROOMS[1:]):
        level = load_level(left)
        assert any(d['target'] == right and d['side'] == 'east' for d in level.doors)
    for left, right in zip(ROOMS, ROOMS[1:]):
        world = World(left)
        door = next(d for d in world.room.doors if d['target'] == right)
        world.player.x = door['x'] - 4
        world.player.y = door['y'] + door['h'] - world.player.h
        world.step(1/60, InputFrame(interact=True))
        assert world.room_name == right
        assert world.player.x < 150


def test_west_door_returns_to_previous_room():
    world = World('primeval_rookery')
    door = next(d for d in world.room.doors if d['side'] == 'west')
    world.player.x, world.player.y = door['x'], door['y'] + door['h'] - world.player.h
    world.step(1/60, InputFrame(interact=True))
    assert world.room_name == 'primeval_run'
    assert world.player.x > 2800


def test_boss_is_last_room_only_and_uses_source_hp():
    for name in ROOMS[:-1]:
        assert load_level(name).boss is None
    boss_room = World(ROOMS[-1])
    assert boss_room.boss.max_hp == 44
    assert boss_room.boss.hp == 44
