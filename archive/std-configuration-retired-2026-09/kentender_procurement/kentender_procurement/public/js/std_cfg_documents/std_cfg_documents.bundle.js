import { createApp } from "vue";
import StdCfgDocuments from "./StdCfgDocuments.vue";

// kt_industry_page_rail.bundle.js (kentender_core) is required alongside this
// bundle by std_cfg_documents_page.js (AGENTS.md §6.6: each bundle carries
// its own Vue instance, so PageRail can't cross a bundle boundary as a child
// vnode — it's consumed via usePageRail()'s mount-helper call instead).
frappe.kt_mount_std_cfg_documents = function (el) {
	const app = createApp(StdCfgDocuments);
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return app;
};
