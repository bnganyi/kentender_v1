// STR-UI-01 Strategy Portfolio — Stitch shell + live API data (REQ Prompt B).
(function () {
	"use strict";

	var PAGE_SLUG = "strategy-alignment";

	function routeFromAttr($el) {
		var raw = ($el.attr("data-kt-str-route") || "").trim();
		if (!raw) {
			return null;
		}
		return raw.split("/").filter(Boolean);
	}

	function bind($root) {
		$root.off("click.ktStrPf").on("click.ktStrPf", "[data-kt-str-action]", function (e) {
			e.preventDefault();
			var $el = $(this);
			var action = $el.attr("data-kt-str-action");
			if (action === "clear-filters") {
				return; // handled by live binder
			}
			if (action === "create-plan") {
				frappe.set_route("strategy-plan-create");
				return;
			}

			var route = routeFromAttr($el);
			if (route && route.length) {
				frappe.set_route.apply(frappe, route);
				return;
			}

			var code = $el.closest("tr").attr("data-plan-code");
			if (action === "open-plan" && code) {
				frappe.set_route("strategy-plan-overview", code);
				return;
			}
			if (action === "review-plan" && code) {
				frappe.set_route("strategy-plan-review", code);
				return;
			}
			if (action === "pvo-catalogue") {
				frappe.set_route("strategy-pvo-catalogue");
			}
		});
	}

	function mount(page) {
		document.body.classList.add("kt-str-surface", "kt-str-pf-active");
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
						{ label: __("Strategy Alignment") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
		var html =
			kentender_strategy.ui_fixtures &&
			typeof kentender_strategy.ui_fixtures.portfolio === "function"
				? kentender_strategy.ui_fixtures.portfolio()
				: '<div class="p-4 text-danger">Portfolio fixture missing.</div>';
		sh.mountContent(page.main, {
			pageHeader: { title: "", subtitle: "", hideBreadcrumbs: true },
			mainHtml: html,
		});
		$(page.main).find("#kt-cl-page-header-host").attr("hidden", "hidden");
		var $root = $(page.main).find('[data-testid="kt-str-portfolio"]');
		if (kentender_strategy.alignment && typeof kentender_strategy.alignment.annotatePortfolio === "function") {
			kentender_strategy.alignment.annotatePortfolio($root);
		} else {
			var $grids = $root.find(".grid.grid-cols-4");
			if ($grids.length) {
				$grids.first().attr("data-testid", "kt-str-summary-strip");
			}
			$root.find("table").first().attr("data-testid", "kt-str-plans-table");
		}
		bind($root);
		if (kentender_strategy.live && typeof kentender_strategy.live.bindPortfolio === "function") {
			kentender_strategy.live.bindPortfolio($root).catch(function (err) {
				console.warn("Portfolio live bind failed", err);
			});
		}
	}

	frappe.pages[PAGE_SLUG] = frappe.pages[PAGE_SLUG] || {};
	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Strategy Alignment"),
			single_column: true,
		});
		wrapper.page = page;
		frappe.pages[PAGE_SLUG].page = page;
		mount(page);
	};
	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		document.body.classList.add("kt-str-pf-active");
		if (wrapper && wrapper.page) {
			mount(wrapper.page);
		}
	};
	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-str-pf-active");
	};
})();
