// PLN-CHG-001 v1.2 §10 — /app/procurement-plan-item/{plan_item_id}. Same
// shell and bundle as the workspace page; the shared root component reads
// the full route (page slug included) and picks the screen. Slug safety
// (D2): the DocType is "Annual Plan Item", whose slug "annual-plan-item"
// leaves this route free (the exact collision D2 exists to avoid — a
// DocType literally named "Procurement Plan Item" would have scrubbed to
// this same route and lost to its own List View).
frappe.pages["procurement-plan-item"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Procurement Plan Item"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["procurement-plan-item"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
		const chromeHost = document.getElementById("kt-cl-chrome-host");
		if (chromeHost) chromeHost.innerHTML = "";
		document.querySelectorAll(".navbar, .page-head").forEach((el) => {
			el.style.setProperty("display", "none", "important");
		});
	}
	mount_procurement_plan_item(wrapper);
};

frappe.pages["procurement-plan-item"].on_page_hide = function (wrapper) {
	wrapper.__kt_pln_item_pending = false;
	unmount_procurement_plan_item(wrapper);
};

function mount_procurement_plan_item(wrapper) {
	if (wrapper.__kt_pln_item_app) return;

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	wrapper.__kt_pln_item_pending = true;
	frappe
		.require(["kt_industry_page_rail.bundle.js", "procurement_planning.bundle.js"])
		.then(() => {
			if (!wrapper.__kt_pln_item_pending) return;
			wrapper.__kt_pln_item_pending = false;
			wrapper.__kt_pln_item_app = frappe.kt_mount_procurement_planning(el);
		});
}

function unmount_procurement_plan_item(wrapper) {
	if (!wrapper.__kt_pln_item_app) return;
	wrapper.__kt_pln_item_app.unmount();
	wrapper.__kt_pln_item_app = null;
}
