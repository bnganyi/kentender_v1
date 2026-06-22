/**
 * P5C-001 / P5C-002 — Dedicated Planning Home surface shell + summary.
 */
(function () {
	frappe.provide("kentender_procurement");

	function html() {
		return (
			'<article class="pp2-planning-home" data-testid="pp2-planning-home-surface">' +
			'<div class="pp2-planning-home__body" data-testid="pp2-planning-home-body">' +
			'<div class="pp2-planning-home__summary-host"></div>' +
			'<div class="pp2-planning-home__queues" data-testid="pp2-planning-home-queues"></div>' +
			"</div></article>"
		);
	}

	function mountSummary(body) {
		if (!body) return;
		const summaryHost = body.querySelector(".pp2-planning-home__summary-host");
		if (!summaryHost) return;
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningSummary &&
			typeof kentender_procurement.PlanningSummary.fetchAndRender === "function"
				? kentender_procurement.PlanningSummary
				: null;
		if (api) {
			api.fetchAndRender(summaryHost);
			return;
		}
		summaryHost.innerHTML =
			'<section class="pp2-planning-summary" data-testid="pp2-planning-summary"></section>';
	}

	function mountQueues(body) {
		if (!body) return;
		const queuesHost = body.querySelector('[data-testid="pp2-planning-home-queues"]');
		if (!queuesHost) return;
		const api =
			kentender_procurement &&
			kentender_procurement.PlanningHomeQueues &&
			typeof kentender_procurement.PlanningHomeQueues.fetchAndRender === "function"
				? kentender_procurement.PlanningHomeQueues
				: null;
		if (api) {
			api.fetchAndRender(queuesHost);
		}
	}

	function render(host) {
		if (!host) return;
		host.innerHTML = html();
		const body = host.querySelector('[data-testid="pp2-planning-home-body"]');
		mountSummary(body);
		mountQueues(body);
	}

	kentender_procurement.PlanningHome = {
		html: html,
		render: render,
		mountSummary: mountSummary,
		mountQueues: mountQueues,
	};
})();
