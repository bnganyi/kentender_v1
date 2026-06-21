/**
 * P5-004 — Shared PlanningStatusBadge component for PP2 lifecycle labels.
 */
(function () {
	frappe.provide("kentender_procurement");

	const PACKAGE_STATUS_CLASS = {
		draft: "is-draft",
		"in review": "is-in-review",
		"returned for correction": "is-returned-for-correction",
		approved: "is-approved",
		"ready for release": "is-ready-for-release",
		"released to tender": "is-released-to-tender",
		"consumed by tender management": "is-consumed-by-tm",
		superseded: "is-superseded",
		cancelled: "is-cancelled",
	};

	const PACKAGE_LIST_LABEL = {
		draft: __("Draft"),
		"in review": __("In Review"),
		"returned for correction": __("Returned"),
		approved: __("Approved"),
		"ready for release": __("Ready for Release"),
		"released to tender": __("Released"),
		"consumed by tender management": __("Consumed"),
		superseded: __("Superseded"),
		cancelled: __("Cancelled"),
	};

	const DEMAND_STATUS_LABEL = {
		"planning ready": __("Ready for Planning"),
		"ready for planning": __("Ready for Planning"),
		"not planned": __("Ready for Planning"),
		"partially planned": __("Partially Planned"),
		blocked: __("Blocked"),
	};

	const DEMAND_STATUS_CLASS = {
		"ready for planning": "is-demand-ready",
		"partially planned": "is-demand-partial",
		blocked: "is-demand-blocked",
	};

	function normalize(raw) {
		return String(raw || "").trim().toLowerCase();
	}

	function packageStatusLabel(status, scope) {
		const key = normalize(status);
		const raw = String(status || "").trim();
		if (!raw) return "—";
		if (String(scope || "").trim().toLowerCase() === "list") {
			return PACKAGE_LIST_LABEL[key] || raw;
		}
		return raw;
	}

	function demandStatusLabel(status) {
		const key = normalize(status);
		return DEMAND_STATUS_LABEL[key] || String(status || "").trim() || "—";
	}

	function packageClass(status) {
		const key = normalize(status);
		return PACKAGE_STATUS_CLASS[key] || "is-unknown";
	}

	function demandClass(status) {
		const normalizedLabel = normalize(demandStatusLabel(status));
		return DEMAND_STATUS_CLASS[normalizedLabel] || "is-unknown";
	}

	function badgeHtml(status, opts) {
		const o = opts || {};
		const context = String(o.context || "package").trim().toLowerCase();
		const scope = String(o.scope || "header").trim().toLowerCase();
		const label =
			context === "demand"
				? demandStatusLabel(status)
				: packageStatusLabel(status, scope);
		const stateClass = context === "demand" ? demandClass(status) : packageClass(status);
		const statusKey = normalize(status);
		const attrs =
			'data-testid="pp2-planning-status-badge" data-status-context="' +
			frappe.utils.escape_html(context) +
			'" data-status-scope="' +
			frappe.utils.escape_html(scope) +
			'" data-status-key="' +
			frappe.utils.escape_html(statusKey) +
			'"';
		return (
			'<span class="pp2-planning-status-badge ' +
			stateClass +
			'" ' +
			attrs +
			">" +
			frappe.utils.escape_html(label) +
			"</span>"
		);
	}

	function badgeRender($host, status, opts) {
		const $target = $host && $host.jquery ? $host : $(String($host || ""));
		if (!$target || !$target.length) return;
		$target.html(badgeHtml(status, opts));
	}

	kentender_procurement.PlanningStatusBadge = {
		html: badgeHtml,
		render: badgeRender,
		normalizePackageStatus: packageStatusLabel,
		normalizeDemandStatus: demandStatusLabel,
	};
})();
