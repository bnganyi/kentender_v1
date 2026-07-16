(function () {
	"use strict";

	frappe.pages["it-tender-configuration-implementation-schedule"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-implementation-schedule",
			title: __("Implementation Schedule"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_implementation_schedule.html",
			screen: "implementation_schedule",
			shell_class: "it-wizard-implementation-schedule-shell",
			root_class: "it-wizard-implementation-schedule-root",
			iframe_class: "it-wizard-implementation-schedule-iframe",
			testid: "it-wizard-implementation-schedule",
		});
	};
})();
