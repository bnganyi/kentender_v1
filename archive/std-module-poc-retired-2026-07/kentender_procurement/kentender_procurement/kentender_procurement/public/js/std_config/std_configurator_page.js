/* global frappe */
// STD-CFG-0230 — STD Configurator Desk page bootstrap.
// Route: /app/std-configurator/{template_code}/{tab}
(function () {
	"use strict";

	const shared = kentender_procurement.std_config_shared;
	const shell = kentender_procurement.std_configurator_shell;

	function _templateCodeFromRoute() {
		const route = frappe.get_route() || [];
		return String(route[1] || "").trim();
	}

	function _normalizeTabSlug(raw) {
		const slug = String(raw || "").trim().toLowerCase();
		if (!slug || slug === "undefined" || slug === "null") {
			return "overview";
		}
		return slug;
	}

	function _tabFromRoute() {
		const route = frappe.get_route() || [];
		return _normalizeTabSlug(route[2] || "overview");
	}

	function _mount(wrapper) {
		shared._ensureFonts();
		if (!wrapper) return;
		const templateCode = _templateCodeFromRoute();
		if (!templateCode) {
			wrapper.innerHTML = `<div class="kt-std-cfg-root"><p class="kt-std-cfg-empty">${__(
				"Select an STD template from the library to configure.",
			)}</p></div>`;
			return;
		}
		shell.mount(wrapper, templateCode, _tabFromRoute());
	}

	function _ensureSidebar() {
		if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
			frappe.app.sidebar.setup("Governance & Configuration");
		}
	}

	frappe.pages["std-configurator"].on_page_load = function (wrapper) {
		_mount(wrapper);
	};

	frappe.pages["std-configurator"].on_page_show = function (wrapper) {
		document.body.classList.add("kt-std-cfg-shell");
		setTimeout(_ensureSidebar, 0);
		_mount(wrapper);
	};

	frappe.pages["std-configurator"].on_page_hide = function () {
		document.body.classList.remove("kt-std-cfg-shell");
	};
})();
