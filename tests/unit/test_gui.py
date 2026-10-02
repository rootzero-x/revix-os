"""gui.py testlari -- dashboard'ning O'LCHOV YAXLITLIGI qulflari.

Bu testlar GO'ZALLIKNI sinamaydi. Ular AYNAN shu narsalarni qulflaydi:

  1. `None` (o'lchanmadi) hech qachon `0` (o'lchangan nol) kabi ko'rinmaydi,
     va o'lchanmagan qiymat ko'rinadigan matnida BIRORTA RAQAM bo'lmaydi;
  2. manbada yo'q kalit uchun panel SON O'YLAB CHIQARMAYDI;
  3. eksklyuziya darajasi TO'PLAMI nomlanmasa KO'RSATILMAYDI (§16.4);
  4. sintetik fixture RENDERLANGAN CHIQISHDA sintetik deb belgilanadi;
  5. server loopback'ga bog'lanadi, loopback bo'lmagan bind rad etiladi;
  6. fayldan o'qilgan matn (`run_meta` maydoni, journal satri) escape
     qilinadi -- u sahifa uchun kirish ma'lumoti, markup emas.

TESTLAR MUHITGA TAYANMAYDI: panel renderlari toza funksiyalar va ularga
dict'lar BERILADI, shuning uchun bu fayl Linux PSI yoki systemd bo'lmagan
holatda ham bir xil narsani isbotlaydi. Yagona istisno -- `Gateway` ning
fayl o'qishi (`tmp_path` bilan) va bind qoidasi (socket ochmasdan).

NEGA "KO'RINADIGAN MATN" ustida tekshiriladi: `html.escape(quote=True)`
apostrofni `&#x27;` ga aylantiradi, ya'ni XOM markup'da raqam paydo bo'ladi
(`2`, `7`) hech qanday son ko'rsatilmasa ham. Foydalanuvchi esa markup'ni
emas, RENDER NATIJASINI ko'radi. Shu sababli `visible_text()` avval teglarni
olib tashlaydi, keyin entity'larni ochadi -- va qoida AYNAN ko'rinadigan
matnga qo'llanadi. Markup ustida tekshirish soxta yiqilish berardi.
"""
from __future__ import annotations

import html as html_mod
import json
import os
import re

import pytest

from revix import cli
from revix import gui


# --- yordamchilar -----------------------------------------------------------


def visible_text(markup: str) -> str:
    """Foydalanuvchi EKRANDA ko'radigan matn: teglar olinadi, entity ochiladi.

    Tartib muhim: avval tegni olib tashlash, keyin `unescape`. Teskarisida
    `&lt;b&gt;` ochilib `<b>` bo'lardi va keyin teg deb o'chirilardi -- ya'ni
    escape qilingan matn ko'rinmay qolardi va test aynan escape'ni
    tekshirayotganda yolg'on "o'tdi" berardi.
    """
    no_tags = re.sub(r"<[^>]*>", " ", markup)
    return html_mod.unescape(no_tags)


def has_digit(text: str) -> bool:
    return any(ch.isdigit() for ch in text)


def make_opts(**kw) -> gui.Options:
    base = dict(host="127.0.0.1", port=8787, datasets_dir="/nonexistent-datasets")
    base.update(kw)
    return gui.Options(**base)


def make_ctx(opts: gui.Options | None = None) -> gui.Context:
    o = opts or make_opts()
    return gui.Context(opts=o, gw=gui.Gateway(o), now_real_us=1_700_000_000_000_000)


NOW = 1_700_000_000_000_000
LIVE_SRC = gui.Source(kind="live", name="test", read_real_us=NOW)


# ===========================================================================
# 1. None != 0 -- to'rt holat to'rt xil ko'rinadi
# ===========================================================================


def test_olchanmagan_qiymat_korinadigan_matnida_birorta_raqam_yoq():
    """`None` -> "o'lchanmadi": ko'rinadigan matnda RAQAM BO'LMAYDI.

    Busiz nima buzilardi: o'lchanmagan maydon uchun `0` yoki `-` bosilsa,
    o'quvchi uni o'lchov natijasi deb o'qiydi va mavjud bo'lmagan nolga
    ishonadi (`PREREGISTRATION.md` §15.4 ning aynan masalasi).
    """
    out = gui.value_html(None)
    assert not has_digit(visible_text(out))
    assert gui.TEXT_NOT_MEASURED in visible_text(out)


def test_none_va_nol_bir_xil_renderlanMAYDI():
    """`None` va `0` -- IKKI BOSHQA chiqish, matni ham, klassi ham."""
    none_out = gui.value_html(None)
    zero_out = gui.value_html(0)
    assert none_out != zero_out
    assert "v-missing" in none_out
    assert "v-zero" in zero_out
    assert visible_text(none_out) != visible_text(zero_out)


def test_olchangan_nol_sonni_KORSATADI_va_belgilaydi():
    """`0` -> son ko'rinadi + "o'lchangan nol" belgisi (nol -- natija)."""
    text = visible_text(gui.value_html(0))
    assert "0" in text
    assert gui.TEXT_MEASURED_ZERO in text
    # Float nol ham xuddi shunday -- nol butun songa xos emas.
    assert gui.TEXT_MEASURED_ZERO in visible_text(gui.value_html(0.0))


def test_tort_holat_matni_HAM_klassi_HAM_turlicha():
    """o'lchanmadi / hali ishga tushirilmadi / manba yo'q / nol -- to'rt xil."""
    outs = {
        "missing": gui.value_html(None),
        "norun": gui.norun_html(),
        "nosource": gui.nosource_html(),
        "zero": gui.value_html(0),
    }
    texts = {k: visible_text(v).strip() for k, v in outs.items()}
    assert len(set(texts.values())) == 4, texts
    classes = {k: re.search(r'class="val ([a-z-]+)"', v).group(1)
               for k, v in outs.items()}
    assert len(set(classes.values())) == 4, classes


def test_uch_holat_matnida_raqam_yoq_toplami():
    """Uchta "qiymat yo'q" matni raqamsiz; faqat NOL son ko'rsatadi."""
    for text in (gui.TEXT_NOT_MEASURED, gui.TEXT_NOT_YET_RUN, gui.TEXT_NO_SOURCE):
        assert not has_digit(text), text


def test_false_olchangan_nol_deb_belgilanMAYDI():
    """`False` -- bool o'lchovi, "o'lchangan nol" EMAS.

    Busiz nima buzilardi: `False == 0` Python'da rost, demak bool nol
    tekshiruvidan oldin ushlanmasa, `False` "o'lchangan nol" bo'lib
    ko'rinardi -- bu esa butunlay boshqa gap.
    """
    out = gui.value_html(False)
    assert gui.TEXT_MEASURED_ZERO not in visible_text(out)
    assert "v-zero" not in out
    assert "yo'q" in visible_text(out)
    assert "ha" in visible_text(gui.value_html(True))


def test_olchanmagan_qiymatda_BIRLIK_ham_bosilmaydi():
    """O'lchanmagan narsaning birligi yo'q -- `unit` jimgina tushadi.

    Busiz nima buzilardi: "o'lchanmadi s" qiymat go'yo mavjud bo'lib
    ko'rinardi va birlik o'lchovning bo'lganini da'vo qilardi.
    """
    assert "s" not in visible_text(gui.value_html(None, unit="s")).replace(
        gui.TEXT_NOT_MEASURED, "")


def test_kb_html_none_uchun_savol_belgisi_BERMAYDI():
    """`cli.human_kb(None)` `"?"` qaytaradi -- GUI uni ISHLATMAYDI.

    `"?"` to'rt holatning qaysi biri ekanini aytmaydi, shuning uchun
    `kb_html` `None` ni aniq "o'lchanmadi" qiladi.
    """
    assert cli.human_kb(None) == "?"
    out = gui.kb_html(None)
    assert "?" not in visible_text(out)
    assert gui.TEXT_NOT_MEASURED in visible_text(out)
    assert not has_digit(visible_text(out))


def test_kb_html_nolni_olchangan_nol_deb_beradi():
    out = gui.kb_html(0)
    assert gui.TEXT_MEASURED_ZERO in visible_text(out)


# ===========================================================================
# 2. Manbada yo'q kalit uchun panel SON O'YLAB CHIQARMAYDI
# ===========================================================================


def _cell_for(markup: str, label: str) -> str:
    """`dl.kv` dagi `label` ning qiymat yacheykasi (`<dd>`) ni qaytaradi."""
    pattern = re.compile(
        r"<dt>" + re.escape(html_mod.escape(label, quote=True)) + r"</dt><dd>(.*?)</dd>",
        re.S)
    m = pattern.search(markup)
    assert m is not None, f"{label!r} yacheykasi topilmadi"
    return m.group(1)


def test_memory_kartasi_yoq_kalit_uchun_SON_YOZMAYDI():
    """`mem_total_kb` manbada YO'Q -> o'sha yacheykada raqam bo'lmaydi.

    Busiz nima buzilardi: yetishmagan kalit uchun `0` yoki oxirgi ma'lum
    qiymat bosilsa, ekranda manbada MAVJUD BO'LMAGAN son paydo bo'lardi --
    aynan qoida 1 taqiqlagan narsa.
    """
    live = {"health": {"memory": {"mem_available_kb": 4096}}, "status": {}}
    out = gui.card_memory(live)

    total_cell = _cell_for(out, "MemTotal")
    assert not has_digit(visible_text(total_cell)), visible_text(total_cell)
    assert "v-missing" in total_cell

    # Mavjud kalit esa HAQIQIY qiymatini ko'rsatadi (test o'zini sinaydi).
    avail_cell = _cell_for(out, "MemAvailable")
    assert has_digit(visible_text(avail_cell))


def test_memory_kartasi_butunlay_bosh_manbada_birorta_son_bermaydi():
    """Manba butunlay bo'sh -> kartada BIRORTA o'lchov soni yo'q."""
    out = gui.card_memory({})
    for label in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree",
                  "eksperiment uchun kerak"):
        cell = _cell_for(out, label)
        assert not has_digit(visible_text(cell)), (label, visible_text(cell))


def test_psi_jadvali_yoq_resurs_uchun_tezlik_OYLAB_CHIQARMAYDI():
    """Scope resursni bermagan -> tezlik "o'lchanmadi", nol EMAS."""
    psi = {"scopes": {"host": {"resources": {"cpu": None, "io": None,
                                             "memory": None}}}}
    rows = gui._psi_scope_rows(psi)
    assert rows, "scope qatorlari yasalmadi"
    for row in rows:
        for cell in row[2:]:
            assert not has_digit(visible_text(cell)), visible_text(cell)
            assert "v-missing" in cell


def test_psi_jadvali_nol_tezlikni_NOL_deb_beradi():
    """`0.0` tezlik -- o'lchangan nol, "o'lchanmadi" EMAS.

    Busiz nima buzilardi: nol stall "o'lchanmadi" deb ko'rsatilsa,
    pressure YO'Q holati pressure O'LCHANMAGAN holatidan ajralmay qolardi --
    H1 uchun bu ikkisi butunlay boshqa xulosa.
    """
    psi = {"scopes": {"host": {"resources": {
        "cpu": {"some_rate": 0.0, "full_rate": 0.0, "window_us": 2_000_000},
        "io": None, "memory": None}}}}
    rows = gui._psi_scope_rows(psi)
    cpu_row = next(r for r in rows if "cpu" in visible_text(r[1]))
    assert gui.TEXT_MEASURED_ZERO in visible_text(cpu_row[2])
    assert gui.TEXT_NOT_MEASURED not in visible_text(cpu_row[2])


def test_disk_va_tarmoq_MANBA_YOQ_deb_beriladi_son_bilan_emas():
    """DISK va NETWORK -- birorta modul chiqarmaydi, demak "manba yo'q".

    Bu `None` ham, `0` ham emas: maydonni ishlab chiqaradigan KOD yo'q.
    Uchinchi holat shuning uchun bor.
    """
    for card, labels in ((gui.card_disk({}), ("sig'im / band",
                                              "o'qish / yozish tezligi")),
                         (gui.card_network({}), ("interfeyslar", "bayt / paket"))):
        for label in labels:
            cell = _cell_for(card, label)
            assert "v-nosource" in cell, (label, cell)
            assert gui.TEXT_NO_SOURCE in visible_text(cell)
            assert not has_digit(visible_text(cell))


def test_cpu_kartasi_foydalanish_foizini_IXTIRO_QILMAYDI():
    """CPU % ni birorta modul o'lchamaydi -> "manba yo'q", foiz EMAS.

    Busiz nima buzilardi: PSI stall ulushini "CPU %" deb ko'rsatish --
    GUI ichida statistika hisoblash (qoida 4) va ikki boshqa o'lchovni
    bir deb atash bo'lardi.
    """
    cell = _cell_for(gui.card_cpu({}), "foydalanish %")
    assert "v-nosource" in cell
    assert not has_digit(visible_text(cell))


def test_MISSING_SOURCES_har_biri_NIMA_va_NEGA_ni_aytadi():
    """Har "manba yo'q" yozuvi sababni AYTADI -- bo'sh e'tirof emas."""
    assert set(gui.MISSING_SOURCES) >= {"cpu_utilization", "disk", "network"}
    for key, (what, why) in gui.MISSING_SOURCES.items():
        assert what.strip(), key
        assert len(why) > 80, f"{key}: sabab juda qisqa"


def test_run_meta_governor_None_holida_qoladi_nolga_aylanmaydi():
    """§15.4: `governor`/`scaling_driver` = `None` (o'lchanmadi), `0` EMAS.

    Bu muhitda `cpufreq` sysfs interfeysi umuman yo'q. `0` bosilsa u
    "o'lchandi va nolga teng" degan YOLG'ON bo'lardi.
    """
    run = {"run_meta": {"run_id": "r1", "governor": None,
                        "scaling_driver": None}}
    out = gui.panel_run_meta(run, LIVE_SRC, NOW)
    for label in ("governor", "scaling_driver"):
        cell = _cell_for(out, label)
        assert "v-missing" in cell, label
        assert not has_digit(visible_text(cell)), label


# ===========================================================================
# 3. §16.4 -- eksklyuziya darajasi to'plamini NOMLASHI SHART
# ===========================================================================


def test_toplami_nomlanmagan_eksklyuziya_darajasi_KORSATILMAYDI():
    """`rate` bor, `rate_set` yo'q -> SON BOSILMAYDI (§16.4).

    `PREREGISTRATION.md` §16.4: *"Nomlanmagan eksklyuziya darajasi
    takrorlanuvchi emas va natija sifatida berilmaydi."* Binar `P(VR)`
    maxraji bilan survival analiz to'plami turli darajalar beradi, demak
    nomsiz raqam qaysi savolga javob berayotgani ma'lum emas.
    """
    out = gui.exclusion_rate_html({"rate": 0.3737, "by_reason": {}})
    text = visible_text(out)
    assert "0.3737" not in text
    assert "3737" not in text
    assert "37" not in text
    # Va sabab AYTILADI -- jimgina tushirib qoldirilmaydi.
    assert "16.4" in text
    assert "rate_set" in text


def test_nomlangan_eksklyuziya_darajasi_KORSATILADI_nomi_bilan():
    out = gui.exclusion_rate_html({
        "rate": 0.25, "rate_set": "binary_p_vr_denominator",
        "n_total": 40, "n_excluded": 10, "n_primary": 30, "by_reason": {},
    })
    text = visible_text(out)
    assert "0.250" in text
    assert "binary_p_vr_denominator" in text


def test_ikki_toplam_ALOHIDA_qator_boladi_va_har_biri_nomlangan():
    """§16.4: ikki to'plam ikki daraja -- bitta `rate` yetarli EMAS."""
    out = gui.exclusion_rate_html({
        "rate": 0.2, "rate_set": "binary_p_vr_denominator",
        "by_set": {
            "binary_p_vr_denominator": {
                "set": "binary_p_vr_denominator", "description": "binar maxraj",
                "rate": 0.2, "n_total": 50, "n_included": 40, "n_excluded": 10},
            "survival_analysis_set": {
                "set": "survival_analysis_set", "description": "survival to'plami",
                "rate": 0.1, "n_total": 50, "n_included": 45, "n_excluded": 5},
        },
    })
    text = visible_text(out)
    assert "binary_p_vr_denominator" in text
    assert "survival_analysis_set" in text
    assert "0.200" in text and "0.100" in text


def test_eksklyuziya_darajasi_NATIJA_deb_aytiladi():
    """§12: yuqori eksklyuziya darajasi o'zi natija -- yashirilmaydi."""
    text = visible_text(gui.exclusion_rate_html({"by_reason": {}}))
    assert "natija" in text.lower()


def test_fr_a_asosi_yoq_bolsa_raqami_KORSATILMAYDI():
    """Shartnoma §3.1: `fr_a.basis` yo'q -> FR-A raqami bosilmaydi.

    Asossiz nisbat talqin qilinmaydi (§2.9a): qaysi denominator
    ishlatilgani ma'lum bo'lmaganda son o'zi hech narsa aytmaydi.
    """
    analysis = {
        "primary": {"endpoint": "e"},
        "false_recovery": {"fr_a": {"per_action": 0.4242, "basis": None},
                           "fr_b": {"computed": False, "reason": "no matrix"}},
    }
    ctx = make_ctx()
    out = gui.page_research_metrics(_ctx_with_analysis(ctx, analysis))
    text = visible_text(out)
    assert "0.4242" not in text
    assert "4242" not in text
    assert "basis" in text


def _ctx_with_analysis(ctx: gui.Context, analysis: dict) -> gui.Context:
    """`derived()` ni berilgan `analysis` bilan almashtiradi (I/O yo'q)."""
    src = gui.Source(kind="derived", name="test analysis.json", read_real_us=NOW)
    data = {"run_dir": "/t", "analysis": analysis, "analysis_path": "/t/analysis.json",
            "analysis_error": None,
            "figures": {n: {"svg_exists": False, "svg_path": None,
                            "sidecar": None, "sidecar_error": None}
                        for n in gui.FIGURE_NAMES}}
    ctx.gw.derived = lambda: (data, src)          # type: ignore[method-assign]
    ctx.gw.run = lambda: (None, src)              # type: ignore[method-assign]
    return ctx


def test_vaqt_birligi_elon_qilinmasa_sekundga_AYLANTIRILMAYDI():
    """Shartnoma §3.1: `time_unit` yo'q -> birlik TAXMIN QILINMAYDI."""
    analysis = {
        "primary": {"endpoint": "e"},
        "false_recovery": {"fr_a": {"basis": "per_action"}},
        "downtime": {"d_probe": {"median": 1500.0, "p90": 2000.0, "p99": 2500.0}},
    }
    out = gui.page_research_metrics(_ctx_with_analysis(make_ctx(), analysis))
    text = visible_text(out)
    assert "birlik" in text.lower()
    assert "taxmin" in text.lower()


# ===========================================================================
# 4. Sintetik fixture RENDERLANGAN CHIQISHDA belgilanadi
# ===========================================================================


def test_sintetik_run_EKRANDA_sintetik_deb_belgilanadi(tmp_path):
    """Sintetik run -> sahifada banner, panelda ramka belgisi.

    Busiz nima buzilardi: "bu fixture" degan izoh kodda qoladi, skrinshot
    esa izohsiz tarqaydi -- va soxta raqam haqiqiy natija bo'lib yuradi.
    """
    run_dir = tmp_path / "synthetic-run"
    run_dir.mkdir()
    (run_dir / "run_meta.json").write_text(
        json.dumps({"run_id": "SYNTHETIC-FIXTURE", "synthetic": True}),
        encoding="utf-8")
    (run_dir / "SYNTHETIC").write_text("qo'lda yasalgan fixture\n", encoding="utf-8")

    opts = make_opts(datasets_dir=str(tmp_path))
    ctx = make_ctx(opts)
    run, src = ctx.gw.run()
    assert src.synthetic is True

    page = gui.render_page("recovery-events", ctx)
    text = visible_text(page)
    assert gui.SYNTHETIC_INLINE_TEXT in text
    assert "HAQIQIY O'LCHOV EMAS" in text
    assert "synthetic-banner" in page
    assert "panel synthetic" in page


def test_sintetik_belgisi_FAQAT_QOSHILADI_hech_qachon_olinmaydi(tmp_path):
    """`--mark-synthetic` belgi QO'SHADI; `synthetic: false` uni OLMAYDI.

    Busiz nima buzilardi: biror flag ogohlikni o'chira olsa, "sintetik
    emas" deb belgilangan sintetik ma'lumot paydo bo'lishi mumkin bo'lardi.
    """
    # Hech qanday belgi yo'q -> sintetik emas.
    assert gui.is_synthetic_run("", {"synthetic": False}, forced=False) is False
    # Flag belgilaydi, `run_meta` ni inkor qila OLMAYDI.
    assert gui.is_synthetic_run("", {"synthetic": False}, forced=True) is True
    # `run_meta` o'zi ham yetarli.
    assert gui.is_synthetic_run("", {"synthetic": True}, forced=False) is True
    # Katalogdagi marker fayl ham yetarli.
    d = tmp_path / "r"
    d.mkdir()
    (d / "SYNTHETIC").write_text("x", encoding="utf-8")
    assert gui.is_synthetic_run(str(d), {}, forced=False) is True


def test_mark_synthetic_flagi_butun_sahifani_belgilaydi():
    """`--mark-synthetic` run bo'lmasa ham sahifani belgilaydi."""
    ctx = make_ctx(make_opts(mark_synthetic=True))
    page = gui.render_page("policies", ctx)
    assert gui.SYNTHETIC_INLINE_TEXT in visible_text(page)


# ===========================================================================
# 5. Server LOOPBACK'ga bog'lanadi
# ===========================================================================


def test_default_bind_loopback():
    """Default `127.0.0.1` -- bu server tirik tizim holatini o'qiydi."""
    assert gui.DEFAULT_HOST == "127.0.0.1"
    assert gui.is_loopback(gui.DEFAULT_HOST) is True
    assert gui.Options().host == gui.DEFAULT_HOST
    assert gui.build_parser().parse_args([]).host == "127.0.0.1"


def test_loopback_bolmagan_bind_RAD_ETILADI():
    """`--allow-remote` siz loopback bo'lmagan bind -- xato, server yo'q.

    Busiz nima buzilardi: bu server cgroup, PSI, unit holati, muhit
    fingerprint'i va journal satrlarini beradi; tarmoqqa ochilgan nusxa
    o'lchanayotgan mashina haqida hamma narsani oshkor qilardi.
    """
    for host in ("0.0.0.0", "192.168.1.10", "::"):
        with pytest.raises(ValueError, match="loopback"):
            gui.make_server(make_opts(host=host))


def test_noanniq_host_loopback_DEB_HISOBLANMAYDI():
    """Noma'lum nom loopback emas (fail-closed, `cli.py` qoida 3 ruhi)."""
    for host in ("example.com", "", "revix.local", "0177.0.0.1"):
        assert gui.is_loopback(host) is False, host
    for host in ("127.0.0.1", "::1", "localhost", "127.5.5.5"):
        assert gui.is_loopback(host) is True, host


def test_loopback_bind_ochiladi_va_yopiladi():
    """Loopback bind HAQIQATAN ochiladi (port 0 -- kernel tanlaydi)."""
    srv = gui.make_server(make_opts(port=0))
    try:
        host, port = srv.server_address[0], srv.server_address[1]
        assert host == "127.0.0.1"
        assert port > 0
    finally:
        srv.server_close()


def test_faqat_GET_qollanadi():
    """Server FAQAT O'QIYDI (qoida 9): POST handler'i YO'Q."""
    assert hasattr(gui.GuiHandler, "do_GET")
    assert not hasattr(gui.GuiHandler, "do_POST")
    assert not hasattr(gui.GuiHandler, "do_PUT")
    assert not hasattr(gui.GuiHandler, "do_DELETE")


# ===========================================================================
# 6. HTML escaping -- fayldan o'qilgan matn MARKUP EMAS
# ===========================================================================

INJECT = "<script>alert('xss')</script>"


def test_run_meta_maydoni_escape_qilinadi():
    """`run_meta.json` maydoni tashqi matn -- `<script>` teg BO'LMAYDI.

    Busiz nima buzilardi: `run_meta` ni driver yozadi, uning ichidagi
    `cpu_model` yoki `run_id` esa tizimdan/konfiguratsiyadan keladi. Teg
    sifatida talqin qilinsa sahifa o'z ma'lumotiga bo'ysunib qolardi.
    """
    run = {"run_meta": {"run_id": INJECT, "cpu_model": INJECT,
                        "governor": None, "scaling_driver": None}}
    out = gui.panel_run_meta(run, LIVE_SRC, NOW)
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    # Matn YO'QOLMAYDI -- escape qilinadi, tushirib qoldirilmaydi.
    assert INJECT in visible_text(out)


def test_journal_satri_escape_qilinadi():
    """`guard.jsonl` satri ISHONCHSIZ matn (mustaqil guard jarayoni yozadi)."""
    run = {"guard_lines": [INJECT, '{"record_type": "guard_start"}'],
           "guard_error": None}
    out = gui.panel_logs(run, LIVE_SRC, NOW)
    assert "<script>" not in out
    assert "&lt;script&gt;" in out
    assert INJECT in visible_text(out)


def test_events_record_payloadi_escape_qilinadi():
    """`events.jsonl` record'i xom JSON sifatida ko'rsatiladi -- escape bilan."""
    events = {"file": INJECT, "count": 1, "total_lines": 1, "matched": 1,
              "truncated_tail": False, "bad_lines": [], "types": {INJECT: 1},
              "records": [{"seq": 1, "mono_us": 5, "record_type": INJECT,
                           "trial_id": INJECT, "payload": {"k": INJECT}}]}
    out = gui.panel_events({"events": events}, LIVE_SRC, NOW)
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_unit_nomi_escape_qilinadi():
    """`systemctl` chiqishidagi unit nomi ham tashqi matn."""
    live = {"status": {"units": {"ok": True, "units": [
        {"name": INJECT, "load": "loaded", "active": "active", "sub": "running"}]}}}
    out = gui.panel_services(live, LIVE_SRC, NOW)
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_doctor_kuzatilgan_qiymati_escape_qilinadi():
    """Doctor `observed` maydoni subprocess chiqishidan keladi."""
    doctor = {"summary": {"total": 1, "pass": 1, "warn": 0, "fail": 0, "ok": True},
              "checks": [{"key": "k", "status": "PASS", "observed": INJECT,
                          "required": INJECT, "consequence": INJECT}]}
    out = gui.panel_doctor(doctor, LIVE_SRC, NOW)
    assert "<script>" not in out
    assert "&lt;script&gt;" in out


def test_esc_atribut_uchun_ham_xavfsiz():
    """`esc()` `quote=True` -- qiymat atribut ichiga tushsa ham xavfsiz."""
    assert gui.esc('" onload="x') == "&quot; onload=&quot;x"
    assert gui.esc("a&b") == "a&amp;b"


def test_bosh_satr_olchanmadi_DEB_KORSATILMAYDI():
    """Bo'sh satr o'qildi va bo'sh edi -- bu "o'lchanmadi" EMAS."""
    out = gui.text_html("")
    assert gui.TEXT_NOT_MEASURED not in visible_text(out)
    assert "v-missing" not in out
    assert gui.TEXT_NOT_MEASURED in visible_text(gui.text_html(None))


# ===========================================================================
# 7. "Hali ishga tushirilmadi" holati ATAYLAB shunday ko'rinadi
# ===========================================================================


def test_run_yoq_holatida_hodisa_paneli_HALI_ISHGA_TUSHIRILMADI_deydi():
    """Run yo'q -> "hali ishga tushirilmadi", "o'lchanmadi" EMAS.

    Ikkisi boshqa gap: biri artifact YO'Q, ikkinchisi artifact bor-u
    maydon o'lchanmagan. Ularni aralashtirish o'quvchini mavjud bo'lmagan
    natijani qidirishga majburlaydi.
    """
    out = gui.panel_events(None, gui.Source("artifact", "run yo'q"), NOW)
    text = visible_text(out)
    assert gui.TEXT_NOT_YET_RUN in text
    # Manbani NOMLAYDI va qanday hosil qilishni aytadi.
    assert "events.jsonl" in text
    assert "revix" in text


def test_recovery_engine_paneli_REVIX_QARORI_DEB_DAVO_QILMAYDI():
    """§13: arm C muzlatilmagan -> adaptiv engine YO'Q, atributsiya systemd'ga.

    Busiz nima buzilardi: "RECOVERY ENGINE" sarlavhasi ostidagi panel
    REVIX bir qaror qabul qilganini ko'rsatardi, lekin bunday kod yo'q --
    bu esa mavjud bo'lmagan hissani da'vo qilish bo'lardi.
    """
    out = gui.panel_recovery_engine(None, gui.Source("artifact", "run yo'q"), NOW)
    text = visible_text(out)
    assert "adaptiv recovery engine YO'Q" in text
    assert "§13" in text
    assert "SYSTEMD" in text


def test_recovery_siyosatlari_arm_C_ni_YOQ_deb_beradi():
    """Arm C -- siyosat muzlatilmagan, demak "manba yo'q" (ixtiro emas)."""
    text = visible_text(gui.page_policies(make_ctx()))
    assert "Restart=on-failure" in text
    assert "RestartSec=100ms" in text
    assert "Restart=no" in text
    assert "MUZLATILMAGAN" in text
    assert gui.TEXT_NO_SOURCE in text


def test_arm_konfiguratsiyalari_README_bilan_mos():
    """A / B / no_action mavjud, C esa `config=None` (yo'q)."""
    by_arm = {a["arm"]: a for a in gui.ARM_CONFIGS}
    assert by_arm["A"]["config"] == "Restart=on-failure, RestartSec=100ms"
    assert by_arm["no_action"]["config"] == "Restart=no"
    assert "RestartSteps=4" in by_arm["B"]["config"]
    assert by_arm["C"]["config"] is None


def test_barcha_on_ikki_sahifa_royxatda_va_slug_lari_yagona():
    assert len(gui.PAGES) == 12
    slugs = [p.slug for p in gui.PAGES]
    assert len(set(slugs)) == 12
    assert "" in slugs          # dashboard ildizda
    for p in gui.PAGES:
        assert p.needs, f"{p.slug}: manba e'lon qilinmagan"
        assert p.intro.strip(), f"{p.slug}: tavsif yo'q"


def test_manbasi_yoq_sahifa_NAVIGATSIYADA_belgilanadi():
    """Bugun manbasi yo'q sahifa nav'da `empty-page` bilan belgilanadi.

    NEGA: bo'sh sahifani kutilmaganda ko'rish "buzilgan" degan taassurot
    beradi; nav'dagi belgi bosishdan OLDIN aytadi.
    """
    nav = gui.nav_html("", have={"document", "config"})
    assert 'class="empty-page"' in nav
    # `run`/`derived` manbasi yo'q -> o'sha sahifalar belgilanadi.
    assert nav.count("empty-page") >= 4


# ===========================================================================
# 8. Manba va eskirish (QOIDA 3)
# ===========================================================================


def test_har_panel_manbasini_va_oqilgan_vaqtini_AYTADI():
    out = gui.panel("TEST", LIVE_SRC, "x", NOW)
    assert 'class="source' in out
    assert "1 TIRIK" in visible_text(out)
    assert "test" in visible_text(out)
    assert 'data-read-real-us="%d"' % NOW in out


def test_eskirgan_oqish_ESKIRGAN_korinadi_javascript_SIZ_ham():
    """`stale` klassi SERVER tomonida qo'yiladi (JS o'chirilgan bo'lsa ham)."""
    old = gui.Source("live", "test", read_real_us=NOW - int(
        (gui.STALE_AFTER_S + 5) * 1e6))
    fresh = gui.Source("live", "test", read_real_us=NOW)
    assert old.is_stale(NOW) is True
    assert fresh.is_stale(NOW) is False
    assert "source stale" in gui.panel("T", old, "x", NOW)
    assert "source stale" not in gui.panel("T", fresh, "x", NOW)


def test_oqilmagan_manba_vaqt_DAVO_QILMAYDI():
    """O'qish bo'lmagan manba yoshi `None` -- `stale` ham emas, yangi ham emas."""
    src = gui.Source("artifact", "run yo'q")
    assert src.age_s(NOW) is None
    assert src.is_stale(NOW) is False
    assert "o'qilmadi" in visible_text(gui.panel("T", src, "x", NOW))


def test_manba_ishonch_darajalari_tartiblangan():
    """1 tirik > 2 artifact > 3 derived -- ishonch tartibi ekranda ko'rinadi."""
    assert gui.SOURCE_TIERS["live"].startswith("1")
    assert gui.SOURCE_TIERS["artifact"].startswith("2")
    assert gui.SOURCE_TIERS["derived"].startswith("3")


def test_live_oqish_xatosi_JIM_QOLMAYDI(monkeypatch):
    """`status_report()` istisno tashlasa -- manba xatoni AYTADI (fail-closed)."""
    def boom(*_a, **_k):
        raise RuntimeError("psi o'qilmadi")
    monkeypatch.setattr(cli, "status_report", boom)
    gw = gui.Gateway(make_opts())
    data, src = gw.live()
    assert src.error is not None
    assert "psi o'qilmadi" in src.error
    assert src.read_real_us is None
    assert "o'qish xatosi" in visible_text(gui.panel("T", src, "x", NOW))
    assert data == {}


# ===========================================================================
# 9. Gateway -- fayl o'qish (hisoblash YO'Q)
# ===========================================================================


def test_run_meta_json_yoq_katalog_RUN_HISOBLANMAYDI(tmp_path):
    """`run_meta.json` yo'q katalog run sifatida KO'RSATILMAYDI (§1.1).

    Busiz nima buzilardi: bo'sh yoki yarim katalog run bo'lib ko'rinardi va
    dashboard mavjud bo'lmagan run'ni mavjud deb ko'rsatardi.
    """
    (tmp_path / "bosh-katalog").mkdir()
    (tmp_path / "yarim").mkdir()
    (tmp_path / "yarim" / "events.jsonl").write_text("", encoding="utf-8")
    assert gui.discover_run_dirs(str(tmp_path)) == []

    (tmp_path / "haqiqiy").mkdir()
    (tmp_path / "haqiqiy" / "run_meta.json").write_text("{}", encoding="utf-8")
    assert gui.discover_run_dirs(str(tmp_path)) == [
        str(tmp_path / "haqiqiy")]


def test_datasets_katalogi_yoq_bolsa_run_YOQ_xato_emas():
    """`datasets/` bo'lmasa -- "run yo'q", istisno EMAS."""
    gw = gui.Gateway(make_opts(datasets_dir="/aniq-mavjud-bolmagan-yol"))
    run, src = gw.run()
    assert run is None
    assert src.read_real_us is None
    assert "run yo'q" in src.name


def test_buzuq_analysis_json_SABABI_BILAN_aytiladi(tmp_path):
    """Buzuq JSON -- jim tushirilmaydi, sabab manbada ko'rinadi."""
    run_dir = tmp_path / "r"
    run_dir.mkdir()
    (run_dir / "run_meta.json").write_text("{}", encoding="utf-8")
    (run_dir / "analysis.json").write_text("{buzuq", encoding="utf-8")
    gw = gui.Gateway(make_opts(datasets_dir=str(tmp_path)))
    derived, src = gw.derived()
    assert derived["analysis"] is None
    assert "buzuq JSON" in (src.error or "")


def test_figura_nomlari_figures_py_dan_olinadi():
    """Figura ro'yxati `figures.py` ning YAGONA manbasidan (qayta yozilmaydi)."""
    from revix import figures
    assert gui.FIGURE_NAMES is figures.FIGURE_NAMES
    assert len(gui.FIGURE_NAMES) == 6


def test_figura_svg_i_yoq_bolsa_HALI_ISHGA_TUSHIRILMADI():
    """SVG yo'q -> "hali ishga tushirilmadi"; bo'sh o'q CHIZILMAYDI."""
    derived = {"analysis_path": "/t/analysis.json", "figures": {
        n: {"svg_exists": False, "svg_path": None, "sidecar": None,
            "sidecar_error": None} for n in gui.FIGURE_NAMES}}
    out = gui.panel_figures(derived, LIVE_SRC, NOW)
    text = visible_text(out)
    assert text.count(gui.TEXT_NOT_YET_RUN) >= len(gui.FIGURE_NAMES)
    assert "<img" not in out


# ===========================================================================
# 10. Aktivlar va marshrutlash
# ===========================================================================


def test_aktivlar_mavjud_va_rang_FAQAT_css_da():
    """Rang AYNAN bitta joyda -- `style.css` `:root` (branding almashtirishi).

    Busiz nima buzilardi: markup'ga tarqagan literal rang brendni
    almashtirishni butun GUI ni qayta yozishga aylantirardi.
    """
    files = gui._asset_files()
    assert "style.css" in files
    assert "app.js" in files
    css = open(files["style.css"], encoding="utf-8").read()
    for token in ("--revix-black-0", "--revix-red", "--revix-green",
                  "--color-critical", "--color-healthy"):
        assert token in css, token
    # Markup'da va skriptda hex rang YO'Q.
    py = open(os.path.join(gui.PKG_DIR, "gui.py"), encoding="utf-8").read()
    js = open(files["app.js"], encoding="utf-8").read()
    assert not re.search(r"#[0-9a-fA-F]{6}\b", py)
    assert not re.search(r"#[0-9a-fA-F]{6}\b", js)


def test_css_da_gradient_glow_va_animatsiya_YOQ():
    """Taqiqlangan estetika: gradient, glow, animatsiya (neon/cyberpunk emas).

    IZOHLAR OLIB TASHLANADI: `style.css` ning dizayn qoidalari AYNAN shu
    taqiqlangan atamalarni nomlab taqiqlaydi, demak izohda ular uchraydi.
    Qoida DEKLARATSIYALARGA tegishli, prozaga emas.
    """
    raw = open(gui._asset_files()["style.css"], encoding="utf-8").read()
    css = re.sub(r"/\*.*?\*/", " ", raw, flags=re.S).lower()
    assert "--revix-black-0" in css, "izoh olib tashlash qoidalarni ham yedi"
    for banned in ("gradient", "box-shadow", "text-shadow", "@keyframes",
                   "animation:", "transition:"):
        assert banned not in css, banned


def test_yangi_boglliqlik_YOQ_faqat_stdlib():
    """`gui.py` faqat stdlib + `revix` ichidan import qiladi (CONTRIBUTING §4)."""
    py = open(os.path.join(gui.PKG_DIR, "gui.py"), encoding="utf-8").read()
    imports = set(re.findall(r"^import (\w+)", py, re.M))
    imports |= set(re.findall(r"^from ([\w.]+) import", py, re.M))
    allowed = {"argparse", "html", "http", "http.server", "ipaddress", "json",
               "os", "shutil", "socket", "sys", "time", "dataclasses",
               "typing", "__future__", ".", ".figures"}
    assert imports <= allowed, imports - allowed
    # Tashqi havola ham yo'q (offline ishlashi SHART): CDN yo'q, font
    # havolasi yo'q, `@import` yo'q.
    for name, path in gui._asset_files().items():
        text = open(path, encoding="utf-8").read()
        assert "http://" not in text, name
        assert "https://" not in text, name
        assert "cdn" not in text.lower(), name
        assert "@import" not in text.lower(), name


def test_sahifa_HTML_i_CSP_self_bilan_beriladi():
    """CSP `self` -- CDN mumkin emas, ya'ni offline ishlash STRUKTURAVIY."""
    page = gui.render_page("about", make_ctx())
    assert "Content-Security-Policy" in page
    assert "default-src 'self'" in page
    assert "https://" not in page.split("</head>")[0]


def test_render_page_barcha_sahifalar_uchun_ishlaydi(tmp_path):
    """O'n ikki sahifa ham renderlanadi (run yo'q holatda ham)."""
    opts = make_opts(datasets_dir=str(tmp_path))
    for page in gui.PAGES:
        ctx = make_ctx(opts)
        # `live()` va `doctor()` ni soxtalashtirmaymiz -- bo'sh dict ham
        # yetadi, chunki renderlar yo'q kalitga chidamli bo'lishi SHART.
        ctx.gw.live = lambda: ({}, LIVE_SRC)       # type: ignore[method-assign]
        ctx.gw.doctor = lambda: (None, LIVE_SRC)   # type: ignore[method-assign]
        out = gui.render_page(page.slug, ctx)
        assert out.startswith("<!doctype html>")
        assert "REVIX" in out


def test_bosh_manba_bilan_renderlangan_sahifa_SON_IXTIRO_QILMAYDI(tmp_path):
    """Manba butunlay bo'sh -> panellarda o'lchov soni YO'Q, so'z bor."""
    opts = make_opts(datasets_dir=str(tmp_path))
    ctx = make_ctx(opts)
    ctx.gw.live = lambda: ({}, LIVE_SRC)           # type: ignore[method-assign]
    out = gui.render_page("", ctx)
    # MemTotal / MemAvailable yacheykalarida raqam bo'lmaydi.
    for label in ("MemTotal", "MemAvailable", "CPU soni"):
        cell = _cell_for(out, label)
        assert not has_digit(visible_text(cell)), (label, visible_text(cell))


def test_404_sahifasi_halol_va_HTML():
    ctx = make_ctx()
    out = gui.render_not_found("/yoq-sahifa", ctx)
    assert out.startswith("<!doctype html>")
    assert "/yoq-sahifa" in visible_text(out)


def test_figura_marshruti_whitelist_bilan_cheklangan():
    """Figura nomi FAQAT `FIGURE_NAMES` dan -- so'rov matni yo'lga aylanmaydi."""
    assert "../../etc/passwd" not in gui.FIGURE_NAMES
    assert "p_vr_vs_pressure" in gui.FIGURE_NAMES


def test_aktiv_marshruti_whitelist_katalog_royxatidan():
    """Aktiv nomi katalogning O'Z ro'yxatidan keladi (path traversal yo'q)."""
    files = gui._asset_files()
    assert "../gui.py" not in files
    assert all("/" not in name and "\\" not in name for name in files)


# ===========================================================================
# 11. main() shartnomasi
# ===========================================================================


def test_main_imzosi_va_modul_sifatida_ishlashi():
    """`main(argv=None) -> int` va `python3 -m revix.gui` ishlaydi."""
    import inspect
    sig = inspect.signature(gui.main)
    assert list(sig.parameters) == ["argv"]
    assert sig.parameters["argv"].default is None
    assert sig.return_annotation in (int, "int")
    # `-m` uchun `__main__` gate'i bo'lishi SHART.
    py = open(os.path.join(gui.PKG_DIR, "gui.py"), encoding="utf-8").read()
    assert 'if __name__ == "__main__":' in py
    assert "sys.exit(main())" in py


def test_main_loopback_bolmagan_bindda_NONZERO_qaytaradi(capsys):
    rc = gui.main(["--host", "0.0.0.0", "--port", "0"])
    assert rc == 1
    assert "loopback" in capsys.readouterr().err


def test_main_render_to_barcha_sahifalarni_yozadi(tmp_path):
    """`--render-to` serverni ochmasdan statik HTML yozadi (vizual tekshiruv)."""
    out_dir = tmp_path / "out"
    rc = gui.main(["--render-to", str(out_dir),
                   "--datasets", str(tmp_path / "yoq")])
    assert rc == 0
    assert (out_dir / "index.html").is_file()
    assert (out_dir / "about.html").is_file()
    assert (out_dir / "assets" / "style.css").is_file()
    # Statik faylda aktiv havolasi NISBIY bo'lishi SHART (ildiz yo'q).
    text = (out_dir / "index.html").read_text(encoding="utf-8")
    assert 'href="assets/style.css"' in text
    assert 'href="/assets/' not in text
    assert len(list(out_dir.glob("*.html"))) == len(gui.PAGES)


def test_server_HAQIQATAN_loopbackda_javob_beradi(tmp_path):
    """Uchidan-uchiga: server ochiladi, `127.0.0.1` dan sahifa va aktiv beriladi.

    `policies` sahifasi tanlangan: uning manbasi HUJJAT, demak PSI uchun
    >= 2 s uxlash shart emas va test tez. Shu bilan birga bu HAQIQIY HTTP
    so'rov -- marshrutlash, sarlavhalar va kodlash tekshiriladi.
    """
    import http.client
    import threading

    opts = make_opts(port=0, datasets_dir=str(tmp_path))
    srv = gui.make_server(opts)
    host, port = srv.server_address[0], srv.server_address[1]
    thread = threading.Thread(target=srv.serve_forever, daemon=True)
    thread.start()
    try:
        conn = http.client.HTTPConnection(host, port, timeout=10)

        conn.request("GET", "/policies")
        resp = conn.getresponse()
        body = resp.read().decode("utf-8")
        assert resp.status == 200
        assert resp.getheader("Content-Type") == "text/html; charset=utf-8"
        # Kesh YO'Q: keshlangan sahifa o'z o'qish vaqtini yolg'on qilardi.
        assert resp.getheader("Cache-Control") == "no-store"
        assert resp.getheader("X-Content-Type-Options") == "nosniff"
        assert body.startswith("<!doctype html>")
        assert "Restart=on-failure" in visible_text(body)

        conn.request("GET", "/assets/style.css")
        resp = conn.getresponse()
        css = resp.read().decode("utf-8")
        assert resp.status == 200
        assert resp.getheader("Content-Type") == "text/css; charset=utf-8"
        assert "--revix-black-0" in css

        # Noma'lum yo'l -- 404, lekin HALOL HTML sahifa.
        conn.request("GET", "/aniq-yoq-sahifa")
        resp = conn.getresponse()
        nf = resp.read().decode("utf-8")
        assert resp.status == 404
        assert nf.startswith("<!doctype html>")

        # Path traversal -- aktiv sifatida BERILMAYDI.
        conn.request("GET", "/assets/../gui.py")
        resp = conn.getresponse()
        resp.read()
        assert resp.status in (301, 400, 404), resp.status

        conn.close()
    finally:
        srv.shutdown()
        srv.server_close()
        thread.join(timeout=10)


def test_parser_default_qiymatlari():
    args = gui.build_parser().parse_args([])
    assert args.port == gui.DEFAULT_PORT
    assert args.allow_remote is False
    assert args.mark_synthetic is False
    assert args.interval_s == cli.MIN_RATE_WINDOW_S
    assert args.render_to is None


def test_psi_oynasi_cli_minimumiga_tayanadi():
    """PSI oynasi `cli.MIN_RATE_WINDOW_S` dan -- GUI o'z chegarasini QO'YMAYDI.

    Busiz nima buzilardi: GUI 1 s oyna bersa, `total=` delta'si PSI ning
    2 s ichki kadensidan qisqa bo'lardi va tezlik oniy tezlik bo'lmasdi
    (`PREREGISTRATION.md` §7).
    """
    assert gui.Options().interval_s == cli.MIN_RATE_WINDOW_S
    assert cli.MIN_RATE_WINDOW_S >= 2.0
