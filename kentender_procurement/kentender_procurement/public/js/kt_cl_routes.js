// Civic Ledger desk-shell router glue. Loaded on every desk page via
// app_include_js. Two responsibilities:
//
// 1. Permanent redirect: the "Procurement Home" workspace ALWAYS lands on the
//    Civic Ledger POC page. Per .cursor/rules/frappe-workspace-route-pattern.mdc
//    a workspace route is ["Workspaces", "Procurement Home"] (route[1] is the
//    workspace TITLE, not the slug). Loop-guarded: never redirects when already
//    on the POC page.
// 2. Shell teardown: the POC page mounts a fixed, full-height custom sidenav and
//    adds body.kt-cl-shell. Frappe never calls our leave() when routing away, so
//    the shell would leak onto other pages (e.g. strategy-management), covering
//    their content with the 256px rail. On every route change that is NOT the
//    POC page, tear the shell down so each destination renders normally.
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

	function teardownShell() {
		if (!document.body.classList.contains("kt-cl-shell")) return;
		var shell = window.kentender_core && kentender_core.cl_shell;
		if (shell && typeof shell.leave === "function") {
			shell.leave();
		}
	}

	function onRouteChange() {
		try {
			var route = frappe.get_route() || [];
			if (route[0] === POC_PAGE) return; // loop guard: shell owns the POC page
			if (isHomeWorkspace(route)) {
				frappe.set_route(POC_PAGE); // shell will re-mount on the POC page
				return;
			}
			// Any other route: ensure the POC shell is not leaking onto it.
			teardownShell();
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
			frappe.router.on("change", onRouteChange);
		}
		onRouteChange();
		if (typeof frappe.ready === "function") {
			frappe.ready(onRouteChange);
		}
	}

	boot();
})();
