/* The site is fully readable without JS. These are optional enhancements. */
(() => {
  "use strict";
  // No bulk prefetch: only cache images the reader actually requests.
  if ("serviceWorker" in navigator && window.isSecureContext) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js", {updateViaCache: "none"}).catch(() => {});
    }, {once: true});
  }
  const search = document.querySelector("#publication-search");
  const year = document.querySelector("#publication-year");
  if (search && year) {
    const papers = [...document.querySelectorAll(".publication")];
    const groups = [...document.querySelectorAll(".publication-year")];
    const count = document.querySelector("#publication-count");
    const empty = document.querySelector(".no-results");
    const filter = () => {
      const words = search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
      let visible = 0;
      for (const paper of papers) {
        const match = (year.value === "all" || year.value === paper.dataset.year)
          && words.every(word => paper.dataset.search.includes(word));
        paper.hidden = !match;
        if (match) visible++;
      }
      for (const group of groups) {
        group.hidden = ![...group.querySelectorAll(".publication")].some(paper => !paper.hidden);
      }
      count.textContent = `${visible} publication${visible === 1 ? "" : "s"}`;
      empty.hidden = visible > 0;
    };
    document.querySelector("[data-search-tools]").hidden = false;
    search.addEventListener("input", filter);
    year.addEventListener("change", filter);
  }
  if (navigator.clipboard && window.isSecureContext) {
    for (const button of document.querySelectorAll(".copy-bibtex")) {
      button.hidden = false;
      button.addEventListener("click", async () => {
        try {
          await navigator.clipboard.writeText(button.parentElement.querySelector("pre").textContent);
          button.textContent = "Copied!";
        } catch {
          button.textContent = "Select and copy the text above";
        }
        setTimeout(() => { button.textContent = "Copy BibTeX"; }, 2500);
      });
    }
  }
})();
