"""Analytical DFT and Fourier-plane coordinate helpers."""

from __future__ import annotations

import numpy as np


def centered_dft_matrix(n: int = 4, sign: int = -1) -> np.ndarray:
    """Return unitary centered n-point DFT matrix, with explicit +/- sign."""
    if not isinstance(n, (int, np.integer)) or n < 1:
        raise ValueError("n must be a positive integer")
    if sign not in (-1, 1):
        raise ValueError("sign must be -1 or +1")
    coordinates = np.arange(n, dtype=np.float64) - (n - 1) / 2.0
    matrix = np.exp(sign * 2j * np.pi / n * np.outer(coordinates, coordinates)) / np.sqrt(n)
    if not np.allclose(matrix.conj().T @ matrix, np.eye(n), rtol=0.0, atol=1e-12):
        raise ArithmeticError("Computed centered DFT matrix failed its unitary check")
    return matrix


def dft_frequencies(n: int, pitch_mm: float) -> np.ndarray:
    if n < 1 or not np.isfinite(pitch_mm) or pitch_mm <= 0:
        raise ValueError("n and pitch_mm must be positive")
    orders = np.arange(n, dtype=np.float64) - (n - 1) / 2.0
    return orders / (n * pitch_mm)


def focal_plane_positions(
    n: int,
    pitch_mm: float,
    wavelength_mm: float,
    focal_length_mm: float,
) -> np.ndarray:
    """Return centered DFT channel x coordinates at ideal lens back focal plane."""
    if not np.isfinite(wavelength_mm) or wavelength_mm <= 0:
        raise ValueError("wavelength_mm must be finite and positive")
    if not np.isfinite(focal_length_mm) or focal_length_mm <= 0:
        raise ValueError("focal_length_mm must be finite and positive")
    return wavelength_mm * focal_length_mm * dft_frequencies(n, pitch_mm)


def gaussian_fourier_envelope(frequencies_per_mm: np.ndarray, waist_mm: float) -> np.ndarray:
    if not np.isfinite(waist_mm) or waist_mm <= 0:
        raise ValueError("waist_mm must be finite and positive")
    frequencies = np.asarray(frequencies_per_mm, dtype=np.float64)
    return np.exp(-(np.pi * waist_mm * frequencies) ** 2)
