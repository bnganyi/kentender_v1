// STD-CHG-001 v1.3 Phase 11 — STD-WF-05 Version Comparison.
frappe.pages["std-cfg-comparison"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Version Comparison"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["std-cfg-comparison"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
		const chromeHost = document.getElementById("kt-cl-chrome-host");
		if (chromeHost) chromeHost.innerHTML = "";
		document.querySelectorAll(".navbar, .page-head").forEach((el) => {
			el.style.setProperty("display", "none", "important");
		});
	}
	mount_std_cfg_comparison(wrapper);
};

frappe.pages["std-cfg-comparison"].on_page_hide = function (wrapper) {
	wrapper.__kt_std_cfg_comparison_pending = false;
	unmount_std_cfg_comparison(wrapper);
};

function mount_std_cfg_comparison(wrapper) {
	if (wrapper.__kt_std_cfg_comparison_app) return;

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	wrapper.__kt_std_cfg_comparison_pending = true;
	frappe.require(["kt_industry_page_rail.bundle.js", "std_cfg_comparison.bundle.js"]).then(() => {
		if (!wrapper.__kt_std_cfg_comparison_pending) return;
		wrapper.__kt_std_cfg_comparison_pending = false;
		wrapper.__kt_std_cfg_comparison_app = frappe.kt_mount_std_cfg_comparison(el);
	});
}

function unmount_std_cfg_comparison(wrapper) {
	if (!wrapper.__kt_std_cfg_comparison_app) return;
	wrapper.__kt_std_cfg_comparison_app.unmount();
	wrapper.__kt_std_cfg_comparison_app = null;
}
