// BUD-UI-08 — Create Budget Revision dedicated Desk page (not Revisions tab).
(function () {
	"use strict";

	var PAGE_SLUG = "budget-revision-create";

	function budgetCodeFromRoute() {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]).trim();
		}
		return "MOH-BUD-0001";
	}

	function revisionCodeFromRoute() {
		var route = frappe.get_route() || [];
		if (route.length > 2 && route[2]) {
			return String(route[2]).trim();
		}
		return "";
	}

	function activateSurface() {
		document.body.classList.remove("kt-bud-pf-active");
		document.body.classList.add("kt-bud-surface", "kt-bud-rev-create-active");
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
		var code = budgetCodeFromRoute();
		var revisionCode = revisionCodeFromRoute();
		if (typeof sh.enterNative === "function") {
			sh.enterNative({
				sidebarWorkspaceKey: "procurement",
				toolbar: {
					breadcrumbs: [
						{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
						{ label: __("Budget & Funding"), route: ["budget-funding"] },
						{ label: __("Revisions"), route: ["budget-revisions", code] },
						{ label: __("Create budget revision") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
		var html =
			kentender_budget.ui_fixtures &&
			typeof kentender_budget.ui_fixtures.revision_create === "function"
				? kentender_budget.ui_fixtures.revision_create()
				: '<div class="p-4 text-danger">Revision create fixture missing.</div>';
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		$(page.main).find("#kt-cl-page-header-host").attr("hidden", "hidden");
		var $root = page.main.find('[data-testid="kt-bud-revision-create"]');
		if (!$root.length) {
			$root = page.main.find(".kt-bud-root").first();
		}
		$root.attr("data-kt-bud-budget-code", code);
		page._ktBudRevCreateMounted = true;
		page._ktBudRevCreateCode = code;
		page._ktBudRevCreateRevision = revisionCode;
		if (kentender_budget.live && typeof kentender_budget.live.bindRevisionCreate === "function") {
			kentender_budget.live.bindRevisionCreate($root, code, revisionCode).catch(function (err) {
				console.warn("Revision create bind failed", err);
				frappe.show_alert({
					message: __("Could not load revision form"),
					indicator: "orange",
				});
			});
		}
	}

	function ensureMounted(wrapper) {
		if (!wrapper || !wrapper.page) {
			return;
		}
		activateSurface();
		var code = budgetCodeFromRoute();
		var $root = wrapper.page.main.find('[data-testid="kt-bud-revision-create"]');
		if (
			wrapper.page._ktBudRevCreateMounted &&
			$root.length &&
			wrapper.page._ktBudRevCreateCode === code
		) {
			var sh = kentender_core.cl_shell;
			if (sh && typeof sh.enterNative === "function") {
				sh.enterNative({
					sidebarWorkspaceKey: "procurement",
					toolbar: {
						breadcrumbs: [
							{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
							{ label: __("Budget & Funding"), route: ["budget-funding"] },
							{ label: __("Revisions"), route: ["budget-revisions", code] },
							{ label: __("Create budget revision") },
						],
						showSearch: false,
						showUserMeta: true,
					},
				});
			}
			if (kentender_budget.live && typeof kentender_budget.live.bindRevisionCreate === "function") {
				kentender_budget.live.bindRevisionCreate($root, code).catch(function (err) {
					console.warn("Revision create rebind failed", err);
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
			title: __("Create budget revision"),
			single_column: true,
		});
		wrapper.page = page;
		frappe.pages[PAGE_SLUG].page = page;
		page._ktBudRevCreateMounted = false;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		ensureMounted(wrapper);
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-bud-rev-create-active");
	};
})();
