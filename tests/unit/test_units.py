"""units.py testlari -- SHU MASHINADAGI HAQIQIY systemd'ga qarshi.

Mock YO'Q. Sabab: bu modul butunlay systemd'ning haqiqiy xatti-harakatiga
tayanadi (property nomlari, tur kodlari, `--collect` tuzog'i, signal
payload'lari). Mock qilingan D-Bus faqat bizning taxminimizni tekshirardi,
systemd'ni emas -- ya'ni aynan buzilishi mumkin bo'lgan narsani sinamagan
bo'lardik.

XAVFSIZLIK QOIDALARI (buzilmaydi):
  * Har unit `revixselftest-` prefiksida, slice `revixselftest.slice`.
    HECH QACHON `revix-*` yoki `revixlab.slice`/`revixmon.slice` emas --
    aks holda parallel ishlayotgan haqiqiy eksperiment run'i yoki boshqa
    agent bilan to'qnashardik.
  * Har unit `RuntimeMaxSec` bilan: test halokatli yiqilsa ham unit o'zi
    o'ladi.
  * Yig'ishtirish FIXTURE'da, testdan oldin VA keyin -- test yiqilganda ham.
"""

import os
import re

import pytest

from revix import units as U

# --- butun modul skip'i -----------------------------------------------------
# Foydalanuvchi D-Bus sessiyasi bo'lmasa bu testlarning ma'nosi yo'q. Sabab
# ANIQ ko'rsatiladi: "o'tdi" va "umuman ishlamadi" bir xil ko'rinmasligi kerak.
_SKIP = U.user_bus_reason()
pytestmark = pytest.mark.skipif(_SKIP is not None, reason=f"user D-Bus yo'q: {_SKIP}")

SELF_SLICE = "revixselftest.slice"
SELF_GLOB = "revixselftest-*"
SELF_PATTERNS = [SELF_GLOB]
SELF_SLICES = [SELF_SLICE]


def _selftest_teardown(sd):
    """FAQAT selftest nomlarini yig'ishtiradi.

    `units.teardown()` default'lari `revixlab.slice`/`revixmon.slice` -- ularni
    testdan turib to'xtatish jonli eksperimentni o'ldirardi, shuning uchun
    bu yerda har doim aniq pattern beriladi.
    """
    return U.teardown(
        systemd=sd,
        unit_patterns=SELF_PATTERNS,
        slices=SELF_SLICES,
        clear_drop_ins=True,
    )


@pytest.fixture
def sd():
    s = U.SystemdUser()
    try:
        yield s
    finally:
        s.close()


@pytest.fixture
def lab(sd):
    """Toza boshlanish va KAFOLATLANGAN yig'ishtirish (test yiqilsa ham)."""
    _selftest_teardown(sd)
    try:
        yield sd
    finally:
        _selftest_teardown(sd)


def unit_props(**over):
    """Test unit'ining property to'plami.

    `RuntimeMaxSec=30` + `Collect=True` -- himoya: test halokatli yiqilib
    fixture ishlamasa ham unit 30 s ichida o'zi o'ladi va yo'qoladi.
    `StandardOutput/Error=null` -- PREREGISTRATION §3.4: journald'ga hech
    narsa oqmaydi.
    """
    p = dict(
        Description="revix selftest",
        Slice=SELF_SLICE,
        MemoryMax="64M",
        MemoryHigh="48M",
        MemorySwapMax=0,
        TasksMax=16,
        CPUQuota="400%",
        Restart="on-failure",
        RestartSec=0.1,
        RestartSteps=4,
        RestartMaxDelaySec="8s",
        StartLimitBurst=0,
        WatchdogSec=30,
        TimeoutStartSec="3s",
        RuntimeMaxSec=30,
        Environment=["REVIX_SELFTEST=1"],
        WorkingDirectory="/tmp",
        Type="exec",
        OOMPolicy="continue",
        Collect=True,
        StandardOutput="null",
        StandardError="null",
        ExecStart=["/bin/sleep", "30"],
    )
    p.update(over)
    return p


# --- sof funksiyalar (D-Bus'siz mantiq) -------------------------------------


def test_bus_label_escape_systemd_bilan_mos():
    """Kuzatilgan haqiqiy obyekt yo'llariga qarshi tekshiruv.

    `_` ning O'ZI ham qochiriladi va raqamlar faqat birinchi belgi bo'lganda --
    systemd'ning `bus_label_escape()` i aynan shunday.
    """
    assert U.bus_label_escape("revixselftest-a.service") == "revixselftest_2da_2eservice"
    assert U.bus_label_escape("-.slice") == "_2d_2eslice"
    assert U.bus_label_escape("a_b") == "a_5fb"
    assert U.bus_label_escape("1a") == "_31a"
    assert (
        U.unit_object_path("revixselftest-a.service")
        == "/org/freedesktop/systemd1/unit/revixselftest_2da_2eservice"
    )


def test_parse_bytes():
    assert U.parse_bytes("64M") == 64 * 1024**2
    assert U.parse_bytes(123) == 123
    assert U.parse_bytes(None) == U.UINT64_MAX
    assert U.parse_bytes("infinity") == U.UINT64_MAX
    with pytest.raises(U.UnitsError):
        U.parse_bytes("olti")


def test_parse_time_us_son_sekund_satr_suffiks():
    """SON -> SEKUND, SATR -> suffiksli. Ikkisi aralashsa o'lchov buzilardi."""
    assert U.parse_time_us(0.1) == 100_000
    assert U.parse_time_us(8) == 8_000_000
    assert U.parse_time_us("100ms") == 100_000
    assert U.parse_time_us("8s") == 8_000_000
    assert U.parse_time_us("500us") == 500
    assert U.parse_time_us("1min") == 60_000_000
    assert U.parse_time_us("infinity") == U.UINT64_MAX
    with pytest.raises(U.UnitsError):
        U.parse_time_us("8 parsek")


def test_cpu_quota_foizdan_us_per_sec():
    """`CPUQuota=400%` -> 4_000_000 us/s (bu mashinada tekshirilgan: '4s')."""
    assert U.parse_cpu_quota_us_per_sec("400%") == 4_000_000
    assert U.parse_cpu_quota_us_per_sec(400) == 4_000_000
    assert U.parse_cpu_quota_us_per_sec(50) == 500_000


def test_nomalum_property_JIMGINA_tashlanmaydi():
    """Jimgina tashlangan `MemoryMax=` butun cheklash rejimini yo'q qilardi."""
    with pytest.raises(U.UnitsError, match="tanilmadi"):
        U.encode_properties({"MemoryMaxx": "64M"})


def test_execstart_satr_qabul_qilinmaydi():
    """'sleep 30' ni bo'lish qo'shtirnoq xatolarini yashirardi."""
    with pytest.raises(U.UnitsError, match="satr bo'lishi mumkin emas"):
        U.encode_properties({"ExecStart": "/bin/sleep 30"})


def test_systemctl_show_parsi_kop_qatorli_qiymatni_yutmaydi():
    txt = "Id=x.service\nStatusText=birinchi\nikkinchi\nActiveState=active\n"
    d = U.parse_systemctl_show(txt)
    assert d["Id"] == "x.service"
    assert d["StatusText"] == "birinchi\nikkinchi"
    assert d["ActiveState"] == "active"


# --- haqiqiy systemd: hayot tsikli ------------------------------------------

NAME_LIFE = "revixselftest-life.service"


def test_transient_unit_yaratiladi_active_boladi_va_property_lar_qaytadi(lab):
    sd = lab
    started = sd.start_transient(NAME_LIFE, unit_props())

    # Job natijasi SINXRON keladi -- "chaqiruv qaytdi" va "start tugadi"
    # aralashtirilmaydi.
    assert started["job_result"] == "done"
    assert started["mono_us_after_call"] >= started["mono_us_before_call"]
    assert started["mono_us_job_removed"] >= started["mono_us_after_call"]

    assert sd.is_active(NAME_LIFE)
    wa = U.wait_for_active(sd, NAME_LIFE, timeout_s=5.0)
    assert wa["ok"] and wa["active_state"] == "active"

    # --- JONLI unit'dan o'qib olish (D-Bus, aniq sonlar) ---
    g = lambda p: sd.get_property(NAME_LIFE, U.SERVICE_IFACE, p)  # noqa: E731
    assert g("Slice") == SELF_SLICE
    assert g("MemoryMax") == 64 * 1024**2
    assert g("MemoryHigh") == 48 * 1024**2
    assert g("MemorySwapMax") == 0
    assert g("TasksMax") == 16
    assert g("CPUQuotaPerSecUSec") == 4_000_000
    assert g("Restart") == "on-failure"
    assert g("RestartUSec") == 100_000
    assert g("RestartMaxDelayUSec") == 8_000_000
    assert g("StartLimitBurst") == 0
    assert g("WatchdogUSec") == 30_000_000
    assert g("TimeoutStartUSec") == 3_000_000
    assert g("RuntimeMaxUSec") == 30_000_000
    assert g("Environment") == ["REVIX_SELFTEST=1"]
    assert g("WorkingDirectory") == "/tmp"
    assert g("Type") == "exec"
    assert g("OOMPolicy") == "continue"
    assert sd.get_property(NAME_LIFE, U.UNIT_IFACE, "CollectMode") == "inactive-or-failed"

    # Slice DASH'SIZ nom bo'lgani uchun user@ ning TO'G'RIDAN-TO'G'RI childi
    # bo'lishi shart (ierarxiya tuzog'i -- PREREGISTRATION amendment v1->v1.1).
    cgroup = sd.get_property(NAME_LIFE, U.SERVICE_IFACE, "ControlGroup")
    assert cgroup.endswith(f"/user@{os.getuid()}.service/{SELF_SLICE}/{NAME_LIFE}"), cgroup

    # --- run_meta dump: JONLI obyektdan, barcha property ---
    dump = U.dump_unit_properties(NAME_LIFE, systemd=sd)
    assert dump["dump_valid"] is True
    assert dump["alive_before"] and dump["alive_after"]
    assert dump["load_state"] == "loaded"
    assert dump["property_count"] > 100, dump["property_count"]
    assert dump["properties"]["Id"] == NAME_LIFE
    assert dump["properties"]["MemoryMax"] == str(64 * 1024**2)
    assert dump["properties"]["Slice"] == SELF_SLICE
    assert dump["properties"]["CollectMode"] == "inactive-or-failed"

    # --- yig'ishtirish: hech narsa qolmaydi ---
    U.teardown(systemd=sd, units=[NAME_LIFE], unit_patterns=SELF_PATTERNS,
               slices=SELF_SLICES, clear_drop_ins=True)
    assert sd.unit_loaded(NAME_LIFE) is False
    rep = U.preflight(systemd=sd, unit_patterns=SELF_PATTERNS, slices=SELF_SLICES)
    assert rep["clean"], rep["problems"]


def test_restart_steps_4_round_trip(lab):
    """Baseline B arm'i BUTUNLAY shu property'ga tayanadi.

    Agar `RestartSteps=` transient unit'da jimgina tashlanib ketsa, B arm'i
    A arm'idan farq qilmay qolardi va A-vs-B taqqoslash MA'NOSIZ bo'lardi --
    lekin log'lar hech narsa ko'rsatmasdi. Shuning uchun bu alohida test.
    """
    sd = lab
    name = "revixselftest-steps.service"
    sd.start_transient(name, unit_props(RestartSteps=4, RestartSec="1s",
                                       RestartMaxDelaySec="8s"))
    assert sd.get_property(name, U.SERVICE_IFACE, "RestartSteps") == 4
    dump = U.dump_unit_properties(name, systemd=sd)
    assert dump["dump_valid"] is True
    assert dump["properties"]["RestartSteps"] == "4"
    assert dump["properties"]["RestartUSec"] == "1s"
    assert dump["properties"]["RestartMaxDelayUSec"] == "8s"


# --- PropertiesChanged ------------------------------------------------------

_HEX32 = re.compile(r"^[0-9a-f]{32}$")


def test_properties_changed_holat_otishini_yetkazadi_va_ikki_vaqtni_ALOHIDA_beradi(lab):
    """§1 / §8: systemd'ning monotonic vaqti AVTORITET, bizning qabul vaqti ALOHIDA.

    Ikkisi bitta field'ga birlashtirilsa D-Bus yetkazish kechikishi o'lchov
    ichida YASHIRINIB qolardi va `D_sd` / `L_det_sd` shu miqdorda buzilardi.
    """
    sd = lab
    name = "revixselftest-watch.service"
    watcher = U.UnitWatcher(sd, name)
    # Obuna unit YARATILISHIDAN OLDIN: obyekt yo'li nom'dan hisoblanadi,
    # demak eng birinchi o'tish ham o'tkazib yuborilmaydi.
    watcher.start()
    try:
        sd.start_transient(name, unit_props())
        up = watcher.wait_for(lambda r: r["ActiveState"] == "active", timeout_s=5.0)
        assert up is not None, "active o'tishi PropertiesChanged orqali kelmadi"

        # Har record TO'LIQ field to'plamini beradi (Unit + Service signallari
        # merge qilingan), aks holda analiz ikki oqimni qo'lda ulashga majbur
        # bo'lardi.
        assert up["snapshot_complete"] is True, up["missing_props"]
        for p in ("ActiveState", "SubState", "InvocationID", "NRestarts", "Result",
                  "ExecMainPID", "ExecMainCode", "ExecMainStatus"):
            assert p in up
        assert _HEX32.match(up["InvocationID"]), up["InvocationID"]
        assert up["NRestarts"] == 0
        assert up["ExecMainPID"] > 0

        # systemd'ning TO'LIQ monotonic to'plami -- yettitasi ham.
        for p in U.MONOTONIC_TIMESTAMP_PROPS:
            assert p in up, p
            assert isinstance(up[p], int), (p, up[p])
        assert up["InactiveExitTimestampMonotonic"] > 0
        assert up["ActiveEnterTimestampMonotonic"] >= up["InactiveExitTimestampMonotonic"]
        assert up["ConditionTimestampMonotonic"] > 0

        # ALOHIDA field: harness qabul vaqti. Bir xil monotonic domenda,
        # lekin systemd'ning qiymatidan KEYIN -- ya'ni kechikish KO'RINADI.
        assert "recv_mono_us" in up and "mono_us" not in up
        assert up["recv_mono_us"] >= up["ActiveEnterTimestampMonotonic"]
        lag = up["recv_mono_us"] - up["StateChangeTimestampMonotonic"]
        assert 0 <= lag < 5_000_000, lag
        assert up["recv_real_us"] > 0
        assert up["signal_iface"] in (U.UNIT_IFACE, U.SERVICE_IFACE)
        assert up["changed_count"] >= len(up["changed_props"])

        # --- ikkinchi o'tish: active -> inactive ---
        cursor = watcher.mark()
        sd.stop(name)
        down = watcher.wait_for(
            lambda r: r["ActiveState"] == "inactive", timeout_s=10.0, since=cursor
        )
        assert down is not None, "inactive o'tishi kelmadi"
        assert down["recv_mono_us"] > up["recv_mono_us"]
        assert watcher.dropped == 0
        assert watcher.sink_errors == 0
        assert watcher.signals_seen >= 2
    finally:
        watcher.stop()


def test_watcher_sink_har_record_ni_oladi(lab):
    """Driver record'larni JSONL'ga sink orqali yozadi -- yo'l ishlashi shart."""
    sd = lab
    name = "revixselftest-sink.service"
    seen = []
    watcher = U.UnitWatcher(sd, name, sink=seen.append)
    watcher.start()
    try:
        sd.start_transient(name, unit_props())
        assert watcher.wait_for(lambda r: r["ActiveState"] == "active", timeout_s=5.0)
        assert len(seen) >= 1
        assert all(r["unit"] == name for r in seen)
        assert watcher.sink_errors == 0
    finally:
        watcher.stop()


# --- pre-flight -------------------------------------------------------------


def test_preflight_qoldiq_unit_va_cgroup_ni_topadi_va_toza_holatda_otadi(lab):
    """Qoldiq holat JIMGINA keyingi run'ga qo'shilib ketmasligi kerak.

    DIQQAT -- nega `revix-*` emas: haqiqiy `revix-` prefiksli unit yaratish
    parallel ishlayotgan eksperiment run'i yoki boshqa agent bilan
    to'qnashardi. Shuning uchun pattern parametr orqali beriladi va AYNAN
    SHU kod yo'li `revixselftest-*` bilan sinaladi; qo'shimcha ravishda
    DEFAULT (`revix-*`) tekshiruv bizning selftest unit'imizni KO'RMASLIGI
    ham tasdiqlanadi (prefiks izolyatsiyasi).
    """
    sd = lab
    name = "revixselftest-preflight.service"

    before = U.preflight(systemd=sd, unit_patterns=SELF_PATTERNS, slices=SELF_SLICES)
    assert before["clean"], before["problems"]

    sd.start_transient(name, unit_props())

    dirty = U.preflight(systemd=sd, unit_patterns=SELF_PATTERNS, slices=SELF_SLICES)
    assert dirty["clean"] is False
    assert any(name in p for p in dirty["problems"]), dirty["problems"]
    assert any(u["unit"] == name for u in dirty["units"])
    # Slice cgroup'i ham topiladi.
    assert any(p.endswith(SELF_SLICE) for p in dirty["cgroups"]), dirty["cgroups"]

    with pytest.raises(U.PreflightError) as ei:
        U.require_clean(systemd=sd, unit_patterns=SELF_PATTERNS, slices=SELF_SLICES)
    assert ei.value.report["clean"] is False

    # Prefiks izolyatsiyasi: `revix-*` glob'i `revixselftest-...` ga MOS EMAS.
    isolated = U.preflight(systemd=sd)
    assert not any(name in p for p in isolated["problems"]), isolated["problems"]

    U.teardown(systemd=sd, units=[name], unit_patterns=SELF_PATTERNS,
               slices=SELF_SLICES, clear_drop_ins=True)
    after = U.preflight(systemd=sd, unit_patterns=SELF_PATTERNS, slices=SELF_SLICES)
    assert after["clean"], after["problems"]


# --- teardown ---------------------------------------------------------------


def test_teardown_idempotent(lab):
    """Ikki marta chaqirish xavfsiz: washout yo'lida bu MAJBURIY."""
    sd = lab
    name = "revixselftest-teardown.service"
    sd.start_transient(name, unit_props())
    assert sd.is_active(name)

    first = U.teardown(systemd=sd, units=[name], unit_patterns=SELF_PATTERNS,
                       slices=SELF_SLICES, clear_drop_ins=True)
    assert first["errors"] == [], first["errors"]
    assert any(k["ok"] for k in first["killed"]), first["killed"]
    assert sd.unit_loaded(name) is False

    second = U.teardown(systemd=sd, units=[name], unit_patterns=SELF_PATTERNS,
                        slices=SELF_SLICES, clear_drop_ins=True)
    assert second["errors"] == [], second["errors"]
    assert second["killed"] == []          # cgroup allaqachon yo'q

    third = U.teardown(systemd=sd, units=[name], unit_patterns=SELF_PATTERNS,
                       slices=SELF_SLICES, clear_drop_ins=True)
    assert third["errors"] == [], third["errors"]
    assert U.preflight(systemd=sd, unit_patterns=SELF_PATTERNS,
                       slices=SELF_SLICES)["clean"]


def test_teardown_failed_unit_ni_reset_qiladi(lab):
    """`Result=` va failed holat F_sd detektorining manbasi (§3).

    Failed unit reset qilinmasa keyingi pre-flight'da qoldiq bo'lib qolardi.
    """
    sd = lab
    name = "revixselftest-failed.service"
    # Collect=False -- failed holat KO'RINIB turishi kerak, aks holda unit
    # darhol yo'qolib, reset-failed yo'lini sinab bo'lmasdi.
    with pytest.raises(U.JobFailedError) as ei:
        sd.start_transient(
            name,
            unit_props(ExecStart=["/nonexistent/revixselftest-binary"], Restart="no",
                       Collect=False, WatchdogSec=0),
        )
    assert ei.value.result != "done"
    assert sd.active_state(name) == "failed"
    assert sd.get_property(name, U.SERVICE_IFACE, "Result") != "success"

    td = U.teardown(systemd=sd, units=[name], unit_patterns=SELF_PATTERNS,
                    slices=SELF_SLICES, clear_drop_ins=True)
    assert name in td["reset"], td
    assert sd.unit_loaded(name) is False


# --- `systemctl show` tuzog'i -----------------------------------------------


def test_olgan_unit_dumpi_DEFAULTlarni_beradi_va_bu_ANIQLANADI(lab):
    """⚠️ Bu test hujjatdagi tuzoqning bajariladigan shakli.

    `--collect` bilan tugagan unit yo'qoladi, va `systemctl show` undan keyin
    rc=0 bilan TO'LIQ DEFAULT to'plamini chiqaradi. Default'lar haqiqiy
    qiymatlarga o'xshaydi (`MemoryMax=infinity`, `RestartSteps=0`), demak
    tekshirilmasa run_meta'ga YOLG'ON konfiguratsiya yozilardi.
    """
    sd = lab
    name = "revixselftest-ghost.service"
    assert sd.unit_loaded(name) is False

    with pytest.raises(U.UnitNotAliveError):
        U.dump_unit_properties(name, systemd=sd)

    ghost = U.dump_unit_properties(name, systemd=sd, require_alive=False)
    assert ghost["dump_valid"] is False
    assert ghost["alive_before"] is False and ghost["alive_after"] is False
    assert ghost["load_state"] == "not-found"
    assert ghost["systemctl_rc"] == 0            # <-- jimgina muvaffaqiyat
    assert ghost["property_count"] > 100         # <-- to'liq default to'plam
    # Aynan shu ikki qiymat haqiqiy konfiguratsiyaga o'xshaydi:
    assert ghost["properties"]["MemoryMax"] == "infinity"
    assert ghost["properties"]["RestartSteps"] == "0"


# --- slice runtime property'lari --------------------------------------------


def test_slice_property_runtime_only_persistent_dropin_qoldirmaydi(lab):
    """PI controller `MemoryHigh=` ni shu yo'l bilan buradi.

    `~/.config/systemd/user/` ga yozish keyingi run'ni JIMGINA
    kontaminatsiya qilardi, shuning uchun faqat runtime drop-in.
    """
    sd = lab
    name = "revixselftest-sliceprop.service"
    sd.start_transient(name, unit_props())

    sd.set_unit_properties(SELF_SLICE, {"MemoryHigh": "96M", "TasksMax": 128})
    assert sd.get_property(SELF_SLICE, "org.freedesktop.systemd1.Slice",
                           "MemoryHigh") == 96 * 1024**2
    assert sd.get_property(SELF_SLICE, "org.freedesktop.systemd1.Slice",
                           "TasksMax") == 128

    persistent = os.path.expanduser("~/.config/systemd/user")
    leftovers = [
        f for f in (os.listdir(persistent) if os.path.isdir(persistent) else [])
        if f.startswith("revix")
    ]
    assert leftovers == [], leftovers

    runtime = U.list_runtime_drop_ins([SELF_GLOB, SELF_SLICE])
    assert any(p.endswith(f"{SELF_SLICE}.d") for p in runtime), runtime
    assert all(p.startswith(U.user_control_dir()) for p in runtime), runtime

    removed = U.clear_runtime_drop_ins([SELF_GLOB, SELF_SLICE], systemd=sd)
    assert removed, removed
    assert U.list_runtime_drop_ins([SELF_GLOB, SELF_SLICE]) == []


# --- wait_for_active chegaralari -------------------------------------------


def test_wait_for_active_timeout_istisno_EMAS(lab):
    """Timeout -- O'LCHOV NATIJASI (§9.2 (i) mexanizmi), xato emas.

    Istisno tashlansa driver uni `harness_error` deb yozardi va `Result=timeout`
    mexanizmi ma'lumot sifatida yo'qolardi.
    """
    sd = lab
    res = U.wait_for_active(sd, "revixselftest-never.service", timeout_s=0.2)
    assert res["ok"] is False
    # None != "inactive": unit umuman yo'q, to'xtagan emas.
    assert res["active_state"] is None
    assert res["elapsed_us"] >= 150_000
    assert res["polls"] >= 2


def test_active_state_yoq_unit_uchun_None(lab):
    sd = lab
    assert sd.active_state("revixselftest-absent.service") is None
    assert sd.is_active("revixselftest-absent.service") is False
    assert sd.unit_loaded("revixselftest-absent.service") is False


# --- oxirgi tekshiruv -------------------------------------------------------


def test_zzz_hech_qanday_selftest_qoldigi_qolmadi(sd):
    """Oxirgi test: fixture'lar chindan ham hech narsa qoldirmaganini tasdiqlaydi."""
    _selftest_teardown(sd)
    rep = U.preflight(systemd=sd, unit_patterns=SELF_PATTERNS, slices=SELF_SLICES,
                      strict_drop_ins=True)
    assert rep["clean"], rep["problems"]

    # Haqiqiy eksperiment nomlari (`revix-*`, revixlab/revixmon) ham toza --
    # testlar ularga TEGMAGAN.
    #
    # `strict_drop_ins` ATAYLAB QO'YILMAYDI: bu mashinada `revixlab.slice.d` /
    # `revixmon.slice.d` runtime drop-in'lari testlardan OLDIN ham bor edi
    # (guard kalibratsiyasi / pressure ishlaridan qolgan). Ular /run ostida,
    # ya'ni logout'da o'chadi, va ularni bu testdan o'chirish parallel
    # ishlayotgan boshqa ishni buzardi. Shuning uchun bu yerda faqat unit va
    # cgroup qoldiqlari tekshiriladi -- aynan test yaratishi mumkin bo'lgan
    # narsalar.
    real = U.preflight(systemd=sd)
    assert real["clean"], real["problems"]
    # Bizning testlar `revix-*` yoki lab/mon uchun drop-in YARATMAGAN bo'lishi
    # kerak; selftest drop-in'lari esa butunlay tozalangan bo'lishi kerak.
    assert U.list_runtime_drop_ins([SELF_GLOB, SELF_SLICE]) == []
