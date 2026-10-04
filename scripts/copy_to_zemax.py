#!/usr/bin/env python3
"""Copy generated input beams to OpticStudio's POP/BEAMFILES folder."""

from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from optical_mvm import load_project_config


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pop-dir", required=True, type=Path, help="Existing OpticStudio POP or POP/BEAMFILES directory")
    parser.add_argument("--input-dir", type=Path, default=ROOT / "data" / "input")
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "project.yaml")
    args = parser.parse_args()

    if not args.pop_dir.is_dir():
        raise SystemExit(f"POP directory does not exist or is not a directory: {args.pop_dir}")
    beam_dir = args.pop_dir if args.pop_dir.name.casefold() == "beamfiles" else args.pop_dir / "BEAMFILES"
    if not beam_dir.is_dir():
        raise SystemExit(f"OpticStudio input-beam folder does not exist: {beam_dir}")
    config = load_project_config(args.config)
    filenames = [f"basis_{i}.zbf" for i in range(int(config["input_channels"]["count"]))] + ["demo.zbf"]
    missing = [name for name in filenames if not (args.input_dir / name).is_file()]
    if missing:
        raise SystemExit(f"Missing generated input beam(s) in {args.input_dir}: {', '.join(missing)}")
    for filename in filenames:
        destination = shutil.copy2(args.input_dir / filename, beam_dir / filename)
        print(f"Copied {filename} -> {destination}")


if __name__ == "__main__":
    main()
