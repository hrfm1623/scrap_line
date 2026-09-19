"use strict";
const cards = [...document.querySelectorAll(".story")];
const buttons = [...document.querySelectorAll("[data-filter]")];
const search = document.querySelector("#search");
const normalize = value => value.normalize("NFKC").toLocaleLowerCase("ja").trim();
let category = "all";
function filter() {
  const query = normalize(search.value);
  let count = 0;
  cards.forEach(card => {
    const matches = (category === "all" || card.dataset.category === category)
      && normalize(card.textContent).includes(query);
    card.hidden = !matches;
    if (matches) count += 1;
  });
  buttons.forEach(button => button.setAttribute("aria-pressed", String(button.dataset.filter === category)));
  document.querySelector(".result-count").textContent = `${count}件の話題`;
  document.querySelector("#no-results").hidden = count > 0 || cards.length === 0;
}
if (cards.length) document.querySelector(".filters").hidden = false;
buttons.forEach(button => button.addEventListener("click", () => { category = button.dataset.filter; filter(); }));
search.addEventListener("input", filter);
document.querySelector("form").addEventListener("submit", event => { event.preventDefault(); filter(); });
document.querySelector("#reset").addEventListener("click", () => {
  category = "all"; search.value = ""; filter(); search.focus();
});
