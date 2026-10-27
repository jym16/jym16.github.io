"""Render one retained diffusion eigenmode; no dynamics integration."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from lattice_snapshot_style import DATA, ROOT, read_geometry, draw_layout, layout_legend
from modsync_style import BLUE, ORANGE, manuscript_style, save_plot
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.pyplot as plt
import numpy as np

@manuscript_style
def plot(preview=None):
    with (DATA / "pete-lattice-eigenmode.csv").open(newline="") as stream:
        rows = list(csv.DictReader(stream))
    metadata = json.loads((DATA / "pete-lattice-eigenmode-metadata.json").read_text())
    amplitude = np.array([float(row["amplitude"]) for row in rows])
    coordinates, source, target, internal = read_geometry()
    assert np.array_equal(coordinates, [[float(r["x"]), float(r["y"])] for r in rows])
    assert abs(np.sum(amplitude ** 2) - 1) < 1e-12
    assert abs(np.sum(amplitude ** 4) - metadata["IPR"]) < 1e-12
    assert amplitude[np.argmax(abs(amplitude))] > 0
    cmap = LinearSegmentedColormap.from_list("modsync_signed_eigenmode", [BLUE, "white", ORANGE])
    bound = 0.25
    norm = Normalize(-bound, bound)
    fig = plt.figure(figsize=(3.5, 4))
    ax = fig.add_axes([.055, .185, .89, .735])
    draw_layout(ax, coordinates, source, target, internal, values=amplitude, cmap=cmap, norm=norm)
    layout_legend(fig, .153)
    color_ax = fig.add_axes([.18, .107, .64, .025])
    scalar = plt.cm.ScalarMappable(norm=norm, cmap=cmap)
    colorbar = fig.colorbar(scalar, cax=color_ax, orientation="horizontal", ticks=[-bound, 0, bound])
    colorbar.set_ticklabels([f"{-bound:.2f}", "0", f"{bound:.2f}"])
    colorbar.ax.tick_params(length=3, width=.8, labelsize=11, pad=2)
    colorbar.set_label(r"Eigenmode $u_i$", fontsize=13, labelpad=3)
    colorbar.outline.set_linewidth(.8)
    save_plot(fig, ROOT / "assets/images/research/diffusion-localized-mode.svg", 350, 400,
              preview, "Raw signed microscopic diffusion eigenmode amplitudes, with effective participation approximately fifty lattice sites")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path)
    plot(parser.parse_args().preview)
