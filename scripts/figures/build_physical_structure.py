#!/usr/bin/env python3
"""Arrange the paper's Figure 1(a,b) horizontally without panel markers."""
from pathlib import Path
import base64
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / "assets/images/research"
DATA = Path(__file__).resolve().parent / "data"
WIDTH, HEIGHT = 1160, 514
PANELS = [
    ("physical-structure-panel-a.webp", 960, 785, 20),
    ("physical-structure-panel-b.webp", 960, 842, 600),
]


def main():
    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        '<title>Microscopic and coarse-grained physical networks</title>',
        '<desc>Figure 1(a) on the left and Figure 1(b) on the right, '
        'with original colors and scientific labels preserved.</desc>',
        '<rect width="100%" height="100%" fill="white"/>',
    ]
    sources = []
    scale = 540 / 960
    for filename, width, height, x in PANELS:
        raster = (DATA / filename).read_bytes()
        encoded = base64.b64encode(raster).decode("ascii")
        y = (HEIGHT - height * scale) / 2
        elements.extend([
            f'<g transform="translate({x:g} {y:.8g}) scale({scale:g})">',
            f'<image width="{width}" height="{height}" '
            f'href="data:image/webp;base64,{encoded}"/>',
            '<rect x="0" y="0" width="110" height="160" fill="white"/>',
            '</g>',
        ])
        sources.append({
            "file": "data/" + filename, "width": width, "height": height,
            "sha256": hashlib.sha256(raster).hexdigest(),
            "placement": {"x": x, "y": y, "scale": scale},
            "panel_label_mask_px": [0, 0, 110, 160],
        })
    elements.append('</svg>')
    target = ASSETS / "physical-structure-panels.svg"
    target.write_text('\n'.join(elements) + '\n')
    provenance = {
        "source": "deloc_revised.zip/pre_revised/figures/fig_multiscale_origin.pdf",
        "source_sha256": "362c64d11d11f96e3cb8406690c16fe980a79c7b4bbd2532d73c7aea52d277e8",
        "panels": "Figure 1(a,b), horizontally arranged at equal scale",
        "crop_a_pt": [0, 0, 78.27417, 64],
        "crop_b_pt": [0, 65, 78.27417, 133.667],
        "rendering": "Poppler 1440 dpi; Lanczos resize to 960 px width; lossless WebP",
        "inputs": sources,
        "output": target.name, "width": WIDTH, "height": HEIGHT,
        "bytes": target.stat().st_size,
        "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
    }
    Path(__file__).with_name("physical-structure-sources.json").write_text(
        json.dumps(provenance, indent=2) + '\n'
    )
    print(f"Created {target.name}: {WIDTH} x {HEIGHT}.")


if __name__ == "__main__":
    main()
