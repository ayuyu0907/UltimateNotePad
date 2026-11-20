/**
 * UltimateNotePad UI controller
 * Search, dialogs, and date display share a single DOM-ready entry point.
 * Autosave remains a separate module because it owns its retry/queue lifecycle.
 */
(() => {
  "use strict";

  const select = (selector, scope = document) => scope.querySelector(selector);
  const selectAll = (selector, scope = document) => scope.querySelectorAll(selector);

  // Keep the modal's animation and focus behavior in one place.
  function bindDialog({ id, openers, closers, initialFocus, resetOnOpen = false, animateClose = false }) {
    const dialog = select(id);
    if (!dialog) return;

    const form = select("form", dialog);
    const openButtons = openers.map((id) => select(id)).filter(Boolean);
    const closeButtons = closers.map((id) => select(id)).filter(Boolean);
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)");
    let closeTimer = null;
    let lastOpener = null;

    function openDialog(opener) {
      if (dialog.open) return;
      if (closeTimer !== null) {
        window.clearTimeout(closeTimer);
        closeTimer = null;
      }
      delete dialog.dataset.closing;
      if (resetOnOpen) form?.reset();
      lastOpener = opener;
      dialog.showModal();
      select(initialFocus, dialog)?.focus();
    }

    function closeDialog() {
      if (!dialog.open || Object.hasOwn(dialog.dataset, "closing")) return;
      if (!animateClose || reduceMotion?.matches) {
        dialog.close();
        return;
      }
      dialog.dataset.closing = "";
      closeTimer = window.setTimeout(() => {
        closeTimer = null;
        if (dialog.open) dialog.close();
      }, 200);
    }

    openButtons.forEach((button) => {
      button.addEventListener("click", () => openDialog(button));
    });
    closeButtons.forEach((button) => {
      button.addEventListener("click", closeDialog);
    });

    // Only a click outside the dialog's visible rectangle closes it.
    dialog.addEventListener("click", (event) => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      const outside = event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom;
      if (outside) closeDialog();
    });

    if (animateClose) {
      dialog.addEventListener("cancel", (event) => {
        event.preventDefault();
        closeDialog();
      });
    }
    dialog.addEventListener("close", () => {
      if (closeTimer !== null) {
        window.clearTimeout(closeTimer);
        closeTimer = null;
      }
      delete dialog.dataset.closing;
      lastOpener?.focus();
    });
  }

  function initDialogs() {
    bindDialog({
      id: "#create-note-dialog",
      openers: ["#create-note-open", "#welcome-create-note"],
      closers: ["#create-note-close", "#create-note-cancel"],
      initialFocus: "#create-title",
      resetOnOpen: true,
      animateClose: true
    });
    bindDialog({
      id: "#delete-note-dialog",
      openers: ["#delete-note-open"],
      closers: ["#delete-note-cancel"],
      initialFocus: "#delete-note-cancel"
    });
  }

  function initSearch() {
    const form = select("#note-search-form");
    const sort = select("#note-sort");
    if (!form || !sort) return;
    sort.addEventListener("change", () => form.requestSubmit());
  }

  // Existing DB values are interpreted as UTC, and displayed in Tokyo time.
  const jstFormatter = new Intl.DateTimeFormat("ja-JP", {
    timeZone: "Asia/Tokyo",
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit", hourCycle: "h23"
  });

  function parseUTC(value) {
    if (!value) return null;
    const match = String(value).trim().match(
      /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?(?:Z)?$/
    );
    if (!match) return null;
    const [, year, month, day, hour, minute, second = "00"] = match;
    const date = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}Z`);
    if (!Number.isFinite(date.getTime())) return null;
    if (date.getUTCFullYear() !== Number(year) ||
        date.getUTCMonth() + 1 !== Number(month) ||
        date.getUTCDate() !== Number(day) ||
        date.getUTCHours() !== Number(hour) ||
        date.getUTCMinutes() !== Number(minute) ||
        date.getUTCSeconds() !== Number(second)) return null;
    return date;
  }

  function formatJST(date) {
    const parts = Object.fromEntries(jstFormatter.formatToParts(date)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value]));
    return `${parts.year}/${parts.month}/${parts.day} ${parts.hour}:${parts.minute}`;
  }

  function initDates() {
    for (const element of selectAll("[data-utc]")) {
      const date = parseUTC(element.dataset.utc);
      if (!date) continue;
      const display = formatJST(date);
      element.textContent = element.classList.contains("last-updated")
        ? `最終更新：${display}` : display;
      if (element.tagName === "TIME") element.dateTime = date.toISOString();
      element.title = `${display} (JST)`;
    }
  }

  function init() {
    initDialogs();
    initSearch();
    initDates();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
  } else {
    init();
  }
})();
