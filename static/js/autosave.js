
/**
 * UltimateNotePad - Autosave
 *
 * - 入力停止から1秒後に保存
 * - 保存リクエストの直列実行
 * - 通信エラー時の自動再試行（最大3回）
 * - 指数バックオフ（2秒 / 4秒 / 8秒）
 * - 最新の入力内容を優先
 * - 保存ステータス表示
 * - 通信復旧時の再保存
 * - 未保存状態でのページ離脱警告
 */

function initAutosave() {
    const form = document.querySelector(".note-edit-form");
    const status = document.querySelector("#save-status");

    if (!form || !status) return;

    const title = form.querySelector('[name="title"]');
    const content = form.querySelector('[name="content"]');

    if (!title || !content) return;

    const SAVE_DELAY = 1000;
    const MAX_RETRIES = 3;
    const RETRY_BASE_DELAY = 2000;

    let saveTimer = null;
    let editVersion = 0;
    let savedVersion = 0;
    let isSaving = false;

    function setStatus(state, message) {
        status.dataset.state = state;
        status.textContent = window.UNPSettings?.statusText?.(state, message) ?? message;
    }

    function delay(ms) {
        return new Promise((resolve) => {
            setTimeout(resolve, ms);
        });
    }

    function scheduleSave(wait = SAVE_DELAY) {
        clearTimeout(saveTimer);
        if (window.UNPSettings?.get?.()?.editor?.autosave === false) return;

        saveTimer = setTimeout(() => {
            void saveNote();
        }, wait);
    }

    // 最新の入力を送信。通信エラーなら最大3回再試行
    async function sendWithRetry() {
        for (
            let retryCount = 0;
            retryCount <= MAX_RETRIES;
            retryCount++
        ) {
            if (!title.value.trim()) {
                throw new Error("タイトルを入力してください");
            }

            // 再試行するたびに最新の入力を取得
            const currentVersion = editVersion;
            const formData = new FormData(form);

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    body: formData
                });

                if (!response.ok) {
                    const error = new Error(
                        `HTTP ${response.status}`
                    );

                    // 429とサーバーエラーのみ再試行
                    error.retryable =
                        response.status === 429 ||
                        response.status >= 500;

                    throw error;
                }

                const result = await response.json();

                if (result.success !== true) {
                    throw new Error(
                        result.message || "保存に失敗しました"
                    );
                }

                console.log("保存成功:", result);

                return currentVersion;

            } catch (error) {
                const retryable =
                    error.retryable === true ||
                    error instanceof TypeError;

                if (!retryable || retryCount >= MAX_RETRIES) {
                    throw error;
                }

                const waitMs =
                    RETRY_BASE_DELAY * (2 ** retryCount);

                setStatus(
                    "saving",
                    `再試行中 (${retryCount + 1}/${MAX_RETRIES})`
                );

                console.warn(
                    `保存失敗。${waitMs / 1000}秒後に再試行`,
                    error
                );

                await delay(waitMs);
            }
        }
    }

    // 保存処理は必ず1件ずつ実行
    async function saveNote() {
        if (isSaving) return;

        if (editVersion === savedVersion) {
            setStatus("saved", "保存済み");
            return;
        }

        if (!title.value.trim()) {
            setStatus("error", "タイトルを入力してください");
            return;
        }

        isSaving = true;

        try {
            while (savedVersion < editVersion) {
                setStatus("saving", "保存中...");

                const completedVersion =
                    await sendWithRetry();

                savedVersion = Math.max(
                    savedVersion,
                    completedVersion
                );
            }

            setStatus("saved", "保存済み");

        } catch (error) {
            console.error("自動保存失敗:", error);

            setStatus("error", "保存失敗");

        } finally {
            isSaving = false;
        }
    }

    // 入力変更を監視
    for (const field of [title, content]) {
        field.addEventListener("input", () => {
            editVersion++;

            setStatus("dirty", "未保存の変更");

            scheduleSave();
        });
    }

    // 手動保存も同じ保存キューを使用
    form.addEventListener("submit", (event) => {
        event.preventDefault();

        clearTimeout(saveTimer);

        void saveNote();
    });

    // 通信が復旧したら未保存の変更を再送
    window.addEventListener("online", () => {
        if (savedVersion < editVersion) {
            setStatus("dirty", "再接続しました");

            scheduleSave(0);
        }
    });

    // UNP_SETTINGS_AUTOSAVE_HOOK: user setting and language changes.
    window.addEventListener("unp:preferenceschange", () => {
        clearTimeout(saveTimer);
        setStatus(status.dataset.state || "saved", status.textContent);
        if (window.UNPSettings?.get?.()?.editor?.autosave !== false &&
            savedVersion < editVersion) {
            scheduleSave(0);
        }
    });

    // 未保存の変更があれば離脱前に警告
    window.addEventListener("beforeunload", (event) => {
        if (savedVersion < editVersion) {
            event.preventDefault();
            event.returnValue = "";
        }
    });

    console.log(
        "UltimateNotePad: Autosave initialized"
    );
}

// DOM読み込み完了後に初期化
if (document.readyState === "loading") {
    document.addEventListener(
        "DOMContentLoaded",
        initAutosave
    );
} else {
    initAutosave();
}
