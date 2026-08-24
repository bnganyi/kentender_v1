import { createApp } from "vue";
import StrategyReviewTask from "./StrategyReviewTask.vue";

frappe.kt_mount_strategy_review_task = function (el) {
	const app = createApp(StrategyReviewTask);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
