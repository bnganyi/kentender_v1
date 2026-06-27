/* global frappe */
// ── Budget Management workspace → Budget Hub redirect ─────────────────────
// When the user navigates to the "Budget Management" workspace route
// (desk/budget-management), redirect immediately to the budget-builder page.
(function () {
	"use strict";

	function _maybeRedirect() {
		const route = frappe.get_route() || [];
		if (route[0] === "budget-management") {
			frappe.set_route("budget-builder");
		}
	}

	$(document).on("page-change", _maybeRedirect);
	if (frappe.router && frappe.router.on) {
		frappe.router.on("change", _maybeRedirect);
	}

	_maybeRedirect();
})();
