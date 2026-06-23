/**
 * P2-004 — Shared PP3 ActivePlanBanner component.
 */
(function () {
	frappe.provide("kentender_procurement");

	const ACTIVE_PLAN_API =
		"kentender_procurement.procurement_planning.api.active_plan.get_pp_active_plan_view_model";
	let renderToken = 0;

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function readMessage(response) {
		if (!response) return {};
		if (response.message && typeof response.message === "object") {
			return response.message;
		}
		return response;
	}

	function buildNoActiveHtml(payload) {
		const message = String(payload.message || "").trim();
		const fallbackMessage = __("No active procurement plan exists for this fiscal year.");
		const primary = payload.primary_action || {};
		const secondary = payload.secondary_action || {};
		const primaryLabel = String(primary.label || __("Create Plan")).trim();
		const secondaryLabel = String(secondary.label || __("Activate Existing Plan")).trim();
		return (
			'<section class="pp3-active-plan-banner pp3-active-plan-banner--gate" data-testid="pp3-no-active-plan-gate">' +
			'<p class="pp3-active-plan-banner__title mb-1">' +
			esc(message || fallbackMessage) +
			"</p>" +
			'<p class="pp3-active-plan-banner__help text-muted small mb-2">' +
			esc(__("Create or activate a procurement plan before planning approved demands.")) +
			"</p>" +
			'<div class="pp3-active-plan-banner__actions">' +
			'<button type="button" class="btn btn-sm btn-primary" data-testid="pp3-create-plan-button" data-pp3-action="' +
			esc(primary.action || "create_plan") +
			'">' +
			esc(primaryLabel) +
			"</button>" +
			'<button type="button" class="btn btn-sm btn-default" data-testid="pp3-activate-plan-button" data-pp3-action="' +
			esc(secondary.action || "activate_existing_plan") +
			'">' +
			esc(secondaryLabel) +
			"</button>" +
			"</div>" +
			"</section>"
		);
	}

	function buildActiveHtml(payload) {
		const title = String(payload.plan_title || payload.plan_code || "").trim();
		const code = String(payload.plan_code || "").trim();
		const fiscalYear = String(payload.fiscal_year || "").trim();
		const planLabel = title || __("Procurement Plan");
		const detailParts = [];
		if (code && code !== title) detailParts.push(code);
		if (fiscalYear) detailParts.push(fiscalYear);
		const details = detailParts.join(" · ");
		const canChange = !!payload.can_change_plan;
		const canView = !!payload.can_view_plan;
		return (
			'<section class="pp3-active-plan-banner pp3-active-plan-banner--active" data-testid="pp3-active-plan-banner">' +
			'<p class="pp3-active-plan-banner__title mb-1">' +
			esc(__("Active plan: {0}").replace("{0}", planLabel)) +
			"</p>" +
			(details
				? '<p class="pp3-active-plan-banner__meta text-muted small mb-2">' + esc(details) + "</p>"
				: "") +
			'<div class="pp3-active-plan-banner__actions">' +
			(canChange
				? '<button type="button" class="btn btn-sm btn-default" data-testid="pp3-change-plan-button" data-pp3-action="change_plan">' +
					esc(__("Change Plan")) +
					"</button>"
				: "") +
			(canView
				? '<button type="button" class="btn btn-sm btn-default" data-testid="pp3-view-plan-button" data-pp3-action="view_plan">' +
					esc(__("View Plan")) +
					"</button>"
				: "") +
			"</div>" +
			"</section>"
		);
	}

	function html(payload) {
		const p = payload || {};
		return p.has_active_plan ? buildActiveHtml(p) : buildNoActiveHtml(p);
	}

	function render(host, payload) {
		if (!host || host.nodeType !== 1) return;
		host.innerHTML = html(payload || {});
	}

	function callApi(args) {
		return new Promise(function (resolve) {
			frappe.call({
				method: ACTIVE_PLAN_API,
				args: args || {},
				callback: function (response) {
					resolve(readMessage(response));
				},
				error: function () {
					resolve({ ok: false, has_active_plan: false });
				},
			});
		});
	}

	function fetchAndRender(host, opts) {
		if (!host || host.nodeType !== 1) return Promise.resolve();
		const token = ++renderToken;
		const options = opts || {};
		const args = {};
		if (options.procuring_entity) args.procuring_entity = options.procuring_entity;
		if (options.fiscal_year) args.fiscal_year = options.fiscal_year;
		return callApi(args).then(function (payload) {
			if (token !== renderToken) return;
			render(host, payload || {});
		});
	}

	function fetchPayload(opts) {
		return callApi(opts || {});
	}

	kentender_procurement.PlanningActivePlanBanner = {
		html: html,
		render: render,
		fetchAndRender: fetchAndRender,
		fetchPayload: fetchPayload,
	};
})();
