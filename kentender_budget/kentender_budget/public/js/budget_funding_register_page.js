// Register approved budget — Stitch shell + live API bind.
// Do NOT remount on every on_page_show (causes flash + broken layout after back/forth).
(function () {
	"use strict";

	var PAGE_SLUG = "budget-register";

	function clearOtherSurfaceClasses() {
		document.body.classList.remove("kt-bud-pf-active");
	}

	function activateSurface() {
		clearOtherSurfaceClasses();
		document.body.classList.add("kt-bud-surface", "kt-bud-register-active");
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
		// Enter shell before painting fixture — avoids Desk page flash.
		if (typeof sh.enterNative === "function") {
			sh.enterNative({
				sidebarWorkspaceKey: "procurement",
				toolbar: {
					breadcrumbs: [
						{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
						{ label: __("Budget & Funding"), route: ["budget-funding"] },
						{ label: __("Register approved budget") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
		var html =
			kentender_budget.ui_fixtures &&
			typeof kentender_budget.ui_fixtures.register === "function"
				? kentender_budget.ui_fixtures.register()
				: '<div class="p-4 text-danger">Register fixture missing.</div>';
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		var $root = page.main.find("[data-testid='kt-bud-register']");
		if (!$root.length) {
			$root = page.main.find(".kt-bud-root").first();
		}
		page._ktBudRegisterMounted = true;
		if (kentender_budget.live && typeof kentender_budget.live.bindRegister === "function") {
			kentender_budget.live.bindRegister($root).catch(function (err) {
				console.warn("Register budget bind failed", err);
			});
		}
	}

	function ensureMounted(wrapper) {
		if (!wrapper || !wrapper.page) {
			return;
		}
		activateSurface();
		var $root = wrapper.page.main.find("[data-testid='kt-bud-register']");
		if (wrapper.page._ktBudRegisterMounted && $root.length) {
			// Re-enter shell + rebind only — keep DOM (no flash / no layout wipe).
			var sh = kentender_core.cl_shell;
			if (sh && typeof sh.enterNative === "function") {
				sh.enterNative({
					sidebarWorkspaceKey: "procurement",
					toolbar: {
						breadcrumbs: [
							{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
							{ label: __("Budget & Funding"), route: ["budget-funding"] },
							{ label: __("Register approved budget") },
						],
						showSearch: false,
						showUserMeta: true,
					},
				});
			}
			if (kentender_budget.live && typeof kentender_budget.live.bindRegister === "function") {
				kentender_budget.live.bindRegister($root).catch(function (err) {
					console.warn("Register budget rebind failed", err);
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
			title: __("Register approved budget"),
			single_column: true,
		});
		wrapper.page = page;
		frappe.pages[PAGE_SLUG].page = page;
		page._ktBudRegisterMounted = false;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		ensureMounted(wrapper);
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function () {
		document.body.classList.remove("kt-bud-register-active");
	};
})();
