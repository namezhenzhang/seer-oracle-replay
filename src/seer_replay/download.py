"""Download compact replay inputs at an explicit HF commit; raw traces are opt-in."""

import argparse, json, hashlib
from pathlib import Path
from huggingface_hub import snapshot_download


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", default="namezz/seer-agent-traces")
    p.add_argument(
        "--revision",
        required=True,
        help="Pinned full HF commit SHA from DATA_RELEASE.json",
    )
    p.add_argument("--dest", type=Path, required=True)
    p.add_argument("--with-raw", action="store_true")
    a = p.parse_args()
    patterns = [
        "README.md",
        "MANIFEST.json",
        "RAW_ARCHIVE_INDEX.json",
        "replay/**",
        "provenance/**",
        "reference-results/**",
    ]
    if a.with_raw:
        patterns += ["raw/**"]
    snapshot_download(
        a.repo,
        repo_type="dataset",
        revision=a.revision,
        local_dir=str(a.dest),
        allow_patterns=patterns,
    )
    manifest = json.loads((a.dest / "MANIFEST.json").read_text())
    if a.with_raw and not manifest.get("raw_available", True):
        raise RuntimeError("Raw archives are not available at this revision; compact replay is complete.")
    checked = 0
    for item in manifest["files"]:
        path = a.dest / item["path"]
        if not a.with_raw and item["path"].startswith("raw/"):
            continue
        if not path.is_file():
            raise RuntimeError("Missing " + item["path"])
        h = hashlib.sha256()
        with path.open("rb") as f:
            for b in iter(lambda: f.read(1024**2), b""):
                h.update(b)
        if path.stat().st_size != item["bytes"] or h.hexdigest() != item["sha256"]:
            raise RuntimeError("Checksum mismatch: " + item["path"])
        checked += 1
    print(f"Verified {checked} files at {a.revision}")


if __name__ == "__main__":
    main()
