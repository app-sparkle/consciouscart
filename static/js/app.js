document.addEventListener("click", (event) => {
  const btn = event.target.closest(".js-select-alt");
  if (!btn) return;
  openNeedVerification(Number(btn.dataset.productId), btn.dataset.productName);
});