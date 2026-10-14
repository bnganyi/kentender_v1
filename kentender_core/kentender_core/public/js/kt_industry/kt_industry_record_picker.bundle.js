// The shared record picker, owned by kentender_core and published as a runtime mount helper for
// the same reason as kt_industry_pager.bundle.js: every bundle on this bench carries its own Vue
// runtime, so a component object cannot cross a bundle boundary (AGENTS.md section 6.6). The helper
// mounts the picker as an isolated app on the host's element and exposes only update(), focus()
// and unmount(). A module reaches it through its one wrapper, record_picker_shared/RecordPickerHost.vue.
//
// A module never builds its own dropdown, typed list or search box for choosing one person or one
// record from a list that can grow: it registers a source (kentender_core.services.record_picker)
// and mounts this.
import { createApp, h, reactive } from "vue";
import RecordPicker from "./components/RecordPicker.vue";

frappe.provide("kentender_core.industry");

// opts: { source, context, value, valueLabel, inputId, placeholder, noun, plural, listLabel, allLabel,
//         invalid, required, disabled, errorText, user, fetch, onChange(row | null) }
kentender_core.industry.mountRecordPicker = function (el, opts) {
	const { onChange, ...rest } = opts || {};
	const state = reactive({ ...rest });
	const listeners = { onChange: onChange || (() => {}) };
	let instance = null;
	const app = createApp({
		render() {
			return h(RecordPicker, { ...state, ...listeners, ref: (component) => (instance = component) });
		},
	});
	app.config.globalProperties.__ = window.__;
	app.config.globalProperties.frappe = window.frappe;
	app.mount(el);
	return {
		update(next) {
			const { onChange: changed, ...props } = next || {};
			Object.assign(state, props);
			if (changed) listeners.onChange = changed;
		},
		focus() {
			if (instance && instance.focus) instance.focus();
		},
		unmount() {
			app.unmount();
		},
	};
};
