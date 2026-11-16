/*
 * UTCで保存された旧形式の日時（YYYY-MM-DD HH:mm:ss）を日本時間へ表示変換。
 * サーバーOSや閲覧者のタイムゾーンに依存しません。
 * データベース自体の日時は変更しません。
 */
(() => {
  "use strict";

  const formatter = new Intl.DateTimeFormat("ja-JP", {
    timeZone: "Asia/Tokyo",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  });

  function parseUTC(value) {
    if (!value) return null;

    // DBの従来形式または ISO 8601 UTC を受け付ける。
    const match = String(value).trim().match(
      /^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})(?::(\d{2}))?(?:Z)?$/
    );
    if (!match) return null;

    const [, year, month, day, hour, minute, second = "00"] = match;
    const date = new Date(`${year}-${month}-${day}T${hour}:${minute}:${second}Z`);

    // 無効な日時を自動繰り上がりで誤表示しない。
    if (!Number.isFinite(date.getTime())) return null;
    if (
      date.getUTCFullYear() !== Number(year) ||
      date.getUTCMonth() + 1 !== Number(month) ||
      date.getUTCDate() !== Number(day) ||
      date.getUTCHours() !== Number(hour) ||
      date.getUTCMinutes() !== Number(minute) ||
      date.getUTCSeconds() !== Number(second)
    ) return null;

    return date;
  }

  function formatJST(date) {
    const parts = Object.fromEntries(
      formatter.formatToParts(date)
        .filter((part) => part.type !== "literal")
        .map((part) => [part.type, part.value])
    );
    return `${parts.year}/${parts.month}/${parts.day} ${parts.hour}:${parts.minute}`;
  }

  function updateTimes() {
    for (const element of document.querySelectorAll("[data-utc]")) {
      const date = parseUTC(element.dataset.utc);
      if (!date) continue;

      const display = formatJST(date);
      element.textContent = element.classList.contains("last-updated")
        ? `最終更新：${display}` : display;
      if (element.tagName === "TIME") element.dateTime = date.toISOString();
      element.title = `${display} (JST)`;
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", updateTimes, { once: true });
  } else {
    updateTimes();
  }
})();
