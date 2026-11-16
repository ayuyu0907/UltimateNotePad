/* UltimateNotePad: 新規メモ作成モーダル（開閉アニメーション対応） */
(() => {
  "use strict";

  function initCreateModal() {
    const dialog = document.querySelector("#create-note-dialog");
    const openButton = document.querySelector("#create-note-open");
    const welcomeButton = document.querySelector("#welcome-create-note");
    const closeButton = document.querySelector("#create-note-close");
    const cancelButton = document.querySelector("#create-note-cancel");
    const titleInput = document.querySelector("#create-title");
    const form = dialog?.querySelector("form");

    if (!dialog || !openButton || !form || !titleInput) return;

    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let closeTimer = null;

    function openDialog() {
      if (dialog.open) return;
      form.reset();
      delete dialog.dataset.closing;
      dialog.showModal();
      titleInput.focus();
    }

    function closeDialog() {
      if (!dialog.open || dialog.dataset.closing) return;

      if (reduceMotion.matches) {
        dialog.close();
        return;
      }

      // 即時close()だとCSS非対応のブラウザで退出演出が途中で消えるため
      // 短いフェード中だけtop layerに残す。
      dialog.dataset.closing = "";
      closeTimer = window.setTimeout(() => {
        dialog.close();
        closeTimer = null;
      }, 200);
    }

    openButton.addEventListener("click", openDialog);
    welcomeButton?.addEventListener("click", openDialog);
    closeButton?.addEventListener("click", closeDialog);
    cancelButton?.addEventListener("click", closeDialog);

    // ダイアログの外側（backdrop）クリックで閉じる。
    dialog.addEventListener("click", (event) => {
      if (event.target !== dialog) return;
      const rect = dialog.getBoundingClientRect();
      if (
        event.clientX < rect.left || event.clientX > rect.right ||
        event.clientY < rect.top || event.clientY > rect.bottom
      ) closeDialog();
    });

    // OS標準のEsc操作を保持しつつ、閉じるアニメーションを適用。
    dialog.addEventListener("cancel", (event) => {
      event.preventDefault();
      closeDialog();
    });

    dialog.addEventListener("close", () => {
      if (closeTimer !== null) {
        window.clearTimeout(closeTimer);
        closeTimer = null;
      }
      delete dialog.dataset.closing;
      openButton.focus();
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initCreateModal, { once: true });
  } else {
    initCreateModal();
  }
})();
