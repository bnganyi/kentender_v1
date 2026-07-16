(function () {
	"use strict";

	frappe.pages["it-tender-configuration-it-requirements"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-it-requirements",
			title: __("IT Requirements"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_it_requirements.html",
			screen: "it_requirements",
			shell_class: "it-wizard-it-requirements-shell",
			root_class: "it-wizard-it-requirements-root",
			iframe_class: "it-wizard-it-requirements-iframe",
			testid: "it-wizard-it-requirements",
		});
	};
})();
