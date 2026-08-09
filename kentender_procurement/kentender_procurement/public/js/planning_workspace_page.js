// PLN-UI-01 Procurement Planning workspace — Stitch shell + live API data.
(function () {
	"use strict";

	// Page slug must not collide with Workspace "Procurement Planning" URL.
	var PAGE_SLUG = "planning-workspace";

	function activateSurface() {
		document.body.classList.add("kt-pln-surface", "kt-pln-ws-active");
	}

	function enterShell() {
		var sh = kentender_core.cl_shell;
		if (!sh || typeof sh.enterNative !== "function") {
			return;
		}
		sh.enterNative({
			sidebarWorkspaceKey: "procurement",
			toolbar: {
				breadcrumbs: [
					{ label: __("Home"), route: ["coming-soon"] },
					{ label: __("Procurement Planning") },
				],
				showSearch: false,
				showUserMeta: true,
			},
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
			typeof kentender_procurement.ui_fixtures.planning_workspace === "function"
				? kentender_procurement.ui_fixtures.planning_workspace()
				: '<div class="p-4 text-danger">' + __("Planning workspace fixture missing.") + "</div>";
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		var $root = page.main.find('[data-testid="kt-pln-ui01-root"]');
		page._ktPlnWorkspaceMounted = true;
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningWorkspace === "function"
		) {
			kentender_procurement.live.bindPlanningWorkspace($root);
		}
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		activateSurface();
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Procurement Planning"),
			single_column: true,
		});
		wrapper.page = page;
		page._ktPlnWorkspaceMounted = false;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (!wrapper.page) {
			return;
		}
		activateSurface();
		var $root = wrapper.page.main.find('[data-testid="kt-pln-ui01-root"]');
		if (!wrapper.page._ktPlnWorkspaceMounted || !$root.length) {
			mount(wrapper.page);
			return;
		}
		enterShell();
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningWorkspace === "function"
		) {
			kentender_procurement.live.bindPlanningWorkspace($root);
		}
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-pln-ws-active");
	};
})();
