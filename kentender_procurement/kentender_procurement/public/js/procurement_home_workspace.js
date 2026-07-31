/* global frappe */
// Legacy Workspace "Procurement Home" → functional Page (unique slug).
(function () {
	"use strict";

	function _maybeRedirect() {
		if (typeof frappe === "undefined" || !frappe.get_route || !frappe.set_route) return;
		var route = frappe.get_route();
		if (
			Array.isArray(route) &&
			route[0] === "Workspaces" &&
			route[1] === "Procurement Home"
		) {
			frappe.set_route("kt-procurement-home");
		}
	}

	function _wait() {
		if (typeof frappe === "undefined" || !frappe.router) {
			setTimeout(_wait, 50);
			return;
		}
		_maybeRedirect();
		if (frappe.router.on) {
			frappe.router.on("change", _maybeRedirect);
		}
		$(document).on("page-change", _maybeRedirect);
	}

	_wait();
})();
