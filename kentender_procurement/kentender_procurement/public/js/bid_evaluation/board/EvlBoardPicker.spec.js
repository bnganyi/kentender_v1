// The evaluation board's two ways of naming a person through the shared record picker: a cell in the
// committee table and a stand-alone field. A choice leaves three things in the screen's form (id, name,
// facts), and a cleared choice clears all three, so the department cell never reads a stale person.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import EvlBoard from "./EvlBoard.vue";
import { fi, tb } from "./model.js";

const ROW = { id: "grace", label: "Grace Wambui", detail: "Chair · HR", section: "rest", disabled_reason: null, extra: { designation: "Chair", department: "Human Resources" } };
const flush = async (ms = 0) => {
	await vi.advanceTimersByTimeAsync(ms);
	await nextTick();
};
let calls;

beforeEach(() => {
	vi.useFakeTimers();
	calls = [];
	globalThis.window.frappe = globalThis.frappe;
	globalThis.frappe.call = async ({ method, args }) => {
		calls.push({ method, args });
		return { message: { rows: [ROW], total: 1, limit: 20, typed: false, labels: { noun: "person", plural: "people", near: "Your department", rest: "Everyone else", hint: "" } } };
	};
});
afterEach(() => {
	vi.useRealTimers();
	document.body.innerHTML = "";
});

const board = (blocks) => ({ title: "Appoint evaluation committee", desc: "x", blocks, guidance: { answer: null, journey: null } });
const updates = (w) => w.emitted("update").map(([u]) => [u.name, u.value]);

describe("a person in a table cell", () => {
	const table = tb(["Person", "Department", "Capacity"], [[{ picker: "m0_user", source: "bid_evaluation.committee_member", testid: "evl-member-0-user", context: { tender_reference: "T", mode: "appoint", taken: [] } }, "", ""]], { title: "Committee members" });

	it("is the shared picker, searching this source for this Tender, with an input the screen can label", async () => {
		const w = mount(EvlBoard, { attachTo: document.body, props: { board: board([table]), form: {}, pending: false } });
		const input = w.get("#evl-member-0-user");
		expect(input.attributes("role")).toBe("combobox");
		await input.trigger("focus");
		await flush();
		expect(calls[0].args.source).toBe("bid_evaluation.committee_member");
		expect(JSON.parse(calls[0].args.context)).toEqual({ tender_reference: "T", mode: "appoint", taken: [] });
		w.unmount();
	});

	it("reports a choice as the id, the name and the facts, and a clear as all three emptied", async () => {
		const w = mount(EvlBoard, { attachTo: document.body, props: { board: board([table]), form: {}, pending: false } });
		const input = w.get("#evl-member-0-user");
		await input.trigger("focus");
		await flush();
		await input.trigger("keydown", { key: "Enter" });
		await flush();
		expect(updates(w)).toEqual([["m0_user", "grace"], ["m0_user__label", "Grace Wambui"], ["m0_user__extra", { designation: "Chair", department: "Human Resources" }]]);
		await w.setProps({ form: { m0_user: "grace", m0_user__label: "Grace Wambui" } });
		await w.get('[data-testid="kt-picker-clear"]').trigger("click");
		await flush();
		expect(updates(w).slice(3)).toEqual([["m0_user", ""], ["m0_user__label", ""], ["m0_user__extra", undefined]]);
		w.unmount();
	});

	it("shows a saved person's name from the form, without searching", async () => {
		const w = mount(EvlBoard, { attachTo: document.body, props: { board: board([table]), form: { m0_user: "grace", m0_user__label: "Grace Wambui" }, pending: false } });
		expect(w.get("#evl-member-0-user").element.value).toBe("Grace Wambui");
		expect(calls.length).toBe(0);
		w.unmount();
	});
});

describe("a person as a stand-alone field", () => {
	it("is labelled by the field and takes its input id from the field's name", async () => {
		const field = fi("Incoming person", "", { picker: true, req: true, name: "incoming", source: "bid_evaluation.committee_member", context: { tender_reference: "T", mode: "replace" } });
		const w = mount(EvlBoard, { attachTo: document.body, props: { board: board([field]), form: {}, pending: false } });
		expect(w.get("label").text()).toContain("Incoming person");
		expect(w.get("label").attributes("for")).toBe("evl-incoming");
		expect(w.get("#evl-incoming").attributes("role")).toBe("combobox");
		w.unmount();
	});
});
