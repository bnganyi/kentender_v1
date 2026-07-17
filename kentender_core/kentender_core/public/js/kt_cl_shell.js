// Civic Ledger desk shell — layout from B-Components/code.html lines 309-335
frappe.provide("kentender_core.cl_shell");

(function () {
	"use strict";

	var SHELL_CLASS = "kt-cl-shell";
	var HYDRATION_CLASS = "kt-cl-hydration-pending";
	var PREPAINT_STYLE_ID = "kt-cl-shell-prepaint";

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

	function mountSidebar(workspaceKey, sidebarOpts) {
		if (kentender_core.cl_sidebar && typeof kentender_core.cl_sidebar.mount === "function") {
			kentender_core.cl_sidebar.mount(workspaceKey, sidebarOpts || {});
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

			if (hydrationGate) {
				injectPrepaintStyle();
				document.body.classList.add(HYDRATION_CLASS);
			}

			document.body.classList.add(SHELL_CLASS);
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
			document.body.classList.remove(HYDRATION_CLASS);
			if (kentender_core.cl_sidebar && typeof kentender_core.cl_sidebar.unmount === "function") {
				kentender_core.cl_sidebar.unmount();
			}
			$(".kt-cl-canvas").remove();
			return this;
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

			// code.html lines 309-335
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
	};

	frappe.provide("kentender_core.cl");
	kentender_core.cl.shell = kentender_core.cl_shell;
})();
