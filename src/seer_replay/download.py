"""Download one verified compact bundle; full teacher archives are opt-in."""

import argparse
import hashlib
import json
import tarfile
from pathlib import Path, PurePosixPath
from huggingface_hub import hf_hub_download


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for data in iter(lambda: f.read(1024**2), b""):
            h.update(data)
    return h.hexdigest()


def unpack(bundle, dest, max_bytes):
    total = 0
    seen = set()
    with tarfile.open(bundle, "r:gz") as archive:
        for member in archive:
            name = PurePosixPath(member.name)
            if (
                not member.isfile()
                or name.is_absolute()
                or ".." in name.parts
                or "\\" in member.name
                or member.name in seen
            ):
                raise RuntimeError("Unsafe or duplicate bundle member: " + member.name)
            seen.add(member.name)
            total += member.size
            if total > max_bytes or len(seen) > 10000:
                raise RuntimeError("Bundle exceeds declared limits")
            target = dest.joinpath(*name.parts)
            if not target.resolve().is_relative_to(dest.resolve()):
                raise RuntimeError("Bundle path escapes destination")
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_name(target.name + ".download-partial")
            with temporary.open("wb") as out:
                src = archive.extractfile(member)
                for chunk in iter(lambda: src.read(1024**2), b""):
                    out.write(chunk)
            temporary.replace(target)
    return len(seen)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo", default="namezz/seer-agent-traces")
    p.add_argument(
        "--revision", required=True, help="Full HF commit SHA in DATA_RELEASE.json"
    )
    p.add_argument("--dest", type=Path, required=True)
    p.add_argument("--with-raw", action="store_true")
    a = p.parse_args()
    a.dest.mkdir(parents=True, exist_ok=True)
    cache = a.dest / ".hf-cache"

    def fetch(name):
        return Path(
            hf_hub_download(
                a.repo, name, repo_type="dataset", revision=a.revision, cache_dir=cache
            )
        )

    pointer = json.loads(fetch("REPLAY_BUNDLE.json").read_text())
    bundle = fetch(pointer["path"])
    if bundle.stat().st_size != pointer["bytes"] or digest(bundle) != pointer["sha256"]:
        raise RuntimeError("Compact bundle checksum mismatch")
    unpack(bundle, a.dest, pointer["uncompressed_bytes"])
    manifest = json.loads((a.dest / "MANIFEST.json").read_text())
    checked = 0
    for item in manifest["files"]:
        raw = item["path"].startswith("raw/")
        if raw and not a.with_raw:
            continue
        path = fetch(item["path"]) if raw else a.dest / item["path"]
        if (
            not path.is_file()
            or path.stat().st_size != item["bytes"]
            or digest(path) != item["sha256"]
        ):
            raise RuntimeError("Checksum mismatch: " + item["path"])
        if raw:
            target = a.dest / item["path"]
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.exists():
                try:
                    target.hardlink_to(path)
                except OSError:
                    import shutil

                    shutil.copy2(path, target)
            elif digest(target) != item["sha256"]:
                raise RuntimeError("Existing raw shard differs: " + item["path"])
        checked += 1
    print(f"Verified {checked} payload files at {a.revision}; raw={a.with_raw}")


if __name__ == "__main__":
    main()
