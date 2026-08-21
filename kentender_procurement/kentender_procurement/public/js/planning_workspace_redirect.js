// Redirect Workspace "Procurement Planning" → Stitch Page planning-workspace.
// URL /desk/procurement-planning is owned by the Workspace slug; the Page cannot share it.
(function () {
	"use strict";

	function maybeRedirect() {
		var route = frappe.get_route() || [];
		if (route[0] === "Workspaces" && route[1] === "Procurement Planning") {
			frappe.set_route("planning-workspace");
		}
	}

	if (frappe.router && typeof frappe.router.on === "function") {
		frappe.router.on("change", maybeRedirect);
	}
	$(document).on("page-change", maybeRedirect);
	frappe.after_ajax(maybeRedirect);
})();
