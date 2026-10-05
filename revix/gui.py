"""REVIX dashboard -- tizim holatini FAQAT haqiqiy manbadan o'qib ko'rsatadi.

Faqat Python stdlib: `http.server` + `json` + `html`, statik aktivlar
`revix/gui_assets/` dan. Yangi bog'liqlik YO'Q (`CONTRIBUTING.md` §4,
`PREREGISTRATION.md` §10.3), build qadami yo'q, CDN yo'q, offline ishlaydi.

**Default bind -- FAQAT localhost (`127.0.0.1`).** Bu server TIRIK tizim
holatini (cgroup'lar, PSI, unit'lar, muhit fingerprint'i, journal satrlari)
o'qiydi va tashqariga ochilmasligi SHART. Loopback bo'lmagan manzil
`--allow-remote` ni ATAYLAB talab qiladi, aks holda server ishga tushmaydi.

Amalga oshiradigan bandlar:
  * `revix/cli.py` -- `status_report()`, `health_report()`, `collect_checks()` +
    `build_report()` (18 doctor tekshiruvi), `read_events()`, `version_report()`,
    `REPORT_SCHEMA_VERSION`, `Check` dataclass'i -- 1-darajali TIRIK manba
  * `docs/architecture/04-driver-va-analiz-shartnomasi.md` §1.1 -- `run_meta.json`
    majburiy maydonlari; §1.2 -- trial hodisalari ketma-ketligi (2-daraja);
    §2.2 -- `analysis.json` sxemasi; §3 -- figura va uning raqam sidecar'i
    (3-daraja)
  * `revix/figures.py` -- `FIGURE_NAMES` va sidecar shakli; SVG QAYTA
    CHIZILMAYDI, mavjud fayl shunday beriladi
  * `PREREGISTRATION.md` §12 -- disposition yopiq enum'i va eksklyuziya
    darajasi NATIJA; §16.4 -- eksklyuziya darajasi TO'PLAMINI nomlashi SHART;
    §15.4 -- `governor`/`scaling_driver` bu muhitda `None` = o'lchanmadi,
    HECH QACHON `0`; §13 -- arm C (adaptiv engine) muzlatilmagan, demak YO'Q

DIZAYN QOIDALARI (buzilmaydi):

  1. **EKRANDA MANBADAN O'QILMAGAN SON BO'LMAYDI.** Placeholder yo'q, namuna
     ma'lumot yo'q, interpolyatsiya yo'q, "taxminan shunday" default yo'q,
     soxta sparkline yo'q. Qiymat yo'q bo'lsa UI buni SO'Z bilan aytadi.
     NEGA: bu loyihaning butun qiymati o'lchov yaxlitligi; ekrandagi
     ishonchli ko'rinadigan o'ylab chiqarilgan son bo'sh paneldan YOMONROQ,
     chunki kimdir unga ishonadi va u natija sifatida tarqaydi.

  2. **TO'RT HOLAT TO'RT XIL KO'RINADI** (`style.css` qoida 4):
     `None` -> "o'lchanmadi"; `0` -> "0" + "o'lchangan nol" belgisi;
     artifact yo'q -> "hali ishga tushirilmadi"; birorta modul chiqarmaydi ->
     "manba yo'q". NEGA: `None` va `0` ni bir xil ko'rsatish -- yolg'on
     (`CONTRIBUTING.md` §4 kontrol ro'yxati, `PREREGISTRATION.md` §15.4).
     Shu sababli `value_html(None)` chiqishida BIRORTA RAQAM BO'LMAYDI --
     bu `tests/unit/test_gui.py` da qulflangan.
     KO'RINISH (jurnal 19, `docs/architecture/19-gui-soddalashtirish.md`):
     semantika o'zgarmagan, faqat balandligi pasaytirilgan -- `None` ->
     "—" + kichik "i" + oddiy tildagi sabab `title` da; `0` -> oddiy "0".
     Matnli belgilar (`o'lchanmadi n/m reason=...`, "o'lchangan nol") DOM da
     qoladi va "Tadqiqotchi uchun" sahifalarida matn bo'lib ko'rinadi.

  3. **HAR PANEL O'Z MANBASINI VA O'QILGAN VAQTINI AYTADI**, ishonch darajasi
     bilan (1 tirik / 2 run artifact / 3 derived / hujjat / konfig). Eskirgan
     o'qish ESKIRGAN ko'rinadi (`stale`). NEGA: manbasi ko'rinmagan son
     tekshirilmaydi, va "hozirgi" deb ko'rsatilgan eski son yolg'on gapiradi.

  4. **GUI HECH NARSA HISOBLAMAYDI.** CI, p-qiymat, kvantil, tezlik, ulush --
     hammasi `cli.py` / `analysis.json` / sidecar'dan TAYYOR keladi. Bu modul
     faqat o'qiydi, formatlaydi va escape qiladi. NEGA: GUI ichida ikkinchi
     analiz paydo bo'lsa, u birinchisidan uzoqlashadi -- aynan `figures.py`
     qoida 5 va shartnoma §3 oldini olmoqchi bo'lgan narsa.

  5. **FAYLDAN O'QILGAN HAR MATN ISHONCHSIZ.** `run_meta` maydoni, journal
     satri, unit nomi, event payload'i -- hammasi `esc()` (ya'ni
     `html.escape(quote=True)`) orqali o'tadi. NEGA: `events.jsonl` va
     `guard.jsonl` ga SUT, systemd va guard yozadi; ulardagi matn sahifa
     uchun kirish ma'lumoti, markup emas.

  6. **HOZIRGI NORMAL HOLAT -- "MA'LUMOT YO'Q".** Hech qanday eksperiment
     ishga tushirilmadi va hech qanday natija yo'q (`README.md`,
     `CONTRIBUTING.md`). Bo'sh sahifa ATAYLAB shunday ko'rinadi: nima
     yo'qligini, QAYSI modul uni chiqarishini va uni qanday hosil qilishni
     aytadi. NEGA: "buzilgan" bilan "hali yo'q" ni ajratmaslik o'quvchini
     mavjud bo'lmagan natijani qidirishga majburlaydi.

  7. **SINTETIK MA'LUMOT EKRANDA BELGILANADI**, izohda emas. Manba sintetik
     bo'lsa panel ramkasi va sahifa boshidagi banner buni aytadi, va bu
     belgi FAQAT QO'SHILADI -- hech bir flag uni olib tashlamaydi. NEGA:
     ekranda ko'rilgan son keyin skrinshot bo'lib yuradi va izoh u bilan
     birga ketmaydi.

  8. **GUI REVIX NOMIDAN QAROR DA'VO QILMAYDI.** REVIX da adaptiv recovery
     engine YO'Q -- arm C muzlatilmagan (`PREREGISTRATION.md` §13). Shu
     sababli "RECOVERY ENGINE" paneli systemd AYNAN nima qilganini
     ko'rsatadi va uni SYSTEMD ga atributsiya qiladi; "Recovery siyosatlari"
     esa mavjud arm konfiguratsiyalarini beradi, o'ylab chiqarilgan policy
     engine'ni emas.

  9. **FAQAT O'QISH.** Bu server hech qanday POST qabul qilmaydi, hech qanday
     faylga yozmaydi, hech qanday unit'ga tegmaydi va hech qanday eksperiment
     ishga tushirmaydi. "Sozlamalar" sahifasi -- joriy konfiguratsiyaning
     KO'RINISHI, tahrirlagich emas. NEGA: o'lchov vositasi o'lchayotgan
     tizimni o'zgartirmasligi kerak (`cli.py` qoida 4 bilan bir xil
     doktrina).

 10. **FIGURA QAYTA CHIZILMAYDI.** `figures.py` SVG ni allaqachon chiqaradi;
     GUI o'sha faylni shunday beradi va yoniga uning O'Z sidecar raqamlarini
     qo'yadi. NEGA: figura ko'z bilan emas, raqam bilan tekshiriladi
     (shartnoma §3), va ikkinchi chizuvchi birinchisidan uzoqlashadi.
"""

from __future__ import annotations

import argparse
import html
import http.server
import ipaddress
import json
import os
import shutil
import socket
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from . import cli
from .figures import FIGURE_NAMES

# --- doimiylar --------------------------------------------------------------

GUI_VERSION = 1

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
ASSET_DIR = os.path.join(PKG_DIR, "gui_assets")
REPO_ROOT = cli.REPO_ROOT

# Default bind -- loopback. Bu qiymat docstring'da ham e'lon qilingan.
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8787
# `localhost` IP emas, shuning uchun nom bo'yicha alohida ruxsat etiladi.
LOOPBACK_NAMES = frozenset({"localhost", "localhost.localdomain"})

# O'qish shundan keyin ESKI hisoblanadi. NEGA 30 s: PSI ning ichki kadensi
# 2 s va `cli.MIN_RATE_WINDOW_S` oynasi 2 s (PREREGISTRATION.md §7), ya'ni
# bir necha oynadan keyin ko'rsatilgan tezlik endi "hozir" emas.
STALE_AFTER_S = 30.0

# Tirik snapshot keshi. NEGA kesh BOR: har so'rov PSI uchun >= 2 s uxlaydi
# (`sample_psi_rates`), demak keshsiz har sahifa yuklash o'lchayotgan
# mashinaga o'z yuki bo'lib tushardi (`PREREGISTRATION.md` §8.2 -- o'z
# perturbatsiyasi). NEGA kesh XAVFSIZ: o'qish vaqti har panelda ko'rinadi va
# yoshi o'tgach `stale` bo'ladi, ya'ni kesh yashirilmaydi.
DEFAULT_CACHE_S = 10.0

# `revix doctor` 18 tekshiruv qiladi va ularning ba'zilari subprocess chaqiradi
# -- shuning uchun alohida, uzunroq kesh.
DEFAULT_DOCTOR_CACHE_S = 60.0

# Qancha hodisa/log satri ko'rsatiladi (ko'rsatish chegarasi, O'LCHOV emas).
EVENTS_LIMIT = 200
LOG_TAIL_LINES = 200

# --- qiymat holati matnlari (QOIDA 2) --------------------------------------
#
# Bu to'rt matn BIR-BIRIDAN FARQ QILISHI SHART va ularning hech biri raqam
# O'Z ICHIGA OLMAYDI -- test shu ikki shartni ham qulflaydi.

TEXT_NOT_MEASURED = "o'lchanmadi"
TEXT_NOT_YET_RUN = "hali ishga tushirilmadi"
TEXT_NO_SOURCE = "manba yo'q"
TEXT_MEASURED_ZERO = "o'lchangan nol"
TIP_MEASURED_ZERO = "O'lchangan qiymat: aniq nol (o'lchov bo'ldi)."

# Zich teglar (`docs/branding/state-indicators.md` §5). Mashina qiymatlari
# (`data-state`) INGLIZCHA va yopiq enum -- tarjima QILINMAYDI; ekranda
# ko'rinadigan matn esa o'zbekcha (DEVELOPMENT.md §6 til jadvali).
TAG_NOT_MEASURED = "n/m"
TAG_NOT_YET_RUN = "n/r"
STATE_NOT_MEASURED = "not_measured"
STATE_NOT_YET_RUN = "not_run"

# `state-indicators.md` §4.2-4: SABABSIZ `n/m` -- TAQIQ. Shuning uchun
# `missing_html()` sababni MAJBURIY oladi va u yopiq lug'atdan bo'lishi
# SHART. Hujjat sabab kodlarini "illyustrativ taklif" deb beradi va yopiq
# lug'atni amalga oshiruvchiga qoldiradi -- bu o'sha lug'at.
#
# NEGA yopiq: erkin matnli sabab vaqt o'tib "yo'q", "-" va "bilmadim" ga
# aylanadi, va o'sha paytda `n/m` yana sababsiz holatga qaytadi.
REASON_NOT_REPORTED = "not_reported"            # manba maydonni qiymatsiz berdi
REASON_KEY_ABSENT = "key_absent"                # manbada kalit umuman yo'q
REASON_SYSFS_ABSENT = "sysfs_absent"            # kernel interfeysi yo'q (cpufreq)
REASON_SCOPE_NO_DATA = "scope_no_data"          # PSI scope bu resursni bermadi
REASON_SOURCE_ERROR = "source_error"            # o'qish istisno bilan tugadi
REASON_HORIZON_NOT_REPORTED = "horizon_not_reported"
REASON_TIME_UNIT_NOT_DECLARED = "time_unit_not_declared"
REASON_PROBE_GAP = "probe_gap"                  # probe uzilishi > 2xP

MISSING_REASONS: frozenset[str] = frozenset({
    REASON_NOT_REPORTED,
    REASON_KEY_ABSENT,
    REASON_SYSFS_ABSENT,
    REASON_SCOPE_NO_DATA,
    REASON_SOURCE_ERROR,
    REASON_HORIZON_NOT_REPORTED,
    REASON_TIME_UNIT_NOT_DECLARED,
    REASON_PROBE_GAP,
})

# Har sabab kodining ODDIY TILDAGI bir jumlali izohi. Ekranda u `title`
# (sichqoncha bilan ustiga borganda) va "Yordam" sahifasida ko'rinadi;
# mashina kodi (`reason=<kod>`) esa DOM da qoladi va tadqiqotchi
# sahifalarida ko'rinadi. NEGA alohida lug'at: kod tadqiqotchi uchun aniq,
# lekin oddiy foydalanuvchiga hech narsa aytmaydi (jurnal 19 §3).
REASON_PLAIN: dict[str, str] = {
    REASON_NOT_REPORTED: "manba bu qiymatni bermadi.",
    REASON_KEY_ABSENT: "manbada bu maydon umuman yo'q.",
    REASON_SYSFS_ABSENT: "bu tizimda kerakli kernel interfeysi (fayl) yo'q.",
    REASON_SCOPE_NO_DATA: "bu guruh uchun bosim (PSI) ma'lumoti berilmadi.",
    REASON_SOURCE_ERROR: "ma'lumotni o'qishda xato yuz berdi.",
    REASON_HORIZON_NOT_REPORTED: "kuzatuv muddati (horizon) e'lon qilinmagan.",
    REASON_TIME_UNIT_NOT_DECLARED: "vaqt birligi e'lon qilinmagan.",
    REASON_PROBE_GAP: "tekshiruv signallari orasida uzilish bo'lgan.",
}

# Bo'sh qiymat belgisi. NEGA em dash: u raqam emas (ko'rinadigan matnda
# raqam yo'q -- qoida 2), qisqa va "yo'q" ning odatiy tipografik belgisi.
DASH = "—"

SYNTHETIC_BANNER_TEXT = (
    "SINTETIK MA'LUMOT -- HAQIQIY O'LCHOV EMAS. Bu sahifadagi raqamlar "
    "qo'lda yasalgan fixture'dan keladi va natija sifatida ISHLATILMAYDI."
)
SYNTHETIC_INLINE_TEXT = "SINTETIK"

# Manba ishonch darajasi -> ekrandagi nishon. Tartib = ishonch tartibi.
SOURCE_TIERS = {
    "live": "1 TIRIK",
    "artifact": "2 ARTIFACT",
    "derived": "3 DERIVED",
    "document": "HUJJAT",
    "config": "KONFIG",
}

# Birorta modul chiqarmaydigan maydonlar. Bu ro'yxat GUI ning "nima yo'q"
# javobi: har biri NIMA kerakligini va NEGA yo'qligini aytadi. Yangi maydon
# bu yerga faqat haqiqatan tekshirilgandan keyin qo'shiladi.
MISSING_SOURCES: dict[str, tuple[str, str]] = {
    "cpu_utilization": (
        "CPU foydalanish foizi",
        "revix paketi CPU foydalanishini (%) hech qayerda o'lchamaydi. "
        "`cgroup.snapshot_cgroup()` faqat `cpu.stat` ni XOM holda o'qiydi va "
        "`cli.sample_psi_rates()` CPU uchun PSI stall tezligini beradi -- "
        "stall ulushi foydalanish foizi EMAS. Foizga aylantirish GUI ichida "
        "hisoblash bo'lardi (qoida 4), shuning uchun qilinmaydi.",
    ),
    "disk": (
        "Disk sig'imi va IO",
        "revix paketida disk o'lchovi YO'Q: `os.statvfs`, `/proc/diskstats` "
        "va `io.stat` birorta modulda o'qilmaydi. Bundan tashqari `io` "
        "controller bu mashinada delegated EMAS "
        "(`cli.OPTIONAL_CONTROLLERS`, `cli.check_io_delegation`), demak "
        "cgroup darajasidagi IO hisobi privilegiyasiz olinmaydi.",
    ),
    "network": (
        "Tarmoq",
        "revix paketida tarmoq o'lchovi YO'Q: `/proc/net/dev` va socket "
        "statistikasi birorta modulda o'qilmaydi. P1 tarmoq fault "
        "injection'ini ishlatmaydi (`tc netem` root talab qiladi), shuning "
        "uchun uni chiqaradigan modul ham yozilmagan.",
    ),
}

# Arm konfiguratsiyalari -- HUJJAT fakti, o'lchov emas. Manba: `README.md`
# "Baseline'lar" jadvali. Arm C ATAYLAB "yo'q" deb beriladi
# (`PREREGISTRATION.md` §13: arm C siyosati muzlatilmagan).
ARM_CONFIGS: tuple[dict[str, str | None], ...] = (
    {
        "arm": "A",
        "config": "Restart=on-failure, RestartSec=100ms",
        "role": "tez restart baseline'i",
        "status": "mavjud (systemd konfiguratsiyasi)",
    },
    {
        "arm": "B",
        "config": ("Restart=on-failure, RestartSec=10s, RestartSteps=4, "
                   "RestartMaxDelaySec=160s"),
        "role": "systemd NATIVE exponential backoff -- kuchli baseline",
        "status": "mavjud (systemd >= 254 talab qiladi)",
    },
    {
        "arm": "no_action",
        "config": "Restart=no",
        "role": "majburiy nazorat: hech qanday recovery harakati yo'q",
        "status": "mavjud (systemd konfiguratsiyasi)",
    },
    {
        "arm": "C",
        "config": None,
        "role": "PSI-gated admission control + post-restart verification",
        "status": ("YO'Q -- siyosat va gate chegaralari MUZLATILMAGAN "
                   "(PREREGISTRATION.md §13). Hech qanday kod bu qarorni "
                   "qabul qilmaydi."),
    },
)

# "Recovery siyosatlari" va "RECOVERY ENGINE" panellari uchun majburiy
# halollik izohi (qoida 8).
ENGINE_HONESTY = (
    "REVIX da adaptiv recovery engine YO'Q. Arm C -- PSI-gated admission "
    "control -- hali muzlatilmagan (`PREREGISTRATION.md` §13), ya'ni birorta "
    "kod qator bu qarorni qabul qilmaydi. Quyida ko'rsatilgan narsa -- "
    "SYSTEMD ning o'z `Restart=` konfiguratsiyasi bo'yicha AYNAN nima "
    "qilgani, shu bilan atributsiya qilingan. Bu REVIX ning qarori EMAS."
)


# ===========================================================================
# escape va qiymat renderlari (QOIDA 2, QOIDA 5)
# ===========================================================================


def esc(value: Any) -> str:
    """Har qanday qiymatni HTML matn sifatida XAVFSIZ qiladi (qoida 5).

    `quote=True`: qiymat atribut ichiga ham tushishi mumkin. `None` ataylab
    bo'sh satr emas, balki `TEXT_NOT_MEASURED` ga aylanTIRILMAYDI -- bu
    funksiyaning vazifasi escape, qiymat talqini emas. `None` ni to'g'ri
    ko'rsatish `value_html()` ning ishi.
    """
    return html.escape("" if value is None else str(value), quote=True)


def missing_html(reason: str = REASON_NOT_REPORTED) -> str:
    """`None` = o'lchanmadi. Chiqishda BIRORTA RAQAM YO'Q (qoida 2).

    `reason` MAJBURIY (`docs/branding/state-indicators.md` §4.2-4: sababsiz
    `n/m` -- taqiq) va yopiq lug'atdan (`MISSING_REASONS`). Noma'lum kod --
    `ValueError`, jim qabul EMAS: busiz lug'at vaqt o'tib ochilib ketardi
    va sabab yana ma'nosiz erkin matnga aylanardi.

    BESH KANAL (§4.5), chunki rang eng zaif kanal -- monoxromda
    `--rx-fail` va `--rx-fg-2` kontrasti 1.00:1, ya'ni BIR XIL kulrang:
      1. shakl/to'ldirish -- CSS `.v-missing` shtrixi + yaxlit chegara,
      2. matn yorlig'i -- "o'lchanmadi" + zich teg `n/m`,
      3. sabab -- `reason=<kod>` ko'rinadi,
      4. dasturiy ma'no -- `data-state="not_measured"` + `aria-label`,
      5. joylashuv -- katakda RAQAM YO'Q, demak sonli ustunga aralashib
         `0` bo'la olmaydi.

    `role="img"` + `aria-label`: ekran o'quvchi `n/m` ni "n slash m" deb
    o'qimaydi (§4.5-4).

    KO'RINISH (jurnal 19 §3): oddiy sahifada katakda faqat "—" va kichik
    "i" belgisi turadi; sabab ODDIY TILDA `title` da (sichqoncha bilan
    ustiga borganda). Matnli tafsilot (`o'lchanmadi n/m reason=<kod>`)
    DOM dan OLIB TASHLANMAYDI: u `.detail` ichida qoladi, tadqiqotchi
    sahifalarida ko'rinadi, oddiy sahifada esa vizual yashiriladi. Semantika
    o'zgarmadi -- faqat qanchalik baland ko'rinishi o'zgardi.
    """
    if reason not in MISSING_REASONS:
        raise ValueError(
            f"noma'lum `not_measured` sababi: {reason!r}; "
            f"yopiq lug'at: {', '.join(sorted(MISSING_REASONS))}")
    label = f"not measured, reason: {reason}"
    tip = f"O'lchanmadi: {REASON_PLAIN[reason]} (reason={reason})"
    return (f'<span class="val v-missing" data-state="{STATE_NOT_MEASURED}"'
            f' data-reason="{esc(reason)}"'
            f' role="img" aria-label="{esc(label)}" title="{esc(tip)}">'
            f'<span class="dash" aria-hidden="true">{DASH}</span>'
            f'<span class="info" aria-hidden="true">i</span>'
            f'<span class="detail">{esc(TEXT_NOT_MEASURED)} '
            f'<span class="tag">{esc(TAG_NOT_MEASURED)}</span> '
            f'<span class="reason">reason={esc(reason)}</span>'
            f"</span></span>")


def norun_html() -> str:
    """Artifact hali yo'q -- "hali ishga tushirilmadi" (o'lchanmadi EMAS).

    `state-indicators.md` §4.3: ichi BO'SH + PUNKTIR chegara, ya'ni
    `not_measured` dan IKKI mustaqil kanal bilan ajraladi (to'ldirish va
    chegara turi). Sabab SHART EMAS -- hali bajarilmagani sababning o'zi
    (§4.3-3).
    """
    label = "not run"
    tip = ("Hali ishga tushirilmadi: bu ma'lumotni beradigan tajriba hali "
           "o'tkazilmagan.")
    return (f'<span class="val v-norun" data-state="{STATE_NOT_YET_RUN}"'
            f' role="img" aria-label="{esc(label)}" title="{esc(tip)}">'
            f"{esc(TEXT_NOT_YET_RUN)}"
            f'<span class="tag">{esc(TAG_NOT_YET_RUN)}</span></span>')


def nosource_html() -> str:
    """Birorta modul bu qiymatni chiqarmaydi -- to'rtinchi, alohida holat.

    `state-indicators.md` ning yetti holatida bu YO'Q, va ataylab
    `not_run` ga QO'SHILMAYDI: `not_run` "hali bajarilmagan, KUTILMOQDA"
    deydi, bu esa "uni ishlab chiqaradigan kod yo'q" deydi. Ikkisini
    birlashtirish mavjud bo'lmagan ishni rejadagi ish deb ko'rsatardi.
    """
    label = "no source: no module produces this value"
    tip = ("Manba yo'q: REVIX bu qiymatni umuman o'lchamaydi -- uni "
           "chiqaradigan modul yo'q. Bu xato emas.")
    return (f'<span class="val v-nosource" data-state="no_source"'
            f' role="img" aria-label="{esc(label)}" title="{esc(tip)}">'
            f'<span class="dash" aria-hidden="true">{DASH}</span>'
            f'<span class="info" aria-hidden="true">i</span>'
            f'<span class="detail">{esc(TEXT_NO_SOURCE)}</span></span>')


def _default_fmt(v: Any) -> str:
    """Formatlash -- hisoblash EMAS: birlik o'zgartirilmaydi, yaxlitlanmaydi.

    Faqat ming ajratuvchisi (ingichka bo'shliq) va float uchun uch kasr.
    Butun son XOM holda qoladi, demak ekrandagi raqam manbadagi raqam.
    """
    if isinstance(v, int):
        return f"{v:,}".replace(",", " ")
    if isinstance(v, float):
        return f"{v:.3f}"
    return str(v)


def value_html(value: Any, unit: str | None = None,
               fmt: Callable[[Any], str] | None = None,
               reason: str = REASON_NOT_REPORTED) -> str:
    """Bitta qiymatni TO'RT HOLATNI AJRATIB ko'rsatadi (qoida 2).

      * `None`  -> "o'lchanmadi", RAQAMSIZ va birliksiz. Birlik ham
                   bosilmaydi: o'lchanmagan narsaning birligi yo'q, va
                   birlik bosilsa qiymat go'yo mavjud bo'lib ko'rinardi.
      * `0`/`0.0` -> son KO'RINADI + "o'lchangan nol" belgisi. NEGA belgi:
                   nol o'lchov natijasi, va u "yo'q" bilan adashtirilmasligi
                   kerak (`PREREGISTRATION.md` §15.4 ning aynan masalasi).
      * `True`/`False` -> "ha"/"yo'q". `False` NOL EMAS, shuning uchun bool
                   nol tekshiruvidan OLDIN ushlanadi -- aks holda `False`
                   "o'lchangan nol" bo'lib ko'rinardi, bu esa boshqa gap.
      * qolgani -> o'lchangan qiymat, escape qilingan holda.
    """
    if value is None:
        return missing_html(reason)
    if isinstance(value, bool):
        # NEGA alohida o'zgaruvchi: f-string IFODASI ichida backslash
        # Python 3.12 dan oldin sintaksis xatosi, loyiha minimumi esa 3.11
        # (`cli.MIN_PYTHON`).
        word = "ha" if value else "yo'q"
        return f'<span class="val v-num">{esc(word)}</span>'
    render = fmt or _default_fmt
    text = esc(render(value))
    suffix = f' <span class="unit">{esc(unit)}</span>' if unit else ""
    if isinstance(value, (int, float)) and value == 0:
        # Ko'rinish (jurnal 19 §3): nol ODDIY son kabi ko'rinadi; "o'lchangan
        # nol" belgisi DOM da qoladi -- tadqiqotchi sahifasida kichik matn,
        # oddiy sahifada `title`. `v-zero` klassi `None` dan farqni saqlaydi.
        return (f'<span class="val v-zero" title="{esc(TIP_MEASURED_ZERO)}">'
                f'{text}{suffix}'
                f'<span class="zmark">{esc(TEXT_MEASURED_ZERO)}</span></span>')
    return f'<span class="val v-num">{text}{suffix}</span>'


def kb_html(kb: Any, reason: str = REASON_NOT_REPORTED) -> str:
    """kB qiymati odam o'qishi uchun. `None` -> o'lchanmadi, `0` -> nol.

    `cli.human_kb()` ATAYLAB ishlatilmaydi `None` uchun: u `"?"` qaytaradi,
    va `"?"` to'rt holatning qaysi biri ekanini aytmaydi (qoida 2).
    """
    if kb is None:
        return missing_html(reason)
    if isinstance(kb, bool) or not isinstance(kb, int):
        return value_html(kb, reason=reason)
    return value_html(kb, fmt=lambda v: cli.human_kb(int(v)), reason=reason)


def rate_html(v: Any, reason: str = REASON_NOT_REPORTED) -> str:
    """PSI stall tezligi (`total=` delta'sidan, `cli.sample_psi_rates`)."""
    return value_html(v, fmt=lambda x: f"{float(x):.4f}", reason=reason)


def text_html(value: Any, reason: str = REASON_NOT_REPORTED) -> str:
    """Fayldan kelgan ERKIN MATN uchun (qoida 5). `None` -> o'lchanmadi."""
    if value is None:
        return missing_html(reason)
    s = str(value)
    if not s.strip():
        # Bo'sh satr -- "o'lchanmadi" EMAS: u o'qildi va bo'sh edi.
        return '<span class="val v-num">&lt;bo\'sh&gt;</span>'
    return f'<span class="val v-num">{esc(s)}</span>'


# ===========================================================================
# manba (QOIDA 3)
# ===========================================================================


@dataclass
class Source:
    """Bir panel ma'lumoti QAYDAN va QACHON o'qilgani.

    `read_real_us` -- `cli.real_us()` bilan bir xil birlik (CLOCK_REALTIME
    mikrosekund), shunda sahifadagi vaqt `cli` hisobotlaridagi vaqt bilan
    taqqoslanadi. `None` bo'lsa o'qish BO'LMAGAN.
    """

    kind: str
    name: str
    read_real_us: int | None = None
    synthetic: bool = False
    error: str | None = None
    note: str | None = None

    def age_s(self, now_real_us: int) -> float | None:
        if self.read_real_us is None:
            return None
        return (now_real_us - self.read_real_us) / 1e6

    def is_stale(self, now_real_us: int) -> bool:
        age = self.age_s(now_real_us)
        return age is not None and age > STALE_AFTER_S


def _iso(real_us: int | None) -> str:
    if real_us is None:
        return TEXT_NOT_MEASURED
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(real_us / 1e6))


def source_badge(src: Source, now_real_us: int) -> str:
    """Panel sarlavhasidagi manba nishoni: daraja + nom + o'qilgan vaqt.

    Yoshni `app.js` har sekundda yangilaydi, lekin `stale` klassi SERVER
    tomonida ham qo'yiladi -- JavaScript o'chirilgan bo'lsa ham eskirgan
    o'qish eskirgan ko'rinadi (`app.js` qoida 4).
    """
    tier = SOURCE_TIERS.get(src.kind, src.kind)
    cls = "source stale" if src.is_stale(now_real_us) else "source"
    attrs = ""
    if src.read_real_us is not None:
        attrs = (f' data-read-real-us="{int(src.read_real_us)}"'
                 f' data-stale-after-s="{STALE_AFTER_S:g}"')
    parts = [
        f'<div class="{cls}"{attrs}>',
        f'<span class="tier">{esc(tier)}</span>',
        f'<span class="src-name">{esc(src.name)}</span>',
    ]
    if src.read_real_us is None and src.kind == "document":
        # Hujjat fakti o'qish vaqtiga ega emas -- "o'qilmadi" deyish uni
        # buzilgan manba kabi ko'rsatardi (Yordam skrinshotida ko'rildi).
        pass
    elif src.read_real_us is None:
        parts.append(' <span class="read-at">o\'qilmadi</span>')
    else:
        parts.append(f' <span class="read-at">{esc(_iso(src.read_real_us))}</span>'
                     f' <span class="age"></span>')
    if src.synthetic:
        parts.append(f' <span class="synthetic-inline">{esc(SYNTHETIC_INLINE_TEXT)}</span>')
    if src.error:
        parts.append(f'<div class="err">o\'qish xatosi: {esc(src.error)}</div>')
    if src.note:
        parts.append(f'<div class="note">{esc(src.note)}</div>')
    parts.append("</div>")
    return "".join(parts)


def panel(title: str, src: Source | None, body: str, now_real_us: int) -> str:
    """Panel -- sarlavha + manba nishoni + tana. Manbasiz panel YO'Q."""
    cls = "panel synthetic" if (src is not None and src.synthetic) else "panel"
    badge = source_badge(src, now_real_us) if src is not None else ""
    return (f'<section class="{cls}"><header><h2>{esc(title)}</h2>{badge}</header>'
            f'<div class="body">{body}</div></section>')


def notice(kind: str, heading: str, *paragraphs: str,
           collapsed: bool | None = None) -> str:
    """Izoh bloki. `kind`: honesty | critical | empty.

    YIG'ILADIGAN (jurnal 19 §3): `honesty` izohlari default bo'yicha
    `<details>` -- sarlavha ko'rinadi, uzun tushuntirish bosilganda
    ochiladi. NEGA: uzun izohlar sahifani bosib ketardi va asosiy
    qiymatlar ko'rinmay qolardi. Matn DOM dan olib tashlanMAYDI -- faqat
    yig'iladi. `critical` HECH QACHON yig'ilmaydi: xato yashirilmaydi.
    Ochiq/yopiq holat `app.js` da `data-key` bo'yicha eslab qolinadi.

    SHARTNOMA: `heading` MATN (bu yerda escape qilinadi), `paragraphs` esa
    ALLAQACHON HTML -- chaqiruvchi ularni `esc()` yoki `esc_paragraph()` dan
    o'tkazgan bo'lishi SHART. NEGA shu tartibda: izohlarning ko'pi
    `backtick` bilan kod havolasi beradi va u `<code>` ga aylanishi kerak,
    ya'ni paragraf xom escape'dan ko'proq ishlov talab qiladi. Fayldan
    kelgan matn (xato satri, journal qatori) HAR DOIM `esc()` bilan
    uzatiladi (qoida 5).
    """
    body = "".join(f"<p>{p}</p>" for p in paragraphs)
    if collapsed is None:
        collapsed = kind == "honesty"
    if kind == "critical":
        collapsed = False
    if collapsed:
        return (f'<details class="notice {esc(kind)}" data-key="{esc(heading)}">'
                f'<summary>{esc(heading)}</summary>{body}</details>')
    return (f'<div class="notice {esc(kind)}"><h3>{esc(heading)}</h3>{body}</div>')


def empty_notice(what: str, producer: str, how: str) -> str:
    """"Hali ishga tushirilmadi" holati -- ATAYLAB shunday ko'rinadi (qoida 6).

    Uchta narsani AYTADI: nima yo'q, QAYSI modul uni chiqaradi, va uni
    qanday hosil qilish. NEGA: "buzilgan" bilan "hali yo'q" ni ajratmaslik
    o'quvchini mavjud bo'lmagan natijani qidirishga majburlaydi.
    """
    return notice(
        "empty",
        f"{what} -- {TEXT_NOT_YET_RUN}",
        # `notice()` paragraflarini escape QILMAYDI (chaqiruvchi tayyor HTML
        # beradi), shuning uchun bu yerda `esc_paragraph` MAJBURIY: u matnni
        # escape qiladi va `backtick` ni `<code>` ga aylantiradi.
        esc_paragraph(f"Bu sahifaning ma'lumot manbasi: {producer}."),
        esc_paragraph(f"Uni hosil qilish: {how}"),
        esc_paragraph(
            "Hech qanday eksperiment hali ishga tushirilmadi va hech qanday "
            "natija hali yo'q (`README.md`, `CONTRIBUTING.md`). Shu sababli "
            "bu panel bo'sh -- bu nuqson emas, joriy holat."),
    )


def nosource_notice(key: str) -> str:
    """`MISSING_SOURCES` dagi maydon uchun izoh: NIMA kerak, NEGA yo'q."""
    what, why = MISSING_SOURCES[key]
    return notice("empty", f"{what} -- {TEXT_NO_SOURCE}", esc_paragraph(why),
                  collapsed=True)


def esc_paragraph(text: str) -> str:
    """Izoh matnidagi `backtick` ni `<code>` ga aylantiradi, qolganini escape."""
    out: list[str] = []
    for i, chunk in enumerate(text.split("`")):
        out.append(esc(chunk) if i % 2 == 0 else f"<code>{esc(chunk)}</code>")
    return "".join(out)


def kv(rows: list[tuple[str, str] | tuple[str, str, str]]) -> str:
    """Kalit/qiymat ro'yxati. Qiymat ALLAQACHON HTML (renderdan o'tgan).

    Qator `(yorliq, qiymat)` yoki `(yorliq, qiymat, xom_nom)`. Uchinchi
    element -- manbadagi XOM maydon nomi (`MemTotal`, `cpu.some`): u
    yorliq yonida kichik ikkilamchi matn bo'lib turadi. NEGA: oddiy
    foydalanuvchi odam tilidagi yorliqni o'qiydi, tadqiqotchi esa aynan
    qaysi maydon ekanini ko'radi (jurnal 19 §3).
    """
    items: list[str] = []
    for row in rows:
        k, v = row[0], row[1]
        raw = row[2] if len(row) > 2 else None
        rawhtml = f'<span class="rawkey">{esc(raw)}</span>' if raw else ""
        items.append(f"<dt>{esc(k)}{rawhtml}</dt><dd>{v}</dd>")
    return f'<dl class="kv">{"".join(items)}</dl>'


def table(headers: list[str], rows: list[list[str]],
          empty_text: str | None = None) -> str:
    """Jadval. Yacheykalar ALLAQACHON HTML. Bo'sh jadval SO'Z bilan aytiladi."""
    if not rows:
        text = empty_text or "qator yo'q"   # (f-string ifodasida backslash yo'q)
        return f"<p>{esc(text)}</p>"
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>"
                   for r in rows)
    return (f'<div class="tbl-wrap"><table><thead><tr>{head}</tr></thead>'
            f"<tbody>{body}</tbody></table></div>")


def status_badge(status: str | None) -> str:
    """PASS/WARN/FAIL yoki ok/warn/fail -> ma'noli rangli nishon.

    Rang MA'NO tashiydi (`style.css` qoida 2): yashil = o'tdi, qizil = FAIL.
    Noma'lum holat neytral -- yashil deb HISOBLANMAYDI (fail-closed ruhi).

    BELGI + SO'Z (jurnal 19 §5): rang hech qachon yagona kanal emas -- har
    nishonda belgi (✓ ! ✗ •) va o'zbekcha so'z bor; manbadagi xom qiymat
    (`PASS`, `active`) kichik ikkilamchi matn bo'lib qoladi.
    """
    if status is None:
        return missing_html()
    s = str(status)
    low = s.lower()
    cls = status_class(low)
    word = STATUS_WORDS.get(low)
    icon = STATUS_ICONS[cls]
    raw = (f'<span class="raw">{esc(s)}</span>'
           if word is not None and word != low else "")
    shown = word if word is not None else s
    return (f'<span class="badge {cls}"><span class="ico" aria-hidden="true">'
            f'{icon}</span>{esc(shown)}{raw}</span>')


# Manba holat qiymati -> o'zbekcha so'z. Faqat MA'LUM qiymatlar tarjima
# qilinadi; noma'lumi xom holda ko'rsatiladi (o'ylab topilgan tarjima yo'q).
STATUS_WORDS: dict[str, str] = {
    "pass": "o'tdi", "ok": "yaxshi", "warn": "diqqat", "warning": "diqqat",
    "fail": "xato", "failed": "xato", "error": "xato",
    "active": "faol", "running": "ishlayapti", "loaded": "yuklangan",
    "inactive": "faol emas", "dead": "to'xtagan", "exited": "tugagan",
    "activating": "ishga tushmoqda", "deactivating": "to'xtamoqda",
    "degraded": "qisman ishlayapti", "not-found": "topilmadi",
    "listening": "kutyapti", "waiting": "kutyapti",
}

STATUS_ICONS: dict[str, str] = {
    "ok": "✓", "fail": "✗", "warn": "!", "neutral": "•",
}


def status_class(low: str) -> str:
    """Holat -> `ok` | `fail` | `warn` | `neutral`. Noma'lum -- NEYTRAL."""
    if low in ("pass", "ok", "active", "running"):
        return "ok"
    if low in ("fail", "failed", "error"):
        return "fail"
    if low in ("warn", "warning", "degraded"):
        return "warn"
    return "neutral"


# ===========================================================================
# ma'lumot manbalari -- O'QISH (hisoblash YO'Q, qoida 4)
# ===========================================================================


@dataclass
class Options:
    """Serverning joriy konfiguratsiyasi. "Sozlamalar" sahifasi shuni ko'rsatadi."""

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    interval_s: float = cli.MIN_RATE_WINDOW_S
    cache_s: float = DEFAULT_CACHE_S
    doctor_cache_s: float = DEFAULT_DOCTOR_CACHE_S
    datasets_dir: str = os.path.join(REPO_ROOT, "datasets")
    run_dir: str | None = None
    allow_remote: bool = False
    mark_synthetic: bool = False
    verbose: bool = False


def discover_run_dirs(datasets_dir: str) -> list[str]:
    """`datasets/` ichidagi run kataloglari -- `run_meta.json` BOR bo'lganlari.

    Faqat `run_meta.json` mavjud katalog run hisoblanadi (shartnoma §1.1 uni
    MAJBURIY deydi). Bo'sh yoki yarim katalog run sifatida KO'RSATILMAYDI --
    aks holda dashboard mavjud bo'lmagan run'ni mavjud deb ko'rsatardi.
    """
    out: list[str] = []
    try:
        names = sorted(os.listdir(datasets_dir))
    except OSError:
        return out
    for name in names:
        path = os.path.join(datasets_dir, name)
        if os.path.isfile(os.path.join(path, "run_meta.json")):
            out.append(path)
    return out


def _read_json(path: str) -> tuple[Any, str | None]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh), None
    except OSError as exc:
        return None, repr(exc)
    except (json.JSONDecodeError, ValueError) as exc:
        return None, f"buzuq JSON: {exc!r}"


def _tail_lines(path: str, limit: int) -> tuple[list[str], str | None]:
    """Faylning oxirgi `limit` satri. Matn ISHONCHSIZ -- escape chaqiruvchida."""
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
    except OSError as exc:
        return [], repr(exc)
    return [ln.rstrip("\n") for ln in lines[-limit:]], None


def is_synthetic_run(run_dir: str, run_meta: Any, forced: bool) -> bool:
    """Run sintetikmi. Belgi FAQAT QO'SHILADI, hech qachon olib tashlanmaydi.

    Uchta mustaqil belgi -- har biri YETARLI (mantiqiy YOKI):
      * `--mark-synthetic` berilgan (vizual tekshiruv uchun),
      * katalogda `SYNTHETIC` nomli fayl bor,
      * `run_meta.json` da `"synthetic": true`.

    NEGA FAQAT QO'SHILADI: birorta flag ogohlikni O'CHIRA olmasligi kerak
    (qoida 7). Aks holda "sintetik emas" deb belgilangan sintetik ma'lumot
    paydo bo'lishi mumkin bo'lardi, va bu aynan oldini olmoqchi bo'lgan narsa.
    """
    if forced:
        return True
    if run_dir and os.path.exists(os.path.join(run_dir, "SYNTHETIC")):
        return True
    return bool(isinstance(run_meta, dict) and run_meta.get("synthetic"))


class Gateway:
    """Manbalarni o'qiydi va keshlaydi. HECH NARSA HISOBLAMAYDI (qoida 4).

    Har metod `(data, Source)` qaytaradi. O'qish bajarilmasa `data` `None`
    bo'ladi va `Source.error` sababni AYTADI -- jim muvaffaqiyat YO'Q
    (`cli.py` qoida 3 bilan bir xil fail-closed doktrina).
    """

    def __init__(self, opts: Options) -> None:
        self.opts = opts
        self._live: tuple[float, dict[str, Any], Source] | None = None
        self._doctor: tuple[float, dict[str, Any] | None, Source] | None = None

    # --- 1-daraja: tirik tizim -------------------------------------------

    def live(self) -> tuple[dict[str, Any], Source]:
        """`cli.status_report()` + `cli.health_report()` -- bitta o'qishda.

        Ikkisi birga olinadi, chunki ikkisi ham `sample_psi_rates()` ni
        chaqiradi va u >= 2 s uxlaydi; alohida olinsa sahifa ikki marta
        kutardi va ikki xil o'qish vaqti chiqardi.
        """
        now = time.monotonic()
        if self._live is not None and (now - self._live[0]) < self.opts.cache_s:
            return self._live[1], self._live[2]
        data: dict[str, Any] = {}
        error: str | None = None
        try:
            data["status"] = cli.status_report(self.opts.interval_s)
            data["health"] = cli.health_report(self.opts.interval_s)
        except Exception as exc:  # noqa: BLE001 -- fail-closed, qoida 3
            error = repr(exc)
        src = Source(
            kind="live",
            name="revix.cli status_report() + health_report()",
            read_real_us=cli.real_us() if error is None else None,
            error=error,
        )
        self._live = (now, data, src)
        return data, src

    def doctor(self) -> tuple[dict[str, Any] | None, Source]:
        """`cli.collect_checks()` + `cli.build_report()` -- 18 tekshiruv.

        DIQQAT: `check_cgroup_write` HAQIQIY yozishni sinaydi va o'zidan
        keyin tozalaydi (`cli.py` qoida 4). Bu GUI ning yagona yon ta'siri
        va u `cli doctor` ning o'z yon ta'siri -- GUI yangi narsa qilmaydi.
        """
        now = time.monotonic()
        if self._doctor is not None and (now - self._doctor[0]) < self.opts.doctor_cache_s:
            return self._doctor[1], self._doctor[2]
        data: dict[str, Any] | None = None
        error: str | None = None
        try:
            data = cli.build_report(cli.collect_checks())
        except Exception as exc:  # noqa: BLE001 -- fail-closed
            error = repr(exc)
        src = Source(
            kind="live",
            name="revix.cli collect_checks() + build_report()",
            read_real_us=cli.real_us() if error is None else None,
            error=error,
            note=("`cgroup_write` tekshiruvi bitta throwaway cgroup yaratadi "
                  "va o'chiradi (cli.py qoida 4)"),
        )
        self._doctor = (now, data, src)
        return data, src

    def version(self) -> tuple[dict[str, Any] | None, Source]:
        try:
            data = cli.version_report()
            return data, Source("live", "revix.cli version_report()",
                                read_real_us=cli.real_us())
        except Exception as exc:  # noqa: BLE001
            return None, Source("live", "revix.cli version_report()",
                                error=repr(exc))

    # --- 2-daraja: run artifact'lari -------------------------------------

    def run_dirs(self) -> list[str]:
        if self.opts.run_dir:
            return [self.opts.run_dir]
        return discover_run_dirs(self.opts.datasets_dir)

    def run(self) -> tuple[dict[str, Any] | None, Source]:
        """Run katalogi: `run_meta.json`, `events.jsonl`, `guard.jsonl` (§1.1-1.2).

        Keshsiz: run artifact'lari append-only fayllar, ularni har so'rovda
        qayta o'qish arzon va eskirgan nusxani ko'rsatishdan to'g'riroq.
        """
        dirs = self.run_dirs()
        if not dirs:
            where = self.opts.run_dir or self.opts.datasets_dir
            return None, Source(
                kind="artifact",
                name=f"{where} (run yo'q)",
                note="`run_meta.json` bo'lgan katalog topilmadi",
            )
        run_dir = dirs[-1]
        meta, meta_err = _read_json(os.path.join(run_dir, "run_meta.json"))
        events_path = os.path.join(run_dir, "events.jsonl")
        events: dict[str, Any] | None = None
        if os.path.exists(events_path):
            events = cli.read_events(events_path, limit=EVENTS_LIMIT)
        guard_lines, guard_err = _tail_lines(
            os.path.join(run_dir, "guard.jsonl"), LOG_TAIL_LINES)
        synthetic = is_synthetic_run(run_dir, meta, self.opts.mark_synthetic)
        data = {
            "run_dir": run_dir,
            "run_meta": meta,
            "run_meta_error": meta_err,
            "events": events,
            "events_path": events_path if os.path.exists(events_path) else None,
            "guard_lines": guard_lines,
            "guard_error": guard_err,
            "all_run_dirs": dirs,
        }
        return data, Source(
            kind="artifact",
            name=f"{run_dir} (run_meta.json, events.jsonl, guard.jsonl)",
            read_real_us=cli.real_us(),
            synthetic=synthetic,
            error=meta_err,
        )

    # --- 3-daraja: derived (analysis.json + figura sidecar'lari) ---------

    def derived(self) -> tuple[dict[str, Any] | None, Source]:
        """`analysis.json` (§2.2) + `figures/<nom>.json` sidecar'lari (§3)."""
        run_data, run_src = self.run()
        if run_data is None:
            return None, Source(
                kind="derived",
                name="analysis.json (run yo'q)",
                note="run bo'lmaganda analiz ham yo'q",
            )
        run_dir = run_data["run_dir"]
        apath = os.path.join(run_dir, "analysis.json")
        analysis, aerr = (None, None)
        if os.path.exists(apath):
            analysis, aerr = _read_json(apath)
        figures: dict[str, dict[str, Any]] = {}
        fig_dir = os.path.join(run_dir, "figures")
        for name in FIGURE_NAMES:
            svg = os.path.join(fig_dir, f"{name}.svg")
            side = os.path.join(fig_dir, f"{name}.json")
            sidecar, serr = (None, None)
            if os.path.exists(side):
                sidecar, serr = _read_json(side)
            figures[name] = {
                "svg_exists": os.path.exists(svg),
                "svg_path": svg if os.path.exists(svg) else None,
                "sidecar": sidecar,
                "sidecar_error": serr,
            }
        data = {
            "run_dir": run_dir,
            "analysis": analysis,
            "analysis_path": apath if os.path.exists(apath) else None,
            "analysis_error": aerr,
            "figures": figures,
        }
        return data, Source(
            kind="derived",
            name=(f"{apath} + figures/<nom>.json"
                  if os.path.exists(apath) else f"{apath} (yo'q)"),
            read_real_us=cli.real_us() if os.path.exists(apath) else None,
            synthetic=run_src.synthetic,
            error=aerr,
        )


# ===========================================================================
# panellar
# ===========================================================================


# --- TAXMINIY TALQIN (jurnal 19 §4) ---------------------------------------
#
# PSI `some` stall ulushi (0..1: oynaning qancha qismida KAMIDA BITTA vazifa
# resursni kutib turdi) -> oddiy so'z. Bu chegaralar O'LCHOV EMAS va
# `PREREGISTRATION.md` da YO'Q: ular FAQAT ekrandagi so'z uchun, hech qaysi
# qaror, guard yoki analiz ularni ishlatmaydi. Ekranda har doim
# "taxminiy talqin" deb yoziladi va xom son yonida turadi.
#
# NEGA shu qiymatlar (konservativ): bo'sh desktopda `some` odatda 0.01 dan
# past; 0.05 (oynaning 5 %) kutish allaqachon sezilarli, shuning uchun
# "o'rta" erta boshlanadi; 0.25 (chorak vaqt kutish) -- "yuqori". Ya'ni
# shubhali holatda so'z YUQORIROQ darajani beradi, "hammasi joyida" ni emas.
STALL_LEVEL_MID = 0.05
STALL_LEVEL_HIGH = 0.25
STALL_INTERP_LABEL = "taxminiy talqin"

# Darajaning so'zi va bir jumlali ma'nosi (resurs nomi `{r}` o'rniga).
STALL_WORDS: dict[str, tuple[str, str]] = {
    "low": ("past", "Dasturlar {r} navbatini deyarli kutmayapti."),
    "mid": ("o'rta", "Dasturlar ba'zan {r} navbatini kutyapti."),
    "high": ("yuqori", "Dasturlar ko'p vaqt {r} navbatini kutyapti."),
}


def stall_level(rate: Any) -> str | None:
    """`some` ulushi -> `low` | `mid` | `high`; o'lchanmagan bo'lsa `None`.

    `None` HECH QACHON "past" ga aylanmaydi: o'lchanmagan narsa haqida
    talqin yo'q (qoida 2).
    """
    if rate is None or isinstance(rate, bool):
        return None
    try:
        r = float(rate)
    except (TypeError, ValueError):
        return None
    if r >= STALL_LEVEL_HIGH:
        return "high"
    if r >= STALL_LEVEL_MID:
        return "mid"
    return "low"


def stall_html(rate: Any, reason: str = REASON_NOT_REPORTED) -> str:
    """Xom stall soni + uning taxminiy talqini (so'z). `None` -> "—"."""
    lvl = stall_level(rate)
    if lvl is None:
        return rate_html(rate, reason=reason)
    word = STALL_WORDS[lvl][0]
    return (rate_html(rate, reason=reason)
            + f' <span class="interp" data-level="{lvl}" '
            f'title="{esc(STALL_INTERP_LABEL)}: chegaralar Yordam sahifasida">'
            f"{esc(word)} <small>({esc(STALL_INTERP_LABEL)})</small></span>")


def _host_psi(live: dict[str, Any], resource: str) -> dict[str, Any]:
    """Host scope'ining bitta resursi uchun PSI yozuvi (yo'q bo'lsa `{}`)."""
    psi = ((live.get("status") or {}).get("psi") or {}).get("scopes") or {}
    return ((psi.get("host") or {}).get("resources") or {}).get(resource) or {}


# Resurs mashina nomi -> ekrandagi nom (xom nom qavsda qoladi).
RESOURCE_LABELS = {"cpu": "protsessor (cpu)", "memory": "xotira (memory)",
                   "io": "disk (io)"}


def _psi_scope_rows(psi: dict[str, Any] | None) -> list[list[str]]:
    """PSI scope'lari jadvali. Tezlik `total=` delta'sidan (§7), avgN EMAS."""
    if not isinstance(psi, dict):
        return []
    rows: list[list[str]] = []
    for scope, info in sorted((psi.get("scopes") or {}).items()):
        resources = (info or {}).get("resources") or {}
        for res in cli.PSI_RESOURCES:
            entry = resources.get(res)
            res_label = esc(RESOURCE_LABELS.get(res, res))
            if entry is None:
                # Scope bu resursni BERMADI -- o'lchanmadi, nol emas.
                rows.append([esc(scope), res_label,
                             missing_html(REASON_SCOPE_NO_DATA),
                             missing_html(REASON_SCOPE_NO_DATA),
                             missing_html(REASON_SCOPE_NO_DATA)])
                continue
            rows.append([
                esc(scope), res_label,
                stall_html(entry.get("some_rate")),
                rate_html(entry.get("full_rate")),
                value_html(entry.get("window_us"), unit="us"),
            ])
    return rows


def panel_psi(live: dict[str, Any], src: Source, now_us: int) -> str:
    psi = (live.get("status") or {}).get("psi")
    rows = _psi_scope_rows(psi)
    body = [
        f'<p class="lead">{esc_paragraph(PSI_PLAIN)}</p>',
        notice("honesty", "Tezlik `total=` delta'sidan, `avgN` dan EMAS",
               esc_paragraph(
                   "`PREREGISTRATION.md` §7 muzlatilgan qarori: `avgN` "
                   "eksponensial silliqlangan va 2 s kadensda yangilanadi, "
                   "demak u \"hozir\" ni ko'rsatmaydi. Bu jadvaldagi tezlik "
                   "`cli.sample_psi_rates()` ning `total=` monotonik "
                   "akkumulyator delta'sidan olinadi. GUI uni QAYTA "
                   "HISOBLAMAYDI.")),
    ]
    interval = (psi or {}).get("interval_s")
    body.append(kv([("o'lchov oynasi", value_html(interval, unit="s"), "interval_s"),
                    ("usul", text_html((psi or {}).get("method")), "method")]))
    body.append(table(["guruh (scope)", "resurs", "kimdir kutdi (some)",
                       "hamma kutdi (full)", "oyna"],
                      rows, "PSI scope o'qilmadi"))
    return panel("Bosim (PSI): resursni kutish ulushi", src, "".join(body), now_us)


# PSI ni oddiy tilda bir jumla bilan tushuntirish (Resurslar sahifasi).
PSI_PLAIN = (
    "Har son -- o'lchov oynasining qancha qismida dasturlar shu resursni "
    "KUTIB turgani (0 = hech kim kutmadi, 1 = butun vaqt kutildi). \"Kimdir "
    "kutdi\" -- kamida bitta dastur kutgan, \"hamma kutdi\" -- barcha "
    "dasturlar bir vaqtda to'xtab qolgan. Bu band foizi (CPU %) EMAS."
)


def card_cpu(live: dict[str, Any]) -> str:
    """CPU karta -- cpu_count va PSI CPU stall tezligi. Foiz YO'Q (manba yo'q)."""
    host = (live.get("status") or {}).get("host") or {}
    hostpsi = _host_psi(live, "cpu")
    rows = [
        ("Yadrolar soni", value_html(host.get("cpu_count")), "cpu_count"),
        ("Arxitektura", text_html(host.get("machine")), "machine"),
        ("Kutish: kimdir kutdi", stall_html(hostpsi.get("some_rate") if hostpsi else None),
         "host cpu some"),
        ("Kutish: hamma kutdi", rate_html(hostpsi.get("full_rate") if hostpsi else None),
         "host cpu full"),
        ("Band foizi (%)", nosource_html(), "cpu utilization"),
    ]
    return kv(rows) + nosource_notice("cpu_utilization")


def card_memory(live: dict[str, Any]) -> str:
    """MEMORY karta -- `cli.health_report()["memory"]` (= `/proc/meminfo`)."""
    mem = (live.get("health") or {}).get("memory") or {}
    hostmem = _host_psi(live, "memory")
    return kv([
        ("Jami xotira", kb_html(mem.get("mem_total_kb")), "MemTotal"),
        ("Bo'sh (ishlatsa bo'ladigan)", kb_html(mem.get("mem_available_kb")),
         "MemAvailable"),
        ("Tajriba uchun kerak", kb_html(mem.get("required_kb")), "required_kb"),
        ("Swap (diskdagi zaxira) jami", kb_html(mem.get("swap_total_kb")), "SwapTotal"),
        ("Swap bo'sh", kb_html(mem.get("swap_free_kb")), "SwapFree"),
        ("Kutish: kimdir kutdi", stall_html(hostmem.get("some_rate") if hostmem else None),
         "host memory some"),
        ("Kutish: hamma kutdi", rate_html(hostmem.get("full_rate") if hostmem else None),
         "host memory full"),
    ])


def card_disk(live: dict[str, Any]) -> str:
    """DISK karta -- O'LCHOV MANBASI YO'Q. Faqat PSI IO stall tezligi bor."""
    hostio = _host_psi(live, "io")
    rows = [
        ("Sig'im / band joy", nosource_html(), "statvfs"),
        ("O'qish / yozish tezligi", nosource_html(), "diskstats"),
        ("Kutish: kimdir kutdi", stall_html(hostio.get("some_rate") if hostio else None),
         "host io some"),
        ("Kutish: hamma kutdi", rate_html(hostio.get("full_rate") if hostio else None),
         "host io full"),
    ]
    return kv(rows) + nosource_notice("disk")


def card_network(live: dict[str, Any]) -> str:
    """NETWORK karta -- O'LCHOV MANBASI YO'Q. `live` ataylab ishlatilmaydi."""
    return kv([
        ("Interfeyslar", nosource_html(), "/proc/net/dev"),
        ("Bayt / paket", nosource_html(), "/proc/net/dev"),
        ("Ulanishlar (socket)", nosource_html(), "ss"),
    ]) + nosource_notice("network")


def panel_system_health(live: dict[str, Any], src: Source, now_us: int) -> str:
    """Spetsifikatsiyaning SYSTEM HEALTH bloki: CPU / MEMORY / DISK / NETWORK.

    To'rtta karta bir panelda, va ikkisida (DISK, NETWORK) manba YO'Q --
    bu ochiq yoziladi, bo'sh raqam bilan to'ldirilmaydi (qoida 1).
    """
    health = live.get("health") or {}
    summary = [kv([
        ("Umumiy holat", status_badge(health.get("status")), "health.status"),
        ("Muammolar soni", value_html(len(health["problems"]) if isinstance(
            health.get("problems"), list) else None), "problems"),
        ("Ogohliklar soni", value_html(len(health["warnings"]) if isinstance(
            health.get("warnings"), list) else None), "warnings"),
    ])]
    summary.append('<div class="subgrid">')
    for name, card in (("Protsessor (CPU)", card_cpu(live)),
                       ("Xotira (RAM)", card_memory(live)),
                       ("Disk", card_disk(live)),
                       ("Tarmoq", card_network(live))):
        summary.append(f'<div class="subcard"><h3>{esc(name)}</h3>{card}</div>')
    summary.append("</div>")
    return panel("Tizim holati va resurslar", src, "".join(summary), now_us)


# Unit holati -> (klass, belgi, oddiy so'z). Bosh sahifadagi xizmatlar
# ro'yxati va Xizmatlar jadvali uchun. Shakl ham farq qiladi (to'la doira,
# bo'sh doira, xoch) -- rang yagona kanal emas.
UNIT_PLAIN: dict[str, tuple[str, str, str]] = {
    "running": ("ok", "●", "ishlayapti"),
    "active": ("ok", "●", "ishlayapti"),
    "exited": ("neutral", "○", "ishini tugatgan"),
    "failed": ("fail", "✗", "xato bilan to'xtagan"),
    "dead": ("neutral", "○", "to'xtagan"),
    "inactive": ("neutral", "○", "to'xtagan"),
    "activating": ("neutral", "◐", "ishga tushmoqda"),
    "auto-restart": ("neutral", "◐", "qayta ishga tushmoqda"),
    "deactivating": ("neutral", "◐", "to'xtamoqda"),
}


def unit_plain(u: dict[str, Any]) -> tuple[str, str, str]:
    """Unit -> (klass, belgi, so'z). `failed` HAR DOIM ustun; noma'lum -- neytral."""
    active = str(u.get("active") or "").lower()
    sub = str(u.get("sub") or "").lower()
    if active == "failed" or sub == "failed":
        return UNIT_PLAIN["failed"]
    if sub in UNIT_PLAIN:
        return UNIT_PLAIN[sub]
    if active in UNIT_PLAIN:
        return UNIT_PLAIN[active]
    raw = sub or active
    return ("neutral", "?", raw if raw else "holat noma'lum")


def panel_services(live: dict[str, Any], src: Source, now_us: int) -> str:
    """SERVICES bloki -- `systemctl --user list-units revix*` (per-service state)."""
    units = (live.get("status") or {}).get("units") or {}
    rows: list[list[str]] = []
    for u in units.get("units") or []:
        cls, icon, word = unit_plain(u)
        rows.append([
            text_html(u.get("name")),
            (f'<span class="svc-state {cls}"><span class="dot" aria-hidden="true">'
             f"{icon}</span>{esc(word)}</span>"),
            status_badge(u.get("load")),
            status_badge(u.get("active")),
            status_badge(u.get("sub")),
        ])
    body: list[str] = [f'<p class="lead">{esc_paragraph(SERVICES_PLAIN)}</p>']
    if not units.get("ok", False):
        body.append(notice("critical", "Unit ro'yxati o'qilmadi",
                           esc(units.get("error") or TEXT_NOT_MEASURED)))
    body.append(table(["xizmat (unit)", "holati", "yuklanganmi (load)",
                       "faolmi (active)", "aniq holat (sub)"], rows,
                      "Hozir birorta REVIX xizmati (revix* unit) yo'q -- "
                      "tajriba o'tkazilmayotganda bu NORMAL holat."))
    return panel("REVIX xizmatlari", src, "".join(body), now_us)


SERVICES_PLAIN = (
    "Xizmat (systemd unit) -- fonda ishlaydigan dastur. REVIX tajriba "
    "paytida o'z xizmatlarini (`revix*`) ishga tushiradi, ularni ataylab "
    "to'xtatadi va systemd ularni qanday qayta tiklashini kuzatadi."
)


def panel_slices(live: dict[str, Any], src: Source, now_us: int) -> str:
    """Lab/mon slice holati -- `cli.slice_state()` (cgroup snapshot'i)."""
    slices = (live.get("status") or {}).get("slices") or {}
    body: list[str] = [
        '<p class="lead">Slice -- tajriba dasturlari uchun ajratilgan, xotira '
        "chegarasi qo'yiladigan alohida guruh. Tajriba bo'lmaganda ular "
        "odatda mavjud emas.</p>"]
    for name in (cli.LAB_SLICE, cli.MON_SLICE):
        st = slices.get(name) or {}
        snap = st.get("snapshot")
        rows = [
            ("Mavjudmi", value_html(st.get("exists")), "exists"),
            ("Joylashuv", text_html(st.get("path")), "cgroup path"),
            ("Ichidagi jarayonlar soni", value_html(len(st["procs"]) if isinstance(
                st.get("procs"), list) else None), "procs"),
        ]
        if isinstance(snap, dict):
            rows += [
                ("Hozir ishlatilayotgan xotira", kb_html(
                    None if snap.get("memory_current") is None
                    else int(snap["memory_current"]) // 1024), "memory.current"),
                ("Xotira chegarasi", text_html(snap.get("memory_max")), "memory.max"),
                ("Eng yuqori ishlatilgan", text_html(snap.get("memory_peak")),
                 "memory.peak"),
            ]
        else:
            # Slice yo'q -> cgroup fayllari yo'q, demak sabab `sysfs_absent`
            # (snapshot O'LCHANMADI, nol EMAS).
            rows += [("Hozir ishlatilayotgan xotira",
                      missing_html(REASON_SYSFS_ABSENT), "memory.current"),
                     ("Xotira chegarasi", missing_html(REASON_SYSFS_ABSENT),
                      "memory.max"),
                     ("Eng yuqori ishlatilgan", missing_html(REASON_SYSFS_ABSENT),
                      "memory.peak")]
        role = ("tajriba dasturlari" if name == cli.LAB_SLICE
                else "o'lchov vositalari")
        body.append(f"<h3>{esc(name)} <small>({esc(role)})</small></h3>{kv(rows)}")
    return panel("Tajriba guruhlari (slice)", src, "".join(body), now_us)


def _last_record(events: dict[str, Any] | None,
                 record_type: str | None = None) -> dict[str, Any] | None:
    if not isinstance(events, dict):
        return None
    recs = events.get("records") or []
    for rec in reversed(recs):
        if not isinstance(rec, dict):
            continue
        if record_type is None or rec.get("record_type") == record_type:
            return rec
    return None


def panel_recovery_engine(run: dict[str, Any] | None, src: Source,
                          now_us: int) -> str:
    """RECOVERY ENGINE bloki -- SYSTEMD nima qildi (qoida 8).

    "Oxirgi hodisa / qaror / natija" uchun manba `events.jsonl` (§1.2):
    `unit_state` systemd ning XOM holatini, `action` esa `actor` maydoni
    bilan AYNAN kim harakat qilganini yozadi. REVIX ning qarori sifatida
    hech narsa KO'RSATILMAYDI, chunki bunday qaror qabul qiladigan kod yo'q.
    """
    body = [notice("honesty", "Bu REVIX ning qarori EMAS",
                   esc_paragraph(ENGINE_HONESTY))]
    if run is None:
        body.append(empty_notice(
            "Recovery engine hodisalari",
            "run katalogining `events.jsonl` fayli (shartnoma §1.2)",
            "`python3 -m revix.cli run --run-dir datasets/<nom> --seed <N>` "
            "(va undan oldin `revix doctor` o'tishi SHART).",
        ))
        body.append(kv([("oxirgi hodisa", norun_html()),
                        ("qaror (aktor)", norun_html()),
                        ("natija (disposition)", norun_html())]))
        return panel("Recovery: systemd nima qildi", src, "".join(body), now_us)

    events = run.get("events")
    last = _last_record(events)
    action = _last_record(events, "action")
    end = _last_record(events, "trial_end")
    unit_state = _last_record(events, "unit_state")

    actor = (action or {}).get("actor") if isinstance(action, dict) else None
    rows = [
        ("oxirgi hodisa turi", text_html((last or {}).get("record_type")) if last else norun_html()),
        ("oxirgi hodisa mono_us", value_html((last or {}).get("mono_us")) if last else norun_html()),
        ("oxirgi action aktori", text_html(actor) if action else norun_html()),
        ("action_class", text_html((action or {}).get("action_class")) if action else norun_html()),
        ("oxirgi unit holati", text_html((unit_state or {}).get("active_state")) if unit_state else norun_html()),
        ("natija (disposition)", text_html((end or {}).get("disposition")) if end else norun_html()),
        ("sabab", text_html((end or {}).get("reason")) if end else norun_html()),
    ]
    body.append(kv(rows))
    if action is not None and actor is not None and str(actor).lower() != "systemd":
        body.append(notice(
            "critical", "Aktor systemd emas",
            esc_paragraph(
                "`events.jsonl` dagi `action.actor` maydoni `systemd` dan "
                "boshqa qiymat beradi. Bu panel harakatni AYNAN shu aktorga "
                "atributsiya qiladi va uni REVIX ning qarori deb "
                "ko'rsatMAYDI -- arm C hali yo'q (§13).")))
    return panel("Recovery: systemd nima qildi", src, "".join(body), now_us)


def panel_doctor(doctor: dict[str, Any] | None, src: Source, now_us: int,
                 only_keys: tuple[str, ...] | None = None,
                 title: str = "Avtomatik tekshiruvlar (revix doctor)") -> str:
    """18 doctor tekshiruvi (yoki nomlangan qism-to'plami).

    Har tekshiruv TO'RTTA narsani beradi (`cli.py` qoida 2): holat,
    KUZATILGAN qiymat, KERAKLI qiymat va buzilsa NIMA BO'LADI. GUI
    to'rttasini ham ko'rsatadi -- qisqartirish tekshiruvni "✓" ga
    aylantirardi va u hech narsa isbotlamay qolardi.
    """
    if doctor is None:
        return panel(title, src, notice(
            "critical", "Doctor hisoboti o'qilmadi",
            esc(src.error or TEXT_NOT_MEASURED)), now_us)
    checks = doctor.get("checks") or []
    if only_keys is not None:
        checks = [c for c in checks if c.get("key") in only_keys]
    # Tartib: avval FAIL, keyin WARN, keyin PASS -- muammo yuqorida turadi.
    # Bu faqat TARTIB, hech bir qator tushirib qoldirilmaydi.
    order = {"FAIL": 0, "WARN": 1}
    checks = sorted(checks, key=lambda c: order.get(str(c.get("status")), 2))
    rows: list[list[str]] = []
    for c in checks:
        key = c.get("key")
        plain = CHECK_PLAIN.get(str(key))
        name = (f'<span class="plain-name">{esc(plain)}</span>'
                f'<span class="rawkey">{esc(key)}</span>' if plain
                else text_html(key))
        rows.append([
            name,
            status_badge(c.get("status")),
            text_html(c.get("observed")),
            text_html(c.get("required")),
            text_html(c.get("consequence")),
        ])
    summary = doctor.get("summary") or {}
    body = [kv([
        ("Jami tekshiruvlar", value_html(summary.get("total")), "total"),
        ("O'tdi", value_html(summary.get("pass")), "PASS"),
        ("Diqqat talab qiladi", value_html(summary.get("warn")), "WARN"),
        ("Xato", value_html(summary.get("fail")), "FAIL"),
        ("Xulosa", status_badge("ok" if summary.get("ok") else "fail"), "summary.ok"),
    ])]
    if only_keys is not None:
        body.append(notice(
            "honesty", "Bu QISM-TO'PLAM",
            esc_paragraph(
                "Yuqoridagi hisob BUTUN doctor to'plamining hisobi; "
                "jadvalda esa faqat nomlangan tekshiruvlar ko'rinadi. "
                "Qaysi tekshiruvlar tanlangani ro'yxat sifatida berilgan, "
                "shunda \"tanlanmagan tekshiruv o'tdi\" degan xulosa "
                "chiqarib bo'lmaydi.")))
        body.append(kv([("tanlangan tekshiruvlar",
                         text_html(", ".join(only_keys)))]))
    body.append(table(["tekshiruv", "natija", "hozirgi holat", "talab",
                       "buzilsa nima bo'ladi"],
                      rows, "tekshiruv qatori yo'q"))
    return panel(title, src, "".join(body), now_us)


# `revix doctor` tekshiruv kaliti -> oddiy tildagi savol. Kalit o'zi
# (`memory_headroom`) yonida kichik matn bo'lib qoladi. Kalitlar
# `cli.CHECKS` dagi `check_<kalit>` funksiyalaridan; ro'yxatda yo'q kalit
# xom holda ko'rsatiladi (o'ylab topilgan nom yo'q).
CHECK_PLAIN: dict[str, str] = {
    "systemd_version": "systemd versiyasi yetarlimi?",
    "cgroup_v2": "Resurs guruhlari (cgroup v2) yoqilganmi?",
    "delegated_controllers": "Foydalanuvchiga resurs boshqaruvi berilganmi?",
    "io_delegation": "Disk (IO) boshqaruvi berilganmi?",
    "psi_host": "Tizim bosim o'lchagichi (PSI) bormi?",
    "psi_cgroup": "Guruh darajasida bosim o'lchagichi bormi?",
    "oomd": "Xotira qo'riqchisi (systemd-oomd) xavfli emasmi?",
    "leftover_state": "Oldingi tajribadan qoldiq yo'qmi?",
    "cgroup_write": "Resurs guruhini yaratib bo'ladimi?",
    "memory_headroom": "Bo'sh xotira yetarlimi?",
    "swap_headroom": "Swap (diskdagi zaxira xotira) holati",
    "cpu_governor": "Protsessor chastota rejimi",
    "toolchain_cc": "C kompilyatori bormi?",
    "python_version": "Python versiyasi yetarlimi?",
    "python_modules": "Kerakli Python modullari bormi?",
    "kvm_access": "Virtualizatsiya (KVM) ruxsati bormi?",
    "git_present": "git o'rnatilganmi?",
    "git_clean": "Kod o'zgartirilmaganmi (git toza)?",
}


# `cli.health_report()` muammo/ogohlik matnining BOSHI -> oddiy jumla.
# Xom matn har doim yonida qoladi; mos kelmagan matn xom holda beriladi.
# Tartib muhim: aniqroq prefiks oldin.
HEALTH_PLAIN: tuple[tuple[str, str], ...] = (
    ("MemAvailable o'qilmadi", "Bo'sh xotira miqdorini o'qib bo'lmadi."),
    ("MemAvailable", "Bo'sh xotira tajriba uchun yetmaydi."),
    ("xotira zaxirasi yupqa", "Bo'sh xotira tajriba uchun zo'rg'a yetadi."),
    ("qoldiq unit ro'yxati o'qilmadi",
     "Oldingi tajribadan qoldiq bor-yo'qligini tekshirib bo'lmadi."),
    ("qoldiq holat", "Oldingi tajribadan qolgan obyektlar yangi tajribaga xalal beradi."),
    ("boshqa revix* obyektlar", "Tizimda boshqa REVIX obyektlari bor (xalal bermaydi)."),
    ("oomd kill authority, duration ANIQLANMADI",
     "Xotira qo'riqchisi (systemd-oomd) dasturlarni o'chira oladi, sozlamasi noma'lum."),
    ("oomd duration",
     "Xotira qo'riqchisi (systemd-oomd) tajriba dasturlarini juda tez o'chirishi mumkin."),
    ("oomd kill authority",
     "Xotira qo'riqchisi (systemd-oomd) yoqilgan: tajribada REVIX guard majburiy."),
)


def plain_health_item(text: Any) -> str | None:
    """Health muammo/ogohlik matni -> oddiy jumla (topilmasa `None`)."""
    s = str(text)
    for prefix, plain in HEALTH_PLAIN:
        if s.startswith(prefix):
            return plain
    if "memory.full tezligi" in s:
        return "Kompyuter hozir xotira bosimi ostida."
    return None


def health_item_html(text: Any) -> str:
    """Bitta muammo/ogohlik: oddiy jumla + xom matn (kichik). Escape bilan."""
    plain = plain_health_item(text)
    raw = f'<span class="rawline">{esc(text)}</span>'
    if plain is None:
        return f'<span class="plainline">{esc(text)}</span>'
    return f'<span class="plainline">{esc(plain)}</span>{raw}'


def panel_health_detail(live: dict[str, Any], src: Source, now_us: int) -> str:
    """`cli.health_report()` ning muammo/ogohlik/oomd/qoldiq bo'limlari."""
    health = live.get("health") or {}
    oom = health.get("oomd_risk") or {}
    left = health.get("leftover") or {}
    problems = health.get("problems")
    warnings = health.get("warnings")
    body: list[str] = []
    for label, items in (("Muammolar", problems), ("Ogohliklar", warnings)):
        body.append(f"<h3>{esc(label)}</h3>")
        if items is None:
            body.append(f"<p>{missing_html()}</p>")
        elif not items:
            body.append(f"<p>{value_html(0)} -- ro'yxat o'qildi va bo'sh edi</p>")
        else:
            body.append('<ul class="items">' + "".join(
                f"<li>{health_item_html(x)}</li>" for x in items) + "</ul>")
    body.append("<h3>Tafsilot</h3>")
    body.append(kv([
        ("Umumiy xulosa", status_badge(health.get("status")), "health.status"),
        ("Foydalanuvchi sessiyasida xotira bosimi (hamma kutdi)",
         rate_html((health.get("psi") or {}).get("user_memory_full_rate")),
         "user memory.full"),
        ("Xotira qo'riqchisi dasturlarni o'chira oladimi",
         value_html(oom.get("kill_authority")), "oomd kill_authority"),
        ("Qo'riqchi rejimi", text_html(oom.get("mode")), "oomd mode"),
        ("Qo'riqchi bosim chegarasi, %", value_html(oom.get("limit_percent")),
         "oomd limit_percent"),
        ("Qo'riqchi kutish vaqti", value_html(oom.get("duration_s"), unit="s"),
         "oomd duration_s"),
        ("REVIX guard ruxsat etgan eng uzoq bosim",
         value_html(oom.get("guard_sustain_max_s"), unit="s"), "guard_sustain_max_s"),
        ("Qo'riqchi xavfi yumshatilganmi", value_html(oom.get("mitigated")),
         "mitigated"),
        ("Qoldiq xizmatlar so'rovi muvaffaqiyatli",
         value_html(left.get("unit_query_ok")), "unit_query_ok"),
    ]))
    return panel("Sog'liq tafsiloti (revix health)", src, "".join(body), now_us)


def panel_run_meta(run: dict[str, Any] | None, src: Source, now_us: int) -> str:
    """`run_meta.json` majburiy maydonlari (shartnoma §1.1).

    `governor` va `scaling_driver` ATAYLAB `None` ko'rinishida qoldiriladi:
    bu muhitda `cpufreq` sysfs interfeysi YO'Q, demak ular o'lchanMADI va
    HECH QACHON `0` emas (`PREREGISTRATION.md` §15.4).
    """
    if run is None:
        return panel("Run metadata'si (run_meta.json)", src, empty_notice(
            "Run metadata'si",
            "`revix.driver` yozadigan `run_meta.json` (shartnoma §1.1)",
            "`python3 -m revix.cli run --run-dir datasets/<nom> --seed <N>`",
        ), now_us)
    meta = run.get("run_meta")
    if not isinstance(meta, dict):
        return panel("Run metadata'si (run_meta.json)", src, notice(
            "critical", "`run_meta.json` o'qilmadi",
            esc(run.get("run_meta_error") or TEXT_NOT_MEASURED)), now_us)
    gen = meta.get("guest_generation")
    rows = [
        ("run_id", text_html(meta.get("run_id"))),
        ("session_id", text_html(meta.get("session_id"))),
        ("run_mode", text_html(meta.get("run_mode"))),
        ("boot_id", text_html(meta.get("boot_id"))),
        ("guest_generation pid1_starttime_ticks",
         value_html((gen or {}).get("pid1_starttime_ticks")) if isinstance(gen, dict)
         else missing_html()),
        ("preregistration_sha256", text_html(meta.get("preregistration_sha256"))),
        ("preregistration_version", text_html(meta.get("preregistration_version"))),
        ("git_commit", text_html(meta.get("git_commit"))),
        ("git_dirty", value_html(meta.get("git_dirty"))),
        ("rng_seed", value_html(meta.get("rng_seed"))),
        ("schedule_digest", text_html(meta.get("schedule_digest"))),
        ("t_trial_us", value_html(meta.get("t_trial_us"), unit="us")),
        ("systemd_version", text_html(meta.get("systemd_version"))),
        ("cpu_model", text_html(meta.get("cpu_model"))),
        ("cpu_count", value_html(meta.get("cpu_count"))),
        ("mem_total_kb", kb_html(meta.get("mem_total_kb"))),
        # §15.4: `cpufreq` sysfs interfeysi bu muhitda umuman eksport
        # qilinmaydi -> sabab AYNAN `sysfs_absent`, umumiy "not_reported" emas.
        ("governor", value_html(meta.get("governor"),
                                reason=REASON_SYSFS_ABSENT)),
        ("scaling_driver", value_html(meta.get("scaling_driver"),
                                      reason=REASON_SYSFS_ABSENT)),
        ("python_version", text_html(meta.get("python_version"))),
    ]
    body = [kv(rows), notice(
        "honesty", "`governor` / `scaling_driver` -- o'lchanMADI, nol EMAS",
        esc_paragraph(
            "`PREREGISTRATION.md` §15.4: bu muhitda `cpufreq` sysfs "
            "interfeysi umuman eksport qilinmaydi, demak bu ikki maydon "
            "`None` -- ma'nosi \"o'lchanmadi\". `0` bo'lsa u \"o'lchandi va "
            "nolga teng\" degan ma'noni berardi, bu esa yolg'on bo'lardi. "
            "DVFS mavjud bo'lishi MUMKIN va butunlay o'lchanmaydi."))]
    return panel("Run metadata'si (run_meta.json)", src, "".join(body), now_us)


def panel_events(run: dict[str, Any] | None, src: Source, now_us: int) -> str:
    """`events.jsonl` -- `cli.read_events()` orqali (qismli oxirgi qator tolerant)."""
    if run is None:
        return panel("Recovery hodisalari (events.jsonl)", src, empty_notice(
            "Recovery hodisalari oqimi",
            "`revix.driver` yozadigan `events.jsonl` (shartnoma §1.2)",
            "`python3 -m revix.cli run --run-dir datasets/<nom> --seed <N>`",
        ), now_us)
    events = run.get("events")
    if not isinstance(events, dict):
        return panel("Recovery hodisalari (events.jsonl)", src, empty_notice(
            "Recovery hodisalari oqimi",
            "run katalogining `events.jsonl` fayli (shartnoma §1.2)",
            "driver'ni shu run katalogi uchun ishga tushirish",
        ), now_us)
    body: list[str] = []
    if events.get("error"):
        body.append(notice("critical", "`events.jsonl` o'qilmadi",
                           esc(events["error"])))
    body.append(kv([
        ("fayl", text_html(events.get("file"))),
        ("record", value_html(events.get("count"))),
        ("umumiy satr", value_html(events.get("total_lines"))),
        ("mos kelgan", value_html(events.get("matched"))),
        ("qismli oxirgi qator", value_html(events.get("truncated_tail"))),
        ("buzuq qatorlar", value_html(len(events["bad_lines"]) if isinstance(
            events.get("bad_lines"), list) else None)),
    ]))
    if events.get("truncated_tail"):
        body.append(notice(
            "honesty", "Oxirgi qator qismli -- bu XATO EMAS",
            esc_paragraph(
                "JSONL append-only va yozuvchi `fsync` ni DAVRIY qiladi, "
                "demak jarayon o'lganda oxirgi qator yarim yozilgan bo'lishi "
                "normal (`cli.read_events` docstring'i). O'RTADAGI buzuq "
                "qator -- boshqa gap va u \"buzuq qatorlar\" hisobiga "
                "tushadi.")))
    types = events.get("types") or {}
    body.append("<h3>Record turlari</h3>")
    body.append(table(["record_type", "soni"],
                      [[text_html(k), value_html(v)]
                       for k, v in sorted(types.items(), key=lambda kv_: str(kv_[0]))],
                      "record turi yo'q"))
    rows: list[list[str]] = []
    for rec in (events.get("records") or []):
        if not isinstance(rec, dict):
            continue
        rows.append([
            value_html(rec.get("seq")),
            value_html(rec.get("mono_us")),
            text_html(rec.get("record_type")),
            text_html(rec.get("trial_id")),
            # Payload -- FAYLDAN kelgan ishonchsiz matn (qoida 5).
            f'<pre class="raw">{esc(json.dumps(rec, ensure_ascii=False, sort_keys=True))}</pre>',
        ])
    body.append("<h3>Record'lar</h3>")
    body.append(table(["seq", "mono_us", "record_type", "trial_id", "xom record"],
                      rows, "record yo'q"))
    return panel("Recovery hodisalari (events.jsonl)", src, "".join(body), now_us)


def exclusion_rate_html(exclusions: Any) -> str:
    """Eksklyuziya darajasi -- TO'PLAMI NOMLANMASA KO'RSATILMAYDI (§16.4).

    `PREREGISTRATION.md` §16.4 ning majburiy hisobot qoidasi: *"Har qanday
    maqolada, jadvalda yoki `analysis.json` da berilgan eksklyuziya darajasi
    QAYSI to'plam ustida hisoblanganini NOMLASHI SHART ... Nomlanmagan
    eksklyuziya darajasi takrorlanuvchi emas va natija sifatida
    berilmaydi."*

    Shu sababli bu funksiya `rate` ni FAQAT to'plam nomi bilan birga
    bosadi. `by_set` bo'lsa har to'plam ALOHIDA qator bo'ladi (§16.4 aynan
    shuni talab qiladi: ikki to'plam ikki daraja). Faqat yalang'och `rate`
    bo'lsa va `rate_set` bo'lmasa -- SON BOSILMAYDI va sabab yoziladi.
    Busiz GUI nomlanmagan darajani natija sifatida tarqatardi.
    """
    if not isinstance(exclusions, dict):
        return f"<p>{norun_html()}</p>"
    by_set = exclusions.get("by_set")
    out: list[str] = []
    if isinstance(by_set, dict) and by_set:
        rows: list[list[str]] = []
        for key, blk in sorted(by_set.items()):
            if not isinstance(blk, dict):
                continue
            name = blk.get("set") or key
            rows.append([
                text_html(name),
                text_html(blk.get("description")),
                value_html(blk.get("rate")),
                value_html(blk.get("n_total")),
                value_html(blk.get("n_included")),
                value_html(blk.get("n_excluded")),
            ])
        out.append(table(
            ["to'plam (NOMLANGAN)", "ta'rifi", "daraja", "n_total",
             "n_included", "n_excluded"], rows, "to'plam yo'q"))
    rate = exclusions.get("rate")
    rate_set = exclusions.get("rate_set")
    if rate is None:
        out.append(kv([("yuqori darajadagi `rate`", missing_html())]))
    elif not rate_set:
        out.append(notice(
            "critical",
            "Eksklyuziya darajasi KO'RSATILMADI -- to'plami nomlanmagan",
            esc_paragraph(
                "`analysis.json` da `exclusions.rate` bor, lekin `rate_set` "
                "yo'q. `PREREGISTRATION.md` §16.4: nomlanmagan eksklyuziya "
                "darajasi takrorlanuvchi EMAS va natija sifatida berilmaydi "
                "-- binar `P(VR)` maxraji bilan survival/`k/n` analiz "
                "to'plami turli darajalar beradi. Shu sababli raqamning "
                "o'zi bu yerda bosilmaydi: qaysi to'plam ekani ma'lum "
                "bo'lmaganda u talqin qilinmaydi.")))
    else:
        out.append(kv([
            (f"daraja ({rate_set})", value_html(rate)),
            ("to'plam nomi", text_html(rate_set)),
            ("n_total", value_html(exclusions.get("n_total"))),
            ("n_excluded", value_html(exclusions.get("n_excluded"))),
            ("n_primary", value_html(exclusions.get("n_primary"))),
        ]))
    by_reason = exclusions.get("by_reason")
    out.append("<h3>Sabab bo'yicha</h3>")
    if not isinstance(by_reason, dict):
        out.append(f"<p>{missing_html()}</p>")
    else:
        out.append(table(["sabab", "soni"],
                         [[text_html(k), value_html(v)]
                          for k, v in sorted(by_reason.items())],
                         "sabab yozilmagan"))
    out.append(notice(
        "honesty", "Eksklyuziya darajasi -- NATIJA, yashirilmaydi",
        esc_paragraph(
            "`PREREGISTRATION.md` §12: `contaminated` va `aborted_guard` "
            "trial'lar birlamchi analizdan chiqariladi, LEKIN ularning "
            "ulushi natija sifatida beriladi. Yuqori eksklyuziya darajasi "
            "o'zi natija.")))
    return "".join(out)


def panel_primary(analysis: Any, src: Source, now_us: int) -> str:
    """`analysis.json` ning `primary` bloki (§2.2) -- O'QILADI, hisoblanMAYDI."""
    if not isinstance(analysis, dict):
        return panel("Birlamchi endpoint", src, empty_notice(
            "Birlamchi endpoint natijasi",
            "`revix.analyze` yozadigan `analysis.json` (shartnoma §2.2)",
            "`python3 -m revix.cli analyze --trials <...> --run-meta <...> "
            "--out datasets/<run>/analysis.json`",
        ), now_us)
    pri = analysis.get("primary")
    if not isinstance(pri, dict):
        return panel("Birlamchi endpoint", src, notice(
            "critical", "`primary` bloki yo'q",
            esc_paragraph(
                "`analysis.json` o'qildi, lekin §2.2 ning `primary` kaliti "
                "yo'q. Bu kalit MAJBURIY MINIMUM (§2.8), shuning uchun "
                "uning o'rniga hech narsa ko'rsatilmaydi.")), now_us)
    rd = pri.get("risk_difference") or {}
    rows = [
        ("endpoint", text_html(pri.get("endpoint"))),
        ("arm / qamrov", text_html(pri.get("arm") or pri.get("scope"))),
        ("test", text_html(pri.get("test"))),
        ("statistika", value_html(pri.get("statistic"))),
        ("p qiymati", value_html(pri.get("p_value"))),
        ("yo'nalish", text_html(pri.get("direction"))),
        ("CI darajasi", value_html(pri.get("ci_level"))),
        ("recovered_within_horizon", text_html(pri.get("recovered_within_horizon"))),
        ("t_trial_us (horizon)", value_html(analysis.get("t_trial_us"), unit="us")),
        ("falsifikatsiya qilindi", value_html(pri.get("falsified"))),
        ("falsifikatsiya qoidasi", text_html(pri.get("falsification_rule"))),
        ("RD kontrasti", text_html(rd.get("contrast"))),
        ("RD bahosi", value_html(rd.get("estimate"))),
        ("RD CI pastki", value_html(rd.get("ci_lower"))),
        ("RD CI yuqori", value_html(rd.get("ci_upper"))),
        ("RD CI usuli", text_html(rd.get("ci_method"))),
    ]
    cells = pri.get("cells")
    body = [kv(rows)]
    if pri.get("ci_level") is None:
        body.append(notice(
            "honesty", "CI darajasi e'lon qilinmagan",
            esc_paragraph(
                "`primary.ci_level` yo'q, shuning uchun bu yerda \"95%\" "
                "YOZILMAYDI (shartnoma §3.1, §2.8). CI chegaralari o'z "
                "qiymati bilan beriladi, darajasi esa o'lchanmadi.")))
    body.append("<h3>Yacheykalar (pressure darajasi bo'yicha)</h3>")
    if not isinstance(cells, list):
        body.append(f"<p>{missing_html()}</p>")
    else:
        body.append(table(
            ["daraja", "arm", "k", "n", "p_hat", "CI pastki", "CI yuqori", "CI usuli"],
            [[text_html(c.get("level")), text_html(c.get("arm")),
              value_html(c.get("k")), value_html(c.get("n")),
              value_html(c.get("p_hat")), value_html(c.get("ci_lower")),
              value_html(c.get("ci_upper")), text_html(c.get("ci_method"))]
             for c in cells if isinstance(c, dict)],
            "yacheyka yo'q"))
    return panel("Birlamchi endpoint", src, "".join(body), now_us)


def panel_figures(derived: dict[str, Any] | None, src: Source,
                  now_us: int) -> str:
    """Figura + uning O'Z sidecar raqamlari (§3). SVG QAYTA CHIZILMAYDI (qoida 10)."""
    if derived is None or not derived.get("analysis_path"):
        return panel("Figuralar", src, empty_notice(
            "Figuralar va ularning raqam sidecar'lari",
            "`revix.figures` yozadigan `figures/<nom>.svg` + `figures/<nom>.json` "
            "(shartnoma §3)",
            "`python3 -m revix.cli figures --analysis datasets/<run>/analysis.json "
            "--out-dir datasets/<run>`",
        ), now_us)
    figures = derived.get("figures") or {}
    body: list[str] = []
    for name in FIGURE_NAMES:
        info = figures.get(name) or {}
        body.append(f"<h3>{esc(name)}</h3>")
        if info.get("svg_exists"):
            body.append(
                f'<figure class="figure">'
                f'<img src="/figure/{esc(name)}.svg" alt="{esc(name)}">'
                f"<figcaption>{esc(info.get('svg_path'))}</figcaption></figure>")
        else:
            body.append(f"<p>SVG: {norun_html()}</p>")
        sidecar = info.get("sidecar")
        if info.get("sidecar_error"):
            body.append(notice("critical", f"{name}.json o'qilmadi",
                               esc(info["sidecar_error"])))
        elif not isinstance(sidecar, dict):
            body.append(f"<p>sidecar raqamlari: {norun_html()}</p>")
        else:
            body.append(kv([("figura holati", status_badge(sidecar.get("status"))),
                            ("analysis_sha256", text_html(sidecar.get("analysis_sha256")))]))
            body.append(
                f'<pre class="raw">{esc(json.dumps(sidecar, ensure_ascii=False, indent=2, sort_keys=True))}</pre>')
    body.append(notice(
        "honesty", "Raqamlar figuradan EMAS, sidecar'dan",
        esc_paragraph(
            "Shartnoma §3: har figura yonida `figures/<nom>.json` -- "
            "figurani hosil qilgan AYNAN raqamlar, shunda figura ko'z bilan "
            "emas, raqam bilan tekshiriladi. GUI SVG ni qayta chizmaydi va "
            "sidecar'da bo'lmagan hech narsani ko'rsatmaydi.")))
    return panel("Figuralar", src, "".join(body), now_us)


def panel_logs(run: dict[str, Any] | None, src: Source, now_us: int) -> str:
    """`guard.jsonl` xom satrlari -- ISHONCHSIZ MATN, escape qilinadi (qoida 5)."""
    if run is None:
        return panel("Guard oqimi (guard.jsonl)", src, empty_notice(
            "Guard log oqimi",
            "`revix.guard` yozadigan `guard.jsonl` (mustaqil jarayon)",
            "driver run'i (guard birinchi ishga tushadi, oxirida to'xtadi)",
        ), now_us)
    lines = run.get("guard_lines") or []
    body: list[str] = []
    if run.get("guard_error"):
        body.append(notice("critical", "`guard.jsonl` o'qilmadi",
                           esc(run["guard_error"])))
    body.append(kv([("ko'rsatilgan satr", value_html(len(lines))),
                    ("ko'rsatish chegarasi", value_html(LOG_TAIL_LINES))]))
    body.append(notice(
        "honesty", "Bu matn SAHIFA UCHUN KIRISH MA'LUMOTI, markup emas",
        esc_paragraph(
            "`guard.jsonl` ga mustaqil guard jarayoni yozadi va satrlar "
            "tashqi matn hisoblanadi (qoida 5). Har satr "
            "`html.escape(quote=True)` dan o'tadi va `<pre>` ichida xom "
            "holda ko'rsatiladi -- talqin ham, qisqartirish ham yo'q.")))
    if not lines:
        body.append(f"<p>{norun_html()}</p>")
    else:
        body.append('<pre class="raw">'
                    + "\n".join(esc(ln) for ln in lines) + "</pre>")
    return panel("Guard oqimi (guard.jsonl)", src, "".join(body), now_us)


# ===========================================================================
# sahifalar
# ===========================================================================


@dataclass
class Context:
    """Bir so'rovning render konteksti."""

    opts: Options
    gw: Gateway
    now_real_us: int


# ===========================================================================
# BOSH SAHIFA -- oddiy til (jurnal 19 §1)
# ===========================================================================
#
# Bosh sahifa 10 soniyada uchta savolga javob beradi: tizim yaxshimi? REVIX
# nima? nima qilsam bo'ladi? QOIDALAR o'zgarmaydi: har son manbadan
# (`cli.health_report()` / `cli.status_report()`), o'lchanmagan -> "—",
# talqin -- har doim "taxminiy talqin" deb belgilangan.

# Umumiy holat -> (klass, belgi, sarlavha shabloni). `{n}` = soni.
HERO_TEXT: dict[str, tuple[str, str, str]] = {
    "ok": ("ok", "✓", "Tizim yaxshi holatda"),
    "warn": ("warn", "!", "Diqqat: {n} ta ogohlik bor"),
    "fail": ("fail", "✗", "Muammo bor: {n} ta muammo topildi"),
    "unknown": ("neutral", "?", "Tizim holatini o'qib bo'lmadi"),
}

HERO_OK_SUB = ("Bo'sh xotira, tajriba qoldiqlari, xotira qo'riqchisi va xotira "
               "bosimi tekshirildi -- muammo yo'q.")
HERO_LIST_MAX = 3

REVIX_WHAT = (
    "REVIX -- tadqiqot stendi: Linux'da ishdan chiqqan xizmat (dastur) xotira "
    "yoki protsessor tanqisligi paytida qanchalik tez va to'g'ri qayta "
    "tiklanishini o'lchaydi.",
    "Bu ekran faqat O'QIYDI: hech narsani o'zgartirmaydi, tajriba boshlamaydi.",
)


def freshness_html(src: Source, now_real_us: int) -> str:
    """Ixcham "qachon o'qildi" satri. `app.js` yoshini yangilaydi, eskirsa
    `stale` qo'yadi; server ham `stale` ni o'zi qo'yadi (JS siz ham)."""
    if src.read_real_us is None:
        err = f" -- {esc(src.error)}" if src.error else ""
        return (f'<span class="fresh" title="{esc(src.name)}">'
                f"Ma'lumot o'qilmadi{err}</span>")
    cls = "fresh stale" if src.is_stale(now_real_us) else "fresh"
    return (f'<span class="{cls}" data-read-real-us="{int(src.read_real_us)}"'
            f' data-stale-after-s="{STALE_AFTER_S:g}" title="manba: {esc(src.name)}">'
            f"Ma'lumot o'qildi: <span class=\"read-at\">"
            f"{esc(_iso(src.read_real_us)[-8:])}</span> "
            f'<span class="age"></span></span>')


def home_hero(live: dict[str, Any], src: Source, now_us: int,
              more_link: bool = True, show_items: bool = True) -> str:
    """Bitta katta holat jumlasi -- FAQAT `health_report()` dan.

    Holat so'zi `health.status` dan (ok / warn / fail), son -- muammo yoki
    ogohliklar ro'yxati uzunligidan. Boshqa hech narsa (masalan, stall
    talqini) bu jumlaga TA'SIR QILMAYDI.
    """
    health = live.get("health") or {}
    status = health.get("status")
    problems = health.get("problems") if isinstance(health.get("problems"), list) else None
    warnings = health.get("warnings") if isinstance(health.get("warnings"), list) else None
    key = status if status in ("ok", "warn", "fail") else "unknown"
    cls, icon, title = HERO_TEXT[key]
    items: list[Any] = []
    extra_warn = 0
    if key == "fail":
        # Sarlavha "N ta muammo" deydi -- ro'yxatda ham FAQAT muammolar;
        # ogohliklar soni alohida qatorda (aralashtirilsa son mos kelmasdi).
        items = list(problems or [])
        extra_warn = len(warnings or [])
        title = title.format(n=len(problems or []))
    elif key == "warn":
        items = list(warnings or [])
        title = title.format(n=len(warnings or []))
    sub: list[str] = []
    if key == "ok":
        sub.append(f'<p class="hero-sub">{esc(HERO_OK_SUB)}</p>')
    elif key == "unknown":
        why = src.error or "health hisoboti holat bermadi"
        sub.append(f'<p class="hero-sub">Sabab: {esc(why)}</p>')
    if items and show_items:
        lis = "".join(f"<li>{health_item_html(x)}</li>"
                      for x in items[:HERO_LIST_MAX])
        more = ""
        if len(items) > HERO_LIST_MAX:
            more = (f'<li class="more">yana {len(items) - HERO_LIST_MAX} ta '
                    f"-- Tizim holati sahifasida</li>")
        if extra_warn:
            more += (f'<li class="more">va {extra_warn} ta ogohlik -- Tizim '
                     f"holati sahifasida</li>")
        sub.append(f'<ul class="hero-items">{lis}{more}</ul>')
    elif items:
        sub.append('<p class="hero-sub">Tafsilot pastda.</p>')
    return (
        f'<section class="hero {cls}" data-status="{esc(key)}">'
        f'<div class="hero-icon" aria-hidden="true">{icon}</div>'
        f'<div class="hero-text"><p class="hero-title">{esc(title)}</p>'
        f'{"".join(sub)}'
        f'<p class="hero-meta">{freshness_html(src, now_us)} '
        f'<span class="basis">manba: revix health</span></p></div>'
        + ('<a class="hero-more" href="/system-health">Batafsil &rarr;</a>'
           if more_link else "")
        + "</section>")


def _card(title: str, field_name: str, big: str, lines: list[str],
          extra: str = "", foot: str = "") -> str:
    """Bosh sahifa resurs kartasi. `big` va `lines` ALLAQACHON HTML."""
    ls = "".join(f'<p class="line">{x}</p>' for x in lines)
    f = f'<p class="foot">{foot}</p>' if foot else ""
    return (f'<section class="rcard" data-card="{esc(field_name)}">'
            f'<h2>{esc(title)}</h2>'
            f'<div class="big" data-field="{esc(field_name)}">{big}</div>'
            f"{extra}{ls}{f}</section>")


def _stall_line(rate: Any, resource_word: str) -> str:
    """Kutish darajasi jumlasi (taxminiy talqin) yoki "—" + sabab."""
    lvl = stall_level(rate)
    if lvl is None:
        return (f"Kutish darajasi: {missing_html(REASON_SCOPE_NO_DATA)}")
    word, meaning = STALL_WORDS[lvl]
    return (f'Kutish: <strong class="interp" data-level="{lvl}">{esc(word)}</strong> '
            f'<small>({esc(STALL_INTERP_LABEL)})</small><br>'
            f'<span class="muted">{esc(meaning.format(r=resource_word))}</span>')


def home_cpu(live: dict[str, Any]) -> str:
    host = (live.get("status") or {}).get("host") or {}
    rate = _host_psi(live, "cpu").get("some_rate")
    count = host.get("cpu_count")
    big = (value_html(count, unit="yadro") if count is not None
           else missing_html(REASON_NOT_REPORTED))
    foot = (f'PSI cpu some = {rate_html(rate)} &middot; band foizi (CPU %) '
            f"o'lchanmaydi" if rate is not None else
            "band foizi (CPU %) o'lchanmaydi")
    return _card("Protsessor (CPU)", "cpu_count", big,
                 [_stall_line(rate, "protsessor")], foot=foot)


def home_memory(live: dict[str, Any]) -> str:
    """RAM: band / jami + chiziq. Band = MemTotal - MemAvailable.

    Bu GUI dagi YAGONA arifmetika (ayirish) va u ekranda asosi bilan
    yoziladi (`band = jami − bo'sh`). NEGA ruxsat: bu analiz emas, bir
    manbaning (`/proc/meminfo`) ikki maydoni orasidagi ko'rsatish farqi;
    ikkala maydon ham yonida o'z qiymati bilan turadi (jurnal 19 §4).
    """
    health = live.get("health") or {}
    mem = health.get("memory") or {}
    total = mem.get("mem_total_kb")
    avail = mem.get("mem_available_kb")
    need = mem.get("required_kb")
    ok_ints = all(isinstance(v, int) and not isinstance(v, bool)
                  for v in (total, avail))
    if ok_ints and total > 0 and 0 <= avail <= total:
        used = total - avail
        big = (f'<span class="val v-num">{esc(cli.human_kb(used))}</span>'
               f' <span class="of">/ {esc(cli.human_kb(total))}</span>')
        bar = (f'<progress class="bar" max="{int(total)}" value="{int(used)}"'
               f' aria-label="band xotira">{esc(cli.human_kb(used))}</progress>')
    else:
        big = missing_html(REASON_NOT_REPORTED if total is None or avail is None
                           else REASON_SOURCE_ERROR)
        bar = ""
    lines = [f"Bo'sh: {kb_html(avail)}"]
    verdict = memory_verdict(health)
    if need is not None:
        v = f" &rarr; {verdict}" if verdict else ""
        lines.append(f"Tajriba uchun kerak: {kb_html(need)}{v}")
    return _card("Xotira (RAM)", "mem", big, lines, extra=bar,
                 foot="band = jami &minus; bo'sh (MemTotal &minus; MemAvailable)")


def memory_verdict(health: dict[str, Any]) -> str:
    """"Yetadimi?" -- FAQAT `cli.health_report()` hukmidan (o'zimiz solishtirmaymiz)."""
    problems = health.get("problems")
    warnings = health.get("warnings")
    if not isinstance(problems, list) or not isinstance(warnings, list):
        return ""
    if any(str(p).startswith("MemAvailable") for p in problems):
        return '<span class="verdict fail">✗ yetmaydi</span>'
    if any(str(w).startswith("xotira zaxirasi yupqa") for w in warnings):
        return '<span class="verdict warn">! zo\'rg\'a yetadi</span>'
    return '<span class="verdict ok">✓ yetadi</span>'


def home_disk(live: dict[str, Any]) -> str:
    rate = _host_psi(live, "io").get("some_rate")
    return _card("Disk", "disk", nosource_html(),
                 ["REVIX disk hajmini o'lchamaydi.",
                  _stall_line(rate, "disk")],
                 foot=(f"PSI io some = {rate_html(rate)}" if rate is not None
                       else ""))


def home_network(_live: dict[str, Any]) -> str:
    return _card("Tarmoq", "network", nosource_html(),
                 ["REVIX tarmoqni o'lchamaydi.",
                  '<span class="muted">Bu tajriba tarmoqdan foydalanmaydi, '
                  "shuning uchun tarmoq ko'rsatkichi yo'q -- bu xato emas.</span>"])


def home_services(live: dict[str, Any]) -> str:
    """Xizmatlar mini-ro'yxati: nuqta + nom + oddiy so'z."""
    units = (live.get("status") or {}).get("units") or {}
    rows = [u for u in (units.get("units") or []) if isinstance(u, dict)]
    body: list[str] = []
    if not units:
        body.append(f'<p class="line">Xizmatlar ro\'yxati: {missing_html()}</p>')
    elif not units.get("ok", False):
        body.append('<p class="line"><span class="svc-state fail"><span class="dot"'
                    ' aria-hidden="true">✗</span>ro\'yxatni o\'qib bo\'lmadi'
                    f'</span> <span class="muted">{esc(units.get("error"))}</span></p>')
    elif not rows:
        body.append('<p class="line"><span class="svc-state neutral"><span class="dot"'
                    ' aria-hidden="true">○</span>Hozir hech qanday REVIX '
                    "xizmati ishlamayapti.</span></p>"
                    '<p class="line muted">Tajriba o\'tkazilmayotganda bu NORMAL '
                    "holat: xizmatlar faqat tajriba paytida paydo bo'ladi.</p>")
    else:
        lis = []
        for u in rows[:6]:
            cls, icon, word = unit_plain(u)
            lis.append(f'<li><span class="svc-state {cls}"><span class="dot" '
                       f'aria-hidden="true">{icon}</span>{esc(word)}</span>'
                       f'<code class="svc-name">{esc(u.get("name"))}</code></li>')
        if len(rows) > 6:
            lis.append(f'<li class="more">yana {len(rows) - 6} ta</li>')
        body.append(f'<ul class="svc-list">{"".join(lis)}</ul>')
    body.append('<p class="line"><a href="/services">Barcha xizmatlar &rarr;</a></p>')
    return (f'<section class="rcard wide" data-card="services"><h2>Xizmatlar</h2>'
            f'{"".join(body)}</section>')


def home_about() -> str:
    ps = "".join(f"<p>{esc(p)}</p>" for p in REVIX_WHAT)
    return f'<section class="about" data-card="about"><h2>REVIX nima?</h2>{ps}</section>'


def home_todo() -> str:
    n_checks = len(getattr(cli, "CHECKS", ()) or ())
    checks = f"{n_checks} ta tekshiruv" if n_checks else "tekshiruvlar"
    links = [
        ("/services", "Xizmatlar ishlayaptimi?", "Xizmatlar"),
        ("/system-health", f"Tizim tajribaga tayyormi? ({checks})", "Tizim holati"),
        ("/help", "Atama tushunarsizmi?", "Yordam va lug'at"),
    ]
    lis = "".join(f'<li><span>{esc(q)}</span> <a href="{esc(h)}">{esc(t)} &rarr;</a></li>'
                  for h, q, t in links)
    return (f'<section class="todo" data-card="todo"><h2>Nima qilsam '
            f'bo\'ladi?</h2><ul class="todo-list">{lis}</ul></section>')


def home_side() -> str:
    """"REVIX nima?" + "Nima qilsam bo'ladi?" -- bitta keng kartada.

    NEGA birga: 1280x800 da birinchi ekran (holat + 4 karta + xizmatlar)
    aylantirmasdan ko'rinishi SHART; ikki tor karta matnni 8+ qatorga
    sindirib, pastki qatorni ekrandan chiqarib yuborardi (skrinshotda
    ko'rildi, jurnal 19 §6).
    """
    return f'<div class="rcard wide duo">{home_about()}{home_todo()}</div>'


def page_home(ctx: Context) -> str:
    """Bosh sahifa -- oddiy foydalanuvchi uchun birinchi ekran."""
    live, lsrc = ctx.gw.live()
    now = ctx.now_real_us
    return (
        '<div class="home">'
        + home_hero(live, lsrc, now)
        + home_cpu(live) + home_memory(live) + home_disk(live) + home_network(live)
        + home_services(live) + home_side()
        + "</div>"
    )


def page_dashboard(ctx: Context) -> str:
    """Spetsifikatsiyaning yuqori darajadagi shakli: SYSTEM HEALTH / SERVICES /
    RECOVERY ENGINE. Endi "Tadqiqotchi uchun" guruhida (`/overview`)."""
    live, lsrc = ctx.gw.live()
    run, rsrc = ctx.gw.run()
    now = ctx.now_real_us
    return (
        '<div class="grid grid-wide">'
        + panel_system_health(live, lsrc, now)
        + panel_services(live, lsrc, now)
        + panel_recovery_engine(run, rsrc, now)
        + "</div>"
    )


def page_services(ctx: Context) -> str:
    live, lsrc = ctx.gw.live()
    now = ctx.now_real_us
    return ('<div class="grid grid-wide">'
            + panel_services(live, lsrc, now)
            + panel_slices(live, lsrc, now) + "</div>")


def page_recovery_events(ctx: Context) -> str:
    run, rsrc = ctx.gw.run()
    now = ctx.now_real_us
    return ('<div class="grid grid-wide">'
            + panel_recovery_engine(run, rsrc, now)
            + panel_events(run, rsrc, now) + "</div>")


def page_system_health(ctx: Context) -> str:
    live, lsrc = ctx.gw.live()
    doctor, dsrc = ctx.gw.doctor()
    now = ctx.now_real_us
    return ('<div class="grid grid-wide">'
            + home_hero(live, lsrc, now, more_link=False, show_items=False)
            + panel_health_detail(live, lsrc, now)
            + panel_doctor(doctor, dsrc, now) + "</div>")


def page_resources(ctx: Context) -> str:
    live, lsrc = ctx.gw.live()
    now = ctx.now_real_us
    return ('<div class="grid grid-wide">'
            + panel_system_health(live, lsrc, now)
            + panel_psi(live, lsrc, now)
            + panel_slices(live, lsrc, now) + "</div>")


def page_failure_analysis(ctx: Context) -> str:
    derived, dsrc = ctx.gw.derived()
    analysis = (derived or {}).get("analysis")
    now = ctx.now_real_us
    body = ['<div class="grid grid-wide">']
    if not isinstance(analysis, dict):
        body.append(panel("Failure tahlili", dsrc, empty_notice(
            "Failure tahlili",
            "`revix.analyze` ning `analysis.json` fayli (§2.2) va "
            "`revix.figures` ning sidecar'lari (§3)",
            "avval driver run'i, keyin `revix analyze`, keyin `revix figures`",
        ), now))
    else:
        dispositions = (analysis.get("n_trials") or {}).get("by_disposition")
        body.append(panel("Disposition taqsimoti", dsrc, "".join([
            kv([("umumiy trial", value_html(
                (analysis.get("n_trials") or {}).get("total")))]),
            table(["disposition", "soni"],
                  [[text_html(k), value_html(v)]
                   for k, v in sorted((dispositions or {}).items())]
                  if isinstance(dispositions, dict) else [],
                  "disposition hisobi yo'q"),
            notice("honesty", "Disposition -- YOPIQ enum (§12)",
                   esc_paragraph(
                       "Har trial'ga AYNAN BITTA disposition: `complete`, "
                       "`censored`, `contaminated`, `aborted_guard`, "
                       "`washout_timeout`, `harness_error`. Bu jimgina "
                       "eksklyuziyaning oldini oladi.")),
        ]), now))
        body.append(panel("Eksklyuziya", dsrc,
                          exclusion_rate_html(analysis.get("exclusions")), now))
    body.append(panel_figures(derived, dsrc, now))
    body.append("</div>")
    return "".join(body)


def page_policies(ctx: Context) -> str:
    """Mavjud arm konfiguratsiyalari -- o'ylab chiqarilgan policy engine EMAS."""
    src = Source(kind="document",
                 name="README.md \"Baseline'lar\" + PREREGISTRATION.md §13",
                 note="hujjat fakti, o'lchov EMAS")
    rows = [[text_html(a["arm"]),
             text_html(a["config"]) if a["config"] else nosource_html(),
             text_html(a["role"]), text_html(a["status"])]
            for a in ARM_CONFIGS]
    body = [
        notice("honesty", "Policy engine YO'Q", esc_paragraph(ENGINE_HONESTY)),
        table(["arm", "systemd konfiguratsiyasi", "roli", "holati"], rows),
        notice("honesty", "Arm'lar shunchaki systemd konfiguratsiyalari",
               esc_paragraph(
                   "`README.md`: *H1 -- dunyo haqidagi da'vo, REVIX haqida "
                   "emas. Uni sinash uchun REVIX engine'i kerak emas: pilot "
                   "arm'lari shunchaki systemd konfiguratsiyalari.* Bu "
                   "jadval shu konfiguratsiyalarni ko'rsatadi, qaror "
                   "qabul qiladigan komponentni emas.")),
    ]
    return ('<div class="grid grid-wide">'
            + panel("Recovery siyosatlari (arm konfiguratsiyalari)", src,
                    "".join(body), ctx.now_real_us) + "</div>")


# Xavfsizlik sahifasida ko'rsatiladigan doctor tekshiruvlari -- NOMLANGAN
# qism-to'plam. NEGA ro'yxat qattiq kodlangan: "xavfsizlikka tegishli" degan
# avtomatik mezon yo'q, va mezonsiz tanlov keyin jimgina o'zgarardi.
SECURITY_CHECK_KEYS = (
    "oomd",
    "leftover_state",
    "cgroup_write",
    "memory_headroom",
    "swap_headroom",
    "kvm_access",
    "git_clean",
)


def page_security(ctx: Context) -> str:
    """Xavfsizlik -- pressure eksperimentining HAQIQIY xavfi (README ogohligi).

    Bu sahifa "cybersecurity toolkit" EMAS (`README.md`: REVIX "cybersecurity
    toolkit emas"). U bitta aniq savolga javob beradi: bu mashinada pressure
    eksperimenti desktop sessiyasini o'ldirishi mumkinmi.
    """
    doctor, dsrc = ctx.gw.doctor()
    live, lsrc = ctx.gw.live()
    now = ctx.now_real_us
    guard_src = Source(kind="document",
                       name="revix.guard DEFAULTS (02-guard-kalibratsiyasi.md)",
                       note="kalibratsiya bilan o'lchangan chegaralar")
    body = [
        notice("critical", "Bu repozitoriy nazorat qilinadigan memory pressure yaratadi",
               esc_paragraph(
                   "`README.md` xavfsizlik ogohligi: PSI IERARXIK -- test "
                   "slice'i ichidagi stall yuqoriga `user@1000.service` ga "
                   "tarqaladi. Ehtiyotsiz pressure eksperimenti brauzerni, "
                   "editorni yoki butun desktop sessiyani o'ldirishi mumkin. "
                   "Guard sinamasdan hech qanday pressure eksperimenti ishga "
                   "tushirilmaydi.")),
        panel("Guard chegaralari", guard_src, kv([
            ("host MemAvailable minimumi", kb_html(cli.GUARD_MEM_FLOOR_KB)),
            ("guard sustain max", value_html(cli.GUARD_SUSTAIN_MAX_S, unit="s")),
            ("guard sustain tezlik chegarasi", value_html(cli.GUARD_SUSTAIN_RATE)),
            ("pressure oynasi maksimumi", value_html(cli.PRESSURE_WINDOW_MAX_S, unit="s")),
            ("rejalashtirilgan lab shifti", kb_html(cli.PLANNED_CEILING_KB)),
        ]), now),
        panel_health_detail(live, lsrc, now),
        panel_doctor(doctor, dsrc, now, only_keys=SECURITY_CHECK_KEYS,
                     title="Xavfsizlikka tegishli tekshiruvlar (revix doctor)"),
        panel("Bu sahifa nima emas", Source(
            kind="document", name="README.md \"Loyiha nima EMAS\""), notice(
            "honesty", "Bu cybersecurity vositasi emas",
            esc_paragraph(
                "REVIX -- Linux distributivi emas, desktop theme emas, "
                "cybersecurity toolkit emas va Kali Linux moslashtirmasi "
                "emas. Bu sahifa zaiflik skanlamaydi va hech narsani "
                "himoya qilmaydi; u faqat o'lchov harness'ining O'Z "
                "xavfini ko'rsatadi.")), now),
    ]
    return '<div class="grid grid-wide">' + "".join(body) + "</div>"


def page_research_metrics(ctx: Context) -> str:
    derived, dsrc = ctx.gw.derived()
    analysis = (derived or {}).get("analysis")
    now = ctx.now_real_us
    body = ['<div class="grid grid-wide">', panel_primary(analysis, dsrc, now)]
    if not isinstance(analysis, dict):
        body.append(panel("FR-A / downtime / survival", dsrc, empty_notice(
            "FR-A, downtime kvantillari va survival natijalari",
            "`revix.analyze` ning `analysis.json` fayli (§2.2)",
            "`python3 -m revix.cli analyze --trials <...> --run-meta <...> "
            "--out datasets/<run>/analysis.json`",
        ), now))
        body.append("</div>")
        return "".join(body)

    fr = analysis.get("false_recovery") or {}
    fra = fr.get("fr_a") if isinstance(fr.get("fr_a"), dict) else {}
    frb = fr.get("fr_b") if isinstance(fr.get("fr_b"), dict) else {}
    fr_rows: list[tuple[str, str]] = [("FR-A asosi (basis)", text_html(fra.get("basis")))]
    if fra.get("basis"):
        fr_rows += [("FR-A per_action", value_html(fra.get("per_action"))),
                    ("FR-A per_episode", value_html(fra.get("per_episode"))),
                    ("aniqlanmagan (n_undetermined)", value_html(fra.get("n_undetermined")))]
    fr_rows += [("FR-B hisoblandi", value_html(frb.get("computed"))),
                ("FR-B sababi", text_html(frb.get("reason")))]
    fr_body = [kv(fr_rows)]
    if not fra.get("basis"):
        fr_body.append(notice(
            "critical", "FR-A raqami KO'RSATILMADI -- asosi yo'q",
            esc_paragraph(
                "Shartnoma §3.1: `false_recovery.fr_a.basis` bo'lmasa FR-A "
                "raqami ko'rsatilMAYDI -- asossiz nisbat talqin qilinmaydi "
                "(§2.9a). Qaysi denominator ishlatilgani ma'lum bo'lmaganda "
                "son o'zi hech narsa aytmaydi.")))
    body.append(panel("False recovery (FR-A, FR-B)", dsrc, "".join(fr_body), now))

    dt = analysis.get("downtime")
    dt_rows: list[list[str]] = []
    if isinstance(dt, dict):
        for measure in ("d_sd", "d_probe", "d_eff"):
            blk = dt.get(measure)
            if not isinstance(blk, dict):
                dt_rows.append([text_html(measure), missing_html(), missing_html(),
                                missing_html(), missing_html(), missing_html()])
                continue

            def q(key: str, _blk: dict[str, Any] = blk) -> str:
                v = _blk.get(key)
                if isinstance(v, dict):
                    # §2.2 normal shakl: {estimate, ci_lower, ci_upper, ...}
                    if not v:
                        return missing_html()
                    return (value_html(v.get("estimate", v.get("value")))
                            + " [" + value_html(v.get("ci_lower")) + ", "
                            + value_html(v.get("ci_upper")) + "]")
                return value_html(v)

            dt_rows.append([
                text_html(measure), q("median"), q("p90"), q("p99"),
                text_html(blk.get("unit") or analysis.get("time_unit")),
                text_html(blk.get("recovered_within_horizon")),
            ])
    dt_body = [table(["o'lchov", "median [CI]", "p90 [CI]", "p99 [CI]",
                      "birlik", "recovered/horizon"], dt_rows,
                     "downtime bloki yo'q")]
    if isinstance(dt, dict) and not analysis.get("time_unit"):
        dt_body.append(notice(
            "critical", "Vaqt birligi E'LON QILINMAGAN",
            esc_paragraph(
                "`time_unit` yo'q. Shartnoma §3.1: birlik TAXMIN "
                "QILINMAYDI, shuning uchun bu raqamlar birliksiz "
                "ko'rsatiladi va sekundga aylantirilMAYDI.")))
    body.append(panel("Downtime (§6.1 uchala o'lchov)", dsrc, "".join(dt_body), now))
    body.append(panel("Eksklyuziya", dsrc,
                      exclusion_rate_html(analysis.get("exclusions")), now))

    warnings = analysis.get("warnings")
    w_body = ["<h3>Analiz ogohliklari</h3>"]
    if not isinstance(warnings, list):
        w_body.append(f"<p>{missing_html()}</p>")
    elif not warnings:
        w_body.append(f"<p>{value_html(0)} -- ro'yxat o'qildi va bo'sh edi</p>")
    else:
        w_body.append("<ul>" + "".join(
            f'<li><pre class="raw">{esc(json.dumps(w, ensure_ascii=False))}</pre></li>'
            for w in warnings) + "</ul>")
    w_body.append(notice(
        "honesty", "Ogohliklar YASHIRILMAYDI",
        esc_paragraph(
            "`figures.py` qoida 6 va shartnoma §2.3: hisoblab bo'lmagan "
            "narsa `warnings` ga yoziladi va jim tushirib qoldirilmaydi. "
            "GUI ularni xom holda ko'rsatadi.")))
    body.append(panel("Ogohliklar va provenans", dsrc, "".join(w_body) + kv([
        ("schema_version", value_html(analysis.get("schema_version"))),
        ("analysis_version", text_html(analysis.get("analysis_version"))),
        ("preregistration_sha256", text_html(analysis.get("preregistration_sha256"))),
        ("preregistration_version", text_html(analysis.get("preregistration_version"))),
        ("run_id", text_html(analysis.get("run_id"))),
        ("time_unit", text_html(analysis.get("time_unit"))),
        ("t_trial_us", value_html(analysis.get("t_trial_us"), unit="us")),
        ("t_trial_formula", text_html(analysis.get("t_trial_formula"))),
    ]), now))
    body.append("</div>")
    return "".join(body)


def page_logs(ctx: Context) -> str:
    run, rsrc = ctx.gw.run()
    now = ctx.now_real_us
    return ('<div class="grid grid-wide">'
            + panel_logs(run, rsrc, now)
            + panel_run_meta(run, rsrc, now) + "</div>")


def page_settings(ctx: Context) -> str:
    """Joriy konfiguratsiyaning KO'RINISHI -- tahrirlagich EMAS (qoida 9)."""
    o = ctx.opts
    src = Source(kind="config", name="revix.gui argv (joriy jarayon)",
                 read_real_us=ctx.now_real_us)
    runs = ctx.gw.run_dirs()
    body = [
        notice("honesty", "Bu sahifa hech narsani o'zgartirmaydi",
               esc_paragraph(
                   "Bu server FAQAT O'QIYDI (qoida 9): POST qabul qilmaydi, "
                   "faylga yozmaydi, unit'ga tegmaydi va eksperiment ishga "
                   "tushirmaydi. Sozlamani o'zgartirish -- serverni boshqa "
                   "flag bilan qayta ishga tushirish. Saqlanadigan sozlama "
                   "fayli ham YO'Q: birorta modul uni o'qimaydi, shuning "
                   "uchun GUI uni ixtiro qilmaydi.")),
        kv([
            ("bind manzili", text_html(f"{o.host}:{o.port}")),
            ("URL", text_html(f"http://{o.host}:{o.port}/")),
            ("loopback", value_html(is_loopback(o.host))),
            ("--allow-remote", value_html(o.allow_remote)),
            ("PSI oynasi", value_html(o.interval_s, unit="s")),
            ("tirik kesh TTL", value_html(o.cache_s, unit="s")),
            ("doctor kesh TTL", value_html(o.doctor_cache_s, unit="s")),
            ("eskirish chegarasi", value_html(STALE_AFTER_S, unit="s")),
            ("datasets katalogi", text_html(o.datasets_dir)),
            ("--run-dir", text_html(o.run_dir) if o.run_dir else missing_html()),
            ("topilgan run'lar", value_html(len(runs))),
            ("--mark-synthetic", value_html(o.mark_synthetic)),
            ("aktivlar katalogi", text_html(ASSET_DIR)),
            ("gui versiyasi", value_html(GUI_VERSION)),
            ("report_schema_version", value_html(cli.REPORT_SCHEMA_VERSION)),
        ]),
        notice("critical", "Localhost'dan tashqariga ochilmaydi",
               esc_paragraph(
                   "Bu server tirik tizim holatini o'qiydi: cgroup'lar, PSI, "
                   "unit'lar, muhit fingerprint'i va journal satrlari. "
                   "Default bind `127.0.0.1`; loopback bo'lmagan manzil "
                   "`--allow-remote` ni ATAYLAB talab qiladi, aks holda "
                   "server ishga tushmaydi.")),
    ]
    return ('<div class="grid grid-wide">'
            + panel("Sozlamalar (faqat ko'rish)", src, "".join(body),
                    ctx.now_real_us) + "</div>")


def page_about(ctx: Context) -> str:
    version, vsrc = ctx.gw.version()
    now = ctx.now_real_us
    v = version or {}
    body = [
        panel("Versiya va provenans", vsrc, kv([
            ("REVIX versiyasi", text_html(v.get("version"))),
            ("record schema", value_html(v.get("record_schema_version"))),
            ("report schema", value_html(v.get("report_schema_version"))),
            ("git commit", text_html(v.get("git_commit"))),
            ("git dirty", value_html(v.get("git_dirty"))),
            ("git xatosi", text_html(v.get("git_error")) if v.get("git_error")
             else value_html(None)),
            ("python", text_html(v.get("python"))),
            ("repo ildizi", text_html(v.get("repo_root"))),
        ]), now),
        panel("REVIX nima", Source("document", "README.md \"Loyiha nima\""),
              notice("honesty", "O'lchov artifact'i",
                     esc_paragraph(
                         "REVIX -- Linux'da xizmat recovery'ining tizim "
                         "pressure'iga qanday bog'liqligini o'lchaydigan "
                         "tadqiqot artifact'i: operatsion ta'riflar, `FR-A` "
                         "oracle-free false-recovery metrikasi, reproducible "
                         "recovery benchmark va falsifikatsiya qilinadigan "
                         "gipoteza.")), now),
        panel("REVIX nima emas", Source("document", "README.md \"Loyiha nima EMAS\""),
              "".join([
                  notice("honesty", "Adaptiv recovery IXTIRO QILINMAYDI",
                         esc_paragraph(
                             "Exponential backoff -- systemd v254+ "
                             "(`RestartSteps=`); adaptiv multi-action "
                             "selection -- Narya (OSDI '20); post-restart "
                             "health verification -- Kubernetes probe'lari, "
                             "Pacemaker, greenboot. REVIX bularning birini "
                             "ham da'vo qilmaydi.")),
                  notice("honesty", "Va bu shuningdek",
                         esc_paragraph(
                             "Linux distributivi EMAS, desktop theme EMAS, "
                             "cybersecurity toolkit EMAS va Kali Linux "
                             "moslashtirmasi EMAS.")),
              ]), now),
        panel("Hozirgi holat", Source("document", "README.md \"Holat\" + CONTRIBUTING.md"),
              notice("critical", "Hech qanday natija hali yo'q",
                     esc_paragraph(
                         "Hech qanday eksperiment hali ishga tushirilmadi va "
                         "hech qanday natija hali yo'q. Shu sababli bu "
                         "dashboard'ning natija sahifalari bo'sh -- bu "
                         "nuqson emas, joriy holat, va u natija paydo "
                         "bo'lmaguncha shunday qoladi.")), now),
        panel("Bu dashboard qanday ishlaydi", Source("document", "revix/gui.py docstring"),
              "".join([
                  notice("honesty", "Ekranda manbadan o'qilmagan son bo'lmaydi",
                         esc_paragraph(
                             "Placeholder yo'q, namuna ma'lumot yo'q, "
                             "interpolyatsiya yo'q. To'rt holat to'rt xil "
                             "ko'rinadi: `None` = \"o'lchanmadi\", `0` = "
                             "\"o'lchangan nol\" belgisi bilan, artifact "
                             "yo'q = \"hali ishga tushirilmadi\", birorta "
                             "modul chiqarmaydi = \"manba yo'q\".")),
                  notice("honesty", "GUI hech narsa hisoblamaydi",
                         esc_paragraph(
                             "CI, p-qiymat, kvantil, tezlik va ulush "
                             "`cli.py`, `analysis.json` yoki figura "
                             "sidecar'idan TAYYOR keladi. GUI faqat "
                             "o'qiydi, formatlaydi va escape qiladi.")),
              ]), now),
    ]
    return '<div class="grid grid-wide">' + "".join(body) + "</div>"


# Lug'at: atama -> bir jumlali oddiy ta'rif (Yordam sahifasi). Ta'riflar
# loyiha hujjatlaridagi ma'noga mos (PREREGISTRATION.md, README.md).
GLOSSARY: tuple[tuple[str, str], ...] = (
    ("Xizmat (service, unit)",
     "Fonda ishlaydigan dastur; uni systemd ishga tushiradi, kuzatadi va "
     "kerak bo'lsa qayta ishga tushiradi."),
    ("systemd",
     "Linux'da xizmatlarni boshqaradigan tizim dasturi; REVIX uning qayta "
     "tiklash xatti-harakatini o'lchaydi."),
    ("Recovery (tiklanish)",
     "Ishdan chiqqan xizmatning qayta ishga tushib, yana to'g'ri javob "
     "bera boshlashi."),
    ("Failure (nosozlik)",
     "Xizmatning ishdan chiqishi; tajribada u ataylab, nazorat ostida "
     "qo'zg'atiladi."),
    ("Pressure (bosim)",
     "Resurs (xotira, protsessor, disk) tanqisligi: dasturlar uni kutib "
     "qolishga majbur bo'ladi."),
    ("PSI / stall (kutish)",
     "Linux'ning bosim o'lchagichi: dasturlar resursni kutib to'xtab turgan "
     "vaqt ulushi (0 = hech kim kutmadi, 1 = butun vaqt)."),
    ("some / full",
     "PSI ning ikki turi: \"some\" -- kamida bitta dastur kutdi, \"full\" -- "
     "hamma dasturlar bir vaqtda kutdi."),
    ("cgroup",
     "Jarayonlar guruhi; Linux unga xotira yoki protsessor chegarasi qo'yadi "
     "va uning sarfini alohida hisoblaydi."),
    ("Slice",
     "systemd'dagi cgroup turi; REVIX tajriba dasturlarini alohida slice "
     "ichida ishlatadi (revixlab.slice, revixmon.slice)."),
    ("SUT",
     "System Under Test -- tajribada ataylab ishdan chiqariladigan va "
     "tiklanishi o'lchanadigan sinov xizmati."),
    ("Guard (qo'riqchi)",
     "REVIX ning alohida xavfsizlik jarayoni: bosim haddan oshsa tajribani "
     "to'xtatadi, kompyuterni qotib qolishdan saqlaydi."),
    ("systemd-oomd",
     "Tizimning xotira qo'riqchisi: xotira bosimi uzoq davom etsa dasturlarni "
     "o'zi o'chirib yuborishi mumkin."),
    ("Disposition",
     "Har bir sinov (trial) qanday tugaganining yagona yorlig'i, masalan "
     "complete, censored, contaminated."),
    ("Censored (kesilgan)",
     "Kuzatuv muddati tugaguncha xizmat tiklanmagan sinov; tiklanish vaqti "
     "noma'lum, faqat \"muddatdan uzun\" ekani ma'lum."),
    ("Horizon (kuzatuv muddati)",
     "Bir sinovda tiklanish kutiladigan eng uzoq vaqt."),
    ("Median, p90, p99",
     "Taqsimot nuqtalari: p99 -- sinovlarning 99 foizi shu qiymatdan tez "
     "bo'lgan vaqt (eng yomon holatlarga yaqin)."),
    ("CI (ishonch oralig'i)",
     "Haqiqiy qiymat qaysi oraliqda bo'lishi ehtimoli yuqori ekanini "
     "ko'rsatadigan diapazon."),
    ("Arm (A, B, no_action, C)",
     "Taqqoslanadigan tiklash sozlamalari; A va B -- oddiy systemd "
     "sozlamalari, C esa hali muzlatilmagan va mavjud emas."),
    ("FR-A (false recovery)",
     "\"Soxta tiklanish\": xizmat qayta ishga tushgan ko'rinadi, lekin "
     "aslida to'g'ri ishlamaydi -- shuning ulushi."),
    ("MemAvailable / MemTotal",
     "Linux /proc/meminfo maydonlari: dasturlar ishlata oladigan bo'sh xotira "
     "/ jami xotira."),
    ("Swap",
     "Diskdagi zaxira xotira; RAM to'lganda ishlatiladi, lekin juda sekin."),
    ("GiB / MiB",
     "Xotira birligi: 1 GiB = 1024 MiB, taxminan 1.07 GB."),
    ("Synthetic (sintetik)",
     "Qo'lda yasalgan namunaviy ma'lumot; haqiqiy o'lchov EMAS va natija "
     "sifatida ishlatilmaydi."),
)


def page_help(ctx: Context) -> str:
    """Yordam / Qo'llanma: ekranni o'qish, lug'at, live image eslatmalari."""
    src = Source(kind="document", name="revix/gui.py (Yordam matni)",
                 note="hujjat; o'lchov emas")
    now = ctx.now_real_us
    legend = table(["ko'rinish", "ma'nosi"], [
        [status_badge("ok") + " " + status_badge("pass"),
         esc("Yaxshi: tekshiruv o'tdi yoki xizmat ishlayapti.")],
        [status_badge("warn"),
         esc("Diqqat: ishlayapti, lekin e'tibor bering (sabab yonida yozilgan).")],
        [status_badge("fail"),
         esc("Xato: muammo bor, tajriba o'tkazib bo'lmaydi yoki xizmat to'xtagan.")],
        [missing_html(REASON_NOT_REPORTED),
         esc("O'lchanmadi: qiymat yo'q. Sichqonchani ustiga olib boring -- "
             "sabab bir jumlada chiqadi. Bu HECH QACHON nol degani emas.")],
        [nosource_html(),
         esc("REVIX bu narsani umuman o'lchamaydi (masalan, disk hajmi, tarmoq).")],
        [value_html(0),
         esc("Haqiqiy nol: o'lchandi va natija aynan 0.")],
        [norun_html(),
         esc("Hali ishga tushirilmadi: bu ma'lumot tajriba o'tkazilgandan "
             "keyin paydo bo'ladi.")],
        ['<span class="interp" data-level="mid">o\'rta <small>(taxminiy talqin)'
         "</small></span>",
         esc("Ekran sonni so'z bilan izohlagan. Bu O'LCHOV emas, faqat yo'l-yo'riq; "
             "chegaralar pastda.")],
    ])
    how = "".join(f"<li>{esc_paragraph(x)}</li>" for x in (
        "Avval Bosh sahifadagi katta jumlaga qarang: u butun tizim holatini "
        "bir so'z bilan aytadi (belgi + rang + so'z).",
        "Har kartada katta son -- asosiy javob, pastdagi kichik matn -- "
        "uning ma'nosi va manbasi.",
        "Ma'lumot avtomatik YANGILANMAYDI: yangilash uchun yuqoridagi "
        "\"Yangilash\" tugmasini yoki F5 ni bosing. Har panelda o'qilgan vaqt "
        f"turadi; {STALE_AFTER_S:g} soniyadan eski bo'lsa u qizil va tagiga "
        "chizilgan bo'ladi.",
        "Yorliq yonidagi kichik kulrang matn (masalan `MemTotal`) -- manbadagi "
        "aniq maydon nomi, mutaxassislar uchun.",
        "\"Tadqiqotchi uchun\" menyusidagi sahifalar -- tajriba natijalari va "
        "texnik tafsilotlar. Tajriba o'tkazilmagan bo'lsa ular bo'sh -- bu "
        "nuqson emas.",
    ))
    interp = table(["kutish ulushi (PSI some)", "ekrandagi so'z"], [
        [esc(f"< {STALL_LEVEL_MID:g}"), esc(STALL_WORDS["low"][0])],
        [esc(f"{STALL_LEVEL_MID:g} ... < {STALL_LEVEL_HIGH:g}"), esc(STALL_WORDS["mid"][0])],
        [esc(f">= {STALL_LEVEL_HIGH:g}"), esc(STALL_WORDS["high"][0])],
    ])
    gl = "".join(f"<dt>{esc(t)}</dt><dd>{esc(d)}</dd>" for t, d in GLOSSARY)
    reasons = table(["sabab kodi", "oddiy tilda"],
                    [[f"<code>{esc(k)}</code>", esc(REASON_PLAIN[k])]
                     for k in sorted(MISSING_REASONS)])
    live_notes = "".join(f"<li>{esc_paragraph(x)}</li>" for x in (
        "Foydalanuvchi: `revix`. Parol YO'Q -- tizim avtomatik kiradi.",
        "`sudo` parol so'ramaydi (NOPASSWD). Shuning uchun bu image ishonchsiz "
        "tarmoqqa ulanmasligi kerak.",
        "Matnli konsol: Ctrl+Alt+F2 (login: `revix`, parolsiz). Ekranga qaytish: "
        "Ctrl+Alt+F1.",
        "Bu grafik ekran FAQAT KO'RISH uchun: u hech narsani o'zgartirmaydi va "
        "tajriba boshlamaydi. Buyruqlar terminalda beriladi "
        "(`python3 -m revix.cli doctor`).",
        "Virtual mashina (VirtualBox) ichidagi vaqt o'lchovlari tadqiqot "
        "natijasi sifatida YAROQSIZ: virtualizatsiya qo'shimcha kechikish "
        "beradi. VM -- faqat tekshirish va tanishish uchun.",
        "Grafik rejim ~0.4 GiB xotira oladi; 4 GiB li VM da \"Bo'sh xotira "
        "yetmaydi\" xatosi kutilgan holat. Grafik rejim uchun 6 GiB tavsiya "
        "etiladi.",
    ))
    body = [
        panel("Bu ekranni qanday o'qish kerak", src,
              f'<ol class="steps">{how}</ol>' + legend, now),
        panel("Atamalar lug'ati", src, f'<dl class="glossary">{gl}</dl>', now),
        panel("Live image va virtual mashina", src,
              f'<ul class="steps">{live_notes}</ul>', now),
        panel("Taxminiy talqin chegaralari", src, "".join([
            f'<p class="lead">{esc_paragraph(PSI_PLAIN)}</p>',
            interp,
            notice("honesty", "Bu chegaralar o'lchov emas",
                   esc_paragraph(
                       "Chegaralar faqat ekrandagi so'z uchun tanlangan "
                       "(jurnal `docs/architecture/19-gui-soddalashtirish.md`). "
                       "Ular `PREREGISTRATION.md` da yo'q va hech qaysi qaror, "
                       "guard yoki analiz ularni ishlatmaydi. Shubhali holatda "
                       "so'z yuqoriroq darajani beradi."), collapsed=False),
        ]), now),
        panel("\"O'lchanmadi\" sabablari (mutaxassislar uchun)", src, reasons, now),
    ]
    return '<div class="grid grid-wide">' + "".join(body) + "</div>"


@dataclass
class PageDef:
    """Bitta sahifa: slug, sarlavha, renderer va KERAKLI manbalar.

    `needs` navigatsiyada ishlatiladi: manbasi bugun yo'q sahifa nav'da
    belgilanadi (`empty-page`), shunda foydalanuvchi bosishdan OLDIN
    biladi. NEGA: bo'sh sahifani kutilmaganda ko'rish "buzilgan" degan
    taassurot beradi (qoida 6).
    """

    slug: str
    title: str
    render: Callable[[Context], str]
    needs: tuple[str, ...]
    intro: str
    # "main" -- oddiy foydalanuvchi menyusi; "research" -- "Tadqiqotchi
    # uchun" guruhi (jurnal 19 §2). Guruh faqat MENYU joyini va o'lchanmagan
    # qiymat tafsilotining ko'rinishini belgilaydi; ma'lumotga ta'sir yo'q.
    group: str = "main"
    audience: str = ""
    tech: str = ""


GROUP_MAIN = "main"
GROUP_RESEARCH = "research"
RESEARCH_GROUP_TITLE = "Tadqiqotchi uchun"

PAGES: tuple[PageDef, ...] = (
    # --- oddiy foydalanuvchi uchun --------------------------------------
    PageDef("", "Bosh sahifa", page_home, ("live",),
            "Tizim holati bir qarashda: umumiy xulosa, protsessor, xotira, "
            "disk, tarmoq va REVIX xizmatlari.",
            audience="Hamma uchun.",
            tech="`cli.health_report()` + `cli.status_report()` -- tirik manba."),
    PageDef("services", "Xizmatlar", page_services, ("live",),
            "REVIX xizmatlari ishlayaptimi yoki to'xtaganmi, va tajriba "
            "uchun ajratilgan xotira guruhlari (slice) holati.",
            audience="Hamma uchun.",
            tech="`systemctl --user list-units revix*` va lab/mon "
                 "slice'larining cgroup holati."),
    PageDef("system-health", "Tizim holati", page_system_health, ("live",),
            "Kompyuter tajriba o'tkazishga tayyormi? Yuqorida muammo va "
            "ogohliklar oddiy tilda, pastda har bir avtomatik tekshiruv: "
            "hozirgi qiymat, talab va buzilsa nima bo'lishi.",
            audience="Hamma uchun; jadval tafsilotlari -- mutaxassis uchun.",
            tech="`revix health` tafsiloti va 18 `revix doctor` tekshiruvi. "
                 "Doctor bitta vaqtinchalik cgroup yaratib o'chiradi "
                 "(`cli.py` qoida 4)."),
    PageDef("resources", "Resurslar", page_resources, ("live",),
            "Protsessor, xotira va disk qanchalik band, dasturlar ularni "
            "qancha kutib qolyapti (bosim, PSI).",
            audience="Hamma uchun; PSI jadvali -- mutaxassis uchun.",
            tech="PSI stall tezliklari (`total=` delta'sidan, §7), xotira "
                 "zaxirasi va slice snapshot'lari."),
    PageDef("help", "Yordam", page_help, ("document",),
            "Bu ekranni qanday o'qish, belgilar ma'nosi, atamalar lug'ati va "
            "live image (virtual mashina) bo'yicha eslatmalar.",
            audience="Hamma uchun, ayniqsa birinchi marta ko'rayotganlar."),
    # --- tadqiqotchi uchun ----------------------------------------------
    PageDef("overview", "Texnik umumiy ko'rinish", page_dashboard, ("live",),
            "Eski \"Boshqaruv paneli\": tizim holati, xizmatlar va systemd "
            "recovery harakati bitta zich sahifada.",
            group=GROUP_RESEARCH, audience="Tadqiqotchi uchun.",
            tech="Tizim sog'lig'i, `revix*` xizmatlari va systemd'ning recovery "
                 "harakati -- hammasi tirik manbadan."),
    PageDef("recovery-events", "Recovery hodisalari", page_recovery_events,
            ("run",),
            "Tajriba paytida yozilgan hodisalar ketma-ketligi: xizmat qachon "
            "ishdan chiqdi, systemd nima qildi, sinov qanday tugadi.",
            group=GROUP_RESEARCH, audience="Tadqiqotchi uchun.",
            tech="Run katalogining `events.jsonl` oqimi (shartnoma §1.2)."),
    PageDef("failure-analysis", "Failure tahlili", page_failure_analysis,
            ("derived",),
            "Sinovlar qanday tugagani (disposition), qaysilari tahlildan "
            "chiqarilgani va natija grafiklari.",
            group=GROUP_RESEARCH, audience="Tadqiqotchi uchun.",
            tech="Disposition taqsimoti, eksklyuziya darajalari va figuralar -- "
                 "`analysis.json` va sidecar'lardan."),
    PageDef("policies", "Recovery siyosatlari", page_policies, ("document",),
            "Taqqoslanadigan tiklash sozlamalari (arm'lar). Bu oddiy systemd "
            "sozlamalari; REVIX o'zi qaror qabul qilmaydi.",
            group=GROUP_RESEARCH, audience="Tadqiqotchi uchun.",
            tech="Mavjud arm konfiguratsiyalari. Policy engine YO'Q."),
    PageDef("security", "Xavfsizlik", page_security, ("live",),
            "Bosim tajribasi kompyuterni qotirib qo'yishi mumkinmi va REVIX "
            "guard qanday chegaralar bilan himoya qiladi.",
            group=GROUP_RESEARCH, audience="Tajriba o'tkazuvchi uchun.",
            tech="Pressure eksperimentining haqiqiy xavfi va guard chegaralari. "
                 "Bu cybersecurity vositasi emas."),
    PageDef("research-metrics", "Tadqiqot metrikalari", page_research_metrics,
            ("derived",),
            "Tajribaning asosiy natijalari: tiklanish ehtimoli, tiklanish "
            "vaqti (median, p90, p99) va soxta tiklanish ulushi.",
            group=GROUP_RESEARCH, audience="Tadqiqotchi uchun.",
            tech="Birlamchi endpoint, FR-A, downtime va eksklyuziya -- "
                 "`analysis.json` dan o'qib, hisoblamasdan."),
    PageDef("logs", "Log'lar", page_logs, ("run",),
            "Guard jarayonining xom yozuvlari va tajriba metadata'si "
            "(qaysi kod, qaysi kompyuterda).",
            group=GROUP_RESEARCH, audience="Tadqiqotchi uchun.",
            tech="Guard oqimining xom satrlari va run metadata'si."),
    PageDef("settings", "Sozlamalar", page_settings, ("config",),
            "Bu ekran qanday sozlama bilan ishlayapti. Faqat ko'rish -- bu "
            "yerda hech narsa o'zgartirilmaydi.",
            group=GROUP_RESEARCH, audience="Administrator uchun.",
            tech="Joriy konfiguratsiyaning ko'rinishi. Faqat o'qish."),
    PageDef("about", "Loyiha haqida", page_about, ("document",),
            "REVIX versiyasi, u nima va nima EMAS.",
            group=GROUP_RESEARCH, audience="Hamma uchun.",
            tech="Versiya, provenans va REVIX nima EMAS."),
)

PAGE_BY_SLUG: dict[str, PageDef] = {p.slug: p for p in PAGES}


def available_needs(gw: Gateway) -> set[str]:
    """Bugun MAVJUD manbalar to'plami -- nav belgilashi uchun.

    `live` tekshiruvi ATAYLAB `gw.live()` ni chaqirmaydi: u >= 2 s uxlaydi va
    navigatsiyani chizish uchun o'lchov qilish mantiqsiz bo'lardi. Linux
    PSI mavjudligi arzon va aniq signal.
    """
    out: set[str] = {"document", "config"}
    if os.path.isdir("/proc/pressure"):
        out.add("live")
    runs = gw.run_dirs()
    if runs:
        out.add("run")
        if os.path.isfile(os.path.join(runs[-1], "analysis.json")):
            out.add("derived")
    return out


# ===========================================================================
# layout
# ===========================================================================


def _nav_link(p: PageDef, current: str, have: set[str]) -> str:
    href = "/" if p.slug == "" else f"/{p.slug}"
    available = bool(set(p.needs) & have)
    # `class="empty-page"` AYNAN shu shaklda (test va CSS unga tayanadi).
    cls = "" if available else ' class="empty-page"'
    cur = ' aria-current="page"' if p.slug == current else ""
    title = "" if available else f' title="{esc(TEXT_NOT_YET_RUN)}"'
    note = ("" if available else
            '<span class="nav-note">hali bo\'sh: tajriba natijasi yo\'q</span>')
    return f'<a href="{esc(href)}"{cls}{cur}{title}>{esc(p.title)}{note}</a>'


def nav_html(current: str, have: set[str]) -> str:
    """Guruhlangan menyu: oddiy sahifalar + yig'iladigan "Tadqiqotchi uchun".

    Tadqiqotchi guruhi default YOPIQ; joriy sahifa shu guruhda bo'lsa --
    ochiq. Holat `app.js` da eslab qolinadi (`data-key`). Hech bir sahifa
    o'chirilmagan -- hammasi menyuda (jurnal 19 §2).
    """
    main = [_nav_link(p, current, have) for p in PAGES if p.group == GROUP_MAIN]
    research = [_nav_link(p, current, have) for p in PAGES
                if p.group == GROUP_RESEARCH]
    in_research = any(p.slug == current for p in PAGES if p.group == GROUP_RESEARCH)
    opened = " open" if in_research else ""
    forced = ' data-force-open="1"' if in_research else ""
    return (f'<nav class="nav" aria-label="Menyu">'
            f'<div class="nav-main">{"".join(main)}</div>'
            f'<details class="nav-group" data-key="nav-research" data-scope="global"'
            f"{forced}{opened}>"
            f"<summary>{esc(RESEARCH_GROUP_TITLE)}</summary>"
            f'<div class="nav-sub">{"".join(research)}</div></details></nav>')


def intro_html(page: PageDef) -> str:
    """"Bu sahifa nima ko'rsatadi" / "Kim uchun" -- har sahifa boshida."""
    if page.slug == "":
        return ""          # bosh sahifa o'zini o'zi tushuntiradi (hero)
    parts = [f"<p><strong>Bu sahifa nima ko'rsatadi:</strong> "
             f"{esc_paragraph(page.intro)}</p>"]
    if page.audience:
        parts.append(f"<p><strong>Kim uchun:</strong> {esc(page.audience)}</p>")
    if page.tech:
        parts.append(f'<details class="tech" data-key="tech-intro"><summary>'
                     f"Texnik tafsilot</summary><p>{esc_paragraph(page.tech)}</p>"
                     f"</details>")
    return f'<div class="page-intro">{"".join(parts)}</div>\n'


def layout(page: PageDef, body: str, ctx: Context, have: set[str],
           synthetic: bool) -> str:
    """To'liq HTML sahifa. CSP `self` -- CDN mumkin EMAS, offline ishlaydi.

    TUZILISH (jurnal 19 §5): chapda menyu (tor ekranda -- tepada), o'ngda
    sarlavha qatori (sahifa nomi, "Yangilash", soat) va sahifa tanasi.
    `body` klassi sahifa guruhini beradi (`grp-main` / `grp-research`):
    tadqiqotchi sahifalarida o'lchanmagan qiymat tafsiloti
    (`o'lchanmadi n/m reason=...`) matn bo'lib ko'rinadi.
    """
    banner = ""
    if synthetic:
        banner = (f'<div class="synthetic-banner"><strong>'
                  f'{esc(SYNTHETIC_INLINE_TEXT)}</strong> &mdash; '
                  f'{esc(SYNTHETIC_BANNER_TEXT)}</div>')
    grp = "grp-research" if page.group == GROUP_RESEARCH else "grp-main"
    # Server "hozir"i -- sahifa CHIQARILGAN payt, so'rov boshlangan payt
    # emas. NEGA: tirik o'qish (PSI) so'rov ichida >= 2 s uxlaydi, demak
    # o'qish vaqti so'rov boshidan KEYIN; eski qiymat bilan yosh manfiy
    # chiqib, `app.js` uni "?" deb ko'rsatardi (skrinshotda ko'rildi).
    emitted_us = max(int(ctx.now_real_us), int(cli.real_us()))
    return (
        "<!doctype html>\n"
        f'<html lang="uz" data-server-now-real-us="{emitted_us}">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        '<meta http-equiv="Content-Security-Policy" '
        "content=\"default-src 'self'; img-src 'self' data:; "
        "style-src 'self'; script-src 'self'\">\n"
        f"<title>REVIX &mdash; {esc(page.title)}</title>\n"
        '<link rel="stylesheet" href="/assets/style.css">\n'
        f'</head>\n<body class="{grp}">\n'
        '<div class="shell">\n'
        '<aside class="side">'
        '<a class="brand" href="/">REVIX</a>'
        '<span class="brand-sub">xizmatlar tiklanishini o\'lchash stendi</span>'
        + nav_html(page.slug, have)
        + '<p class="side-foot">Faqat ko\'rish rejimi: bu ekran tizimda hech '
        "narsani o'zgartirmaydi.</p>"
        "</aside>\n"
        '<div class="content">\n'
        '<header class="topbar">'
        f"<h1>{esc(page.title)}</h1>"
        '<span class="spacer"></span>'
        '<a class="refresh" href="" title="Sahifani qayta o\'qish (F5)">'
        "&#x21bb; Yangilash</a>"
        '<span class="clock" id="local-clock"></span>'
        "</header>\n"
        "<main>\n"
        + banner
        + intro_html(page)
        + body
        + "\n</main>\n"
        '<footer class="foot">'
        "Ekrandagi har bir son manbadan o'qilgan. O'lchanmagan qiymat "
        f"“{DASH}” bilan ko'rsatiladi va hech qachon 0 deb "
        "yozilmaydi; sababini ko'rish uchun sichqonchani ustiga olib boring. "
        "Atamalar: Yordam sahifasi."
        "</footer>\n"
        "</div>\n</div>\n"
        '<script src="/assets/app.js"></script>\n'
        "</body>\n</html>\n"
    )


def render_page(slug: str, ctx: Context) -> str:
    """Bitta sahifani to'liq HTML sifatida renderlaydi."""
    page = PAGE_BY_SLUG[slug]
    have = available_needs(ctx.gw)
    body = page.render(ctx)
    # Sahifa sintetikmi -- manbalardan QO'SHILIB aniqlanadi (qoida 7).
    synthetic = ctx.opts.mark_synthetic
    if "run" in page.needs or "derived" in page.needs:
        _, rsrc = ctx.gw.run()
        synthetic = synthetic or rsrc.synthetic
    return layout(page, body, ctx, have, synthetic)


def render_not_found(path: str, ctx: Context) -> str:
    """404 -- bu ham halol sahifa: nima yo'qligini va nima borligini aytadi."""
    page = PageDef("404", "Sahifa topilmadi", lambda _c: "", ("config",),
                   "So'ralgan yo'l bu serverda yo'q.")
    body = panel("Topilmadi", Source("config", "revix.gui router"), "".join([
        kv([("so'ralgan yo'l", text_html(path))]),
        notice("empty", "Bu yo'l mavjud emas",
               esc_paragraph(
                   f"Bu REVIX dashboard'i {len(PAGES)} ta sahifa beradi. "
                   "Ro'yxat chapdagi menyuda; \"hali bo'sh\" belgili "
                   "sahifalarning ma'lumot manbasi bugun yo'q.")),
    ]), ctx.now_real_us)
    return layout(page, body, ctx, available_needs(ctx.gw), ctx.opts.mark_synthetic)


# ===========================================================================
# server
# ===========================================================================


def is_loopback(host: str) -> bool:
    """Manzil loopback'mi. Noma'lum bo'lsa FALSE (fail-closed).

    NEGA fail-closed: noma'lum manzilni "ehtimol localhost" deb hisoblash
    tirik tizim holatini tashqariga ochib qo'yishi mumkin bo'lardi.
    """
    h = (host or "").strip().lower()
    if h in LOOPBACK_NAMES:
        return True
    try:
        return ipaddress.ip_address(h).is_loopback
    except ValueError:
        return False


def _asset_files() -> dict[str, str]:
    """`gui_assets/` dagi berish mumkin fayllar: nom -> yo'l (whitelist).

    NEGA whitelist: yo'lni foydalanuvchi matnidan yasash path traversal
    beradi. Bu yerda nom katalogning O'Z ro'yxatidan keladi, demak
    so'rovdagi matn hech qachon yo'lga aylanmaydi.
    """
    out: dict[str, str] = {}
    try:
        for name in os.listdir(ASSET_DIR):
            path = os.path.join(ASSET_DIR, name)
            if os.path.isfile(path):
                out[name] = path
    except OSError:
        pass
    return out


ASSET_TYPES = {
    ".css": "text/css; charset=utf-8",
    ".js": "text/javascript; charset=utf-8",
    ".svg": "image/svg+xml",
    ".png": "image/png",
    ".ico": "image/vnd.microsoft.icon",
}


class GuiHandler(http.server.BaseHTTPRequestHandler):
    """FAQAT GET. POST / PUT / DELETE qo'llanmaydi (qoida 9)."""

    protocol_version = "HTTP/1.1"
    server_version = f"revix-gui/{GUI_VERSION}"
    sys_version = ""

    # `serve()` o'rnatadi.
    opts: Options
    gateway: Gateway

    def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A003
        if getattr(self, "opts", None) is not None and self.opts.verbose:
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        # Kesh YO'Q: har sahifa o'z o'qish vaqtini ko'rsatadi va brauzer
        # keshidan kelgan sahifa o'sha vaqtni YOLG'ON qilib qo'yardi.
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802 -- BaseHTTPRequestHandler API
        path = self.path.split("?", 1)[0].split("#", 1)[0]
        ctx = Context(opts=self.opts, gw=self.gateway, now_real_us=cli.real_us())

        if path.startswith("/assets/"):
            return self._serve_asset(path[len("/assets/"):])
        if path.startswith("/figure/"):
            return self._serve_figure(path[len("/figure/"):])

        slug = path.strip("/")
        if slug in PAGE_BY_SLUG:
            try:
                html_text = render_page(slug, ctx)
            except Exception as exc:  # noqa: BLE001 -- xato SAHIFADA ko'rinadi
                html_text = self._error_page(slug, exc, ctx)
                return self._send(500, html_text.encode("utf-8"),
                                  "text/html; charset=utf-8")
            return self._send(200, html_text.encode("utf-8"),
                              "text/html; charset=utf-8")

        return self._send(404, render_not_found(path, ctx).encode("utf-8"),
                          "text/html; charset=utf-8")

    def do_HEAD(self) -> None:  # noqa: N802
        self.do_GET()

    def _error_page(self, slug: str, exc: BaseException, ctx: Context) -> str:
        """Render xatosi JIM QOLMAYDI -- sahifada aytiladi (fail-closed)."""
        page = PageDef("500", "Render xatosi", lambda _c: "", ("config",),
                       "Sahifa renderlanmadi.")
        body = panel("Render xatosi", Source("config", "revix.gui"), "".join([
            kv([("sahifa", text_html(slug)), ("istisno", text_html(repr(exc)))]),
            notice("critical", "Bu sahifa renderlanmadi",
                   esc_paragraph(
                       "Istisno yuz berdi va u YASHIRILMADI. Qisman "
                       "renderlangan sahifa ko'rsatilmaydi: yarim to'ldirilgan "
                       "panel to'liq panel kabi ko'rinadi va bu yolg'on "
                       "bo'lardi.")),
        ]), ctx.now_real_us)
        return layout(page, body, ctx, available_needs(ctx.gw),
                      ctx.opts.mark_synthetic)

    def _serve_asset(self, name: str) -> None:
        files = _asset_files()
        if name not in files:
            return self._send(404, b"asset topilmadi\n", "text/plain; charset=utf-8")
        ctype = ASSET_TYPES.get(os.path.splitext(name)[1], "application/octet-stream")
        try:
            with open(files[name], "rb") as fh:
                data = fh.read()
        except OSError as exc:
            return self._send(500, repr(exc).encode("utf-8"),
                              "text/plain; charset=utf-8")
        return self._send(200, data, ctype)

    def _serve_figure(self, name: str) -> None:
        """`figures/<nom>.svg` -- `FIGURE_NAMES` bo'yicha qat'iy whitelist.

        NEGA whitelist: nom so'rovdan keladi. Faqat `figures.py` e'lon qilgan
        oltita nom qabul qilinadi, demak so'rovdagi matn yo'lga aylanmaydi.
        """
        if not name.endswith(".svg"):
            return self._send(404, b"figura topilmadi\n", "text/plain; charset=utf-8")
        stem = name[: -len(".svg")]
        if stem not in FIGURE_NAMES:
            return self._send(404, b"noma'lum figura\n", "text/plain; charset=utf-8")
        derived, _src = self.gateway.derived()
        info = ((derived or {}).get("figures") or {}).get(stem) or {}
        path = info.get("svg_path")
        if not path:
            return self._send(404, b"figura fayli yo'q\n", "text/plain; charset=utf-8")
        try:
            with open(path, "rb") as fh:
                data = fh.read()
        except OSError as exc:
            return self._send(500, repr(exc).encode("utf-8"),
                              "text/plain; charset=utf-8")
        return self._send(200, data, "image/svg+xml")


def make_server(opts: Options) -> http.server.ThreadingHTTPServer:
    """Serverni yasaydi (hali `serve_forever` qilmaydi).

    Loopback bo'lmagan bind `--allow-remote` siz RAD ETILADI -- bu server
    tirik tizim holatini o'qiydi (modul docstring'i).
    """
    if not is_loopback(opts.host) and not opts.allow_remote:
        raise ValueError(
            f"bind {opts.host!r} loopback emas. Bu server tirik tizim "
            f"holatini (cgroup, PSI, unit, journal) o'qiydi va tashqariga "
            f"ochilmasligi kerak. Ataylab kerak bo'lsa --allow-remote bering."
        )
    gateway = Gateway(opts)

    class _Handler(GuiHandler):
        pass

    _Handler.opts = opts
    _Handler.gateway = gateway

    class _Server(http.server.ThreadingHTTPServer):
        # NEGA `allow_reuse_address = False`: True bo'lsa server band portga
        # ham "muvaffaqiyatli" bog'lanib, boshqa jarayonning so'rovlarini
        # bo'lishib olishi mumkin. Bu yerda band port XATO bo'lishi kerak.
        allow_reuse_address = False
        daemon_threads = True
        address_family = (socket.AF_INET6 if ":" in opts.host else socket.AF_INET)

    return _Server((opts.host, opts.port), _Handler)


# ===========================================================================
# statik render (vizual tekshiruv uchun)
# ===========================================================================


def render_to_dir(opts: Options, out_dir: str) -> list[str]:
    """Har sahifani `<out_dir>/<slug>.html` ga yozadi + aktivlarni ko'chiradi.

    NEGA bu bor: sahifani brauzerda ochib KO'Z bilan tekshirish uchun
    serverni ochiq qoldirish shart emas. Chiqish statik, ya'ni tekshiruv
    takrorlanadi.
    """
    gateway = Gateway(opts)
    os.makedirs(os.path.join(out_dir, "assets"), exist_ok=True)
    for name, path in _asset_files().items():
        shutil.copyfile(path, os.path.join(out_dir, "assets", name))
    written: list[str] = []
    for page in PAGES:
        ctx = Context(opts=opts, gw=gateway, now_real_us=cli.real_us())
        slug = page.slug or "index"
        target = os.path.join(out_dir, f"{slug}.html")
        text = render_page(page.slug, ctx)
        # Statik faylda `/assets/...` ildizdan ishlamaydi -> nisbiy qilinadi.
        text = text.replace('href="/assets/', 'href="assets/')
        text = text.replace('src="/assets/', 'src="assets/')
        with open(target, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        written.append(target)
    return written


# ===========================================================================
# CLI
# ===========================================================================


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="revix-gui",
        description=("REVIX dashboard -- tizim holatini FAQAT haqiqiy manbadan "
                     "o'qib ko'rsatadi. Default bind: localhost."),
    )
    ap.add_argument("--host", default=DEFAULT_HOST,
                    help=f"bind manzili (default {DEFAULT_HOST} -- loopback)")
    ap.add_argument("--port", type=int, default=DEFAULT_PORT,
                    help=f"bind porti (default {DEFAULT_PORT})")
    ap.add_argument("--allow-remote", action="store_true",
                    help="loopback bo'lmagan manzilga bog'lanishga ATAYLAB "
                         "ruxsat (tirik tizim holati ochiladi)")
    ap.add_argument("--interval", type=float, default=cli.MIN_RATE_WINDOW_S,
                    dest="interval_s", metavar="SEC",
                    help=f"PSI tezlik oynasi, s (min {cli.MIN_RATE_WINDOW_S:g} "
                         f"-- PSI kadensi 2 s)")
    ap.add_argument("--cache-s", type=float, default=DEFAULT_CACHE_S,
                    metavar="SEC", help="tirik snapshot keshi TTL (0 = keshsiz)")
    ap.add_argument("--doctor-cache-s", type=float, default=DEFAULT_DOCTOR_CACHE_S,
                    metavar="SEC", help="doctor hisoboti keshi TTL")
    ap.add_argument("--datasets", default=os.path.join(REPO_ROOT, "datasets"),
                    dest="datasets_dir", metavar="DIR",
                    help="run kataloglari qidiriladigan katalog")
    ap.add_argument("--run-dir", default=None, metavar="DIR",
                    help="aniq run katalogi (berilmasa `--datasets` skanlanadi)")
    ap.add_argument("--mark-synthetic", action="store_true",
                    help="butun chiqishni SINTETIK deb belgilash (vizual "
                         "tekshiruv uchun). Belgi faqat QO'SHILADI.")
    ap.add_argument("--render-to", default=None, metavar="DIR",
                    help="serverni ochmasdan har sahifani statik HTML ga yozish")
    ap.add_argument("--verbose", action="store_true",
                    help="har so'rovni stderr'ga yozish")
    return ap


def main(argv: list[str] | None = None) -> int:
    """`python3 -m revix.gui` kirish nuqtasi.

    Chiqish kodi: 0 -- toza to'xtash (Ctrl-C ham); 1 -- bind rad etildi yoki
    port band; 2 -- argparse (noto'g'ri flag).
    """
    args = build_parser().parse_args(argv)
    opts = Options(
        host=args.host,
        port=args.port,
        interval_s=args.interval_s,
        cache_s=args.cache_s,
        doctor_cache_s=args.doctor_cache_s,
        datasets_dir=args.datasets_dir,
        run_dir=args.run_dir,
        allow_remote=args.allow_remote,
        mark_synthetic=args.mark_synthetic,
        verbose=args.verbose,
    )

    if args.render_to:
        written = render_to_dir(opts, args.render_to)
        for path in written:
            print(path)
        return 0

    try:
        httpd = make_server(opts)
    except ValueError as exc:
        print(f"revix gui: {exc}", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"revix gui: bind {opts.host}:{opts.port} bajarilmadi: {exc!r}",
              file=sys.stderr)
        return 1

    url = f"http://{opts.host}:{opts.port}/"
    # `flush=True` MAJBURIY: stdout faylga yoki quvurga yo'naltirilganda
    # Python uni buferlaydi, va `serve_forever()` qaytmaydi -- ya'ni bufer
    # hech qachon bo'shamaydi. Bu O'LCHANDI: `python3 -m revix.gui > faylga`
    # da URL satri 4 s dan keyin ham ko'rinmadi. Foydalanuvchiga esa aynan
    # URL darhol kerak.
    print(f"REVIX dashboard: {url}", flush=True)
    print(f"  manba: tirik cli hisobotlari + {opts.datasets_dir} run'lari",
          flush=True)
    print("  faqat o'qish; to'xtatish uchun Ctrl-C", flush=True)
    if not is_loopback(opts.host):
        print("  OGOHLIK: loopback BO'LMAGAN manzil -- tirik tizim holati "
              "tashqariga ochilgan", file=sys.stderr, flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("")
    finally:
        httpd.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
