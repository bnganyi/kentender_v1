// STD-CHG-001 v1.3 Phase 11 — STD-UI-00 Standard Tender Documents.
// Mount/unmount + chrome-clearing pattern copied from kentender_strategy's
// strategy_portfolio_page.js (kentender-vue-desk-chrome-systems memory):
// an Industry-design page must never register in kt_cl_surface_registry.js,
// must clear #kt-cl-chrome-host itself, and must force-hide .navbar/.page-head
// since Frappe's own scroll handler re-touches .page-head's inline style.
frappe.pages["std-cfg-documents"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Standard Tender Documents"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["std-cfg-documents"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
		const chromeHost = document.getElementById("kt-cl-chrome-host");
		if (chromeHost) chromeHost.innerHTML = "";
		document.querySelectorAll(".navbar, .page-head").forEach((el) => {
			el.style.setProperty("display", "none", "important");
		});
	}
	mount_std_cfg_documents(wrapper);
};

frappe.pages["std-cfg-documents"].on_page_hide = function (wrapper) {
	wrapper.__kt_std_cfg_documents_pending = false;
	unmount_std_cfg_documents(wrapper);
};

function mount_std_cfg_documents(wrapper) {
	if (wrapper.__kt_std_cfg_documents_app) return;

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	wrapper.__kt_std_cfg_documents_pending = true;
	frappe.require(["kt_industry_page_rail.bundle.js", "std_cfg_documents.bundle.js"]).then(() => {
		if (!wrapper.__kt_std_cfg_documents_pending) return;
		wrapper.__kt_std_cfg_documents_pending = false;
		wrapper.__kt_std_cfg_documents_app = frappe.kt_mount_std_cfg_documents(el);
	});
}

function unmount_std_cfg_documents(wrapper) {
	if (!wrapper.__kt_std_cfg_documents_app) return;
	wrapper.__kt_std_cfg_documents_app.unmount();
	wrapper.__kt_std_cfg_documents_app = null;
}
