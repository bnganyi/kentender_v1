(function () {
	"use strict";

	frappe.pages["it-tender-configuration-scc"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-scc",
			title: __("SCC / Contract Carry-Forward"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_scc.html",
			screen: "scc",
			shell_class: "it-wizard-scc-shell",
			root_class: "it-wizard-scc-root",
			iframe_class: "it-wizard-scc-iframe",
			testid: "it-wizard-scc",
		});
	};
})();
