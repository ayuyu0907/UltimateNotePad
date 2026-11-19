
function initDeleteModal() {
    const dialog = document.querySelector("#delete-note-dialog");
    const openButton = document.querySelector("#delete-note-open");
    const cancelButton = document.querySelector("#delete-note-cancel");

    if (!dialog || !openButton) return;

    openButton.addEventListener("click", () => {
        dialog.showModal();
    });

    cancelButton?.addEventListener("click", () => {
        dialog.close();
    });

    dialog.addEventListener("click", (event) => {
        if (event.target === dialog) {
            dialog.close();
        }
    });

    dialog.addEventListener("close", () => {
        openButton.focus();
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDeleteModal);
} else {
    initDeleteModal();
}
