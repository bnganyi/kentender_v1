(function () {
	"use strict";

	frappe.provide("kentender.it_wizard.shell");

	var NATIVE_SHELL_CLASS = "it-wizard-native-shell";
	var PROCUREMENT_SIDEBAR_KEY = "Procurement";

	function preserve_procurement_sidebar() {
		if (
			window.kentender &&
			kentender.it_wizard &&
			typeof kentender.it_wizard.preserve_procurement_sidebar === "function" &&
			kentender.it_wizard.preserve_procurement_sidebar !== preserve_procurement_sidebar
		) {
			kentender.it_wizard.preserve_procurement_sidebar();
			return;
		}
		if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
			frappe.app.sidebar.setup(PROCUREMENT_SIDEBAR_KEY);
		}
	}

	function show(options) {
		options = options || {};
		document.body.classList.add(NATIVE_SHELL_CLASS);
		if (options.screen_shell_class) {
			document.body.classList.add(options.screen_shell_class);
		}
		preserve_procurement_sidebar();
	}

	function hide(options) {
		options = options || {};
		document.body.classList.remove(NATIVE_SHELL_CLASS);
		if (options.screen_shell_class) {
			document.body.classList.remove(options.screen_shell_class);
		}
	}

	function mount_wrapper(wrapper, html) {
		if (!wrapper) {
			return null;
		}
		wrapper.innerHTML = html;
		return wrapper;
	}

	kentender.it_wizard.shell.NATIVE_SHELL_CLASS = NATIVE_SHELL_CLASS;
	kentender.it_wizard.shell.show = show;
	kentender.it_wizard.shell.hide = hide;
	kentender.it_wizard.shell.preserve_procurement_sidebar = preserve_procurement_sidebar;
	kentender.it_wizard.shell.mount_wrapper = mount_wrapper;
})();
