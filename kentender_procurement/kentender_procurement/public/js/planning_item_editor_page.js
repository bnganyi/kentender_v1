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

	function canonicalizePlanItemRoute(planItem) {
		if (!planItem || !window.history || typeof window.history.replaceState !== "function") {
			return;
		}
		var prefix = window.location.pathname.indexOf("/desk/") === 0 ? "/desk/" : "/app/";
		var canonicalPath = prefix + PAGE_SLUG + "/" + encodeURIComponent(planItem);
		if (window.location.pathname !== canonicalPath || window.location.search) {
			window.history.replaceState(window.history.state, "", canonicalPath);
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
		var planItem = planItemFromRoute();
		canonicalizePlanItemRoute(planItem);
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningItemEditor === "function"
		) {
			kentender_procurement.live.bindPlanningItemEditor($root, {
				plan_item: planItem,
			});
		}
	}

	function mountWithDeps(page) {
		// on_page_load's frappe.require() is async, but Frappe can call
		// on_page_show synchronously right after on_page_load returns, before
		// that async load resolves — without a guard, on_page_show's own
		// "not yet mounted" check would ALSO fire mountWithDeps, doubling the
		// mount() (and its API call). The loading flag makes on_page_show a
		// no-op while on_page_load's own require is already in flight.
		if (page._ktPlnEditorLoading) {
			return;
		}
		page._ktPlnEditorLoading = true;
		frappe.require(
			[
				"/assets/kentender_procurement/js/planning_client_utils.js",
				"/assets/kentender_procurement/js/planning_ui_fixtures/plan_item_editor.js",
				"/assets/kentender_procurement/js/planning_item_editor_bind.js",
			],
			function () {
				page._ktPlnEditorLoading = false;
				mount(page);
			}
		);
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
		mountWithDeps(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (!wrapper.page) {
			return;
		}
		activateSurface();
		var $root = wrapper.page.main.find('[data-testid="kt-pln-ui06-root"]');
		if (!wrapper.page._ktPlnEditorMounted || !$root.length) {
			mountWithDeps(wrapper.page);
			return;
		}
		enterShell();
		var planItem = planItemFromRoute();
		canonicalizePlanItemRoute(planItem);
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningItemEditor === "function"
		) {
			kentender_procurement.live.bindPlanningItemEditor($root, {
				plan_item: planItem,
			});
		}
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function (wrapper) {
		if (wrapper && wrapper.page) wrapper.page.main.find('[data-testid="kt-pln-ui06-root"]').trigger("kt:teardown");
		document.body.classList.remove("kt-pln-editor-active", "kt-pln-surface");
	};
})();
