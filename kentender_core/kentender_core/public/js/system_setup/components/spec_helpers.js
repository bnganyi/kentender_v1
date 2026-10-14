// Shared harness for the System setup component specs. The SFC templates
// compile `__("…")` into a globalProperties lookup, so every mount supplies
// the translation shim and a minimal frappe object.
export function globalMocks() {
	const __ = (text, args) =>
		String(text).replace(/\{(\d+)\}/g, (_, index) => (args ? String(args[Number(index)]) : ""));
	return {
		mocks: { __, frappe: { set_route: () => {} } },
	};
}

// The shared record picker searches the server through frappe.call. A component spec has no server, so
// `stubPicker` answers a search with the rows it is given (each { id, label, detail }), and `choose`
// does what a person does: type, wait out the quarter-second the picker waits, and press Enter on the first row.
import { flushPromises } from "@vue/test-utils";

export function stubPicker(rows) {
	globalThis.window.frappe = globalThis.frappe;
	globalThis.frappe.call = async ({ method }) => ({
		message: method.endsWith(".resolve")
			? { rows: [] }
			: { rows: rows.map((r) => ({ section: "rest", disabled_reason: null, detail: "", extra: {}, ...r })), total: rows.length, limit: 20, typed: false,
				labels: { noun: "record", plural: "records", near: "Your department", rest: "Everyone else", hint: "" } },
	});
}

export async function choose(wrapper, inputSelector, text = "") {
	const input = wrapper.find(inputSelector);
	if (text) {
		input.element.value = text;
		await input.trigger("input");
	} else {
		await input.trigger("focus");
	}
	await new Promise((resolve) => setTimeout(resolve, text ? 320 : 20));
	await flushPromises();
	await input.trigger("keydown", { key: "Enter" });
	await flushPromises();
}
