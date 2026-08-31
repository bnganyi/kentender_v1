// PLN-CHG-001 v1.2 §10 — /app/departmental-procurement-plan/{dpp_reference}
// (+ entry editors). Same shell and bundle as the workspace page; the shared
// root component reads the full route (page slug included) and picks the
// screen. Slug safety (D2): the DocType is "Departmental Plan", whose slug
// "departmental-plan" leaves this route free.
frappe.pages["departmental-procurement-plan"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Departmental Procurement Plan"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["departmental-procurement-plan"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
		const chromeHost = document.getElementById("kt-cl-chrome-host");
		if (chromeHost) chromeHost.innerHTML = "";
		document.querySelectorAll(".navbar, .page-head").forEach((el) => {
			el.style.setProperty("display", "none", "important");
		});
	}
	mount_departmental_procurement_plan(wrapper);
};

frappe.pages["departmental-procurement-plan"].on_page_hide = function (wrapper) {
	wrapper.__kt_pln_dpp_pending = false;
	unmount_departmental_procurement_plan(wrapper);
};

function mount_departmental_procurement_plan(wrapper) {
	if (wrapper.__kt_pln_dpp_app) return;

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	wrapper.__kt_pln_dpp_pending = true;
	frappe
		.require(["kt_industry_page_rail.bundle.js", "procurement_planning.bundle.js"])
		.then(() => {
			if (!wrapper.__kt_pln_dpp_pending) return;
			wrapper.__kt_pln_dpp_pending = false;
			wrapper.__kt_pln_dpp_app = frappe.kt_mount_procurement_planning(el);
		});
}

function unmount_departmental_procurement_plan(wrapper) {
	if (!wrapper.__kt_pln_dpp_app) return;
	wrapper.__kt_pln_dpp_app.unmount();
	wrapper.__kt_pln_dpp_app = null;
}
