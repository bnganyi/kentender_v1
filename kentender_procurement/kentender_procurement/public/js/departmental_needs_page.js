// NDS-CHG-001 v1.1 §10 — NDS-UI-01…08, all under one Page
// ("departmental-needs") sharing the /app/departmental-needs URL prefix; the
// root DepartmentalNeeds.vue branches on route segments to pick the screen.
//
// The slug is safe from Frappe's doctype-route collision: frappe's client
// router registers every readable doctype's own slug into `this.routes` and
// resolves a bare /app/<slug> against that map before falling back to a
// same-named Page. The doctype here is "Departmental Need", whose slug is
// "departmental-need" (singular) — "departmental-needs" is unclaimed, which is
// why §10 can specify it.
frappe.pages["departmental-needs"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Departmental Needs"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["departmental-needs"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
		// This page's own PageRail (mounted inside DepartmentalNeeds.vue via
		// usePageRail) is the only rail — force-empty the native chrome host and
		// hide the navbar/page-head, matching the Budget and Strategy pages.
		const chromeHost = document.getElementById("kt-cl-chrome-host");
		if (chromeHost) chromeHost.innerHTML = "";
		document.querySelectorAll(".navbar, .page-head").forEach((el) => {
			el.style.setProperty("display", "none", "important");
		});
	}
	mount_departmental_needs(wrapper);
};

frappe.pages["departmental-needs"].on_page_hide = function (wrapper) {
	wrapper.__kt_nds_pending = false;
	unmount_departmental_needs(wrapper);
};

function mount_departmental_needs(wrapper) {
	if (wrapper.__kt_nds_app) return;

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	wrapper.__kt_nds_pending = true;
	frappe.require(["kt_industry_page_rail.bundle.js", "departmental_needs.bundle.js"]).then(() => {
		if (!wrapper.__kt_nds_pending) return;
		wrapper.__kt_nds_pending = false;
		wrapper.__kt_nds_app = frappe.kt_mount_departmental_needs(el);
	});
}

function unmount_departmental_needs(wrapper) {
	if (!wrapper.__kt_nds_app) return;
	wrapper.__kt_nds_app.unmount();
	wrapper.__kt_nds_app = null;
}
