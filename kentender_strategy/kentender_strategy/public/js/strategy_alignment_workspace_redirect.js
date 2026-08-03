// Redirect legacy Strategy Management workspace → Strategy Alignment portfolio.
(function () {
	"use strict";

	function maybeRedirect() {
		var route = frappe.get_route() || [];
		if (route[0] === "Workspaces" && route[1] === "Strategy Management") {
			frappe.set_route("strategy-alignment");
		}
	}

	if (frappe.router && typeof frappe.router.on === "function") {
		frappe.router.on("change", maybeRedirect);
	}
	$(document).on("app_ready", maybeRedirect);
	maybeRedirect();
})();
