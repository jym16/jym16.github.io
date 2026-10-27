# Active research visuals and provenance

This document maps the eleven displayed image assets to retained inputs and
builders. Scientific source data live under `scripts/figures/data/`; public
outputs live under `assets/images/research/`. Full earlier provenance and
superseded alternatives are preserved in the ignored local cleanup archive.

## Homepage

- **`home-physical-pore.svg` (960 x 976):** empirical sandstone pore-space
  reconstruction from
  `slides-defence.zip/slides-defence/figures/introduction/pore_reconstruction.png`.
  The source slides identify X-ray micro-CT and credit Lucas-Oliveira et al.,
  *Data in Brief* **41**, 107893 (2022), DOI 10.1016/j.dib.2022.107893. The exact
  sample is unspecified. `build_home_pore.py` preserves the source pixels,
  embeds lossless WebP, and trims transparent margins through the SVG viewport.
  `data/home-pore-source.png` and `data/home-pore-provenance.json` retain the
  original image, source hashes, encoding checks, and viewport transformation.
- **`home-scaling-schematic.svg` (960 x 455):** Figure 1(b), PDF page 3, from
  Yamamoto and Yakubo, *Bifractality of fractal scale-free networks*, PRE **108**,
  024302 (2023), DOI 10.1103/PhysRevE.108.024302. The crop is
  [45, 198, 296, 317] pt in top-left PDF coordinates. Poppler rendering and
  lossless WebP preserve the original diagram. `build_home_scaling.py` embeds
  `data/home-scaling-schematic.webp` unchanged and covers only the panel marker
  with a white vector rectangle at [0, 190, 75, 75] px. The scientific green `b`
  and `b_c` labels remain. `home-scaling-source.json` records the source PDF
  hash, crop, retained-input hash, and output hash.
- **`home-fhn-voltage.svg` (640 x 400):** the specifically authorized top-left
  panel of execution `In[6]` (zero-based cell index 12) in
  `letter_v6/companion-code/notebooks/fhn_fig01_explorer.ipynb`.
  `build_home_fhn.py` reads only time and eight mean-voltage curves from
  `data/home-fhn-voltage.csv`. It preserves the source colors and five-reference-
  period window [555.9489491379145, 800]. The first row is the exact clipped
  endpoint of the original plotted polyline; the remaining 1221 rows are
  unmodified saved-sample means. There is no smoothing or new integration.
  `data/home-fhn-voltage-provenance.json` records hashes and exact aggregation.
  Other notebook panels, private parameters, and the full state archive are
  excluded from the retained website data.

## Physical-network figures

**`physical-structure-panels.svg` (1160 x 514)** arranges Figure 1(a,b) from
`deloc_revised.zip/pre_revised/figures/fig_multiscale_origin.pdf` horizontally
at equal scale. The crops are [0, 0, 78.27417, 64] and
[0, 65, 78.27417, 133.667] pt. Original colors and scientific labels are
preserved; only panel letters are covered. The lossless inputs are
`data/physical-structure-panel-a.webp` and
`data/physical-structure-panel-b.webp`. Rebuild with
`build_physical_structure.py`; source hashes, crops, placement, and output hash
are recorded in `physical-structure-sources.json`.

Both dynamics illustrations use the same newly generated realization of
Pete et al., *Physical networks as network-of-networks*, Nature Communications
**15**, 4882 (2024), DOI 10.1038/s41467-024-49227-8. The construction follows the
authors' `simulations/RWModels.cpp` and `simulations/example_usage.ipynb` at
<https://github.com/posfaim/physnets_as_net-o-nets>. The open 20 x 20 lattice and
first physical-node volume 20 follow their example; bulk paper simulations use
periodic boundaries. The website realization uses seed 2024.

Chronologically loop-erased paths fill 400 microscopic sites and form 166
physical nodes. Only path bonds and each later path's single terminal contact
are retained: 234 internal edges and 165 contacts. Unused substrate bonds are
absent. Illustrative weights are 1 internally and 0.02 at contacts. These are
not fitted experimental parameters or a guarantee of strong time-scale
separation on long paths. Geometry, partition, edges, source links, and checks
are retained in `data/pete-lattice-{vertices.csv,edges.csv,source.json}`;
`build_pete_lattice.py` regenerates the seeded realization.

- **`diffusion-localized-mode.svg` (350 x 400):** one eigenmode of the symmetric
  weighted microscopic Laplacian, selected by proximity to target IPR 0.02.
  Counting the zero mode as number 1, the selected mode is number 9, with
  eigenvalue 0.0008027404408399634. Its Euclidean-normalized vector satisfies
  `sum_i |u_i|^2 = 1`. Color uses the raw signed `amplitude` column, without
  squaring or dividing by the maximum, on the fixed symmetric range
  [-0.25, 0.25]. The largest-magnitude amplitude is positive by convention.
  IPR is 0.01958631973702968 and effective participation `1/IPR` is 51.0560;
  this is not a count of nonzero sites or a thermodynamic classification.
  The eigenpair residual is 2.612e-15. `plot_diffusion_lattice.py` reads
  `data/pete-lattice-eigenmode.csv`; the metadata and full spectrum are retained
  alongside it. `prepare_lattice_eigenmode.py` recomputes the selection.
- **`synchronization-phase-arrows.svg` (350 x 380):** one simulated state of
  identical-frequency Kuramoto oscillators with
  `dtheta_i/dt = sum_j w_ij sin(theta_j-theta_i)`. Initial phases comprise one
  full-circle random phase per physical node and small site jitter. Integer
  seeds 0 through 31 are tested in order until initial microscopic R < 0.09;
  seed 1 is selected. The trajectory is followed to the first 0.125-grid
  crossing of microscopic `R = |mean_i exp(i theta_i)| = 0.7`, then recomputed
  at timestep 0.0625. The retained state at time 7736.875 has R = 0.7000039205;
  the two integrations differ by at most 1.95e-8 radians and 3.91e-9 in R.
  Equal weights apply to all microscopic sites, not to unequal-volume physical
  nodes. Phases are not rescaled or rotated to enforce the target.
  Constant-length arrows encode angle. `prepare_sync_phase.py` retains the
  state and checks in `data/pete-sync-phase.npz` and its metadata;
  `plot_sync_lattice.py` renders them without integration. This explicitly
  selected state is not claimed to be statistically representative.

These dynamics are new website illustrations, not measurements or saved paper
frames. `lattice_snapshot_style.py` supplies the common geometry rendering.

## Scaling data plots

- **`scaling-return-probability.svg` (640 x 480):** 197 points for each of a hub
  and distant non-hub start, recovered from circular vector markers in Figure
  2(b), PDF page 5, of Yakubo, Shimojo and Yamamoto, PRE **110**, 064318 (2024),
  DOI 10.1103/PhysRevE.110.064318. These are digitized published points, not
  original numerical files. The example is deterministic generator G_A,
  generation 8; both G_A series are unshifted. Filled/open markers preserve
  starting-node identity. Tick-calibration discrepancies correspond to about
  0.21% in time and 0.64% in probability; these are calibration checks rather
  than statistical errors. Theoretical spectral dimensions are approximately
  1.13865 and 2. Guides have explicitly illustrative vertical offsets. The inset
  reproduces Generator A from Figure 1(a): four nodes and five edges, with white
  left/right roots and black top/bottom internal nodes. Data, calibration,
  source PDF hash, and slope checks are retained in
  `data/scaling-return-probability*`.
- **`scaling-crossover.svg` (640 x 400):** supplied figure-ready data from
  `crossover/figures/data/figures/fig2{a,b}.csv`. The displayed series has
  gamma = 4.25 and root degrees 15, 20, 25, 30. These critical random networks
  differ from the G_A model above. Source column order, file hashes, observables,
  and selection are retained in `data/scaling-crossover-source.json`; the
  supplied observations remain in `data/scaling-crossover.csv`.

`build_scaling.py` redraws both charts. `modsync_style.py` supplies Times New
Roman/STIX, black axes, outward ticks, unframed legends, and the Hiroshige
palette; `modsync-style-source.json` records the source style hashes. Outlined
SVG text removes visitors' dependence on local fonts. Scaling labels are enlarged
for the narrow website column without changing data or guide meanings.

## Selected published work

These retained PNG exports preserve the original paper presentation:

- `bifractality-fig1.png`: Figure 1, Yamamoto and Yakubo, PRE **108**, 024302
  (2023), DOI 10.1103/PhysRevE.108.024302.
- `random-walks-return-probability.png`: Figure 2(b), Yakubo, Shimojo and
  Yamamoto, PRE **110**, 064318 (2024), DOI 10.1103/PhysRevE.110.064318. The full
  panel was cropped from PDF page 5 at 288 dpi; its other-model series retain
  the published vertical offsets. The optional `--published-crop` operation in
  `build_scaling.py` reproduces the export from the original PDF.
- `triadic-interactions-fig1-panels-ab.png`: Figure 1(a,b), Niedostatek et al.,
  Nature Communications **16**, 11613 (2025), DOI 10.1038/s41467-025-66577-z.

Original research directories are read only. The ignored local archive retains
superseded alternatives and their full earlier provenance, including withheld
working-manuscript materials; the active builders create only displayed assets.
