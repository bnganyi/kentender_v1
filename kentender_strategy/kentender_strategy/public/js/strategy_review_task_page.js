// STR-CHG-001 v1.3 Phase 7 — STR-UI-04 Review task (reviewer/approver).
frappe.pages["strategy-review-task"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Review Task"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["strategy-review-task"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
		// See strategy_portfolio_page.js for why this host must be force-emptied and
		// the native navbar/page-head force-hidden: this page's own PageRail.vue is
		// the only rail, matching kentender_core's reference_data pattern.
		const chromeHost = document.getElementById("kt-cl-chrome-host");
		if (chromeHost) chromeHost.innerHTML = "";
		document.querySelectorAll(".navbar, .page-head").forEach((el) => {
			el.style.setProperty("display", "none", "important");
		});
	}
	mount_strategy_review_task(wrapper);
};

frappe.pages["strategy-review-task"].on_page_hide = function (wrapper) {
	wrapper.__kt_strategy_review_task_pending = false;
	unmount_strategy_review_task(wrapper);
};

function mount_strategy_review_task(wrapper) {
	if (wrapper.__kt_strategy_review_task_app) return;

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	wrapper.__kt_strategy_review_task_pending = true;
	frappe.require("strategy_review_task.bundle.js").then(() => {
		if (!wrapper.__kt_strategy_review_task_pending) return;
		wrapper.__kt_strategy_review_task_pending = false;
		wrapper.__kt_strategy_review_task_app = frappe.kt_mount_strategy_review_task(el);
	});
}

function unmount_strategy_review_task(wrapper) {
	if (!wrapper.__kt_strategy_review_task_app) return;
	wrapper.__kt_strategy_review_task_app.unmount();
	wrapper.__kt_strategy_review_task_app = null;
}
