(function () {
	"use strict";

	frappe.pages["it-tender-configuration-tds"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-tds",
			title: __("Tender Data Sheet"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_tds.html",
			screen: "tds",
			shell_class: "it-wizard-tds-shell",
			root_class: "it-wizard-tds-root",
			iframe_class: "it-wizard-tds-iframe",
			testid: "it-wizard-tds",
		});
	};
})();
