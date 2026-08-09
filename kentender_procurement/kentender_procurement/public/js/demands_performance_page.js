// DEM-UI-10 Demand performance — Stitch shell + live API bind.
// Do NOT remount on every on_page_show.
(function () {
	"use strict";

	var PAGE_SLUG = "demand-performance";
	var SURFACE_ID = "DEM-UI-10";

	function surface() {
		var reg = kentender_core.cl_surface_registry;
		return reg && typeof reg.get === "function" ? reg.get(SURFACE_ID) : null;
	}

	function activateSurface() {
		document.body.classList.add("kt-dem-surface", "kt-dem-perf-active");
	}

	function enterShell() {
		var sh = kentender_core.cl_shell;
		var surf = surface();
		if (!sh || typeof sh.enterNative !== "function") {
			return;
		}
		sh.enterNative({
			sidebarWorkspaceKey: (surf && surf.sidebarWorkspaceKey) || "procurement",
			toolbar:
				(surf && surf.chrome && surf.chrome.toolbar) || {
					breadcrumbs: [
						{ label: __("Home"), route: ["coming-soon"] },
						{ label: __("Demands"), route: ["demands-workspace"] },
						{ label: __("Demand Performance") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			chrome: surf && surf.chrome,
		});
	}

	function mount(page) {
		activateSurface();
		var sh = kentender_core.cl_shell;
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html(
				'<div class="p-4 text-danger">' + __("Civic Ledger shell is not loaded.") + "</div>"
			);
			return;
		}
		enterShell();
		var html =
			kentender_procurement.ui_fixtures &&
			typeof kentender_procurement.ui_fixtures.demand_performance === "function"
				? kentender_procurement.ui_fixtures.demand_performance()
				: '<div class="p-4 text-danger">' + __("Demand performance fixture missing.") + "</div>";
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		var $root = page.main.find('[data-testid="kt-dem-ui10-root"]');
		page._ktDemPerfMounted = true;
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindDemandPerformance === "function"
		) {
			kentender_procurement.live.bindDemandPerformance($root);
		}
	}

	frappe.pages[PAGE_SLUG] = frappe.pages[PAGE_SLUG] || {};

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		activateSurface();
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Demand Performance"),
			single_column: true,
		});
		wrapper.page = page;
		page._ktDemPerfMounted = false;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (!wrapper.page) {
			return;
		}
		activateSurface();
		var $root = wrapper.page.main.find('[data-testid="kt-dem-ui10-root"]');
		if (!wrapper.page._ktDemPerfMounted || !$root.length) {
			mount(wrapper.page);
			return;
		}
		enterShell();
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindDemandPerformance === "function"
		) {
			kentender_procurement.live.bindDemandPerformance($root);
		}
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-dem-perf-active");
	};
})();
