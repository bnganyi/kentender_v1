// Review tab — readiness checklist and workflow actions.

frappe.provide("kentender_strategy.strategy_review_panel");

(function () {
	let latestMountToken = 0;
	const readinessCacheByPlan = Object.create(null);

	function esc(s) {
		return frappe.utils.escape_html(s == null ? "" : String(s));
	}

	function buildReviewHtml(planName, payload) {
		const checks = payload.checks || [];
		const ready = payload.ready;
		const status = payload.status || "Draft";
		let html =
			'<div class="kt-strategy-review-panel" data-testid="strategy-review-panel">' +
			"<h6>" +
			esc(__("Review & Submit")) +
			"</h6>" +
			'<p class="small text-muted" data-testid="strategy-review-status">' +
			esc(__("Current state:")) +
			" " +
			esc(status) +
			"</p>" +
			'<ul class="list-unstyled mb-3" data-testid="strategy-readiness-checklist">';
		checks.forEach(function (c) {
			html +=
				"<li data-testid=\"readiness-check-" +
				esc(c.id) +
				'">' +
				(c.passed ? "✓" : "✗") +
				" " +
				esc(c.label) +
				"</li>";
		});
		html += "</ul>";
		html += '<div class="btn-group btn-group-sm" data-testid="strategy-review-actions">';
		if (status === "Draft") {
			html +=
				'<button type="button" class="btn btn-primary" data-testid="strategy-submit-plan"' +
				(ready ? "" : " disabled") +
				">" +
				esc(__("Submit Plan")) +
				"</button>";
		} else if (status === "Submitted") {
			html +=
				'<button type="button" class="btn btn-primary" data-testid="strategy-approve-plan">' +
				esc(__("Approve")) +
				"</button> " +
				'<button type="button" class="btn btn-default" data-testid="strategy-return-plan">' +
				esc(__("Return for Correction")) +
				"</button>";
		} else if (status === "Approved") {
			html +=
				'<button type="button" class="btn btn-primary" data-testid="strategy-activate-plan">' +
				esc(__("Activate Plan")) +
				"</button>";
		} else if (status === "Active") {
			html +=
				'<button type="button" class="btn btn-default" data-testid="strategy-archive-plan">' +
				esc(__("Archive Plan")) +
				"</button>";
		}
		html += "</div></div>";
		return html;
	}

	function buildFallbackPayload(planSnapshot) {
		const programCount = Number(planSnapshot && planSnapshot.program_count ? planSnapshot.program_count : 0);
		const subProgramCount = Number(planSnapshot && planSnapshot.sub_program_count ? planSnapshot.sub_program_count : 0);
		const indicatorCount = Number(
			planSnapshot && planSnapshot.indicator_count != null
				? planSnapshot.indicator_count
				: planSnapshot && planSnapshot.objective_count
					? planSnapshot.objective_count
					: 0,
		);
		const targetCount = Number(planSnapshot && planSnapshot.target_count ? planSnapshot.target_count : 0);
		const checks = [
			{ id: "program", label: __("At least one Program exists"), passed: programCount > 0 },
			{ id: "sub_program", label: __("At least one Sub-program exists"), passed: subProgramCount > 0 },
			{ id: "indicator", label: __("At least one Indicator exists"), passed: indicatorCount > 0 },
			{ id: "target", label: __("At least one Target exists"), passed: targetCount > 0 },
		];
		return {
			status: (planSnapshot && planSnapshot.status) || "Draft",
			checks: checks,
			ready: checks.every(function (c) {
				return c.passed;
			}),
		};
	}

	kentender_strategy.strategy_review_panel = {
		mount(hostEl, planName, planSnapshot) {
			if (!hostEl || !planName) return;
			const $host = $(hostEl);
			const mountToken = ++latestMountToken;
			const existingPlan = $host.attr("data-plan-name");
			const hasRenderedPanel = $host.find("[data-testid='strategy-review-panel']").length > 0;
			const cached = readinessCacheByPlan[planName];
			const fallbackPayload = !cached && planSnapshot ? buildFallbackPayload(planSnapshot) : null;
			if (cached) {
				$host.html(buildReviewHtml(planName, cached));
			} else if (fallbackPayload) {
				$host.html(buildReviewHtml(planName, fallbackPayload));
			} else if (!hasRenderedPanel) {
				$host.html('<div class="text-muted small">' + esc(__("Loading review…")) + "</div>");
			}
			$host.attr("data-plan-name", planName);

			frappe.call({
				method: "kentender_strategy.api.strategy_workflow.get_plan_readiness",
				args: { plan_name: planName },
				callback(r) {
					if (mountToken !== latestMountToken) return;
					const payload = r.message || {};
					readinessCacheByPlan[planName] = payload;
					$host.html(buildReviewHtml(planName, payload));

						$host.find("[data-testid='strategy-submit-plan']").on("click", function () {
							frappe.call({
								method: "kentender_strategy.api.strategy_workflow.submit_plan",
								args: { plan_name: planName },
								callback() {
									frappe.show_alert({ message: __("Submitted"), indicator: "green" });
									kentender_strategy.strategy_review_panel.mount(hostEl, planName);
								},
								error(r) {
									frappe.msgprint(
										(r && r.message) || __("Unable to submit plan."),
									);
								},
							});
						});
						$host.find("[data-testid='strategy-approve-plan']").on("click", function () {
							frappe.call({
								method: "kentender_strategy.api.strategy_workflow.approve_plan",
								args: { plan_name: planName },
								callback() {
									kentender_strategy.strategy_review_panel.mount(hostEl, planName);
								},
							});
						});
						$host.find("[data-testid='strategy-activate-plan']").on("click", function () {
							frappe.call({
								method: "kentender_strategy.api.strategy_workflow.activate_plan",
								args: { plan_name: planName },
								callback() {
									kentender_strategy.strategy_review_panel.mount(hostEl, planName);
								},
							});
						});
						$host.find("[data-testid='strategy-return-plan']").on("click", function () {
							frappe.call({
								method: "kentender_strategy.api.strategy_workflow.return_for_correction",
								args: { plan_name: planName },
								callback() {
									kentender_strategy.strategy_review_panel.mount(hostEl, planName);
								},
							});
						});
						$host.find("[data-testid='strategy-archive-plan']").on("click", function () {
							frappe.call({
								method: "kentender_strategy.api.strategy_workflow.archive_plan",
								args: { plan_name: planName },
								callback() {
									kentender_strategy.strategy_review_panel.mount(hostEl, planName);
								},
							});
						});
				},
				error() {
					if (mountToken !== latestMountToken) return;
					if (!hasRenderedPanel) {
						$host.html(
							'<div class="text-muted small" data-testid="strategy-review-unavailable">' +
								esc(__("Review readiness is temporarily unavailable.")) +
								"</div>",
						);
					}
				},
			});
		},
	};
})();
