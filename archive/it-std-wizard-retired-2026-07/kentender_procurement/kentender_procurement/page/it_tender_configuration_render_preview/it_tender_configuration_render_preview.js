(function () {
	"use strict";

	frappe.pages["it-tender-configuration-render-preview"].on_page_load = function (wrapper) {
		kentender.it_wizard.mount_page(wrapper, {
			page: "it-tender-configuration-render-preview",
			title: __("Render Preview"),
			asset: "/assets/kentender_procurement/it_tender_wizard_impl/it_wizard_render_preview.html",
			screen: "render_preview",
			shell_class: "it-wizard-render-preview-shell",
			root_class: "it-wizard-render-preview-root",
			iframe_class: "it-wizard-render-preview-iframe",
			testid: "it-wizard-render-preview",
		});
	};
})();
