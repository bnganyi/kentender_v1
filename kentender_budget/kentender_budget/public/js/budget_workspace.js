/* global frappe */
// ── Budget Management workspace → Budget Hub redirect ─────────────────────
// When the user navigates to the "Budget Management" workspace route
// (desk/budget-management), redirect immediately to the budget-builder page.
(function () {
	"use strict";

	function _maybeRedirect() {
		const route = frappe.get_route() || [];
		if (route[0] === "Workspaces" && route[1] === "Budget Management") {
			frappe.set_route("budget-hub");
		}
	}

	$(document).on("page-change", _maybeRedirect);
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", _maybeRedirect);
	}

	_maybeRedirect();
})();
