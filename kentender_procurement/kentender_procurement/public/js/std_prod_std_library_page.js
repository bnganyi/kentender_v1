(function () {
	"use strict";

	frappe.pages["std-library"].on_page_load = function (wrapper) {
		frappe.require(
			[
				"/assets/kentender_procurement/js/std_prod_engine.js",
				"/assets/kentender_procurement/css/std_prod_std_library_page.css",
			],
			function () {
				kentender.std_prod.mount_page(wrapper, {
					page: "std-library",
					title: __("Official STD Library"),
					asset: "/assets/kentender_procurement/std_prod_impl/std_library.html",
					screen: "library",
					shell_class: "std-prod-std-library-shell",
					root_class: "std-prod-std-library-root",
					iframe_class: "std-prod-std-library-iframe",
					testid: "std-prod-std-library",
				});
			}
		);
	};
})();
