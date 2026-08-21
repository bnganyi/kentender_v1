// PLN-UI-08 Plan review — Stitch shell + live review API.
(function () {
	"use strict";

	var PAGE_SLUG = "procurement-plan-review";

	function activateSurface() {
		document.body.classList.add("kt-pln-surface", "kt-pln-review-active");
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
					{ label: __("Review") },
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
		var q = frappe.utils.get_query_params ? frappe.utils.get_query_params() : {};
		if (q && q.plan) {
			return q.plan;
		}
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
			typeof kentender_procurement.ui_fixtures.planning_plan_review === "function"
				? kentender_procurement.ui_fixtures.planning_plan_review()
				: '<div class="p-4 text-danger">' + __("Planning review fixture missing.") + "</div>";
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		var $root = page.main.find('[data-testid="kt-pln-ui08-root"]');
		page._ktPlnReviewMounted = true;
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningReview === "function"
		) {
			kentender_procurement.live.bindPlanningReview($root, { plan: planFromRoute() });
		}
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		activateSurface();
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Plan review"),
			single_column: true,
		});
		wrapper.page = page;
		page._ktPlnReviewMounted = false;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (!wrapper.page) {
			return;
		}
		activateSurface();
		var $root = wrapper.page.main.find('[data-testid="kt-pln-ui08-root"]');
		if (!wrapper.page._ktPlnReviewMounted || !$root.length) {
			mount(wrapper.page);
			return;
		}
		enterShell();
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningReview === "function"
		) {
			kentender_procurement.live.bindPlanningReview($root, { plan: planFromRoute() });
		}
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-pln-review-active");
	};
})();
