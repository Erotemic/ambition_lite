"""One tiny boundary around the imported (and deliberately editable) map JSON."""
from __future__ import annotations

from dataclasses import dataclass
from importlib.resources import files
import json

ROOMS = (
    'primeval_trailhead', 'primeval_run', 'primeval_rookery',
    'primeval_ridge', 'primeval_canopy', 'primeval_tyrant_hall',
)
ROOM_TITLES = (
    '01  TRAILHEAD', '02  THE RUN', '03  ROOKERY',
    '04  RIDGE ROAD', '05  CANOPY', '06  THE TYRANT KING',
)


@dataclass(frozen=True)
class Level:
    name: str
    width: int
    height: int
    spawn: tuple[int, int]
    solids: tuple[tuple[int, int, int, int], ...]
    platforms: tuple[tuple[int, int, int, int], ...]
    doors: tuple[dict, ...]
    enemies: tuple[dict, ...]
    items: tuple[dict, ...]
    props: tuple[dict, ...]
    boss: dict | None


def asset_root():
    """Repo-local assets also work when launched from another directory."""
    from pathlib import Path
    return Path(__file__).resolve().parents[2] / 'assets'


def load_level(name: str) -> Level:
    if name not in ROOMS:
        raise ValueError(f'Unknown room {name!r}')
    data = json.loads((asset_root() / 'levels' / (name + '.json')).read_text())
    return Level(
        name=name, width=data['width'], height=data['height'],
        spawn=tuple(data['spawn']),
        solids=tuple(map(tuple, data['solid'])),
        platforms=tuple(map(tuple, data['platforms'])),
        doors=tuple(data['doors']), enemies=tuple(data['enemies']),
        items=tuple(data['items']), props=tuple(data['props']), boss=data['boss'],
    )
