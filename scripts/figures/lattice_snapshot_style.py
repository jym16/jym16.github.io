"""Common rendering of retained states on the Pete et al. physical layout."""
from __future__ import annotations

import csv
from pathlib import Path

from modsync_style import manuscript_style, save_plot
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.lines import Line2D
import numpy as np

DATA = Path(__file__).resolve().parent / "data"
ROOT = Path(__file__).resolve().parents[2]


def read_geometry():
    with (DATA / "pete-lattice-vertices.csv").open(newline="") as stream:
        vertices = list(csv.DictReader(stream))
    with (DATA / "pete-lattice-edges.csv").open(newline="") as stream:
        edges = list(csv.DictReader(stream))
    coordinates = np.array([[float(v["x"]), float(v["y"])] for v in vertices])
    source = np.array([int(e["i"]) - 1 for e in edges])
    target = np.array([int(e["j"]) - 1 for e in edges])
    internal = np.array([e["kind"] == "internal" for e in edges])
    return coordinates, source, target, internal


def draw_layout(ax, coordinates, source, target, internal, *, values=None,
                cmap=None, norm=None, node_size=12):
    """Draw retained bonds only; strong path bonds identify physical nodes."""
    segments = np.stack([coordinates[source], coordinates[target]], axis=1)
    ax.add_collection(LineCollection(segments[~internal], colors="#a0a6ab",
                      linewidths=.65, linestyles=(0, (1.5, 1.5)), zorder=1))
    ax.add_collection(LineCollection(segments[internal], colors="#68717a",
                      linewidths=2.7, capstyle="round", zorder=2))
    if values is None:
        edge_colors = "#e4e8eb"
        node_colors = "white"
    else:
        edge_values = (values[source] + values[target]) / 2
        edge_colors = cmap(norm(edge_values[internal]))
        node_colors = cmap(norm(values))
    ax.add_collection(LineCollection(segments[internal], colors=edge_colors,
                      linewidths=2.0, capstyle="round", zorder=3))
    ax.scatter(coordinates[:, 0], coordinates[:, 1], c=node_colors,
               s=node_size, edgecolors="#68717a", linewidths=.25, zorder=4)
    ax.set(xlim=(-.8, 19.8), ylim=(-.8, 19.8), aspect="equal")
    ax.set_axis_off()


def layout_legend(fig, y):
    fig.legend(handles=[Line2D([], [], color="#68717a", linewidth=2.7, label="Within node"),
                        Line2D([], [], color="#a0a6ab", linewidth=.65,
                               linestyle=(0, (1.5, 1.5)), label="Contact")],
               loc="center", bbox_to_anchor=(.5, y), ncol=2, fontsize=9,
               handlelength=1.6, columnspacing=1.2)


@manuscript_style
def render_snapshots(coordinates, source, target, internal, states, times, *,
                     cmap, norm, ticks, quantity, output, title, preview=None):
    assert len(times) == len(states) == 3
    assert states.shape[1] == len(coordinates) == 400
    fig = plt.figure(figsize=(3.5, 9))
    segments = np.stack([coordinates[source], coordinates[target]], axis=1)
    for bottom, time, values in zip((.688, .388, .088), times, states):
        ax = fig.add_axes([.13, bottom, .74, .268])
        # Strong path bonds reveal the extended physical nodes. Thin contacts
        # join distinct physical nodes. No absent substrate bonds are drawn.
        ax.add_collection(LineCollection(segments[~internal], colors="#6c7379",
                          linewidths=.65, linestyles=(0, (1.5, 1.5)), zorder=1))
        ax.add_collection(LineCollection(segments[internal], colors="#555c62",
                          linewidths=2.6, capstyle="round", zorder=2))
        edge_values = (values[source] + values[target]) / 2
        ax.add_collection(LineCollection(segments[internal], colors=cmap(norm(edge_values[internal])),
                          linewidths=1.9, capstyle="round", zorder=3))
        points = ax.scatter(coordinates[:, 0], coordinates[:, 1], c=values,
                            cmap=cmap, norm=norm, s=9.5, edgecolors="#454b50",
                            linewidths=.3, zorder=4)
        ax.set(xlim=(-.8, 19.8), ylim=(-.8, 19.8), aspect="equal")
        ax.set_axis_off()
        ax.set_title(rf"$t = {time:g}$", fontsize=16, pad=5)
    fig.legend(handles=[Line2D([], [], color="#555c62", linewidth=2.6, label="Within node"),
                        Line2D([], [], color="#6c7379", linewidth=.65,
                               linestyle=(0, (1.5, 1.5)), label="Contact")],
               loc="center", bbox_to_anchor=(.5, .084), ncol=2, fontsize=8.5,
               handlelength=1.6, columnspacing=1.2)
    color_ax = fig.add_axes([.18, .055, .64, .014])
    colorbar = fig.colorbar(points, cax=color_ax, orientation="horizontal", ticks=ticks)
    colorbar.ax.tick_params(length=3, width=.8, labelsize=11, pad=2)
    colorbar.set_label(quantity, fontsize=13, labelpad=3)
    colorbar.outline.set_linewidth(.8)
    save_plot(fig, output, 350, 900, preview, title)
    plt.close(fig)
