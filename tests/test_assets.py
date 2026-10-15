import struct
import wave
from pathlib import Path

from ambition_lite.content import asset_root
from ambition_lite.pose import Rig, interpolate_angle
from ambition_lite.__main__ import main


def test_robot_and_trex_rigs_are_made_of_independent_parts():
    root = asset_root()
    for name, expected_parts in (('robot',29), ('trex',31)):
        rig = Rig(name)
        assert len(rig.parts) == expected_parts
        assert len(rig.clips) >= 10
        for part in rig.parts:
            assert part['bone'] in rig.parents
            assert len(part['crop_pivot']) == 2
            png = root / 'parts' / name / (part['name'] + '.png')
            assert png.read_bytes()[:8] == b'\x89PNG\r\n\x1a\n'
    assert len(list((root / 'creatures').glob('*.png'))) >= 12


def test_pose_editor_rotates_entire_arm_hierarchy():
    rig = Rig('robot')
    pose = rig.sample('idle', 0)
    assert rig.parents['near_arm_l'] == 'near_arm_u'
    before = pose.bones['near_arm_l']
    rig.adjust(pose, 'near_arm_u', 20)
    after = pose.bones['near_arm_l']
    assert after[:2] != before[:2]
    assert after[2] != before[2]
    assert pose.bones['near_arm_u'][2] != rig.sample('idle', 0).bones['near_arm_u'][2]


def test_looping_and_one_shot_pose_time():
    rig = Rig('robot')
    loop = rig.clips['idle']
    seconds = len(loop['frames']) * loop['frame_ms']/1000
    a, b = rig.sample('idle', 0), rig.sample('idle', seconds)
    assert a.bones == b.bones
    assert rig.sample('smash_forward', 999).bones == rig.sample('smash_forward', 998).bones
    assert interpolate_angle(179, -179, .5) == 180


def test_audio_tracks_and_fx_are_standard_mono_wavs():
    root = asset_root() / 'audio'
    for name in ('primeval','boss','jump','dash','hit','boss_hit','victory'):
        with wave.open(str(root / (name+'.wav')), 'rb') as sound:
            assert sound.getnchannels() == 1
            assert sound.getsampwidth() == 2
            assert sound.getframerate() == 22050
            assert sound.getnframes() > 1000


def test_headless_demo_runs_without_pygame(capsys):
    assert main(['--headless','--frames','90']) == 0
    out = capsys.readouterr().out
    assert 'frames=90' in out
    assert 'room=primeval_trailhead' in out
