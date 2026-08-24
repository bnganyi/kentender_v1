import { createApp } from "vue";
import StrategyPlanWorkspace from "./StrategyPlanWorkspace.vue";
import "../strategy_shared/styles/tokens.css";

frappe.kt_mount_strategy_plan_workspace = function (el) {
	const app = createApp(StrategyPlanWorkspace);
	app.mount(el);
	return app;
};
