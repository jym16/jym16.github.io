#!/usr/bin/env python3
"""Build only the authorized FHN notebook voltage panel for the homepage.

Default rebuilding reads the bundled minimal CSV and provenance, without any
access to LocalProj. An explicit initial import reads saved results only::

    python build_home_fhn.py --source-dir /path/to/letter_v6/companion-code

The source is execution In[6], cell index12, axes[0,0] of plot_dashboard. No
simulation or notebook is executed. Only eight displayed module-mean voltage
curves are retained; other states, coordinates, diagnostics, and parameters are
not copied. The first CSV row is the exact original polyline's clipped boundary
value, followed by unmodified means at the saved times inside the plot window.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

from modsync_style import HIROSHIGE, manuscript_style, save_plot

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DATA = HERE / "data"
CSV_NAME = "home-fhn-voltage.csv"
PROVENANCE_NAME = "home-fhn-voltage-provenance.json"
TAIL_PERIODS = 5


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def import_saved_panel(source_dir: Path, data_dir: Path) -> dict:
    """Read original saved data; write only this panel's minimal local inputs."""
    source_dir = source_dir.resolve()
    notebook = source_dir / "notebooks/fhn_fig01_explorer.ipynb"
    helper = source_dir / "notebooks/fhn_explorer.py"
    states_file = source_dir / "results/fhn_fig01_explorer/fhn_fig01_run.npz"
    modules_file = source_dir / "data/vdp_primary/schematic/panel_a_modules.csv"
    cells = json.loads(notebook.read_text())["cells"]
    cell = cells[12]
    if cell.get("execution_count") != 6 or "plot_dashboard" not in "".join(cell["source"]):
        raise ValueError("Source notebook no longer identifies the expected execution In[6] dashboard.")
    with modules_file.open(newline="") as stream:
        modules = sorted((row for row in csv.DictReader(stream) if row["view"] == "main"),
                         key=lambda row: int(row["module_id"]))
    colors = [HIROSHIGE[int(row["color_index"])] for row in modules]
    with np.load(states_file, allow_pickle=False) as bundle:
        time = bundle["time"]
        states = bundle["states"]
        membership = bundle["module_of"]
        metadata = json.loads(str(bundle["metadata_json"]))
        if not np.array_equal(np.unique(membership), np.arange(8)) or len(modules) != 8:
            raise ValueError("Expected eight source module-mean curves.")
        if not np.array_equal(np.bincount(membership), bundle["sizes"]):
            raise ValueError("Retained membership disagrees with source module sizes.")
        if not np.all(np.diff(time) > 0) or states.shape[:2] != (len(time), len(membership)):
            raise ValueError("Saved source time/state arrays are inconsistent.")
        # Match diagnostics()'s exact arithmetic and array-axis order; retain
        # only coordinate0 (v), never the other physical coordinate or metrics.
        means = np.stack([states[:, membership == c].mean(axis=1)
                          for c in range(8)], axis=1)[:, :, 0]
        start = max(0.0, float(time[-1] - TAIL_PERIODS * metadata["cycle_period"]))
        end = float(time[-1])
        inside = (time >= start) & (time <= end)
        retained_time = time[inside].copy()
        retained_means = means[inside].copy()
        boundary = None
        if retained_time[0] > start:
            right = int(np.searchsorted(time, start))
            left = right - 1
            fraction = float((start - time[left]) / (time[right] - time[left]))
            clipped_values = means[left] + fraction * (means[right] - means[left])
            retained_time = np.r_[start, retained_time]
            retained_means = np.vstack([clipped_values, retained_means])
            boundary = {"time": start,
                        "kind": "Clipped endpoint of the original plotted piecewise-linear curves; not a new simulation sample",
                        "adjacent_source_times": [float(time[left]), float(time[right])],
                        "interpolation_fraction": fraction}
    data_dir.mkdir(parents=True, exist_ok=True)
    csv_file = data_dir / CSV_NAME
    with csv_file.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["time"] + [f"module_{c+1}_mean_v" for c in range(8)])
        for t, values in zip(retained_time, retained_means):
            writer.writerow([f"{t:.17g}"] + [f"{value:.17g}" for value in values])
    provenance = {
        "artifact": "Only the authorized top-left voltage panel from the saved FHN notebook dashboard, reformatted for the website",
        "source_root_at_import": str(source_dir),
        "source_panel": {"notebook": "notebooks/fhn_fig01_explorer.ipynb", "cell_index_zero_based": 12,
                         "execution_count": 6, "function": "notebooks/fhn_explorer.py::plot_dashboard", "axes": "[0,0]"},
        "quantity": "Arithmetic mean of saved state coordinate v (coordinate index0) within each of the eight modules, in source module order",
        "source_data": "results/fhn_fig01_explorer/fhn_fig01_run.npz",
        "source_sha256": {str(path.relative_to(source_dir)): sha256(path)
                          for path in (notebook, helper, states_file, modules_file)},
        "window": {"definition": "Final five isolated-reference-cycle periods, exactly as the source panel",
                   "tail_periods": TAIL_PERIODS, "isolated_reference_period": metadata["cycle_period"],
                   "xlim": [start, end], "first_original_sample_in_window": float(time[inside][0]),
                   "unmodified_original_sample_rows": int(inside.sum()), "clipped_boundary_row": boundary},
        "colors": {"palette": "Source Hiroshige palette and module_colors() indices", "curve_hex": colors},
        "retained_data": {"file": CSV_NAME, "sha256": sha256(csv_file), "rows": len(retained_time),
                          "columns": 9, "includes": "time and eight module-mean voltage columns only"},
        "transforms": "Arithmetic module means and optional exact viewport clipping only; no smoothing, rescaling, normalization, downsampling, or recomputed simulation",
        "validation": {"source_sample_maximum_difference": 0.0,
                       "voltage_range_in_visible_curves": [float(retained_means.min()), float(retained_means.max())],
                       "source_aggregation_order": "Identical to diagnostics(): states[:,module_mask].mean(axis=1), then coordinate0"},
        "rebuild": "Default invocation uses only this minimal CSV and provenance; the original project is read only when --source-dir is explicitly supplied",
    }
    (data_dir / PROVENANCE_NAME).write_text(json.dumps(provenance, indent=2) + "\n")
    # CSV formatting must preserve every original computed mean exactly.
    loaded = np.loadtxt(csv_file, delimiter=",", skiprows=1)
    if not np.array_equal(loaded[:, 0], retained_time) or not np.array_equal(loaded[:, 1:], retained_means):
        raise RuntimeError("CSV round trip altered source values.")
    return provenance


@manuscript_style
def draw(data_dir: Path, output: Path, preview: Path | None) -> None:
    provenance = json.loads((data_dir / PROVENANCE_NAME).read_text())
    csv_file = data_dir / CSV_NAME
    if sha256(csv_file) != provenance["retained_data"]["sha256"]:
        raise ValueError("Bundled voltage CSV does not match its provenance checksum.")
    values = np.loadtxt(csv_file, delimiter=",", skiprows=1)
    start, end = provenance["window"]["xlim"]
    if values.shape != (provenance["retained_data"]["rows"], 9) or not np.isfinite(values).all():
        raise ValueError("Expected time and eight finite module-voltage curves.")
    if values[0, 0] != start or values[-1, 0] != end or not np.all(np.diff(values[:, 0]) > 0):
        raise ValueError("The bundled curve endpoints no longer match the exact source window.")
    colors = provenance["colors"]["curve_hex"]
    fig = plt.figure(figsize=(6.4, 4.0), dpi=100)
    ax = fig.add_axes([0.16, 0.22, 0.79, 0.73])
    for column, color in enumerate(colors, start=1):
        ax.plot(values[:, 0], values[:, column], color=color, linewidth=1.5)
    ax.set_xlim(start, end)
    ax.set_xlabel(r"Time $t$", fontsize=22, labelpad=7)
    ax.set_ylabel(r"Mean voltage $v$", fontsize=22, labelpad=7)
    ax.set_xticks([600, 700, 800])
    ax.set_yticks([-2, 0, 2])
    ax.tick_params(axis="both", which="major", labelsize=18, pad=5)
    save_plot(fig, output, 640, 400, preview_path=preview,
              title="FitzHugh–Nagumo voltage dynamics")
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, help="Explicit read-only companion-code source root for importing the saved authorized panel")
    parser.add_argument("--data-dir", type=Path, default=DATA)
    parser.add_argument("--output", type=Path, default=ROOT / "assets/images/research/home-fhn-voltage.svg")
    parser.add_argument("--preview", type=Path, default=Path("/private/tmp/homepage-home-fhn/home-fhn-voltage.png"))
    args = parser.parse_args()
    if args.source_dir:
        import_saved_panel(args.source_dir, args.data_dir)
    draw(args.data_dir, args.output, args.preview)
    print(f"Wrote {args.output} (640 x400); preview {args.preview}")


if __name__ == "__main__":
    main()
