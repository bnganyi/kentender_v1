// PLN-CHG-001 v1.2 §10 — /app/annual-procurement-plan/{plan_reference}. Same
// shell and bundle as the workspace page; the shared root component reads
// the full route (page slug included) and picks the screen. Slug safety
// (D2): the DocType is "Annual Plan", whose slug "annual-plan" leaves this
// route free.
frappe.pages["annual-procurement-plan"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Annual Procurement Plan"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["annual-procurement-plan"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
		const chromeHost = document.getElementById("kt-cl-chrome-host");
		if (chromeHost) chromeHost.innerHTML = "";
		document.querySelectorAll(".navbar, .page-head").forEach((el) => {
			el.style.setProperty("display", "none", "important");
		});
	}
	mount_annual_procurement_plan(wrapper);
};

frappe.pages["annual-procurement-plan"].on_page_hide = function (wrapper) {
	wrapper.__kt_pln_plan_pending = false;
	unmount_annual_procurement_plan(wrapper);
};

function mount_annual_procurement_plan(wrapper) {
	if (wrapper.__kt_pln_plan_app) return;

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	wrapper.__kt_pln_plan_pending = true;
	frappe
		.require(["kt_industry_page_rail.bundle.js", "procurement_planning.bundle.js"])
		.then(() => {
			if (!wrapper.__kt_pln_plan_pending) return;
			wrapper.__kt_pln_plan_pending = false;
			wrapper.__kt_pln_plan_app = frappe.kt_mount_procurement_planning(el);
		});
}

function unmount_annual_procurement_plan(wrapper) {
	if (!wrapper.__kt_pln_plan_app) return;
	wrapper.__kt_pln_plan_app.unmount();
	wrapper.__kt_pln_plan_app = null;
}
