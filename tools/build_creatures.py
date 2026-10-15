#!/usr/bin/env python3
"""Rebuild static simplified enemy PNGs from the included Ambition SVGs.

    python tools/build_creatures.py

Requires cairosvg and pillow only while rebuilding, not while playing.
"""
from __future__ import annotations

import io
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
NAMES = ('kiwi', 'chicken', 'chicken_hen', 'emu', 'ostrich', 'ostrich_hen',
         'european_swallow', 'african_swallow', 'compsognathus', 'penguin',
         'shoebill', 'owl', 'vulture', 'cassowary', 'pachycephalosaurus',
         'triceratops', 'dilophosaurus', 'raptor_stalker')


def main():
    from PIL import Image
    import cairosvg
    ET.register_namespace('', 'http://www.w3.org/2000/svg')
    out_dir = ROOT / 'assets/creatures'
    out_dir.mkdir(exist_ok=True)
    for name in NAMES:
        source = ROOT / 'assets/svg/creatures' / (name + '.svg')
        root = ET.parse(source).getroot()
        # Keep only main drawing; exclude authoring markers and multiple views.
        art = next((e for e in root if e.tag.endswith('}g') and e.get('id', '').endswith('-side')), None)
        if art is None:
            art = next((e for e in root if e.tag.endswith('}g') and e.get('id', '') not in ('rig-joints', 'ambition-rig-markers')), None)
        if art is None:
            raise ValueError(f'No character SVG artwork group: {name}')
        for node in list(root):
            if node is not art and not node.tag.endswith('}defs'):
                root.remove(node)
        for node in art.iter():
            part = node.get('data-rig-part', '')
            if part.startswith('eye_') and part != 'eye_open':
                node.set('style', node.get('style', '') + ';display:none')
        # 512mm source dimensions -> 512px with 25.4 DPI; any viewBox size works.
        png = cairosvg.svg2png(bytestring=ET.tostring(root, encoding='utf8'), dpi=25.4)
        image = Image.open(io.BytesIO(png)).convert('RGBA')
        bbox = image.getbbox()
        if bbox is None:
            raise ValueError(f'No visible character art in {name}')
        cropped = image.crop(bbox)
        cropped.thumbnail((210, 210), Image.Resampling.LANCZOS)
        cropped.save(out_dir / (name + '.png'), optimize=True)
        print(name, image.size, '->', cropped.size)


if __name__ == '__main__':
    main()
