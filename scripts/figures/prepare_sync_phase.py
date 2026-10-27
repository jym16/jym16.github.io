#!/usr/bin/env python3
"""Prepare one genuine selected Kuramoto phase snapshot on the Pete graph.

This is an explicitly selected new illustrative trajectory, not a paper result
or a representative random-initial-condition claim. The first seed from 0..31
with initial microscopic unit-weight R < 0.09 is selected. The RK4 trajectory
is followed to its first dt=0.125 grid crossing of TARGET_R, and that time is
independently integrated at dt=0.0625. The finer state is the retained snapshot.
No phase rescaling, recentering, or manual modification is performed.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path
import time

import numpy as np

DATA = Path(__file__).resolve().parent / "data"
TARGET_R = 0.7
INITIAL_R_LIMIT = 0.09
INITIAL_SEED_CANDIDATES = range(32)
JITTER_BOUND = 0.05
DT = 0.125
MAX_TIME = 100000.0
TRACE_STRIDE = 8


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="") as stream:
        return list(csv.DictReader(stream))


def order_parameter(theta: np.ndarray) -> float:
    """Every microscopic site has unit weight; phases are in radians."""
    return float(abs(np.mean(np.exp(1j * theta))))


def inputs(folder: Path) -> dict:
    vertex_file = folder / "pete-lattice-vertices.csv"
    edge_file = folder / "pete-lattice-edges.csv"
    manifest_file = folder / "pete-lattice-source.json"
    manifest = json.loads(manifest_file.read_text())
    for path in (vertex_file, edge_file):
        if sha256(path) != manifest["files"][path.name]["sha256"]:
            raise ValueError(f"Input checksum does not match graph provenance: {path.name}")
    vertices = sorted(read_csv(vertex_file), key=lambda row: int(row["node"]))
    edges = read_csv(edge_file)
    n = len(vertices)
    if [int(row["node"]) for row in vertices] != list(range(1, n + 1)):
        raise ValueError("Expected consecutive one-based microscopic node IDs.")
    module = np.array([int(row["module"]) for row in vertices])
    module_ids = np.unique(module)
    if not np.array_equal(module_ids, np.arange(1, len(module_ids) + 1)):
        raise ValueError("Expected consecutive one-based physical-node IDs.")
    source = np.array([int(row["i"]) - 1 for row in edges])
    target = np.array([int(row["j"]) - 1 for row in edges])
    coupling = np.array([float(row["weight"]) for row in edges])
    internal = np.array([row["kind"] == "internal" for row in edges])
    if not np.array_equal(internal, module[source] == module[target]):
        raise ValueError("Physical-node membership disagrees with edge classification.")
    if not np.array_equal(coupling, np.where(internal, 1.0, 0.02)):
        raise ValueError("Expected internal coupling 1 and external coupling 0.02.")
    return {"n": n, "module": module, "module_ids": module_ids,
            "coordinates": np.array([[float(row["x"]), float(row["y"])] for row in vertices]),
            "source": source, "target": target, "coupling": coupling, "internal": internal,
            "manifest": manifest, "input_files": (vertex_file, edge_file, manifest_file)}


def make_rhs(graph: dict):
    source, target, weight, n = (graph[key] for key in ("source", "target", "coupling", "n"))

    def rhs(theta):
        flow = weight * np.sin(theta[target] - theta[source])
        return (np.bincount(source, weights=flow, minlength=n)
                - np.bincount(target, weights=flow, minlength=n))

    return rhs


def rk4_step(rhs, theta: np.ndarray, dt: float) -> np.ndarray:
    k1 = rhs(theta)
    k2 = rhs(theta + dt * k1 / 2)
    k3 = rhs(theta + dt * k2 / 2)
    k4 = rhs(theta + dt * k3)
    return theta + dt * (k1 + 2 * k2 + 2 * k3 + k4) / 6


def phase_potential(theta: np.ndarray, graph: dict) -> float:
    return float(np.sum(graph["coupling"] * (1 - np.cos(theta[graph["target"]] - theta[graph["source"]]))))


def select_initial_state(graph: dict) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[dict]]:
    attempted = []
    for seed in INITIAL_SEED_CANDIDATES:
        rng = np.random.Generator(np.random.PCG64(seed))
        module_phase = rng.uniform(-np.pi, np.pi, len(graph["module_ids"]))
        jitter = rng.uniform(-JITTER_BOUND, JITTER_BOUND, graph["n"])
        theta = module_phase[graph["module"] - 1] + jitter
        value = order_parameter(theta)
        attempted.append({"seed": seed, "initial_microscopic_R": value})
        if value < INITIAL_R_LIMIT:
            return theta, module_phase, jitter, attempted
    raise RuntimeError("No initial phase seed met the stated criterion within the fixed 32-seed search.")


def prepare(folder: Path) -> dict:
    graph = inputs(folder)
    rhs = make_rhs(graph)
    initial, module_phase, jitter, attempts = select_initial_state(graph)
    # Check the implemented edge flow against an independent scalar sum.
    scalar = np.zeros(graph["n"])
    for i, j, weight in zip(graph["source"], graph["target"], graph["coupling"]):
        value = weight * np.sin(initial[j] - initial[i])
        scalar[i] += value
        scalar[j] -= value
    rhs_error = float(np.max(abs(rhs(initial) - scalar)))
    if rhs_error > 1e-13:
        raise RuntimeError("Independent scalar RHS comparison failed.")

    started = time.perf_counter()
    theta = initial.copy()
    trace_time, trace_R = [0.0], [order_parameter(theta)]
    trace_potential, trace_mean = [phase_potential(theta, graph)], [float(theta.mean())]
    previous = theta.copy()
    previous_R = trace_R[0]
    for step in range(1, round(MAX_TIME / DT) + 1):
        previous = theta.copy()
        previous_R = order_parameter(previous)
        theta = rk4_step(rhs, theta, DT)
        value = order_parameter(theta)
        if step % TRACE_STRIDE == 0 or value >= TARGET_R:
            trace_time.append(step * DT)
            trace_R.append(value)
            trace_potential.append(phase_potential(theta, graph))
            trace_mean.append(float(theta.mean()))
        if value >= TARGET_R:
            break
    else:
        raise RuntimeError("The chosen trajectory did not cross the target within the declared time limit.")
    selected_time = step * DT
    coarse = theta.copy()
    fine = initial.copy()
    fine_mean_error = 0.0
    for fine_step in range(1, 2 * step + 1):
        fine = rk4_step(rhs, fine, DT / 2)
        if fine_step % (2 * TRACE_STRIDE) == 0 or fine_step == 2 * step:
            fine_mean_error = max(fine_mean_error, abs(float(fine.mean() - initial.mean())))
    actual_R = order_parameter(fine)
    state_error = float(np.max(abs(coarse - fine)))
    order_error = abs(order_parameter(coarse) - actual_R)
    mean_error = max(fine_mean_error, float(np.max(abs(np.asarray(trace_mean) - initial.mean()))))
    potential_increase = float(max(0.0, np.max(np.diff(trace_potential))))
    if (not np.isfinite(fine).all() or abs(actual_R - TARGET_R) > 0.005
            or state_error > 1e-5 or order_error > 1e-7 or mean_error > 1e-11
            or potential_increase > 1e-11 or previous_R >= TARGET_R):
        raise RuntimeError(f"Selected phase snapshot failed validation: R={actual_R}, state error={state_error}.")

    physical_means = np.array([np.mean(np.exp(1j * fine[graph["module"] == group]))
                               for group in graph["module_ids"]])
    volumes = np.bincount(graph["module"])[1:]
    equal_node_R = float(abs(np.mean(np.exp(1j * np.angle(physical_means)))))
    equal_node_complex_R = float(abs(physical_means.mean()))
    volume_weighted_R = float(abs(np.sum(volumes * physical_means) / volumes.sum()))
    diagnostics = {
        "selected_time": selected_time, "target_microscopic_R": TARGET_R,
        "actual_microscopic_R": actual_R, "coarse_microscopic_R": order_parameter(coarse),
        "previous_coarse_grid_time": selected_time - DT, "previous_coarse_grid_R": previous_R,
        "coarse_vs_fine_maximum_phase_difference_rad": state_error,
        "coarse_vs_fine_R_difference": order_error,
        "global_mean_phase_conservation_maximum_error_rad": mean_error,
        "phase_potential_largest_sampled_increase": potential_increase,
        "independent_scalar_RHS_maximum_difference": rhs_error,
        "physical_node_equal_weight_mean_phase_R": equal_node_R,
        "physical_node_equal_weight_complex_mean_R": equal_node_complex_R,
        "physical_node_volume_weighted_complex_mean_R": volume_weighted_R,
        "equal_physical_node_R_differs_from_microscopic_R": bool(abs(equal_node_R - actual_R) > 1e-3),
        "within_physical_node_coherence_range": [float(abs(physical_means).min()), float(abs(physical_means).max())],
        "integration_wall_seconds": time.perf_counter() - started,
    }
    output = folder / "pete-sync-phase.npz"
    np.savez_compressed(output, theta=fine, theta_mod_2pi=np.mod(fine, 2 * np.pi),
                        theta_initial=initial, theta_coarse_step=coarse,
                        theta_previous_coarse_step=previous, time=np.array(selected_time),
                        initial_module_phase=module_phase, initial_site_jitter=jitter,
                        module=graph["module"], module_volume=volumes,
                        module_complex_mean=physical_means, coordinates=graph["coordinates"],
                        edge_i=graph["source"] + 1, edge_j=graph["target"] + 1,
                        edge_internal=graph["internal"], edge_weight=graph["coupling"],
                        order_parameter_R=np.array(actual_R), trace_time=np.asarray(trace_time),
                        trace_order_parameter_R=np.asarray(trace_R),
                        trace_phase_potential=np.asarray(trace_potential),
                        trace_global_mean_phase=np.asarray(trace_mean),
                        source_manifest=np.array("pete-lattice-source.json"))
    metadata = {
        "status": "New illustrative Kuramoto trajectory with an explicitly selected phase snapshot; not paper frames or measurements.",
        "geometry": "The same bundled Pete et al. LERW open20x20 realization used for the diffusion figure; see pete-lattice-source.json.",
        "equation": "dtheta_i/dt = sum_j w_ij*sin(theta_j-theta_i), with every intrinsic frequency zero",
        "couplings": {"internal": 1.0, "external": 0.02, "status": "Illustrative parameters, not fitted or recovered paper parameters"},
        "initial_condition": {"rng": "numpy.random.Generator(PCG64)",
            "module_phase_distribution": "One independent Uniform[-pi,pi) phase per physical node, in ascending physical-node ID order",
            "site_jitter_distribution": "Independent Uniform[-0.05,0.05) radians, in ascending microscopic-site ID order, drawn after all module phases",
            "seed_protocol": "Test integer seeds0..31 in ascending order; select the first with microscopic unit-weight initial R<0.09; no other seed or state criterion",
            "attempted_seeds": attempts, "selected_seed": attempts[-1]["seed"],
            "phase_adjustment": "None: no rescaling, centering, or rotation before or after integration"},
        "snapshot_selection": {"target_R": TARGET_R,
            "criterion": f"First dt={DT:g} grid crossing from R<{TARGET_R:g} to R>={TARGET_R:g}; the same time is recomputed at dt={DT/2:g}, whose full state is retained",
            "maximum_search_time": MAX_TIME, "actual_time": selected_time,
            "actual_R": actual_R, "accepted_absolute_target_tolerance": 0.005},
        "solver": {"method": "Classical fixed-step RK4, NumPy float64", "retained_state_dt": DT / 2,
            "coarse_comparison_dt": DT, "accepted_snapshot_phase_difference_rad": 1e-5,
            "accepted_snapshot_R_difference": 1e-7, "time_units": "Dimensionless inverse internal-coupling rate"},
        "phase_reference": "Raw seeded angular coordinate shared by every site; no state-dependent rotation. theta_mod_2pi is only the equivalent arrow orientation.",
        "order_parameter_definition": "R=abs(mean_i(exp(1j*theta_i))) with equal unit weight for each of the400 microscopic sites; not equal weight per physical node",
        "physical_node_weighting_note": "Equal physical-node weighting can differ because physical-node volumes are unequal. Volume-weighted complex physical-node means reproduce the microscopic order parameter; the displayed target uses microscopic unit weights.",
        "interpretation_limit": "This is one trajectory from phases spanning a full circle; it makes no claim that arbitrary full-circle initial phases guarantee global consensus or that the selected snapshot is statistically representative.",
        "saved_quantities": "Full fine snapshot, initial phases, coarse snapshot, previous coarse-grid phases, geometry, edge weights, and sampled scalar diagnostics; traces are the coarse run at one time unit intervals plus the crossing",
        "diagnostics": diagnostics,
        "source_manifest": "pete-lattice-source.json",
        "input_sha256": {path.name: sha256(path) for path in graph["input_files"]},
        "script_sha256": sha256(Path(__file__)),
        "output": {"file": output.name, "sha256": sha256(output)},
        "software": {"numpy": np.__version__},
    }
    (folder / "pete-sync-phase-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps(diagnostics, indent=2))
    return diagnostics


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA)
    args = parser.parse_args()
    prepare(args.data_dir)


if __name__ == "__main__":
    main()
