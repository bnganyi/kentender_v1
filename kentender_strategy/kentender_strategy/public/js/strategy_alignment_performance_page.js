// STR-UI-15 Strategy Performance — Stitch shell + live API projection.
(function () {
	"use strict";

	var PAGE_SLUG = "strategy-performance";

	function mount(page) {
		document.body.classList.add("kt-str-surface", "kt-str-perf-active");
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
						{ label: __("Strategy Performance") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
		var html =
			kentender_strategy.ui_fixtures &&
			typeof kentender_strategy.ui_fixtures.performance === "function"
				? kentender_strategy.ui_fixtures.performance()
				: '<div class="p-4 text-danger">Performance fixture missing.</div>';
		sh.mountContent(page.main, {
			pageHeader: { title: "", subtitle: "", hideBreadcrumbs: true },
			mainHtml: html,
		});
		$(page.main).find("#kt-cl-page-header-host").attr("hidden", "hidden");
		var $root = $(page.main).find('[data-testid="kt-str-performance"]');
		if (kentender_strategy.live && typeof kentender_strategy.live.bindStrategyPerformance === "function") {
			kentender_strategy.live.bindStrategyPerformance($root).catch(function (err) {
				console.warn("Strategy Performance live bind failed", err);
			});
		}
	}

	frappe.pages[PAGE_SLUG] = frappe.pages[PAGE_SLUG] || {};
	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Strategy Performance"),
			single_column: true,
		});
		wrapper.page = page;
		frappe.pages[PAGE_SLUG].page = page;
		mount(page);
	};
	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		document.body.classList.add("kt-str-perf-active");
		if (wrapper && wrapper.page) {
			mount(wrapper.page);
		}
	};
	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-str-perf-active");
	};
})();
