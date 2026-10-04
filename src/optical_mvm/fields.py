"""Complex input-channel field construction."""

from __future__ import annotations

import numpy as np


def _coordinate_grid(x_mm: np.ndarray, y_mm: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    x = np.asarray(x_mm, dtype=np.float64)
    y = np.asarray(y_mm, dtype=np.float64)
    if x.ndim == 1 and y.ndim == 1:
        return np.meshgrid(x, y, indexing="xy")
    try:
        return np.broadcast_arrays(x, y)
    except ValueError as exc:
        raise ValueError("x_mm and y_mm must be coordinate vectors or broadcast-compatible arrays") from exc


def _pixel_area(x: np.ndarray, y: np.ndarray) -> float:
    if x.ndim != 2 or y.ndim != 2 or x.shape != y.shape or min(x.shape) < 2:
        return 1.0
    dx = float(np.median(np.abs(np.diff(x[0, :]))))
    dy = float(np.median(np.abs(np.diff(y[:, 0]))))
    if dx <= 0 or dy <= 0:
        raise ValueError("Coordinate arrays must have nonzero sample spacing")
    return dx * dy


def field_normalization_factor(
    x_mm: np.ndarray,
    y_mm: np.ndarray,
    coefficients: np.ndarray,
    centers_x_mm: np.ndarray,
    centers_y_mm: np.ndarray,
    waist_mm: float,
) -> float:
    """Return L2 field norm before normalization, including sampled pixel area."""
    x, y = _coordinate_grid(x_mm, y_mm)
    coeff = np.asarray(coefficients, dtype=np.complex128).reshape(-1)
    cx = np.asarray(centers_x_mm, dtype=np.float64).reshape(-1)
    cy = np.asarray(centers_y_mm, dtype=np.float64).reshape(-1)
    if coeff.size == 0 or coeff.size != cx.size or coeff.size != cy.size:
        raise ValueError("coefficients and center arrays must have equal nonzero length")
    if not np.isfinite(coeff).all() or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Coordinates and coefficients must be finite")
    if not np.isfinite(waist_mm) or waist_mm <= 0:
        raise ValueError("waist_mm must be finite and positive")
    field = np.zeros_like(x, dtype=np.complex128)
    for amplitude, center_x, center_y in zip(coeff, cx, cy):
        radius_sq = (x - center_x) ** 2 + (y - center_y) ** 2
        field += amplitude * np.exp(-radius_sq / waist_mm**2)
    power = float(np.sum(np.abs(field) ** 2) * _pixel_area(x, y))
    if not np.isfinite(power) or power <= 0:
        raise ValueError("Input field has zero or invalid sampled power")
    return float(np.sqrt(power))


def make_input_field(
    x_mm: np.ndarray,
    y_mm: np.ndarray,
    coefficients: np.ndarray,
    centers_x_mm: np.ndarray,
    centers_y_mm: np.ndarray,
    waist_mm: float,
) -> np.ndarray:
    """Build Gaussian channels and normalize total sampled optical power to one."""
    x, y = _coordinate_grid(x_mm, y_mm)
    coeff = np.asarray(coefficients, dtype=np.complex128).reshape(-1)
    cx = np.asarray(centers_x_mm, dtype=np.float64).reshape(-1)
    cy = np.asarray(centers_y_mm, dtype=np.float64).reshape(-1)
    if coeff.size == 0 or coeff.size != cx.size or coeff.size != cy.size:
        raise ValueError("coefficients and center arrays must have equal nonzero length")
    if not np.isfinite(coeff).all() or not np.isfinite(x).all() or not np.isfinite(y).all():
        raise ValueError("Coordinates and coefficients must be finite")
    if not np.isfinite(waist_mm) or waist_mm <= 0:
        raise ValueError("waist_mm must be finite and positive")
    field = np.zeros_like(x, dtype=np.complex128)
    for amplitude, center_x, center_y in zip(coeff, cx, cy):
        radius_sq = (x - center_x) ** 2 + (y - center_y) ** 2
        field += amplitude * np.exp(-radius_sq / waist_mm**2)
    norm = np.sqrt(float(np.sum(np.abs(field) ** 2) * _pixel_area(x, y)))
    if not np.isfinite(norm) or norm <= 0:
        raise ValueError("Input field has zero or invalid sampled power")
    return field / norm
