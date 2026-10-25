(function () {
  var doc = document.documentElement;

  /* ---------------- language ---------------- */
  var nodes = Array.prototype.slice.call(document.querySelectorAll('[data-zh]'));
  nodes.forEach(function (el) { el.dataset.en = el.innerHTML; });

  var titleEN = doc.dataset.titleEn || document.title;
  var titleZH = doc.dataset.titleZh || titleEN;

  function setLang(lang) {
    doc.dataset.lang = lang;
    doc.lang = lang === 'zh' ? 'zh-CN' : 'en';
    nodes.forEach(function (el) {
      el.innerHTML = lang === 'zh' ? el.dataset.zh : el.dataset.en;
    });
    document.title = lang === 'zh' ? titleZH : titleEN;
    Array.prototype.forEach.call(document.querySelectorAll('[data-lang-btn]'), function (b) {
      var on = b.dataset.langBtn === lang;
      b.classList.toggle('is-active', on);
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
    });
    try { localStorage.setItem('site-lang', lang); } catch (e) {}
  }

  Array.prototype.forEach.call(document.querySelectorAll('[data-lang-btn]'), function (b) {
    b.addEventListener('click', function () { setLang(b.dataset.langBtn); });
  });

  var savedLang = null;
  try { savedLang = localStorage.getItem('site-lang'); } catch (e) {}
  setLang(savedLang === 'zh' ? 'zh' : 'en');

  /* ---------------- theme ---------------- */
  var THEME_KEY = 'site-theme';
  var themeBtn = document.querySelector('[data-theme-btn]');

  function current() { return doc.dataset.theme === 'dark' ? 'dark' : 'light'; }

  function label() {
    if (!themeBtn) return;
    themeBtn.setAttribute('aria-label', current() === 'dark' ? 'Switch to light theme' : 'Switch to dark theme');
    themeBtn.setAttribute('title', current() === 'dark' ? 'Light' : 'Dark');
  }

  function setTheme(t) {
    doc.dataset.theme = t;
    label();
    try { localStorage.setItem(THEME_KEY, t); } catch (e) {}
  }

  label();
  if (themeBtn) {
    themeBtn.addEventListener('click', function () {
      setTheme(current() === 'dark' ? 'light' : 'dark');
    });
  }

  /* ---------------- anchor offset ----------------
     Chrome ignores scroll-margin-top on the first fragment jump when
     scroll-behavior:smooth is on, so the sticky header covers the target. */
  var HEADER = 96;

  function fixHash() {
    if (!location.hash) return;
    var el = null;
    try { el = document.querySelector(location.hash); } catch (e) { return; }
    if (!el) return;
    var y = el.getBoundingClientRect().top + window.pageYOffset - HEADER;
    if (Math.abs(window.pageYOffset - y) < 4) return;
    window.scrollTo({ top: Math.max(0, y), behavior: 'instant' });
  }

  if (location.hash) {
    window.addEventListener('load', function () { setTimeout(fixHash, 60); });
    setTimeout(fixHash, 260);
  }
})();
