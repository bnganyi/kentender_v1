// Stub Desk page for Funding Performance (Phase 8 — not Overview).
(function () {
	"use strict";

	var STUBS = [
		{
			slug: "budget-funding-performance",
			title: "Funding Performance",
			message: "Funding Performance is next in the Budget MVP-1 build sequence.",
		},
	];

	STUBS.forEach(function (stub) {
		if (!frappe.pages[stub.slug]) {
			return;
		}
		frappe.pages[stub.slug].on_page_load = function (wrapper) {
			document.body.classList.add("kt-bud-surface");
			var page = frappe.ui.make_app_page({
				parent: wrapper,
				title: __(stub.title),
				single_column: true,
			});
			var sh = kentender_core.cl_shell;
			if (sh && typeof sh.enterNative === "function") {
				sh.enterNative({
					sidebarWorkspaceKey: "procurement",
					toolbar: {
						breadcrumbs: [
							{ label: __("Home"), route: ["Workspaces", "Procurement Home"] },
							{ label: __("Budget & Funding"), route: ["budget-funding"] },
							{ label: __(stub.title) },
						],
						showSearch: false,
						showUserMeta: true,
					},
				});
			}
			page.main.html(
				'<div class="p-6 kt-bud-root" data-testid="kt-bud-stub">' +
					'<h2 class="text-lg font-semibold mb-2">' +
					frappe.utils.escape_html(__(stub.title)) +
					"</h2>" +
					'<p class="text-muted">' +
					frappe.utils.escape_html(__(stub.message)) +
					"</p>" +
					'<p class="mt-4"><a href="/desk/budget-funding">' +
					frappe.utils.escape_html(__("Back to Budget & Funding")) +
					"</a></p></div>"
			);
		};
	});
})();
