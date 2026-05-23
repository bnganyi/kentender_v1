frappe.provide("kentender_budget.budget_allocations_panel");

(function () {
	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function testIdPart(value) {
		if (value == null || value === "") return "unknown";
		return String(value).replace(/[^a-zA-Z0-9 _-]/g, "_");
	}

	function formatAmount(value) {
		const n = Number(value || 0);
		return n.toLocaleString("en-US", {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2,
		});
	}

	function lineStatusLabel(line) {
		if (!Number(line.is_active || 0)) return __("Inactive");
		if (Number(line.amount_allocated || 0) === 0) return __("Unallocated");
		return __("Active");
	}

	function programLabel(line) {
		if (
			kentender_budget.budget_allocation_drawer &&
			typeof kentender_budget.budget_allocation_drawer.hierarchyLabel === "function"
		) {
			return kentender_budget.budget_allocation_drawer.hierarchyLabel(line);
		}
		const sub = line.sub_program_label || line.sub_program;
		const prog = line.program_label || line.program || line.budget_line_name;
		if (sub && sub !== prog) return prog + " / " + sub;
		return prog || line.budget_line_name || "—";
	}

	function truncateNotes(notes, maxLen) {
		const raw = String(notes || "").trim();
		if (!raw) return "—";
		const split =
			kentender_budget.budget_allocation_drawer &&
			kentender_budget.budget_allocation_drawer.splitNotesForDisplay
				? kentender_budget.budget_allocation_drawer.splitNotesForDisplay(raw)
				: { description: raw };
		const text = split.description || raw;
		if (text.length <= maxLen) return text;
		return text.slice(0, maxLen - 1) + "…";
	}

	let boundHost = null;
	const lineCacheByBudget = Object.create(null);

	function openLineDrawer(line, readOnly) {
		const budgetName = boundHost.getAttribute("data-budget-name");
		if (!line || !budgetName || !kentender_budget.budget_allocation_drawer) return;
		kentender_budget.budget_allocation_drawer.openEdit(line, budgetName, readOnly, function () {
			document.dispatchEvent(new CustomEvent("kt-budget-panel-changed"));
		});
	}

	function handlePanelClick(ev) {
		if (!boundHost || !boundHost.contains(ev.target)) return;
		const addBtn = ev.target.closest("[data-testid='budget-allocation-add']");
		if (addBtn) {
			const budgetName = boundHost.getAttribute("data-budget-name");
			const strategicPlan = boundHost.getAttribute("data-strategic-plan");
			if (budgetName && kentender_budget.budget_allocation_drawer) {
				kentender_budget.budget_allocation_drawer.openCreate(budgetName, strategicPlan, function () {
					document.dispatchEvent(new CustomEvent("kt-budget-panel-changed"));
				});
			}
			return;
		}
		const editBtn = ev.target.closest("[data-edit-allocation]");
		if (!editBtn) return;
		const lineName = editBtn.getAttribute("data-edit-allocation");
		const budgetName = boundHost.getAttribute("data-budget-name");
		const readOnly = boundHost.getAttribute("data-read-only") === "1";
		const lines = lineCacheByBudget[budgetName] || [];
		const line = lines.find(function (item) {
			return item.name === lineName;
		});
		if (line) openLineDrawer(line, readOnly);
	}

	if (!window.__ktBudgetAllocationsPanelBound) {
		window.__ktBudgetAllocationsPanelBound = true;
		document.addEventListener("click", handlePanelClick);
	}

	kentender_budget.budget_allocations_panel = {
		mount(hostEl, ctx) {
			if (!hostEl || !ctx || !ctx.selected) return;
			const payload = ctx.reviewPayload || {};
			const lines = payload.budget_lines || [];
			const selected = ctx.selected;
			const cur = selected.currency || "KES";
			const totals = payload.totals || {};
			const locked = ctx.isBudgetReadOnly ? ctx.isBudgetReadOnly(selected.status) : !ctx.canEditBudget;

			hostEl.setAttribute("data-budget-name", selected.name || "");
			hostEl.setAttribute("data-strategic-plan", selected.strategic_plan || "");
			hostEl.setAttribute("data-read-only", locked ? "1" : "0");
			boundHost = hostEl;
			lineCacheByBudget[selected.name] = lines;

			let banner = "";
			if (locked) {
				const st = String(selected.status || "").trim();
				const msg =
					st === "Approved"
						? __("This budget is approved and locked. Allocations are read-only.")
						: __("This budget is submitted and awaiting approval. Allocations are read-only.");
				banner =
					'<div class="alert alert-info py-2 mb-2" data-testid="budget-allocations-readonly-banner">' +
					esc(msg) +
					"</div>";
			}

			const addBtn = !locked && ctx.canEditBudget
				? '<button type="button" class="btn btn-primary btn-sm" data-testid="budget-allocation-add">' +
					esc(__("Add Allocation")) +
					"</button>"
				: "";

			const actionHeader = esc(__("Actions"));

			let tableBody = "";
			if (!lines.length) {
				tableBody =
					'<tr><td colspan="6" class="text-muted" data-testid="budget-allocations-empty">' +
					esc(__("No allocations yet.")) +
					"</td></tr>";
			} else {
				for (let i = 0; i < lines.length; i++) {
					const line = lines[i];
					const rowLabel = line.budget_line_name || line.name;
					const idPart = testIdPart(rowLabel);
					const actionLabel = locked ? __("View") : __("Edit");
					const actionTestId = locked
						? "budget-allocation-view-" + idPart
						: "budget-allocation-edit-" + idPart;
					tableBody +=
						'<tr class="kt-budget-allocation-row" data-budget-line="' +
						esc(line.name) +
						'" data-testid="budget-allocation-row-' +
						esc(idPart) +
						'">' +
						'<td class="kt-budget-allocation-program">' +
						esc(programLabel(line)) +
						"</td>" +
						'<td class="text-right" data-testid="budget-allocation-amount-' +
						esc(idPart) +
						'">' +
						esc(cur + " " + formatAmount(line.amount_allocated)) +
						"</td>" +
						"<td>" +
						esc(line.funding_source_label || line.funding_source || "—") +
						"</td>" +
						"<td>" +
						esc(lineStatusLabel(line)) +
						"</td>" +
						'<td class="text-muted small">' +
						esc(truncateNotes(line.notes, 80)) +
						"</td>" +
						'<td class="text-right">' +
						'<button type="button" class="btn btn-xs btn-link kt-row-action" data-edit-allocation="' +
						esc(line.name) +
						'" data-testid="' +
						esc(actionTestId) +
						'">' +
						esc(actionLabel) +
						"</button></td></tr>";
				}
			}

			const allocatedSum =
				totals.allocated_sum != null ? totals.allocated_sum : selected.allocated_amount || 0;
			const remaining =
				totals.remaining_amount != null
					? totals.remaining_amount
					: Math.max(0, Number(selected.total_budget_amount || 0) - Number(allocatedSum || 0));

			hostEl.innerHTML =
				'<div class="kt-budget-section kt-surface" data-testid="budget-allocations-panel">' +
				'<div class="d-flex justify-content-between align-items-center mb-2">' +
				"<h6 class=\"mb-0\">" +
				esc(__("Allocations")) +
				"</h6>" +
				addBtn +
				"</div>" +
				banner +
				'<table class="table table-sm mb-0 kt-budget-allocations-table" data-testid="budget-allocations-table">' +
				"<thead><tr><th>" +
				esc(__("Program / Sub-program")) +
				'</th><th class="text-right">' +
				esc(__("Allocated")) +
				"</th><th>" +
				esc(__("Funding Source")) +
				"</th><th>" +
				esc(__("Status")) +
				"</th><th>" +
				esc(__("Notes")) +
				"</th><th class=\"text-right\">" +
				actionHeader +
				"</th></tr></thead><tbody>" +
				tableBody +
				"</tbody></table>" +
				'<div class="kt-budget-allocations-footer mt-2 pt-2 border-top small" data-testid="budget-allocations-footer">' +
				"<span>" +
				esc(__("Total allocated")) +
				": " +
				esc(cur + " " + formatAmount(allocatedSum)) +
				"</span>" +
				'<span class="ml-3">' +
				esc(__("Remaining")) +
				": " +
				esc(cur + " " + formatAmount(remaining)) +
				"</span></div></div>";
		},
	};
})();
