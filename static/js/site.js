/* Blue Route Logistics: site behaviour (no dependencies). */
(function () {
  "use strict";
  var doc = document.documentElement;
  doc.classList.add("js");
  var reduceMotion = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  /* ------------------------------------------------------------ header + mobile nav */
  var header = document.querySelector("[data-header]");
  var toggle = document.querySelector("[data-nav-toggle]");
  var menu = document.querySelector("[data-nav-menu]");

  function onScroll() { if (header) header.classList.toggle("is-scrolled", window.scrollY > 8); }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  function setMenu(open, returnFocus) {
    if (!toggle || !menu) return;
    toggle.setAttribute("aria-expanded", String(open));
    menu.classList.toggle("is-open", open);
    document.body.classList.toggle("nav-open", open);
    if (open) {
      var first = menu.querySelector("a");
      if (first) first.focus();
    } else if (returnFocus) {
      toggle.focus();
    }
  }
  if (toggle && menu) {
    toggle.addEventListener("click", function () {
      setMenu(toggle.getAttribute("aria-expanded") !== "true");
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") setMenu(false, true);
    });
    menu.addEventListener("click", function (e) { if (e.target.closest("a")) setMenu(false); });
    window.addEventListener("resize", function () {
      if (window.innerWidth > 1060 && toggle.getAttribute("aria-expanded") === "true") setMenu(false);
    });
  }

  /* ------------------------------------------------------------ "how it works" route line */
  var steps = document.querySelector(".steps");
  if (steps && !reduceMotion && "IntersectionObserver" in window) {
    steps.setAttribute("data-draw", "");
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (en) {
        if (en.isIntersecting) { steps.classList.add("is-drawn"); io.disconnect(); }
      });
    }, { threshold: 0.35 });
    io.observe(steps);
  }

  /* ------------------------------------------------------------ service-area map highlight */
  function highlightArea() {
    var id = decodeURIComponent(location.hash.slice(1));
    document.querySelectorAll(".area").forEach(function (a) { a.classList.toggle("is-target", a.id === id); });
    document.querySelectorAll(".map-node").forEach(function (n) {
      n.classList.toggle("is-active", (n.getAttribute("href") || "").split("#")[1] === id);
    });
  }
  window.addEventListener("hashchange", highlightArea);
  highlightArea();

  /* ------------------------------------------------------------ forms (Netlify Forms) */
  var MSG = {
    required: "Enter {label}.",
    select: "Choose {label}.",
    email: "Enter a valid email address, like name@yourpharmacy.com.",
    phone: "Enter a phone number with area code, like (772) 555-0100.",
    number: "Enter a number of 0 or more.",
    date: "Choose a start date that is today or later.",
    check: "Confirm that this request contains no patient information."
  };

  function labelText(field) {
    var l = field.form.querySelector('label[for="' + field.id + '"]');
    var txt = field.getAttribute("data-label") || (l ? l.textContent.replace("*", "").trim() : field.name);
    return txt.charAt(0).toLowerCase() + txt.slice(1);
  }

  function validateField(field) {
    var v = (field.value || "").trim();
    var msg = "";
    if (field.type === "checkbox") {
      if (field.required && !field.checked) msg = MSG.check;
    } else if (field.required && !v) {
      msg = (field.tagName === "SELECT" ? MSG.select : MSG.required).replace("{label}", labelText(field));
    } else if (v && field.type === "email" && !/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(v)) {
      msg = MSG.email;
    } else if (v && field.type === "tel" && v.replace(/\D/g, "").length < 10) {
      msg = MSG.phone;
    } else if (v && field.type === "number" && (isNaN(Number(v)) || Number(v) < 0)) {
      msg = MSG.number;
    } else if (v && field.type === "date") {
      var today = new Date(); today.setHours(0, 0, 0, 0);
      var d = new Date(v + "T00:00:00");
      if (isNaN(d.getTime()) || d < today) msg = MSG.date;
    } else if (v && field.maxLength > 0 && v.length > field.maxLength) {
      msg = "Keep this under " + field.maxLength + " characters.";
    }
    var err = document.getElementById(field.id + "-error");
    if (msg) {
      field.setAttribute("aria-invalid", "true");
      if (err) { err.textContent = msg; err.classList.add("is-visible"); }
    } else {
      field.removeAttribute("aria-invalid");
      if (err) { err.textContent = ""; err.classList.remove("is-visible"); }
    }
    return msg;
  }

  function hash(str) {
    var h = 5381;
    for (var i = 0; i < str.length; i++) h = ((h << 5) + h + str.charCodeAt(i)) | 0;
    return String(h >>> 0);
  }

  function store(key, val) { try { if (val === undefined) return sessionStorage.getItem(key); sessionStorage.setItem(key, val); } catch (e) { return null; } }

  document.querySelectorAll("form[data-form]").forEach(function (form) {
    form.setAttribute("novalidate", "");
    var status = form.querySelector("[data-form-status]");
    var button = form.querySelector('button[type="submit"]');
    var success = document.getElementById(form.getAttribute("data-success"));
    var fields = Array.prototype.slice.call(form.querySelectorAll("input, select, textarea"))
      .filter(function (f) { return f.type !== "hidden" && !f.closest(".hp-field"); });
    var busy = false;

    // Prefill from links like /request-a-quote/?service=pharmacy&area=stuart
    var params = new URLSearchParams(location.search);
    [["service", "service"], ["area", "delivery_area"]].forEach(function (pair) {
      var key = params.get(pair[0]), sel = form.querySelector('select[name="' + pair[1] + '"]');
      if (!key || !sel) return;
      var opt = sel.querySelector('option[data-key="' + key.replace(/[^a-z-]/g, "") + '"]');
      if (opt) sel.value = opt.value;
    });

    var dateField = form.querySelector('input[type="date"]');
    if (dateField) {
      var t = new Date();
      dateField.min = t.getFullYear() + "-" + String(t.getMonth() + 1).padStart(2, "0") + "-" + String(t.getDate()).padStart(2, "0");
    }

    fields.forEach(function (f) {
      f.addEventListener("blur", function () { if (f.value || f.getAttribute("aria-invalid")) validateField(f); });
      f.addEventListener("input", function () { if (f.getAttribute("aria-invalid")) validateField(f); });
      f.addEventListener("change", function () { if (f.getAttribute("aria-invalid")) validateField(f); });
    });

    function showStatus(html) {
      status.innerHTML = html;
      status.classList.add("is-visible");
      status.focus();
    }

    function setBusy(on) {
      busy = on;
      form.classList.toggle("is-submitting", on);
      button.disabled = on;
      button.querySelector("[data-label]").textContent = on ? "Sending…" : button.getAttribute("data-idle");
    }

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (busy) return;
      status.classList.remove("is-visible");

      var errors = [];
      fields.forEach(function (f) {
        var m = validateField(f);
        if (m) errors.push('<li><a href="#' + f.id + '">' + m + "</a></li>");
      });
      if (errors.length) {
        showStatus("<strong>Please fix " + (errors.length === 1 ? "1 field" : errors.length + " fields") +
          " before sending:</strong><ul>" + errors.join("") + "</ul>");
        return;
      }

      var data = new FormData(form);
      var fingerprint = hash(form.getAttribute("name") + "|" + Array.from(data.entries())
        .filter(function (p) { return p[0] !== "bot-field"; }).map(function (p) { return p[1]; }).join("|"));
      if (store("br-sent-" + fingerprint)) {
        showStatus("<strong>We already received this exact request.</strong> There's no need to send it again. " +
          "If something has changed, edit the form before sending.");
        return;
      }

      setBusy(true);
      var controller = "AbortController" in window ? new AbortController() : null;
      var timer = setTimeout(function () { if (controller) controller.abort(); }, 20000);

      fetch("/", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded", "Accept": "text/html" },
        body: new URLSearchParams(data).toString(),
        signal: controller ? controller.signal : undefined
      }).then(function (res) {
        clearTimeout(timer);
        if (!res.ok) throw new Error("HTTP " + res.status);
        store("br-sent-" + fingerprint, String(Date.now()));
        form.reset();
        if (success) {
          form.hidden = true;
          success.hidden = false;
          success.setAttribute("tabindex", "-1");
          success.focus();
          success.scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
        }
        if (window.plausible) window.plausible(form.getAttribute("name") + " submitted");
      }).catch(function () {
        clearTimeout(timer);
        showStatus("<strong>Your request was not sent.</strong> Check your connection and try again. " +
          "If it still doesn't go through, please " + (form.getAttribute("data-fallback") || "try again later") + ".");
      }).then(function () { setBusy(false); });
    });
  });
})();
