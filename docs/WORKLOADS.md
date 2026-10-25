# Historical Teacher evaluation configuration

| Setting | TMax | DeepSWE |
|---|---|---|
| Teacher | allenai/tmax-27b, 27B | agentica-org/DeepSWE-Preview, 32B |
| Model revision | 4acf9950f27dc231cb48b9cfe57cacc4e97875a9 | 4887205c533cd162baac7ba758159cfc3304cf94 |
| Benchmark | Terminal-Bench 2.1; 89 tasks × seeds 42,43,44 | SWE-bench Verified; 500 tasks × four attempts |
| Harness | Harbor + TMax Vanillux2Agent | R2E-Gym; edit_non_fn_calling scaffold |
| Serving | vLLM 0.19.1, BF16, TP8 | vLLM 0.10.2, FP16, TP8 |
| Context | 65,536 tokens | 65,536 tokens |
| Output budget | 16,384 tokens/request | Remaining server context window |
| Sampling | T=0.7, top-p=0.95 | T=1.0, top-p=0.95, top-k=20; thinking enabled |
| Agent steps | 64; 64 format errors | 40 advisory; 100 absolute; no history condensation |
| Tool timeout | 120 seconds | 90 seconds |
| Other timeouts | Native task agent budgets 600–12,000 seconds, mostly 900 | Per LLM request 7,200 seconds; trajectory 50,000 seconds |
| Sandbox | Per task: 1–4 cores, 2–8 GiB | 2 cores, 8 GiB |
| Inference concurrency | 16 active trials | Up to 32 attempts per shared service |
| Lifecycle accounted | Full recorded trial, including verifier/teardown | Generation only, no downstream official grading |

DeepSWE attempt seed: `42 + trial_index * 500 + canonical_sorted_instance_index`.

The FP16 experiment contract overrides the older `controlled-protocol.json` BF16 / 16-attempt settings. The four-attempt Teacher data are the actual artifacts used here. These are local historical evaluation configurations, not a claim of byte-identical reproduction of every official reported score.

Before new online experiments, pin harness/model/tokenizer/task revisions and record both configured and effective limits. Measure CPU usage, RSS, GPU activity and storage I/O separately from quota reservations; record pause/offload/restore overhead and verify task success is unchanged.
