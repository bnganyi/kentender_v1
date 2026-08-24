// STR-CHG-001 v1.3 Phase 7 — STR-UI-01 Strategy Portfolio.
// Mount/unmount guard pattern copied from strategy_portfolio_pilot_page.js
// (CLAUDE.md §6.4: frappe.router.off() is a confirmed no-op — an active-flag
// guard inside the Vue composable neutralizes stale listeners, this page_js
// guard only prevents double-mount / a mount racing an early unmount).
frappe.pages["strategy-portfolio"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Strategy Portfolio"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["strategy-portfolio"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
	}
	mount_strategy_portfolio(wrapper);
};

frappe.pages["strategy-portfolio"].on_page_hide = function (wrapper) {
	wrapper.__kt_strategy_portfolio_pending = false;
	unmount_strategy_portfolio(wrapper);
};

function mount_strategy_portfolio(wrapper) {
	if (wrapper.__kt_strategy_portfolio_app) return;

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	wrapper.__kt_strategy_portfolio_pending = true;
	frappe.require("strategy_portfolio.bundle.js").then(() => {
		if (!wrapper.__kt_strategy_portfolio_pending) return;
		wrapper.__kt_strategy_portfolio_pending = false;
		wrapper.__kt_strategy_portfolio_app = frappe.kt_mount_strategy_portfolio(el);
	});
}

function unmount_strategy_portfolio(wrapper) {
	if (!wrapper.__kt_strategy_portfolio_app) return;
	wrapper.__kt_strategy_portfolio_app.unmount();
	wrapper.__kt_strategy_portfolio_app = null;
}
