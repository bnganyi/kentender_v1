// PLN-UI-06 Plan Item editor — Stitch shell + live editor API.
(function () {
	"use strict";

	var PAGE_SLUG = "procurement-plan-item-editor";

	function activateSurface() {
		document.body.classList.add("kt-pln-surface", "kt-pln-editor-active");
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
					{ label: __("Procurement Planning"), route: ["planning-workspace"] },
					{ label: __("Plan Item") },
				],
				showSearch: false,
				showUserMeta: true,
			},
		});
	}

	function planItemFromRoute() {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]);
		}
		if (frappe.route_options && frappe.route_options.plan_item) {
			return String(frappe.route_options.plan_item);
		}
		var q = frappe.utils.get_query_params ? frappe.utils.get_query_params() : {};
		if (q && q.plan_item) {
			return q.plan_item;
		}
		try {
			return new URLSearchParams(window.location.search || "").get("plan_item") || "";
		} catch (e) {
			return "";
		}
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
			typeof kentender_procurement.ui_fixtures.planning_plan_item_editor === "function"
				? kentender_procurement.ui_fixtures.planning_plan_item_editor()
				: '<div class="p-4 text-danger">' + __("Plan Item editor fixture missing.") + "</div>";
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		var $root = page.main.find('[data-testid="kt-pln-ui06-root"]');
		page._ktPlnEditorMounted = true;
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningItemEditor === "function"
		) {
			kentender_procurement.live.bindPlanningItemEditor($root, {
				plan_item: planItemFromRoute(),
			});
		}
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		activateSurface();
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Plan Item editor"),
			single_column: true,
		});
		wrapper.page = page;
		page._ktPlnEditorMounted = false;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (!wrapper.page) {
			return;
		}
		activateSurface();
		var $root = wrapper.page.main.find('[data-testid="kt-pln-ui06-root"]');
		if (!wrapper.page._ktPlnEditorMounted || !$root.length) {
			mount(wrapper.page);
			return;
		}
		enterShell();
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningItemEditor === "function"
		) {
			kentender_procurement.live.bindPlanningItemEditor($root, {
				plan_item: planItemFromRoute(),
			});
		}
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-pln-editor-active");
	};
})();
