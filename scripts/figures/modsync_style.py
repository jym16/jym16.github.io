"""Website-sized adaptation of the modsync manuscript's plotting style.

Source: letter_v6/companion-code/figures/style.py and the VDP-primary renderer.
Paper typography/line/tick proportions are enlarged uniformly by 2 for the web.
All data plots use the same 100-dpi export geometry and outlined SVG fonts.
"""
from __future__ import annotations

from functools import wraps
from pathlib import Path
import os
import re
import tempfile

os.environ.setdefault("MPL_IGNORE_SYSTEM_FONTS", "1")
os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "homepage-modsync-mpl"))

import matplotlib as mpl
from matplotlib import font_manager

HIROSHIGE = (
    "#e76254", "#ef8a47", "#f7aa58", "#ffd06f", "#ffe6b7",
    "#aadce0", "#72bcd5", "#528fad", "#376795", "#1e466e",
)
BLUE = HIROSHIGE[8]
ORANGE = HIROSHIGE[1]
PHASE_COLORS = ("#eeeeee", HIROSHIGE[4], HIROSHIGE[6], HIROSHIGE[8], HIROSHIGE[5], "#b6a5cf")
_FONT_FAMILY = None


def manuscript_rc():
    global _FONT_FAMILY
    if _FONT_FAMILY is None:
        folder = Path("/System/Library/Fonts/Supplemental")
        for suffix in ("", " Bold", " Italic", " Bold Italic"):
            font = folder / f"Times New Roman{suffix}.ttf"
            if font.exists():
                font_manager.fontManager.addfont(str(font))
        try:
            font_manager.findfont("Times New Roman", directory="/", fallback_to_default=False)
            _FONT_FAMILY = ["Times New Roman", "STIXGeneral"]
        except ValueError:
            _FONT_FAMILY = ["STIXGeneral"]
    return {
        "font.family": _FONT_FAMILY, "font.size": 16,
        "mathtext.fontset": "stix", "text.color": "black",
        "axes.labelsize": 16, "axes.titlesize": 16, "axes.titleweight": "normal",
        "axes.labelcolor": "black", "axes.edgecolor": "black",
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.spines.left": True, "axes.spines.bottom": True,
        "axes.linewidth": 1.2, "axes.grid": False,
        "legend.fontsize": 12, "legend.frameon": False, "legend.labelcolor": "black",
        "xtick.labelsize": 12, "ytick.labelsize": 12,
        "xtick.color": "black", "ytick.color": "black",
        "xtick.direction": "out", "ytick.direction": "out",
        "xtick.major.size": 7, "ytick.major.size": 7,
        "xtick.minor.size": 4, "ytick.minor.size": 4,
        "xtick.major.width": 1.6, "ytick.major.width": 1.6,
        "xtick.minor.width": 1.2, "ytick.minor.width": 1.2,
        "xtick.top": False, "ytick.right": False,
        "lines.linewidth": 2, "lines.markersize": 4,
        "figure.facecolor": "white", "axes.facecolor": "white",
        "savefig.facecolor": "white", "savefig.dpi": 300, "savefig.bbox": None,
        "pdf.fonttype": 42, "ps.fonttype": 42,
        "svg.fonttype": "path", "svg.hashsalt": "jun-yamamoto-modsync-style-v1",
    }


def manuscript_style(function):
    @wraps(function)
    def render(*args, **kwargs):
        # Font discovery has already finished. Allow explicitly registered Times
        # files during lookup; MPL_IGNORE_SYSTEM_FONTS otherwise filters them out.
        ignored = os.environ.pop("MPL_IGNORE_SYSTEM_FONTS", None)
        try:
            with mpl.rc_context(manuscript_rc()):
                return function(*args, **kwargs)
        finally:
            if ignored is not None:
                os.environ["MPL_IGNORE_SYSTEM_FONTS"] = ignored
    return render


def save_plot(fig, path: Path, width: int, height: int,
              preview_path: Path | None = None, title: str | None = None):
    """Keep typography identical across scripts using one physical SVG scale."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.set_size_inches(width / 100, height / 100)
    fig.savefig(path, format="svg", dpi=100, metadata={
        "Date": None, "Creator": "Jun Yamamoto website — modsync manuscript style",
        "Title": title or path.stem,
    })
    svg = path.read_text()
    svg = re.sub(r'width="[0-9.]+pt" height="[0-9.]+pt"',
                 f'width="{width}" height="{height}"', svg, count=1)
    path.write_text(svg)
    if preview_path is not None:
        preview_path = Path(preview_path)
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(preview_path, dpi=100)
