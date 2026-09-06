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
		if (kentender_core.page_lifecycle) {
			kentender_core.page_lifecycle.bindPagesWithin(document);
		}

		var route = frappe.get_route();
		// A Vue-in-Desk page registered with kentender_core.desk_page owns its
		// own chrome (Industry rail, no Civic Ledger toolbar). This handler
		// runs AFTER the page's on_page_show (router.route(): render() then
		// trigger("change")), so falling through to leaveNative() here used to
		// strip the shell body classes that on_page_show had just applied —
		// a full layout reflow on every navigation.
		var deskPage = kentender_core.desk_page || null;
		if (deskPage && deskPage.ownsRoute(route)) {
			deskPage.applyChrome(route);
			lastSurfaceId = null;
			return;
		}

		var surface = reg.resolveFromRoute(route);
		if (surface) {
			var chrome = (surface.chrome && surface.chrome.toolbar) || {};
			sh.enterNative({
				sidebarWorkspaceKey: surface.sidebarWorkspaceKey || "procurement",
				toolbar: chrome,
				chrome: surface.chrome,
			});
			lastSurfaceId = surface.id;
		} else {
			if (kentender_core.page_lifecycle) {
				kentender_core.page_lifecycle.clearSurfaceBodyClasses();
			}
			if (lastSurfaceId || (sh.isNativeActive && sh.isNativeActive())) {
				sh.leaveNative();
			}
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
