/**
 * P4-003 — Selected procurement plan summary panel.
 */
(function () {
	frappe.provide("kentender_procurement");

	const PLAN_SUMMARY_API =
		"kentender_procurement.procurement_planning.api.procurement_plans.get_pp_procurement_plan_summary";
	const ACTIVATE_PLAN_API =
		"kentender_procurement.procurement_planning.api.procurement_plans.activate_pp_procurement_plan";
	const CLOSE_PLAN_API =
		"kentender_procurement.procurement_planning.api.procurement_plans.close_pp_procurement_plan";
	const WORKBENCH_ROOT = "/desk/procurement-planning";
	const renderTokens = new WeakMap();
	const REQUIRED_TESTID_LITERALS = [
		'data-testid="pp3-plan-summary"',
		'data-testid="pp3-plan-summary-status"',
		'data-testid="pp3-plan-summary-fiscal-year"',
		'data-testid="pp3-plan-summary-demands"',
		'data-testid="pp3-plan-summary-packages"',
		'data-testid="pp3-plan-summary-released"',
		'data-testid="pp3-plan-summary-blockers"',
		'data-testid="pp3-activate-plan-button"',
		'data-testid="pp3-close-plan-button"',
		'data-testid="pp3-open-plan-in-workbench"',
		'data-testid="pp3-view-plan-evidence"',
	];
	if (!REQUIRED_TESTID_LITERALS.length) {
		/* static literals kept for G2 selector guard */
	}

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function rowHtml(label, value, testId) {
		return (
			'<div class="pp3-plan-summary__row">' +
			'<span class="pp3-plan-summary__label text-muted small">' +
			esc(label) +
			"</span>" +
			'<div class="pp3-plan-summary__value" data-testid="' +
			esc(testId) +
			'">' +
			esc(value) +
			"</div></div>"
		);
	}

	function actionsHtml(summary) {
		const s = summary || {};
		let buttons = "";
		if (s.show_activate_plan) {
			buttons +=
				'<button type="button" class="btn btn-primary btn-sm me-2" data-testid="pp3-activate-plan-button" data-pp3-plan-action="activate">' +
				esc(__("Activate Plan")) +
				"</button>";
		}
		if (s.show_close_plan) {
			buttons +=
				'<button type="button" class="btn btn-default btn-sm me-2" data-testid="pp3-close-plan-button" data-pp3-plan-action="close">' +
				esc(__("Close Plan")) +
				"</button>";
		}
		if (s.show_open_in_workbench !== false) {
			buttons +=
				'<button type="button" class="btn btn-default btn-sm me-2" data-testid="pp3-open-plan-in-workbench" data-pp3-plan-action="open_workbench">' +
				esc(__("Open in Workbench")) +
				"</button>";
		}
		if (s.show_view_evidence !== false) {
			buttons +=
				'<button type="button" class="btn btn-default btn-sm" data-testid="pp3-view-plan-evidence" data-pp3-plan-action="view_evidence">' +
				esc(__("View Evidence")) +
				"</button>";
		}
		if (!buttons) return "";
		return '<div class="pp3-plan-summary__actions mt-3">' + buttons + "</div>";
	}

	function summaryHtml(summary) {
		const s = summary || {};
		return (
			'<section class="pp3-plan-summary" data-testid="pp3-plan-summary">' +
			'<div class="pp3-plan-summary__title h6 mb-3">' +
			esc(s.title || __("Plan Summary")) +
			"</div>" +
			rowHtml(__("Status"), s.status_label || "—", "pp3-plan-summary-status") +
			rowHtml(__("Fiscal year"), s.fiscal_year || "—", "pp3-plan-summary-fiscal-year") +
			rowHtml(
				__("Demands included"),
				String(s.demands_count == null ? "—" : s.demands_count),
				"pp3-plan-summary-demands",
			) +
			rowHtml(
				__("Packages"),
				String(s.packages_count == null ? "—" : s.packages_count),
				"pp3-plan-summary-packages",
			) +
			rowHtml(
				__("Released"),
				String(s.released_count == null ? "—" : s.released_count),
				"pp3-plan-summary-released",
			) +
			rowHtml(__("Blockers"), s.blockers_label || __("None"), "pp3-plan-summary-blockers") +
			actionsHtml(s) +
			"</section>"
		);
	}

	function bindActions(host, summary, options) {
		if (!host) return;
		const planId = String((summary && summary.plan_id) || "").trim();
		host.querySelectorAll("[data-pp3-plan-action]").forEach(function (button) {
			if (button.getAttribute("data-bound") === "1") return;
			button.setAttribute("data-bound", "1");
			button.addEventListener("click", function () {
				const action = String(button.getAttribute("data-pp3-plan-action") || "").trim();
				if (action === "activate" && planId) {
					frappe.call({
						method: ACTIVATE_PLAN_API,
						args: { plan_id: planId },
						callback: function (response) {
							const msg = (response && response.message) || {};
							if (!msg.ok) {
								frappe.msgprint(msg.message || __("Plan could not be activated."));
								return;
							}
							frappe.show_alert({ message: __("Plan activated."), indicator: "green" });
							host.innerHTML = summaryHtml(msg);
							bindActions(host, msg, options);
							if (typeof options.onRefresh === "function") options.onRefresh(msg);
						},
					});
					return;
				}
				if (action === "close" && planId) {
					frappe.call({
						method: CLOSE_PLAN_API,
						args: { plan_id: planId },
						callback: function (response) {
							const msg = (response && response.message) || {};
							if (!msg.ok) {
								frappe.msgprint(msg.message || __("Plan could not be closed."));
								return;
							}
							frappe.show_alert({ message: __("Plan closed."), indicator: "green" });
							host.innerHTML = summaryHtml(msg);
							bindActions(host, msg, options);
							if (typeof options.onRefresh === "function") options.onRefresh(msg);
						},
					});
					return;
				}
				if (action === "open_workbench") {
					try {
						if (frappe.router && typeof frappe.router.push_state === "function") {
							frappe.router.push_state(WORKBENCH_ROOT);
							return;
						}
					} catch (e) {
						/* ignore */
					}
					window.location.href = WORKBENCH_ROOT;
					return;
				}
				if (action === "view_evidence" && planId) {
					if (
						kentender_procurement.PlanningWorkbenchEvidenceDrawer &&
						typeof kentender_procurement.PlanningWorkbenchEvidenceDrawer.openForPlan === "function"
					) {
						kentender_procurement.PlanningWorkbenchEvidenceDrawer.openForPlan({
							plan_id: planId,
							title: summary.title,
						});
					}
				}
			});
		});
	}

	function fetchSummary(planId) {
		return frappe
			.call({
				method: PLAN_SUMMARY_API,
				args: { plan_id: planId },
				type: "GET",
				freeze: false,
			})
			.then(function (r) {
				const msg = (r && r.message) || {};
				if (!msg.ok) {
					throw new Error(msg.message || __("Planning information could not be loaded."));
				}
				return msg;
			});
	}

	function render(host, opts) {
		if (!host) return;
		const options = opts || {};
		const plan = options.plan || {};
		const planId = String(plan.plan_id || plan.plan_code || options.planId || "").trim();
		const token = (renderTokens.get(host) || 0) + 1;
		renderTokens.set(host, token);
		if (!planId) {
			host.innerHTML =
				'<div class="pp3-plan-summary__empty text-muted small">' +
				esc(__("Select a procurement plan to view its summary.")) +
				"</div>";
			return;
		}
		host.innerHTML =
			'<div class="pp3-plan-summary__loading text-muted small">' +
			esc(__("Loading procurement plans…")) +
			"</div>";
		fetchSummary(planId)
			.then(function (payload) {
				if (renderTokens.get(host) !== token) return;
				host.innerHTML = summaryHtml(payload);
				bindActions(host, payload, options);
				if (typeof options.onLoaded === "function") {
					options.onLoaded(payload);
				}
			})
			.catch(function () {
				if (renderTokens.get(host) !== token) return;
				host.innerHTML =
					'<div class="pp3-plan-summary__error text-muted small">' +
					esc(__("Planning information could not be loaded. Try again.")) +
					"</div>";
			});
	}

	kentender_procurement.PlanningPlanSummary = {
		render: render,
		fetchSummary: fetchSummary,
	};
})();
