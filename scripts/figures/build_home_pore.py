#!/usr/bin/env python3
"""Package the supplied empirical pore reconstruction for the homepage.

Default rebuilding uses the retained original PNG only. An explicit
``--source-archive`` imports the single named image from the supplied slide
archive. No research checkout or source archive is written.

The self-contained SVG embeds a lossless WebP at its original resolution.
Only the SVG viewport changes: transparent margins are reduced to 20 pixels.
Visible RGB values and every alpha value are checked after WebP decoding.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
from io import BytesIO
import json
from pathlib import Path
from zipfile import ZipFile

from PIL import Image, __version__ as pillow_version

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
SOURCE_NAME = "home-pore-source.png"
PROVENANCE_NAME = "home-pore-provenance.json"
MEMBER = "slides-defence/figures/introduction/pore_reconstruction.png"
SOURCE_SHA256 = "1e247659a969edb64335b790453aa797ea811ffe790344d78d79e939b1e1126c"
PADDING = 20
DISPLAY_WIDTH = 960


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def build(data_dir: Path, output: Path, preview: Path | None,
          source_archive: Path | None) -> dict:
    source_file = data_dir / SOURCE_NAME
    if source_archive is not None:
        with ZipFile(source_archive) as archive:
            original = archive.read(MEMBER)
        if digest(original) != SOURCE_SHA256:
            raise ValueError("Archive image does not match the documented original PNG.")
        data_dir.mkdir(parents=True, exist_ok=True)
        source_file.write_bytes(original)
    elif not source_file.is_file():
        raise FileNotFoundError("Retained PNG is missing; import it with --source-archive.")

    original = source_file.read_bytes()
    if digest(original) != SOURCE_SHA256:
        raise ValueError("Retained PNG does not match its original source checksum.")
    source = Image.open(BytesIO(original))
    if source.mode != "RGBA" or source.size != (2048, 2048):
        raise ValueError("Expected the original 2048 by 2048 RGBA reconstruction.")
    source.load()
    alpha = source.getchannel("A")
    bounds = alpha.getbbox()
    if bounds is None:
        raise ValueError("The source reconstruction is entirely transparent.")
    left, top, right, bottom = bounds
    crop = (max(0, left - PADDING), max(0, top - PADDING),
            min(source.width, right + PADDING), min(source.height, bottom + PADDING))
    crop_width, crop_height = crop[2] - crop[0], crop[3] - crop[1]
    display_height = round(DISPLAY_WIDTH * crop_height / crop_width)

    encoded = BytesIO()
    source.save(encoded, format="WEBP", lossless=True, quality=100, method=6, exact=True)
    webp = encoded.getvalue()
    decoded = Image.open(BytesIO(webp)).convert("RGBA")
    decoded.load()
    source_bytes, decoded_bytes = source.tobytes(), decoded.tobytes()
    alpha_identical = decoded.getchannel("A").tobytes() == alpha.tobytes()
    visible_pixels = 0
    differing_visible_pixels = 0
    for offset in range(0, len(source_bytes), 4):
        if source_bytes[offset + 3]:
            visible_pixels += 1
            differing_visible_pixels += (
                source_bytes[offset:offset + 4] != decoded_bytes[offset:offset + 4])
    if not alpha_identical or differing_visible_pixels:
        raise RuntimeError("Lossless WebP changed a visible source pixel or an alpha value.")

    payload = base64.b64encode(webp).decode("ascii")
    svg = (
        '<svg xmlns="http://www.w3.org/2000/svg" '
        'xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{DISPLAY_WIDTH}" height="{display_height}" '
        f'viewBox="{crop[0]} {crop[1]} {crop_width} {crop_height}">\n'
        '<title>Sandstone pore-space reconstruction</title>\n'
        '<desc>Empirical sandstone pore-space reconstruction from the supplied '
        'defence slides. The slides credit Lucas-Oliveira et al. (2022), '
        'doi:10.1016/j.dib.2022.107893. Original visible colors and transparency '
        'are preserved; only transparent viewport margins are reduced. '
        'The exact sandstone sample is not identified in the supplied provenance.</desc>\n'
        '<image x="0" y="0" width="2048" height="2048" '
        f'xlink:href="data:image/webp;base64,{payload}"/>\n'
        '</svg>\n'
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg)
    provenance = {
        "artifact": "Empirical sandstone pore-space reconstruction for the homepage",
        "source": {
            "archive": "slides-defence.zip",
            "member": MEMBER,
            "retained_file": SOURCE_NAME,
            "png_sha256": digest(original),
            "png_bytes": len(original),
            "mode": source.mode,
            "dimensions_px": list(source.size),
            "slide_provenance": "Image object 22 and associated soft mask, page 2 of the supplied introduction reference PDF; extracted as PNG without altering decoded RGBA values.",
            "credit": "Lucas-Oliveira et al., Micro-computed tomography of sandstone rocks: Raw, filtered and segmented datasets, Data in Brief 41, 107893 (2022)",
            "doi": "10.1016/j.dib.2022.107893",
            "credit_basis": "The supplied slides identify Sandstone pores / X-ray micro-CT and credit Lucas-Oliveira et al. (2022). The exact sample and original published figure panel are not identified.",
        },
        "processing": {
            "alpha_bounding_box_ltrb_px": list(bounds),
            "transparent_padding_px": PADDING,
            "png_clip_coordinates_ltrb_px": list(crop),
            "svg_viewBox_xywh": [crop[0], crop[1], crop_width, crop_height],
            "source_pixels_resized": False,
            "encoding": "Lossless WebP, quality 100, method 6, exact transparent RGB preservation",
            "webp_sha256": digest(webp),
            "webp_bytes": len(webp),
            "webp_decoded_dimensions_px": list(decoded.size),
            "source_rgba_sha256": digest(source_bytes),
            "decoded_rgba_sha256": digest(decoded_bytes),
            "alpha_identical": alpha_identical,
            "visible_pixels_checked": visible_pixels,
            "differing_visible_rgba_pixels": differing_visible_pixels,
            "all_rgba_bytes_identical": source_bytes == decoded_bytes,
            "transform": "Original-resolution WebP embedded once in SVG; viewport trims transparent whitespace only. No retouching, recoloring, object crop, resampling, or generated content.",
        },
        "output": {
            "file": output.name,
            "dimensions_px": [DISPLAY_WIDTH, display_height],
            "exact_aspect_height_at_width_960": DISPLAY_WIDTH * crop_height / crop_width,
            "bytes": output.stat().st_size,
            "sha256": digest(output.read_bytes()),
            "self_contained": True,
        },
        "software": {"Pillow": pillow_version},
        "rebuild": "Default reads the retained PNG; --source-archive explicitly imports only the original named image.",
    }
    (data_dir / PROVENANCE_NAME).write_text(json.dumps(provenance, indent=2) + "\n")
    if preview is not None:
        preview.parent.mkdir(parents=True, exist_ok=True)
        view = source.crop(crop).resize((DISPLAY_WIDTH, display_height), Image.Resampling.LANCZOS)
        white = Image.new("RGBA", view.size, "white")
        white.alpha_composite(view)
        white.convert("RGB").save(preview)
    return provenance


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-archive", type=Path, help="Explicit read-only slide archive import")
    parser.add_argument("--data-dir", type=Path, default=DATA)
    parser.add_argument("--output", type=Path, default=ROOT / "assets/images/research/home-physical-pore.svg")
    parser.add_argument("--preview", type=Path, default=Path("/private/tmp/homepage-home-pore/home-physical-pore.png"))
    args = parser.parse_args()
    result = build(args.data_dir, args.output, args.preview, args.source_archive)
    print(json.dumps({"output": result["output"],
                      "crop_box": result["processing"]["png_clip_coordinates_ltrb_px"],
                      "visible_rgba_differences": result["processing"]["differing_visible_rgba_pixels"],
                      "alpha_identical": result["processing"]["alpha_identical"],
                      "preview": str(args.preview)}, indent=2))


if __name__ == "__main__":
    main()
