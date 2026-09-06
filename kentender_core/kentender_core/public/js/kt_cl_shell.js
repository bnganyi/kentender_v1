// Civic Ledger desk shell — layout from B-Components/code.html lines 309-335
// Step 2: native-sidebar mode keeps Frappe .body-sidebar; replaces top chrome only.
frappe.provide("kentender_core.cl_shell");

(function () {
	"use strict";

	var SHELL_CLASS = "kt-cl-shell";
	var NATIVE_CLASS = "kt-cl-shell-native";
	var HYDRATION_CLASS = "kt-cl-hydration-pending";
	var PREPAINT_STYLE_ID = "kt-cl-shell-prepaint";
	var NATIVE_PREPAINT_STYLE_ID = "kt-cl-shell-native-prepaint";
	var CHROME_HOST_ID = "kt-cl-chrome-host";
	var routeToken = 0;
	var nativeActive = false;

	function components() {
		return kentender_core.cl_components || null;
	}

	function injectPrepaintStyle() {
		if (document.getElementById(PREPAINT_STYLE_ID)) return;
		var style = document.createElement("style");
		style.id = PREPAINT_STYLE_ID;
		style.textContent =
			"body.kt-cl-hydration-pending .body-sidebar-container," +
			"body.kt-cl-hydration-pending .navbar," +
			"body.kt-cl-hydration-pending .page-head{display:none!important;}" +
			"body.kt-cl-hydration-pending .kt-cl-canvas{visibility:hidden;}";
		(document.head || document.documentElement).appendChild(style);
	}

	function injectNativePrepaintStyle() {
		if (document.getElementById(NATIVE_PREPAINT_STYLE_ID)) return;
		var style = document.createElement("style");
		style.id = NATIVE_PREPAINT_STYLE_ID;
		/* Native mode: hide only top chrome during hydration — keep sidebar visible. */
		style.textContent =
			"body.kt-cl-hydration-pending.kt-cl-shell-native .navbar," +
			"body.kt-cl-hydration-pending.kt-cl-shell-native .page-head{display:none!important;}" +
			"body.kt-cl-hydration-pending.kt-cl-shell-native #kt-cl-chrome-host{visibility:hidden;}";
		(document.head || document.documentElement).appendChild(style);
	}

	function mountSidebar(workspaceKey, sidebarOpts) {
		if (kentender_core.cl_sidebar && typeof kentender_core.cl_sidebar.mount === "function") {
			kentender_core.cl_sidebar.mount(workspaceKey, sidebarOpts || {});
		}
	}

	function ensureChromeHost() {
		var existing = document.getElementById(CHROME_HOST_ID);
		if (existing) return existing;

		var host = document.createElement("div");
		host.id = CHROME_HOST_ID;
		host.setAttribute("data-testid", "kt-cl-chrome-host");

		var insertTarget =
			document.querySelector(".main-section") ||
			document.querySelector(".page-container") ||
			document.querySelector(".layout-main-section") ||
			document.body;

		var pageHead = insertTarget.querySelector(".page-head");
		if (pageHead && pageHead.parentNode === insertTarget) {
			insertTarget.insertBefore(host, pageHead);
		} else {
			insertTarget.insertBefore(host, insertTarget.firstChild);
		}
		return host;
	}

	function removeChromeHost() {
		var host = document.getElementById(CHROME_HOST_ID);
		if (host && host.parentNode) {
			host.parentNode.removeChild(host);
		}
	}

	function ensureNativeSidebar(sidebarWorkspaceKey) {
		var key = (sidebarWorkspaceKey || "procurement").toLowerCase();
		// setup() uses the argument as the visible header title — never pass the
		// lowercased boot key (that renders "procurement" instead of "Procurement").
		var bootItem =
			frappe.boot &&
			frappe.boot.workspace_sidebar_item &&
			frappe.boot.workspace_sidebar_item[key];
		var title = (bootItem && (bootItem.label || bootItem.title)) || sidebarWorkspaceKey || "Procurement";
		try {
			if (
				frappe.app &&
				frappe.app.sidebar &&
				typeof frappe.app.sidebar.setup === "function"
			) {
				// setup() tears the whole workspace rail down and rebuilds it.
				// Every in-page segment navigation re-enters here through the
				// page controller's on_page_show (e.g. an editor's first save
				// replacing /new with /{reference}/edit), and the rebuild made
				// the rail visibly flash on each one. The rail only needs
				// building when it is missing or showing another workspace.
				var railBuilt =
					frappe.app.sidebar.sidebar_title === title &&
					document.querySelector(".body-sidebar .sidebar-item-container");
				if (!railBuilt) {
					frappe.app.sidebar.setup(title);
				}
			}
		} catch (e) {
			/* ignore — boot fast-path may already have the rail */
		}
	}

	kentender_core.cl_shell = {
		enter: function (opts) {
			opts = opts || {};
			var workspaceKey = opts.workspaceKey || opts.sidebarKey || "Procurement";
			var hydrationGate = opts.hydrationGate !== false;
			var sidebarOpts = opts.sidebar || {
				portalTitle: opts.portalTitle,
				portalSubtitle: opts.portalSubtitle,
				avatarUrl: opts.avatarUrl,
				avatarInitials: opts.avatarInitials,
			};

			/* Leave native mode if switching to full-replacement POC shell. */
			if (nativeActive) {
				this.leaveNative();
			}

			if (hydrationGate) {
				injectPrepaintStyle();
				document.body.classList.add(HYDRATION_CLASS);
			}

			document.body.classList.add(SHELL_CLASS);
			document.body.classList.remove(NATIVE_CLASS);
			mountSidebar(workspaceKey, sidebarOpts);

			if (hydrationGate) {
				requestAnimationFrame(function () {
					document.body.classList.remove(HYDRATION_CLASS);
				});
			}

			return this;
		},

		leave: function () {
			document.body.classList.remove(SHELL_CLASS);
			document.body.classList.remove(NATIVE_CLASS);
			document.body.classList.remove(HYDRATION_CLASS);
			nativeActive = false;
			if (kentender_core.cl_sidebar && typeof kentender_core.cl_sidebar.unmount === "function") {
				kentender_core.cl_sidebar.unmount();
			}
			$(".kt-cl-canvas").remove();
			removeChromeHost();
			return this;
		},

		/**
		 * Step 2 native-sidebar mode: keep Frappe .body-sidebar, replace top chrome.
		 * Adds both kt-cl-shell (Tailwind scope) and kt-cl-shell-native (keep rail).
		 */
		enterNative: function (opts) {
			opts = opts || {};
			// Only the first genuine entry into native mode needs to hide-then-
			// reveal the raw Frappe chrome (navbar/page-head/chrome host) while
			// the custom UI hydrates. `enterNative()` is called again on every
			// in-page route change within an already-native page (e.g. a save
			// replacing /new with /{reference}/edit via frappe.set_route(),
			// which re-fires on_page_show — see AGENTS.md §6.1) — chrome is
			// already hidden/replaced by then, so re-running the hide/reveal
			// cycle only repaints it and reads as a visible flash on every save.
			// Same fix already applied to the sidebar rail below (ensureNativeSidebar).
			var hydrationGate = opts.hydrationGate !== false && !nativeActive;
			var token = ++routeToken;

			/* Tear down full-replacement custom sidenav if present. */
			if (kentender_core.cl_sidebar && typeof kentender_core.cl_sidebar.unmount === "function") {
				kentender_core.cl_sidebar.unmount();
			}
			$(".kt-cl-canvas").filter(function () {
				return !$(this).closest("#" + CHROME_HOST_ID).length;
			}).remove();

			if (hydrationGate) {
				injectNativePrepaintStyle();
				document.body.classList.add(HYDRATION_CLASS);
			}

			document.body.classList.add(SHELL_CLASS);
			document.body.classList.add(NATIVE_CLASS);
			nativeActive = true;

			ensureChromeHost();
			ensureNativeSidebar(opts.sidebarWorkspaceKey);

			if (opts.toolbar || (opts.chrome && opts.chrome.toolbar)) {
				this.updateChrome({
					toolbar: opts.toolbar || (opts.chrome && opts.chrome.toolbar) || {},
				});
			}

			if (hydrationGate) {
				requestAnimationFrame(function () {
					if (token !== routeToken) return;
					document.body.classList.remove(HYDRATION_CLASS);
				});
			}

			return this;
		},

		leaveNative: function () {
			routeToken += 1;
			document.body.classList.remove(NATIVE_CLASS);
			document.body.classList.remove(SHELL_CLASS);
			document.body.classList.remove(HYDRATION_CLASS);
			nativeActive = false;
			removeChromeHost();
			return this;
		},

		isNativeActive: function () {
			return nativeActive;
		},

		getRouteToken: function () {
			return routeToken;
		},

		isStaleToken: function (token) {
			return token !== routeToken;
		},

		/**
		 * Update persistent toolbar inside #kt-cl-chrome-host (in-place).
		 * pageHeader is applied via mountContent into page.main.
		 */
		updateChrome: function (opts) {
			opts = opts || {};
			var comp = components();
			if (!comp) return null;

			var host = ensureChromeHost();
			var toolbarOpts = opts.toolbar || {};
			host.innerHTML = comp.renderTopToolbar(toolbarOpts);
			comp.bindBreadcrumbRoutes(host);
			return host;
		},

		/**
		 * Mount page header + body content into a page container (typically page.main).
		 * Toolbar stays in #kt-cl-chrome-host; this only owns the content area.
		 */
		mountContent: function (container, opts) {
			opts = opts || {};
			var comp = components();
			if (!comp) return null;

			var $host = container && container.jquery ? container : $(container);
			if (!$host || !$host.length) return null;

			var pageHeaderOpts = opts.pageHeader || opts.header || {};
			var mainHtml = opts.mainHtml || "";

			var html =
				'<div class="kt-cl-native-canvas flex flex-col min-h-0" data-testid="kt-cl-page-root">' +
				'<main class="flex-1 p-4 md:p-6 overflow-y-auto bg-surface-bright">' +
				'<div class="max-w-[1280px] mx-auto space-y-4">' +
				'<div id="kt-cl-page-header-host">' +
				comp.renderPageHeader(pageHeaderOpts) +
				"</div>" +
				'<div data-testid="kt-cl-page-body">' +
				mainHtml +
				"</div>" +
				"</div></main></div>";

			$host.html(html);
			comp.bindBreadcrumbRoutes($host);
			return $host;
		},

		/** Update only the page-header host inside a previously mounted content area. */
		updatePageChrome: function (container, pageHeaderOpts) {
			var comp = components();
			if (!comp) return null;
			var $host = container && container.jquery ? container : $(container);
			if (!$host || !$host.length) return null;
			var $headerHost = $host.find("#kt-cl-page-header-host");
			if (!$headerHost.length) {
				return this.mountContent($host, { pageHeader: pageHeaderOpts, mainHtml: "" });
			}
			$headerHost.html(comp.renderPageHeader(pageHeaderOpts || {}));
			comp.bindBreadcrumbRoutes($host);
			return $host;
		},

		mountPageChrome: function (container, opts) {
			opts = opts || {};
			var comp = components();
			if (!comp) return null;

			var $host = container && container.jquery ? container : $(container);
			if (!$host || !$host.length) return null;

			var toolbarOpts = opts.toolbar || {};
			var pageHeaderOpts = opts.pageHeader || opts.header || {};
			var mainHtml = opts.mainHtml || "";

			// code.html lines 309-335 (full-replacement POC path)
			var html =
				'<div class="kt-cl-canvas flex flex-col min-h-screen" data-testid="kt-cl-page-root">' +
				comp.renderTopToolbar(toolbarOpts) +
				'<main class="flex-1 p-4 md:p-6 overflow-y-auto bg-surface-bright">' +
				'<div class="max-w-[1280px] mx-auto space-y-4">' +
				comp.renderPageHeader(pageHeaderOpts) +
				mainHtml +
				"</div></main></div>";

			$host.html(html);
			comp.bindBreadcrumbRoutes($host);
			return $host;
		},

		setupSidebar: mountSidebar,
		ensureNativeSidebar: ensureNativeSidebar,
	};

	frappe.provide("kentender_core.cl");
	kentender_core.cl.shell = kentender_core.cl_shell;
})();
