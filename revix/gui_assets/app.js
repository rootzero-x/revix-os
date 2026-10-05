/* REVIX dashboard skripti -- SON YARATMAYDI, faqat VAQT o'tishini ko'rsatadi
 * va SERVER bergan sahifani qayta oladi.
 *
 * DIZAYN QOIDALARI (buzilmaydi):
 *
 *   1. BU SKRIPT HECH QANDAY O'LCHOV QIYMATINI YOZMAYDI, o'zgartirmaydi,
 *      interpolyatsiya qilmaydi va formatlamaydi. U faqat server tomonida
 *      HTML'ga joylangan `data-read-real-us` tamg'asidan o'qishning YOSHINI
 *      hisoblaydi va avtomatik yangilanishda SERVER renderlagan `<main>` ni
 *      butunligicha almashtiradi. NEGA: dashboard'dagi har bir son haqiqiy
 *      manbadan o'qilgan bo'lishi SHART; brauzer qiymat yasasa, u qaydan
 *      kelgani tekshirilmay qoladi.
 *
 *   2. AVTOMATIK YANGILANISH (jurnal 19 §11) -- faqat server
 *      `body[data-autorefresh-s] > 0` desa. Har N soniyada AYNAN SHU sahifa
 *      (bir xil origin, `fetch`, CSP `default-src 'self'` ichida) qayta
 *      olinadi va FAQAT `<main>` almashtiriladi: menyu, sarlavha, aylantirish
 *      joyi, fokus va `<details>` ochiq/yopiq holati saqlanadi. Ekranda
 *      "avtomatik yangilanish: N s" yozuvi va "Pauza" tugmasi bor -- jimgina
 *      yangilanish YO'Q. Doctor ishga tushiradigan sahifalarda server 0
 *      beradi va yozuv sababni aytadi. `file://` (statik render) da
 *      yangilanish o'chiq. Tarmoq xatosida eski tarkib QOLADI, yozuv xatoni
 *      aytadi va yosh o'sib, `stale` bo'ladi -- eski son "yangi" bo'lib
 *      ko'rinmaydi.
 *
 *   3. ESKI O'QISH ESKI KO'RINADI. Yosh `stale_after_s` dan oshsa, manba
 *      nishoniga `stale` klassi qo'yiladi (rangi `style.css` da). Yosh har
 *      yangilanishda YANGI sahifaning `data-server-now-real-us` dan qayta
 *      hisoblanadi.
 *
 *   4. JavaScript O'CHIRILGAN BO'LSA ham sahifa to'liq o'qiladi: server
 *      o'qish vaqtini matn sifatida ham bosadi va `stale` klassini o'zi
 *      ham qo'yadi. Avtomatik yangilanish yozuvi ham JS bilan yaratiladi,
 *      ya'ni JS yo'q bo'lsa "yangilanadi" degan yolg'on yozuv ham yo'q.
 *
 *   5. YIG'ILADIGAN BLOKLAR (`<details data-key>`) ochiq/yopiq holatini
 *      brauzer xotirasida (localStorage) eslab qoladi. Bu faqat KO'RINISH
 *      holati -- serverga hech narsa yubormaydi. localStorage ishlamasa
 *      sahifa server bergan default holatda qoladi. `data-force-open` bo'lsa
 *      server holati USTUN.
 */

(function () {
  "use strict";

  var store = null;
  try { store = window.localStorage; } catch (e) { store = null; }

  function storeGet(k) { try { return store ? store.getItem(k) : null; } catch (e) { return null; } }
  function storeSet(k, v) { try { if (store) { store.setItem(k, v); } } catch (e) { /* faqat ko'rinish */ } }

  // --- yig'iladigan bloklar holati (qoida 5) -----------------------------

  function detailsKey(el) {
    var key = el.getAttribute("data-key");
    if (!key) { return null; }
    var scope = el.getAttribute("data-scope") === "global" ? "*" : window.location.pathname;
    return "revix-details:" + scope + ":" + key;
  }

  function bindDetails(root, current) {
    // `current`: avtomatik yangilanishdan OLDINGI holat (kalit+tartib -> open).
    var seen = {};
    var blocks = root.querySelectorAll("details[data-key]");
    for (var b = 0; b < blocks.length; b++) {
      (function (el) {
        var k = detailsKey(el);
        if (!k) { return; }
        seen[k] = (seen[k] || 0) + 1;
        var slot = k + "#" + seen[k];
        if (current && Object.prototype.hasOwnProperty.call(current, slot)) {
          el.open = current[slot];
        } else if (el.getAttribute("data-force-open") !== "1") {
          var saved = storeGet(k);
          if (saved === "1") { el.open = true; }
          if (saved === "0") { el.open = false; }
        }
        el.addEventListener("toggle", function () { storeSet(k, el.open ? "1" : "0"); });
      })(blocks[b]);
    }
  }

  function snapshotDetails(root) {
    var out = {};
    var seen = {};
    var blocks = root.querySelectorAll("details[data-key]");
    for (var b = 0; b < blocks.length; b++) {
      var k = detailsKey(blocks[b]);
      if (!k) { continue; }
      seen[k] = (seen[k] || 0) + 1;
      out[k + "#" + seen[k]] = blocks[b].open;
    }
    return out;
  }

  bindDetails(document, null);

  // --- o'qish yoshi (qoida 3) ---------------------------------------------
  // Serverning "hozir" i va brauzer soati farq qilishi mumkin, shuning uchun
  // yosh = (server hozir - o'qilgan) + shundan keyin o'tgan monotonik vaqt.

  var root = document.documentElement;
  var serverNowUs = parseInt(root.getAttribute("data-server-now-real-us") || "", 10);
  var t0 = now();

  function now() { return (window.performance && performance.now) ? performance.now() : Date.now(); }

  function ageSeconds(readUs) {
    return (serverNowUs - readUs) / 1e6 + (now() - t0) / 1000;
  }

  function fmtAge(s) {
    if (s < 0) { return "?"; }          // soat orqaga ketgan -- taxmin qilinmaydi
    if (s < 90) { return Math.round(s) + " s oldin"; }
    if (s < 5400) { return Math.round(s / 60) + " min oldin"; }
    return Math.round(s / 3600) + " soat oldin";
  }

  function tick() {
    if (!isFinite(serverNowUs)) { return; }
    var nodes = document.querySelectorAll("[data-read-real-us]");
    for (var i = 0; i < nodes.length; i++) {
      var el = nodes[i];
      var readUs = parseInt(el.getAttribute("data-read-real-us"), 10);
      if (!isFinite(readUs)) { continue; }
      var limit = parseFloat(el.getAttribute("data-stale-after-s"));
      var age = ageSeconds(readUs);
      var slot = el.querySelector(".age");
      if (slot) { slot.textContent = fmtAge(age); }
      if (isFinite(limit) && age > limit) { el.classList.add("stale"); }
    }
  }

  tick();
  window.setInterval(tick, 1000);

  // Mahalliy devor soati -- O'LCHOV emas, ataylab "mahalliy soat" deb nomlangan.
  var clock = document.getElementById("local-clock");
  function pad(n) { return (n < 10 ? "0" : "") + n; }
  function hms(d) { return pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds()); }
  if (clock) {
    var paint = function () { clock.textContent = "mahalliy soat " + hms(new Date()); };
    paint();
    window.setInterval(paint, 1000);
  }

  // --- avtomatik yangilanish (qoida 2) -------------------------------------

  var badge = document.getElementById("autoref");
  var body = document.body;
  var period = parseInt((body && body.getAttribute("data-autorefresh-s")) || "0", 10);
  var why = (body && body.getAttribute("data-autorefresh-why")) || "";
  var httpPage = window.location.protocol === "http:" || window.location.protocol === "https:";
  if (!badge) { return; }

  if (!(period > 0) || !httpPage || !window.fetch || !window.DOMParser) {
    badge.textContent = "avtomatik yangilanish o'chiq";
    badge.title = why || (httpPage ? "brauzer fetch/DOMParser ni qo'llamaydi"
                                   : "statik fayl -- server yo'q");
    badge.className = "autoref off";
    return;
  }

  var PAUSE_KEY = "revix-autorefresh-paused";
  var paused = storeGet(PAUSE_KEY) === "1";
  var busy = false;
  var lastOk = null;      // oxirgi muvaffaqiyatli yangilanish (Date)
  var lastErr = null;

  var label = document.createElement("span");
  label.className = "autoref-text";
  var btn = document.createElement("button");
  btn.type = "button";
  btn.className = "autoref-toggle";
  badge.appendChild(label);
  badge.appendChild(btn);

  function paintBadge() {
    var txt;
    if (paused) {
      txt = "avtomatik yangilanish: pauzada";
    } else {
      txt = "avtomatik yangilanish: " + period + " s";
    }
    if (lastErr) {
      txt += " · yangilanmadi (" + lastErr + ")";
    } else if (lastOk) {
      txt += " · oxirgi " + hms(lastOk);
    }
    label.textContent = txt;
    btn.textContent = paused ? "Davom ettirish" : "Pauza";
    btn.setAttribute("aria-pressed", paused ? "true" : "false");
    badge.className = "autoref" + (paused ? " paused" : "") + (lastErr ? " err" : "");
  }

  btn.addEventListener("click", function () {
    paused = !paused;
    storeSet(PAUSE_KEY, paused ? "1" : "0");
    paintBadge();
    if (!paused) { schedule(200); }
  });

  function focusInfo(main) {
    var a = document.activeElement;
    if (!a || !main.contains(a)) { return null; }
    var all = main.querySelectorAll("a, summary, button, [tabindex]");
    for (var i = 0; i < all.length; i++) { if (all[i] === a) { return i; } }
    return null;
  }

  function userBusy(main) {
    // Matn belgilangan yoki sabab tooltip'i (`title`) o'qilayotgan bo'lsa,
    // shu siklda almashtirilmaydi -- aks holda belgilash/tooltip yo'qoladi.
    var sel = window.getSelection ? window.getSelection() : null;
    if (sel && String(sel).length > 0 && sel.anchorNode && main.contains(sel.anchorNode)) {
      return true;
    }
    try { if (main.querySelector("[title]:hover")) { return true; } } catch (e) { /* :hover yo'q */ }
    return false;
  }

  function swap(text) {
    var doc = new DOMParser().parseFromString(text, "text/html");
    var fresh = doc.querySelector("main");
    var cur = document.querySelector("main");
    if (!fresh || !cur) { throw new Error("main yo'q"); }
    var openState = snapshotDetails(cur);
    var focusIdx = focusInfo(cur);
    var x = window.scrollX, y = window.scrollY;
    var adopted = document.adoptNode(fresh);
    cur.parentNode.replaceChild(adopted, cur);
    bindDetails(adopted, openState);
    // Yosh YANGI sahifaning server vaqtidan hisoblanadi (qoida 3).
    var ns = parseInt(doc.documentElement.getAttribute("data-server-now-real-us") || "", 10);
    if (isFinite(ns)) { serverNowUs = ns; t0 = now(); }
    if (focusIdx !== null) {
      var all = adopted.querySelectorAll("a, summary, button, [tabindex]");
      if (all[focusIdx]) { try { all[focusIdx].focus({ preventScroll: true }); } catch (e) { all[focusIdx].focus(); } }
    }
    // Aylantirish joyi fokusdan KEYIN tiklanadi: eski brauzer `preventScroll`
    // ni bilmasa ham sahifa sakramaydi.
    window.scrollTo(x, y);
    tick();
  }

  var timer = null;
  function schedule(ms) {
    if (timer) { window.clearTimeout(timer); }
    timer = window.setTimeout(cycle, ms);
  }

  function cycle() {
    timer = null;
    var main = document.querySelector("main");
    if (paused || busy || document.hidden || !main || userBusy(main)) {
      schedule(period * 1000);
      return;
    }
    busy = true;
    window.fetch(window.location.pathname + window.location.search,
                 { cache: "no-store", credentials: "same-origin" })
      .then(function (r) { return r.text(); })
      .then(function (text) { swap(text); lastOk = new Date(); lastErr = null; })
      .catch(function () { lastErr = "server javob bermadi " + hms(new Date()); })
      .then(function () { busy = false; paintBadge(); schedule(period * 1000); });
  }

  paintBadge();
  schedule(period * 1000);
})();
