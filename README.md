# Seer Oracle Replay

Reproduce the Project Seer teacher-only resource study, then extend the scheduling experiments without the original GPU cluster. This repository contains the analysis code and handoff; **namezz/seer-agent-traces** contains immutable inputs and reference results.

## Quick start

Python 3.10 or newer; CPU only. No CUDA, Docker, Slurm, model download, or new inference is needed for offline replay. The published run takes roughly 1–2 minutes on the original CPU host; runtime varies by machine.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
# Public dataset; no HF login is required.
# Replace COMMIT with the full revision in DATA_RELEASE.json:
seer-download --revision COMMIT --dest data
seer-replay reproduce --data-dir data/replay --output-dir runs/reproduction
python tests/check_reproduction.py runs/reproduction
```

The replay writes `RESULT.json`, independently checked schedules and `VALIDATION.json`, two workload-specific PNG/PDF/SVG plots, and `joint_schedules.csv`. **The same color within a plot means the same complete schedule.** The reproduction test compares all 28 published resource/time/bound/reduction values.

To examine full model/tool logs, add `--with-raw` to the download command. The compact layer is 3.79 MiB compressed (approximately 11 MB unpacked); the original compressed teacher archives are approximately 10.34 GB. See `docs/DATA.md` for contents and exclusions.

## What was evaluated?

| Workload | Teacher | Scope | Included |
|---|---|---|---|
| Terminal-Bench 2.1 | TMax-27B, 27B | 89 tasks × 3 seeds | 253 normal trials; 14 execution exceptions separate |
| SWE-bench Verified | DeepSWE-Preview, 32B | 500 tasks × 4 attempts | 1,998 generations; 2 infrastructure failures separate |

DeepSWE includes generation only, excluding downstream official grading. TMax includes the recorded trial lifecycle including verifier/teardown. Model mistakes and ordinary step/token limits remain included. Do not directly compare the two lifecycle definitions as if they were identical.

## What the numbers mean

These are **conditional offline replay estimates of reservations**, not measured utilization or deployed speedups. Per-task durations and internal model-request intervals remain fixed. CPU/RAM are sandbox quotas; waiting sandboxes are assumed to pause/offload with zero cost. GPU-hours count an 8-GPU service while any model request is pending. Storage covers only shared compressed OCI image blobs, not total disk or RAM-offload storage.

Each objective is optimized separately, subject to completion no later than FIFO and unchanged resource caps. CPU/RAM attain analytical minima in this model. GPU/cache results are the best feasible schedules found, not globally proven minima. See `docs/METHODS.md` and `docs/HANDOFF.md` before extending the results.

## Results retained for handoff

| Workload / objective | Resource-hours | Completion (min) | FIFO deadline (min) |
|---|---:|---:|---:|
| TMax CPU | 19.8786 core-h | 110.3300 | 132.8094 |
| TMax RAM | 54.0641 GiB-h | 110.3300 | 132.8094 |
| TMax GPU | 14.3611 GPU-h | 129.2053 | 132.8094 |
| DeepSWE CPU | 148.0393 core-h | 1,311.4622 | 1,352.9339 |
| DeepSWE RAM | 592.1572 GiB-h | 1,311.4622 | 1,352.9339 |
| DeepSWE GPU | 173.2963 GPU-h | 1,311.8427 | 1,352.9339 |
| DeepSWE image cache | 180.1541 GiB-h | 1,313.4180 | 1,352.9339 |

CPU/RAM minima coexist with every selected oracle schedule. TMax's GPU schedule achieves all three measured minima together. DeepSWE's GPU and cache best-found values belong to different schedules; read `joint_schedules.csv` for simultaneously attained values.

## Repository map

- `src/seer_replay/search.py`: admission scheduling, objective accounting, seeded order search.
- `refine_storage.py`: additional shared-image task grouping search.
- `validate.py`: independent scalar interval-union and capacity/deadline validation.
- `plot_schedules.py`: complete-schedule comparisons, independent workload axes.
- `download.py`: pinned HF download and SHA256 verification.
- `provenance/original-analysis/`: original scripts, retained for audit; not portable entrypoints.
- `docs/`: workload configuration, schema, assumptions, next experiments, team handoff.

No credentials, unrelated Codex conversation, model weights, Docker images, or Python environments are part of this project. No new benchmark/training jobs are started by these commands.
