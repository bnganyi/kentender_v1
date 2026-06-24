/**
 * P4-002 — Procurement Plans list (setup/oversight).
 */
(function () {
	frappe.provide("kentender_procurement");

	const PLANS_LIST_API =
		"kentender_procurement.procurement_planning.api.procurement_plans.get_pp_procurement_plans_list";
	const renderTokens = new WeakMap();
	const REQUIRED_TESTID_LITERALS = [
		'data-testid="pp3-plan-list"',
		'data-testid="pp3-plan-row"',
	];
	if (!REQUIRED_TESTID_LITERALS.length) {
		/* static literals kept for G2 selector guard */
	}

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function planId(plan) {
		return String(plan.plan_id || plan.plan_code || "").trim();
	}

	function rowHtml(plan, selectedId) {
		const id = planId(plan);
		const active = id && id === selectedId;
		const meta = [plan.fiscal_year, plan.status_label].filter(Boolean).join(" · ");
		return (
			'<button type="button" class="pp3-plan-list__row' +
			(active ? " is-active" : "") +
			'" data-testid="pp3-plan-row" data-pp3-plan-id="' +
			esc(id) +
			'" aria-selected="' +
			(active ? "true" : "false") +
			'">' +
			'<div class="pp3-plan-list__title">' +
			esc(plan.title || "") +
			"</div>" +
			'<div class="pp3-plan-list__meta text-muted small">' +
			esc(meta) +
			"</div>" +
			'<div class="pp3-plan-list__counts text-muted small">' +
			esc(plan.counts_label || "") +
			"</div>" +
			"</button>"
		);
	}

	function listHtml(plans, selectedId) {
		const rows = Array.isArray(plans) ? plans : [];
		if (!rows.length) {
			return (
				'<div class="pp3-plan-list__empty text-muted small">' +
				esc(__("No procurement plans found for this entity/fiscal year.")) +
				"</div>"
			);
		}
		let html = "";
		for (let i = 0; i < rows.length; i += 1) {
			html += rowHtml(rows[i], selectedId);
		}
		return html;
	}

	function fetchPlans() {
		return frappe
			.call({
				method: PLANS_LIST_API,
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
		const token = (renderTokens.get(host) || 0) + 1;
		renderTokens.set(host, token);
		const selectedId = String(options.selectedPlanId || "").trim();
		host.innerHTML =
			'<div class="pp3-plan-list" data-testid="pp3-plan-list">' +
			'<div class="pp3-plan-list__loading text-muted small">' +
			esc(__("Loading procurement plans…")) +
			"</div></div>";
		fetchPlans()
			.then(function (payload) {
				if (renderTokens.get(host) !== token) return;
				const list = host.querySelector('[data-testid="pp3-plan-list"]');
				if (!list) return;
				const plans = payload.plans || [];
				list.innerHTML = listHtml(plans, selectedId);
				if (typeof options.onLoaded === "function") {
					options.onLoaded(payload, plans);
				}
				if (typeof options.onSelect === "function") {
					list.querySelectorAll('[data-testid="pp3-plan-row"]').forEach(function (btn) {
						btn.addEventListener("click", function () {
							const planCode = String(btn.getAttribute("data-pp3-plan-id") || "").trim();
							const plan = plans.find(function (row) {
								return planId(row) === planCode;
							});
							if (plan) options.onSelect(plan);
						});
					});
				}
			})
			.catch(function () {
				if (renderTokens.get(host) !== token) return;
				const list = host.querySelector('[data-testid="pp3-plan-list"]');
				if (!list) return;
				list.innerHTML =
					'<div class="pp3-plan-list__error text-muted small">' +
					esc(__("Planning information could not be loaded. Try again.")) +
					"</div>";
			});
	}

	kentender_procurement.PlanningPlanList = {
		render: render,
		fetchPlans: fetchPlans,
	};
})();
