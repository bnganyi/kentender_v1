// Audit tab — downstream usage (read-only).

frappe.provide("kentender_strategy.strategy_audit_panel");

(function () {
	function esc(s) {
		return frappe.utils.escape_html(s == null ? "" : String(s));
	}

	kentender_strategy.strategy_audit_panel = {
		mount(hostEl, planName) {
			if (!hostEl || !planName) return;
			const $host = $(hostEl);
			$host.html(
				'<div class="kt-strategy-audit-panel" data-testid="strategy-audit-panel">' +
				"<h6>" +
				esc(__("Audit & Usage")) +
				"</h6>" +
				'<details class="mb-2" data-testid="strategy-downstream-usage">' +
				"<summary>" +
				esc(__("Downstream usage")) +
				"</summary>" +
				'<div class="small text-muted py-2" data-testid="strategy-downstream-usage-body">' +
				esc(__("Loading…")) +
				"</div></details>" +
				'<p class="small text-muted mb-0" data-testid="strategy-audit-history-note">' +
				esc(__("Change history is available from the Strategic Plan document.")) +
				"</p></div>",
			);

			frappe.call({
				method: "kentender_strategy.api.workspace.get_plan_downstream_usage",
				args: { plan_name: planName },
				callback(r) {
					const usage = (r.message && r.message.items) || [];
					const $body = $host.find("[data-testid='strategy-downstream-usage-body']");
					if (!usage.length) {
						$body.text(__("No downstream references yet."));
						return;
					}
					let html = "<ul class=\"list-unstyled mb-0\">";
					usage.forEach(function (item) {
						html += "<li>" + esc(item.label) + ": " + esc(String(item.count)) + "</li>";
					});
					html += "</ul>";
					$body.html(html);
				},
				error() {
					$host.find("[data-testid='strategy-downstream-usage-body']").text(__("Unable to load usage."));
				},
			});
		},
	};
})();
