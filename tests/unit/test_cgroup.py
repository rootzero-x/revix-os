"""cgroup.py testlari -- PSI parse va stall fraction kvantlash qoidasi."""
import pytest

from revix import cgroup as cg

SAMPLE = """some avg10=1.23 avg60=4.56 avg300=7.89 total=1234567
full avg10=0.10 avg60=0.20 avg300=0.30 total=42
"""


def test_psi_parse():
    psi = cg.parse_psi(SAMPLE)
    assert psi["some"]["avg10"] == 1.23
    assert psi["some"]["total"] == 1234567
    assert psi["full"]["avg300"] == 0.30
    assert psi["full"]["total"] == 42
    assert isinstance(psi["some"]["total"], int)


def test_psi_parse_faqat_some():
    """cpu.pressure ba'zi kernel'larda faqat 'some' beradi."""
    psi = cg.parse_psi("some avg10=0.00 avg60=0.00 avg300=0.00 total=5\n")
    assert set(psi) == {"some"}


def test_psi_parse_tanilmagan_satrda_xato():
    """Jimgina tashlash sxema o'zgarganda o'lchovni jimgina buzardi."""
    with pytest.raises(ValueError, match="tanilmadi"):
        cg.parse_psi("some avg10=0.00 yangi_field=1 total=5\n")


def test_stall_fraction_2s_dan_qisqa_oyna_None():
    """PSI 2 s kadensda partiyalarda kreditlanadi, demak qisqa oyna oniy
    tezlik EMAS (PREREGISTRATION §7 kvantlash ogohligi)."""
    assert cg.stall_fraction(0, 100_000, 0, 100_000) is None   # 100 ms
    assert cg.stall_fraction(0, 100_000, 0, 1_999_999) is None  # 2 s dan bir oz kam


def test_stall_fraction_togri_hisoblanadi():
    # 2 s oynada 1 s stall = 0.5
    assert cg.stall_fraction(0, 1_000_000, 0, 2_000_000) == 0.5
    # 4 s oynada 4 s stall = 1.0 (to'liq stall)
    assert cg.stall_fraction(1_000, 4_001_000, 0, 4_000_000) == 1.0


def test_stall_fraction_teskari_vaqt_None():
    assert cg.stall_fraction(0, 100, 5_000_000, 0) is None


def test_read_text_yoq_fayl_None():
    """None = o'lchov yo'qoldi. 0 EMAS -- 0 haqiqiy o'lchov qiymati."""
    assert cg.read_text("/proc/yoq-bunday-fayl-revix") is None
    assert cg.read_int("/proc/yoq-bunday-fayl-revix") is None


def test_read_int_max_None():
    """cgroup fayllarida 'max' -> chegara yo'q, 0 emas."""
    import tempfile, os
    fd, p = tempfile.mkstemp()
    try:
        os.write(fd, b"max\n"); os.close(fd)
        assert cg.read_int(p) is None
    finally:
        os.unlink(p)


def test_user_child_dash_siz_nom():
    """Slice nomida '-' ierarxiya ajratuvchisi, shuning uchun revixlab/revixmon
    dash'siz (PREREGISTRATION amendment v1 -> v1.1)."""
    p = cg.user_child("revixlab.slice")
    assert p.endswith("/revixlab.slice")
    assert "revix.slice" not in p, "dash'li nom nesting keltiradi"
