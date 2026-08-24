// STR-CHG-001 v1.3 Phase 7 — STR-UI-02 Plan workspace + STR-UI-03 Structure
// editor (one Page: the editor is the Structure tab in edit mode when the
// current version is Draft/Returned — see StrategyPlanWorkspace.vue).
frappe.pages["strategy-plan-workspace"].on_page_load = function (wrapper) {
	const page = frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Plan Workspace"),
		single_column: true,
	});
	wrapper.page = page;
};

frappe.pages["strategy-plan-workspace"].on_page_show = function (wrapper) {
	if (window.kentender_core && kentender_core.cl_shell) {
		kentender_core.cl_shell.enterNative({ sidebarWorkspaceKey: "procurement" });
	}
	mount_strategy_plan_workspace(wrapper);
};

frappe.pages["strategy-plan-workspace"].on_page_hide = function (wrapper) {
	wrapper.__kt_strategy_plan_workspace_pending = false;
	unmount_strategy_plan_workspace(wrapper);
};

function mount_strategy_plan_workspace(wrapper) {
	if (wrapper.__kt_strategy_plan_workspace_app) return;

	const $mountPoint = $(wrapper).find(".layout-main-section");
	$mountPoint.empty();
	const el = document.createElement("div");
	$mountPoint.get(0).appendChild(el);

	wrapper.__kt_strategy_plan_workspace_pending = true;
	frappe.require("strategy_plan_workspace.bundle.js").then(() => {
		if (!wrapper.__kt_strategy_plan_workspace_pending) return;
		wrapper.__kt_strategy_plan_workspace_pending = false;
		wrapper.__kt_strategy_plan_workspace_app = frappe.kt_mount_strategy_plan_workspace(el);
	});
}

function unmount_strategy_plan_workspace(wrapper) {
	if (!wrapper.__kt_strategy_plan_workspace_app) return;
	wrapper.__kt_strategy_plan_workspace_app.unmount();
	wrapper.__kt_strategy_plan_workspace_app = null;
}
