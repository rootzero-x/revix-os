"""schema.py testlari -- envelope, seq bo'shliqlarini aniqlash, yozuvchilar."""
import json
import os

import pytest

from revix import schema as S


def test_envelope_barcha_field_lari_bor():
    em = S.Emitter("t", "run1", "sess1", boot_id="boot1")
    env = em.envelope("demo")
    for f in S.ENVELOPE_FIELDS:
        assert f in env, f"envelope'da {f} yo'q"
    assert env["schema_version"] == S.SCHEMA_VERSION
    assert env["boot_id"] == "boot1"
    assert env["emitter"].startswith("t:")


def test_seq_har_oqim_uchun_alohida_monotonik():
    """seq oqim bo'yicha monotonik bo'lishi kerak -- shunda validator
    yo'qolgan record'ni (bo'shliqni) aniqlaydi."""
    em = S.Emitter("t", "r", "s", boot_id="b")
    a = [em.envelope("x", stream="A")["seq"] for _ in range(3)]
    b = [em.envelope("y", stream="B")["seq"] for _ in range(2)]
    assert a == [1, 2, 3]
    assert b == [1, 2]  # B oqimi A dan mustaqil


def test_payload_envelope_ni_bosib_otolmaydi():
    """Jimgina ustiga yozish o'lchovni buzadi -- xato tashlanishi kerak."""
    em = S.Emitter("t", "r", "s", boot_id="b")
    with pytest.raises(ValueError, match="bosib o'tdi"):
        em.record("demo", {"mono_us": 0})
    with pytest.raises(ValueError):
        em.record("demo", {"boot_id": "boshqa"})


def test_monotonic_realtime_dan_mustaqil():
    a = S.mono_us()
    b = S.mono_us()
    assert b >= a
    assert isinstance(S.real_us(), int)


def test_boot_id_oqiladi():
    bid = S.read_boot_id()
    assert len(bid) >= 32


def test_jsonl_har_record_bitta_qator(tmp_path):
    p = tmp_path / "e.jsonl"
    em = S.Emitter("t", "r", "s", boot_id="b")
    with S.JsonlWriter(str(p)) as w:
        for i in range(5):
            w.write(em.record("demo", {"i": i, "matn": "vergul, va \"qoshtirnoq\"\nyangi qator"}))
    lines = p.read_text().splitlines()
    assert len(lines) == 5, "har record aynan bitta qator bo'lishi kerak"
    recs = [json.loads(x) for x in lines]
    assert [r["i"] for r in recs] == [0, 1, 2, 3, 4]
    assert [r["seq"] for r in recs] == [1, 2, 3, 4, 5]
    # Yangi qator JSON ichida escape bo'lishi kerak, qatorni bo'lmasligi kerak
    assert "\n" in recs[0]["matn"]


def test_jsonl_append_only(tmp_path):
    """Qayta ochish mavjud record'larni o'chirmasligi kerak -- datasets/
    append-only."""
    p = tmp_path / "e.jsonl"
    em = S.Emitter("t", "r", "s", boot_id="b")
    with S.JsonlWriter(str(p)) as w:
        w.write(em.record("a", {}))
    with S.JsonlWriter(str(p)) as w:
        w.write(em.record("b", {}))
    assert len(p.read_text().splitlines()) == 2


def test_csv_none_bosh_maydon_boladi(tmp_path):
    """None -> bo'sh maydon. 0 yoki NaN EMAS: ular haqiqiy o'lchov bilan
    aralashib ketardi."""
    p = tmp_path / "s.csv"
    with S.CsvWriter(str(p), ["a", "b", "c"]) as w:
        w.write({"a": 1, "b": None, "c": 2.5})
    lines = p.read_text().splitlines()
    assert lines[0] == "a,b,c"
    assert lines[1] == "1,,2.5"


def test_csv_vergul_va_qoshtirnoq_qochiriladi(tmp_path):
    p = tmp_path / "s.csv"
    with S.CsvWriter(str(p), ["x"]) as w:
        w.write({"x": 'a,b "c"'})
    assert p.read_text().splitlines()[1] == '"a,b ""c"""'


def test_csv_header_faqat_bir_marta(tmp_path):
    p = tmp_path / "s.csv"
    with S.CsvWriter(str(p), ["x"]) as w:
        w.write({"x": 1})
    with S.CsvWriter(str(p), ["x"]) as w:
        w.write({"x": 2})
    lines = p.read_text().splitlines()
    assert lines == ["x", "1", "2"], "qayta ochilganda header takrorlanmasligi kerak"


def test_disposition_enum_yopiq():
    """Yopiq enum jimgina eksklyuziyaning oldini oladi (PREREGISTRATION §12)."""
    assert set(S.DISPOSITIONS) == {
        "complete", "censored", "contaminated",
        "aborted_guard", "washout_timeout", "harness_error",
    }
