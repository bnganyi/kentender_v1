(function () {
	"use strict";

	frappe.pages["std-family-detail"].on_page_load = function (wrapper) {
		kentender.std_prod.mount_page(wrapper, {
			page: "std-family-detail",
			title: __("STD Family Detail"),
			asset: "/assets/kentender_procurement/std_prod_impl/std_family_detail.html",
			screen: "family",
			shell_class: "std-prod-std-family-detail-shell",
			root_class: "std-prod-std-family-detail-root",
			iframe_class: "std-prod-std-family-detail-iframe",
			testid: "std-prod-std-family-detail",
		});
	};
})();
