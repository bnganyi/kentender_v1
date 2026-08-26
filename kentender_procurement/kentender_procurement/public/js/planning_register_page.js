// PLN-UI-02 Register annual plan — Stitch shell + live create-scope API.
(function () {
	"use strict";

	var PAGE_SLUG = "procurement-plan-register";

	function activateSurface() {
		document.body.classList.add("kt-pln-surface", "kt-pln-reg-active");
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
					{ label: __("Register plan") },
				],
				showSearch: false,
				showUserMeta: true,
			},
		});
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
			typeof kentender_procurement.ui_fixtures.planning_register === "function"
				? kentender_procurement.ui_fixtures.planning_register()
				: '<div class="p-4 text-danger">' + __("Planning register fixture missing.") + "</div>";
		sh.mountContent(page.main, {
			mainHtml: html,
			pageHeader: { title: "", hidden: true },
		});
		var $root = page.main.find('[data-testid="kt-pln-ui02-root"]');
		page._ktPlnRegisterMounted = true;
		page._ktPlnRegisterActive = true;
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningRegister === "function"
		) {
			kentender_procurement.live.bindPlanningRegister($root);
		}
	}

	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		activateSurface();
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Register annual plan"),
			single_column: true,
		});
		wrapper.page = page;
		page._ktPlnRegisterMounted = false;
		frappe.require(
			[
				"/assets/kentender_procurement/js/planning_client_utils.js",
				"/assets/kentender_procurement/js/planning_ui_fixtures/register.js",
				"/assets/kentender_procurement/js/planning_register_bind.js",
			],
			function () {
				mount(page);
			}
		);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (!wrapper.page) {
			return;
		}
		activateSurface();
		var $root = wrapper.page.main.find('[data-testid="kt-pln-ui02-root"]');
		if (!wrapper.page._ktPlnRegisterMounted || !$root.length) {
			mount(wrapper.page);
			return;
		}
		enterShell();
		if (wrapper.page._ktPlnRegisterActive) {
			return;
		}
		wrapper.page._ktPlnRegisterActive = true;
		if (
			kentender_procurement.live &&
			typeof kentender_procurement.live.bindPlanningRegister === "function"
		) {
			kentender_procurement.live.bindPlanningRegister($root);
		}
	};

	frappe.pages[PAGE_SLUG].on_page_hide = function (wrapper) {
		if (wrapper.page) wrapper.page._ktPlnRegisterActive = false;
		$('[data-testid="kt-pln-ui02-root"]').trigger("kt:teardown").off(".ktPlnRegisterRevision").attr("data-kt-request-id", "-1");
		document.body.classList.remove("kt-pln-reg-active", "kt-pln-surface");
	};
})();
