/* REVIX dashboard skripti -- SON YARATMAYDI, faqat VAQT o'tishini ko'rsatadi.
 *
 * DIZAYN QOIDALARI (buzilmaydi):
 *
 *   1. BU SKRIPT HECH QANDAY O'LCHOV QIYMATINI YOZMAYDI, o'zgartirmaydi,
 *      interpolyatsiya qilmaydi va formatlamaydi. U faqat server tomonida
 *      HTML'ga joylangan `data-read-real-us` tamg'asidan o'qishning YOSHINI
 *      hisoblaydi. NEGA: dashboard'dagi har bir son haqiqiy manbadan
 *      o'qilgan bo'lishi SHART; agar brauzerdagi skript qiymat yozishga
 *      qodir bo'lsa, u qiymat qaydan kelgani tekshirilmay qoladi.
 *
 *   2. AUTO-REFRESH YO'Q. Sahifa o'zini jimgina yangilamaydi. NEGA: jimgina
 *      yangilangan sahifada foydalanuvchi qaysi sonni qachon o'qilganini
 *      bilmaydi; bu yerda esa butun maqsad shu. Yangilash -- ongli qadam
 *      (sahifani qayta yuklash).
 *
 *   3. ESKI O'QISH ESKI KO'RINADI. Yosh `stale_after_s` dan oshsa, manba
 *      nishoniga `stale` klassi qo'yiladi (rangi `style.css` da). NEGA:
 *      ochiq qoldirilgan sahifa eskirgan holatni "hozirgi" deb ko'rsatsa,
 *      u yolg'on gapiradi.
 *
 *   4. JavaScript O'CHIRILGAN BO'LSA ham sahifa to'liq o'qiladi: server
 *      o'qish vaqtini matn sifatida ham bosadi va `stale` klassini o'zi
 *      ham qo'yadi. Bu skript faqat vaqt o'tishini KUZATADI.
 */

(function () {
  "use strict";

  // Serverning "hozir" i va brauzerning soati farq qiladi (soat siljishi,
  // turli zona). Yoshni brauzer soatidan hisoblash xato bo'lardi, shuning
  // uchun server o'z `now` ini beradi va biz FAQAT shundan keyin o'tgan
  // monotonik brauzer vaqtini qo'shamiz.
  var root = document.documentElement;
  var serverNowUs = parseInt(root.getAttribute("data-server-now-real-us") || "", 10);
  if (!isFinite(serverNowUs)) { return; }
  var t0 = (window.performance && performance.now) ? performance.now() : 0;

  function ageSeconds(readUs) {
    var elapsedMs = ((window.performance && performance.now) ? performance.now() : 0) - t0;
    return (serverNowUs - readUs) / 1e6 + elapsedMs / 1000;
  }

  function fmtAge(s) {
    if (s < 0) { return "?"; }          // soat orqaga ketgan -- taxmin qilinmaydi
    if (s < 90) { return Math.round(s) + " s oldin"; }
    if (s < 5400) { return Math.round(s / 60) + " min oldin"; }
    return Math.round(s / 3600) + " soat oldin";
  }

  function tick() {
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

  // Mahalliy devor soati -- bu O'LCHOV emas, shuning uchun sarlavhada va
  // ataylab "mahalliy soat" deb nomlangan (panel ichidagi hech bir qiymat
  // bunga tayanmaydi).
  var clock = document.getElementById("local-clock");
  if (clock) {
    var paint = function () {
      var d = new Date();
      var p = function (n) { return (n < 10 ? "0" : "") + n; };
      clock.textContent = "mahalliy soat " + p(d.getHours()) + ":" + p(d.getMinutes()) + ":" + p(d.getSeconds());
    };
    paint();
    window.setInterval(paint, 1000);
  }
})();
