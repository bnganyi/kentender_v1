(function () {
	"use strict";

	frappe.pages["it-tender-configuration-dashboard"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-dashboard",
			title: __("Tender Configuration Dashboard"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_dashboard.html",
			screen: "dashboard",
			shell_class: "it-wizard-dashboard-shell",
			root_class: "it-wizard-dashboard-root",
			iframe_class: "it-wizard-dashboard-iframe",
			testid: "it-wizard-dashboard",
		});
	};
})();
