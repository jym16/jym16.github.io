# Website research figures

The eight configured website pages share eleven research image outputs. This
directory retains the builders, scientific inputs, and provenance for those
outputs. The three paper figures under Selected published work retain their
original presentation; the other eight outputs have reproducible builders.

## Rebuild the displayed figures

Install `requirements.txt` in a Python environment, then run from the repository
root:

```sh
python scripts/figures/build_home_pore.py
python scripts/figures/build_home_scaling.py
python scripts/figures/build_home_fhn.py
python scripts/figures/build_physical_structure.py
python scripts/figures/plot_diffusion_lattice.py
python scripts/figures/plot_sync_lattice.py
python scripts/figures/build_scaling.py
quarto render
```

These commands read retained inputs under `scripts/figures/data/`. They do not
require a research-project checkout or integrate new dynamics. Optional PNG
previews go to temporary directories. The two original physical-schematic WebPs
and the published scaling-schematic WebP are source inputs in `data/`; the
website SVGs embed them, so only the final figures live in the public image
directory.

`build_scaling.py` renders only the two displayed data plots. Its older
`--plots-only` option remains accepted for compatibility. Optional source import
and original-paper cropping flags remain available; use `--help` for details.
They read the supplied external source paths and write only the website checkout.

## Retained sources

| Output | Builder | Retained inputs |
| --- | --- | --- |
| `home-physical-pore.svg` | `build_home_pore.py` | `data/home-pore-source.png` and its provenance |
| `home-scaling-schematic.svg` | `build_home_scaling.py` | `data/home-scaling-schematic.webp`, `home-scaling-source.json` |
| `home-fhn-voltage.svg` | `build_home_fhn.py` | `data/home-fhn-voltage.csv` and its provenance |
| `physical-structure-panels.svg` | `build_physical_structure.py` | `data/physical-structure-panel-{a,b}.webp`, `physical-structure-sources.json` |
| `diffusion-localized-mode.svg` | `plot_diffusion_lattice.py` | `data/pete-lattice-eigenmode*` and the shared Pete network |
| `synchronization-phase-arrows.svg` | `plot_sync_lattice.py` | `data/pete-sync-phase*` and the shared Pete network |
| `scaling-return-probability.svg` | `build_scaling.py` | `data/scaling-return-probability*` |
| `scaling-crossover.svg` | `build_scaling.py` | `data/scaling-crossover*` |

The pore reconstruction retains its original pixels and trims transparent
viewport margins. The slides credit Lucas-Oliveira et al. (2022),
DOI 10.1016/j.dib.2022.107893; the exact sandstone sample is unspecified.

The homepage voltage plot retains only the specifically authorized top-left
panel from notebook execution `In[6]` (zero-based cell index 12) in
`fhn_fig01_explorer.ipynb`. Its CSV contains time and eight module-mean voltage
curves over the source window. The first row is the exact clipped endpoint of
the source's plotted polyline; subsequent rows are unmodified saved-sample means.
The full notebook, full simulation archive, other dashboard panels, and private
model parameters are not bundled. Default rebuilding uses the minimal CSV;
`--source-dir` explicitly imports this one panel from a read-only source checkout.

## Recompute the illustrative network and states

The physical-network dynamics figures use a new realization of the loop-erased
random-walk construction of Pete et al., *Physical networks as
network-of-networks*, Nature Communications **15**, 4882 (2024),
[DOI 10.1038/s41467-024-49227-8](https://doi.org/10.1038/s41467-024-49227-8).
The retained open 20 x 20 geometry, first physical-node volume 20, seed 2024,
path edges, and terminal contacts are documented in `data/pete-lattice-source.json`.
Internal weights 1 and contact weights 0.02 are illustrative dynamics parameters.

To regenerate the geometry, selected eigenmode, and selected phase state,
optionally run:

```sh
python scripts/figures/build_pete_lattice.py
python scripts/figures/prepare_lattice_eigenmode.py
python scripts/figures/prepare_sync_phase.py
```

The diffusion figure displays a Euclidean-norm-one eigenvector's raw signed
amplitudes, with a zero-centered color scale fixed at [-0.25, 0.25]. Its
`IPR = sum_i |u_i|^4 = 0.0195863197` corresponds to approximately 51.06 effective
participating sites. No additional amplitude rescaling is applied.

The phase arrows show one genuine identical-frequency Kuramoto state selected
near the first upward crossing of microscopic
`R = |mean_i exp(i theta_i)| = 0.7`. Each microscopic site has equal weight.
The unchanged seed-selection protocol chooses seed 1; the retained state at
time 7736.875 has R = 0.7000039205. The coarse and fine timesteps agree within
1.95e-8 radians. This selected state is an illustration rather than a claim
about typical random initial conditions or guaranteed global consensus.

## Data plots and typography

The return-probability points were recovered from published vector markers in
PRE **110**, 064318 (2024), Figure 2(b). They are digitized published data rather
than original numerical files. The crossover plot uses supplied figure-ready
data for a different network model. Their source hashes, curve identities,
calibration, and transformations remain with the retained scaling data.

The shared `modsync_style.py` uses the manuscript's Times New Roman/STIX
typography, black axes, outward ticks, unframed legends, and Hiroshige palette.
The scaling charts use larger text for the narrow website column. Installed
Times New Roman faces are registered on macOS; STIXGeneral is the portable
fallback. SVG glyphs are outlined, so site visitors need no local font files.
`modsync-style-source.json` records the original style-source hashes.

See [SOURCES.md](SOURCES.md) for the active figure mapping and scientific notes.

## Local archive

Superseded overviews, unused paper exports, older time-series simulations, and
withheld synchronization alternatives were moved with their inputs and source
records to the ignored local directory
`_backup/repository-cleanup-20261027/figures/`, preserving their relative paths.
Its manifest records hashes and distinguishes archived originals from copied
shared dependencies. Those historical builders are absent from the normal
rebuild commands and cannot recreate unused public assets accidentally.
