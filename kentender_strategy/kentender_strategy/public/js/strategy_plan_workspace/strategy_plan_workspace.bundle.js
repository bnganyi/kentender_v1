import { createApp } from "vue";
import StrategyPlanWorkspace from "./StrategyPlanWorkspace.vue";

frappe.kt_mount_strategy_plan_workspace = function (el) {
	const app = createApp(StrategyPlanWorkspace);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
