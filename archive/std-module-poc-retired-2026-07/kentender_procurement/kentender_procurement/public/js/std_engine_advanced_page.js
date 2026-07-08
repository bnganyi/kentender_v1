/* global frappe */
// STD-CFG-0620 — Advanced STD catalogue (legacy master-detail shell for technical admins).
(function () {
	"use strict";

	const shared = kentender_procurement.std_config_shared;

	function _mount(wrapper) {
		shared._ensureFonts();
		if (!wrapper) return;
		if (!shared.canUseStdAdvancedCatalogue()) {
			wrapper.innerHTML = `<div class="kt-std-lib-root" data-testid="std-library-page">
				<p class="kt-std-lib-empty">${__(
					"You do not have permission to open the Advanced Technical catalogue.",
				)}</p>
			</div>`;
			return;
		}
		const shell = kentender_procurement.std_library_shell;
		if (!shell || typeof shell.mountInto !== "function") {
			wrapper.innerHTML = `<div class="kt-std-lib-root" data-testid="std-library-page">
				<p class="kt-std-lib-empty">${__("Advanced catalogue shell failed to load.")}</p>
			</div>`;
			return;
		}
		shell.mountInto(wrapper);
	}

	frappe.pages["std-engine-advanced"].on_page_load = function (wrapper) {
		_mount(wrapper);
	};

	frappe.pages["std-engine-advanced"].on_page_show = function (wrapper) {
		_mount(wrapper);
	};
})();
