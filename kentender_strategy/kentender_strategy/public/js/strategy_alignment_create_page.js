// Create strategic plan — focused Desk page in Strategy Alignment shell.
(function () {
	"use strict";

	var PAGE_SLUG = "strategy-plan-create";

	function mount(page) {
		document.body.classList.add("kt-str-surface", "kt-str-create-active");
		var sh = kentender_core.cl_shell;
		if (!sh || typeof sh.mountContent !== "function") {
			page.main.html('<div class="p-4 text-danger">Civic Ledger shell is not loaded.</div>');
			return;
		}
		if (typeof sh.enterNative === "function") {
			sh.enterNative({
				sidebarWorkspaceKey: "procurement",
				toolbar: {
					breadcrumbs: [
						{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
						{ label: __("Strategy Alignment"), route: ["strategy-alignment"] },
						{ label: __("Create strategic plan") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
		var html =
			kentender_strategy.ui_fixtures &&
			typeof kentender_strategy.ui_fixtures.create_plan === "function"
				? kentender_strategy.ui_fixtures.create_plan()
				: '<div class="p-4 text-danger">Create plan fixture missing.</div>';
		sh.mountContent(page.main, {
			pageHeader: { title: "", subtitle: "", hideBreadcrumbs: true },
			mainHtml: html,
		});
		var $root = $(page.main).find('[data-testid="kt-str-create-plan"]');
		if (kentender_strategy.live && typeof kentender_strategy.live.bindCreatePlan === "function") {
			kentender_strategy.live.bindCreatePlan($root).catch(function (err) {
				console.warn("Create plan bind failed", err);
			});
		}
	}

	frappe.pages[PAGE_SLUG] = frappe.pages[PAGE_SLUG] || {};
	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Create Strategic Plan"),
			single_column: true,
		});
		wrapper.page = page;
		frappe.pages[PAGE_SLUG].page = page;
		mount(page);
	};
	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		document.body.classList.add("kt-str-create-active");
		if (wrapper && wrapper.page) {
			mount(wrapper.page);
		}
	};
	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-str-create-active");
	};
})();
