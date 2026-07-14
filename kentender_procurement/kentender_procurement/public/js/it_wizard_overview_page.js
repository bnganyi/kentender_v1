(function () {
	"use strict";

	frappe.pages["it-tender-configuration-overview"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-overview",
			title: __("Tender STD Configuration Overview"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_std_config_overview.html",
			screen: "std_config_overview",
			shell_class: "it-wizard-overview-shell",
			root_class: "it-wizard-overview-root",
			iframe_class: "it-wizard-overview-iframe",
			testid: "it-wizard-overview",
		});
	};
})();
