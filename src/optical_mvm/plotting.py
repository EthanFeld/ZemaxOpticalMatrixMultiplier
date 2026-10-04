"""Publication-quality diagnostic plots for the optical multiplier."""

from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

from .zbf import ZBFBeam


def _save(fig: plt.Figure, path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=220, bbox_inches="tight")
    plt.close(fig)


def _heatmap(
    data: np.ndarray,
    title: str,
    colorbar_label: str,
    path: Path,
    *,
    cmap: str = "viridis",
    fmt: str = "{:.3f}",
    vmin: float | None = None,
    vmax: float | None = None,
) -> None:
    fig, ax = plt.subplots(figsize=(6.0, 5.2), constrained_layout=True)
    image = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, origin="upper")
    ax.set(title=title, xlabel="Input channel n", ylabel="Output channel m")
    ax.set_xticks(range(data.shape[1]), labels=[str(i) for i in range(data.shape[1])])
    ax.set_yticks(range(data.shape[0]), labels=[str(i) for i in range(data.shape[0])])
    midpoint = (float(np.nanmax(data)) + float(np.nanmin(data))) / 2
    for row in range(data.shape[0]):
        for col in range(data.shape[1]):
            color = "white" if data[row, col] < midpoint else "black"
            ax.text(col, row, fmt.format(data[row, col]), ha="center", va="center", color=color, fontsize=9)
    fig.colorbar(image, ax=ax, label=colorbar_label)
    _save(fig, path)


def plot_input_intensity(field: np.ndarray, dx_mm: float, dy_mm: float, path: Path) -> None:
    ny, nx = field.shape
    extent = (-nx * dx_mm / 2, nx * dx_mm / 2, -ny * dy_mm / 2, ny * dy_mm / 2)
    fig, ax = plt.subplots(figsize=(7.2, 5.5), constrained_layout=True)
    image = ax.imshow(np.abs(field) ** 2, extent=extent, origin="lower", cmap="magma")
    ax.set(title="Normalized coherent input field", xlabel="x (mm)", ylabel="y (mm)", aspect="equal")
    fig.colorbar(image, ax=ax, label=r"$|E_{input}|^2$ (normalized)")
    _save(fig, path)


def plot_output_intensity(
    beam: ZBFBeam,
    sample_positions_x_mm: np.ndarray,
    path: Path,
    *,
    title: str = "Zemax POP output intensity",
) -> None:
    extent = (
        beam.x_mm[0] - beam.dx_mm / 2,
        beam.x_mm[-1] + beam.dx_mm / 2,
        beam.y_mm[0] - beam.dy_mm / 2,
        beam.y_mm[-1] + beam.dy_mm / 2,
    )
    fig, ax = plt.subplots(figsize=(8.0, 5.2), constrained_layout=True)
    intensity = np.abs(beam.ex) ** 2 / (beam.dx_mm * beam.dy_mm)
    image = ax.imshow(intensity, extent=extent, origin="lower", cmap="magma", aspect="auto")
    for xpos in sample_positions_x_mm:
        ax.axvline(xpos, color="cyan", linestyle="--", linewidth=0.9, alpha=0.9)
    ax.set(title=title, xlabel="x (mm)", ylabel="y (mm)")
    fig.colorbar(image, ax=ax, label="Irradiance (W/mm²)")
    _save(fig, path)


def plot_matrix_magnitude(target: np.ndarray, path: Path, measured: bool = False) -> None:
    title = "Measured transfer matrix magnitude" if measured else "Target DFT matrix magnitude"
    _heatmap(np.abs(target), title, "Magnitude", path, vmin=0.0)


def plot_matrix_phase(matrix: np.ndarray, path: Path, measured: bool = False) -> None:
    title = "Measured transfer matrix phase" if measured else "Target DFT matrix phase"
    _heatmap(np.angle(matrix, deg=True), title, "Phase (degrees)", path, cmap="twilight", fmt="{:.0f}", vmin=-180, vmax=180)


def plot_matrix_error(measured: np.ndarray, target: np.ndarray, path: Path) -> None:
    _heatmap(np.abs(measured - target), "Absolute complex matrix error", "Absolute error", path, cmap="viridis", fmt="{:.3f}", vmin=0.0)


def plot_demo_comparison(theory: np.ndarray, measured: np.ndarray, path: Path) -> None:
    indices = np.arange(theory.size)
    width = 0.36
    fig, axes = plt.subplots(2, 1, figsize=(8.0, 7.0), sharex=True, constrained_layout=True)
    axes[0].bar(indices - width / 2, np.abs(theory), width, label="Theory", color="#3b6fb6")
    axes[0].bar(indices + width / 2, np.abs(measured), width, label="Zemax", color="#e08a37")
    axes[0].set_ylabel("Magnitude")
    axes[0].set_title("Demo-vector validation (global phase aligned)")
    axes[0].legend()
    axes[0].grid(axis="y", alpha=0.25)
    axes[1].bar(indices - width / 2, np.angle(theory, deg=True), width, label="Theory", color="#3b6fb6")
    axes[1].bar(indices + width / 2, np.angle(measured, deg=True), width, label="Zemax", color="#e08a37")
    axes[1].set_ylabel("Phase (degrees)")
    axes[1].set_xlabel("Output channel m")
    axes[1].set_xticks(indices)
    axes[1].grid(axis="y", alpha=0.25)
    _save(fig, path)
