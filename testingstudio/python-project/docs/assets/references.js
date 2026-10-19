"use strict";
(() => {
  const catalog = window.TESTING_STUDIO.references;
  const node = (tag, text, className) => {
    const element = document.createElement(tag);
    if (text !== undefined) element.textContent = text;
    if (className) element.className = className;
    return element;
  };
  document.getElementById("references-date").textContent = "Revisão bibliográfica: " + catalog.review_date;
  document.getElementById("references-note").textContent = catalog.note;
  const map = document.getElementById("references-map");
  for (const [module, ids] of Object.entries(catalog.modules)) {
    const row = node("div", undefined, "reference-map-row");
    row.append(node("strong", module), node("span", ids.join(" · ")));
    map.append(row);
  }
  const target = document.getElementById("references-catalog");
  for (const group of catalog.groups) {
    const section = node("section", undefined, "reference-group");
    section.append(node("h2", group));
    const grid = node("div", undefined, "reference-grid");
    for (const source of catalog.sources.filter(source => source.group === group)) {
      const card = node("article", undefined, "reference-card");
      card.id = "reference-" + source.id;
      card.append(node("span", source.id, "reference-id"), node("h3", source.title),
        node("p", source.citation, "reference-citation"), node("p", source.scope),
        node("p", source.location, "microcopy"));
      if (source.url) {
        const link = node("a", "Consultar fonte ↗", "reference-link");
        link.href = source.url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.setAttribute("aria-label", "Consultar fonte: " + source.title);
        card.append(link, node("p", "Acesso em: " + catalog.review_date, "microcopy"));
      }
      grid.append(card);
    }
    section.append(grid);
    target.append(section);
  }
  document.getElementById("download-references").addEventListener("click", () => {
    const url = URL.createObjectURL(new Blob([catalog.markdown], {type: "text/markdown;charset=utf-8"}));
    const link = node("a");
    link.href = url;
    link.download = "TestingStudio_Referencias.md";
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  });
})();
