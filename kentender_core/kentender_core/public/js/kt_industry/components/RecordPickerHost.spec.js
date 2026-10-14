// The host wrapper every module mounts the picker through: v-model carries the id (or null), `change`
// carries the whole row, and the screen's own selection and context flow down without the picker
// moving by itself. The real mount helper (kt_industry_record_picker.bundle.js) is loaded, so this
// is also the proof that the bundle publishes what the wrapper calls.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import RecordPickerHost from "../../record_picker_shared/RecordPickerHost.vue";

globalThis.frappe = globalThis.frappe || {};
globalThis.frappe.provide =
	globalThis.frappe.provide ||
	((path) => {
		let node = globalThis;
		for (const part of path.split(".")) {
			node[part] = node[part] || {};
			node = node[part];
		}
		return node;
	});
globalThis.window.kentender_core = globalThis.kentender_core;
await import("../kt_industry_record_picker.bundle.js");

const answer = { rows: [{ id: "amina", label: "Amina Hassan", detail: "Accountant", section: "rest", disabled_reason: null, extra: { department: "HR" } }], total: 1, limit: 20, typed: false, labels: { noun: "person", plural: "people", near: "Your department", rest: "Everyone else", hint: "" } };
const fetch = vi.fn(async (endpoint) => (endpoint === "resolve" ? { rows: [] } : answer));
const flush = async () => {
	await vi.advanceTimersByTimeAsync(0);
	await nextTick();
};

beforeEach(() => {
	vi.useFakeTimers();
	fetch.mockClear();
});
afterEach(() => {
	vi.useRealTimers();
	document.body.innerHTML = "";
});

describe("RecordPickerHost", () => {
	it("mounts the shared picker and reports a choice as v-model and as the whole row", async () => {
		const w = mount(RecordPickerHost, { attachTo: document.body, props: { source: "s.s", inputId: "who", fetch } });
		const input = w.get("#who");
		await input.trigger("focus");
		await flush();
		await input.trigger("keydown", { key: "Enter" });
		await flush();
		expect(w.emitted("update:modelValue").at(-1)).toEqual(["amina"]);
		expect(w.emitted("change").at(-1)[0]).toMatchObject({ id: "amina", label: "Amina Hassan" });
		expect(input.element.value).toBe("Amina Hassan");
		w.unmount();
	});

	it("follows the screen's own selection, and reports a clear as null", async () => {
		const w = mount(RecordPickerHost, { attachTo: document.body, props: { source: "s.s", inputId: "who", modelValue: "zoe", valueLabel: "Zoë Mwangi", fetch } });
		expect(w.get("#who").element.value).toBe("Zoë Mwangi");
		await w.setProps({ modelValue: "amina", valueLabel: "Amina Hassan" });
		await nextTick();
		expect(w.get("#who").element.value).toBe("Amina Hassan");
		await w.get('[data-testid="kt-picker-clear"]').trigger("click");
		expect(w.emitted("update:modelValue").at(-1)).toEqual([null]);
		w.unmount();
	});

	it("passes the invalid mark and a changed context down to the one picker", async () => {
		const w = mount(RecordPickerHost, { attachTo: document.body, props: { source: "s.s", inputId: "who", context: { role: "Member" }, fetch } });
		await w.setProps({ invalid: true, errorText: "Choose a member." });
		await nextTick();
		expect(w.get("#who").attributes("aria-invalid")).toBe("true");
		expect(w.get('[data-testid="kt-picker-error"]').text()).toBe("Choose a member.");
		w.unmount();
	});

	it("adds several: each choice is an `add` carrying the whole row, the list stays open, and the screen's staged ids come back greyed", async () => {
		const w = mount(RecordPickerHost, { attachTo: document.body, props: { source: "s.s", inputId: "who", inline: true, multiple: true, stagedNoun: "to appoint", fetch } });
		await flush();
		await w.get("#who").trigger("keydown", { key: "Enter" });
		await flush();
		expect(w.emitted("add").at(-1)[0]).toMatchObject({ id: "amina", label: "Amina Hassan", extra: { department: "HR" } });
		expect(w.emitted("update:modelValue")).toBeUndefined(); // nothing is "chosen"
		expect(w.find('[data-testid="kt-picker-list"]').exists()).toBe(true);
		await w.setProps({ staged: ["amina"] });
		await flush();
		expect(w.get('[role="option"]').attributes("aria-disabled")).toBe("true");
		expect(w.get(".kt-picker-reason").text()).toBe("Added to this list");
		w.unmount();
	});

	it("says so on the console, once, when the bundle is not loaded", () => {
		const published = window.kentender_core.industry.mountRecordPicker;
		delete window.kentender_core.industry.mountRecordPicker;
		const spy = vi.spyOn(console, "error").mockImplementation(() => {});
		const w = mount(RecordPickerHost, { props: { source: "s.s" } });
		expect(spy).toHaveBeenCalledTimes(1);
		expect(spy.mock.calls[0][0]).toContain("kt_industry_record_picker.bundle.js");
		w.unmount();
		spy.mockRestore();
		window.kentender_core.industry.mountRecordPicker = published;
	});
});
