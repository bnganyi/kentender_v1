// DEM-UI-09 / 09A–D Approved Demand detail — Stitch shell + live API bind.
// Do NOT remount on every on_page_show.
(function () {
	"use strict";

	var PAGE_SLUG = "demand-detail";
	var SURFACE_ID = "DEM-UI-09";

	function surface() {
		var reg = kentender_core.cl_surface_registry;
		return reg && typeof reg.get === "function" ? reg.get(SURFACE_ID) : null;
	}

	function routeDemandId() {
		var route = (frappe.get_route && frappe.get_route()) || [];
		return route.length > 1 ? String(route[1] || "") : "";
	}

	function activateSurface() {
		document.body.classList.add("kt-dem-surface", "kt-dem-detail-active");
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
						{ label: __("Demand Detail") },
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
		var id = routeDemandId();
		if (!id) {
			sh.mountContent(page.main, {
				mainHtml:
					'<div class="p-6" data-testid="kt-dem-ui09-missing">' +
					__("Open an Approved Demand from the Demands workspace.") +
					' <a href="/desk/demands-workspace">' +
					__("Back to Demands") +
					"</a></div>",
				pageHeader: { title: "", hidden: true },
			});
			page._ktDemDetailMounted = true;
			page._ktDemDetailId = "";
			return;
		}
		var html =
			kentender_procurement.ui_fixtures &&
			typeof kentender_procurement.ui_fixtures.demand_detail === "function"
				? kentender_procurement.ui_fixtures.demand_detail()
				: '<div class="p-4 text-danger">' + __("Demand detail fixture missing.") + "</div>";
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		var $root = page.main.find('[data-testid="kt-dem-ui09-root"]');
		page._ktDemDetailMounted = true;
		page._ktDemDetailId = id;
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindDemandDetail === "function"
		) {
			kentender_procurement.live.bindDemandDetail($root, id).catch(function (err) {
				console.warn("Demand detail bind failed", err);
			});
		}
	}

	function ensureMounted(wrapper) {
		if (!wrapper || !wrapper.page) {
			return;
		}
		activateSurface();
		var id = routeDemandId();
		var $root = wrapper.page.main.find('[data-testid="kt-dem-ui09-root"]');
		var idChanged = String(wrapper.page._ktDemDetailId || "") !== String(id || "");
		if (wrapper.page._ktDemDetailMounted && $root.length && !idChanged && id) {
			enterShell();
			if (
				kentender_procurement.live &&
				typeof kentender_procurement.live.bindDemandDetail === "function"
			) {
				kentender_procurement.live.bindDemandDetail($root, id).catch(function (err) {
					console.warn("Demand detail rebind failed", err);
				});
			}
			return;
		}
		mount(wrapper.page);
	}

	frappe.pages[PAGE_SLUG] = frappe.pages[PAGE_SLUG] || {};
	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		activateSurface();
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Demand Detail"),
			single_column: true,
		});
		wrapper.page = page;
		page._ktDemDetailMounted = false;
		page._ktDemDetailId = "";
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		ensureMounted(wrapper);
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-dem-detail-active");
	};
})();
