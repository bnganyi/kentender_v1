// PLN-UI-09 Approved plan — Stitch shell + live implementation API.
(function () {
	"use strict";

	var PAGE_SLUG = "procurement-plan-approved";

	function activateSurface() {
		document.body.classList.add("kt-pln-surface", "kt-pln-approved-active");
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
					{ label: __("Approved plan") },
				],
				showSearch: false,
				showUserMeta: true,
			},
		});
	}

	function planFromRoute() {
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
			typeof kentender_procurement.ui_fixtures.planning_plan_approved === "function"
				? kentender_procurement.ui_fixtures.planning_plan_approved()
				: '<div class="p-4 text-danger">' + __("Planning approved fixture missing.") + "</div>";
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		var $root = page.main.find('[data-testid="kt-pln-ui09-root"]');
		page._ktPlnApprovedMounted = true;
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningApproved === "function"
		) {
			kentender_procurement.live.bindPlanningApproved($root, { plan: planFromRoute() });
		}
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		activateSurface();
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Approved plan"),
			single_column: true,
		});
		wrapper.page = page;
		page._ktPlnApprovedMounted = false;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (!wrapper.page) {
			return;
		}
		activateSurface();
		var $root = wrapper.page.main.find('[data-testid="kt-pln-ui09-root"]');
		if (!wrapper.page._ktPlnApprovedMounted || !$root.length) {
			mount(wrapper.page);
			return;
		}
		enterShell();
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningApproved === "function"
		) {
			kentender_procurement.live.bindPlanningApproved($root, { plan: planFromRoute() });
		}
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-pln-approved-active");
	};
})();
