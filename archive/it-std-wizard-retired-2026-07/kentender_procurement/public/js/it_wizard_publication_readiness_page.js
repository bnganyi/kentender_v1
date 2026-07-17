(function () {
	"use strict";

	frappe.pages["it-tender-configuration-publication-readiness"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-publication-readiness",
			title: __("Publication Readiness"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_publication_readiness.html?v=20260716",
			screen: "publication_readiness",
			shell_class: "it-wizard-publication-readiness-shell",
			root_class: "it-wizard-publication-readiness-root",
			iframe_class: "it-wizard-publication-readiness-iframe",
			testid: "it-wizard-publication-readiness",
		});
	};
})();
