// Placeholder Desk pages for Demands routes not yet ported (DEM-UI-02…10).
(function () {
	"use strict";

	var STUBS = [
		{
			slug: "demand-detail",
			title: __("Demand Detail"),
			blurb: __("Approved Demand detail tabs — DEM-UI-09 / 09A–D."),
		},
		{
			slug: "demand-performance",
			title: __("Demand Performance"),
			blurb: __("Demand performance metrics — DEM-UI-10."),
		},
	];

	function routeId() {
		var route = (frappe.get_route && frappe.get_route()) || [];
		return route.length > 1 ? String(route[1] || "") : "";
	}

	function mountStub(def) {
		return function (wrapper) {
			var page = frappe.ui.make_app_page({
				parent: wrapper,
				title: def.title,
				single_column: true,
			});
			wrapper.page = page;
			var id = routeId();
			page.main.html(
				'<div class="kt-dem-stub" data-testid="kt-dem-stub" data-page="' +
					frappe.utils.escape_html(def.slug) +
					'">' +
					'<p class="text-headline-sm text-primary mb-2">' +
					frappe.utils.escape_html(def.title) +
					"</p>" +
					'<p class="text-body-md text-on-surface-variant mb-3">' +
					frappe.utils.escape_html(def.blurb) +
					"</p>" +
					(id
						? '<p class="text-body-md" data-testid="kt-dem-stub-id">' +
							frappe.utils.escape_html(id) +
							"</p>"
						: "") +
					'<p><a href="/desk/demands-workspace">' +
					__("Back to Demands workspace") +
					"</a></p></div>"
			);
		};
	}

	STUBS.forEach(function (def) {
		frappe.pages[def.slug] = frappe.pages[def.slug] || {};
		frappe.pages[def.slug].on_page_load = mountStub(def);
		frappe.pages[def.slug].on_page_show = function (wrapper) {
			if (wrapper && !wrapper.page) {
				mountStub(def)(wrapper);
			}
		};
	});
})();
