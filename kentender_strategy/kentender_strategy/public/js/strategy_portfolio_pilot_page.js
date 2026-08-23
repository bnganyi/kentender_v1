// Claude Design -> Vue 3 pilot (see docs/mvp-1-r1/00_common/KenTender_UI_Construction_Framework.md).
// Partial shared-shell participation: kt_cl_shell.enterNative() for the chrome/toolbar
// sliver only (see kt_cl_surface_registry.js's "strategy-portfolio-pilot" entry) — never
// mountContent() near the Vue root, which would destroy Vue's own DOM management.
frappe.pages["strategy-portfolio-pilot"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Strategy Portfolio (Pilot)"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["strategy-portfolio-pilot"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
	}
	mount_strategy_portfolio_pilot(wrapper);
};

frappe.pages["strategy-portfolio-pilot"].on_page_hide = function (wrapper) {
	wrapper.__kt_portfolio_pilot_pending = false; // cancel an in-flight mount race (see below)
	unmount_strategy_portfolio_pilot(wrapper);
};

function mount_strategy_portfolio_pilot(wrapper) {
	if (wrapper.__kt_portfolio_pilot_app) {
		// Already mounted (on_page_show fired again without an intervening hide) — Vue's
		// own reactivity handles route changes from here; re-mounting would duplicate the app.
		return;
	}

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	// frappe.require() is async — guard against on_page_hide firing before it resolves
	// (a fast navigate-away-and-back on the very first, uncached load of the bundle),
	// which would otherwise mount an app nothing ever unmounts.
	wrapper.__kt_portfolio_pilot_pending = true;
	frappe.require("strategy_portfolio_pilot.bundle.js").then(() => {
		if (!wrapper.__kt_portfolio_pilot_pending) return;
		wrapper.__kt_portfolio_pilot_pending = false;
		wrapper.__kt_portfolio_pilot_app = frappe.kt_mount_strategy_portfolio_pilot(el);
	});
}

function unmount_strategy_portfolio_pilot(wrapper) {
	if (!wrapper.__kt_portfolio_pilot_app) return;
	wrapper.__kt_portfolio_pilot_app.unmount();
	wrapper.__kt_portfolio_pilot_app = null;
}
