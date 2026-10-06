// The table-pagination standard's pager, owned by kentender_core and published
// as a runtime mount helper for the same reason as kt_industry_guidance.bundle.js:
// every bundle on this bench carries its own Vue runtime, so a component object
// cannot cross a bundle boundary (AGENTS.md §6.6). The helper mounts the pager as
// an isolated app on the host's element and exposes only update()/unmount().
//
// A module never builds its own pager (nor its own "n rows" line under a table):
// it holds `page` and `pageSize`, hands them here, and reacts to onPage/onSize.
import { createApp, h, reactive } from "vue";
import TablePager from "./components/TablePager.vue";

frappe.provide("kentender_core.industry");

// opts: { total, page, pageSize, pageSizes, noun, nounPlural, onPage(n), onSize(n) }
kentender_core.industry.mountPager = function (el, opts) {
	opts = opts || {};
	const state = reactive({
		total: opts.total || 0,
		page: opts.page || 1,
		pageSize: opts.pageSize || 10,
		noun: opts.noun || "row",
		nounPlural: opts.nounPlural || "",
		...(opts.pageSizes ? { pageSizes: opts.pageSizes } : {}),
	});
	const listeners = { onPage: opts.onPage || (() => {}), onSize: opts.onSize || (() => {}) };
	const app = createApp({
		render() {
			return h(TablePager, { ...state, ...listeners });
		},
	});
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return {
		update(next) {
			Object.assign(state, next || {});
		},
		unmount() {
			app.unmount();
		},
	};
};
