// BUD-UI-02 Funding Performance — Stitch shell + live API data (Portfolio twin).
(function () {
	"use strict";

	var PAGE_SLUG = "budget-funding-performance";

	function activateSurface() {
		document.body.classList.add("kt-bud-surface", "kt-bud-perf-active");
	}

	function mount(page) {
		activateSurface();
		var sh = kentender_core.cl_shell;
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html(
				'<div class="p-4 text-danger">Civic Ledger shell is not loaded.</div>'
			);
			return;
		}
		if (typeof sh.enterNative === "function") {
			sh.enterNative({
				sidebarWorkspaceKey: "procurement",
				toolbar: {
					breadcrumbs: [
						{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
						{ label: __("Budget & Funding"), route: ["budget-funding"] },
						{ label: __("Funding Performance") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
		var html =
			kentender_budget.ui_fixtures &&
			typeof kentender_budget.ui_fixtures.performance === "function"
				? kentender_budget.ui_fixtures.performance()
				: '<div class="p-4 text-danger">Performance fixture missing.</div>';
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		var $root = page.main.find('[data-testid="kt-bud-performance"]');
		if (!$root.length) {
			$root = page.main.find(".kt-bud-root").first();
		}
		page._ktBudPerfMounted = true;
		if (kentender_budget.live && typeof kentender_budget.live.bindPerformance === "function") {
			kentender_budget.live.bindPerformance($root);
		}
	}

	function mountWithDeps(page) {
		// on_page_load's frappe.require() is async, but Frappe can call
		// on_page_show synchronously right after on_page_load returns, before
		// that async load resolves — without a guard, on_page_show's own
		// "not yet mounted" check would ALSO fire mountWithDeps, doubling the
		// mount() (and its API call). The loading flag makes on_page_show a
		// no-op while on_page_load's own require is already in flight.
		if (page._ktBudPerfLoading) {
			return;
		}
		page._ktBudPerfLoading = true;
		frappe.require(
			[
				"/assets/kentender_core/js/kt_form_errors.js",
				"/assets/kentender_budget/js/budget_live_bind.js",
				"/assets/kentender_budget/js/budget_ui_fixtures/performance.js",
			],
			function () {
				page._ktBudPerfLoading = false;
				mount(page);
			}
		);
	}

	frappe.pages[PAGE_SLUG] = frappe.pages[PAGE_SLUG] || {};
	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		activateSurface();
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Funding Performance"),
			single_column: true,
		});
		wrapper.page = page;
		page._ktBudPerfMounted = false;
		mountWithDeps(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (!wrapper.page) {
			return;
		}
		activateSurface();
		var $root = wrapper.page.main.find('[data-testid="kt-bud-performance"]');
		if (!wrapper.page._ktBudPerfMounted || !$root.length) {
			mountWithDeps(wrapper.page);
			return;
		}
		var sh = kentender_core.cl_shell;
		if (sh && typeof sh.enterNative === "function") {
			sh.enterNative({
				sidebarWorkspaceKey: "procurement",
				toolbar: {
					breadcrumbs: [
						{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
						{ label: __("Budget & Funding"), route: ["budget-funding"] },
						{ label: __("Funding Performance") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
		if (kentender_budget.live && typeof kentender_budget.live.bindPerformance === "function") {
			kentender_budget.live.bindPerformance($root);
		}
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-bud-perf-active");
	};
})();
