(function () {
  "use strict";
  var TIMEOUT_MS = 25000;
  var SLOW_MS = 8000;

  function $(id) { return document.getElementById(id); }
  function safeStorage(fn) { try { return fn(); } catch (e) { return null; } }

  /* 다크 모드 */
  var root = document.documentElement;
  var saved = safeStorage(function () { return localStorage.getItem("theme"); });
  if (saved) root.setAttribute("data-theme", saved);
  else if (window.matchMedia && matchMedia("(prefers-color-scheme: dark)").matches) root.setAttribute("data-theme", "dark");
  $("theme-toggle").addEventListener("click", function () {
    var next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    safeStorage(function () { localStorage.setItem("theme", next); });
  });

  /* 모바일 메뉴 */
  var nav = $("nav"), toggle = $("menu-toggle");
  toggle.addEventListener("click", function () {
    var open = nav.classList.toggle("open");
    toggle.setAttribute("aria-expanded", String(open));
  });
  nav.addEventListener("click", function (e) {
    if (e.target.tagName === "A") { nav.classList.remove("open"); toggle.setAttribute("aria-expanded", "false"); }
  });

  /* 현재 섹션 강조 */
  if ("IntersectionObserver" in window) {
    var links = nav.querySelectorAll("a");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (!en.isIntersecting) return;
        links.forEach(function (a) { a.classList.toggle("active", a.getAttribute("href") === "#" + en.target.id); });
      });
    }, { rootMargin: "-40% 0px -55% 0px" });
    document.querySelectorAll("main section").forEach(function (s) { io.observe(s); });
  }

  /* AI 코치 */
  var form = $("coach-form"), statusEl = $("status"), resultEl = $("result"), btn = $("submit-btn");

  function setStatus(msg, cls) { statusEl.textContent = msg; statusEl.className = "status" + (cls ? " " + cls : ""); }

  function render(data) {
    resultEl.textContent = "";
    (data.questions || []).forEach(function (q, i) {
      var box = document.createElement("div"); box.className = "q";
      var s = document.createElement("strong"); s.textContent = (i + 1) + ". " + q.question;
      var p = document.createElement("span"); p.textContent = q.why;
      box.appendChild(s); box.appendChild(p); resultEl.appendChild(box);
    });
    if (data.keywords && data.keywords.length) {
      var wrap = document.createElement("div");
      var h = document.createElement("strong"); h.textContent = "문헌 검색 키워드";
      var tags = document.createElement("div"); tags.className = "tags";
      data.keywords.forEach(function (k) { var t = document.createElement("span"); t.className = "tag"; t.textContent = k; tags.appendChild(t); });
      wrap.appendChild(h); wrap.appendChild(tags); resultEl.appendChild(wrap);
    }
    if (data.caution) { var c = document.createElement("p"); c.className = "note"; c.textContent = "주의: " + data.caution; resultEl.appendChild(c); }
    resultEl.hidden = false;
  }

  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var fieldEl = $("field"), kwEl = $("keywords");
    var payload = { field: fieldEl.value.trim(), keywords: kwEl.value.trim(), level: $("level").value };
    fieldEl.classList.toggle("invalid", !payload.field);
    kwEl.classList.toggle("invalid", !payload.keywords);
    resultEl.hidden = true;
    if (!payload.field || !payload.keywords) {
      setStatus("필수값을 입력하세요. 전공 분야와 관심 키워드가 모두 필요합니다.", "error");
      return;
    }
    btn.disabled = true;
    setStatus("AI가 연구 질문을 만드는 중입니다…", "loading");
    var slowTimer = setTimeout(function () { setStatus("응답이 평소보다 늦어지고 있습니다. 조금만 더 기다려 주세요…", "loading"); }, SLOW_MS);
    var ctrl = new AbortController();
    var abortTimer = setTimeout(function () { ctrl.abort(); }, TIMEOUT_MS);

    fetch("/api/coach", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: ctrl.signal
    }).then(function (res) {
      return res.json().catch(function () { return {}; }).then(function (body) { return { ok: res.ok, status: res.status, body: body }; });
    }).then(function (r) {
      if (!r.ok) {
        var msg = r.body && r.body.error ? r.body.error : "오류가 발생했습니다. 잠시 후 다시 시도하세요.";
        setStatus(msg, "error");
        return;
      }
      setStatus("");
      render(r.body);
    }).catch(function (err) {
      setStatus(err && err.name === "AbortError"
        ? "응답 시간이 초과되었습니다. 잠시 후 다시 시도하세요."
        : "네트워크 오류입니다. 연결을 확인하고 다시 시도하세요.", "error");
    }).then(function () {
      clearTimeout(slowTimer); clearTimeout(abortTimer); btn.disabled = false;
    });
  });
})();
