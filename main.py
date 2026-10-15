#!/usr/bin/env python3
"""Play Ambition Lite: ``python main.py`` (no package install needed).

On the first graphical run, install Pygame into this repo's private .venv
if it is not already available. ``--headless`` and ``--help`` need no Pygame.
"""
from __future__ import annotations

import importlib
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import venv

ROOT = Path(__file__).resolve().parent
VENV = ROOT / '.venv'
PYGAME_REQUIREMENT = 'pygame-ce>=2.5,<3'


def _venv_python() -> Path:
    if os.name == 'nt':
        return VENV / 'Scripts' / 'python.exe'
    return VENV / 'bin' / 'python'


def _prepare_graphics(argv: list[str]) -> None:
    """Make graphical launches work without touching the system Python."""
    if importlib.util.find_spec('pygame') is not None:
        return

    if Path(sys.prefix).resolve() != VENV.resolve():
        python = _venv_python()
        if not python.is_file():
            print('Creating a local .venv for Pygame (first launch only)...', flush=True)
            try:
                venv.create(VENV, with_pip=True)
            except (OSError, subprocess.CalledProcessError, RuntimeError) as ex:
                raise SystemExit(
                    f'Unable to create .venv: {ex}\n'
                    'Install Python venv support (python3-venv on Ubuntu) and try again.'
                ) from ex
        # Start again with the repo-local interpreter. Only that interpreter
        # installs packages; the global environment stays untouched.
        try:
            os.execv(str(python), [str(python), str(ROOT / 'main.py'), *argv])
        except OSError as ex:
            raise SystemExit(
                f'Unable to start {python}: {ex}\n'
                'If .venv belongs to an older Python, rename it and try again.'
            ) from ex

    print('Installing Pygame into .venv (first launch only)...', flush=True)
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', PYGAME_REQUIREMENT], check=True)
    except (OSError, subprocess.CalledProcessError) as ex:
        raise SystemExit(
            f'Pygame installation failed: {ex}\n'
            'Internet access is required once; rerun python main.py when available.\n'
            'You can still run python main.py --headless without Pygame.'
        ) from ex
    importlib.invalidate_caches()


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # Always run the checked-out project, even when launched from elsewhere
    # or when an older ambition_lite is installed in the Python environment.
    sys.path.insert(0, str(ROOT / 'src'))
    if not any(option in argv for option in ('--headless', '--help', '-h')):
        _prepare_graphics(argv)
    from ambition_lite.__main__ import main as game_main
    return game_main(argv)


if __name__ == '__main__':
    raise SystemExit(main())
