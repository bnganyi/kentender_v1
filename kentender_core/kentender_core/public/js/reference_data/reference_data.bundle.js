import { createApp } from "vue";
import ReferenceData from "./ReferenceData.vue";

frappe.kt_mount_reference_data = function (el) {
	const app = createApp(ReferenceData);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
