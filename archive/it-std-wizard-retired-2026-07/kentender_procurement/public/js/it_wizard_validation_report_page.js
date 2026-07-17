(function () {
	"use strict";

	frappe.pages["it-tender-configuration-validation-report"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-validation-report",
			title: __("Validation Report"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_validation_report.html?v=20260716",
			screen: "validation_report",
			shell_class: "it-wizard-validation-report-shell",
			root_class: "it-wizard-validation-report-root",
			iframe_class: "it-wizard-validation-report-iframe",
			testid: "it-wizard-validation-report",
		});
	};
})();
