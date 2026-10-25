from pathlib import Path
import json, heapq, csv, time, hashlib
import numpy as np
from .paths import paths

P, D = paths()
rng = np.random.default_rng(20261020)


def union(starts, ends):
    if len(starts) == 0:
        return 0.0
    ix = np.argsort(starts, kind="stable")
    a = np.asarray(starts)[ix]
    b = np.asarray(ends)[ix]
    prior = np.r_[-np.inf, np.maximum.accumulate(b)[:-1]]
    return float(np.maximum(0, b - np.maximum(a, prior)).sum())


def run(pair):
    t0 = time.monotonic()
    if pair == "tmax":
        details = {
            r["id"]: r
            for r in json.loads((P / "unified-oracle/tmax-intervals.json").read_text())
        }
        old = list(csv.DictReader((P / "normal-teachers/schedules.csv").open()))
        bs = [r for r in old if r["pair"] == "tmax" and r["scenario"] == "fifo"]
        rows = [details[r["id"]] for r in bs]
        baseline = json.loads((P / "unified-oracle/RESULT.json").read_text())["tmax"][
            "fifo"
        ]
        C = 16
        cc = 27
        mm = 66
    else:
        rows = sorted(
            [
                json.loads(p.read_text())
                for p in (P / "deepswe-full/rows").glob("*.json")
            ],
            key=lambda r: (r["start"], r["id"]),
        )
        rows = [r for r in rows if r["status"] == "generation_complete"]
        baseline = json.loads((P / "deepswe-full/RESULT.json").read_text())["fifo"]
        C = 32
        cc = 64
        mm = 256
    n = len(rows)
    dur = np.array([r["duration"] for r in rows])
    cpu = np.array([r["cpu"] for r in rows])
    mem = np.array([r["memory_gib"] for r in rows])
    deadline = baseline["minutes"] * 60
    mi = np.array(
        [i for i, r in enumerate(rows) for a, b in r["model_intervals"]], dtype=int
    )
    ma = np.array([a for r in rows for a, b in r["model_intervals"]])
    mb = np.array([b for r in rows for a, b in r["model_intervals"]])
    ms = np.bincount(mi, weights=mb - ma, minlength=n)
    groups = {}
    for i, r in enumerate(rows):
        groups.setdefault(r["task"], []).append(i)
    gs = list(groups.values())
    gmax = np.array([max(dur[g]) for g in gs])
    gmean = np.array([np.mean(dur[g]) for g in gs])
    gmodel = np.array([max(ms[g]) for g in gs])
    blobs = []
    if pair == "deepswe":
        inv = json.loads((P / "deepswe-full/IMAGE_INVENTORY.json").read_text())
        bi = {}
        for i, r in enumerate(rows):
            for b in inv["images"][r["task"]]:
                bi.setdefault(b, []).append(i)
        blobs = [
            (np.array(v, dtype=int), inv["sizes"][b] / 1024**3) for b, v in bi.items()
        ]
    lower = {
        "cpu": float(np.sum((dur - ms) * cpu) / 3600),
        "memory": float(np.sum((dur - ms) * mem) / 3600),
        "gpu": 8 * max(float(ms.sum() / C), float(ms.max())) / 3600,
        "storage": (
            sum(
                size * max(float(dur[ix].max()), float(dur[ix].sum() / C))
                for ix, size in blobs
            )
            / 3600
            if blobs
            else None
        ),
    }

    def schedule(order):
        starts = np.empty(n)
        lanes = []
        if pair == "deepswe":
            heap = [(0.0, j) for j in range(C)]
            for i in order:
                a, l = heapq.heappop(heap)
                starts[i] = a
                heapq.heappush(heap, (a + dur[i], l))
        else:
            pending = list(map(int, order))
            running = []
            now = 0.0
            uc = um = 0.0
            while pending or running:
                while running and running[0][0] <= now + 1e-8:
                    _, i = heapq.heappop(running)
                    uc -= cpu[i]
                    um -= mem[i]
                while len(running) < C:
                    pos = next(
                        (
                            j
                            for j, i in enumerate(pending)
                            if uc + cpu[i] <= cc + 1e-8 and um + mem[i] <= mm + 1e-8
                        ),
                        None,
                    )
                    if pos is None:
                        break
                    i = pending.pop(pos)
                    starts[i] = now
                    heapq.heappush(running, (now + dur[i], i))
                    uc += cpu[i]
                    um += mem[i]
                if running:
                    now = running[0][0]
                elif pending:
                    raise ValueError("Infeasible")
        return starts

    def evaluate(starts):
        end = starts + dur
        finish = float(end.max())
        if finish > deadline + 1e-6:
            return None
        gh = 8 * union(starts[mi] + ma, starts[mi] + mb) / 3600
        sh = (
            sum(size * union(starts[ix], end[ix]) for ix, size in blobs) / 3600
            if blobs
            else None
        )
        return {
            "minutes": finish / 60,
            "cpu": lower["cpu"],
            "memory": lower["memory"],
            "gpu": gh,
            "storage": sh,
        }

    best = {}
    count = 0
    feasible = 0
    history = []

    def consider(order, label):
        nonlocal count, feasible
        order = np.array(order, dtype=int)
        assert np.array_equal(np.sort(order), np.arange(n))
        count += 1
        starts = schedule(order)
        m = evaluate(starts)
        if m is None:
            return None
        feasible += 1
        for key in ["time", "gpu"] + (["storage"] if blobs else []):
            target = m["minutes"] if key == "time" else m[key]
            prior = best.get(key)
            old = (
                np.inf
                if prior is None
                else (
                    prior["metrics"]["minutes"]
                    if key == "time"
                    else prior["metrics"][key]
                )
            )
            if target < old - 1e-9 or (
                abs(target - old) < 1e-9 and m["minutes"] < prior["metrics"]["minutes"]
            ):
                best[key] = {
                    "order": order.copy(),
                    "starts": starts.copy(),
                    "metrics": m,
                    "label": label,
                    "candidate": count,
                }
                history.append(
                    {
                        "candidate": count,
                        "objective": key,
                        "value": target,
                        "minutes": m["minutes"],
                        "label": label,
                    }
                )
        return m

    def progress(stage):
        p = {
            "pair": pair,
            "stage": stage,
            "evaluated": count,
            "feasible": feasible,
            "elapsed_seconds": time.monotonic() - t0,
            "best": {k: v["metrics"] for k, v in best.items()},
        }
        (D / (pair + "-progress.json")).write_text(json.dumps(p, indent=2))
        print(json.dumps(p), flush=True)

    # Invariant CPU/RAM minima are attained by every feasible phase-reclaim schedule.
    consider(np.arange(n), "historical FIFO with phase reclamation")
    for key, v in [
        ("LPT", dur),
        ("model time", ms),
        ("CPU-time", dur * cpu),
        ("RAM-time", dur * mem),
        ("model fraction", ms / dur),
    ]:
        consider(np.argsort(-v, kind="stable"), key)
    # Grouping repeated attempts increases overlap of shared image blobs.
    for w in [gmax, gmean, gmodel]:
        for rev in [False, True]:
            go = np.argsort(-w if not rev else w, kind="stable")
            for within in ["long", "short"]:
                consider(
                    [
                        i
                        for g in go
                        for i in sorted(
                            gs[g], key=lambda i: dur[i], reverse=within == "long"
                        )
                    ],
                    f"group priority {within} {rev}",
                )
    for j in range(320):
        amp = [0.03, 0.1, 0.3, 0.6, 1.2, 2.5][j % 6]
        if j % 2:
            w = [gmax, gmean, gmodel][j % 3] * np.exp(rng.normal(0, amp, len(gs)))
            go = np.argsort(-w)
            order = [i for g in go for i in sorted(gs[g], key=lambda i: -dur[i])]
        else:
            order = np.argsort(-dur * np.exp(rng.normal(0, amp, n)))
        consider(order, f"randomized duration/group priority {j}")
        if j % 80 == 79:
            progress("priority-search")
    # Objective-specific local order search. Resource eligibility and time bound checked on every candidate.
    for objective in ["time", "gpu"] + (["storage"] if blobs else []):
        for j in range(240):
            order = best[objective]["order"].copy()
            kind = j % 3
            if kind == 0:
                a, b = rng.choice(n, 2, replace=False)
                order[a], order[b] = order[b], order[a]
            elif kind == 1:
                a, b = sorted(rng.choice(n, 2, replace=False))
                v = order[a]
                order[a:b] = order[a + 1 : b + 1]
                order[b] = v
            else:
                # Bring all attempts of a selected task together at its earliest position.
                g = gs[int(rng.integers(len(gs)))]
                mask = np.isin(order, g)
                pos = int(np.flatnonzero(mask)[0])
                group = order[mask]
                rest = order[~mask]
                order = np.r_[rest[:pos], group, rest[pos:]]
            consider(order, f"{objective} local search {j}")
            if j % 80 == 79:
                progress(objective + "-local")
    # Save reproducible per-attempt schedules for independent validation.
    result = {
        "pair": pair,
        "attempts": n,
        "deadline_minutes": deadline / 60,
        "caps": {
            "concurrent_trials": C,
            "cpu_whole_trial": cc,
            "memory_whole_trial_gib": mm,
            "gpu": 8,
        },
        "baseline": baseline,
        "lower_bounds": lower,
        "candidates": count,
        "feasible_candidates": feasible,
        "search_seed": 20261020,
        "elapsed_seconds": time.monotonic() - t0,
        "best": {},
    }
    for objective in ["cpu", "memory", "gpu"] + (["storage"] if blobs else []):
        b = best["time" if objective in ["cpu", "memory"] else objective]
        m = b["metrics"]
        val = m[objective]
        result["best"][objective] = {
            "resource_hours": val,
            "minutes": m["minutes"],
            "saving_percent": 100 * (1 - val / baseline[objective]["hours"]),
            "lower_bound": lower[objective],
            "above_lower_bound_percent": 100 * (val / lower[objective] - 1),
            "optimality": (
                "proven within fixed-duration phase-reclaim model"
                if objective in ["cpu", "memory"]
                else "best feasible found; not proven global minimum"
            ),
            "label": b["label"],
            "candidate": b["candidate"],
        }
        with (D / f"{pair}-{objective}-schedule.csv").open("w") as f:
            w = csv.writer(f)
            w.writerow(["id", "task", "start", "end"])
            for i, r in enumerate(rows):
                w.writerow(
                    [r["id"], r["task"], b["starts"][i], b["starts"][i] + dur[i]]
                )
    result["best_time"] = best["time"]["metrics"]
    (D / (pair + "-result.json")).write_text(json.dumps(result, indent=2))
    (D / (pair + "-history.json")).write_text(json.dumps(history, indent=2))
    progress("complete")
    return result


if __name__ == "__main__":
    results = {p: run(p) for p in ["tmax", "deepswe"]}
    (D / "RESULT.json").write_text(json.dumps(results, indent=2))
