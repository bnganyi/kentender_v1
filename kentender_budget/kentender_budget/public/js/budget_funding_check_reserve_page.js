// BUD-UI-06 Check and Reserve — thin Desk host for Stitch modal smoke / deep-link.
(function () {
	"use strict";

	var PAGE_SLUG = "budget-check-reserve";

	function scenarioFromRoute() {
		var route = frappe.get_route ? frappe.get_route() : [];
		var kind = (route[1] || "available").toLowerCase();
		if (kind === "insufficient") {
			return {
				demandName: "DMD-MOH-2027-014",
				demandTitle: "National digital health infrastructure upgrade",
				department: "Digital Health Directorate",
				requestedAmount: 455000000,
				budgetLine: "MOH-BL-0001",
				mode: "standalone",
			};
		}
		// Available path uses MOH-BL-0002 headroom (80M available).
		return {
			demandName: "DMD-TEST-UI-AVAILABLE",
			demandTitle: "National digital health capability uplift",
			department: "Digital Health Directorate",
			requestedAmount: 50000000,
			budgetLine: "MOH-BL-0002",
			mode: "standalone",
		};
	}

	function mount(page) {
		var sh = kentender_core.cl_shell;
		if (sh && typeof sh.enterNative === "function") {
			sh.enterNative({
				sidebarWorkspaceKey: "procurement",
				toolbar: {
					breadcrumbs: [
						{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
						{ label: __("Budget & Funding"), route: ["budget-funding"] },
						{ label: __("Check and reserve funding") },
					],
					showSearch: false,
					showUserMeta: true,
				},
			});
		}
		var intro =
			'<div class="p-4" data-testid="kt-bud-check-reserve-page">' +
			'<p class="text-muted">' +
			__(
				"Opening the Check and Reserve funding decision. Close the dialog to return to Budget & Funding."
			) +
			"</p></div>";
		if (sh && typeof sh.mountContent === "function") {
			sh.mountContent(page.main, {
				mainHtml: intro,
				pageHeader: { title: "", hidden: true },
			});
		} else {
			page.main.html(intro);
		}
		page._ktBudCrMounted = true;
		if (kentender_budget.live && typeof kentender_budget.live.openCheckReserve === "function") {
			kentender_budget.live.openCheckReserve(scenarioFromRoute());
		}
	}

	frappe.pages[PAGE_SLUG] = frappe.pages[PAGE_SLUG] || {};
	frappe.pages[PAGE_SLUG].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("Check and reserve funding"),
			single_column: true,
		});
		wrapper.page = page;
		page._ktBudCrMounted = false;
		mount(page);
	};

	frappe.pages[PAGE_SLUG].on_page_show = function (wrapper) {
		if (!wrapper.page) {
			return;
		}
		if (!wrapper.page._ktBudCrMounted) {
			mount(wrapper.page);
			return;
		}
		if (kentender_budget.live && typeof kentender_budget.live.openCheckReserve === "function") {
			kentender_budget.live.openCheckReserve(scenarioFromRoute());
		}
	};
})();
