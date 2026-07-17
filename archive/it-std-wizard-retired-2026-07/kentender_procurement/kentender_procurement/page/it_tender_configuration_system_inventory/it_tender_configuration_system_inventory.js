(function () {
	"use strict";

	frappe.pages["it-tender-configuration-system-inventory"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-system-inventory",
			title: __("System Inventory"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_system_inventory.html",
			screen: "system_inventory",
			shell_class: "it-wizard-system-inventory-shell",
			root_class: "it-wizard-system-inventory-root",
			iframe_class: "it-wizard-system-inventory-iframe",
			testid: "it-wizard-system-inventory",
		});
	};
})();
