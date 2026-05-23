frappe.provide("kentender_budget.budget_summary_panel");

(function () {
	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function editabilityLabel(status) {
		const st = String(status || "").trim();
		if (st === "Approved" || st === "Submitted") return __("Locked");
		return __("Editable");
	}

	kentender_budget.budget_summary_panel = {
		mount(hostEl, ctx) {
			if (!hostEl || !ctx || !ctx.selected) return;
			const selected = ctx.selected;
			const payload = ctx.reviewPayload || {};
			const totals = payload.totals || {};
			const cur = selected.currency || "";
			const programs =
				totals.programs_funded != null
					? totals.programs_funded
					: selected.budget_lines_allocated != null
						? selected.budget_lines_allocated
						: 0;
			const st = String(selected.status || "Draft").trim();

			hostEl.innerHTML =
				'<div class="kt-budget-section kt-surface" data-testid="budget-summary-panel">' +
				"<h6>" +
				esc(__("Summary")) +
				"</h6>" +
				'<div class="mb-2" data-testid="budget-summary-identity">' +
				'<div class="font-weight-bold">' +
				esc(selected.budget_name || selected.name) +
				"</div>" +
				'<div class="text-muted small">' +
				esc(selected.fiscal_year || "—") +
				" · " +
				esc(selected.strategic_plan_title || selected.strategic_plan || "—") +
				" · " +
				esc(cur || "—") +
				"</div>" +
				'<div class="small mt-1">' +
				esc(st) +
				" · " +
				esc(editabilityLabel(st)) +
				"</div></div>" +
				'<h6 class="small text-muted text-uppercase mt-3 mb-2">' +
				esc(__("Financial summary")) +
				"</h6>" +
				'<dl class="row mb-0 kt-budget-dl">' +
				'<dt class="col-sm-4">' +
				esc(__("Total")) +
				'</dt><dd class="col-sm-8 kt-budget-money">' +
				esc(
					ctx.formatMoney(
						totals.total_budget_amount != null
							? totals.total_budget_amount
							: selected.total_budget_amount,
						cur,
					),
				) +
				"</dd>" +
				'<dt class="col-sm-4">' +
				esc(__("Allocated")) +
				'</dt><dd class="col-sm-8 kt-budget-money">' +
				esc(
					ctx.formatMoney(
						totals.allocated_sum != null ? totals.allocated_sum : selected.allocated_amount,
						cur,
					),
				) +
				"</dd>" +
				'<dt class="col-sm-4">' +
				esc(__("Remaining")) +
				'</dt><dd class="col-sm-8 kt-budget-money">' +
				esc(
					ctx.formatMoney(
						totals.remaining_amount != null
							? totals.remaining_amount
							: selected.remaining_amount,
						cur,
					),
				) +
				"</dd>" +
				'<dt class="col-sm-4">' +
				esc(__("Programs funded")) +
				'</dt><dd class="col-sm-8">' +
				esc(String(programs || 0)) +
				"</dd>" +
				"</dl>" +
				'<div class="mt-3 pt-2 border-top" data-testid="budget-summary-next-step">' +
				'<h6 class="small text-muted text-uppercase mb-1">' +
				esc(__("Next step")) +
				"</h6>" +
				'<p class="small mb-0">' +
				esc(ctx.nextStepLabel(st)) +
				"</p></div>" +
				'<div class="kt-budget-summary-actions mt-3 pt-2">' +
				(ctx.canEditBudget
					? '<button type="button" class="btn btn-default btn-sm kt-context-action" data-testid="selected-budget-edit">' +
						esc(__("Edit Budget Info")) +
						"</button>"
					: "") +
				"</div>" +
				"</div>";
		},
	};
})();
