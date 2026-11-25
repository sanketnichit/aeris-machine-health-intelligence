"""Read-only MFPT measurement reliability workspace using registered summaries."""
import json

import pandas as pd
import streamlit as st


def measurement_rows(report, error):
    return pd.DataFrame([
        {"Width (%)": 100*s["declared_uncertainty"],
         "Reference contained": s["reference_in_interval"],
         "Correct": s["refined"]["correct_accepted"],
         "Incorrect": s["refined"]["incorrect_accepted"],
         "Withheld": s["refined"]["abstained"],
         "Normal false suggestions": s["refined"]["normal_incorrect_accepted"]}
        for s in report["scenarios"] if s["declared_speed_error"] == error
    ]).sort_values("Width (%)").reset_index(drop=True)


def bias_rows(report):
    rows = []
    for bound in sorted({s["assumed_bias_bound"] for s in report["scenarios"]}):
        selected = [s for s in report["scenarios"] if s["assumed_bias_bound"] == bound]
        rows.append({"Bias bound (%)": 100*bound,
                     "Fault assessments": sum(s["composed"]["fault_records"] for s in selected),
                     "Correct": sum(s["composed"]["correct_accepted"] for s in selected),
                     "Incorrect": sum(s["composed"]["incorrect_accepted"] for s in selected),
                     "Withheld": sum(s["composed"]["abstained"] for s in selected),
                     "Normal false suggestions": sum(s["composed"]["normal_incorrect_accepted"] for s in selected)})
    return pd.DataFrame(rows)


def possibility_rows(report):
    return pd.DataFrame([
        {"Speed error (%)": 100*s["declared_speed_error"],
         "Width (%)": 100*s["declared_uncertainty"],
         "Reference contained": s["reference_in_interval"],
         **{f"Size {i}": s["outer_set_sizes"][str(i)] for i in range(4)},
         "Fault truth included": s["fault_truth_in_outer_set"],
         "Fault assessments": s["fault_records"],
         "Normal nonempty sets": s["normal_nonempty_outer_set"]}
        for s in report["scenarios"]
    ])


def witness_counts(report):
    groups = {}
    for s in report["scenarios"]:
        for group, counts in s["counterexample_counts"].items():
            target = groups.setdefault(group, {})
            for key, count in counts.items():
                target[key] = target.get(key, 0) + count
    return groups


def fusion_rows(report):
    rows = []
    for mode in sorted({s["secondary_mode"] for s in report["scenarios"]}):
        selected = [s for s in report["scenarios"] if s["secondary_mode"] == mode]
        rows.append({"Secondary mode": mode,
                     "Fault assessments": sum(s["fused"]["fault_records"] for s in selected),
                     "Primary correct": sum(s["primary"]["correct_accepted"] for s in selected),
                     "Fused correct": sum(s["fused"]["correct_accepted"] for s in selected),
                     "Fused incorrect": sum(s["fused"]["incorrect_accepted"] for s in selected),
                     "Conflicts": sum(s["conflicts"] for s in selected),
                     "Compatible outside reference": sum(s["nonempty_without_reference"] for s in selected),
                     "Accepted outside reference": sum(s["accepted_without_reference"] for s in selected)})
    return pd.DataFrame(rows)


def common_mode_rows(report):
    rows = []
    for bound in sorted({s["assumed_common_bound"] for s in report["scenarios"]}):
        selected = [s for s in report["scenarios"] if s["assumed_common_bound"] == bound]
        rows.append({"Common bound (%)": 100*bound,
                     "Correct": sum(s["common_guard"]["correct_accepted"] for s in selected),
                     "Incorrect": sum(s["common_guard"]["incorrect_accepted"] for s in selected),
                     "Withheld": sum(s["common_guard"]["abstained"] for s in selected),
                     "Compatible outside reference": sum(s["nonempty_without_reference"] for s in selected),
                     "Accepted outside reference": sum(s["accepted_without_reference"] for s in selected),
                     "Differential conflicts": sum(s["differential_conflicts"] for s in selected)})
    return pd.DataFrame(rows)


def evidence_link(report, filename):
    st.caption(report["scope"])
    st.markdown(f"[Execution evidence]({report['run_url']}) | revision `{report['revision']}`")
    st.download_button("Download registered evidence", json.dumps(report, indent=2),
                       filename, "application/json", key=f"download_{filename}")


def render_measurement_reliability(read_report):
    st.subheader("MFPT diagnostic measurement reliability")
    st.warning("The same 17 physical recordings recur across these retrospective synthetic metadata scenarios. Counts are not independent field samples. No safe sensor specification is established.")
    choice = st.radio("Audit", ["Stability refinement", "Counterexamples", "Diagnostic possibilities",
                                "Measurement width", "Systematic bias", "Two-channel fusion", "Common-mode error"], key="mfpt_measurement_audit")
    if choice == "Stability refinement":
        name = "mfpt_breakpoint_summary.json"
        report = read_report(name)
        rows = pd.DataFrame([{"Speed error (%)": 100*s["declared_speed_error"],
                              "Width (%)": 100*s["declared_uncertainty"],
                              "Point correct": s["point"]["correct_accepted"],
                              "Global correct": s["global_bound"]["correct_accepted"],
                              "Refined correct": s["refined"]["correct_accepted"],
                              "Refined incorrect": s["refined"]["incorrect_accepted"],
                              "Recovered correct": s["recovered_correct"]}
                             for s in report["scenarios"]])
        st.metric("Recovered correct suggestions", int(rows["Recovered correct"].sum()))
        st.dataframe(rows, hide_index=True)
        st.caption("Closed-cell refinement is a sufficient numerical stability check, not formal interval arithmetic.")
    elif choice == "Counterexamples":
        name = "mfpt_counterexample_summary.json"
        report = read_report(name)
        counts = witness_counts(report)
        st.metric("Point evaluations", sum(s["point_evaluations"] for s in report["scenarios"]))
        st.dataframe(pd.DataFrame(counts).fillna(0).astype(int), hide_index=False)
        st.caption("First witnesses only. Failure to find a witness is not proof of invariance.")
    elif choice == "Diagnostic possibilities":
        name = "mfpt_possibility_summary.json"
        report = read_report(name)
        rows = possibility_rows(report)
        contained = rows[rows["Reference contained"]]
        st.metric("Fault truth in outer set (reference contained)",
                  f'{contained["Fault truth included"].sum()}/{contained["Fault assessments"].sum()}')
        st.bar_chart(rows[[f"Size {i}" for i in range(4)]].sum())
        st.dataframe(rows, hide_index=True)
        st.warning("A singleton is not a stable diagnosis; an empty set does not establish health. Outer sets are not calibrated probabilities.")
    elif choice == "Measurement width":
        name = "mfpt_measurement_width_summary.json"
        report = read_report(name)
        error = st.selectbox("Declared speed error", sorted({s["declared_speed_error"] for s in report["scenarios"]}),
                             index=2, format_func=lambda x: f"{x:+.0%}", key="mfpt_measurement_error")
        rows = measurement_rows(report, error)
        st.bar_chart(rows.set_index("Width (%)")[["Correct", "Incorrect", "Withheld"]])
        st.dataframe(rows, hide_index=True)
        st.warning("Narrowing uncertainty does not correct a biased reading; accepted suggestions outside reference containment can be wrong.")
    elif choice == "Systematic bias":
        name = "mfpt_bias_budget_summary.json"
        report = read_report(name)
        rows = bias_rows(report)
        st.bar_chart(rows.set_index("Bias bound (%)")[["Correct", "Incorrect", "Withheld"]])
        st.dataframe(rows, hide_index=True)
        st.warning("An assumed bias bound is not a calibrated sensor specification. Unknown bias fails closed in the research guard.")
    elif choice == "Two-channel fusion":
        name = "mfpt_measurement_fusion_summary.json"
        report = read_report(name)
        rows = fusion_rows(report)
        st.bar_chart(rows.set_index("Secondary mode")[["Primary correct", "Fused correct"]])
        st.dataframe(rows, hide_index=True)
        st.metric("Accepted outside reference containment", int(rows["Accepted outside reference"].sum()))
        st.warning("Agreement is not calibration. Shared bias can yield compatible measurements that exclude the reference speed. The second channel is simulated.")
    else:
        name = "mfpt_common_mode_summary.json"
        report = read_report(name)
        rows = common_mode_rows(report)
        st.bar_chart(rows.set_index("Common bound (%)")[["Correct", "Incorrect", "Withheld"]])
        st.dataframe(rows, hide_index=True)
        st.warning("A shared-error bound must come from independent calibration. Compatibility and zero observed errors are not field safety guarantees.")
    evidence_link(report, name)
