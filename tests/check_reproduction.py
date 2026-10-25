"""Compare actual full-data reproduction against frozen published metrics."""

import argparse, json, math
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument("output", type=Path)
a = p.parse_args()
ref = json.loads(Path(__file__).with_name("reference_result.json").read_text())
got = json.loads((a.output / "RESULT.json").read_text())
checks = 0
for pair, r in ref.items():
    for objective, b in r["best"].items():
        x = got[pair]["best"][objective]
        for k in ["resource_hours", "minutes", "lower_bound", "saving_percent"]:
            assert math.isclose(x[k], b[k], rel_tol=1e-10, abs_tol=1e-7), (
                pair,
                objective,
                k,
                x[k],
                b[k],
            )
            checks += 1
        assert x["minutes"] <= r["deadline_minutes"] + 1e-6
validation = json.loads((a.output / "VALIDATION.json").read_text())
assert len(validation) == 7 and all(x["verified"] for x in validation)
print(f"PASS: {checks} published metrics; all 7 schedules independently validated.")
