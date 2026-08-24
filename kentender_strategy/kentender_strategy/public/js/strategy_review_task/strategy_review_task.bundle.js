import { createApp } from "vue";
import StrategyReviewTask from "./StrategyReviewTask.vue";
import "../strategy_shared/styles/tokens.css";

frappe.kt_mount_strategy_review_task = function (el) {
	const app = createApp(StrategyReviewTask);
	app.mount(el);
	return app;
};
