#!/usr/bin/env python3
"""Print useful dimensions and field diagnostics for a ZBF beam."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optical_mvm.plotting import plot_output_intensity
from optical_mvm.zbf import read_zbf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path)
    parser.add_argument("--preview", type=Path, help="Optional path for a PNG intensity preview")
    args = parser.parse_args()

    beam = read_zbf(args.file)
    print(f"filename: {args.file}")
    print(f"nx: {beam.nx}")
    print(f"ny: {beam.ny}")
    print(f"dx: {beam.dx_mm:.12g} mm")
    print(f"dy: {beam.dy_mm:.12g} mm")
    print(f"physical width: {beam.nx * beam.dx_mm:.12g} mm x {beam.ny * beam.dy_mm:.12g} mm")
    print(f"wavelength: {beam.wavelength_mm:.12g} mm")
    print(f"peak |E|: {np.max(np.abs(beam.ex)):.12g}")
    print(f"sum |E|^2: {np.sum(np.abs(beam.ex) ** 2):.12g}")
    print(
        "coordinate range: "
        f"x=[{beam.x_mm[0]:.12g}, {beam.x_mm[-1]:.12g}] mm; "
        f"y=[{beam.y_mm[0]:.12g}, {beam.y_mm[-1]:.12g}] mm"
    )
    if args.preview:
        plot_output_intensity(
            beam, np.asarray([], dtype=np.float64), args.preview,
            title=f"ZBF intensity preview: {args.file.name}",
        )
        print(f"intensity preview: {args.preview}")


if __name__ == "__main__":
    main()
