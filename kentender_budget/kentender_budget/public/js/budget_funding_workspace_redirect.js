// Redirect Budget Management workspace → Budget & Funding portfolio.
(function () {
	"use strict";

	function maybeRedirect() {
		var route = frappe.get_route() || [];
		if (route[0] === "Workspaces" && route[1] === "Budget Management") {
			frappe.set_route("budget-funding");
		}
	}

	if (frappe.router && typeof frappe.router.on === "function") {
		frappe.router.on("change", maybeRedirect);
	}
	$(document).on("page-change", maybeRedirect);
	frappe.after_ajax(maybeRedirect);
})();
