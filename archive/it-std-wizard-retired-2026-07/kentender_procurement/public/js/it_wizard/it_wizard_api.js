(function () {
	"use strict";

	frappe.provide("kentender.it_wizard.api");

	var API = "kentender_procurement.it_tender_wizard.api.instance_api";

	function call(method, args) {
		return frappe.call({
			method: API + "." + method,
			args: args || {},
		});
	}

	kentender.it_wizard.api.API = API;
	kentender.it_wizard.api.call = call;
})();
