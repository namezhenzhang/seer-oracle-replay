from pathlib import Path
import json, heapq, csv, time
import numpy as np
from .search import union
from .paths import paths

P, D = paths()
R = json.loads((D / "deepswe-result.json").read_text())
rows = sorted(
    [json.loads(p.read_text()) for p in (P / "deepswe-full/rows").glob("*.json")],
    key=lambda r: (r["start"], r["id"]),
)
rows = [r for r in rows if r["status"] == "generation_complete"]
dur = np.array([r["duration"] for r in rows])
n = len(rows)
groups = {}
for i, r in enumerate(rows):
    groups.setdefault(r["task"], []).append(i)
gs = list(groups.values())
gmax = np.array([max(dur[g]) for g in gs])
inv = json.loads((P / "deepswe-full/IMAGE_INVENTORY.json").read_text())
bi = {}
for i, r in enumerate(rows):
    for b in inv["images"][r["task"]]:
        bi.setdefault(b, []).append(i)
blobs = [(np.array(v, dtype=int), inv["sizes"][b] / 1024**3) for b, v in bi.items()]
gbytes = np.array(
    [sum(inv["sizes"][b] for b in inv["images"][rows[g[0]]["task"]]) for g in gs]
)
rng = np.random.default_rng(20261021)
deadline = R["deadline_minutes"] * 60
best = R["best"]["storage"]["resource_hours"]
count = feasible = 0
t0 = time.monotonic()
history = []
for j in range(360):
    fraction = [0, 0.25, 0.5, 0.75, 1][j % 5]
    amp = [0, 0.1, 0.3, 0.7, 1.5, 3][(j // 5) % 6]
    order = np.argsort(-gmax * np.exp(rng.normal(0, amp, len(gs))))
    ranks = (
        np.argsort(-gbytes * np.exp(rng.normal(0, 0.7, len(gs))))
        if j % 2
        else rng.permutation(len(gs))
    )
    gang = set(ranks[: int(fraction * len(gs))])
    h = [(0.0, l) for l in range(32)]
    starts = np.empty(n)
    for gi in order:
        g = sorted(gs[gi], key=lambda i: -dur[i])
        if gi in gang:
            slots = [heapq.heappop(h) for _ in g]
            a = max(t for t, l in slots)
            for i, (t, l) in zip(g, slots):
                starts[i] = a
                heapq.heappush(h, (a + dur[i], l))
        else:
            for i in g:
                a, l = heapq.heappop(h)
                starts[i] = a
                heapq.heappush(h, (a + dur[i], l))
    end = starts + dur
    count += 1
    if end.max() > deadline + 1e-6:
        continue
    feasible += 1
    sh = sum(size * union(starts[ix], end[ix]) for ix, size in blobs) / 3600
    if sh < best - 1e-9:
        best = sh
        minutes = float(end.max() / 60)
        R["best"]["storage"].update(
            resource_hours=sh,
            minutes=minutes,
            saving_percent=100 * (1 - sh / R["baseline"]["storage"]["hours"]),
            above_lower_bound_percent=100 * (sh / R["lower_bounds"]["storage"] - 1),
            label=f"partial simultaneous task-group starts {j}, fraction {fraction}",
            candidate=R["candidates"] + count,
        )
        with (D / "deepswe-storage-schedule.csv").open("w") as f:
            w = csv.writer(f)
            w.writerow(["id", "task", "start", "end"])
            w.writerows(
                (r["id"], r["task"], starts[i], end[i]) for i, r in enumerate(rows)
            )
        history.append(
            {"candidate": j, "hours": sh, "minutes": minutes, "fraction": fraction}
        )
R["candidates"] += count
R["feasible_candidates"] += feasible
R["elapsed_seconds"] += time.monotonic() - t0
R["additional_search_seed"] = 20261021
(D / "deepswe-result.json").write_text(json.dumps(R, indent=2))
(D / "storage-refinement.json").write_text(
    json.dumps(
        {"candidates": count, "feasible": feasible, "improvements": history}, indent=2
    )
)
allr = json.loads((D / "RESULT.json").read_text())
allr["deepswe"] = R
(D / "RESULT.json").write_text(json.dumps(allr, indent=2))
print(
    json.dumps(
        {"best": R["best"]["storage"], "count": count, "feasible": feasible}, indent=2
    )
)
