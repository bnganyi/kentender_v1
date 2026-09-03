// CFG-CHG-002 v0.6 §9 / AUTH-ADR-001 v1.6 §12 — the one System setup page.
//
// Unlike the retired organisation-structure/user-responsibilities controllers,
// this page keeps the standard Frappe Desk header and breadcrumb: §12 and
// KT-STD-001 §2.5 make Frappe supply the shell, and authorise no second
// application header. Only the legacy CL chrome host is cleared, and
// enterNative keeps the native sidebar when arriving from a CL surface.

/* global frappe */

frappe.pages["system-setup"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("System setup"),
		single_column: true,
	});
};

frappe.pages["system-setup"].on_page_show = function (wrapper) {
	if (
		window.kentender_core &&
		window.kentender_core.cl_shell &&
		typeof window.kentender_core.cl_shell.enterNative === "function"
	) {
		window.kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
	}
	const chromeHost = document.getElementById("kt-cl-chrome-host");
	if (chromeHost) chromeHost.innerHTML = "";

	const container = wrapper.querySelector(".layout-main-section");
	if (!container) return;

	// A second on_page_show while the bundle is still loading must not queue a
	// second mount (the pending-flag guard the sibling pages proved).
	if (container.__kt_vue_app || container.__kt_system_setup_pending) return;
	container.__kt_system_setup_pending = true;
	frappe.require("system_setup.bundle.js", () => {
		container.__kt_system_setup_pending = false;
		if (container.__kt_vue_app) return;
		if (typeof frappe.kt_mount_system_setup === "function") {
			container.__kt_vue_app = frappe.kt_mount_system_setup(container);
		}
	});
};

frappe.pages["system-setup"].on_page_hide = function (wrapper) {
	const container = wrapper.querySelector(".layout-main-section");
	if (container && container.__kt_vue_app) {
		container.__kt_vue_app.unmount();
		container.__kt_vue_app = null;
		container.innerHTML = "";
	}
};
