"""Complex field sampling at theoretical output-channel coordinates."""

from __future__ import annotations

import numpy as np

from .zbf import ZBFBeam


def extract_channels(
    beam: ZBFBeam,
    positions_x_mm: np.ndarray,
    y_mm: float = 0.0,
    half_width_mm: float = 0.005,
) -> np.ndarray:
    """Return complex mean Ex in square windows around each requested coordinate."""
    positions = np.asarray(positions_x_mm, dtype=np.float64).reshape(-1)
    if positions.size == 0 or not np.isfinite(positions).all() or not np.isfinite(y_mm):
        raise ValueError("Output coordinates must be a nonempty finite array")
    if not np.isfinite(half_width_mm) or half_width_mm <= 0:
        raise ValueError("half_width_mm must be finite and positive")
    outputs = np.empty(positions.size, dtype=np.complex128)
    for index, x_center in enumerate(positions):
        col_mask = np.abs(beam.x_mm - x_center) <= half_width_mm
        row_mask = np.abs(beam.y_mm - y_mm) <= half_width_mm
        if not np.any(col_mask) or not np.any(row_mask):
            raise ValueError(
                f"No output samples fall inside extraction window at x={x_center:.9g} mm, "
                f"y={y_mm:.9g} mm; check POP sampling or increase extraction_half_width_um"
            )
        region = beam.ex[np.ix_(row_mask, col_mask)]
        if region.size == 0:
            raise ValueError(f"Empty extraction region at x={x_center:.9g} mm")
        outputs[index] = np.mean(region, dtype=np.complex128)
    return outputs
