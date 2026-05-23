frappe.provide("kentender_budget.budget_audit_panel");

(function () {
	let latestMountToken = 0;
	const auditCacheByBudget = Object.create(null);

	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function formatAmount(value) {
		const n = Number(value || 0);
		return n.toLocaleString("en-US", {
			minimumFractionDigits: 2,
			maximumFractionDigits: 2,
		});
	}

	function renderAuditHtml(selected, auditPayload, cur) {
		const timeline = (auditPayload && auditPayload.timeline) || [];
		const downstream = (auditPayload && auditPayload.downstream) || {};
		let timelineHtml = "";
		if (!timeline.length) {
			timelineHtml =
				'<p class="text-muted small mb-0">' + esc(__("No workflow history yet.")) + "</p>";
		} else {
			timelineHtml = '<ul class="list-unstyled mb-0">';
			for (let i = 0; i < timeline.length; i++) {
				const row = timeline[i];
				timelineHtml +=
					"<li class=\"mb-1\" data-testid=\"budget-audit-timeline-row\">" +
					"<strong>" +
					esc(row.label) +
					"</strong>" +
					(row.detail ? " — " + esc(row.detail) : "") +
					(row.at ? '<span class="text-muted small"> · ' + esc(row.at) + "</span>" : "") +
					(row.note ? '<div class="small text-muted">' + esc(row.note) + "</div>" : "") +
					"</li>";
			}
			timelineHtml += "</ul>";
		}

		function usageValue(key, fallback) {
			const val = downstream[key];
			if (val == null) return fallback;
			return String(val);
		}

		const usage = [
			{
				label: __("Reserved amount"),
				value: cur + " " + formatAmount(downstream.reserved_sum || 0),
				testId: "budget-audit-reserved",
			},
			{
				label: __("Available for reservation"),
				value: cur + " " + formatAmount(downstream.available_sum || 0),
				testId: "budget-audit-available",
			},
			{
				label: __("Linked demands"),
				value: downstream.procurement_available === false ? __("Unavailable") : usageValue("linked_demands", "0"),
				testId: "budget-audit-demands",
			},
			{
				label: __("Linked procurement packages"),
				value: downstream.procurement_available === false ? __("Unavailable") : usageValue("linked_packages", "0"),
				testId: "budget-audit-packages",
			},
			{
				label: __("Linked procurement journeys"),
				value: downstream.procurement_available === false ? __("Unavailable") : usageValue("linked_journeys", "0"),
				testId: "budget-audit-journeys",
			},
		];

		let lines = "";
		for (let j = 0; j < usage.length; j++) {
			lines +=
				'<div class="kt-budget-audit-line" data-testid="' +
				esc(usage[j].testId) +
				'">' +
				'<span class="kt-budget-audit-line__label">' +
				esc(usage[j].label) +
				'</span><span class="kt-budget-audit-line__value">' +
				esc(usage[j].value) +
				"</span></div>";
		}

		return (
			'<div class="kt-budget-section kt-surface" data-testid="budget-audit-panel">' +
			"<h6>" +
			esc(__("Audit")) +
			"</h6>" +
			'<div class="mb-3" data-testid="budget-audit-workflow-history">' +
			'<div class="small font-weight-bold mb-1">' +
			esc(__("Workflow history")) +
			"</div>" +
			timelineHtml +
			"</div>" +
			"<details open data-testid=\"budget-audit-downstream\">" +
			"<summary>" +
			esc(__("Downstream usage")) +
			'</summary><div class="kt-budget-audit-lines mt-2">' +
			lines +
			"</div></details></div>"
		);
	}

	kentender_budget.budget_audit_panel = {
		mount(hostEl, ctx) {
			if (!hostEl || !ctx || !ctx.selected) return;
			const selected = ctx.selected;
			const budgetName = selected.name;
			const cur = selected.currency || "KES";
			const mountToken = ++latestMountToken;
			const cached = auditCacheByBudget[budgetName];

			if (cached) {
				hostEl.innerHTML = renderAuditHtml(selected, cached, cur);
				return;
			}

			hostEl.innerHTML =
				'<div class="text-muted small py-2" data-testid="budget-audit-loading">' +
				esc(__("Loading audit…")) +
				"</div>";

			frappe.call({
				method: "kentender_budget.api.audit.get_budget_audit_data",
				args: { budget_name: budgetName },
				callback: function (r) {
					if (mountToken !== latestMountToken) return;
					const payload = (r && r.message) || {};
					auditCacheByBudget[budgetName] = payload;
					hostEl.innerHTML = renderAuditHtml(selected, payload, cur);
				},
				error: function () {
					if (mountToken !== latestMountToken) return;
					hostEl.innerHTML =
						'<div class="text-muted small py-2" data-testid="budget-audit-error">' +
						esc(__("Unable to load audit data.")) +
						"</div>";
				},
			});
		},
		invalidate(budgetName) {
			if (budgetName) delete auditCacheByBudget[budgetName];
		},
	};
})();
