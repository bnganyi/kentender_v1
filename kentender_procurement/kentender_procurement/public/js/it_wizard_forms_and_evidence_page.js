(function () {
	"use strict";

	frappe.pages["it-tender-configuration-forms-and-evidence"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-forms-and-evidence",
			title: __("Forms and Evidence"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_forms_and_evidence.html?v=20260716",
			screen: "forms_and_evidence",
			shell_class: "it-wizard-forms-and-evidence-shell",
			root_class: "it-wizard-forms-and-evidence-root",
			iframe_class: "it-wizard-forms-and-evidence-iframe",
			testid: "it-wizard-forms-and-evidence",
		});
	};
})();
