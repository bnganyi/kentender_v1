/**
 * P5C-002 — Planning Home summary count bar.
 */
(function () {
	frappe.provide("kentender_procurement");

	const SUMMARY_API =
		"kentender_procurement.procurement_planning.api.planning_home.get_pp_planning_home_summary";

	const SUMMARY_METRICS = [
		{ key: "needs_planning", label: __("Needs Planning"), testId: "pp2-planning-summary-needs-planning" },
		{ key: "needs_review", label: __("Needs Review"), testId: "pp2-planning-summary-needs-review" },
		{
			key: "ready_to_release",
			label: __("Ready to Release"),
			testId: "pp2-planning-summary-ready-to-release",
		},
		{
			key: "released_recently",
			label: __("Released Recently"),
			testId: "pp2-planning-summary-released-recently",
		},
		{ key: "blocked", label: __("Blocked"), testId: "pp2-planning-summary-blocked" },
	];

	let fetchToken = 0;

	function esc(value) {
		return frappe.utils.escape_html(String(value == null ? "" : value));
	}

	function emptySummary() {
		const out = {};
		for (let i = 0; i < SUMMARY_METRICS.length; i += 1) {
			out[SUMMARY_METRICS[i].key] = 0;
		}
		return out;
	}

	function normalizeSummary(raw) {
		const base = emptySummary();
		const source = raw && typeof raw === "object" ? raw : {};
		for (let i = 0; i < SUMMARY_METRICS.length; i += 1) {
			const key = SUMMARY_METRICS[i].key;
			const value = Number(source[key]);
			base[key] = Number.isFinite(value) && value >= 0 ? Math.floor(value) : 0;
		}
		return base;
	}

	function html(summary) {
		const counts = normalizeSummary(summary);
		let metricsHtml = "";
		for (let i = 0; i < SUMMARY_METRICS.length; i += 1) {
			const metric = SUMMARY_METRICS[i];
			const count = counts[metric.key];
			metricsHtml +=
				'<span class="pp2-planning-summary__metric" data-testid="' +
				esc(metric.testId) +
				'">' +
				esc(metric.label) +
				": <strong>" +
				esc(String(count)) +
				"</strong></span>";
		}
		return (
			'<section class="pp2-planning-summary" data-testid="pp2-planning-summary">' + metricsHtml + "</section>"
		);
	}

	function render(host, summary) {
		if (!host) return;
		host.innerHTML = html(summary);
	}

	function fetchAndRender(host) {
		if (!host) return;
		fetchToken += 1;
		const token = fetchToken;
		render(host, emptySummary());
		frappe.call({
			method: SUMMARY_API,
			callback: function (response) {
				if (token !== fetchToken) return;
				const message = response && response.message ? response.message : {};
				if (message && message.ok && message.summary) {
					render(host, message.summary);
					return;
				}
				render(host, emptySummary());
			},
			error: function () {
				if (token !== fetchToken) return;
				render(host, emptySummary());
			},
		});
	}

	kentender_procurement.PlanningSummary = {
		SUMMARY_METRICS: SUMMARY_METRICS,
		emptySummary: emptySummary,
		normalizeSummary: normalizeSummary,
		html: html,
		render: render,
		fetchAndRender: fetchAndRender,
	};
})();
