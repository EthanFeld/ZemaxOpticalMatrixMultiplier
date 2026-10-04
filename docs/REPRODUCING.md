# Reproducing the OpticStudio result

This guide records the GUI workflow behind the tracked matrix and metrics. The validated lens file and compact surface table are in `zemax/`.

## Lens model

Open [`../zemax/optical_matrix_4x4.zmx`](../zemax/optical_matrix_4x4.zmx) in OpticStudio Student. The GUI-checked system uses Sequential mode, millimeter lens units, one on-axis field, 632.8 nm wavelength, and a 10 mm entrance pupil. The four-surface summary is in [`../zemax/prescription.csv`](../zemax/prescription.csv); the OpticStudio Lens Data Editor and layout views are included below.

![OpticStudio lens data editor](images/opticstudio-prescription.png)

![OpticStudio sequential layout](images/opticstudio-layout.png)

## Generate input beams

Use Python 3.11 or newer:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python scripts/generate_inputs.py
```

This writes four basis beams, `basis_0.zbf` through `basis_3.zbf`, and `demo.zbf` in `data/input/`. The generated files are binary Zemax Beam Files and are ignored by Git. `data/input/manifest.csv` maps each input vector to its intended output filename.

Copy the beams into OpticStudio's `POP/BEAMFILES` folder. Pass the parent `POP` folder; the helper locates `BEAMFILES`:

```powershell
python scripts/copy_to_zemax.py --pop-dir "C:\path\to\Zemax\POP"
```

## Run the five POP propagations

Open the lens file and select Physical Optics Propagation. Use these settings for every run:

| POP control | Setting |
|---|---|
| Start surface | 1 (INPUT FIELD) |
| End surface | 3 (OUTPUT / DFT PLANE) |
| Field / wavelength | 1 / 1 (632.8 nm) |
| Beam type | File |
| Input beam | One selected input `.zbf` |
| Peak irradiance | 1 W/mm² |
| Polarization | Off |
| Output beam | Save on, matching output filename below |
| Auto Apply | Off |
| Sampling | Use sampling encoded by input ZBF |

![POP general settings](images/opticstudio-pop-setup.png)

![POP file input and sampling](images/opticstudio-pop-file-beam.png)

![POP output beam saving](images/opticstudio-pop-output-save.png)

Keep Auto Apply off before changing the input beam so a recalculation cannot replace a previous output. Run one beam at a time and save each output as:

| Input | Output |
|---|---|
| `basis_0.zbf` | `basis_0_out.zbf` |
| `basis_1.zbf` | `basis_1_out.zbf` |
| `basis_2.zbf` | `basis_2_out.zbf` |
| `basis_3.zbf` | `basis_3_out.zbf` |
| `demo.zbf` | `demo_out.zbf` |

Copy these five output beams into `data/output/`. Keep the exact lowercase names shown above. Raw beam files are not tracked because the five outputs total about 80 MiB.

## Analyze and interpret

```powershell
python scripts/analyze_results.py
```

The analyzer reads input and output grid metadata from the ZBF files, extracts complex `Ex` over a 10 µm × 10 µm window at each expected output position, reconstructs the four transfer-matrix columns from the basis runs, applies the known Gaussian-envelope correction, and fits one global complex scale to the matrix. It does not fit entries independently.

The demo beam has a different POP pilot-sphere reference. The analyzer converts the demo field to the same planar field convention, reuses the matrix amplitude calibration, and removes only a unit-magnitude global phase offset. Both phase-aligned and unaligned demo values are saved so this correction is visible.

The checked-in run used 1024 × 1024 input sampling. It produced 4.61% normalized Frobenius matrix error, 2.64° phase RMSE, and 0.78% normalized demo-vector error after global phase alignment. The unaligned demo complex error was 117.6%. Metrics and their supporting values are in [`../results/metrics.json`](../results/metrics.json); matrices and vectors are in [`../results/matrices/`](../results/matrices/).

Use `python scripts/inspect_zbf.py path/to/file.zbf` to inspect beam dimensions, spacing, wavelength, and field power. Run software-only tests with `python -m pytest`; these do not require OpticStudio.
