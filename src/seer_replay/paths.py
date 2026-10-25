"""Portable roots; no original cluster directory is required."""

import argparse
from pathlib import Path


def paths():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--data-dir", type=Path, required=True, help="HF dataset replay/ directory"
    )
    p.add_argument("--output-dir", type=Path, required=True)
    a = p.parse_args()
    data = a.data_dir.resolve()
    out = a.output_dir.resolve()
    if not data.is_dir():
        p.error("Data directory does not exist: " + str(data))
    if out == data or data in out.parents:
        p.error("Outputs must be outside the immutable data directory")
    out.mkdir(parents=True, exist_ok=True)
    return data, out
