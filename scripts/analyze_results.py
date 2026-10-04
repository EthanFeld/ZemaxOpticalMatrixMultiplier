#!/usr/bin/env python3
"""Reconstruct and compare the measured optical transfer matrix."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optical_mvm import load_project_config
from optical_mvm.extraction import extract_channels
from optical_mvm.fields import field_normalization_factor
from optical_mvm.plotting import (
    plot_demo_comparison,
    plot_input_intensity,
    plot_matrix_error,
    plot_matrix_magnitude,
    plot_matrix_phase,
    plot_output_intensity,
)
from optical_mvm.theory import (
    centered_dft_matrix,
    dft_frequencies,
    focal_plane_positions,
    gaussian_fourier_envelope,
)
from optical_mvm.zbf import plane_reference_factor, read_zbf


def save_complex_matrix_csv(path: Path, matrix: np.ndarray) -> None:
    columns: dict[str, np.ndarray] = {}
    for col in range(matrix.shape[1]):
        columns[f"input_{col}_real"] = matrix[:, col].real
        columns[f"input_{col}_imag"] = matrix[:, col].imag
    dataframe = pd.DataFrame(columns, index=pd.Index(range(matrix.shape[0]), name="output_channel"))
    dataframe.to_csv(path, float_format="%.12g")


def save_complex_vector_csv(path: Path, vector: np.ndarray) -> None:
    pd.DataFrame({
        "output_channel": np.arange(vector.size),
        "real": vector.real,
        "imag": vector.imag,
        "magnitude": np.abs(vector),
        "phase_deg": np.angle(vector, deg=True),
    }).to_csv(path, index=False, float_format="%.12g")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "project.yaml")
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data" / "input")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "output")
    parser.add_argument("--results-dir", type=Path, default=ROOT / "results")
    args = parser.parse_args()

    config = load_project_config(args.config)
    count = int(config["matrix"]["size"])
    channel_cfg = config["input_channels"]
    optical_cfg = config["optics"]
    analysis_cfg = config["analysis"]
    wavelength = float(optical_cfg["wavelength_mm"])
    focal_length = float(optical_cfg["focal_length_mm"])
    pitch = float(channel_cfg["pitch_mm"])
    waist = float(channel_cfg["gaussian_radius_mm"])
    sign = int(config["matrix"].get("fourier_sign", 1))
    positions = focal_plane_positions(count, pitch, wavelength, focal_length)
    frequencies = dft_frequencies(count, pitch)
    envelope = gaussian_fourier_envelope(frequencies, waist)
    half_width = float(analysis_cfg["extraction_half_width_um"]) * 1e-3
    target = centered_dft_matrix(count, sign)
    alternative_sign = -sign
    alternative_target = centered_dft_matrix(count, alternative_sign)
    real = np.asarray(config["demo_vector"]["real"], dtype=np.float64)
    imag = np.asarray(config["demo_vector"].get("imag", np.zeros_like(real)), dtype=np.float64)
    demo_vector = real + 1j * imag

    for filename in ("basis_0.zbf", "demo.zbf"):
        if not (args.input_dir / filename).is_file():
            raise SystemExit(f"Missing generated input beam: {args.input_dir / filename}; run scripts/generate_inputs.py first.")
    basis_input = read_zbf(args.input_dir / "basis_0.zbf")
    demo_input = read_zbf(args.input_dir / "demo.zbf")
    if not np.isclose(basis_input.wavelength_mm, wavelength, rtol=1e-6, atol=0.0):
        raise SystemExit(f"Input basis wavelength ({basis_input.wavelength_mm:g} mm) does not match config ({wavelength:g} mm).")
    if not np.isclose(demo_input.wavelength_mm, wavelength, rtol=1e-6, atol=0.0):
        raise SystemExit(f"Input demo wavelength ({demo_input.wavelength_mm:g} mm) does not match config ({wavelength:g} mm).")
    if (basis_input.nx, basis_input.ny, basis_input.dx_mm, basis_input.dy_mm) != (
        demo_input.nx, demo_input.ny, demo_input.dx_mm, demo_input.dy_mm
    ):
        raise SystemExit("Generated basis_0.zbf and demo.zbf use different sampling grids.")
    nx, ny = basis_input.nx, basis_input.ny
    dx, dy = basis_input.dx_mm, basis_input.dy_mm
    basis_norm = field_normalization_factor(
        basis_input.x_mm, basis_input.y_mm, np.eye(count, dtype=np.complex128)[0],
        channel_cfg["centers_x_mm"], channel_cfg["centers_y_mm"], waist
    )
    demo_norm = field_normalization_factor(
        demo_input.x_mm, demo_input.y_mm, demo_vector,
        channel_cfg["centers_x_mm"], channel_cfg["centers_y_mm"], waist
    )
    # POP's Beam Definition uses Peak Irradiance = 1 W/mm² for every run.
    # This known input scaling cancels the generated files' individual power
    # normalization for this non-overlapping Gaussian-channel configuration.
    basis_peak = float(np.max(np.abs(basis_input.ex) ** 2))
    demo_peak = float(np.max(np.abs(demo_input.ex) ** 2))
    input_compensation = (demo_norm / basis_norm) * np.sqrt(demo_peak / basis_peak)
    del basis_input

    raw_columns = []
    output_sampling = None
    for input_index in range(count):
        path = args.output_dir / f"basis_{input_index}_out.zbf"
        if not path.is_file():
            raise SystemExit(f"Missing POP output beam: {path}")
        beam = read_zbf(path)
        if not np.isclose(beam.wavelength_mm, wavelength, rtol=1e-6, atol=0.0):
            raise SystemExit(f"Wavelength in {path.name} ({beam.wavelength_mm:g} mm) does not match config ({wavelength:g} mm).")
        if output_sampling is None:
            output_sampling = beam
        # ZBF Ex is amplitude per pixel: divide by sqrt(pixel area) before
        # comparing fields saved on different POP grids.
        sampled = extract_channels(beam, positions, half_width_mm=half_width)
        sampled *= plane_reference_factor(beam, positions)
        raw_columns.append(sampled / np.sqrt(beam.dx_mm * beam.dy_mm))
    raw_matrix = np.column_stack(raw_columns)
    corrected = raw_matrix / envelope[:, None] if analysis_cfg.get("gaussian_envelope_correction", True) else raw_matrix.copy()

    if analysis_cfg.get("normalize_global_complex_scale", True):
        alpha = np.vdot(target, corrected) / np.vdot(target, target)
    else:
        alpha = 1.0 + 0.0j
    corrected_norm = float(np.linalg.norm(corrected))
    denominator = max(corrected_norm, np.finfo(float).tiny)

    def sign_shape_error(candidate: np.ndarray) -> float:
        # Normalized complex overlap scores matrix shape without fitting/applying
        # another calibration scalar to the measured transfer matrix.
        overlap = abs(np.vdot(candidate, corrected)) / (np.linalg.norm(candidate) * denominator)
        return float(np.sqrt(max(0.0, 1.0 - min(float(overlap), 1.0) ** 2)))

    primary_fit_error = sign_shape_error(target)
    alt_fit_error = sign_shape_error(alternative_target)
    if not np.isfinite(alpha) or abs(alpha) <= np.finfo(float).eps * denominator:
        favored = alternative_sign if alt_fit_error < primary_fit_error else sign
        raise SystemExit(
            f"Configured sign {sign:+d} has no stable global calibration (projection is zero or near zero). "
            f"Sign diagnostic: {sign:+d} error={primary_fit_error:.6g}, "
            f"{alternative_sign:+d} error={alt_fit_error:.6g}; diagnostic favors {favored:+d}. "
            "Set matrix.fourier_sign explicitly in config/project.yaml and rerun."
        )
    measured = corrected / alpha
    alt_error = alt_fit_error
    matrix_difference = measured - target
    target_nonzero = np.abs(target) > np.finfo(float).eps * max(float(np.max(np.abs(target))), 1.0)
    phase_delta_deg = np.angle(measured[target_nonzero] * np.conj(target[target_nonzero]), deg=True)
    magnitude_delta = np.abs(measured) - np.abs(target)
    frobenius_error = float(np.linalg.norm(matrix_difference) / np.linalg.norm(target))

    matrices_dir = args.results_dir / "matrices"
    figures_dir = args.results_dir / "figures"
    matrices_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)
    np.save(matrices_dir / "T_raw.npy", raw_matrix)
    np.save(matrices_dir / "T_measured.npy", measured)
    np.save(matrices_dir / "W_target.npy", target)
    save_complex_matrix_csv(matrices_dir / "T_raw.csv", raw_matrix)
    save_complex_matrix_csv(matrices_dir / "T_measured.csv", measured)
    save_complex_matrix_csv(matrices_dir / "W_target.csv", target)

    demo_path = args.output_dir / "demo_out.zbf"
    if not demo_path.is_file():
        raise SystemExit(f"Missing POP output beam: {demo_path}")
    demo_beam = read_zbf(demo_path)
    if not np.isclose(demo_beam.wavelength_mm, wavelength, rtol=1e-6, atol=0.0):
        raise SystemExit(f"Wavelength in {demo_path.name} ({demo_beam.wavelength_mm:g} mm) does not match config ({wavelength:g} mm).")
    demo_raw = extract_channels(demo_beam, positions, half_width_mm=half_width)
    demo_raw *= plane_reference_factor(demo_beam, positions)
    demo_raw /= np.sqrt(demo_beam.dx_mm * demo_beam.dy_mm)
    demo_corrected = demo_raw / envelope if analysis_cfg.get("gaussian_envelope_correction", True) else demo_raw.copy()

    demo_unaligned = demo_corrected / alpha * input_compensation
    demo_theory = target @ demo_vector
    # Separate POP runs may use different pilot spheres and arbitrary global
    # phase origins. After removing the known spherical phase, align only one
    # unit-magnitude global phase. No demo amplitude is fitted.
    demo_phase_offset = float(np.angle(np.vdot(demo_theory, demo_unaligned)))
    demo_measured = demo_unaligned * np.exp(-1j * demo_phase_offset)
    save_complex_vector_csv(matrices_dir / "demo_theory.csv", demo_theory)
    save_complex_vector_csv(matrices_dir / "demo_measured_unaligned.csv", demo_unaligned)
    save_complex_vector_csv(matrices_dir / "demo_measured.csv", demo_measured)

    demo_error = float(np.linalg.norm(demo_measured - demo_theory) / np.linalg.norm(demo_theory))
    demo_unaligned_error = float(np.linalg.norm(demo_unaligned - demo_theory) / np.linalg.norm(demo_theory))
    metrics = {
        "fourier_sign": sign,
        "global_complex_scale_real": float(np.real(alpha)),
        "global_complex_scale_imag": float(np.imag(alpha)),
        "normalized_frobenius_error": frobenius_error,
        "max_element_error": float(np.max(np.abs(matrix_difference))),
        "mean_element_error": float(np.mean(np.abs(matrix_difference))),
        "magnitude_rmse": float(np.sqrt(np.mean(magnitude_delta**2))),
        "phase_rmse_deg": float(np.sqrt(np.mean(phase_delta_deg**2))) if phase_delta_deg.size else 0.0,
        "alternative_sign": alternative_sign,
        "alternative_sign_error": alt_error,
        "best_matching_sign_diagnostic": sign if primary_fit_error <= alt_fit_error else alternative_sign,
        "demo_normalized_l2_error": demo_error,
        "demo_unaligned_complex_error": demo_unaligned_error,
        "demo_global_phase_alignment_deg": float(np.degrees(demo_phase_offset)),
        "demo_peak_irradiance_compensation": float(input_compensation),
        "gaussian_envelope_by_output": [float(value) for value in envelope],
        "expected_output_positions_mm": [float(value) for value in positions],
        "sampling": {
            "nx": int(output_sampling.nx),
            "ny": int(output_sampling.ny),
            "dx_mm": float(output_sampling.dx_mm),
            "dy_mm": float(output_sampling.dy_mm),
        },
        "input_sampling": {"nx": nx, "ny": ny, "dx_mm": dx, "dy_mm": dy},
        "demo_output_sampling": {
            "nx": int(demo_beam.nx),
            "ny": int(demo_beam.ny),
            "dx_mm": float(demo_beam.dx_mm),
            "dy_mm": float(demo_beam.dy_mm),
        },
    }
    with (args.results_dir / "metrics.json").open("w", encoding="utf-8") as stream:
        json.dump(metrics, stream, indent=2)
        stream.write("\n")

    plot_input_intensity(demo_input.ex, dx, dy, figures_dir / "01_input_field.png")
    plot_output_intensity(demo_beam, positions, figures_dir / "02_demo_output_intensity.png")
    plot_matrix_magnitude(target, figures_dir / "03_target_matrix_magnitude.png")
    plot_matrix_magnitude(measured, figures_dir / "04_measured_matrix_magnitude.png", measured=True)
    plot_matrix_phase(target, figures_dir / "05_target_matrix_phase.png")
    plot_matrix_phase(measured, figures_dir / "06_measured_matrix_phase.png", measured=True)
    plot_matrix_error(measured, target, figures_dir / "07_matrix_error.png")
    plot_demo_comparison(demo_theory, demo_measured, figures_dir / "08_demo_vector_comparison.png")

    print(f"Configured sign {sign}: normalized Frobenius error = {frobenius_error:.6g}")
    print(f"Alternative sign {alternative_sign}: scale-invariant complex-shape error = {alt_error:.6g}")
    print(f"Demo-vector normalized L2 error = {demo_error:.6g}")
    print(f"Saved matrices, metrics, and figures under {args.results_dir}")
    if frobenius_error > 0.10:
        print("WARNING: error exceeds 10% portfolio target; inspect sign, array orientation, output coordinates, POP sampling, clipping, and extraction window.")
    if primary_fit_error > alt_error:
        print(f"Sign diagnostic favors {alternative_sign:+d}; configured convention remains unchanged. Check Zemax field sign explicitly.")


if __name__ == "__main__":
    main()
