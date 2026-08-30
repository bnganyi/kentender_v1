// PLN-CHG-001 v1.2 §10 — the Procurement Planning workspace and its task deep
// links, one Page ("procurement-planning") owning the /app/procurement-planning
// prefix; ProcurementPlanning.vue branches on route segments.
//
// Slug safety (decision D2): no readable DocType scrubs to
// "procurement-planning" (the v1.2 model deliberately names none that way),
// and the old public Workspace of that name was retired by
// pln_chg_001_v12_retire_planning_workspace — frappe's client router would
// otherwise resolve the bare route to the Workspace, as it did live on
// 2026-08-30 (Phase 0, PLN-006).
//
// The page module is the real Module Def "Procurement Planning", so
// three-segment routes can trigger frappe's auto doctype-sidebar swap; this
// page renders its own rail and hides native chrome, matching NDS/Budget.
frappe.pages["procurement-planning"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Procurement Planning"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["procurement-planning"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
		// This page's own rail (usePageRail inside ProcurementPlanning.vue) is
		// the only rail — force-empty the native chrome host and hide the
		// navbar/page-head, matching the NDS/Budget/Strategy pages.
		const chromeHost = document.getElementById("kt-cl-chrome-host");
		if (chromeHost) chromeHost.innerHTML = "";
		document.querySelectorAll(".navbar, .page-head").forEach((el) => {
			el.style.setProperty("display", "none", "important");
		});
	}
	mount_procurement_planning(wrapper);
};

frappe.pages["procurement-planning"].on_page_hide = function (wrapper) {
	wrapper.__kt_pln_pending = false;
	unmount_procurement_planning(wrapper);
};

function mount_procurement_planning(wrapper) {
	if (wrapper.__kt_pln_app) return;

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	wrapper.__kt_pln_pending = true;
	frappe
		.require(["kt_industry_page_rail.bundle.js", "procurement_planning.bundle.js"])
		.then(() => {
			if (!wrapper.__kt_pln_pending) return;
			wrapper.__kt_pln_pending = false;
			wrapper.__kt_pln_app = frappe.kt_mount_procurement_planning(el);
		});
}

function unmount_procurement_planning(wrapper) {
	if (!wrapper.__kt_pln_app) return;
	wrapper.__kt_pln_app.unmount();
	wrapper.__kt_pln_app = null;
}
