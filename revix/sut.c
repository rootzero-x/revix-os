/*
 * REVIX SUT -- Service Under Test.
 *
 * `docs/architecture/03-sut-protokoli.md` (sut-protocol/v1) ning to'liq
 * implementatsiyasi. Prober shu spetsifikatsiyaga qarab MUSTAQIL yozilgani
 * uchun bu fayl protokoldan bir bayt ham chetga chiqmaydi.
 *
 * NEGA BU FAYL SHUNCHALIK JIDDIY: PREREGISTRATION.md §4 ning 5-bandi
 * (throughput >= theta * R_ref) -- Verified Recovery ni oddiy
 * process-liveness'dan ajratadigan YAGONA narsa. O'sha band `progress`
 * hisoblagichiga tayanadi. Hisoblagich noto'g'ri bo'lsa (probe javobi uni
 * oshirsa, yoki iteratsiya o'zgaruvchan ish bajarsa) -- butun ilmiy hissa
 * qulaydi. Shuning uchun buzilmaydigan qoidalar:
 *
 *   1. `progress` FAQAT ish tsiklida oshadi. Probe javobi hech qachon
 *      oshirmaydi -- aks holda o'lchov o'zini o'lchagan bo'lardi.
 *   2. Bitta iteratsiya = deterministik doimiy CPU ishi. Barqaror holatda
 *      IO yo'q, malloc yo'q -- shunda Δprogress/Δt haqiqiy throughput.
 *   3. Tsikl ABSOLUT CLOCK_MONOTONIC deadline'larda yuradi. sleep(period)
 *      drift yig'adi va throughput o'lchovini sekin surib yuborardi.
 *   4. Watchdog ping'i ISH TSIKLIDAN yuboriladi. Shunda qotib qolgan ish
 *      tsikli watchdog'ni ham to'xtatadi va `stop_progress`/`deadlock`
 *      systemd'ga ham ko'rinadi (protokol §6).
 *
 * THREAD MODELI (ikki thread, ataylab):
 *   - main thread  : accept tsikli. Socket har doim javob beradi.
 *   - work thread  : ish tsikli + watchdog.
 * Sabab: `stop_progress` fault'i "fail-silent" bo'lishi kerak -- ish tsikli
 * o'lgan, socket esa tirik. Bitta thread bilan bu holat ifodalanmaydi.
 *
 * libsystemd'ga BOG'LANMAYDI: sd_notify o'zimizda yozilgan (pastga qarang).
 * Repo ataylab yangi bog'liqlik qo'shmaydi.
 */

#define _GNU_SOURCE

#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <limits.h>
#include <pthread.h>
#include <signal.h>
#include <stdarg.h>
#include <stdatomic.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/time.h>
#include <sys/types.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>

#define PROTO_VERSION 1
#define IMPL_TAG "revix-sut-c/1"
#define MAX_MSG 4096
#define MAX_ARGV 32
#define LISTEN_BACKLOG 64
#define EXIT_CONFIG 78          /* sysexits.h EX_CONFIG -- misconfiguration */
#define LEAK_CHUNK (1u << 20)   /* 1 MiB */

/* --- o'lchov holati -------------------------------------------------------- */

/* Atomik: probe (main thread) lock OLMASDAN o'qiydi. Bu shart -- aks holda
 * `spin`/`deadlock` fault'lari socket javobini ham bloklab qo'yardi va
 * `stop_progress` ning fail-silent semantikasi yo'qolardi. */
static _Atomic uint64_t g_progress = 0;

/* Ish birligining akkumulyatori. `volatile` -- optimizator butun hisobni
 * o'chirib tashlamasligi uchun (u holda "deterministik ish" yolg'on bo'lardi). */
static volatile uint64_t g_work_acc = 1469598103934665603ULL;

static uint64_t g_start_us;
static double g_rate_hz = 2000.0;          /* $REVIX_SUT_RATE_HZ */
static unsigned long g_work_rounds = 4096; /* bitta iteratsiyadagi ish */
static uint64_t g_watchdog_usec;           /* $WATCHDOG_USEC */

static _Atomic int g_ready = 0;            /* READY=1 yuborilganmi */
static _Atomic int g_work_stop = 0;        /* fault: stop_progress */
/* SIGTERM flag'i. `_Atomic sig_atomic_t`, oddiy `volatile` emas: flag signal
 * handler'da yoziladi va work thread'da o'qiladi. C11 handler ichida lock-free
 * atomikaga tegishga ruxsat beradi, `volatile` esa thread'lar orasida hech
 * narsa kafolatlamaydi (ThreadSanitizer aynan shu poygani ko'rsatdi). */
static _Atomic sig_atomic_t g_terminate = 0;

static char g_sock_path[108];              /* sun_path o'lchami */
static char g_invocation[65];
static int g_listen_fd = -1;

/* Ish lock'i: har iteratsiyada olinadi. Narxi -- bitta raqobatsiz atomik
 * juftlik (~20 ns), foydasi -- `spin` va `deadlock` fault'lari haqiqiy lock
 * ustida ifodalanadi, taqlid qilinmaydi. */
static pthread_mutex_t g_work_lock = PTHREAD_MUTEX_INITIALIZER;
static pthread_mutex_t g_aux_lock = PTHREAD_MUTEX_INITIALIZER;

/* Fault latch'lari: fault'lar idempotent (takroriy FAULT ikkinchi thread
 * yaratmaydi, lekin javob baribir `OK armed=<kind>`). */
static _Atomic int g_latch_spin = 0;
static _Atomic int g_latch_deadlock = 0;
static _Atomic int g_latch_leak = 0;
static _Atomic int g_fifo_armed = 0;
static _Atomic int g_latch_fifo = 0;
static char g_fifo_path[PATH_MAX];
static double g_leak_rate_mb_s = 8.0;
static unsigned long g_delay_ready_ms;     /* $REVIX_SUT_DELAY_READY_MS */
static void *g_leak_head;
static int *volatile g_null_ptr = NULL;    /* `sigsegv`: volatile -- constant-fold bo'lmasin */

/* --- vaqt ----------------------------------------------------------------- */

static uint64_t mono_us(void)
{
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000000u + (uint64_t)ts.tv_nsec / 1000u;
}

static void ts_add_ns(struct timespec *ts, uint64_t ns)
{
    ts->tv_sec += (time_t)(ns / 1000000000u);
    ts->tv_nsec += (long)(ns % 1000000000u);
    if (ts->tv_nsec >= 1000000000L) {
        ts->tv_nsec -= 1000000000L;
        ts->tv_sec += 1;
    }
}

static int ts_before(const struct timespec *a, const struct timespec *b)
{
    if (a->tv_sec != b->tv_sec)
        return a->tv_sec < b->tv_sec;
    return a->tv_nsec < b->tv_nsec;
}

static void sleep_ms(unsigned ms)
{
    struct timespec ts;
    ts.tv_sec = (time_t)(ms / 1000u);
    ts.tv_nsec = (long)(ms % 1000u) * 1000000L;
    while (nanosleep(&ts, &ts) != 0 && errno == EINTR)
        ;
}

/* --- sd_notify (libsystemd YO'Q) ------------------------------------------
 * $NOTIFY_SOCKET ga AF_UNIX/SOCK_DGRAM datagram. Ikki shakl qo'llanadi:
 *   "/run/systemd/notify"  -- oddiy fayl yo'li
 *   "@abstract-name"       -- abstrakt nom (sun_path[0] == '\0')
 * MSG_DONTWAIT ataylab: notify socket to'lib qolsa ish tsikli BLOKLANMASLIGI
 * kerak -- bloklangan work thread progress'ni to'xtatib o'lchovni buzardi.
 * Bitta ping yo'qolishi xavfsiz, chunki davr WATCHDOG_USEC/2 (2x zaxira). */
static int sd_notify(int unset_environment, const char *state)
{
    const char *path = getenv("NOTIFY_SOCKET");
    struct sockaddr_un sa;
    socklen_t len;
    ssize_t sent;
    size_t plen;
    int fd;

    if (path == NULL || path[0] == '\0')
        return 0;               /* systemd ostida emas -- no-op */

    memset(&sa, 0, sizeof sa);
    sa.sun_family = AF_UNIX;
    if (path[0] == '@') {
        plen = strlen(path + 1);
        if (plen == 0 || plen >= sizeof sa.sun_path)
            return -1;
        memcpy(sa.sun_path + 1, path + 1, plen);
        len = (socklen_t)(offsetof(struct sockaddr_un, sun_path) + 1 + plen);
    } else {
        plen = strlen(path);
        if (plen >= sizeof sa.sun_path)
            return -1;
        memcpy(sa.sun_path, path, plen);
        len = (socklen_t)(offsetof(struct sockaddr_un, sun_path) + plen + 1);
    }

    fd = socket(AF_UNIX, SOCK_DGRAM | SOCK_CLOEXEC, 0);
    if (fd < 0)
        return -1;
    sent = sendto(fd, state, strlen(state), MSG_NOSIGNAL | MSG_DONTWAIT,
                  (struct sockaddr *)&sa, len);
    close(fd);
    if (unset_environment)
        unsetenv("NOTIFY_SOCKET");
    return sent < 0 ? -1 : 0;
}

/* --- RSS ------------------------------------------------------------------
 * /proc/self/statm ning 2-maydoni = rezident sahifalar. stdio ishlatilmaydi
 * (fopen bufer ajratadi); bu faqat probe yo'lida chaqiriladi, ish tsiklida
 * emas -- shuning uchun iteratsiya narxiga tegmaydi. */
static uint64_t rss_kb(void)
{
    char buf[128];
    char *p;
    ssize_t n;
    int fd = open("/proc/self/statm", O_RDONLY | O_CLOEXEC);

    if (fd < 0)
        return 0;
    n = read(fd, buf, sizeof buf - 1);
    close(fd);
    if (n <= 0)
        return 0;
    buf[n] = '\0';
    p = strchr(buf, ' ');
    if (p == NULL)
        return 0;
    return (uint64_t)strtoull(p + 1, NULL, 10) *
           (uint64_t)sysconf(_SC_PAGESIZE) / 1024u;
}

/* --- ish birligi ---------------------------------------------------------- */

/* Deterministik, doimiy narxli, faqat CPU. Har chaqiruvda AYNAN
 * g_work_rounds marta aylanadi -- shuning uchun Δprogress/Δt bajarilgan ish
 * bilan proporsional. */
static void work_unit(void)
{
    uint64_t x = g_work_acc;
    unsigned long i;

    for (i = 0; i < g_work_rounds; i++) {
        x = x * 6364136223846793005ULL + 1442695040888963407ULL;
        x ^= x >> 29;
    }
    g_work_acc = x;
}

/* --- fault: block_fifo --------------------------------------------------- */

/* FIFO'dan bloklanuvchi o'qish. O_RDONLY bilan open FIFO'da yozuvchi
 * kelmaguncha bloklanadi -- aynan kerakli xatti-harakat. Qaytmaydi: ish
 * tsikli IO'da qotib qoladi, socket esa javob berishda davom etadi. */
static void block_on_fifo(void)
{
    char sink[256];

    for (;;) {
        int fd = open(g_fifo_path, O_RDONLY | O_CLOEXEC);
        if (fd < 0) {
            sleep_ms(1000);     /* yo'l yaroqsiz bo'lsa ham qaytmaymiz */
            continue;
        }
        while (read(fd, sink, sizeof sink) > 0)
            ;
        close(fd);
    }
}

/* --- ish tsikli (work thread) -------------------------------------------- */

static void *work_loop(void *arg)
{
    struct timespec next;
    struct timespec now_ts;
    uint64_t period_ns;
    uint64_t wd_period_us;
    uint64_t wd_next_us = 0;

    (void)arg;
    period_ns = (uint64_t)(1e9 / g_rate_hz);
    if (period_ns == 0)
        period_ns = 1;
    wd_period_us = g_watchdog_usec / 2;
    if (wd_period_us > 0)
        wd_next_us = mono_us() + wd_period_us;

    clock_gettime(CLOCK_MONOTONIC, &next);

    while (!atomic_load(&g_work_stop) && !atomic_load(&g_terminate)) {
        if (atomic_load(&g_fifo_armed))
            block_on_fifo();    /* qaytmaydi */

        pthread_mutex_lock(&g_work_lock);
        work_unit();
        atomic_fetch_add(&g_progress, 1);   /* iteratsiyaga AYNAN +1 */
        pthread_mutex_unlock(&g_work_lock);

        /* Watchdog ISH TSIKLIDAN yuboriladi (protokol §6): tsikl qotsa
         * watchdog ham qotadi. sendmsg iteratsiyaga emas, WATCHDOG_USEC/2
         * ga bir marta to'g'ri keladi -- odatda sekundlar, ya'ni iteratsiya
         * narxiga sezilarli hissa qo'shmaydi. */
        if (wd_period_us > 0) {
            uint64_t now = mono_us();
            if (now >= wd_next_us) {
                sd_notify(0, "WATCHDOG=1");
                wd_next_us = now + wd_period_us;
            }
        }

        /* Absolut deadline. Kechikib qolsak deadline QAYTA TIKLANADI, ya'ni
         * yo'qolgan iteratsiyalar "quvib yetilmaydi". Bu ataylab: quvib
         * yetish stall'ni burst bilan yashirib, throughput pasayishini
         * (§4 ning 5-bandi o'lchaydigan narsani) ko'rinmas qilardi.
         * guard.py dagi pacing qoidasi bilan bir xil. */
        ts_add_ns(&next, period_ns);
        clock_gettime(CLOCK_MONOTONIC, &now_ts);
        if (ts_before(&next, &now_ts)) {
            next = now_ts;
        } else {
            while (clock_nanosleep(CLOCK_MONOTONIC, TIMER_ABSTIME, &next,
                                   NULL) == EINTR)
                ;
        }
    }
    return NULL;
}

/* --- fault thread'lari --------------------------------------------------- */

static void *spin_thread(void *arg)
{
    volatile uint64_t burn = 0;

    (void)arg;
    /* Ish lock'ini ushlab tor spin -> livelock: jarayon tirik, CPU yonadi,
     * progress esa to'xtaydi (ish tsikli lock'da kutadi). */
    pthread_mutex_lock(&g_work_lock);
    for (;;)
        burn = burn + 1;
    return NULL;                /* yetib kelmaydi (kompilyator talab qiladi) */
}

static void *deadlock_a(void *arg)
{
    (void)arg;
    pthread_mutex_lock(&g_work_lock);
    sleep_ms(50);               /* B aux'ni olishiga kafolat */
    pthread_mutex_lock(&g_aux_lock);
    return NULL;                /* yetib kelmaydi */
}

static void *deadlock_b(void *arg)
{
    (void)arg;
    pthread_mutex_lock(&g_aux_lock);
    sleep_ms(50);
    pthread_mutex_lock(&g_work_lock);   /* teskari tartib -> tsikl */
    return NULL;                /* yetib kelmaydi */
}

static void *leak_thread(void *arg)
{
    uint64_t interval_us;
    uint64_t next_us;

    (void)arg;
    interval_us = (uint64_t)(1e6 * ((double)LEAK_CHUNK / 1048576.0) /
                             g_leak_rate_mb_s);
    if (interval_us == 0)
        interval_us = 1;
    next_us = mono_us();
    for (;;) {
        uint64_t now;
        void **chunk = malloc(LEAK_CHUNK);
        if (chunk == NULL) {
            sleep_ms(1000);     /* ajratish imkonsiz -- kutamiz, yiqilmaymiz */
            continue;
        }
        /* TEGISH shart: tegilmagan sahifa RSS'ga kirmaydi va pressure
         * yaratmaydi, ya'ni "leak" nomiga yolg'on bo'lardi. */
        memset(chunk, 0xa5, LEAK_CHUNK);
        chunk[0] = g_leak_head; /* zanjir: hech qachon free qilinmaydi */
        g_leak_head = chunk;

        next_us += interval_us;
        now = mono_us();
        if (next_us > now)
            sleep_ms((unsigned)((next_us - now) / 1000u) + 1u);
        else
            next_us = now;
    }
    return NULL;                /* yetib kelmaydi (kompilyator talab qiladi) */
}

static void spawn_detached(void *(*fn)(void *))
{
    pthread_t t;

    if (pthread_create(&t, NULL, fn, NULL) == 0)
        pthread_detach(t);
}

/* --- javob yozish -------------------------------------------------------- */

/* Protokol: satr oxiri YO'Q (datagram chegarasi = xabar chegarasi). */
static void send_reply(int fd, const char *fmt, ...)
    __attribute__((format(printf, 2, 3)));

static void send_reply(int fd, const char *fmt, ...)
{
    char buf[MAX_MSG];
    va_list ap;
    int n;

    va_start(ap, fmt);
    n = vsnprintf(buf, sizeof buf, fmt, ap);
    va_end(ap);
    if (n < 0)
        return;
    if ((size_t)n >= sizeof buf)
        n = (int)sizeof buf - 1;
    (void)send(fd, buf, (size_t)n, MSG_NOSIGNAL);
}

static void close_conn(int *pfd)
{
    if (*pfd >= 0) {
        /* Javob AF_UNIX'da allaqachon peer navbatiga o'tgan: close ma'lumotni
         * tashlamaydi. Shuning uchun `exit`/`sigkill_self` dan oldin javobni
         * yo'qotish xavfi yo'q. */
        close(*pfd);
        *pfd = -1;
    }
}

/* --- fault dispatcher ---------------------------------------------------- */

static const char *kv_lookup(int argc, char **argv, int from, const char *key)
{
    size_t kl = strlen(key);
    int i;

    for (i = from; i < argc; i++) {
        if (strncmp(argv[i], key, kl) == 0 && argv[i][kl] == '=')
            return argv[i] + kl + 1;
    }
    return NULL;
}

/* Fault "armed" e'loni: AVVAL javob, KEYIN harakat (protokol §5).
 * stderr'ga AYNAN bitta satr -- inject_ack bracket'ining SUT tomoni (§3). */
static void arm_and_ack(int *pfd, const char *kind)
{
    send_reply(*pfd, "OK armed=%s", kind);
    close_conn(pfd);
    fprintf(stderr, "FAULT ARMED %s mono_us=%" PRIu64 "\n", kind, mono_us());
    fflush(stderr);
}

static void handle_fault(int *pfd, int argc, char **argv)
{
    const char *kind;

    if (argc < 2) {
        send_reply(*pfd, "ERR bad_args");
        return;
    }
    kind = argv[1];

    if (strcmp(kind, "exit") == 0) {
        const char *v = kv_lookup(argc, argv, 2, "code");
        long code = 1;          /* spetsifikatsiya: default 1 */
        if (v != NULL) {
            char *end = NULL;
            code = strtol(v, &end, 10);
            if (end == v || *end != '\0' || code < 0 || code > 255) {
                send_reply(*pfd, "ERR bad_args");
                return;
            }
        }
        arm_and_ack(pfd, kind);
        _exit((int)code);
    }

    if (strcmp(kind, "sigkill_self") == 0) {
        arm_and_ack(pfd, kind);
        kill(getpid(), SIGKILL);
        _exit(1);               /* yetib kelmaydi */
    }

    if (strcmp(kind, "sigsegv") == 0) {
        arm_and_ack(pfd, kind);
        *g_null_ptr = 1;
        _exit(1);               /* yetib kelmaydi */
    }

    if (strcmp(kind, "stop_progress") == 0) {
        arm_and_ack(pfd, kind);
        /* Ish tsikli chiqadi -> progress muzlaydi, watchdog to'xtaydi,
         * socket esa javob berishda davom etadi (fail-silent). */
        atomic_store(&g_work_stop, 1);
        return;
    }

    if (strcmp(kind, "spin") == 0) {
        arm_and_ack(pfd, kind);
        if (atomic_exchange(&g_latch_spin, 1) == 0)
            spawn_detached(spin_thread);
        return;
    }

    if (strcmp(kind, "deadlock") == 0) {
        arm_and_ack(pfd, kind);
        if (atomic_exchange(&g_latch_deadlock, 1) == 0) {
            spawn_detached(deadlock_a);
            spawn_detached(deadlock_b);
        }
        return;
    }

    if (strcmp(kind, "block_fifo") == 0) {
        const char *path = kv_lookup(argc, argv, 2, "path");
        if (path == NULL || path[0] == '\0' ||
            strlen(path) >= sizeof g_fifo_path) {
            send_reply(*pfd, "ERR bad_args");
            return;
        }
        arm_and_ack(pfd, kind);
        /* NEGA: yo'l FAQAT latch'ni yutgan (birinchi) chaqiruvda yoziladi.
         * Ilgari takroriy FAULT g_fifo_path ni ish thread'i open()/read()
         * ichida o'qiyotgan paytda qayta yozardi -- ThreadSanitizer'ga ko'rinadigan
         * data race. Endi yo'l thread'ga atomik g_fifo_armed orqali (release)
         * e'lon qilinadi va keyin hech qachon o'zgarmaydi. Javob baribir
         * `OK armed=block_fifo` (idempotentlik, yuqoridagi latch qoidasi bilan
         * bir xil); protokol va fault semantikasi o'zgarmaydi. */
        if (atomic_exchange(&g_latch_fifo, 1) == 0) {
            snprintf(g_fifo_path, sizeof g_fifo_path, "%s", path);
            atomic_store(&g_fifo_armed, 1);     /* yo'l yozilgandan KEYIN */
        }
        return;
    }

    if (strcmp(kind, "leak") == 0) {
        const char *v = kv_lookup(argc, argv, 2, "rate_mb_s");
        double rate = 8.0;      /* spetsifikatsiyada default yo'q -- shu tanlandi */
        if (v != NULL) {
            char *end = NULL;
            rate = strtod(v, &end);
            if (end == v || *end != '\0' || !(rate > 0.0) || rate > 4096.0) {
                send_reply(*pfd, "ERR bad_args");
                return;
            }
        }
        arm_and_ack(pfd, kind);
        /* NEGA: tezlik FAQAT thread yaratilishidan OLDIN, latch'ni yutgan
         * chaqiruvda yoziladi. leak_thread uni bir marta, boshlanishida
         * o'qiydi; takroriy FAULT oldin buni thread ishlab turganda qayta
         * yozardi -- ta'siri yo'q, lekin ThreadSanitizer'ga ko'rinadigan data
         * race (o'lchov asbobida "ma'lum shovqin" bazasi qolmasin). pthread_create
         * happens-before beradi, ya'ni qiymat thread'ga xavfsiz e'lon qilinadi.
         * Xatti-harakat o'zgarmaydi: ilgari ham thread birinchi tezlikni
         * ishlatardi. */
        if (atomic_exchange(&g_latch_leak, 1) == 0) {
            g_leak_rate_mb_s = rate;
            spawn_detached(leak_thread);
        }
        return;
    }

    /* `FAULT` buyrug'i tanilgan, `kind` esa yo'q -> bad_args. `reason` enum'i
     * yopiq: unknown_command/bad_args/not_ready/internal. */
    send_reply(*pfd, "ERR bad_args");
}

/* --- ulanishni qayta ishlash -------------------------------------------- */

static void handle_conn(int fd)
{
    char buf[MAX_MSG + 2];
    char *argv[MAX_ARGV];
    char *save = NULL;
    char *tok;
    int argc = 0;
    ssize_t n;

    n = recv(fd, buf, MAX_MSG + 1, 0);
    if (n <= 0) {
        close(fd);
        return;
    }
    if (n > MAX_MSG) {          /* protokol maksimumidan katta */
        send_reply(fd, "ERR bad_args");
        close(fd);
        return;
    }
    buf[n] = '\0';
    /* Protokolda satr oxiri yo'q, lekin kelganini kechiramiz (toqatlilik
     * integratsiyani himoya qiladi). O'zimiz hech qachon yozmaymiz. */
    while (n > 0 && (buf[n - 1] == '\n' || buf[n - 1] == '\r' ||
                     buf[n - 1] == ' ' || buf[n - 1] == '\t'))
        buf[--n] = '\0';

    for (tok = strtok_r(buf, " \t", &save);
         tok != NULL && argc < MAX_ARGV;
         tok = strtok_r(NULL, " \t", &save))
        argv[argc++] = tok;

    if (argc == 0) {
        send_reply(fd, "ERR unknown_command");
    } else if (strcmp(argv[0], "PROBE") == 0) {
        if (!atomic_load(&g_ready)) {
            /* READY=1 dan oldin contract kuchda emas. `slow_start` fault
             * klassi shu yerda ko'rinadi: socket accept qiladi, xizmat esa
             * hali tayyor emas. */
            send_reply(fd, "ERR not_ready");
        } else {
            uint64_t prog = atomic_load(&g_progress);
            uint64_t rss = rss_kb();
            send_reply(fd,
                       "OK progress=%" PRIu64 " pid=%d invocation=%s"
                       " rss_kb=%" PRIu64 " mono_us=%" PRIu64,
                       prog, (int)getpid(), g_invocation, rss, mono_us());
        }
    } else if (strcmp(argv[0], "INFO") == 0) {
        /* INFO diagnostik: READY'dan oldin ham javob beradi. */
        send_reply(fd,
                   "OK proto=%d impl=%s progress=%" PRIu64 " pid=%d"
                   " invocation=%s uptime_us=%" PRIu64,
                   PROTO_VERSION, IMPL_TAG, atomic_load(&g_progress),
                   (int)getpid(), g_invocation, mono_us() - g_start_us);
    } else if (strcmp(argv[0], "FAULT") == 0) {
        handle_fault(&fd, argc, argv);
    } else {
        send_reply(fd, "ERR unknown_command");
    }

    if (fd >= 0)
        close(fd);              /* har ulanish -- bitta so'rov-javob */
}

/* --- ishga tushish ------------------------------------------------------- */

static void on_signal(int sig)
{
    (void)sig;
    /* Faqat flag: handler'da async-signal-safe ish qilinadi, boshqa hech narsa. */
    atomic_store(&g_terminate, 1);
}

/* $INVOCATION_ID ni AYNAN echo qiladi (prober uni o'zgarish detektori sifatida
 * ishlatadi -- PREREGISTRATION.md §8). Bo'sh joy yoki boshqaruv belgisi javob
 * framing'ini buzardi; bunday qiymat va yo'qlik holatida 32 nol. */
static void init_invocation(void)
{
    const char *env = getenv("INVOCATION_ID");
    size_t i;

    if (env != NULL && env[0] != '\0' && strlen(env) < sizeof g_invocation) {
        for (i = 0; env[i] != '\0'; i++) {
            if ((unsigned char)env[i] <= ' ' || (unsigned char)env[i] == 0x7f)
                break;
        }
        if (env[i] == '\0') {
            snprintf(g_invocation, sizeof g_invocation, "%s", env);
            return;
        }
    }
    memset(g_invocation, '0', 32);
    g_invocation[32] = '\0';
}

/* $REVIX_SUT_CONFIG: yaroqsiz bo'lsa READY'dan OLDIN nolga teng bo'lmagan kod
 * bilan chiqamiz (`misconfiguration` fault klassi). Qat'iy: notanish kalit ham
 * xato -- jimgina e'tiborsizlik konfiguratsiya xatosini yashirardi. */
static int load_config(const char *path)
{
    char line[512];
    FILE *fh = fopen(path, "r");
    int lineno = 0;

    if (fh == NULL) {
        fprintf(stderr, "CONFIG ERROR open %s: %s\n", path, strerror(errno));
        return -1;
    }
    while (fgets(line, sizeof line, fh) != NULL) {
        char *eq;
        char *end = NULL;
        size_t len = strlen(line);
        lineno++;
        if (len == sizeof line - 1 && line[len - 1] != '\n') {
            fprintf(stderr, "CONFIG ERROR %s:%d line too long\n", path, lineno);
            fclose(fh);
            return -1;
        }
        while (len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r' ||
                           line[len - 1] == ' ' || line[len - 1] == '\t'))
            line[--len] = '\0';
        if (len == 0 || line[0] == '#')
            continue;
        eq = strchr(line, '=');
        if (eq == NULL || eq == line) {
            fprintf(stderr, "CONFIG ERROR %s:%d not key=value\n", path, lineno);
            fclose(fh);
            return -1;
        }
        *eq = '\0';
        if (strcmp(line, "rate_hz") == 0) {
            double v = strtod(eq + 1, &end);
            if (end == eq + 1 || *end != '\0' || !(v > 0.0) || v > 1e7) {
                fprintf(stderr, "CONFIG ERROR %s:%d bad rate_hz\n",
                        path, lineno);
                fclose(fh);
                return -1;
            }
            g_rate_hz = v;
        } else if (strcmp(line, "work_unit_rounds") == 0) {
            unsigned long v = strtoul(eq + 1, &end, 10);
            if (end == eq + 1 || *end != '\0' || v == 0 || v > 10000000UL) {
                fprintf(stderr, "CONFIG ERROR %s:%d bad work_unit_rounds\n",
                        path, lineno);
                fclose(fh);
                return -1;
            }
            g_work_rounds = v;
        } else {
            fprintf(stderr, "CONFIG ERROR %s:%d unknown key %s\n",
                    path, lineno, line);
            fclose(fh);
            return -1;
        }
    }
    fclose(fh);
    return 0;
}

/* READY ni e'lon qilish. Protokol §6: socket TINGLAGANDAN keyin.
 * g_ready notify'dan oldin qo'yiladi -- systemd'dan READY ni ko'rgan prober
 * darhol probe qilganda javob tayyor bo'lishi kerak. sd_notify no-op bo'lsa
 * ham (systemd ostida emas) xizmat tayyor hisoblanadi, aks holda
 * systemd'siz test yoki qo'lda ishga tushirish imkonsiz bo'lardi. */
static void announce_ready(void)
{
    atomic_store(&g_ready, 1);
    sd_notify(0, "READY=1\nSTATUS=revix-sut listening");
}

/* `slow_start` (REVIX_SUT_DELAY_READY_MS) ALOHIDA thread'da kutadi, main
 * thread esa darhol accept qilishga o'tadi. Bu ataylab: kechikish accept
 * tsiklini to'xtatib turganda ulanishlar backlog'da jim yotardi va prober
 * faqat conn/rt timeout ko'rardi -- protokolning `not_ready` reason token'i
 * esa hech qachon yuzaga kelmasdi. Kutilgan xatti-harakat: socket accept
 * qiladi va PROBE ga `ERR not_ready` javob beradi, ya'ni "tirik, lekin hali
 * xizmat qilmayapti" holati qotib qolishdan farqlanadi. */
static void *ready_thread(void *arg)
{
    unsigned long left = g_delay_ready_ms;

    (void)arg;
    while (left > 0 && !atomic_load(&g_terminate)) {
        unsigned step = left > 50 ? 50u : (unsigned)left;
        sleep_ms(step);
        left -= step;
    }
    if (!atomic_load(&g_terminate))
        announce_ready();
    return NULL;
}

static int setup_socket(void)
{
    struct sockaddr_un sa;
    mode_t old_umask;
    int fd;

    if (strlen(g_sock_path) >= sizeof sa.sun_path) {
        fprintf(stderr, "SOCKET ERROR path too long: %s\n", g_sock_path);
        return -1;
    }
    /* Eski (stale) socket'ni o'chiramiz: oldingi invocation crash bilan
     * o'lgan bo'lsa fayl qolib, bind EADDRINUSE bilan yiqilardi -- ya'ni
     * restart o'lchovi fault emas, artefakt sababli buzilardi. */
    if (unlink(g_sock_path) != 0 && errno != ENOENT) {
        fprintf(stderr, "SOCKET ERROR unlink %s: %s\n",
                g_sock_path, strerror(errno));
        return -1;
    }
    fd = socket(AF_UNIX, SOCK_SEQPACKET | SOCK_CLOEXEC, 0);
    if (fd < 0) {
        fprintf(stderr, "SOCKET ERROR socket: %s\n", strerror(errno));
        return -1;
    }
    memset(&sa, 0, sizeof sa);
    sa.sun_family = AF_UNIX;
    memcpy(sa.sun_path, g_sock_path, strlen(g_sock_path));

    old_umask = umask(0077);    /* bind 0600 yaratishi uchun */
    if (bind(fd, (struct sockaddr *)&sa, sizeof sa) != 0) {
        fprintf(stderr, "SOCKET ERROR bind %s: %s\n",
                g_sock_path, strerror(errno));
        umask(old_umask);
        close(fd);
        return -1;
    }
    umask(old_umask);
    (void)chmod(g_sock_path, 0600);     /* umask'ga ishonmaymiz */

    if (listen(fd, LISTEN_BACKLOG) != 0) {
        fprintf(stderr, "SOCKET ERROR listen: %s\n", strerror(errno));
        close(fd);
        return -1;
    }
    return fd;
}

int main(void)
{
    struct sigaction sa;
    struct timeval tv;
    pthread_t worker;
    pthread_t ready;
    sigset_t block, old;
    const char *env;

    g_start_us = mono_us();
    init_invocation();

    env = getenv("REVIX_SUT_SOCKET");
    if (env != NULL && env[0] != '\0')
        snprintf(g_sock_path, sizeof g_sock_path, "%s", env);
    else
        snprintf(g_sock_path, sizeof g_sock_path,
                 "/run/user/%u/revix-sut.sock", (unsigned)getuid());

    env = getenv("REVIX_SUT_RATE_HZ");
    if (env != NULL && env[0] != '\0') {
        char *end = NULL;
        double v = strtod(env, &end);
        if (end == env || *end != '\0' || !(v > 0.0) || v > 1e7) {
            fprintf(stderr, "CONFIG ERROR bad REVIX_SUT_RATE_HZ=%s\n", env);
            return EXIT_CONFIG;
        }
        g_rate_hz = v;
    }

    env = getenv("REVIX_SUT_DELAY_READY_MS");
    if (env != NULL && env[0] != '\0')
        g_delay_ready_ms = strtoul(env, NULL, 10);

    env = getenv("WATCHDOG_USEC");
    if (env != NULL && env[0] != '\0')
        g_watchdog_usec = strtoull(env, NULL, 10);

    /* Config env'dan KEYIN o'qiladi, ya'ni ustun. Yaroqsiz bo'lsa READY
     * yuborilmasdan chiqamiz (§5 -- misconfiguration). */
    env = getenv("REVIX_SUT_CONFIG");
    if (env != NULL && env[0] != '\0' && load_config(env) != 0)
        return EXIT_CONFIG;

    memset(&sa, 0, sizeof sa);
    sa.sa_handler = on_signal;
    sigemptyset(&sa.sa_mask);
    sa.sa_flags = 0;            /* SA_RESTART YO'Q: accept() EINTR qaytsin */
    sigaction(SIGTERM, &sa, NULL);
    sigaction(SIGINT, &sa, NULL);
    signal(SIGPIPE, SIG_IGN);   /* o'lgan client javob yozishda o'ldirmasin */

    g_listen_fd = setup_socket();
    if (g_listen_fd < 0)
        return 1;

    /* SIGTERM/SIGINT ni work thread'da bloklaymiz: signal DOIM main
     * thread'ga tushsin, aks holda accept() EINTR olmay qolishi mumkin. */
    sigemptyset(&block);
    sigaddset(&block, SIGTERM);
    sigaddset(&block, SIGINT);
    pthread_sigmask(SIG_BLOCK, &block, &old);
    if (pthread_create(&worker, NULL, work_loop, NULL) != 0) {
        fprintf(stderr, "FATAL pthread_create: %s\n", strerror(errno));
        unlink(g_sock_path);
        return 1;
    }
    if (g_delay_ready_ms > 0 &&
        pthread_create(&ready, NULL, ready_thread, NULL) != 0) {
        fprintf(stderr, "FATAL pthread_create: %s\n", strerror(errno));
        unlink(g_sock_path);
        return 1;
    }
    pthread_sigmask(SIG_SETMASK, &old, NULL);

    /* Kechikish yo'q bo'lsa READY sinxron e'lon qilinadi: thread bilan
     * yuzaga kelishi mumkin bo'lgan "birinchi probe not_ready oldi" poygasi
     * bo'lmasin. */
    if (g_delay_ready_ms == 0)
        announce_ready();

    while (!atomic_load(&g_terminate)) {
        int fd = accept4(g_listen_fd, NULL, NULL, SOCK_CLOEXEC);
        if (fd < 0) {
            if (errno == EINTR || errno == ECONNABORTED)
                continue;
            if (errno == EMFILE || errno == ENFILE || errno == ENOBUFS ||
                errno == ENOMEM) {
                sleep_ms(10);   /* vaqtinchalik resurs tanqisligi */
                continue;
            }
            break;
        }
        /* Sekin yoki qotgan client accept tsiklini bloklab qo'ymasin. */
        tv.tv_sec = 1;
        tv.tv_usec = 0;
        (void)setsockopt(fd, SOL_SOCKET, SO_RCVTIMEO, &tv, sizeof tv);
        (void)setsockopt(fd, SOL_SOCKET, SO_SNDTIMEO, &tv, sizeof tv);
        handle_conn(fd);
    }

    /* SIGTERM'da toza chiqish: socket o'chiriladi, kod 0 (protokol §6).
     *
     * work thread ATAYLAB join qilinmaydi (ThreadSanitizer buni "thread leak"
     * deb ko'rsatadi -- kutilgan). Sabab: `stop_progress`, `spin`, `deadlock`
     * va `block_fifo` fault'larida ish tsikli qaytmaydi, ya'ni join abadiy
     * kutardi. systemd qotib qolgan xizmatni SIGTERM bilan to'xtatadi va
     * DARHOL chiqishimizni kutadi -- join bu holatda toza chiqishni
     * imkonsiz qilardi. */
    close(g_listen_fd);
    unlink(g_sock_path);
    fflush(stderr);
    return 0;
}
