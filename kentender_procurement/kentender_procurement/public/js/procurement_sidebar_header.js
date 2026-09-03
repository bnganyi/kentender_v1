// Procurement rail header: title stays "Procurement"; subtitle must be "KenTender".
// Frappe's choose_app_name overwrites app_title with Desktop Icon.parent_icon when
// a matching icon exists — even when parent_icon is null — which blanks the subtitle.
//
// Also harmonizes Workspace Sidebar active matching:
// 1) coming-soon?feature=… links must not all share one active state (Frappe strips query)
// 2) Workspace hubs and their child pages map to rail items
// 3) Workspace `url` overrides slug path (Plans → /desk/planning-hub)
(function () {
	"use strict";

	function applyKenTenderSubtitle(sidebar) {
		if (!sidebar || (sidebar.sidebar_title || "") !== "Procurement") {
			return;
		}
		sidebar.header_subtitle = "KenTender";
		var $sub = sidebar.wrapper && sidebar.wrapper.find(".header-subtitle");
		if ($sub && $sub.length) {
			$sub.text("KenTender");
		}
	}

	function patchSidebar() {
		if (!frappe.ui || !frappe.ui.Sidebar || frappe.ui.Sidebar.prototype.__ktProcHeaderPatched) {
			return;
		}
		var original = frappe.ui.Sidebar.prototype.choose_app_name;
		frappe.ui.Sidebar.prototype.choose_app_name = function () {
			original.apply(this, arguments);
			if ((this.sidebar_title || "") === "Procurement") {
				this.header_subtitle = "KenTender";
			} else if (this.header_subtitle == null || this.header_subtitle === "") {
				// Avoid blank subtitle when Desktop Icon.parent_icon is empty.
				var app = frappe.boot && frappe.boot.app_data;
				if (app && app.length && app[0].app_title) {
					this.header_subtitle = app[0].app_title;
				}
			}
		};
		frappe.ui.Sidebar.prototype.__ktProcHeaderPatched = true;
	}

	function patchHeaderMake() {
		if (!frappe.ui || !frappe.ui.SidebarHeader || frappe.ui.SidebarHeader.prototype.__ktProcHeaderPatched) {
			return;
		}
		var originalMake = frappe.ui.SidebarHeader.prototype.make;
		frappe.ui.SidebarHeader.prototype.make = function () {
			if (this.sidebar && (this.sidebar.sidebar_title || "") === "Procurement") {
				this.sidebar.header_subtitle = "KenTender";
			}
			originalMake.apply(this, arguments);
			applyKenTenderSubtitle(this.sidebar);
		};
		frappe.ui.SidebarHeader.prototype.__ktProcHeaderPatched = true;
	}

	/** Prefer explicit hub `url` over Workspace slug (Frappe only checks `route`). */
	function patchWorkspaceGetPath() {
		var TypeLink = frappe.ui && frappe.ui.sidebar_item && frappe.ui.sidebar_item.TypeLink;
		if (!TypeLink || TypeLink.prototype.__ktProcPathPatched) {
			return;
		}
		var original = TypeLink.prototype.get_path;
		TypeLink.prototype.get_path = function () {
			var path = original.apply(this, arguments);
			if (this.item && this.item.link_type === "Workspace" && this.item.url) {
				return this.item.url;
			}
			return path;
		};
		TypeLink.prototype.__ktProcPathPatched = true;
	}

	/**
	 * A `URL` sidebar item is rendered by Frappe with a hard `target="_blank"`
	 * (sidebar_item.html), so an in-app Desk sub-route such as
	 * `/desk/departmental-needs/intake-window` opens a second browser tab.
	 * A sub-route cannot be expressed as a `Page` link — `link_to` is a Dynamic
	 * Link validated against a real Page record — so the rail keeps `URL` and the
	 * target is dropped for same-origin paths. Frappe's own body click handler
	 * then push-states it (router.js), giving normal in-place navigation.
	 * External `http(s)` URLs keep opening in a new tab.
	 */
	function patchInternalUrlTarget() {
		var TypeLink = frappe.ui && frappe.ui.sidebar_item && frappe.ui.sidebar_item.TypeLink;
		if (!TypeLink || TypeLink.prototype.__ktProcTargetPatched) {
			return;
		}
		var originalMake = TypeLink.prototype.make;
		TypeLink.prototype.make = function () {
			originalMake.apply(this, arguments);
			var url = (this.item && this.item.link_type === "URL" && this.item.url) || "";
			// Relative in-app path only; "//host" is protocol-relative and external.
			if (!/^\/[^/]/.test(url) || !this.wrapper) {
				return;
			}
			this.wrapper.find("a.item-anchor").removeAttr("target").removeAttr("rel");
		};
		TypeLink.prototype.__ktProcTargetPatched = true;
	}

	function stripTrailingSlash(s) {
		return (s || "").replace(/\/$/, "");
	}

	function hrefParts(rawHref) {
		var href = decodeURIComponent(rawHref || "");
		var qIdx = href.indexOf("?");
		var hIdx = href.indexOf("#");
		var end = href.length;
		if (qIdx >= 0) end = Math.min(end, qIdx);
		if (hIdx >= 0) end = Math.min(end, hIdx);
		var path = stripTrailingSlash(href.slice(0, end));
		var feature = "";
		if (qIdx >= 0) {
			var query = href.slice(qIdx + 1, hIdx >= 0 ? hIdx : undefined);
			var params = new URLSearchParams(query);
			feature = params.get("feature") || "";
		}
		return { path: path, feature: feature };
	}

	function currentFeature() {
		try {
			var fromSearch = new URLSearchParams(window.location.search || "").get("feature");
			if (fromSearch) return fromSearch;
		} catch (e) {
			/* ignore */
		}
		if (frappe.route_options && frappe.route_options.feature != null) {
			return String(frappe.route_options.feature);
		}
		return "";
	}

	/**
	 * Hub / child-route equivalents for active matching.
	 *
	 * `exact` distinguishes the two sides of the comparison. The current
	 * *path* expands by prefix — any sub-route lights its module hub up. An
	 * item *href* expands only when it IS a hub alias: a sibling sub-route
	 * href (`…/intake-window`, 38 chars) that also expanded by prefix became
	 * "equivalent" to the hub on every departmental-needs route and lit
	 * Intake window up on the workspace itself (observed 2026-08-30 while a
	 * "Review tasks" entry still existed; the asymmetry stays load-bearing
	 * for Intake window).
	 */
	function expandPathEquivalents(path, exact) {
		var out = {};
		function add(p) {
			if (p) out[p] = true;
		}
		add(path);
		var groups = [
			["/desk/kt-procurement-home", "/desk/procurement-home"],
			["/desk/departmental-needs"],
			["/desk/budget-hub", "/desk/budget-management"],
			["/desk/planning-workspace", "/desk/procurement-planning", "/desk/planning-hub"],
			["/desk/strategy-management"],
		];
		for (var g = 0; g < groups.length; g++) {
			var group = groups[g];
			for (var i = 0; i < group.length; i++) {
				if (path === group[i] || (!exact && path.indexOf(group[i] + "/") === 0)) {
					for (var j = 0; j < group.length; j++) add(group[j]);
					break;
				}
			}
		}
		if (/^\/desk\/strategy-builder(\/|$)/.test(path)) add("/desk/strategy-management");
		if (/^\/desk\/budget-workbench(\/|$)/.test(path) || /^\/desk\/budget-builder(\/|$)/.test(path)) {
			add("/desk/budget-hub");
			add("/desk/budget-management");
		}
		// The demand-form/-review/-detail/-performance routes and the workspace
		// they resolved to were all deleted with the Demands module
		// (NDS-CHG-001 v1.1 Phase 8); Departmental Needs owns its own §10 routes
		// and needs no ancestor mapping.
		if (/^\/desk\/it-tender-configuration(?!-dashboard)([/-]|$)/.test(path)) {
			add("/desk/it-tender-configuration-dashboard");
		}
		return Object.keys(out);
	}

	function pathMatches(cleanPath, cleanHref) {
		if (!cleanHref) return false;
		var paths = expandPathEquivalents(cleanPath);
		var hrefs = expandPathEquivalents(cleanHref, true);
		for (var i = 0; i < paths.length; i++) {
			for (var j = 0; j < hrefs.length; j++) {
				var p = paths[i];
				var h = hrefs[j];
				if (p === h || p.indexOf(h + "/") === 0) {
					return true;
				}
			}
		}
		return false;
	}

	var KT_ROUTE_PATCH_VERSION = 4;

	function patchActiveRouteMatching() {
		if (!frappe.ui || !frappe.ui.Sidebar) {
			return;
		}
		if (frappe.ui.Sidebar.prototype.__ktProcRoutePatchVersion === KT_ROUTE_PATCH_VERSION) {
			return;
		}
		frappe.ui.Sidebar.prototype.is_route_in_sidebar = function () {
			var match = false;
			var that = this;
			var cleanPath = stripTrailingSlash(decodeURIComponent(window.location.pathname || ""));
			var liveFeature = currentFeature();
			var bestScore = -1;

			$(".item-anchor").each(function () {
				var raw = $(this).attr("href");
				if (!raw) return;
				var parts = hrefParts(raw);
				var cleanHref = parts.path;
				var isComingSoon = /\/coming-soon$/.test(cleanHref);

				var isActive = false;
				var score = 0;
				if (isComingSoon) {
					// Only match Planned items when we are on coming-soon AND feature equals.
					if (/\/coming-soon$/.test(cleanPath) && parts.feature && parts.feature === liveFeature) {
						isActive = true;
						score = 1000 + parts.feature.length;
					}
				} else if (pathMatches(cleanPath, cleanHref)) {
					isActive = true;
					score = cleanHref.length;
				}

				if (isActive && score >= bestScore) {
					bestScore = score;
					match = true;
					if (that.active_item) that.active_item.removeClass("active-sidebar");
					that.active_item = $(this).parent();
				}
			});
			return match;
		};
		frappe.ui.Sidebar.prototype.__ktProcRoutePatched = true;
		frappe.ui.Sidebar.prototype.__ktProcRoutePatchVersion = KT_ROUTE_PATCH_VERSION;
	}

	/**
	 * Resolve the rail from the route's FIRST segment before Frappe's
	 * entity/module walk. `set_workspace_sidebar` resolves a record route
	 * (`/desk/departmental-needs/NDS-MOH-2027-0003`) through route[1] — the
	 * record reference, never a sidebar — and then falls back through the
	 * current Page's Module Def, landing on whatever module sidebar that walk
	 * produces (observed: the reviewer's rail replaced by Frappe's "Build"
	 * sidebar on a Need detail route). patch_bootinfo already publishes a
	 * boot alias for every KenTender page route key (route[0] → the owning
	 * rail payload), so when one exists it is authoritative. Framework view
	 * routes (form/list/…) keep Frappe's own resolution.
	 */
	var FRAMEWORK_VIEW_SEGMENTS = {
		form: true,
		list: true,
		workspaces: true,
		"query-report": true,
		report: true,
		"dashboard-view": true,
		private: true,
	};

	function patchRouteFirstSidebarResolution() {
		if (!frappe.ui || !frappe.ui.Sidebar || frappe.ui.Sidebar.prototype.__ktProcRouteFirstPatched) {
			return;
		}
		var original = frappe.ui.Sidebar.prototype.set_workspace_sidebar;
		frappe.ui.Sidebar.prototype.set_workspace_sidebar = function () {
			try {
				var seg0 = String((frappe.get_route() || [])[0] || "").toLowerCase();
				var boot = frappe.boot && frappe.boot.workspace_sidebar_item;
				var payload = seg0 && !FRAMEWORK_VIEW_SEGMENTS[seg0] && boot && boot[seg0];
				var canonical = payload && (payload.label || payload.title || payload.name);
				if (canonical) {
					// setup() itself dedupes (patchSetupSkipsRedundantRebuild):
					// same rendered title costs a highlight refresh, not a rebuild.
					frappe.app.sidebar.setup(canonical);
					return;
				}
			} catch (e) {
				/* fall through to Frappe's own resolution */
			}
			return original.apply(this, arguments);
		};
		frappe.ui.Sidebar.prototype.__ktProcRouteFirstPatched = true;
	}

	/**
	 * Frappe rebuilds the whole workspace rail on every router change
	 * (Sidebar.setup_events → set_workspace_sidebar → setup), and the page
	 * controllers' cl_shell.enterNative() adds a second rebuild. Within one
	 * KenTender module every in-page segment navigation — e.g. an editor's
	 * first save replacing /new with /{reference}/edit — therefore tore the
	 * rail down and rebuilt it: a visible flash on every save or click.
	 * When the requested workspace is already rendered, only the active item
	 * needs refreshing. The sidebar editor's edit mode still gets a full
	 * rebuild, as do title changes and an empty rail.
	 */
	function patchSetupSkipsRedundantRebuild() {
		if (!frappe.ui || !frappe.ui.Sidebar || frappe.ui.Sidebar.prototype.__ktProcSetupSkipPatched) {
			return;
		}
		var original = frappe.ui.Sidebar.prototype.setup;
		frappe.ui.Sidebar.prototype.setup = function (workspace_title) {
			try {
				var unchanged =
					this.sidebar_title === workspace_title &&
					this.wrapper &&
					// A hidden rail (e.g. arriving from Desk home) must take the
					// full path so patchSetupShowsRail can reveal it again.
					this.wrapper.is(":visible") &&
					this.wrapper.find(".sidebar-item-container").length > 0;
				var editing = this.editor && this.editor.edit_mode;
				if (unchanged && !editing) {
					if (typeof this.set_active_workspace_item === "function") {
						this.set_active_workspace_item();
					}
					return;
				}
			} catch (e) {
				/* fall through to a full setup */
			}
			return original.apply(this, arguments);
		};
		frappe.ui.Sidebar.prototype.__ktProcSetupSkipPatched = true;
	}

	/**
	 * Desk home leaves `.body-sidebar-container` display:none. Frappe's
	 * `sidebar.setup()` rebuilds the rail but does not `.show()` it, so the first
	 * navigation into a Procurement Page (e.g. Home) looks rail-less until refresh.
	 */
	function patchSetupShowsRail() {
		if (!frappe.ui || !frappe.ui.Sidebar || frappe.ui.Sidebar.prototype.__ktProcSetupShowPatched) {
			return;
		}
		var original = frappe.ui.Sidebar.prototype.setup;
		frappe.ui.Sidebar.prototype.setup = function (workspace_title) {
			original.apply(this, arguments);
			try {
				var page = frappe.container && frappe.container.page && frappe.container.page.page;
				if (page && page.hide_sidebar) {
					return;
				}
				if (this.wrapper && typeof this.wrapper.show === "function") {
					this.wrapper.show();
				}
			} catch (e) {
				/* ignore */
			}
		};
		frappe.ui.Sidebar.prototype.__ktProcSetupShowPatched = true;
	}

	function boot() {
		patchSidebar();
		patchHeaderMake();
		patchWorkspaceGetPath();
		patchInternalUrlTarget();
		patchActiveRouteMatching();
		patchSetupShowsRail();
		patchSetupSkipsRedundantRebuild();
		patchRouteFirstSidebarResolution();
	}

	boot();
	$(document).on("app_ready", boot);
	// TypeLink may load after app_include; retry briefly so Workspace `url` wins.
	setTimeout(boot, 0);
	setTimeout(boot, 250);
})();
