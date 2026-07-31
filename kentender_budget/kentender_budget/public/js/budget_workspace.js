/* global frappe */
// ── Budget Management workspace — sidebar setup + hub redirect ────────────
// Mirrors the robust pattern used by strategy_workspace.js:
//   • page-change + app_ready jQuery event  → _onRouteChange()
//   • frappe.router.on("change")           → _onRouteChange()
//   • setTimeout retries on boot           → survive async Frappe init
//   • frappe.ready() callback              → survive SPA first load
//
// This ensures the left navbar (Budget Management workspace) is populated
// reliably on first load, hard refresh, and back/forward navigation —
// without relying on on_page_show / on_page_hide events, which can miss
// the setup call when the sidebar has not yet initialised.
(function () {
	"use strict";

	// Routes that belong to the Budget Management workspace
	function _isBudgetRoute() {
		if (typeof frappe === "undefined") return false;
		const route = frappe.get_route ? frappe.get_route() : [];
		if (!Array.isArray(route)) return false;
		return route[0] === "budget-hub" || route[0] === "budget-workbench";
	}

	// Redirect Workspace tile → hub
	function _maybeRedirect() {
		if (typeof frappe === "undefined") return;
		const route = frappe.get_route ? frappe.get_route() : [];
		if (Array.isArray(route) && route[0] === "Workspaces" && route[1] === "Budget Management") {
			frappe.set_route("budget-hub");
		}
	}

	// Populate the left sidebar with Budget Management workspace items.
	// Called on every route change; is a no-op when not on a budget route.
	function _ensureSidebar() {
		if (!_isBudgetRoute()) return;
		if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
			frappe.app.sidebar.setup("Procurement");
		}
	}

	function _onRouteChange() {
		_maybeRedirect();
		_ensureSidebar();
	}

	function _boot() {
		_onRouteChange();
		// Retry in case sidebar component isn't ready on the first tick
		setTimeout(_ensureSidebar, 200);
		setTimeout(_ensureSidebar, 800);
	}

	function _waitForFrappe() {
		if (typeof window.frappe === "undefined") {
			setTimeout(_waitForFrappe, 20);
			return;
		}
		// Wire all route-change signals — same triple-binding as strategy_workspace.js
		if (window.jQuery) {
			window.jQuery(document).on("page-change app_ready", _onRouteChange);
		}
		if (frappe.router && frappe.router.on) {
			frappe.router.on("change", _onRouteChange);
		}
		if (typeof frappe.ready === "function") {
			frappe.ready(_boot);
		}
		_boot();
	}

	_waitForFrappe();
	window.addEventListener("load", _boot);
})();
