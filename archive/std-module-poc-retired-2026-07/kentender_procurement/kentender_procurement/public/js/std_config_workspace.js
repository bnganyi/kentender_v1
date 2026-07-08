/* global frappe */
// STD-CFG-0003 — Governance workspace redirects when STD Config UI v2 is enabled.
(function () {
	"use strict";

	const GOVERNANCE_WORKSPACE = "Governance & Configuration";

	function _isV2Enabled() {
		if (
			kentender_procurement &&
			kentender_procurement.std_config_shared &&
			typeof kentender_procurement.std_config_shared.isV2Enabled === "function"
		) {
			return kentender_procurement.std_config_shared.isV2Enabled();
		}
		const boot = (frappe.boot && frappe.boot.kentender_procurement) || {};
		return !!boot.std_config_ui_v2_enabled;
	}

	function _isStdLibraryRoute() {
		const route = frappe.get_route ? frappe.get_route() : [];
		return Array.isArray(route) && route[0] === "std-library";
	}

	function _isStdConfiguratorRoute() {
		const route = frappe.get_route ? frappe.get_route() : [];
		return Array.isArray(route) && route[0] === "std-configurator";
	}

	function _isStdRoute() {
		return _isStdLibraryRoute() || _isStdConfiguratorRoute();
	}

	function _maybeRedirectStdEngine() {
		if (!_isV2Enabled()) return;
		const route = frappe.get_route ? frappe.get_route() : [];
		if (!Array.isArray(route) || route[0] !== "std-engine") return;
		const seg = String(route[1] || "").toLowerCase();
		if (seg === "advanced") return;
		if (seg === "library" && String(route[2] || "").toLowerCase() === "import") {
			frappe.set_route("std-library", "import");
			return;
		}
		frappe.set_route("std-library");
	}

	function _maybeRedirectGovernanceWorkspace() {
		if (!_isV2Enabled()) return;
		const route = frappe.get_route ? frappe.get_route() : [];
		if (
			Array.isArray(route) &&
			route[0] === "Workspaces" &&
			route[1] === GOVERNANCE_WORKSPACE
		) {
			frappe.set_route("std-library");
		}
	}

	function _ensureSidebar() {
		if (!_isStdRoute()) return;
		if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
			frappe.app.sidebar.setup(GOVERNANCE_WORKSPACE);
		}
	}

	function _onRouteChange() {
		_maybeRedirectStdEngine();
		_maybeRedirectGovernanceWorkspace();
		_ensureSidebar();
		if (!_isStdRoute()) {
			document.body.classList.remove("kt-std-lib-shell", "kt-std-cfg-shell");
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
