/* global frappe */
// STD-CFG-0610 — legacy std-engine route redirects to std-library when v2 is enabled.
(function () {
	"use strict";

	function _v2Enabled() {
		const boot = (frappe.boot && frappe.boot.kentender_procurement) || {};
		if (boot.std_config_ui_v2_enabled) return true;
		if (
			kentender_procurement &&
			kentender_procurement.std_config_shared &&
			typeof kentender_procurement.std_config_shared.isV2Enabled === "function"
		) {
			return kentender_procurement.std_config_shared.isV2Enabled();
		}
		return false;
	}

	function _redirect() {
		if (!_v2Enabled()) return;
		const route = frappe.get_route() || [];
		if (route[0] !== "std-engine") return;
		const seg = String(route[1] || "").toLowerCase();
		if (seg === "advanced") return;
		if (seg === "library" && String(route[2] || "").toLowerCase() === "import") {
			frappe.set_route("std-library", "import");
			return;
		}
		frappe.set_route("std-library");
	}

	frappe.pages["std-engine"].on_page_load = function () {
		_redirect();
	};

	frappe.pages["std-engine"].on_page_show = function () {
		_redirect();
	};
})();
