"""Run the same deterministic pipeline that produced the published report."""

import argparse, subprocess, sys
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=["reproduce", "validate", "plot"])
    p.add_argument("--data-dir", required=True, type=Path)
    p.add_argument("--output-dir", required=True, type=Path)
    a = p.parse_args()
    stages = {
        "reproduce": ["search", "refine_storage", "validate", "plot_schedules"],
        "validate": ["validate"],
        "plot": ["plot_schedules"],
    }[a.command]
    for name in stages:
        print("Running " + name, flush=True)
        subprocess.run(
            [
                sys.executable,
                "-m",
                "seer_replay." + name,
                "--data-dir",
                str(a.data_dir),
                "--output-dir",
                str(a.output_dir),
            ],
            check=True,
        )


if __name__ == "__main__":
    main()
