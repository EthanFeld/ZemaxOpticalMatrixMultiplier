#!/usr/bin/env python3
"""Generate basis and demonstration fields as binary Zemax Beam Files."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optical_mvm import load_project_config
from optical_mvm.fields import make_input_field
from optical_mvm.zbf import write_zbf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "project.yaml")
    parser.add_argument("--output-dir", type=Path, default=ROOT / "data" / "input")
    args = parser.parse_args()

    config = load_project_config(args.config)
    sampling = config["sampling"]
    nx, ny = int(sampling["nx"]), int(sampling["ny"])
    if nx < 2 or ny < 2 or (nx & (nx - 1)) or (ny & (ny - 1)):
        raise SystemExit("Zemax ZBF nx and ny must be powers of two (for example 512, 1024, 2048).")
    dx = float(sampling["width_x_mm"]) / nx
    dy = float(sampling["width_y_mm"]) / ny
    x = (np.arange(nx, dtype=np.float64) - nx / 2.0) * dx
    y = (np.arange(ny, dtype=np.float64) - ny / 2.0) * dy

    channels = config["input_channels"]
    count = int(channels["count"])
    centers_x = np.asarray(channels["centers_x_mm"], dtype=np.float64)
    centers_y = np.asarray(channels["centers_y_mm"], dtype=np.float64)
    if centers_x.size != count or centers_y.size != count or count != int(config["matrix"]["size"]):
        raise SystemExit("Channel centers, input channel count, and matrix size must agree.")
    xx, yy = np.meshgrid(x, y, indexing="xy")
    waist = float(channels["gaussian_radius_mm"])
    wavelength = float(config["optics"]["wavelength_mm"])
    args.output_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    for channel in range(count):
        coeff = np.zeros(count, dtype=np.complex128)
        coeff[channel] = 1.0
        field = make_input_field(xx, yy, coeff, centers_x, centers_y, waist)
        filename = f"basis_{channel}.zbf"
        write_zbf(args.output_dir / filename, field, dx, dy, wavelength)
        vector = "[" + ",".join("1" if i == channel else "0" for i in range(count)) + "]"
        manifest_rows.append((filename, vector, f"basis_{channel}_out.zbf"))

    demo_real = np.asarray(config["demo_vector"]["real"], dtype=np.float64)
    demo_imag = np.asarray(config["demo_vector"].get("imag", np.zeros_like(demo_real)), dtype=np.float64)
    demo = demo_real + 1j * demo_imag
    if demo.size != count:
        raise SystemExit("Demo vector length must equal input channel count.")
    demo_field = make_input_field(xx, yy, demo, centers_x, centers_y, waist)
    write_zbf(args.output_dir / "demo.zbf", demo_field, dx, dy, wavelength)

    def fmt(value: complex) -> str:
        if value.imag == 0:
            return f"{value.real:g}"
        return f"{value.real:g}{value.imag:+g}j"

    vector_text = "[" + ",".join(fmt(value) for value in demo) + "]"
    manifest_rows.append(("demo.zbf", vector_text, "demo_out.zbf"))
    manifest = args.output_dir / "manifest.csv"
    with manifest.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(("input_file", "input_vector", "expected_output_file"))
        writer.writerows(manifest_rows)

    print(f"Wrote {count + 1} binary ZBF beams to {args.output_dir}")
    print(f"Sampling: {nx} x {ny}; dx={dx:g} mm; dy={dy:g} mm; wavelength={wavelength:g} mm")
    print(f"Manifest: {manifest}")


if __name__ == "__main__":
    main()
