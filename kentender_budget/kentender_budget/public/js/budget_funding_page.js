// BUD-CHG-001 v1.2 §10 — BUD-UI-01/02/03/04/05, all under one Page
// ("budget-funding") sharing the /app/budget-funding URL prefix; the root
// Budget.vue branches on route segments to pick the screen.
//
// Not "budget" — Frappe's client router (frappe/public/js/frappe/router.js
// `setup()`) unconditionally registers every readable doctype's own slug
// into `this.routes` and resolves a bare `/app/<slug>` against that map
// before ever falling back to a same-named Page. Since a doctype named
// "Budget" already exists, `/app/budget` always opened its native List View
// (confirmed live) — this collision poisons every route under that prefix,
// not just the workspace, since `/app/budget/<id>` etc. also resolve
// against the doctype first. "budget-funding" has no such collision.
frappe.pages["budget-funding"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Budget & Funding"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["budget-funding"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
		// This page's own PageRail.vue (mounted inside Budget.vue via
		// usePageRail) is the only rail — force-empty the native chrome host
		// and hide the navbar/page-head, matching kentender_strategy's pages.
		const chromeHost = document.getElementById("kt-cl-chrome-host");
		if (chromeHost) chromeHost.innerHTML = "";
		document.querySelectorAll(".navbar, .page-head").forEach((el) => {
			el.style.setProperty("display", "none", "important");
		});
	}
	mount_budget_funding(wrapper);
};

frappe.pages["budget-funding"].on_page_hide = function (wrapper) {
	wrapper.__kt_budget_funding_pending = false;
	unmount_budget_funding(wrapper);
};

function mount_budget_funding(wrapper) {
	if (wrapper.__kt_budget_funding_app) return;

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	wrapper.__kt_budget_funding_pending = true;
	frappe.require(["kt_industry_page_rail.bundle.js", "budget_funding.bundle.js"]).then(() => {
		if (!wrapper.__kt_budget_funding_pending) return;
		wrapper.__kt_budget_funding_pending = false;
		wrapper.__kt_budget_funding_app = frappe.kt_mount_budget_funding(el);
	});
}

function unmount_budget_funding(wrapper) {
	if (!wrapper.__kt_budget_funding_app) return;
	wrapper.__kt_budget_funding_app.unmount();
	wrapper.__kt_budget_funding_app = null;
}
