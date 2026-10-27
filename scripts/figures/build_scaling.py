#!/usr/bin/env python3
"""Build custom website figures from published vector markers and supplied data.

Default usage redraws the two active SVGs from the bundled CSV files and does not
require the original PDF or LocalProj checkout. Optional source import:

    python build_scaling.py --extract-paper /path/PhysRevE.110.064318.pdf \
        --crossover-source /path/crossover/figures/data/figures --data-only

The return probabilities are digitized from circular vector markers in Figure
2(b), page 5 of Yakubo, Shimojo & Yamamoto, PRE 110, 064318 (2024). They are not
raw measurements. Filled red circles are the hub start; open red rings are the
non-hub start. Both are the unshifted deterministic generator G_A curves.

The structural-crossover CSV is independently supplied figure-ready data from
Mizutaka, Yamamoto & Yakubo, arXiv:2610.02883. These are different models and
different observations; the charts never join or identify their data.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import statistics
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from modsync_style import BLUE, ORANGE, HIROSHIGE, manuscript_style, save_plot

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
OUTPUT = ROOT / "assets" / "images" / "research"
NAVY = "#263754"
MUTED = "#647084"
RULE = "#c9d2e2"
# These two charts are displayed at about half their export width. Keep their
# manuscript typography readable in the narrow Research figure column.
SCALING_LABEL_SIZE = 22
SCALING_TICK_SIZE = 18
SCALING_LEGEND_SIZE = 18
SCALING_ANNOTATION_SIZE = 22

# Axis-tick centers measured directly from the published page's vector paths.
# x ticks: t = 1, 10, 100, 1000, 10000. y ticks: p = 10^3 ... 10^-5.
# Coordinates are SVG points in pdftocairo's 607.536 x 810 pt page viewBox;
# the y coordinate increases downward. Least-squares calibration averages the
# small rounding discrepancies already present in the published artwork.
X_TICKS = [347.093750, 397.267578, 447.332031, 497.394531, 547.570312]
Y_POWERS = list(range(3, -6, -1))
Y_TICKS = [
    452.609375, 469.5957035, 486.6933595, 503.6796875, 520.6640625,
    537.6523435, 554.750000, 571.734375, 588.7207035,
]
PUBLISHED_RED = "rgb(93.331909%, 17.64679%, 16.07666%)"
NUMBERS = re.compile(r"[-+]?\d*\.\d+|\d+")
DS_HUB = 2.0 * math.log(2.5) / math.log(5.0)
DS_NONHUB = 2.0


def linear_fit(xs: list[float], ys: list[float]) -> tuple[float, float]:
    """Return intercept and slope without requiring a plotting dependency."""
    xm, ym = statistics.mean(xs), statistics.mean(ys)
    slope = sum((x - xm) * (y - ym) for x, y in zip(xs, ys)) / sum(
        (x - xm) ** 2 for x in xs
    )
    return ym - slope * xm, slope


def extract_return_probability(pdf: Path) -> None:
    """Recover G_A marker centers, calibrate log axes, and save audited CSV."""
    with tempfile.TemporaryDirectory(prefix="homepage-scaling-vector-") as td:
        svg = Path(td) / "page5.svg"
        subprocess.run(
            ["pdftocairo", "-f", "5", "-l", "5", "-svg", str(pdf), str(svg)],
            check=True, capture_output=True,
        )
        root = ET.parse(svg).getroot()
    if root.get("viewBox") != "0 0 607.536 810":
        raise ValueError("Unexpected source page geometry; recalibrate its axes.")
    centers: dict[str, list[tuple[float, float]]] = {"hub": [], "non-hub": []}
    for element in root.iter():
        if not element.tag.endswith("path") or element.get("fill") != PUBLISHED_RED:
            continue
        path = element.get("d", "")
        values = [float(n) for n in NUMBERS.findall(path)]
        if not values:
            continue
        xs, ys = values[::2], values[1::2]
        width, height = max(xs) - min(xs), max(ys) - min(ys)
        x, y = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
        if not (346 < x < 549 and 500 < y < 585 and 1.5 < width < 1.65):
            continue
        if abs(width - height) >= 0.02:
            continue
        if path.count("C") == 4 and path.count("L") == 0:
            centers["hub"].append((x, y))
        elif path.count("C") == 8 and path.count("L") == 3:
            # Open circles are compound paths, with no white raster sampling.
            centers["non-hub"].append((x, y))
    for name, points in centers.items():
        points.sort()
        if len(points) != 197:
            raise ValueError(f"Expected 197 {name} G_A markers; recovered {len(points)}.")
    paired_x_error = max(
        abs(a[0] - b[0]) for a, b in zip(centers["hub"], centers["non-hub"])
    )
    if paired_x_error > 0.01:
        raise ValueError("The two recovered series do not share the plotted time grid.")
    xa, xb = linear_fit(list(range(5)), X_TICKS)
    ya, yb = linear_fit(Y_POWERS, Y_TICKS)
    residual_x = max(abs(x - (xa + xb * p)) for p, x in enumerate(X_TICKS))
    residual_y = max(abs(y - (ya + yb * p)) for p, y in zip(Y_POWERS, Y_TICKS))
    rows = []
    fits = {}
    for name, points in centers.items():
        data = [(10 ** ((x - xa) / xb), 10 ** ((y - ya) / yb)) for x, y in points]
        for (x, y), (time, probability) in zip(points, data):
            rows.append((name, time, probability, x, y))
        fit_data = [(math.log10(t), math.log10(p)) for t, p in data if 100 <= t <= 10000]
        _, slope = linear_fit(*map(list, zip(*fit_data)))
        fits[name] = {"time_range": [100, 10000], "log_log_slope": slope}
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / "scaling-return-probability.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["starting_node", "time", "return_probability", "vector_x_pt", "vector_y_pt"])
        for name, time, probability, x, y in rows:
            writer.writerow([name, f"{time:.12g}", f"{probability:.12g}", f"{x:.9g}", f"{y:.9g}"])
    audit = {
        "source": "Yakubo, Shimojo & Yamamoto, Physical Review E 110, 064318 (2024), Figure 2(b), PDF page 5",
        "doi": "10.1103/PhysRevE.110.064318",
        "source_pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(),
        "data_kind": "Digitized published vector markers, not original raw measurements",
        "model": {"generator": "G_A", "generation": 8, "nodes": 234390, "edges": 390625, "min_degree": 3, "max_degree": 384},
        "starting_nodes": {"hub": "Randomly selected highest-degree node", "non-hub": "Randomly selected lowest-degree node far from hubs"},
        "marker_counts": {name: len(points) for name, points in centers.items()},
        "calibration": {
            "svg_viewBox": "0 0 607.536 810", "x_decade_tick_centers_pt": X_TICKS,
            "y_tick_log10_probabilities": Y_POWERS, "y_decade_tick_centers_pt": Y_TICKS,
            "vector_x_equals_intercept_plus_slope_log10_time": [xa, xb],
            "vector_y_equals_intercept_plus_slope_log10_probability": [ya, yb],
            "maximum_tick_residual_x_pt": residual_x, "maximum_tick_residual_y_pt": residual_y,
            "equivalent_relative_time_tick_discrepancy": 10 ** (residual_x / xb) - 1,
            "equivalent_relative_probability_tick_discrepancy": 10 ** (residual_y / abs(yb)) - 1,
            "maximum_paired_time_coordinate_discrepancy_pt": paired_x_error,
        },
        "theory": {"return_probability_exponent": "-d_s/2", "hub_spectral_dimension": DS_HUB, "non_hub_spectral_dimension": DS_NONHUB},
        "observed_slope_check": fits,
        "limits": "Calibrated values retain the finite precision of the published vector artwork; no error bars or additional measurements are inferred.",
    }
    (DATA / "scaling-return-probability-calibration.json").write_text(json.dumps(audit, indent=2) + "\n")


def import_crossover(source: Path) -> None:
    """Preserve all valid figure-ready triplets, with explicit model columns."""
    rows = []
    source_hashes = {}
    nonpositive = {}
    for filename, gamma, degrees in [("fig2a.csv", 3.75, [50, 60, 70, 80, 90, 100]), ("fig2b.csv", 4.25, [15, 20, 25, 30])]:
        path = source / filename
        source_hashes[filename] = hashlib.sha256(path.read_bytes()).hexdigest()
        nonpositive[filename] = 0
        with path.open(newline="") as stream:
            data = list(csv.reader(stream))
        for index, degree in enumerate(degrees):
            column = index * 3
            for row in data:
                if len(row) <= column + 1 or not row[column].strip() or not row[column + 1].strip():
                    continue
                x, y = float(row[column]), float(row[column + 1])
                if not (x > 0 and y > 0):
                    # Retain source values, including six tiny negative values
                    # in gamma=3.75 far beyond the website chart's domain.
                    # They are not used by the selected gamma=4.25 log plot.
                    nonpositive[filename] += 1
                rows.append((gamma, degree, x, y))
    DATA.mkdir(parents=True, exist_ok=True)
    with (DATA / "scaling-crossover.csv").open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["degree_exponent_gamma", "root_degree_k", "scaled_distance", "rescaled_ball_volume"])
        writer.writerows(rows)
    (DATA / "scaling-crossover-source.json").write_text(json.dumps({
        "source": "Mizutaka, Yamamoto & Yakubo, arXiv:2610.02883, Figure 2 data",
        "source_members": "crossover/figures/data/figures/fig2{a,b}.csv",
        "format": "Supplied figure-ready CSV, repeated x,y,blank triplets; missing coordinates omitted",
        "source_sha256": source_hashes,
        "nonpositive_values_retained_from_source": nonpositive,
        "gamma_3_75_degrees_in_source_column_order": [50, 60, 70, 80, 90, 100],
        "gamma_4_25_degrees_in_source_column_order": [15, 20, 25, 30],
        "x": "l/(k/c)^(1/(D_f-1))", "y": "nu_k(l)/(c*l^(D_f-1)*(l-1))",
        "website_selection": "gamma=4.25, D_f=2; k=15,20,25,30; single chart without paper insets",
        "distinct_model": "These are critical scale-free random networks, not the G_A generator network in the return-probability chart.",
        "rows": len(rows),
    }, indent=2) + "\n")


def load_return() -> dict[str, list[tuple[float, float]]]:
    result: dict[str, list[tuple[float, float]]] = {"hub": [], "non-hub": []}
    with (DATA / "scaling-return-probability.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            result[row["starting_node"]].append((float(row["time"]), float(row["return_probability"])))
    if any(len(points) != 197 for points in result.values()):
        raise ValueError("Expected the two complete digitized G_A series.")
    return result


def setup_plotting():
    os.environ.setdefault("MPL_IGNORE_SYSTEM_FONTS", "1")
    os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "homepage-matplotlib-cache"))
    import matplotlib as mpl
    mpl.use("Agg")
    import matplotlib.pyplot as plt
    mpl.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 13, "text.color": NAVY,
        "axes.labelcolor": NAVY, "axes.edgecolor": RULE, "xtick.color": MUTED,
        "ytick.color": MUTED, "figure.facecolor": "white", "axes.facecolor": "white",
        "svg.fonttype": "path", "svg.hashsalt": "jun-yamamoto-scaling-2026",
        "axes.unicode_minus": True, "mathtext.fontset": "dejavusans",
    })
    return plt


@manuscript_style
def return_chart(plt, qa: Path) -> None:
    from matplotlib.lines import Line2D
    data = load_return()
    fig = plt.figure(figsize=(6.4, 4.8), dpi=100)
    ax = fig.add_axes([0.19, 0.20, 0.76, 0.74])
    ax.tick_params(axis="both", which="major", labelsize=SCALING_TICK_SIZE)
    for key, color, face in [("hub", BLUE, BLUE), ("non-hub", ORANGE, "white")]:
        x, y = zip(*data[key])
        ax.loglog(x, y, color=color, linewidth=2, marker="o", markersize=4,
                  markerfacecolor=face, markeredgecolor=color, markeredgewidth=0.8,
                  zorder=2)
    # Parallel guides show the predicted exponents; their vertical placement is
    # illustrative, anchored above the measured points, and never new data.
    for key, color, exponent, annotation in [
        ("hub", BLUE, -DS_HUB / 2, r"$t^{-d_s^{\mathrm{hub}}/2}$"),
        ("non-hub", ORANGE, -1.0, r"$t^{-d_s^{\mathrm{nonhub}}/2}$"),
    ]:
        anchor = min(data[key], key=lambda point: abs(math.log(point[0] / 500)))
        xs = [250.0, 3000.0]
        ys = [anchor[1] * 1.8 * (x / anchor[0]) ** exponent for x in xs]
        ax.loglog(xs, ys, linestyle=(0, (4, 3)), color=color, linewidth=1.2, zorder=1)
        label_x = 1800
        label_y = anchor[1] * 1.8 * (label_x / anchor[0]) ** exponent
        ax.text(label_x, label_y * 1.4, annotation, color=color,
                fontsize=SCALING_ANNOTATION_SIZE, ha="left")
    ax.set_xlim(0.85, 15000)
    ax.set_ylim(1.5e-5, 0.30)
    ax.set_xticks([1, 10, 100, 1000, 10000], [rf"$10^{{{power}}}$" for power in range(5)])
    ax.set_yticks([1e-1, 1e-2, 1e-3, 1e-4], [r"$10^{-1}$", r"$10^{-2}$", r"$10^{-3}$", r"$10^{-4}$"])
    ax.set_xlabel(r"Time $t$", labelpad=10, fontsize=SCALING_LABEL_SIZE)
    ax.set_ylabel(r"Return probability $p_{ii}(t)$", labelpad=9, fontsize=SCALING_LABEL_SIZE)
    ax.legend(handles=[
        Line2D([], [], color=BLUE, marker="o", markersize=4, label=r"Hub start: $d_s^{\mathrm{hub}}$"),
        Line2D([], [], color=ORANGE, marker="o", markerfacecolor="white", markersize=4, label=r"Distant non-hub: $d_s^{\mathrm{nonhub}}$"),
    ], loc="lower left", bbox_to_anchor=(0.0, 0.01), frameon=False,
        handlelength=1.8, labelspacing=0.5, fontsize=SCALING_LEGEND_SIZE)
    # Generator A from the random-walk paper, Figure 1(a): white roots at
    # left/right, black internal nodes above/below, and five undirected edges.
    generator = ax.inset_axes([0.68, 0.78, 0.27, 0.22])
    positions = {"left": (0, 0), "top": (.5, .45),
                 "right": (1, 0), "bottom": (.5, -.45)}
    edges = [("left", "top"), ("left", "bottom"), ("right", "top"),
             ("right", "bottom"), ("top", "bottom")]
    for start, end in edges:
        x, y = zip(positions[start], positions[end])
        generator.plot(x, y, color="black", linewidth=1.2, zorder=1)
    for name, (x, y) in positions.items():
        generator.scatter(x, y, s=64,
                          facecolor="white" if name in ("left", "right") else "black",
                          edgecolor="black", linewidth=1.2, zorder=2)
    generator.set(xlim=(-.15, 1.15), ylim=(-.6, .6), aspect="equal")
    generator.set_axis_off()
    save_plot(fig, OUTPUT / "scaling-return-probability.svg", 640, 480,
              preview_path=qa / "scaling-return-probability.png",
              title="Return probabilities from hub and distant non-hub starting nodes")
    plt.close(fig)


@manuscript_style
def crossover_chart(plt, qa: Path) -> None:
    from matplotlib.ticker import LogLocator, NullFormatter
    groups: dict[int, list[tuple[float, float]]] = {15: [], 20: [], 25: [], 30: []}
    with (DATA / "scaling-crossover.csv").open(newline="") as stream:
        for row in csv.DictReader(stream):
            if float(row["degree_exponent_gamma"]) == 4.25:
                groups[int(row["root_degree_k"])].append((float(row["scaled_distance"]), float(row["rescaled_ball_volume"])))
    fig = plt.figure(figsize=(6.4, 4.0), dpi=100)
    ax = fig.add_axes([0.19, 0.22, 0.76, 0.65])
    ax.tick_params(axis="both", which="major", labelsize=SCALING_TICK_SIZE)
    ax.set_title(r"$\gamma=4.25,\quad D_f=2$", loc="left", fontsize=20, pad=9)
    colors = [BLUE, ORANGE, HIROSHIGE[6], HIROSHIGE[3]]
    for (degree, points), color, marker in zip(groups.items(), colors, ["s", "o", "^", "D"]):
        x, y = zip(*points)
        ax.loglog(x, y, linestyle="none", marker=marker, markersize=4,
                  markerfacecolor="white", markeredgecolor=color, markeredgewidth=0.9,
                  label=rf"$k={degree}$", zorder=3)
    # These are the theoretical asymptotes and amplitude used by the source
    # Figure 2(b) script, not fits or newly sampled observations.
    ax.loglog([0.28, 1.11], [1.87 / 0.28, 1.87 / 1.11], color="black", linewidth=1.2, linestyle=(0, (4, 3)), zorder=1)
    ax.loglog([2, 28], [1, 1], color="black", linewidth=1.2, linestyle=(0, (4, 3)), zorder=1)
    ax.text(0.32, 8.1, "Local regime", fontsize=18, color="black")
    ax.text(3.2, 2.2, "Fractal regime", fontsize=18, color="black")
    ax.set_xlim(0.25, 32)
    ax.set_ylim(0.45, 12)
    ax.set_xticks([0.25, 1, 4, 16], [r"$2^{-2}$", r"$2^{0}$", r"$2^{2}$", r"$2^{4}$"])
    ax.set_yticks([0.5, 1, 2, 4, 8], [rf"$2^{{{power}}}$" for power in range(-1, 4)])
    ax.xaxis.set_minor_locator(LogLocator(base=2, subs=(math.sqrt(2),)))
    ax.yaxis.set_minor_locator(LogLocator(base=2, subs=(math.sqrt(2),)))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_formatter(NullFormatter())
    ax.set_xlabel(r"Scaled distance $l/l_{\mathrm{co}}(k)$", labelpad=9, fontsize=SCALING_LABEL_SIZE)
    ax.set_ylabel("Rescaled neighborhood size", labelpad=9, fontsize=20)
    ax.legend(loc="upper right", frameon=False, ncol=2, columnspacing=0.8,
              handletextpad=0.4, fontsize=SCALING_LEGEND_SIZE)
    save_plot(fig, OUTPUT / "scaling-crossover.svg", 640, 400,
              preview_path=qa / "scaling-crossover.png",
              title="Structural crossover in critical random networks")
    plt.close(fig)


def published_crop(pdf: Path) -> None:
    """Optional original-paper thumbnail, solely for Selected published work."""
    # Original Fig. 2(b), including its axes, labels, and source panel letter.
    # Crop in top-left PDF coordinates (311,435)..(555,622) pt at 4 px/pt.
    subprocess.run([
        "pdftoppm", "-f", "5", "-l", "5", "-r", "288", "-x", "1244",
        "-y", "1740", "-W", "976", "-H", "748", "-singlefile", "-png",
        str(pdf), str(OUTPUT / "random-walks-return-probability"),
    ], check=True, capture_output=True)
    # The shared panel boundary leaves part of panel (a)'s last y-tick label
    # in the upper-left margin. It is outside panel (b)'s axes and is removed
    # without changing any panel-(b) marks, ticks, labels, or numerical data.
    from PIL import Image, ImageDraw
    image = Image.open(OUTPUT / "random-walks-return-probability.png").convert("RGB")
    ImageDraw.Draw(image).rectangle((0, 0, 142, 26), fill="white")
    image.save(OUTPUT / "random-walks-return-probability.png", optimize=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract-paper", type=Path, help="Optional original PRE PDF; requires pdftocairo")
    parser.add_argument("--crossover-source", type=Path, help="Optional directory containing fig2a.csv and fig2b.csv")
    parser.add_argument("--published-crop", type=Path, help="Optional original PRE PDF; save Fig. 2(b) thumbnail")
    parser.add_argument("--data-only", action="store_true", help="Import supplied sources without plotting")
    parser.add_argument("--plots-only", action="store_true", help="Compatibility option; the default already redraws only the two current plots")
    parser.add_argument("--qa-dir", type=Path, default=Path(tempfile.gettempdir()) / "homepage-scaling-qa")
    args = parser.parse_args()
    if args.extract_paper:
        extract_return_probability(args.extract_paper)
    if args.crossover_source:
        import_crossover(args.crossover_source)
    if args.data_only:
        return
    plt = setup_plotting()
    return_chart(plt, args.qa_dir)
    crossover_chart(plt, args.qa_dir)
    if args.published_crop:
        published_crop(args.published_crop)
    outputs = ["scaling-return-probability.svg", "scaling-crossover.svg"]
    print(json.dumps({"outputs": outputs, "qa_directory": str(args.qa_dir)}))


if __name__ == "__main__":
    main()
