"""Python tools for the 4x4 coherent optical matrix multiplier."""

from pathlib import Path

import yaml


def load_project_config(path: str | Path | None = None) -> dict:
    """Load project YAML; default path is repository config/project.yaml."""
    config_path = Path(path) if path is not None else Path(__file__).resolve().parents[2] / "config" / "project.yaml"
    with config_path.open("r", encoding="utf-8") as stream:
        config = yaml.safe_load(stream)
    if not isinstance(config, dict):
        raise ValueError(f"Invalid project configuration: {config_path}")
    return config
