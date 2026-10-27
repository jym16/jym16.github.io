"""Retain one microscopic diffusion eigenmode near the requested IPR."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parent / "data"
TARGET_IPR = 0.02


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(target_ipr=TARGET_IPR):
    inputs = [DATA / "pete-lattice-vertices.csv", DATA / "pete-lattice-edges.csv"]
    manifest = json.loads((DATA / "pete-lattice-source.json").read_text())
    for path in inputs:
        assert digest(path) == manifest["files"][path.name]["sha256"]
    with inputs[0].open(newline="") as stream:
        vertices = list(csv.DictReader(stream))
    with inputs[1].open(newline="") as stream:
        edges = list(csv.DictReader(stream))
    n = len(vertices)
    assert [int(v["node"]) for v in vertices] == list(range(1, n + 1))
    adjacency = np.zeros((n, n))
    for edge in edges:
        i, j = int(edge["i"]) - 1, int(edge["j"]) - 1
        adjacency[i, j] = adjacency[j, i] = float(edge["weight"])
    laplacian = np.diag(adjacency.sum(axis=1)) - adjacency
    eigenvalues, eigenvectors = np.linalg.eigh(laplacian)
    iprs = np.sum(eigenvectors ** 4, axis=0) / np.sum(eigenvectors ** 2, axis=0) ** 2
    nonzero = np.flatnonzero(eigenvalues > 1e-12)
    selected = int(nonzero[np.argmin(abs(iprs[nonzero] - target_ipr))])
    vector = eigenvectors[:, selected].copy()
    vector /= np.linalg.norm(vector)
    # Deterministic sign for retaining the vector; plotted intensity is sign-free.
    if vector[np.argmax(abs(vector))] < 0:
        vector *= -1
    intensity = vector ** 2
    ipr = float(np.sum(intensity ** 2))
    residual = float(np.linalg.norm(laplacian @ vector - eigenvalues[selected] * vector))
    gaps = [float(eigenvalues[selected] - eigenvalues[selected - 1]),
            float(eigenvalues[selected + 1] - eigenvalues[selected])]
    assert abs(ipr - target_ipr) < 0.005
    assert residual < 1e-11 and min(gaps) > 1e-8
    assert abs(intensity.sum() - 1) < 1e-12
    assert abs(vector.sum()) < 1e-10
    output = DATA / "pete-lattice-eigenmode.csv"
    with output.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["node", "module", "x", "y", "amplitude", "intensity"])
        for vertex, value, power in zip(vertices, vector, intensity):
            writer.writerow([vertex[key] for key in ("node", "module", "x", "y")]
                            + [f"{value:.17g}", f"{power:.17g}"])
    spectrum = DATA / "pete-lattice-eigenmode-spectrum.csv"
    with spectrum.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["mode_index_one_based", "eigenvalue", "IPR"])
        writer.writerows((i + 1, f"{value:.17g}", f"{iprs[i]:.17g}")
                         for i, value in enumerate(eigenvalues))
    sorted_intensity = np.sort(intensity)[::-1]
    metadata = {
        "artifact": "One computed microscopic diffusion eigenmode on the retained Pete et al. lattice realization.",
        "source_manifest": "pete-lattice-source.json",
        "operator": "400-site weighted combinatorial Laplacian L=D-A, unit microscopic capacities, internal weights 1 and terminal contacts 0.02; not the 166-node coarse operator.",
        "selection": {"target_IPR": target_ipr,
                      "rule": "Choose the nonzero eigenmode minimizing absolute distance to target IPR over the full spectrum.",
                      "mode_index_one_based_including_zero": selected + 1},
        "normalization": "Euclidean norm sum_i |u_i|^2=1; IPR=sum_i |u_i|^4. Largest-magnitude amplitude chosen positive; intensity is sign invariant.",
        "display": "Raw signed Euclidean-norm-one eigenmode amplitudes u_i (sum_i u_i^2=1), with fixed zero-centered color limits [-0.25, 0.25]; no division by maximum amplitude, squaring, logarithm, or thresholding.",
        "eigenvalue": float(eigenvalues[selected]), "IPR": ipr,
        "effective_participation_sites": 1 / ipr,
        "validation": {"eigenpair_l2_residual": residual,
                       "neighboring_eigenvalue_gaps": gaps, "intensity_sum": float(intensity.sum()),
                       "amplitude_sum": float(vector.sum()), "maximum_intensity": float(intensity.max()),
                       "sites_containing_90_percent_intensity": int(np.searchsorted(np.cumsum(sorted_intensity), .9) + 1)},
        "inputs": {path.name: {"sha256": digest(path)} for path in inputs},
        "outputs": {path.name: {"sha256": digest(path)} for path in (output, spectrum)},
        "numpy_version": np.__version__,
    }
    (DATA / "pete-lattice-eigenmode-metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({key: metadata[key] for key in ("eigenvalue", "IPR", "effective_participation_sites", "validation")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-ipr", type=float, default=TARGET_IPR)
    main(parser.parse_args().target_ipr)
