// Civic Ledger shell router — global bootstrap that activates native-sidebar
// chrome only on registered surface routes (IT STD wizard first).
frappe.provide("kentender_core.cl_shell_router");

(function () {
	"use strict";

	var bound = false;
	var lastSurfaceId = null;

	function registry() {
		return kentender_core.cl_surface_registry || null;
	}

	function shell() {
		return kentender_core.cl_shell || null;
	}

	function onRouteChange() {
		var reg = registry();
		var sh = shell();
		if (!reg || !sh) return;

		var surface = reg.resolveFromRoute(frappe.get_route());
		if (surface) {
			var chrome = (surface.chrome && surface.chrome.toolbar) || {};
			sh.enterNative({
				sidebarWorkspaceKey: surface.sidebarWorkspaceKey || "procurement",
				toolbar: chrome,
				chrome: surface.chrome,
			});
			lastSurfaceId = surface.id;
		} else if (lastSurfaceId || (sh.isNativeActive && sh.isNativeActive())) {
			sh.leaveNative();
			lastSurfaceId = null;
		}
	}

	function bind() {
		if (bound) return;
		bound = true;
		if (frappe.router && typeof frappe.router.on === "function") {
			frappe.router.on("change", onRouteChange);
		}
		/* Initial route (hard refresh / first paint). */
		onRouteChange();
	}

	kentender_core.cl_shell_router = {
		bind: bind,
		onRouteChange: onRouteChange,
		getLastSurfaceId: function () {
			return lastSurfaceId;
		},
	};

	frappe.provide("kentender_core.cl");
	kentender_core.cl.shell_router = kentender_core.cl_shell_router;

	/* Desk boot: bind after frappe.router exists. */
	if (typeof frappe !== "undefined") {
		if (frappe.router) {
			bind();
		} else {
			$(document).on("app_ready", bind);
		}
	}
})();
