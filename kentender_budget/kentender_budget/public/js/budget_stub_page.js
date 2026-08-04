// Stub Desk pages for next Budget MVP-1 screens (Register / Performance / Overview).
(function () {
	"use strict";

	var STUBS = [
		{
			slug: "budget-funding-performance",
			title: "Funding Performance",
			message: "Funding Performance is next in the Budget MVP-1 build sequence.",
		},
		{
			slug: "budget-overview",
			title: "Budget Overview",
			message: "Budget workspace Overview is next in the Budget MVP-1 build sequence.",
		},
	];

	STUBS.forEach(function (stub) {
		if (!frappe.pages[stub.slug]) {
			return;
		}
		frappe.pages[stub.slug].on_page_load = function (wrapper) {
			var page = frappe.ui.make_app_page({
				parent: wrapper,
				title: __(stub.title),
				single_column: true,
			});
			page.main.html(
				'<div class="p-6" data-testid="kt-bud-stub">' +
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
