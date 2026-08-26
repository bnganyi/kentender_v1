// PLN-UI-03 Plan builder (empty Draft) — Stitch shell + live builder API.
(function () {
	"use strict";

	var PAGE_SLUG = "procurement-plan-builder";

	function activateSurface() {
		document.body.classList.add("kt-pln-surface", "kt-pln-builder-active");
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
					{ label: __("Plan builder") },
				],
				showSearch: false,
				showUserMeta: true,
			},
		});
	}

	function planFromRoute() {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]);
		}
		if (frappe.route_options && frappe.route_options.plan) {
			return String(frappe.route_options.plan);
		}
		var q = frappe.utils.get_query_params
			? frappe.utils.get_query_params()
			: {};
		if (q && q.plan) {
			return q.plan;
		}
		// Fallback: /app/procurement-plan-builder?plan=X may land as query on location.
		try {
			var params = new URLSearchParams(window.location.search || "");
			return params.get("plan") || "";
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
			typeof kentender_procurement.ui_fixtures.planning_builder === "function"
				? kentender_procurement.ui_fixtures.planning_builder()
				: '<div class="p-4 text-danger">' + __("Planning builder fixture missing.") + "</div>";
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		var $root = page.main.find('[data-testid="kt-pln-ui03-root"]');
		page._ktPlnBuilderMounted = true;
		page._ktPlnBuilderActive = true;
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningBuilder === "function"
		) {
			kentender_procurement.live.bindPlanningBuilder($root, { plan: planFromRoute() });
		}
	}

	function mountWithDeps(page) {
		// on_page_load's frappe.require() is async, but Frappe can call
		// on_page_show synchronously right after on_page_load returns, before
		// that async load resolves — without a guard, on_page_show's own
		// "not yet mounted" check would ALSO fire mountWithDeps, doubling the
		// mount() (and its API call). The loading flag makes on_page_show a
		// no-op while on_page_load's own require is already in flight.
		if (page._ktPlnBuilderLoading) {
			return;
		}
		page._ktPlnBuilderLoading = true;
		frappe.require(
			[
				"/assets/kentender_procurement/js/planning_client_utils.js",
				"/assets/kentender_procurement/js/planning_ui_fixtures/builder.js",
				"/assets/kentender_procurement/js/planning_builder_bind.js",
				"/assets/kentender_procurement/js/planning_ui_fixtures/remove_plan_item_dialog.js",
				"/assets/kentender_procurement/js/planning_removal_dialog.js",
				"/assets/kentender_procurement/js/planning_ui_fixtures/empty_update_cancel.js",
				"/assets/kentender_procurement/js/planning_empty_update_dialog.js",
				"/assets/kentender_procurement/js/planning_ui_fixtures/finance_confirm_drawer.js",
				"/assets/kentender_procurement/js/planning_finance_bind.js",
			],
			function () {
				page._ktPlnBuilderLoading = false;
				mount(page);
			}
		);
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		activateSurface();
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Plan builder"),
			single_column: true,
		});
		wrapper.page = page;
		page._ktPlnBuilderMounted = false;
		mountWithDeps(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (!wrapper.page) {
			return;
		}
		activateSurface();
		var $root = wrapper.page.main.find('[data-testid="kt-pln-ui03-root"]');
		if (!wrapper.page._ktPlnBuilderMounted || !$root.length) {
			mountWithDeps(wrapper.page);
			return;
		}
		enterShell();
		if (wrapper.page._ktPlnBuilderActive) {
			return;
		}
		wrapper.page._ktPlnBuilderActive = true;
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningBuilder === "function"
		) {
			kentender_procurement.live.bindPlanningBuilder($root, { plan: planFromRoute() });
		}
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function (wrapper) {
		if (wrapper.page) wrapper.page._ktPlnBuilderActive = false;
		$('[data-testid="kt-pln-ui03-root"]').trigger("kt:teardown").off(".ktPlnBuilderRevision").attr("data-kt-request-id", "-1");
		document.body.classList.remove("kt-pln-builder-active", "kt-pln-surface");
	};
})();
