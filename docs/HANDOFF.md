# Team handoff

## Completed

- Teacher-only trace census: TMax 267 original attempts, DeepSWE 2,000.
- Exception-separated, fixed-duration admission replay with shared TP8 service accounting.
- Peak and reservation-hours comparisons, then resource-specific search subject to FIFO completion deadline.
- Independent final schedule validation and plots showing complete schedules by color.
- Portable CPU-only reproduction from compact HF data; raw archives retained for deeper extraction.

The latest canonical result is `reference-results/RESULT.json` in the pinned HF release, mirrored by `tests/reference_result.json`. The 100-attempt DeepSWE pilot and earlier shortest-time/lower-peak schedules are historical, not the latest objective-specific result.

## First steps for a teammate

1. Clone the GitHub repository and obtain access to the HF dataset.
2. Follow README quick start and run the published-metric check.
3. Read METHODS, especially reservation-vs-utilization, memory offload and fixed-latency assumptions.
4. Choose an experiment, write output to a new `runs/` directory, and preserve input HF commit, git commit, seed and parameters.
5. Compare complete schedules (`joint_schedules.csv`), not an unattainable combination of independently selected minima.

## Next experiments worth running

- Add strong reactive baselines (shortest job, aging, fair sharing, image affinity) and noisy duration predictions. Do not compare a learned policy only with weak FIFO.
- Model nonzero RAM offload/restore and image reload time, bandwidth, cache capacity and destination storage. Report how savings degrade.
- Measure real CPU utilization/RSS/GPU occupancy; current 89.4% DeepSWE CPU/RAM reduction is a quota-hours estimate, not an observed utilization reduction.
- Add an inference response-time model: reordered requests can change queueing/batching, so fixed durations need online validation.
- Optimize multiple resources jointly with explicit weights or a Pareto frontier and fixed quality/deadline; retain all full-schedule metrics.
- Collect additional workloads and real suspend/resume measurements only after validating the offline reproduction.

## Where to change code

`search.py` owns candidate priorities, admission constraints, objective evaluation and lower bounds. `refine_storage.py` explores grouping/simultaneous starts for repeated tasks. `validate.py` is deliberately separate from vectorized search accounting; keep this independent check when adding scheduling policies. `plot_schedules.py` uses validation output so each plotted color is a physically consistent replay schedule.

The current search retains fixed scientific assumptions and original deterministic RNG ordering. Refactor only with a frozen result comparison. Never turn unknown/infrastructure results into zero task scores, remove valid model mistakes, or rerun model calls merely to improve timing/accuracy statistics.

## Access and scope

The repositories are public by owner authorization. Grant GitHub write access to teammates who will commit changes; never share account tokens. The migration contains no conversation export. Research rationale is in PROJECT_SEER.md; the experiment state and caveats are captured here.

Notion report: https://app.notion.com/p/3ff419577f77809aa274eea270a5b461
