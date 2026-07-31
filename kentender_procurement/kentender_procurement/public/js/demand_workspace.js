/* global frappe */
// ── Demand Intake and Approval workspace — sidebar setup + hub redirect ──────
// Same triple-binding pattern as budget_workspace.js and strategy_workspace.js.
(function () {
	"use strict";

	function _isDemandRoute() {
		if (typeof frappe === "undefined") return false;
		var route = frappe.get_route ? frappe.get_route() : [];
		if (!Array.isArray(route)) return false;
		return route[0] === "demand-hub";
	}

	function _maybeRedirect() {
		if (typeof frappe === "undefined") return;
		var route = frappe.get_route ? frappe.get_route() : [];
		if (
			Array.isArray(route) &&
			route[0] === "Workspaces" &&
			route[1] === "Demand Intake and Approval"
		) {
			frappe.set_route("demand-hub");
		}
	}

	function _ensureSidebar() {
		if (!_isDemandRoute()) return;
		if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
			frappe.app.sidebar.setup("Procurement");
		}
	}

	function _onRouteChange() {
		_maybeRedirect();
		_ensureSidebar();
		// Guard: remove the DIA shell class whenever we are NOT on the demand-hub
		// page. This defends against on_page_hide timing gaps that could leave the
		// class on the body and corrupt layout on Budget Hub / Planning Workbench.
		if (!_isDemandRoute()) {
			document.body.classList.remove("kt-dia-shell");
		}
	}

	function _boot() {
		_onRouteChange();
		setTimeout(_ensureSidebar, 200);
		setTimeout(_ensureSidebar, 800);
	}

	function _waitForFrappe() {
		if (typeof window.frappe === "undefined") {
			setTimeout(_waitForFrappe, 20);
			return;
		}
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
