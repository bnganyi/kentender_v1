(function () {
	"use strict";

	frappe.pages["it-tender-configuration-tender-profile"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-tender-profile",
			title: __("Tender Profile"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_tender_profile.html",
			screen: "tender_profile",
			shell_class: "it-wizard-tender-profile-shell",
			root_class: "it-wizard-tender-profile-root",
			iframe_class: "it-wizard-tender-profile-iframe",
			testid: "it-wizard-tender-profile",
		});
	};
})();
