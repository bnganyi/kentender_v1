import { createApp } from "vue";
import StdCfgReview from "./StdCfgReview.vue";

frappe.kt_mount_std_cfg_review = function (el) {
	const app = createApp(StdCfgReview);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
