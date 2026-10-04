import json, sys
a = json.load(open(sys.argv[1]))
print("n_begin", a["n_trial_begin"], "n_end", a["n_trial_end"], "psi_rows", a["psi_rows"], "harness_errors", a["harness_errors"])
print("guard:", json.dumps(a["guard_records"], default=str)[:1500])
for t in a["trials"]:
    for k in ("trial_id","arm","pressure_level","disposition","reason","matched_rules","facts","anomalies","overhead_s","washout","pressure_detail","timeline_rel_s","user_rate_spans_ge_0.35","user_rate_spans_ge_0.05","lab_rate_spans_ge_0.35","lab_rate_spans_ge_0.05","user_rate_max","user_rate_n_ge_runaway_0.98","longest_user_span_ge_0.35_s","ramp_above_threshold_s_generator_ramp_window(10§4)","ramp_above_threshold_s_planned_ramp_window_lab","ramp_above_threshold_s_planned_ramp_window_user","generator_stop","generator_pi_samples","generator_pi_rate_median"):
        print(" ", k, "=", json.dumps(t.get(k), default=str)[:900])
