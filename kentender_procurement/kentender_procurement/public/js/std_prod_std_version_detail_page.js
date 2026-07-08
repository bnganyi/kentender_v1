(function () {
	"use strict";

	var STD_VERSION_DETAIL_ASSET =
		"/assets/kentender_procurement/std_prod_impl/std_version_detail.html";

	frappe.pages["std-version-detail"].on_page_load = function (wrapper) {
		var page = frappe.ui.make_app_page({
			parent: wrapper,
			title: __("STD Version Detail"),
			single_column: true,
		});

		document.body.classList.add("std-prod-std-version-detail-shell");

		var root = page.main.get(0);
		if (!root) {
			return;
		}

		root.className = "std-prod-std-version-detail-root";
		root.setAttribute("data-testid", "std-prod-std-version-detail-root");
		root.innerHTML =
			'<section class="std-prod-std-version-detail-shell" data-testid="std-prod-std-version-detail-shell">' +
			'<iframe class="std-prod-std-version-detail-iframe" data-testid="std-prod-std-version-detail-iframe" src="' +
			STD_VERSION_DETAIL_ASSET +
			'" title="STD Version Detail"></iframe>' +
			"</section>";
	};

	frappe.pages["std-version-detail"].on_page_show = function () {
		document.body.classList.add("std-prod-std-version-detail-shell");
	};

	frappe.pages["std-version-detail"].on_page_hide = function () {
		document.body.classList.remove("std-prod-std-version-detail-shell");
	};
})();
