"""Audit archived result artifacts without rerunning or tuning the classifier.

Usage: python audit_records.py RELEASE_PACKAGE.zip MFPT_ARTIFACT.zip PADERBORN_ARTIFACT.zip
Outputs checked counts to stdout. Requires only the standard library.
"""
import collections
import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

def load(path, expected):
    payload = Path(path).read_bytes()
    assert hashlib.sha256(payload).hexdigest() == expected, path
    return zipfile.ZipFile(io.BytesIO(payload))

def drop(row, key):
    return {k:v for k,v in row.items() if k != key}

def outcome(truth, suggestion):
    if truth == "normal":
        return "healthy_false" if suggestion is not None else "healthy_withheld"
    return "correct" if suggestion == truth else "wrong" if suggestion is not None else "fault_withheld"

def run(package, mfpt, paderborn):
    with load(package, "9ff2b1f242abf44130c74a805124be647a07061e7bf4a83e785537dbffaab9bd") as z:
        with zipfile.ZipFile(io.BytesIO(z.read("aeris-0.2.0.zip"))) as source:
            def archived(name):
                return json.loads(source.read("aeris-0.2.0/research/evidence/" + name + ".json"))
            m = archived("mfpt_common_mode_summary")
            p = archived("paderborn_conditional_summary")
            base = archived("mfpt_transfer_summary")
    with load(mfpt, m["artifact_sha256"]) as z:
        M = json.loads(z.read("summary.json"))
    with load(paderborn, p["artifact_sha256"]) as z:
        P = json.loads(z.read("summary.json"))
    assert {k:v for k,v in M.items() if k != "scenarios"} == {k:m[k] for k in M if k != "scenarios"}
    assert [drop(s,"records") for s in M["scenarios"]] == m["scenarios"]
    assert drop(P,"records") == {k:p[k] for k in P if k != "records"}
    ids = {x["file_id"]:x["fault"] for x in base["records"]}
    assert len(ids) == 17
    per = collections.defaultdict(collections.Counter)
    totals = collections.defaultdict(collections.Counter)
    keys, validn = set(), 0
    for s in M["scenarios"]:
        c = s["assumed_common_bound"]
        key = (c,s["primary_speed_error"],s["primary_bias_bound"],s["secondary_mode"])
        assert key not in keys
        keys.add(key)
        assert len(s["records"]) == 17 and {x["file_id"]:x["truth"] for x in s["records"]} == ids
        a = collections.Counter()
        for x in s["records"]:
            g = x["guarded"]
            i = g["intersection"]
            reference = 1/(1+s["primary_speed_error"])
            contains = i is not None and i[0]-1e-12 <= reference <= i[1]+1e-12
            assert contains == x["reference_contained"]
            assert not s["declared_decomposition_valid"] or contains
            validn += s["declared_decomposition_valid"]
            accepted = g["suggestion"] is not None
            assert not accepted or i is not None
            o = outcome(x["truth"],g["suggestion"])
            a[o] += 1
            per[x["file_id"]][(c,o)] += 1
            a["contained"] += contains
            a["conflicts"] += i is None
            a["differential"] += g["status"] == "common_mode_conflict"
            a["false_compatible"] += i is not None and not contains
            a["accepted_outside"] += accepted and not contains
        for k,v in [("correct","correct_accepted"),("wrong","incorrect_accepted"),("fault_withheld","abstained"),("healthy_false","normal_incorrect_accepted")]:
            assert a[k] == s["common_guard"][v]
        for k,v in [("contained","reference_contained"),("conflicts","conflicts"),("differential","differential_conflicts"),("false_compatible","nonempty_without_reference"),("accepted_outside","accepted_without_reference")]:
            assert a[k] == s[v]
        totals[c].update(a)
    assert len(keys) == 120 and validn == 1224
    assert len(P["records"]) == 68 and len({x["filename"] for x in P["records"]}) == 68
    sp, pc, pa = (collections.defaultdict(collections.Counter) for _ in range(3))
    agree = both = 0
    hashes = set()
    for x in P["records"]:
        assert x["sha256"] not in hashes
        hashes.add(x["sha256"])
        a,b = x["nominal"]["suggestion"],x["stored_time"]["suggestion"]
        agree += a == b
        both += a is not None and a == b
        for mode in ("nominal","stored_time"):
            o = outcome(x["truth"],x[mode]["suggestion"])
            sp[x["specimen"]][(mode,o)] += 1
            pc[x["condition"]][(mode,o)] += 1
            pa[mode][o] += 1
            if not x["structural_pilot"]:
                pa[mode+"_nonpilot"][o] += 1
    assert agree == P["agreement"] and both == P["both_accept_same"]
    def check(a, reported):
        for k,v in [("correct","correct_accepted"),("wrong","incorrect_accepted"),("fault_withheld","fault_abstained"),("healthy_false","normal_incorrect_accepted")]:
            assert a[k] == reported[v]
        assert a["correct"]+a["wrong"]+a["fault_withheld"] == reported["fault_records"]
        assert a["healthy_false"]+a["healthy_withheld"] == reported["normal_records"]
    for mode in ("nominal","stored_time"):
        check(pa[mode],P["overall"][mode])
        check(pa[mode+"_nonpilot"],P["nonpilot"][mode])
        for condition,a in pc.items():
            check(collections.Counter({o:n for (h,o),n in a.items() if h==mode}),P["by_condition"][condition][mode])
        for specimen in P["specimen_summaries"]:
            a=sp[specimen["specimen"]]
            check(collections.Counter({o:n for (h,o),n in a.items() if h==mode}),specimen["metrics"][mode])
    return {"mfpt_comparisons":len(keys)*17,"valid_decomposition_contained":validn,
            "mfpt_totals":totals,
            "mfpt_per_fault_record":{i:[a[c,"correct"] for c in (0,.01,.05)] for i,a in per.items() if ids[i]!="normal"},
            "paderborn_comparisons":len(P["records"]),"agreement":agree,"both_accept_same":both,
            "paderborn_totals":pa,
            "paderborn_specimens":{i:{o:n for (h,o),n in a.items() if h=="nominal"} for i,a in sp.items()},
            "paderborn_conditions":{i:{o:n for (h,o),n in a.items() if h=="nominal"} for i,a in pc.items()},
            "relative_waveform_l2_range":[min(x["preprocessing"]["relative_waveform_l2_difference"] for x in P["records"]),max(x["preprocessing"]["relative_waveform_l2_difference"] for x in P["records"])]}

if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    print(json.dumps(run(*sys.argv[1:]),indent=2,sort_keys=True))
