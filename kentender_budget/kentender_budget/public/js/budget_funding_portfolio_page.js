// BUD-UI-01 Budget Portfolio — Stitch shell + live API data.
(function () {
	"use strict";

	var PAGE_SLUG = "budget-funding";

	function routeFromAttr($el) {
		var raw = ($el.attr("data-kt-bud-route") || "").trim();
		if (!raw) {
			return null;
		}
		return raw.split("/").filter(Boolean);
	}

	function bind($root) {
		$root.off("click.ktBudPf").on("click.ktBudPf", "[data-kt-bud-action]", function (e) {
			e.preventDefault();
			var $el = $(this);
			var action = $el.attr("data-kt-bud-action");
			if (action === "register-budget") {
				frappe.set_route("budget-register");
				return;
			}
			if (action === "open-performance") {
				frappe.set_route("budget-funding-performance");
				return;
			}
			var route = routeFromAttr($el);
			if (route && route.length) {
				frappe.set_route.apply(frappe, route);
				return;
			}
			var code = $el.closest("tr").attr("data-budget-code");
			if (code && (action === "open" || action === "review" || action === "view")) {
				frappe.set_route("budget-overview", code);
			}
		});
	}

	function activateSurface() {
		document.body.classList.remove("kt-bud-register-active");
		document.body.classList.add("kt-bud-surface", "kt-bud-pf-active");
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
						{ label: __("Budget & Funding") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
		var html =
			kentender_budget.ui_fixtures &&
			typeof kentender_budget.ui_fixtures.portfolio === "function"
				? kentender_budget.ui_fixtures.portfolio()
				: '<div class="p-4 text-danger">Portfolio fixture missing.</div>';
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		var $root = page.main.find("[data-testid='kt-bud-portfolio']");
		if (!$root.length) {
			$root = page.main.find(".kt-bud-root").first();
		}
		page._ktBudPortfolioMounted = true;
		bind($root);
		if (kentender_budget.live && typeof kentender_budget.live.bindPortfolio === "function") {
			kentender_budget.live.bindPortfolio($root);
		}
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		activateSurface();
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Budget & Funding"),
			single_column: true,
		});
		wrapper.page = page;
		page._ktBudPortfolioMounted = false;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (!wrapper.page) {
			return;
		}
		activateSurface();
		var $root = wrapper.page.main.find("[data-testid='kt-bud-portfolio']");
		if (!wrapper.page._ktBudPortfolioMounted || !$root.length) {
			mount(wrapper.page);
			return;
		}
		var sh = kentender_core.cl_shell;
		if (sh && typeof sh.enterNative === "function") {
			sh.enterNative({
				sidebarWorkspaceKey: "procurement",
				toolbar: {
					breadcrumbs: [
						{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
						{ label: __("Budget & Funding") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
		bind($root);
		if (kentender_budget.live && typeof kentender_budget.live.bindPortfolio === "function") {
			kentender_budget.live.bindPortfolio($root);
		}
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-bud-pf-active");
	};
})();
