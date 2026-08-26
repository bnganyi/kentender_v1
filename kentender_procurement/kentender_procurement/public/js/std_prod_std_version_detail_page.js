(function () {
	"use strict";

	frappe.pages["std-version-detail"].on_page_load = function (wrapper) {
		frappe.require(
			[
				"/assets/kentender_procurement/js/std_prod_engine.js",
				"/assets/kentender_procurement/css/std_prod_std_version_detail_page.css",
			],
			function () {
				kentender.std_prod.mount_page(wrapper, {
					page: "std-version-detail",
					title: __("STD Version Detail"),
					asset: "/assets/kentender_procurement/std_prod_impl/std_version_detail.html",
					screen: "version",
					shell_class: "std-prod-std-version-detail-shell",
					root_class: "std-prod-std-version-detail-root",
					iframe_class: "std-prod-std-version-detail-iframe",
					testid: "std-prod-std-version-detail",
				});
			}
		);
	};
})();
