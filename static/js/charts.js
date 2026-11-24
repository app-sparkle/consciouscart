window.ConsciousCharts = {
  formatINR(amount) {
    const num = Number(amount || 0);
    return `₹${num.toFixed(2)}`;
  },

  renderBudgetBreakdown(containerId, subtotal, reserve, total) {
    const el = document.getElementById(containerId);
    if (!el) return;

    const subVal = Number(subtotal || 0);
    const resVal = Number(reserve || subVal * 0.2);
    const totVal = Number(total || subVal + resVal);
    const safeTotal = totVal > 0 ? totVal : 1;

    const subPct = Math.min(100, Math.round((subVal / safeTotal) * 100));
    const resPct = Math.max(0, 100 - subPct);

    el.innerHTML = `
      <div class="progress mb-2" style="height: 12px;">
        <div class="progress-bar bg-success" role="progressbar" style="width: ${subPct}%" title="Subtotal"></div>
        <div class="progress-bar bg-warning" role="progressbar" style="width: ${resPct}%" title="20% Safety Reserve"></div>
      </div>
      <div class="d-flex justify-content-between small text-muted">
        <span>Subtotal: ${this.formatINR(subVal)} (${subPct}%)</span>
        <span>20% Reserve: ${this.formatINR(resVal)} (${resPct}%)</span>
      </div>
    `;
  }
};