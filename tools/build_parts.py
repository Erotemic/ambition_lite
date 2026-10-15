#!/usr/bin/env python3
"""Turn the versioned SVG paper-doll pieces into small PNGs.

Pygame cannot display SVG directly. This script does the only slow conversion;
the game loads the resulting PNGs and moves/rotates individual limbs.

    python tools/build_parts.py

Optional authoring requirements: `pip install cairosvg pillow`. No ambition checkout,
Rust tooling, Qt, music software, or procedural sprite-generator framework needed.
"""
from __future__ import annotations

import argparse
import io
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG_NS = "http://www.w3.org/2000/svg"
INK_NS = "http://www.inkscape.org/namespaces/inkscape"
DRAWABLE = {"path", "polygon", "polyline", "rect", "ellipse", "circle", "line", "image", "use", "text"}
ET.register_namespace("", SVG_NS)
ET.register_namespace("inkscape", INK_NS)


def local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def render_subset(source: Path, view: str, include: list[str], dpi: float):
    """Return cropped PNG image and its offset in the full SVG render.

    An include id can select either a group (its whole subtree) or one shape.
    All its ancestors retain their transforms; everything else is hidden.
    """
    import cairosvg
    from PIL import Image

    root = ET.parse(source).getroot()
    by_id = {e.get("id"): e for e in root.iter() if e.get("id")}
    parent = {child: node for node in root.iter() for child in node}
    keep = set()
    for item in include:
        if item not in by_id:
            raise ValueError(f"Missing SVG element id {item!r} in {source}")
        target = by_id[item]
        keep.update(target.iter())
        while target in parent:
            target = parent[target]
            keep.add(target)
    # Don't hide definitions (gradients, masks) or joint metadata.
    for node in root:
        if local(node.tag) == "defs":
            keep.update(node.iter())
    for node in root:
        label = node.get(f"{{{INK_NS}}}label")
        if label is not None and label != view and not any(x in keep for x in node.iter()):
            node.set("style", (node.get("style", "") + ";display:none"))
    for node in root.iter():
        if node in keep and node.get("data-rig-editor-visibility") == "editor-only":
            remaining = [s for s in node.get("style", "").split(";") if not s.strip().startswith("display:")]
            node.set("style", ";".join(remaining))
        if local(node.tag) in DRAWABLE and node not in keep:
            node.set("style", node.get("style", "") + ";display:none")
    data = cairosvg.svg2png(bytestring=ET.tostring(root, encoding="utf8"), dpi=dpi)
    image = Image.open(io.BytesIO(data)).convert("RGBA")
    bbox = image.getbbox()
    if bbox is None:
        return None, (0, 0)
    return image.crop(bbox), bbox[:2]


def build(name: str):
    from PIL import Image

    rig_path = ROOT / 'assets' / 'rigs' / f'{name}.json'
    rig = json.loads(rig_path.read_text())
    src = rig['svg_source']
    svg = ROOT / 'assets' / 'svg' / src['filename']
    dest = ROOT / 'assets' / 'parts' / name
    dest.mkdir(parents=True, exist_ok=True)
    ref_scale = float(src['scale'])
    dpi = float(src['ref_dpi']) * ref_scale
    seen = 0
    for part in rig['parts']:
        png = dest / (part['name'] + '.png')
        image, offset = render_subset(svg, src['view'], part['include'], dpi)
        if image is None:
            raise ValueError(f'Empty SVG part: {name}/{part["name"]}')
        px, py = part['pivot']
        # Pivot is in part-crop coordinates, not the full SVG canvas.
        part['crop_pivot'] = [round(px * ref_scale - offset[0], 4),
                              round(py * ref_scale - offset[1], 4)]
        image.save(png, optimize=True)
        seen += 1
    rig_path.write_text(json.dumps(rig, indent=2, ensure_ascii=False) + '\n')
    print(f'{name}: wrote {seen} part PNGs')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('rigs', nargs='*', default=['robot', 'trex'])
    args = parser.parse_args()
    for name in args.rigs:
        build(name)


if __name__ == '__main__':
    main()
