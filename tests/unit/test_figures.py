"""figures.py testlari -- figura FAQAT analysis.json'dan, va sidecar bilan tekshiriladi.

Bu testlar hech qanday eksperiment ishga tushirmaydi va HECH QANDAY HAQIQIY
NATIJA ishlatmaydi: tajriba hech qachon o'tkazilmagan. Barcha fixture'lar
ATAYLAB SUN'IY (`SYNTHETIC` prefiksi, `analysis_version` ham shunday) va ular
chizgan har figuraning tagida `analysis_version = SYNTHETIC-...` ko'rinadi --
shuning uchun fixture'dan chiqqan figurani natija deb adashib bo'lmaydi.

Tekshiruv usuli: SVG baytlariga EMAS, sidecar JSON'ga (va SVG ichidagi <text>
elementlariga) qaraymiz. Shu sababli renderlash shriftga/versiyaga bog'liq
mayda farqlardan mustaqil.
"""
import ast
import builtins
import copy
import html
import json
import os
import re

import pytest

pytest.importorskip("matplotlib")

from revix import figures as F  # noqa: E402
from revix.schema import DISPOSITIONS  # noqa: E402

LEVELS = ("P0", "P1", "P2")
NOTE = "SYNTHETIC-NOTE-HORIZON: W_stab exceeds the horizon, VR not determinable"


# --- sun'iy fixture ----------------------------------------------------------


def _q(est, lo, hi):
    return {"estimate": est, "ci_lower": lo, "ci_upper": hi, "ci_method": "bca"}


def make_analysis() -> dict:
    """Sxemaga mos, lekin ATAYLAB sun'iy `analysis.json` (§2.2).

    Raqamlar hech narsani anglatmaydi -- ular faqat sidecar'ni tekshirish uchun
    ajratib bilib olinadigan qiymatlar. Ichki mantiqiy muvofiqlik (p_hat = k/n,
    CI p_hat'ni o'z ichiga oladi, sum(by_disposition) = total) saqlangan, aks
    holda figura buni `problems` ga yozadi (alohida test shuni tekshiradi).
    """
    grid = []
    for wi, w in enumerate((8, 10, 30, 60, 120)):
        for ti, th in enumerate((0.5, 0.8, 0.95)):
            if w >= 60:       # §2.3 #7: W_stab > T_trial (40.1 s) -> reduce.py None qaytaradi
                by_level = {lv: None for lv in LEVELS}
                note = NOTE
            else:
                by_level = {lv: round(1.0 - 0.1 * wi - 0.05 * ti - 0.1 * li, 2)
                            for li, lv in enumerate(LEVELS)}
                note = None
            grid.append({"w_stab": w, "theta": th, "p_vr_by_level": by_level, "note": note})
    return {
        "schema_version": 1,
        "analysis_version": "SYNTHETIC-FIXTURE/not-a-result",
        "preregistration_sha256": "SYNTHETIC" + "0" * 55,
        "generated_mono_us": 111,
        "t_trial_us": 40_100_000,       # v1.1 §5: 32.0 + 8.0 + 0.1 s
        "n_trials": {"total": 12, "by_disposition": {
            "complete": 7, "censored": 2, "contaminated": 2, "aborted_guard": 1}},
        "primary": {
            "endpoint": "SYNTHETIC P(VR) trend across pressure levels",
            "test": "cochran_armitage_trend",
            "statistic": -1.25, "p_value": 0.5, "direction": "decreasing",
            "cells": [
                {"level": "P0", "k": 4, "n": 5, "p_hat": 0.8,
                 "ci_lower": 0.5, "ci_upper": 0.95, "ci_method": "clopper_pearson"},
                {"level": "P1", "k": 3, "n": 5, "p_hat": 0.6,
                 "ci_lower": 0.2, "ci_upper": 0.9, "ci_method": "clopper_pearson"},
                {"level": "P2", "k": 2, "n": 5, "p_hat": 0.4,
                 "ci_lower": 0.1, "ci_upper": 0.8, "ci_method": "clopper_pearson"},
            ],
            "risk_difference": {"estimate": 0.4, "ci_lower": -0.1, "ci_upper": 0.7,
                                "ci_method": "newcombe"},
            "falsified": False,
            "falsification_rule": "trend p>0.05 AND newcombe_upper<0.15",
        },
        "survival": {
            "time_unit": "s",
            "km": {"by_arm": {
                "SYNTHETIC_ARM_A": {"times": [1.0, 2.0, 4.0], "survival": [0.8, 0.6, 0.3],
                                    "at_risk": [5, 4, 3], "greenwood_var": [0.03, 0.04, 0.05]},
                "SYNTHETIC_ARM_B": {"times": [2.0, 3.0, 5.0, 6.0],
                                    "survival": [0.9, 0.7, 0.4, 0.2],
                                    "at_risk": [5, 5, 4, 2],
                                    "greenwood_var": [0.02, 0.03, 0.04, 0.05]},
            }},
            "logrank": {"chi2": 0.5, "p_value": 0.48,
                        "observed": {"SYNTHETIC_ARM_A": 3, "SYNTHETIC_ARM_B": 4},
                        "expected": {"SYNTHETIC_ARM_A": 3.5, "SYNTHETIC_ARM_B": 3.5}},
            "rmst": {"tau": 6.0,
                     "by_arm": {"SYNTHETIC_ARM_A": {"estimate": 3.0, "se": 0.5},
                                "SYNTHETIC_ARM_B": {"estimate": 4.0, "se": 0.6}},
                     "difference": {"estimate": -1.0, "se": 0.8,
                                    "ci_lower": -2.5, "ci_upper": 0.5}},
            "proportional_hazards_checked": False,
            "censoring": {"n_censored": 2, "n_undetermined": 1,
                          "recovered_within_horizon": "7/10"},
        },
        "false_recovery": {"fr_a": {"per_action": 0.0, "per_episode": 0.0, "n_undetermined": 0},
                           "fr_b": {"computed": False, "reason": "no calibration matrix (P1)"}},
        "downtime": {
            "time_unit": "s",
            "d_sd": {"median": _q(1.0, 0.5, 1.5), "p90": _q(2.0, 1.5, 2.5),
                     "p99": _q(3.0, 2.0, 4.0)},
            "d_probe": {"median": _q(1.5, 1.0, 2.0), "p90": _q(2.5, 2.0, 3.0),
                        "p99": _q(3.5, 2.5, 4.5)},
            "d_eff": {"median": _q(2.0, 1.5, 2.5), "p90": _q(3.0, 2.5, 3.5), "p99": None},
        },
        "sensitivity": {"w_stab": [8, 10, 30, 60, 120], "theta": [0.5, 0.8, 0.95],
                        "grid": grid},
        "multiplicity": {"method": "holm_bonferroni", "family": [], "adjusted": []},
        "exclusions": {"rate": 0.25, "by_reason": {"contaminated": 2, "aborted_guard": 1}},
        "probe_cost": {"budget_percent": 1.0, "by_arm": {
            "SYNTHETIC_ARM_A": {"core_percent": [0.2, 0.4, 1.3]},
            "SYNTHETIC_ARM_B": {"core_percent": [0.3, None, 0.5]}}},
        "warnings": ["SYNTHETIC: d_eff p99 could not be estimated (not a real warning)",
                     "SYNTHETIC: unrelated housekeeping message"],
    }


def write_analysis(tmp_path, an, name="analysis.json", raw=None):
    p = tmp_path / name
    p.write_text(raw if raw is not None else json.dumps(an), encoding="utf-8")
    return p


def run(tmp_path, an=None, *extra, out="out", raw=None):
    """main() ni ishga tushiradi; (rc, figures katalogi) qaytaradi."""
    p = write_analysis(tmp_path, make_analysis() if an is None else an, raw=raw)
    out_dir = tmp_path / out
    rc = F.main(["--analysis", str(p), "--out-dir", str(out_dir), *extra])
    return rc, out_dir / "figures"


def side(fig_dir, name):
    return json.loads((fig_dir / f"{name}.json").read_text(encoding="utf-8"))


def svg_texts(fig_dir, name):
    """SVG ichidagi <text> elementlarining matni (svg.fonttype=none)."""
    svg = (fig_dir / f"{name}.svg").read_text(encoding="utf-8")
    parts = re.findall(r"<text\b[^>]*>(.*?)</text>", svg, flags=re.S)
    return [html.unescape(re.sub(r"<[^>]+>", "", p)) for p in parts]


def svg_blob(fig_dir, name):
    return "\n".join(svg_texts(fig_dir, name))


@pytest.fixture
def rendered(tmp_path):
    rc, fig_dir = run(tmp_path)
    assert rc == 0
    return fig_dir


# --- har figura ikki fayl ----------------------------------------------------


def test_figura_nomlari_shartnoma_s3_dagi_oltita_majburiy_figura(tmp_path):
    assert set(F.FIGURE_NAMES) == {
        "p_vr_vs_pressure", "km_time_to_vr", "downtime_ecdf",
        "sensitivity_heatmap", "exclusion_breakdown", "probe_cost"}


def test_barcha_majburiy_figuralar_chiziladi(tmp_path):
    rc, fig_dir = run(tmp_path)
    assert rc == 0
    for name in F.FIGURE_NAMES:
        assert (fig_dir / f"{name}.svg").is_file(), name
        assert side(fig_dir, name)["status"] in ("ok", "partial"), name


def test_har_svg_yonida_json_sidecar_bor(rendered):
    svgs = sorted(p.stem for p in rendered.glob("*.svg"))
    jsons = sorted(p.stem for p in rendered.glob("*.json"))
    assert svgs == jsons == sorted(F.FIGURE_NAMES)
    for name in svgs:
        text = (rendered / f"{name}.svg").read_text(encoding="utf-8")
        assert "<svg" in text and len(text) > 1000
        assert (rendered / f"{name}.json").stat().st_size > 0


def test_figures_katalogi_out_dir_ostida_yaratiladi(tmp_path):
    rc, fig_dir = run(tmp_path, out="nested/deeper")
    assert rc == 0
    assert fig_dir == tmp_path / "nested" / "deeper" / "figures"
    assert fig_dir.is_dir()


def test_sidecar_qat_iy_json_va_manba_maydonlari_bor(rendered):
    for name in F.FIGURE_NAMES:
        raw = (rendered / f"{name}.json").read_text(encoding="utf-8")
        d = json.loads(raw, parse_constant=lambda c: pytest.fail(f"{name}: {c} in sidecar"))
        assert d["figure"] == name
        assert d["source"]["file"] == "analysis.json"
        assert re.fullmatch(r"[0-9a-f]{64}", d["source"]["sha256"])
        assert d["source"]["analysis_version"] == "SYNTHETIC-FIXTURE/not-a-result"
        assert d["source"]["generated_mono_us"] == 111      # analizdan o'tkaziladi, soat o'qilmaydi
        assert d["contract"].startswith("driver-contract/v1")


def test_sidecar_sha256_analysis_json_baytlariga_mos(tmp_path):
    import hashlib
    rc, fig_dir = run(tmp_path)
    expected = hashlib.sha256((tmp_path / "analysis.json").read_bytes()).hexdigest()
    assert side(fig_dir, "p_vr_vs_pressure")["source"]["sha256"] == expected


# --- sidecar raqamlari chizilgan raqamlar ------------------------------------


def test_p_vr_sidecar_raqamlari_analizdagi_raqamlarga_aynan_teng(rendered):
    an = make_analysis()
    d = side(rendered, "p_vr_vs_pressure")["data"]
    for got, want in zip(d["cells"], an["primary"]["cells"]):
        assert got["level"] == want["level"]
        for key in ("k", "n", "p_hat", "ci_lower", "ci_upper", "ci_method"):
            assert got[key] == want[key], (want["level"], key)
        assert got["point_drawn"] and got["ci_drawn"]
    assert d["risk_difference"]["estimate"] == 0.4
    assert d["risk_difference"]["ci_lower"] == -0.1
    assert d["risk_difference"]["ci_upper"] == 0.7
    assert (d["test"], d["statistic"], d["p_value"]) == ("cochran_armitage_trend", -1.25, 0.5)
    assert d["falsified"] is False
    assert d["falsification_rule"] == "trend p>0.05 AND newcombe_upper<0.15"


def test_p_vr_svg_matnida_k_n_va_test_natijasi_ko_rsatiladi(rendered):
    blob = svg_blob(rendered, "p_vr_vs_pressure")
    for kn in ("4/5", "3/5", "2/5"):
        assert kn in blob
    assert "cochran_armitage_trend" in blob and "p = 0.5" in blob
    assert "newcombe" in blob
    assert "falsified (§11): false" in blob


def test_km_sidecar_vaqt_va_survival_massivlari_aynan_o_tkaziladi(rendered):
    an = make_analysis()
    d = side(rendered, "km_time_to_vr")["data"]
    by_arm = an["survival"]["km"]["by_arm"]
    assert [a["arm"] for a in d["arms"]] == sorted(by_arm)
    for a in d["arms"]:
        src = by_arm[a["arm"]]
        assert a["times"] == src["times"]
        assert a["survival"] == src["survival"]
        assert a["at_risk"] == src["at_risk"]
        assert a["greenwood_var"] == src["greenwood_var"]
        # chizilgan nuqtalar = S(0)=1 anchor + berilgan massiv, boshqa hech narsa
        assert a["drawn_x"] == [0.0] + src["times"]
        assert a["drawn_y"] == [1.0] + src["survival"]
        assert a["anchor_added"] == {"x": 0.0, "y": 1.0}
    assert d["logrank"]["chi2"] == 0.5 and d["logrank"]["p_value"] == 0.48
    assert d["rmst"]["tau"] == 6.0
    assert d["rmst"]["difference"]["ci_lower"] == -2.5


def test_downtime_sidecar_kvantillari_aynan_o_tkaziladi(rendered):
    an = make_analysis()
    d = side(rendered, "downtime_ecdf")["data"]
    got = {m["measure"]: m for m in d["measures"]}
    for m in ("d_sd", "d_probe"):
        for q in ("median", "p90", "p99"):
            src = an["downtime"][m][q]
            for k in ("estimate", "ci_lower", "ci_upper"):
                assert got[m]["quantiles"][q][k] == src[k]
    assert got["d_eff"]["quantiles"]["median"]["estimate"] == 2.0


def test_sensitivity_sidecar_butun_grid_va_qiymatlar(rendered):
    an = make_analysis()
    d = side(rendered, "sensitivity_heatmap")["data"]
    assert d["w_stab_s"] == [8, 10, 30, 60, 120]
    assert d["theta"] == [0.5, 0.8, 0.95]
    assert d["levels"] == list(LEVELS)
    assert len(d["cells"]) == 15
    src = {(g["w_stab"], g["theta"]): g for g in an["sensitivity"]["grid"]}
    for c in d["cells"]:
        want = src[(c["w_stab"], c["theta"])]["p_vr_by_level"]
        assert {lv: v["p_vr"] for lv, v in c["by_level"].items()} == want


def test_exclusion_sidecar_hamma_disposition_yopiq_enum_tartibida(rendered):
    d = side(rendered, "exclusion_breakdown")["data"]
    assert [r["disposition"] for r in d["by_disposition"]] == list(F.DISPOSITIONS)
    counts = {r["disposition"]: r["count"] for r in d["by_disposition"]}
    assert counts == {"complete": 7, "censored": 2, "contaminated": 2, "aborted_guard": 1,
                      "washout_timeout": 0, "harness_error": 0}
    flagged = {r["disposition"] for r in d["by_disposition"] if r["excluded_from_primary"]}
    assert flagged == {"contaminated", "aborted_guard"}                      # §12
    assert d["total"] == 12 and d["sum_matches_total"] is True
    assert d["exclusion_rate"] == 0.25
    assert {r["reason"]: r["value"] for r in d["by_reason"]} == {"contaminated": 2, "aborted_guard": 1}
    assert "25.0%" in svg_blob(rendered, "exclusion_breakdown")


def test_probe_cost_sidecar_qiymatlar_va_budjetdan_oshganlar(rendered):
    d = side(rendered, "probe_cost")["data"]
    assert d["budget_percent"] == 1.0
    arms = {a["arm"]: a for a in d["arms"]}
    assert arms["SYNTHETIC_ARM_A"]["values"] == [0.2, 0.4, 1.3]
    assert arms["SYNTHETIC_ARM_A"]["n_over_budget"] == 1
    assert arms["SYNTHETIC_ARM_B"]["values"] == [0.3, None, 0.5]       # None saqlanadi
    assert arms["SYNTHETIC_ARM_B"]["n_unmeasured"] == 1
    assert arms["SYNTHETIC_ARM_B"]["n_over_budget"] == 0


# --- yagona kirish: faqat analysis.json --------------------------------------


@pytest.mark.parametrize("name", ["probe.csv", "events.jsonl", "trial_metrics.jsonl",
                                  "psi.csv", "analysis.json.bak", "my_analysis.json"])
def test_analysis_json_dan_boshqa_fayl_nomi_rad_etiladi(tmp_path, name, capsys):
    p = tmp_path / name
    p.write_text(json.dumps(make_analysis()), encoding="utf-8")
    rc = F.main(["--analysis", str(p), "--out-dir", str(tmp_path / "out")])
    assert rc == 1
    assert "FAIL" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()          # hech narsa yozilmadi


def test_analysis_json_nomli_lekin_xom_record_bo_lgan_fayl_rad_etiladi(tmp_path, capsys):
    raw_record = {"schema_version": 1, "record_type": "probe_sample", "run_id": "r",
                  "mono_us": 1}
    rc, _ = run(tmp_path, raw=json.dumps(raw_record))
    assert rc == 1 and "xom" in capsys.readouterr().err


@pytest.mark.parametrize("raw, why", [
    ('{"schema_version": 2, "analysis_version": "x"}', "schema_version"),
    ('{"schema_version": 1}', "analysis_version"),
    ('[1, 2, 3]', "JSON obyekt"),
    ('{"schema_version": 1, "analysis_version": "x"', "yaroqli JSON"),
    ('{"a": 1}\n{"a": 2}\n', "yaroqli JSON"),            # JSONL = xom oqim shakli
])
def test_analysis_json_nomli_lekin_sxemaga_mos_bo_lmagan_fayl_rad_etiladi(tmp_path, capsys, raw, why):
    rc, fig_dir = run(tmp_path, raw=raw)
    assert rc == 1
    assert why in capsys.readouterr().err
    assert not fig_dir.exists()


def test_mavjud_bo_lmagan_analysis_json_rad_etiladi(tmp_path, capsys):
    rc = F.main(["--analysis", str(tmp_path / "analysis.json"), "--out-dir", str(tmp_path / "o")])
    assert rc == 1 and "FAIL" in capsys.readouterr().err


def test_yonidagi_xom_fayllar_hech_qachon_ochilmaydi(tmp_path, monkeypatch):
    # Xom fayllarni analysis.json yoniga qo'yamiz: figura ularga tegmasligi kerak.
    decoys = []
    for n in ("probe.csv", "events.jsonl", "trial_metrics.jsonl", "psi.csv", "run_meta.json"):
        (tmp_path / n).write_text("SYNTHETIC DECOY - must never be read\n", encoding="utf-8")
        decoys.append(n)
    write_analysis(tmp_path, make_analysis())
    opened = []
    real_open = builtins.open

    def spy(file, mode="r", *a, **kw):
        opened.append((os.fspath(file) if not isinstance(file, int) else file, mode))
        return real_open(file, mode, *a, **kw)

    monkeypatch.setattr(builtins, "open", spy)
    rc = F.main(["--analysis", str(tmp_path / "analysis.json"), "--out-dir", str(tmp_path / "o")])
    monkeypatch.setattr(builtins, "open", real_open)
    assert rc == 0
    under = [(p, m) for p, m in opened if isinstance(p, str)
             and os.path.abspath(p).startswith(str(tmp_path))]
    reads = {os.path.basename(p) for p, m in under if "r" in m and "w" not in m}
    assert reads == {"analysis.json"}
    assert not (set(decoys) & {os.path.basename(p) for p, _ in under})
    writes = {os.path.basename(p) for p, m in under if "w" in m}
    assert all(w.endswith((".svg.tmp", ".json.tmp")) for w in writes)


def test_modul_revix_paketidan_va_xom_ma_lumot_modullaridan_import_qilmaydi():
    tree = ast.parse(open(F.__file__, encoding="utf-8").read())
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            assert node.level == 0, "nisbiy import (from .reduce ...) taqiqlangan"
            imported.add((node.module or "").split(".")[0])
    allowed = {"__future__", "argparse", "hashlib", "io", "json", "math", "os", "re", "sys",
               "textwrap", "typing", "matplotlib"}
    assert imported <= allowed, f"kutilmagan import: {imported - allowed}"
    assert "revix" not in imported and "csv" not in imported


def test_disposition_enum_schema_py_bilan_bir_xil():
    assert F.DISPOSITIONS == DISPOSITIONS


def test_agg_backend_aniq_o_rnatiladi(tmp_path):
    import matplotlib
    rc, _ = run(tmp_path)
    assert rc == 0
    assert matplotlib.get_backend().lower() == "agg"


# --- yo'q qiymat: missing deb chiziladi, interpolyatsiya qilinmaydi ----------


def test_none_qiymat_missing_deb_chiziladi_va_nolga_aylantirilmaydi(tmp_path):
    an = make_analysis()
    c = an["primary"]["cells"][1]
    c.update(p_hat=None, ci_lower=None, ci_upper=None)
    rc, fig_dir = run(tmp_path, an)
    assert rc == 0
    s = side(fig_dir, "p_vr_vs_pressure")
    p1 = s["data"]["cells"][1]
    assert p1["p_hat"] is None and p1["ci_lower"] is None and p1["ci_upper"] is None
    assert p1["point_drawn"] is False and p1["ci_drawn"] is False
    # qo'shnilarning o'rtachasi (0.6) YOKI nol emas -- aynan None
    assert s["status"] == "partial"
    assert {"where": "primary.cells[P1]", "fields": ["p_hat", "ci_lower", "ci_upper"]} in s["missing"]
    blob = svg_blob(fig_dir, "p_vr_vs_pressure")
    assert "P1" in blob and "(missing)" in blob and "MISSING" in blob


def test_bitta_chekka_ci_yo_q_bo_lsa_nuqta_chiziladi_ci_chizilmaydi(tmp_path):
    an = make_analysis()
    an["primary"]["cells"][2]["ci_upper"] = None
    rc, fig_dir = run(tmp_path, an)
    p2 = side(fig_dir, "p_vr_vs_pressure")["data"]["cells"][2]
    assert p2["point_drawn"] is True and p2["ci_drawn"] is False
    assert p2["ci_upper"] is None


def test_nol_o_lchangan_nol_hisoblanadi_yo_q_emas(tmp_path):
    an = make_analysis()
    an["primary"]["cells"][2].update(k=0, n=5, p_hat=0.0, ci_lower=0.0, ci_upper=0.45)
    rc, fig_dir = run(tmp_path, an)
    s = side(fig_dir, "p_vr_vs_pressure")
    p2 = s["data"]["cells"][2]
    assert p2["p_hat"] == 0.0 and p2["k"] == 0 and p2["point_drawn"] is True
    assert not any(m["where"] == "primary.cells[P2]" for m in s["missing"])
    assert "0/5" in svg_blob(fig_dir, "p_vr_vs_pressure")


def test_nan_va_inf_yo_q_qiymat_hisoblanadi(tmp_path):
    raw = json.dumps(make_analysis()).replace('"p_value": 0.5', '"p_value": NaN', 1)
    raw = raw.replace('"statistic": -1.25', '"statistic": Infinity', 1)
    rc, fig_dir = run(tmp_path, raw=raw)
    assert rc == 0
    s = side(fig_dir, "p_vr_vs_pressure")
    assert s["data"]["p_value"] is None and s["data"]["statistic"] is None
    assert "p = missing" in svg_blob(fig_dir, "p_vr_vs_pressure")


def test_km_arm_massivida_none_bo_lsa_arm_chizilmaydi_interpolyatsiya_yo_q(tmp_path):
    an = make_analysis()
    an["survival"]["km"]["by_arm"]["SYNTHETIC_ARM_B"]["survival"][1] = None
    rc, fig_dir = run(tmp_path, an)
    s = side(fig_dir, "km_time_to_vr")
    b = next(a for a in s["data"]["arms"] if a["arm"] == "SYNTHETIC_ARM_B")
    assert b["drawn"] is False and b["drawn_x"] is None and b["drawn_y"] is None
    assert "not interpolated" in b["reason"]
    a_ = next(a for a in s["data"]["arms"] if a["arm"] == "SYNTHETIC_ARM_A")
    assert a_["drawn"] is True
    assert "SYNTHETIC_ARM_B" in svg_blob(fig_dir, "km_time_to_vr")
    assert "missing" in svg_blob(fig_dir, "km_time_to_vr")


def test_km_bo_sh_event_vaqtlari_arm_missing_deb_belgilanadi(tmp_path):
    an = make_analysis()
    an["survival"]["km"]["by_arm"]["SYNTHETIC_ARM_B"] = {"times": [], "survival": [],
                                                         "at_risk": [], "greenwood_var": []}
    rc, fig_dir = run(tmp_path, an)
    b = next(a for a in side(fig_dir, "km_time_to_vr")["data"]["arms"]
             if a["arm"] == "SYNTHETIC_ARM_B")
    assert b["drawn"] is False and "no event times" in b["reason"]


def test_downtime_o_lchovi_bo_sh_bo_lsa_missing_deb_ko_rsatiladi(tmp_path):
    an = make_analysis()
    an["downtime"]["d_sd"] = {}                       # §2.2: `d_sd: {}` -- hisoblanmagan
    rc, fig_dir = run(tmp_path, an)
    s = side(fig_dir, "downtime_ecdf")
    sd = next(m for m in s["data"]["measures"] if m["measure"] == "d_sd")
    assert sd["has_data"] is False
    assert all(v is None for v in sd["quantiles"].values())
    assert {"where": "downtime.d_sd", "fields": ["<empty>"]} in s["missing"]
    assert "D_sd" in svg_blob(fig_dir, "downtime_ecdf")
    assert "missing: not provided" in svg_blob(fig_dir, "downtime_ecdf")


def test_downtime_p99_none_bo_lsa_qolgan_kvantillar_chiziladi(rendered):
    d = side(rendered, "downtime_ecdf")["data"]
    eff = next(m for m in d["measures"] if m["measure"] == "d_eff")
    assert eff["quantiles"]["p99"] is None
    assert eff["quantiles"]["median"]["estimate"] == 2.0
    assert eff["has_data"] is True


def test_sensitivity_grid_da_yo_q_yacheyka_no_cell_deb_belgilanadi(tmp_path):
    an = make_analysis()
    an["sensitivity"]["grid"] = [g for g in an["sensitivity"]["grid"]
                                 if not (g["w_stab"] == 30 and g["theta"] == 0.8)]
    rc, fig_dir = run(tmp_path, an)
    s = side(fig_dir, "sensitivity_heatmap")
    cell = next(c for c in s["data"]["cells"] if c["w_stab"] == 30 and c["theta"] == 0.8)
    assert cell["has_cell"] is False and cell["by_level"] == {}
    assert "no cell" in svg_blob(fig_dir, "sensitivity_heatmap")


# --- sweep yacheykasi `note` va warnings -------------------------------------


def test_sweep_yacheyka_note_figurada_ko_rsatiladi(rendered):
    s = side(rendered, "sensitivity_heatmap")
    assert any(NOTE in n for n in s["notes"])
    notes = s["data"]["cell_notes"]
    assert len(notes) == 1 and notes[0]["text"] == NOTE and notes[0]["index"] == 1
    assert sorted(notes[0]["cells"]) == [[60, 0.5], [60, 0.8], [60, 0.95],
                                         [120, 0.5], [120, 0.8], [120, 0.95]]
    for c in s["data"]["cells"]:
        assert (c["note_index"] == 1) == (c["w_stab"] >= 60)
        if c["w_stab"] >= 60:                       # reduce.py None -> "yo'q", nol emas
            assert all(v["p_vr"] is None for v in c["by_level"].values())
    blob = svg_blob(rendered, "sensitivity_heatmap")
    assert "SYNTHETIC-NOTE-HORIZON" in blob          # figura tagida izoh
    assert "n/a [1]" in blob                         # yacheykaning o'zida belgi
    assert s["status"] == "partial"                  # yo'q qiymatlar -> "ok" emas


def test_sweep_primary_pilot_yacheykasi_belgilanadi(rendered):
    d = side(rendered, "sensitivity_heatmap")["data"]
    assert d["pilot"] == {"w_stab": 8.0, "theta": 0.8, "in_grid": True}


def test_note_bo_lmagan_sweep_hech_qanday_izoh_chiqarmaydi(tmp_path):
    an = make_analysis()
    an["sensitivity"]["grid"] = [g for g in an["sensitivity"]["grid"] if g["w_stab"] <= 30]
    an["sensitivity"]["w_stab"] = [8, 10, 30]          # hammasi horizon (40.1 s) ichida
    for g in an["sensitivity"]["grid"]:
        g["note"] = None
        g["p_vr_by_level"] = {lv: 0.5 for lv in LEVELS}
    rc, fig_dir = run(tmp_path, an)
    s = side(fig_dir, "sensitivity_heatmap")
    assert s["notes"] == [] and s["data"]["cell_notes"] == [] and s["status"] == "ok"


def test_warnings_soni_har_figurada_tegishlisi_matni_bilan_ko_rsatiladi(rendered):
    for name in F.FIGURE_NAMES:
        w = side(rendered, name)["analysis_warnings"]
        assert w["total"] == 2, name                  # hech biri jim tushirilmaydi
        assert "analysis.json warnings: 2 in total" in svg_blob(rendered, name), name
    down = side(rendered, "downtime_ecdf")["analysis_warnings"]["relevant"]
    assert down == ["SYNTHETIC: d_eff p99 could not be estimated (not a real warning)"]
    assert "WARNING: SYNTHETIC: d_eff p99" in svg_blob(rendered, "downtime_ecdf")
    for name in ("p_vr_vs_pressure", "km_time_to_vr", "exclusion_breakdown", "probe_cost"):
        assert side(rendered, name)["analysis_warnings"]["relevant"] == [], name


def test_warning_lug_shaklida_figure_maydoni_bilan_belgilanadi(tmp_path):
    an = make_analysis()
    an["warnings"] = [{"message": "SYNTHETIC tagged warning", "figure": "probe_cost"}]
    rc, fig_dir = run(tmp_path, an)
    assert side(fig_dir, "probe_cost")["analysis_warnings"]["relevant"] == ["SYNTHETIC tagged warning"]
    assert side(fig_dir, "km_time_to_vr")["analysis_warnings"]["relevant"] == []
    assert side(fig_dir, "km_time_to_vr")["analysis_warnings"]["total"] == 1


def test_warnings_bo_lmasa_warning_qatori_chiqmaydi(tmp_path):
    an = make_analysis()
    an["warnings"] = []
    rc, fig_dir = run(tmp_path, an)
    assert "analysis.json warnings" not in svg_blob(fig_dir, "p_vr_vs_pressure")
    assert side(fig_dir, "p_vr_vs_pressure")["analysis_warnings"] == {"total": 0, "relevant": []}


# --- §6.2: recovered_within_horizon k/n --------------------------------------


def test_recovered_within_horizon_survival_va_downtime_figuralarida_ko_rsatiladi(rendered):
    for name in ("km_time_to_vr", "downtime_ecdf"):
        s = side(rendered, name)
        assert s["recovered_within_horizon"] == {"raw": "7/10", "k": 7, "n": 10}
        assert "recovered within horizon: 7/10" in svg_blob(rendered, name), name


def test_recovered_within_horizon_analizda_yo_q_bo_lsa_not_provided_deb_ko_rsatiladi(tmp_path):
    an = make_analysis()
    del an["survival"]["censoring"]["recovered_within_horizon"]
    rc, fig_dir = run(tmp_path, an)
    for name in ("km_time_to_vr", "downtime_ecdf"):
        assert side(fig_dir, name)["recovered_within_horizon"] is None
        assert "recovered within horizon: not provided" in svg_blob(fig_dir, name), name


def test_downtime_o_lchovining_o_z_recovered_k_n_i_alohida_ko_rsatiladi(tmp_path):
    an = make_analysis()
    an["downtime"]["d_probe"]["recovered_within_horizon"] = "5/8"
    rc, fig_dir = run(tmp_path, an)
    assert "D_probe (primary): recovered within horizon 5/8" in svg_blob(fig_dir, "downtime_ecdf")


# --- §10.2 taqiqlari; downtime ECDF; vaqt birligi ----------------------------


def test_proportional_hazards_tekshirilmagan_bo_lsa_hazard_ratio_chizilmaydi(rendered):
    s = side(rendered, "km_time_to_vr")
    assert s["data"]["proportional_hazards_checked"] is False
    blob = svg_blob(rendered, "km_time_to_vr")
    assert "proportional_hazards_checked = false" in blob
    assert "hazard ratio is never drawn" in blob
    assert "hazard_ratio" not in json.dumps(s)


def test_figuralarda_mean_sd_va_t_test_chiqmaydi(rendered):
    for name in F.FIGURE_NAMES:
        blob = svg_blob(rendered, name).lower()
        assert "t-test" not in blob and "mean ±" not in blob and "± sd" not in blob, name


def test_ecdf_berilmasa_chiziq_interpolyatsiya_qilinmaydi_va_izoh_beriladi(rendered):
    s = side(rendered, "downtime_ecdf")
    assert s["data"]["ecdf_available"] is False
    assert all(m["ecdf"] is None for m in s["data"]["measures"])
    assert any("no per-trial ECDF" in n and "no ECDF line is interpolated" in n for n in s["notes"])
    assert "no per-trial ECDF" in svg_blob(rendered, "downtime_ecdf")


def test_ecdf_berilsa_aynan_berilgan_nuqtalar_chiziladi(tmp_path):
    an = make_analysis()
    ecdf = {"x": [0.5, 1.0, 2.0, 4.0], "y": [0.1, 0.5, 0.9, 1.0]}
    an["downtime"]["d_probe"]["ecdf"] = ecdf
    rc, fig_dir = run(tmp_path, an)
    s = side(fig_dir, "downtime_ecdf")
    probe = next(m for m in s["data"]["measures"] if m["measure"] == "d_probe")
    assert probe["ecdf"] == ecdf
    assert s["data"]["ecdf_available"] is True
    assert not any("no per-trial ECDF" in n for n in s["notes"])


@pytest.mark.parametrize("bad", [
    {"x": [1.0, 2.0], "y": [0.5]},                   # uzunliklar teng emas
    {"x": [2.0, 1.0], "y": [0.2, 0.4]},              # tartiblanmagan
    {"x": [1.0, 2.0], "y": [0.2, 1.4]},              # [0,1] dan tashqari
    {"x": [1.0, None], "y": [0.2, 0.4]},             # yo'q qiymat
])
def test_yaroqsiz_ecdf_chizilmaydi_va_problem_deb_yoziladi(tmp_path, bad):
    an = make_analysis()
    an["downtime"]["d_probe"]["ecdf"] = bad
    rc, fig_dir = run(tmp_path, an)
    s = side(fig_dir, "downtime_ecdf")
    probe = next(m for m in s["data"]["measures"] if m["measure"] == "d_probe")
    assert probe["ecdf"] is None
    assert any("downtime.d_probe.ecdf is malformed" in p for p in s["problems"])


def test_vaqt_birligi_e_lon_qilinsa_o_qda_yoziladi(rendered):
    assert side(rendered, "km_time_to_vr")["data"]["time_unit"] == {
        "stated": True, "unit": "s", "label": "s"}
    assert "time to VR (s)" in svg_blob(rendered, "km_time_to_vr")
    assert "downtime (s)" in svg_blob(rendered, "downtime_ecdf")


def test_vaqt_birligi_e_lon_qilinmasa_taxmin_qilinmaydi(tmp_path):
    an = make_analysis()
    del an["survival"]["time_unit"]
    del an["downtime"]["time_unit"]
    rc, fig_dir = run(tmp_path, an)
    for name in ("km_time_to_vr", "downtime_ecdf"):
        s = side(fig_dir, name)
        assert s["data"]["time_unit"]["stated"] is False and s["data"]["time_unit"]["unit"] is None
        blob = svg_blob(fig_dir, name)
        assert "unit not stated in analysis.json" in blob
        assert any("time unit is not stated" in n for n in s["notes"])


# --- eksklyuziya: §12 --------------------------------------------------------


def test_by_disposition_yig_indisi_total_ga_teng_bo_lmasa_yo_q_kalit_nol_emas(tmp_path):
    an = make_analysis()
    an["n_trials"]["total"] = 20                      # 12 hisoblangan, 8 tushuntirilmagan
    rc, fig_dir = run(tmp_path, an)
    s = side(fig_dir, "exclusion_breakdown")
    rows = {r["disposition"]: r["count"] for r in s["data"]["by_disposition"]}
    assert rows["washout_timeout"] is None and rows["harness_error"] is None   # nol deb TAXMIN QILINMADI
    assert rows["complete"] == 7
    assert s["data"]["sum_matches_total"] is False
    assert any("sums to 12 but n_trials.total = 20" in p for p in s["problems"])


def test_enumdan_tashqari_disposition_ham_chiziladi_va_problem_bo_ladi(tmp_path):
    an = make_analysis()
    an["n_trials"]["by_disposition"]["SYNTHETIC_unknown"] = 0
    rc, fig_dir = run(tmp_path, an)
    s = side(fig_dir, "exclusion_breakdown")
    names = [r["disposition"] for r in s["data"]["by_disposition"]]
    assert names[-1] == "SYNTHETIC_unknown" and names[:6] == list(F.DISPOSITIONS)
    assert any("not in the closed §12 enum" in p for p in s["problems"])


def test_eksklyuziya_darajasi_va_sababsiz_holat_surfacelanadi(tmp_path):
    an = make_analysis()
    an["exclusions"] = {"rate": 0.25, "by_reason": {}}
    rc, fig_dir = run(tmp_path, an)
    s = side(fig_dir, "exclusion_breakdown")
    assert any("rate > 0 but exclusions.by_reason is empty" in p for p in s["problems"])
    assert "by_reason is empty" in svg_blob(fig_dir, "exclusion_breakdown")


# --- nomuvofiqlik: figura tuzatmaydi, sath qiladi ----------------------------


def test_p_hat_k_n_ga_mos_kelmasa_problems_ga_yoziladi_va_qiymat_o_zgartirilmaydi(tmp_path):
    an = make_analysis()
    an["primary"]["cells"][0]["p_hat"] = 0.7          # k/n = 4/5 = 0.8
    rc, fig_dir = run(tmp_path, an)
    s = side(fig_dir, "p_vr_vs_pressure")
    assert s["data"]["cells"][0]["p_hat"] == 0.7      # jimgina tuzatilmadi
    assert any("differs from k/n=4/5" in p for p in s["problems"])
    assert "DATA PROBLEM" in svg_blob(fig_dir, "p_vr_vs_pressure")


def test_p_hat_ci_dan_tashqarida_bo_lsa_problems_ga_yoziladi(tmp_path):
    an = make_analysis()
    an["primary"]["cells"][0].update(ci_lower=0.1, ci_upper=0.7)
    rc, fig_dir = run(tmp_path, an)
    assert any("outside CI" in p for p in side(fig_dir, "p_vr_vs_pressure")["problems"])


# --- bo'lim yo'q: placeholder -------------------------------------------------


def test_probe_cost_bo_limi_yo_q_bo_lsa_placeholder_chiziladi_va_ogohlantiriladi(tmp_path, capsys):
    an = make_analysis()
    del an["probe_cost"]                              # §2.2 da bu bo'lim umuman yo'q
    rc, fig_dir = run(tmp_path, an)
    assert rc == 0
    s = side(fig_dir, "probe_cost")
    assert s["status"] == "placeholder" and s["data"] is None
    assert "§2.2 does not define it" in s["placeholder_reason"]
    assert (fig_dir / "probe_cost.svg").is_file()     # figura yo'q deb ham AYTILADI
    assert "NOT DRAWN" in svg_blob(fig_dir, "probe_cost")
    assert "probe_cost" in capsys.readouterr().err    # WARN stderr'da
    assert side(fig_dir, "p_vr_vs_pressure")["status"] in ("ok", "partial")   # boshqalar ta'sirlanmaydi


@pytest.mark.parametrize("section, figure", [
    ("primary", "p_vr_vs_pressure"), ("survival", "km_time_to_vr"),
    ("downtime", "downtime_ecdf"), ("sensitivity", "sensitivity_heatmap"),
    ("n_trials", "exclusion_breakdown"),
])
def test_bo_lim_butunlay_yo_q_bo_lsa_figura_placeholder_bo_ladi_ixtiro_qilinmaydi(tmp_path, section, figure):
    an = make_analysis()
    del an[section]
    rc, fig_dir = run(tmp_path, an)
    assert rc == 0
    s = side(fig_dir, figure)
    assert s["status"] == "placeholder" and s["data"] is None
    assert s["placeholder_reason"]
    assert "NOT DRAWN" in svg_blob(fig_dir, figure)


def test_placeholder_ham_warnings_va_manbani_ko_rsatadi(tmp_path):
    an = make_analysis()
    del an["probe_cost"]
    an["warnings"] = [{"message": "SYNTHETIC probe cost not measured", "section": "probe_cost"}]
    rc, fig_dir = run(tmp_path, an)
    blob = svg_blob(fig_dir, "probe_cost")
    assert "WARNING: SYNTHETIC probe cost not measured" in blob
    assert "SYNTHETIC-FIXTURE/not-a-result" in blob


# --- uslub: oq-qora ----------------------------------------------------------


def _colours(svg: str) -> set[str]:
    return {c.lower() for c in re.findall(r"#[0-9a-fA-F]{6}\b", svg)}


def test_oq_qora_chop_etishda_o_qiladi_svg_faqat_kulrang_ranglardan_foydalanadi(rendered):
    for name in F.FIGURE_NAMES:
        svg = (rendered / f"{name}.svg").read_text(encoding="utf-8")
        assert "rgb(" not in svg and "rgba(" not in svg, name
        cols = _colours(svg)
        assert cols, name
        for c in cols:
            r, g, b = c[1:3], c[3:5], c[5:7]
            assert r == g == b, f"{name}: rangli element {c}"


def test_placeholder_svg_ham_kulrang(tmp_path):
    an = make_analysis()
    del an["probe_cost"]
    rc, fig_dir = run(tmp_path, an)
    for c in _colours((fig_dir / "probe_cost.svg").read_text(encoding="utf-8")):
        assert c[1:3] == c[3:5] == c[5:7]


def test_km_qatorlari_marker_va_chiziq_turi_bilan_farqlanadi():
    # rang bilan emas: ketma-ket qatorlarning (marker, chiziq) juftligi takrorlanmaydi
    pairs = [(s["marker"], str(s["ls"])) for s in F._SERIES_STYLES]
    assert len(set(pairs)) == len(pairs)
    d = F._DOWNTIME_STYLES
    assert len({(v["marker"], str(v["ls"])) for v in d.values()}) == len(d) == 3


# --- determinizm --------------------------------------------------------------


def test_bir_xil_kirish_bir_xil_sidecar_beradi(tmp_path):
    a = tmp_path / "a"
    b = tmp_path / "b"
    a.mkdir()
    b.mkdir()
    rc1, fa = run(a)
    rc2, fb = run(b)
    assert rc1 == rc2 == 0
    for name in F.FIGURE_NAMES:
        assert (fa / f"{name}.json").read_bytes() == (fb / f"{name}.json").read_bytes(), name


def test_sidecar_vaqt_tamg_asi_va_yo_l_saqlamaydi(rendered, tmp_path):
    for name in F.FIGURE_NAMES:
        raw = (rendered / f"{name}.json").read_text(encoding="utf-8")
        assert str(tmp_path) not in raw and "\\" not in raw.replace("\\n", "")
        assert not re.search(r"20\d\d-\d\d-\d\dT", raw)


def test_qayta_ishga_tushirish_mavjud_figuralarni_qayta_yozadi(tmp_path):
    rc, fig_dir = run(tmp_path)
    (fig_dir / "probe_cost.json").write_text("STALE", encoding="utf-8")
    rc, fig_dir = run(tmp_path)
    assert rc == 0 and side(fig_dir, "probe_cost")["figure"] == "probe_cost"
    assert not list(fig_dir.glob("*.tmp"))


# --- CLI -----------------------------------------------------------------------


def test_only_flagi_faqat_so_ralgan_figuralarni_chizadi(tmp_path):
    rc, fig_dir = run(tmp_path, None, "--only", "km_time_to_vr", "--only", "probe_cost")
    assert rc == 0
    assert sorted(p.stem for p in fig_dir.glob("*.svg")) == ["km_time_to_vr", "probe_cost"]
    assert sorted(p.stem for p in fig_dir.glob("*.json")) == ["km_time_to_vr", "probe_cost"]


def test_only_flagi_noma_lum_figura_nomini_rad_etadi(tmp_path):
    p = write_analysis(tmp_path, make_analysis())
    with pytest.raises(SystemExit) as e:
        F.main(["--analysis", str(p), "--out-dir", str(tmp_path / "o"), "--only", "nope"])
    assert e.value.code == 2


@pytest.mark.parametrize("missing", ["--analysis", "--out-dir"])
def test_majburiy_flaglar_tushib_qolsa_usage_xatosi(tmp_path, missing):
    args = {"--analysis": str(tmp_path / "analysis.json"), "--out-dir": str(tmp_path / "o")}
    del args[missing]
    argv = [x for kv in args.items() for x in kv]
    with pytest.raises(SystemExit) as e:
        F.main(argv)
    assert e.value.code == 2


def test_json_flagi_barqaror_kalitli_xulosa_chiqaradi(tmp_path, capsys):
    p = write_analysis(tmp_path, make_analysis())
    rc = F.main(["--analysis", str(p), "--out-dir", str(tmp_path / "o"), "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    assert out["analysis_version"] == "SYNTHETIC-FIXTURE/not-a-result"
    assert out["analysis_warnings_total"] == 2
    assert [f["name"] for f in out["figures"]] == list(F.FIGURE_NAMES)
    assert all(f["status"] in ("ok", "partial") for f in out["figures"])
    assert all(os.path.isfile(f["svg"]) and os.path.isfile(f["json"]) for f in out["figures"])


def test_json_flagi_placeholder_statusini_ham_ko_rsatadi(tmp_path, capsys):
    an = make_analysis()
    del an["probe_cost"]
    p = write_analysis(tmp_path, an)
    rc = F.main(["--analysis", str(p), "--out-dir", str(tmp_path / "o"), "--json"])
    assert rc == 0
    out = json.loads(capsys.readouterr().out)
    pc = next(f for f in out["figures"] if f["name"] == "probe_cost")
    assert pc["status"] == "placeholder" and pc["reason"]


def test_matn_chiqishi_figura_sonini_va_katalogni_aytadi(tmp_path, capsys):
    rc, fig_dir = run(tmp_path)
    out = capsys.readouterr().out
    assert rc == 0 and "figuralar: 6" in out and str(fig_dir) in out


def test_main_argv_ro_yxati_bilan_chaqiriladi_cli_py_uchun_shartnoma(tmp_path):
    import inspect
    sig = inspect.signature(F.main)
    assert list(sig.parameters) == ["argv"] and sig.parameters["argv"].default is None
    p = write_analysis(tmp_path, make_analysis())
    assert F.main(["--analysis", str(p), "--out-dir", str(tmp_path / "o")]) == 0


def test_chizish_xatosi_jim_o_tkazib_yuborilmaydi(tmp_path, monkeypatch, capsys):
    def boom(mpl, model):
        raise RuntimeError("SYNTHETIC draw failure")
    monkeypatch.setitem(F._DRAW, "km_time_to_vr", boom)
    p = write_analysis(tmp_path, make_analysis())
    rc = F.main(["--analysis", str(p), "--out-dir", str(tmp_path / "o"), "--json"])
    assert rc == 1
    cap = capsys.readouterr()
    assert "SYNTHETIC draw failure" in cap.err
    out = json.loads(cap.out)
    st = {f["name"]: f["status"] for f in out["figures"]}
    assert st["km_time_to_vr"] == "error" and st["probe_cost"] in ("ok", "partial")
    assert not (tmp_path / "o" / "figures" / "km_time_to_vr.svg").exists()


# --- figura matni sidecar `text` bilan mos -------------------------------------


def test_sidecar_text_maydonidagi_har_qator_figurada_ko_rinadi(rendered):
    for name in F.FIGURE_NAMES:
        s = side(rendered, name)
        blob = svg_blob(rendered, name)
        for line in s["text"]["main"] + s["text"]["small"]:
            assert line[:28] in blob, (name, line[:28])


# --- v1.1: T_trial (recovery horizon) va aniqlanmagan (vr=None) ---------------


def test_horizon_analizdan_olinadi_va_km_hamda_downtime_figuralarida_soniyada_yoziladi(rendered):
    for name in ("km_time_to_vr", "downtime_ecdf", "sensitivity_heatmap"):
        h = side(rendered, name)["data"]["horizon"]
        assert h["t_trial_us"] == 40_100_000 and h["seconds"] == 40.1, name
        assert "T_trial = 40.1 s" in svg_blob(rendered, name), name
    assert "recovered within horizon: 7/10  (T_trial = 40.1 s)" in svg_blob(rendered, "km_time_to_vr")
    # vaqt birligi "s" e'lon qilingan -> horizon o'qda ham (aynan 40.1)
    assert side(rendered, "km_time_to_vr")["data"]["horizon"]["axis_value"] == pytest.approx(40.1)


def test_horizon_birlik_e_lon_qilinmasa_o_qda_chizilmaydi_lekin_matnda_bor(tmp_path):
    an = make_analysis()
    del an["survival"]["time_unit"]
    rc, fig_dir = run(tmp_path, an)
    h = side(fig_dir, "km_time_to_vr")["data"]["horizon"]
    assert h["seconds"] == 40.1 and h["axis_value"] is None
    assert "T_trial = 40.1 s" in svg_blob(fig_dir, "km_time_to_vr")


def test_horizon_analizda_yo_q_bo_lsa_taxmin_qilinmaydi(tmp_path):
    an = make_analysis()
    del an["t_trial_us"]
    rc, fig_dir = run(tmp_path, an)
    for name in ("km_time_to_vr", "downtime_ecdf", "sensitivity_heatmap"):
        s = side(fig_dir, name)
        assert s["data"]["horizon"] == {"t_trial_us": None, "seconds": None, "axis_value": None}
        assert {"where": "analysis.json", "fields": ["t_trial_us"]} in s["missing"]
        assert "T_trial not provided in analysis.json" in svg_blob(fig_dir, name)
        assert "40.1" not in svg_blob(fig_dir, name)


def test_aniqlanmagan_vr_none_alohida_kategoriya_recovered_emasga_qo_shilmaydi(rendered):
    s = side(rendered, "km_time_to_vr")
    assert s["data"]["censoring"]["n_undetermined"] == 1
    assert s["data"]["censoring"]["n_censored"] == 2          # aralashtirilmagan
    blob = svg_blob(rendered, "km_time_to_vr")
    assert "VR undetermined (vr=None, own category; not counted as recovered or failed): 1" in blob
    assert s["recovered_within_horizon"]["k"] == 7            # 7/10 ga 1 qo'shilmadi


def test_aniqlanmagan_soni_berilmasa_not_provided_deb_ko_rsatiladi(tmp_path):
    an = make_analysis()
    del an["survival"]["censoring"]["n_undetermined"]
    rc, fig_dir = run(tmp_path, an)
    assert side(fig_dir, "km_time_to_vr")["data"]["censoring"]["n_undetermined"] is None
    assert "not counted as recovered or failed): not provided" in svg_blob(fig_dir, "km_time_to_vr")


def test_w_stab_horizondan_katta_lekin_note_yo_q_yacheyka_problem_deb_sath_qilinadi(tmp_path):
    an = make_analysis()
    for g in an["sensitivity"]["grid"]:
        if g["w_stab"] == 60 and g["theta"] == 0.8:
            g["note"] = None
    rc, fig_dir = run(tmp_path, an)
    s = side(fig_dir, "sensitivity_heatmap")
    assert any("W_stab=60 s > T_trial=40.1 s" in p and "no note" in p for p in s["problems"])
    assert side(fig_dir, "p_vr_vs_pressure")["problems"] == []


def test_argv_kontrakti_cli_py_chaqiradigan_shaklda_ishlaydi(tmp_path, capsys):
    # agent/cli: ["--analysis", A, "--out-dir", D] + ["--only", N]... + ["--json"]
    p = write_analysis(tmp_path, make_analysis())
    argv = ["--analysis", str(p), "--out-dir", str(tmp_path / "o"),
            "--only", "probe_cost", "--only", "km_time_to_vr", "--json"]
    assert F.main(argv) == 0
    out = json.loads(capsys.readouterr().out)
    assert {f["name"] for f in out["figures"]} == {"probe_cost", "km_time_to_vr"}
