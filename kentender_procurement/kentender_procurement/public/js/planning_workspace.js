/* global frappe */
// Procurement Planning workspace — sidebar setup + Planning Hub redirect.
(function () {
	"use strict";

	function _isPlanningHubRoute() {
		if (typeof frappe === "undefined") return false;
		var route = frappe.get_route ? frappe.get_route() : [];
		if (!Array.isArray(route)) return false;
		return route[0] === "planning-hub";
	}

	function _hasWorkbenchDeepLink() {
		var search = String(window.location.search || "");
		return /[?&](plan|queue|item|package_code)=/.test(search);
	}

	function _maybeRedirect() {
		if (typeof frappe === "undefined") return;
		var route = frappe.get_route ? frappe.get_route() : [];
		if (
			Array.isArray(route) &&
			route[0] === "Workspaces" &&
			route[1] === "Procurement Planning"
		) {
			// Preserve explicit workbench entry (Open Workbench, blocked queue, package deep links).
			if (_hasWorkbenchDeepLink()) {
				return;
			}
			frappe.set_route("planning-hub");
		}
	}

	function _ensureSidebar() {
		if (!_isPlanningHubRoute()) return;
		if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
			frappe.app.sidebar.setup("Procurement");
		}
	}

	function _onRouteChange() {
		_maybeRedirect();
		_ensureSidebar();
		if (!_isPlanningHubRoute()) {
			document.body.classList.remove("kt-pph-shell");
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
