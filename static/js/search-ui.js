document.addEventListener("DOMContentLoaded", () => {
  const sortSelect = document.querySelector("#note-sort");
  const searchForm = document.querySelector("#note-search-form");

  if (!sortSelect || !searchForm) return;

  sortSelect.addEventListener("change", () => {
    searchForm.requestSubmit();
  });
});