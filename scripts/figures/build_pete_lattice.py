"""Generate a new Pete et al. LERW network for website dynamics snapshots.

Independent implementation of the published generator's rules. The open 20x20
substrate and 20-site initial node follow the authors' example_usage notebook;
the paper's bulk experiments use periodic boundaries. Only walk edges and the
single attachment contact are retained. Unused substrate bonds stay absent.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import random

DATA = Path(__file__).resolve().parent / "data"
L = 20
INITIAL_VOLUME = 20
SEED = 2024
CONTACT_WEIGHT = 0.02


def generate():
    rng = random.Random(SEED)
    owner = [-1] * (L * L)
    edges, paths, steps = [], [], []
    adjacency = []
    for node in range(L * L):
        x, y = node % L, node // L
        adjacency.append([yy * L + xx for xx, yy in
                          ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1))
                          if 0 <= xx < L and 0 <= yy < L])
    while -1 in owner:
        module = len(paths)
        start = rng.choice([i for i, value in enumerate(owner) if value == -1])
        path, location, raw_steps = [start], {start: 0}, 0
        while True:
            nxt = rng.choice(adjacency[path[-1]])
            raw_steps += 1
            if owner[nxt] >= 0:
                path.append(nxt)
                break
            if nxt in location:
                cut = location[nxt]
                for node in path[cut + 1:]:
                    del location[node]
                path = path[:cut + 1]
            else:
                location[nxt] = len(path)
                path.append(nxt)
            if module == 0 and len(path) > INITIAL_VOLUME:
                break
        accepted = path[:-1]
        assert accepted and all(owner[i] == -1 for i in accepted)
        for node in accepted:
            owner[node] = module
        edges.extend((a, b, "internal", 1.0) for a, b in zip(accepted[:-1], accepted[1:]))
        if module:
            assert owner[path[-1]] < module
            edges.append((accepted[-1], path[-1], "external", CONTACT_WEIGHT))
        paths.append(accepted)
        steps.append(raw_steps)

    # Independent combinatorial checks; no edge is created just because two
    # sites happen to be adjacent. Each physical node is a nonoverlapping path.
    assert len(edges) == L * L - 1 and len(set(owner)) == len(paths)
    assert sum(e[2] == "external" for e in edges) == len(paths) - 1
    reached, queue = {0}, [0]
    neighbors = [[] for _ in owner]
    for a, b, kind, _ in edges:
        assert b in adjacency[a]
        assert (owner[a] == owner[b]) == (kind == "internal")
        neighbors[a].append(b)
        neighbors[b].append(a)
    for a in queue:
        for b in neighbors[a]:
            if b not in reached:
                reached.add(b)
                queue.append(b)
    assert len(reached) == L * L
    assert len(paths[0]) == INITIAL_VOLUME

    vertex_path = DATA / "pete-lattice-vertices.csv"
    edge_path = DATA / "pete-lattice-edges.csv"
    with vertex_path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["node", "module", "x", "y"])
        writer.writerows((i + 1, module + 1, i % L, i // L) for i, module in enumerate(owner))
    with edge_path.open("w", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(["i", "j", "kind", "weight"])
        writer.writerows((a + 1, b + 1, kind, weight) for a, b, kind, weight in edges)
    metadata = {
        "status": "New seeded realization, independently generated for the website; not copied artwork or a saved paper realization.",
        "paper": {"title": "Physical networks as network-of-networks", "authors": "Pete et al.", "year": 2024, "doi": "10.1038/s41467-024-49227-8"},
        "algorithm_sources": [
            "https://github.com/posfaim/physnets_as_net-o-nets/blob/main/simulations/RWModels.cpp",
            "https://github.com/posfaim/physnets_as_net-o-nets/blob/main/simulations/example_usage.ipynb",
        ],
        "parameters": {"L": L, "initial_node_volume": INITIAL_VOLUME, "seed": SEED,
                       "rng": "Python random.Random (Mersenne Twister)", "boundaries": "open",
                       "boundary_choice": "Authors' open-lattice example notebook; paper bulk simulations use periodic boundaries.",
                       "occupancy": "saturated", "walk": "chronologically loop-erased unbiased nearest-neighbor walk",
                       "later_node_stop": "first hit of any previously occupied site; no length cap",
                       "contact_policy": "single terminal attachment per later path; no unused substrate bonds added",
                       "internal_weight": 1.0, "external_weight": CONTACT_WEIGHT,
                       "weight_choice": "Illustrative dynamics parameters, not fitted or recovered from a paper experiment."},
        "validation": {"sites": len(owner), "edges": len(edges), "connected": True,
                       "tree": True, "physical_nodes": len(paths),
                       "internal_edges": sum(e[2] == "internal" for e in edges),
                       "external_edges": sum(e[2] == "external" for e in edges),
                       "physical_node_volumes": list(map(len, paths)),
                       "raw_steps_per_walk": steps},
        "files": {p.name: {"sha256": hashlib.sha256(p.read_bytes()).hexdigest()}
                  for p in (vertex_path, edge_path)},
    }
    (DATA / "pete-lattice-source.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print(json.dumps({key: value for key, value in metadata["validation"].items()
                      if key not in ("physical_node_volumes", "raw_steps_per_walk")}, indent=2))


if __name__ == "__main__":
    generate()
