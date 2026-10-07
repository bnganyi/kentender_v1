// Civic Ledger surface registry — maps Desk route slugs to chrome metadata.
//
// The registry is empty on purpose. Its only surfaces were the 19 screens of the legacy IT
// Tender Configuration wizard and its publication pages; that module was retired completely
// (7 Oct 2026, RG-04 / RG-05 / AUD-XC-143). The mechanism stays because kt_cl_shell_router.js
// resolves routes through it. A page that needs Civic Ledger chrome registers an entry here
// as {id, label, routePrefixes, sidebarWorkspaceKey, chrome}; Industry pages must not (§6.5).
frappe.provide("kentender_core.cl_surface_registry");

(function () {
	"use strict";

	/**
	 * Route slugs (lower case, first path segment) → surface metadata.
	 * Registered surfaces: none.
	 */
	var surfaces = {
		/* Budget & Funding (kentender_budget) is rebuilt per BUD-CHG-001 v1.2 as
		   Industry-design Vue-in-Desk pages with their own PageRail.vue chrome —
		   deliberately NOT registered here, matching kentender_strategy's three
		   production pages and kentender_core's reference_data page. Registering
		   would let this legacy Civic Ledger router repaint a second, clashing
		   toolbar on every in-page route change. See AGENTS.md §6.5. */
		/* Demands (DEM-UI-01/02/04/09/10) was removed in NDS-CHG-001 v1.1 Phase 8.
		   Departmental Needs replaced that module outright; its Pages
		   (demands-workspace, demand-form, demand-review, demand-detail,
		   demand-performance) no longer exist on any site, so these five entries
		   only claimed routes that resolve to nothing. NDS-BR-020 / NDS-AC-030
		   forbid keeping a legacy Demand route, alias or fixture. */
		/* PLN-CHG-001 v1.2 — Procurement Planning intentionally has no entry
		   here. Like Departmental Needs below, it is an Industry-design-system
		   Vue-in-Desk page rendering its own rail; the seven Stitch-era PLN-UI-*
		   surfaces (and their pages) were demolished in its Phase 3. */
		// NDS-CHG-001 v1.1 — Departmental Needs intentionally has no entry here.
		// It is an Industry-design-system page (Barlow tokens, kt_industry_tokens.css
		// + departmental_needs_industry.css) with its own rail, mounted through
		// kentender_core.industry.mountPageRail — not a Civic Ledger one. Registering
		// it lets kt_cl_shell_router.js's global "change" listener resolve the route
		// and force-render this registry's Civic Ledger toolbar into
		// #kt-cl-chrome-host on every route settle, including the in-page segment
		// navigation the single "departmental-needs" Page does for all eight NDS-UI
		// routes — after departmental_needs_page.js's one-time clear of that host.
		//
		// Five entries (NDS-UI-01/02A/02B/02C/03) lived here until Phase 8. They were
		// added under the retired NDS-CHG-002 Civic Ledger build and four of them
		// named routes that no longer exist (departmental-needs-new/-edit/-review/
		// -detail, deleted in Phase 7). Their comment argued registration was needed
		// because an unresolved route makes onRouteChange call leaveNative() — true,
		// but harmless for an Industry page: leaveNative() only drops the
		// kt-cl-shell/-native body classes and removes the chrome host, and the
		// native sidebar is hidden by body.kt-cl-shell:not(.kt-cl-shell-native)
		// .body-sidebar-container, so losing both classes leaves the rail visible.
		// departmental_needs_page.js hides .navbar/.page-head with its own inline
		// !important styles, which leaveNative() does not touch. This matches
		// Reference Data (below), Budget & Funding and Strategy, none of which are
		// registered here.

		// CFG-CHG-002 — Reference Data intentionally has no "CFG-PEFY-UI" entry here.
		// It's an Industry-design-system page (Barlow tokens, kt_industry_tokens.css),
		// not a Civic Ledger one (Tailwind/Material Symbols) — registering it would let
		// kt_cl_shell_router.js's global route listener auto-render this registry's
		// Civic Ledger toolbar into #kt-cl-chrome-host on every route settle (the same
		// hazard documented above for Departmental Needs), which visually clashes
		// with kt_industry/components/PageRail.vue, the page's own DES-12 rail.
		// reference_data_page.js still calls cl_shell.enterNative() directly (for the
		// shared "procurement" sidebar only, no toolbar), so the sidebar keeps working
		// without this page ever being resolvable by resolveFromRoute().
	};

	function routeKey(route) {
		var r = route || (typeof frappe !== "undefined" && frappe.get_route ? frappe.get_route() : []) || [];
		if (!r.length) return "";
		if (r[0] === "Form" && r.length >= 2) {
			return ("Form/" + r[1]).toLowerCase();
		}
		return String(r[0] || "").toLowerCase();
	}

	kentender_core.cl_surface_registry = {
		surfaces: surfaces,

		/** Registered screen IDs, in registration order. */
		allIds: function () {
			return Object.keys(surfaces);
		},

		get: function (id) {
			return surfaces[id] || null;
		},

		resolveFromRoute: function (route) {
			var key = routeKey(route);
			if (!key) return null;
			var ids = Object.keys(surfaces);
			for (var i = 0; i < ids.length; i++) {
				var surface = surfaces[ids[i]];
				var prefixes = (surface.routePrefixes || []).map(function (p) {
					return String(p).toLowerCase();
				});
				if (prefixes.indexOf(key) >= 0) {
					return surface;
				}
				/* Also match path prefixes like procurement-planning/plans */
				for (var j = 0; j < prefixes.length; j++) {
					if (key === prefixes[j] || key.indexOf(prefixes[j] + "/") === 0) {
						return surface;
					}
				}
			}
			return null;
		},
	};

	frappe.provide("kentender_core.cl");
	kentender_core.cl.surface_registry = kentender_core.cl_surface_registry;
})();
