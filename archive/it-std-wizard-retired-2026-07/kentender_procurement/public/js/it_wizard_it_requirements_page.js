(function () {
	"use strict";

	var SHARED = [
		"/assets/kentender_procurement/js/it_wizard/it_wizard_api.js",
		"/assets/kentender_procurement/js/it_wizard/it_wizard_routes.js",
		"/assets/kentender_procurement/js/it_wizard/it_wizard_components.js",
		"/assets/kentender_procurement/js/it_wizard/it_wizard_shell.js",
	];

	frappe.pages["it-tender-configuration-it-requirements"].on_page_load = function (wrapper) {
		frappe.require(
			SHARED.concat(["/assets/kentender_procurement/js/it_wizard/screens/it_requirements.js"]),
			function () {
				kentender.it_wizard.screens.it_requirements.init(wrapper);
			},
		);
	};

	frappe.pages["it-tender-configuration-it-requirements"].on_page_show = function (wrapper) {
		frappe.require(
			SHARED.concat(["/assets/kentender_procurement/js/it_wizard/screens/it_requirements.js"]),
			function () {
				kentender.it_wizard.screens.it_requirements.show(wrapper);
			},
		);
	};
})();
