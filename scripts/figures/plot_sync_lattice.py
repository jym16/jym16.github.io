"""Render one retained Kuramoto state with an arrow at each site."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from lattice_snapshot_style import DATA, ROOT, read_geometry, draw_layout, layout_legend
from modsync_style import BLUE, manuscript_style, save_plot
import matplotlib.pyplot as plt
import numpy as np


@manuscript_style
def plot(preview=None):
    with np.load(DATA / "pete-sync-phase.npz", allow_pickle=False) as bundle:
        theta = bundle["theta"]
        retained_coordinates = bundle["coordinates"]
        retained_source, retained_target = bundle["edge_i"] - 1, bundle["edge_j"] - 1
    metadata = json.loads((DATA / "pete-sync-phase-metadata.json").read_text())
    coordinates, source, target, internal = read_geometry()
    assert np.array_equal(coordinates, retained_coordinates)
    assert np.array_equal(source, retained_source) and np.array_equal(target, retained_target)
    order = float(abs(np.mean(np.exp(1j * theta))))
    assert abs(order - metadata["snapshot_selection"]["actual_R"]) < 1e-12
    fig = plt.figure(figsize=(3.5, 3.8))
    ax = fig.add_axes([.055, .10, .89, .82])
    draw_layout(ax, coordinates, source, target, internal, node_size=7)
    # All 400 arrows have equal length. Their directions alone encode phase.
    ax.quiver(coordinates[:, 0], coordinates[:, 1], np.cos(theta), np.sin(theta),
              color=BLUE, angles="xy", scale_units="xy", scale=1.35, pivot="mid",
              width=.0038, headwidth=3.0, headlength=3.5, headaxislength=3.2,
              zorder=5)
    layout_legend(fig, .052)
    save_plot(fig, ROOT / "assets/images/research/synchronization-phase-arrows.svg", 350, 380,
              preview, "Microscopic Kuramoto phases shown by arrows at the retained state")
    plt.close(fig)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", type=Path)
    plot(parser.parse_args().preview)
