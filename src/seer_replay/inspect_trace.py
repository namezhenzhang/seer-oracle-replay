"""List a raw attempt's files or copy one explicitly named member without bulk extraction."""

import argparse
import hashlib
import io
import json
import tarfile
from pathlib import Path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-dir", required=True, type=Path)
    p.add_argument("--pair", required=True, choices=["tmax", "deepswe"])
    p.add_argument("--id", required=True)
    p.add_argument("--member", help="Exact inner member name to copy")
    p.add_argument("--output", type=Path, help="Explicit destination for --member")
    a = p.parse_args()
    if bool(a.member) != bool(a.output):
        p.error("--member and --output must be supplied together")
    if a.output and a.output.exists():
        p.error("Output already exists; choose a new path")
    idx = json.loads((a.data_dir / "RAW_ARCHIVE_INDEX.json").read_text())
    found = [j for j in idx["archives"] if j["pair"] == a.pair and j["id"] == a.id]
    if len(found) != 1:
        p.error("Expected exactly one matching attempt")
    item = found[0]
    with tarfile.open(a.data_dir / item["hf_shard"], "r") as outer:
        stream = outer.extractfile(item["member"])
        if stream is None:
            raise RuntimeError("Archive member is not a file")
        payload = stream.read()
    if (
        len(payload) != item["bytes"]
        or hashlib.sha256(payload).hexdigest() != item["sha256"]
    ):
        raise RuntimeError("Original archive checksum mismatch")
    matched = False
    with tarfile.open(fileobj=io.BytesIO(payload), mode="r|gz") as inner:
        for member in inner:
            if not member.isfile():
                continue
            if a.member is None:
                print(f"{member.size}\t{member.name}")
            elif member.name == a.member:
                if matched:
                    raise RuntimeError("Duplicate requested member")
                matched = True
                with a.output.open("xb") as out:
                    src = inner.extractfile(member)
                    for chunk in iter(lambda: src.read(1024**2), b""):
                        out.write(chunk)
    if a.member and not matched:
        raise RuntimeError("Requested member not found")


if __name__ == "__main__":
    main()
