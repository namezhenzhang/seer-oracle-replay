from pathlib import Path
import json, csv, collections, hashlib
from .paths import paths

P, D = paths()


def union(xs):
    spans = []
    for a, b in sorted(xs):
        if spans and a <= spans[-1][1]:
            spans[-1][1] = max(b, spans[-1][1])
        else:
            spans.append([a, b])
    return sum(b - a for a, b in spans)


def peak(xs):
    events = collections.defaultdict(float)
    for a, b, v in xs:
        events[a] += v
        events[b] -= v
    cur = ans = 0
    for t, d in sorted(events.items()):
        cur += d
        ans = max(cur, ans)
        assert cur >= -1e-6
    assert abs(cur) < 1e-6
    return ans


out = []
for pair in ["tmax", "deepswe"]:
    result = json.loads((D / (pair + "-result.json")).read_text())
    if pair == "tmax":
        rows = json.loads((P / "unified-oracle/tmax-intervals.json").read_text())
    else:
        rows = [
            json.loads(p.read_text()) for p in (P / "deepswe-full/rows").glob("*.json")
        ]
        rows = [r for r in rows if r["status"] == "generation_complete"]
    records = {r["id"]: r for r in rows}
    inv = (
        json.loads((P / "deepswe-full/IMAGE_INVENTORY.json").read_text())
        if pair == "deepswe"
        else None
    )
    for obj, reported in result["best"].items():
        path = D / f"{pair}-{obj}-schedule.csv"
        sched = list(csv.DictReader(path.open()))
        assert len(sched) == len(records) and {r["id"] for r in sched} == set(records)
        cpu = []
        ram = []
        env = []
        req = []
        cache = collections.defaultdict(list)
        ch = mh = 0
        finish = 0
        for s in sched:
            r = records[s["id"]]
            a = float(s["start"])
            b = float(s["end"])
            assert a >= 0 and abs(b - a - r["duration"]) < 1e-6
            finish = max(finish, b)
            assert s["task"] == r["task"]
            env.append((a, b, 1))
            cpu.append((a, b, r["cpu"]))
            ram.append((a, b, r["memory_gib"]))
            iv = r["model_intervals"]
            last = 0
            for x, y in iv:
                assert 0 <= x <= y <= r["duration"] + 1e-5 and x >= last - 1e-5
                last = y
                req.append((a + x, a + y))
            residual = r["duration"] - union(iv)
            ch += r["cpu"] * residual / 3600
            mh += r["memory_gib"] * residual / 3600
            if inv:
                for blob in inv["images"][r["task"]]:
                    cache[blob].append((a, b))
        vals = {
            "cpu": ch,
            "memory": mh,
            "gpu": 8 * union(req) / 3600,
            "storage": (
                sum(
                    inv["sizes"][k] / 1024**3 * union(xs) / 3600
                    for k, xs in cache.items()
                )
                if inv
                else None
            ),
        }
        caps = result["caps"]
        peaks = {"env": peak(env), "cpu": peak(cpu), "memory": peak(ram)}
        assert (
            peaks["env"] <= caps["concurrent_trials"]
            and peaks["cpu"] <= caps["cpu_whole_trial"] + 1e-6
            and peaks["memory"] <= caps["memory_whole_trial_gib"] + 1e-6
        )
        assert (
            finish / 60 <= result["deadline_minutes"] + 1e-6
            and abs(finish / 60 - reported["minutes"]) < 1e-6
        )
        assert abs(vals[obj] - reported["resource_hours"]) < 1e-6
        assert reported["resource_hours"] >= reported["lower_bound"] - 1e-6
        out.append(
            {
                "pair": pair,
                "objective": obj,
                "trials": len(sched),
                "minutes": finish / 60,
                "resource_hours": vals[obj],
                "all_resource_hours": vals,
                "whole_trial_peaks": peaks,
                "schedule_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "verified": True,
            }
        )
(D / "VALIDATION.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))
