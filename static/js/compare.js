document.addEventListener("DOMContentLoaded", () => {
  const tierFilter = document.getElementById("tier-filter");
  const cards = document.querySelectorAll("[data-tier]");

  if (tierFilter && cards.length > 0) {
    tierFilter.addEventListener("change", (e) => {
      const selected = e.target.value;
      cards.forEach((card) => {
        const cardTier = card.getAttribute("data-tier");
        if (selected === "all" || cardTier === selected) {
          card.classList.remove("d-none");
        } else {
          card.classList.add("d-none");
        }
      });
    });
  }
});