"use strict";
(() => {
  const key = "testingstudio_theme";
  const allowed = ["system", "light", "dark"];
  const media = window.matchMedia("(prefers-color-scheme: dark)");
  let preference = "system";
  try {
    const saved = localStorage.getItem(key);
    if (allowed.includes(saved)) preference = saved;
  } catch { /* O tema automático também funciona sem armazenamento. */ }

  function apply() {
    const resolved = preference === "system" ? (media.matches ? "dark" : "light") : preference;
    document.documentElement.dataset.theme = resolved;
    document.documentElement.dataset.themePreference = preference;
    const meta = document.querySelector('meta[name="theme-color"]');
    if (meta) meta.content = resolved === "dark" ? "#07090d" : "#f7f9fc";
    const select = document.getElementById("theme-preference");
    if (select) select.value = preference;
  }
  apply();
  media.addEventListener("change", () => { if (preference === "system") apply(); });
  window.addEventListener("storage", event => {
    if (event.key !== key) return;
    preference = allowed.includes(event.newValue) ? event.newValue : "system";
    apply();
  });
  document.addEventListener("DOMContentLoaded", () => {
    const select = document.getElementById("theme-preference");
    select.value = preference;
    select.addEventListener("change", () => {
      preference = allowed.includes(select.value) ? select.value : "system";
      try { localStorage.setItem(key, preference); } catch { /* Mantém a escolha nesta aba. */ }
      apply();
    });
  });
})();
