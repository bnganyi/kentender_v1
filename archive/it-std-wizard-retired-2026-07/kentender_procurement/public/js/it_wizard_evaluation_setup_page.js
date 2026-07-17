(function () {
	"use strict";

	frappe.pages["it-tender-configuration-evaluation-setup"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-evaluation-setup",
			title: __("Evaluation Setup"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_evaluation_setup.html?v=20260716",
			screen: "evaluation_setup",
			shell_class: "it-wizard-evaluation-setup-shell",
			root_class: "it-wizard-evaluation-setup-root",
			iframe_class: "it-wizard-evaluation-setup-iframe",
			testid: "it-wizard-evaluation-setup",
		});
	};
})();
