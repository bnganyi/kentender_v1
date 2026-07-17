// Permanent redirect: the "Procurement Home" workspace ALWAYS lands on the
// Civic Ledger POC page. Loaded on every desk page via app_include_js.
//
// Per .cursor/rules/frappe-workspace-route-pattern.mdc a workspace route is
// ["Workspaces", "Procurement Home"] (route[1] is the workspace TITLE, not the
// slug), so we match route[0] === "Workspaces" && route[1] matches Procurement
// Home. Loop-guarded: never redirects when already on the POC page.
(function () {
	"use strict";

	var POC_PAGE = "kt-cl-shell-poc";
	var HOME_WS = "Procurement Home";

	function matchesHome(name) {
		if (!name) return false;
		if (name === HOME_WS) return true;
		try {
			if (frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(String(name)) === frappe.router.slug(HOME_WS);
			}
		} catch (e) {
			/* ignore */
		}
		return String(name).toLowerCase().replace(/\s+/g, "-") === "procurement-home";
	}

	function isHomeWorkspace(route) {
		if (!route || route[0] !== "Workspaces" || route.length < 2) return false;
		var name = route[1] === "private" && route.length >= 3 ? route[2] : route[1];
		return matchesHome(name);
	}

	function maybeRedirect() {
		try {
			var route = frappe.get_route() || [];
			if (route[0] === POC_PAGE) return; // loop guard
			if (isHomeWorkspace(route)) {
				frappe.set_route(POC_PAGE);
			}
		} catch (e) {
			/* ignore */
		}
	}

	function boot() {
		if (typeof window.frappe === "undefined") {
			setTimeout(boot, 20);
			return;
		}
		if (frappe.router && typeof frappe.router.on === "function") {
			frappe.router.on("change", maybeRedirect);
		}
		maybeRedirect();
		if (typeof frappe.ready === "function") {
			frappe.ready(maybeRedirect);
		}
	}

	boot();
})();
