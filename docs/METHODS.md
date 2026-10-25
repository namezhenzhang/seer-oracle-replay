# Accounting model and optimization

The baseline is an offline FIFO admission replay in historical start order with all tasks ready at time zero. It is not a measurement of the original cluster's full wall-clock run. DeepSWE's original dispatch used eight task groups with four attempts each; the replay uses 32 individual attempt slots.

## Fixed trace model

Each attempt retains its recorded duration and model-request intervals relative to start. Scheduling changes only attempt admission, including grouping repetitions; it does not accelerate model calls, change generated answers, rerun failures or change scoring. The raw model-request time can include queueing, transport and server processing; it is not a measurement of GPU kernel busy time. Changing real concurrency could change these durations, which is deliberately outside this first replay model.

| Workload | Concurrent attempts | CPU cap | Sandbox RAM cap | Shared inference service |
|---|---:|---:|---:|---:|
| TMax | 16 | 27 cores | 66 GiB | 8 GPUs |
| DeepSWE | 32 | 64 cores | 256 GiB | 8 GPUs |

Every candidate must complete no later than the FIFO deadline. Both the full-trial quota caps and concurrency are enforced, even though the ideal accounting releases CPU/RAM during model waits. No additional capacity is assumed.

## Resource-hours

- CPU: sum `quota_cores * seconds_outside_model_requests / 3600`.
- RAM: sum `quota_GiB * seconds_outside_model_requests / 3600`.
- GPU: `8 * length(union(all_scheduled_model_request_intervals)) / 3600`. Concurrent requests count once. All eight GPUs are reserved whenever any request is pending and released as a group otherwise.
- Cache: sum over unique compressed image blob digests of `blob_GiB * length(union(lifetimes_of_tasks_using_blob)) / 3600`.

FIFO holds CPU/RAM for whole attempts, GPUs for the whole batch, and image blobs from first use to batch end. Ideal accounting assumes zero pause/resume, RAM offload/restore, model state transfer, image eviction/reload and restart costs. Pausing Docker alone does not free RAM. Background sandbox processes would need safe suspension. Model-server/harness host CPU/RAM, GPU HBM, expanded image layers, writable files, outputs and RAM-offload destination storage are not included.

## Optimality

CPU/RAM totals are invariant under reordering in this fixed-duration phase model. Their achieved values equal analytical lower bounds; we pick the fastest found tied schedule for display. GPU and cache objectives use seeded scheduling search, not an exact solver. Candidate priority orders, random duration perturbations, repeated-task grouping, local swaps/moves, and partial simultaneous group starts are checked. Reproduce both workload searches in their recorded order to preserve RNG evolution.

GPU lower bound: `8 * max(sum(request_seconds)/concurrency, max(per_task_request_seconds)) / 3600`.

Cache lower bound per blob: `blob_GiB * max(longest_associated_task_duration, sum(associated_task_durations)/concurrency) / 3600`, then sum over blobs. These are bounds, not attained schedules and not necessarily jointly attainable.

Different resource minima need not coexist. `joint_schedules.csv` reports full schedules whose values can coexist. CPU/RAM minima coexist with every selected ideal schedule. DeepSWE's GPU and cache best-found values do not coexist in a selected schedule; this does not prove a joint optimum impossible.

## Timing and cohort audit

TMax normal cohort: 253/267 original Teacher trials, excluding 14 execution exceptions; all normal wrong answers remain. The 14 are explicitly retained in exception metadata and full raw archives.

DeepSWE: all 2,000 original Teacher attempts audited, 1,998 generation-complete and two infrastructure failures. Request start times come from archived request-start file mtimes; elapsed request durations come from captured monotonic timers. Generation lifetime runs from identity-file mtime to `completed_utc`. Intervals were clipped/merged during extraction and clipping information retained. One `llm_query_error` termination remains among generation-complete records rather than being silently excluded. The full 500-task census supersedes the earlier 100-attempt pilot.

Original archives are tied to SHA256, byte count and immutable GCS object generation. HF raw shards contain original archive bytes unchanged. Every selected final schedule is independently validated for exact coverage, fixed durations, interval ordering, nonnegative accounting, quotas and deadline.
