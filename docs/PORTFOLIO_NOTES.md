# Portfolio notes

## Résumé description

Designed a 4×4 coherent optical DFT matrix-vector multiplier and validated it in Ansys Zemax OpticStudio Student. Generated complex Zemax Beam Files, ran four basis-beam POP propagations to measure the complex transfer matrix, and checked a fifth demo-vector run. The measured matrix has 4.61% normalized Frobenius error against the target DFT; the independent demo has 0.78% normalized L2 error after correcting POP's pilot phase reference and aligning one global phase.

## Technical keywords

Fourier optics · coherent optics · computational optics · Zemax OpticStudio · Physical Optics Propagation · matrix-vector multiplication · optical computing · complex electric fields · Python · NumPy · signal processing

## Concepts demonstrated

- Continuous versus discrete Fourier transforms.
- Complex optical encoding with amplitude and phase.
- Spatial-frequency sampling in a lens Fourier plane.
- POP numerical sampling and output-grid inspection.
- Calibration of an optical transfer function with one global complex scale.
- Matrix-level validation using magnitude, phase, and error metrics.

## Validation evidence

The GUI-saved `optical_matrix_4x4.zmx`, POP setup screenshots, native OpticStudio demo plot, measured matrix CSVs, metrics, and validation figures are in the repository. Five raw output ZBFs are omitted because they total about 80 MiB; the README documents how to regenerate them. The matrix result meets the below-5% target. State the phase alignment whenever quoting the demo error; no demo amplitude was fitted.
