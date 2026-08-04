// Redirect legacy Strategy Management workspace → Strategy Alignment portfolio
// (or Strategy Performance for Strategy Viewer — STR-FR-131).
(function () {
	"use strict";

	function isStrategyViewerOnly() {
		var roles = (frappe.user_roles || []).slice();
		if (!roles.length && frappe.boot && frappe.boot.user && frappe.boot.user.roles) {
			roles = frappe.boot.user.roles.slice();
		}
		var hasViewer = roles.indexOf("Strategy Viewer") >= 0;
		if (!hasViewer) {
			return false;
		}
		var operational = [
			"Strategy Officer",
			"Strategy Manager",
			"Strategy Reviewer",
			"Planning Authority",
			"Performance Officer",
			"Performance Verifier",
			"System Manager",
			"Administrator",
		];
		for (var i = 0; i < operational.length; i++) {
			if (roles.indexOf(operational[i]) >= 0) {
				return false;
			}
		}
		return true;
	}

	function strategyHomeRoute() {
		return isStrategyViewerOnly() ? "strategy-performance" : "strategy-alignment";
	}

	function maybeRedirect() {
		var route = frappe.get_route() || [];
		if (route[0] === "Workspaces" && route[1] === "Strategy Management") {
			frappe.set_route(strategyHomeRoute());
			return;
		}
		// Viewer opening the maintenance portfolio lands on Performance by default.
		if (route[0] === "strategy-alignment" && isStrategyViewerOnly()) {
			frappe.set_route("strategy-performance");
		}
	}

	if (frappe.router && typeof frappe.router.on === "function") {
		frappe.router.on("change", maybeRedirect);
	}
	$(document).on("app_ready", maybeRedirect);
	maybeRedirect();
})();
