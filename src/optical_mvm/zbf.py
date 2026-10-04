"""Reader and writer for unpolarized version-1 Zemax Beam Files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import struct

import numpy as np


_HEADER = struct.Struct("<9i20d")
_UNITS_TO_MM = {0: 1.0, 1: 10.0, 2: 25.4, 3: 1000.0}


@dataclass
class ZBFBeam:
    nx: int
    ny: int
    dx_mm: float
    dy_mm: float
    wavelength_mm: float
    ex: np.ndarray
    x_mm: np.ndarray
    y_mm: np.ndarray
    pilot_zx_mm: float = 0.0
    pilot_rayleigh_x_mm: float = 0.0
    pilot_waist_x_mm: float = 0.0
    pilot_zy_mm: float = 0.0
    pilot_rayleigh_y_mm: float = 0.0
    pilot_waist_y_mm: float = 0.0


def plane_reference_factor(beam: ZBFBeam, x_mm: np.ndarray, y_mm: float = 0.0) -> np.ndarray:
    """Convert POP's spherical phase reference to a common planar reference.

    Beyond a pilot beam's Rayleigh range, POP references Ex to a sphere of
    radius equal to its signed distance from the pilot waist. In that case
    the stored phase contains +k*r^2/(2*z) relative to a plane.
    """
    x = np.asarray(x_mm, dtype=np.float64)
    phase = np.zeros_like(x)
    if beam.pilot_rayleigh_x_mm > 0 and abs(beam.pilot_zx_mm) > beam.pilot_rayleigh_x_mm:
        phase += np.pi * x**2 / (beam.wavelength_mm * beam.pilot_zx_mm)
    if beam.pilot_rayleigh_y_mm > 0 and abs(beam.pilot_zy_mm) > beam.pilot_rayleigh_y_mm:
        phase += np.pi * float(y_mm)**2 / (beam.wavelength_mm * beam.pilot_zy_mm)
    return np.exp(-1j * phase)


def _validate_ex(ex: np.ndarray, dx_mm: float, dy_mm: float) -> np.ndarray:
    field = np.asarray(ex, dtype=np.complex128)
    if field.ndim != 2:
        raise ValueError("Ex must be a 2D array with shape (ny, nx)")
    ny, nx = field.shape
    if nx < 1 or ny < 1 or (nx & (nx - 1)) or (ny & (ny - 1)):
        raise ValueError("Zemax beam sampling dimensions nx and ny must be powers of two")
    if not np.isfinite(field).all():
        raise ValueError("Ex contains non-finite values")
    if not np.isfinite(dx_mm) or not np.isfinite(dy_mm) or dx_mm <= 0 or dy_mm <= 0:
        raise ValueError("dx_mm and dy_mm must be finite positive values")
    return field


def _header_values(nx: int, ny: int, dx_mm: float, dy_mm: float, wavelength_mm: float) -> tuple[int | float, ...]:
    if not np.isfinite(wavelength_mm) or wavelength_mm <= 0:
        raise ValueError("wavelength_mm must be finite and positive")
    ints = (1, nx, ny, 0, 0, 0, 0, 0, 0)
    doubles = (
        dx_mm, dy_mm,
        0.0, 0.0, 0.0,
        0.0, 0.0, 0.0,
        wavelength_mm, 1.0,
        0.0, 0.0,
        *(0.0 for _ in range(8)),
    )
    return ints + doubles


def write_zbf(
    path: str | Path,
    ex: np.ndarray,
    dx_mm: float,
    dy_mm: float,
    wavelength_mm: float,
    *,
    text: bool = False,
) -> None:
    """Write unpolarized version-1 ZBF in binary (default) or documented text form.

    Array rows correspond to y and columns to x. Serialized samples advance x first.
    """
    field = _validate_ex(ex, dx_mm, dy_mm)
    ny, nx = field.shape
    values = _header_values(nx, ny, dx_mm, dy_mm, wavelength_mm)
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)

    if text:
        ints, doubles = values[:9], values[9:]
        with destination.open("w", encoding="ascii", newline="\n") as stream:
            stream.write("A\n")
            for value in ints:
                stream.write(f"{value}\n")
            for value in doubles:
                stream.write(f"{value:.17g}\n")
            for row in field:
                samples = np.empty((nx, 2), dtype=np.float64)
                samples[:, 0] = row.real
                samples[:, 1] = row.imag
                np.savetxt(stream, samples, fmt="%.17g")
        return

    interleaved = np.empty((ny, nx, 2), dtype="<f8")
    interleaved[:, :, 0] = field.real
    interleaved[:, :, 1] = field.imag
    with destination.open("wb") as stream:
        stream.write(_HEADER.pack(*values))
        stream.write(memoryview(interleaved).cast("B"))


def _make_beam(
    nx: int, ny: int, dx: float, dy: float, wavelength: float, ex: np.ndarray,
    pilot: tuple[float, float, float, float, float, float],
) -> ZBFBeam:
    x = (np.arange(nx, dtype=np.float64) - nx / 2.0) * dx
    y = (np.arange(ny, dtype=np.float64) - ny / 2.0) * dy
    return ZBFBeam(nx, ny, dx, dy, wavelength, np.asarray(ex, dtype=np.complex128).reshape(ny, nx), x, y, *pilot)


def _parse_header(tokens: list[str]) -> tuple[int, int, int, float, float, float, int, tuple[float, float, float, float, float, float]]:
    if len(tokens) < 29:
        raise ValueError("Truncated ZBF header")
    ints = [int(value) for value in tokens[:9]]
    doubles = [float(value) for value in tokens[9:29]]
    version, nx, ny, ispol, units = ints[:5]
    if version != 1:
        raise ValueError(f"Unsupported ZBF version {version}; only version 1 is supported")
    if nx <= 0 or ny <= 0:
        raise ValueError(f"Invalid ZBF dimensions: nx={nx}, ny={ny}")
    if ispol != 0:
        raise ValueError("Polarized ZBF beams are not supported; POP must save unpolarized Ex data")
    if units not in _UNITS_TO_MM:
        raise ValueError(f"Unsupported ZBF lens units code {units}")
    factor = _UNITS_TO_MM[units]
    dx, dy = doubles[0] * factor, doubles[1] * factor
    wavelength = doubles[8] * factor
    if not all(np.isfinite(value) and value > 0 for value in (dx, dy, wavelength)):
        raise ValueError("ZBF dx, dy, and wavelength must be finite and positive")
    pilot = tuple(value * factor for value in doubles[2:8])
    return nx, ny, ispol, dx, dy, wavelength, units, pilot


def _read_text(data: bytes) -> ZBFBeam:
    try:
        tokens = data.decode("ascii").split()
    except UnicodeDecodeError as exc:
        raise ValueError("ZBF text file is not ASCII") from exc
    if not tokens or tokens[0] != "A":
        raise ValueError("Text ZBF must begin with a single 'A' marker")
    nx, ny, _, dx, dy, wavelength, _, pilot = _parse_header(tokens[1:])
    expected = 29 + 2 * nx * ny
    if len(tokens) != expected + 1:
        raise ValueError(f"ZBF has {len(tokens) - 30} field values; expected {2 * nx * ny}")
    values = np.asarray(tokens[30:], dtype=np.float64)
    ex = values[0::2] + 1j * values[1::2]
    if not np.isfinite(ex).all():
        raise ValueError("ZBF field contains non-finite values")
    return _make_beam(nx, ny, dx, dy, wavelength, ex, pilot)


def _read_binary(data: bytes) -> ZBFBeam:
    if len(data) < _HEADER.size:
        raise ValueError("Truncated binary ZBF header")
    header = _HEADER.unpack_from(data)
    # Normalize binary header into the common token parser's fields.
    ints, doubles = header[:9], header[9:]
    version, nx, ny, ispol, units = ints[:5]
    if version != 1:
        raise ValueError(f"Unsupported ZBF version {version}; only version 1 is supported")
    if nx <= 0 or ny <= 0:
        raise ValueError(f"Invalid ZBF dimensions: nx={nx}, ny={ny}")
    if ispol != 0:
        raise ValueError("Polarized ZBF beams are not supported; POP must save unpolarized Ex data")
    if units not in _UNITS_TO_MM:
        raise ValueError(f"Unsupported ZBF lens units code {units}")
    expected_size = _HEADER.size + nx * ny * 2 * 8
    if len(data) != expected_size:
        raise ValueError(f"Binary ZBF size is {len(data)} bytes; expected {expected_size}")
    factor = _UNITS_TO_MM[units]
    dx, dy = doubles[0] * factor, doubles[1] * factor
    wavelength = doubles[8] * factor
    if not all(np.isfinite(value) and value > 0 for value in (dx, dy, wavelength)):
        raise ValueError("ZBF dx, dy, and wavelength must be finite and positive")
    values = np.frombuffer(data, dtype="<f8", offset=_HEADER.size)
    ex = values[0::2] + 1j * values[1::2]
    if not np.isfinite(ex).all():
        raise ValueError("ZBF field contains non-finite values")
    pilot = tuple(value * factor for value in doubles[2:8])
    return _make_beam(nx, ny, dx, dy, wavelength, ex, pilot)


def read_zbf(path: str | Path) -> ZBFBeam:
    """Read unpolarized version-1 binary or text ZBF file; return coordinates in mm."""
    source = Path(path)
    data = source.read_bytes()
    if data.startswith(b"A"):
        return _read_text(data)
    return _read_binary(data)
