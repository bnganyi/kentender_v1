// BUD-UI-09 — Review Budget Revision dedicated Desk page (not Revisions tab).
(function () {
	"use strict";

	var PAGE_SLUG = "budget-revision-review";

	function revisionCodeFromRoute() {
		var route = frappe.get_route() || [];
		if (route.length > 1 && route[1]) {
			return String(route[1]).trim();
		}
		return "BR-MOH-0002";
	}

	function activateSurface() {
		document.body.classList.remove("kt-bud-pf-active", "kt-bud-rev-create-active");
		document.body.classList.add("kt-bud-surface", "kt-bud-rev-review-active");
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
		var code = revisionCodeFromRoute();
		var budgetHint =
			(kentender_budget.workspace && kentender_budget.workspace.FIXTURE_BUDGET) ||
			"MOH-BUD-0001";
		if (typeof sh.enterNative === "function") {
			sh.enterNative({
				sidebarWorkspaceKey: "procurement",
				toolbar: {
					breadcrumbs: [
						{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
						{ label: __("Budget & Funding"), route: ["budget-funding"] },
						{ label: __("Revisions"), route: ["budget-revisions", budgetHint] },
						{ label: __("Review budget revision") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
		var html =
			kentender_budget.ui_fixtures &&
			typeof kentender_budget.ui_fixtures.revision_review === "function"
				? kentender_budget.ui_fixtures.revision_review()
				: '<div class="p-4 text-danger">Revision review fixture missing.</div>';
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		$(page.main).find("#kt-cl-page-header-host").attr("hidden", "hidden");
		var $root = page.main.find('[data-testid="kt-bud-revision-review"]');
		if (!$root.length) {
			$root = page.main.find(".kt-bud-root").first();
		}
		$root.attr("data-kt-bud-revision-code", code);
		page._ktBudRevReviewMounted = true;
		page._ktBudRevReviewCode = code;
		if (kentender_budget.live && typeof kentender_budget.live.bindRevisionReview === "function") {
			kentender_budget.live.bindRevisionReview($root, code).catch(function (err) {
				console.warn("Revision review bind failed", err);
				frappe.show_alert({
					message: __("Could not load revision review"),
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
		var code = revisionCodeFromRoute();
		var $root = wrapper.page.main.find('[data-testid="kt-bud-revision-review"]');
		if (
			wrapper.page._ktBudRevReviewMounted &&
			$root.length &&
			wrapper.page._ktBudRevReviewCode === code
		) {
			if (kentender_budget.live && typeof kentender_budget.live.bindRevisionReview === "function") {
				kentender_budget.live.bindRevisionReview($root, code).catch(function (err) {
					console.warn("Revision review rebind failed", err);
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
			title: __("Review budget revision"),
			single_column: true,
		});
		wrapper.page = page;
		frappe.pages[PAGE_SLUG].page = page;
		page._ktBudRevReviewMounted = false;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		ensureMounted(wrapper);
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-bud-rev-review-active");
	};
})();
