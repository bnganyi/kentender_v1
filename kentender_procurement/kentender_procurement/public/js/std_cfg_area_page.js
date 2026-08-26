// STD-CHG-001 v1.3 Phase 11 — PCFG-01..09 shared shell. Same
// mount/chrome/unmount pattern as the other STD Configuration pages.
frappe.pages["std-cfg-area"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Configuration area"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["std-cfg-area"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
		const chromeHost = document.getElementById("kt-cl-chrome-host");
		if (chromeHost) chromeHost.innerHTML = "";
		document.querySelectorAll(".navbar, .page-head").forEach((el) => {
			el.style.setProperty("display", "none", "important");
		});
	}
	mount_std_cfg_area(wrapper);
};

frappe.pages["std-cfg-area"].on_page_hide = function (wrapper) {
	wrapper.__kt_std_cfg_area_pending = false;
	unmount_std_cfg_area(wrapper);
};

function mount_std_cfg_area(wrapper) {
	if (wrapper.__kt_std_cfg_area_app) return;

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	wrapper.__kt_std_cfg_area_pending = true;
	frappe.require(["kt_industry_page_rail.bundle.js", "std_cfg_area.bundle.js"]).then(() => {
		if (!wrapper.__kt_std_cfg_area_pending) return;
		wrapper.__kt_std_cfg_area_pending = false;
		wrapper.__kt_std_cfg_area_app = frappe.kt_mount_std_cfg_area(el);
	});
}

function unmount_std_cfg_area(wrapper) {
	if (!wrapper.__kt_std_cfg_area_app) return;
	wrapper.__kt_std_cfg_area_app.unmount();
	wrapper.__kt_std_cfg_area_app = null;
}
