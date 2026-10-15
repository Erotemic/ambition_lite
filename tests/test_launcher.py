"""The classroom entry point works from source, without packaging or SDL."""

import importlib.util
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]


def load_launcher():
    spec = importlib.util.spec_from_file_location('lite_launcher', ROOT / 'main.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('args', [
    ['--headless', '--frames', '5'],
    ['--headless', '--room', 'primeval_tyrant_hall', '--frames', '5'],
    ['--help'],
])
def test_launcher_from_other_directory_works_without_pygame(tmp_path, args):
    result = subprocess.run(
        [sys.executable, str(ROOT / 'main.py'), *args],
        cwd=tmp_path, capture_output=True, text=True, check=True,
    )
    assert result.returncode == 0


def test_installed_pygame_never_installs_or_reexecs(monkeypatch):
    launcher = load_launcher()
    monkeypatch.setattr(launcher.importlib.util, 'find_spec', lambda _: object())
    monkeypatch.setattr(launcher.os, 'execv', lambda *args: pytest.fail('must not reexec'))
    monkeypatch.setattr(launcher.subprocess, 'run', lambda *args, **kwargs: pytest.fail('must not install'))
    launcher._prepare_graphics([])


def test_first_graphical_launch_creates_local_venv_and_reexecs(monkeypatch, tmp_path):
    launcher = load_launcher()
    launcher.ROOT = tmp_path
    launcher.VENV = tmp_path / '.venv'
    monkeypatch.setattr(launcher.importlib.util, 'find_spec', lambda _: None)
    calls = []

    def fake_create(path, *, with_pip):
        calls.append(('venv', path, with_pip))
        python = launcher._venv_python()
        python.parent.mkdir(parents=True)
        python.touch()

    def fake_exec(path, argv):
        calls.append(('exec', path, argv))
        raise RuntimeError('exec was intercepted')

    monkeypatch.setattr(launcher.venv, 'create', fake_create)
    monkeypatch.setattr(launcher.os, 'execv', fake_exec)
    with pytest.raises(RuntimeError, match='exec was intercepted'):
        launcher._prepare_graphics(['--controls', 'wasd'])
    assert calls == [
        ('venv', launcher.VENV, True),
        ('exec', str(launcher._venv_python()),
         [str(launcher._venv_python()), str(tmp_path / 'main.py'), '--controls', 'wasd']),
    ]


def test_in_project_venv_installs_only_game_dependency(monkeypatch, tmp_path):
    launcher = load_launcher()
    launcher.VENV = Path(sys.prefix)
    monkeypatch.setattr(launcher.importlib.util, 'find_spec', lambda _: None)
    calls = []
    monkeypatch.setattr(launcher.subprocess, 'run', lambda *args, **kwargs:
                        calls.append((args, kwargs)))
    launcher._prepare_graphics([])
    assert calls == [(([sys.executable, '-m', 'pip', 'install', 'pygame-ce>=2.5,<3'],),
                     {'check': True})]
