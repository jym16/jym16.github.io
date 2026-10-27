#!/usr/bin/env python3
"""Build the published homepage scaling schematic from its retained crop."""
from pathlib import Path
import base64
import hashlib
import json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ASSETS = ROOT / "assets/images/research"
SOURCES = HERE / "home-scaling-source.json"
MASK = (0, 190, 75, 75)


def main():
    source = json.loads(SOURCES.read_text())
    width, height = source["width"], source["height"]
    x, y, mask_width, mask_height = MASK
    raster = (HERE / source["input_file"]).read_bytes()
    if hashlib.sha256(raster).hexdigest() != source["input_sha256"]:
        raise ValueError("The retained published schematic differs from its provenance.")
    encoded = base64.b64encode(raster).decode("ascii")
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">\n'
        '<title>Paper schematic with panel marker removed</title>\n'
        '<desc>Original diagram and scientific labels preserved.</desc>\n'
        f'<image width="{width}" height="{height}" '
        f'href="data:image/webp;base64,{encoded}"/>\n'
        f'<rect x="{x}" y="{y}" width="{mask_width}" '
        f'height="{mask_height}" fill="white"/>\n</svg>\n'
    )
    target = ASSETS / "home-scaling-schematic.svg"
    target.write_text(svg)
    source["display_asset"] = target.name
    source["panel_label_mask_px"] = list(MASK)
    source["display_bytes"] = target.stat().st_size
    source["display_sha256"] = hashlib.sha256(target.read_bytes()).hexdigest()
    SOURCES.write_text(json.dumps(source, indent=2) + "\n")
    print("Updated the published homepage scaling schematic without altering its diagram pixels.")


if __name__ == "__main__":
    main()
