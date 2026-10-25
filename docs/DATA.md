# Data layout and provenance

The HF dataset is `namezz/seer-agent-traces`. Use the immutable revision in `DATA_RELEASE.json`; do not use a moving `main` for reported experiments.

## Compact layer (default download)

- `replay/unified-oracle/tmax-intervals.json`: 253 included Teacher attempts and relative model-wait intervals.
- `replay/deepswe-full/rows/`: 2,000 compact records, including two infrastructure failures. Generation-complete records alone enter replay.
- `replay/deepswe-full/IMAGE_INVENTORY.json`: task-to-image-blob mapping and deduplicated compressed byte sizes.
- `replay/normal-teachers/schedules.csv`: historical reference schedules; only its TMax FIFO ordering is an input to the current search. Its old DeepSWE pilot rows are not used.
- `replay/normal-teachers/tmax-exceptions.*`: excluded original attempts and reasons.
- `replay/joint/TASK_RESOURCES.json`: all 89 native TMax task resource/budget definitions.
- `provenance/`: frozen evaluation contracts and relevant historical harness sources.
- `reference-results/`: final search output, independent validations, schedules, tables and figures.
- `MANIFEST.json`: SHA256 and size of every dataset payload file.

Some provenance filenames/fields retain original cluster paths. They are historical identifiers, not required filesystem locations. `replay/unified-oracle/RESULT.json` also contains the obsolete 100-attempt DeepSWE pilot; executable modules read its TMax branch only. Full DeepSWE inputs and reference results live under the full-data paths above.

## Raw layer (optional download)

`raw/teacher-archives-*.tar` bundles 2,267 original compressed archives: TMax Teacher 267 and DeepSWE Teacher 2,000. `RAW_ARCHIVE_INDEX.json` maps each attempt to a shard/member, original SHA256, byte size and immutable source generation. An archive may contain prompts, model responses, token IDs, trajectories, tool output, rewards or error diagnostics; exact members differ by harness.

Download with `seer-download --revision COMMIT --dest data --with-raw`. No Google credentials or original cluster access are needed once the HF copy is verified. To inspect an archive, use Python's `tarfile` streaming reader or `tar -xOf SHARD MEMBER`; do not blindly extract untrusted archive paths into a shared directory.

## Core record schema

- `id`, `task`: attempt and benchmark task identity.
- `duration`: seconds for the retained lifecycle.
- `cpu`, `memory_gib`: sandbox reservation quota.
- `model_intervals`: sorted, disjoint `[start_seconds, end_seconds]` intervals relative to attempt start.
- DeepSWE additionally records status, exit reason, call counts, seed, missing-end indices, clipping seconds and archive hashes.

Raw archives are evidence; compact intervals are the replay input. Changes to extraction must version the dataset and preserve provenance, not overwrite archived outcomes.

## Excluded from migration

Base model weights, Docker images/layers themselves, virtual environments, CUDA builds, Slurm allocations, unrelated SFT/SP training data/checkpoints, unrelated conversation history and account credentials. Image metadata is included; image payloads are public/upstream-downloadable and not needed for replay.

See `docs/WORKLOADS.md` to collect new traces. A fresh online run needs its own models, serving endpoint, task environments and resource telemetry; the offline package is not an already deployed agent runtime.

## Inspect a raw attempt without unsafe extraction

```bash
python -m seer_replay.inspect_trace --data-dir data --pair deepswe --id astropy__astropy-12907--00
# Copy one explicitly named member after inspecting its exact name:
python -m seer_replay.inspect_trace --data-dir data --pair deepswe --id astropy__astropy-12907--00 --member EXACT_MEMBER_NAME --output saved-member.json
```

The inspector checks the original archive SHA256 before reading it and never bulk-extracts member paths. Request full raw data first with `--with-raw`.
