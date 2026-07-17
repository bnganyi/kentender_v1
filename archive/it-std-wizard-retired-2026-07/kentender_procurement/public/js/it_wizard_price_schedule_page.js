(function () {
	"use strict";

	frappe.pages["it-tender-configuration-price-schedule"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-price-schedule",
			title: __("Price Schedule"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_price_schedule.html?v=20260716b",
			screen: "price_schedule",
			shell_class: "it-wizard-price-schedule-shell",
			root_class: "it-wizard-price-schedule-root",
			iframe_class: "it-wizard-price-schedule-iframe",
			testid: "it-wizard-price-schedule",
		});
	};
})();
