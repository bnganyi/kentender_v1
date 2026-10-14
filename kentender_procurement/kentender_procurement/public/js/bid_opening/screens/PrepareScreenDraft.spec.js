// The Add members dialog appoints everyone in one action, but the appointment can be refused (the committee still needs an
// independent member, say), and then the people it carried sit in the page's table until the reader fixes it. That table is the
// reader's own work in this browser: a refresh, or leaving and coming back in the same tab, must not lose it, and the screen
// says they are not appointed yet. Once the committee is appointed the draft is gone.
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import PrepareScreen from "./PrepareScreen.vue";

const FIXTURES = import.meta.glob("../fixtures/*.json", { eager: true, import: "default" });
const world = (stage) => JSON.parse(JSON.stringify(FIXTURES[`../fixtures/${stage}.json`].ao));
const settle = async () => {
	for (let i = 0; i < 4; i += 1) await nextTick();
};
const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const REFUSAL = { ok: false, code: "BOP_INDEPENDENT_MEMBER_REQUIRED", guard: { reason_code: "BOP_INDEPENDENT_MEMBER_REQUIRED", headline: "The opening committee needs an independent third member", message: "Appoint someone not involved.", fixes: [{ fix_id: "add_member", label: "Add an independent third member", kind: "focus", primary: true }] }, errors: { "member@x.test": "Involved in processing this Tender." } };
const PEOPLE = ["chair@x.test", "member@x.test"].map((id) => ({ id, label: `Name of ${id}`, detail: "Officer · Finance", section: "rest", disabled_reason: null, extra: { designation: "Officer", department: "Finance", independent_blocker: "" } }));

beforeEach(() => {
	sessionStorage.clear();
	globalThis.window.frappe = globalThis.frappe;
	globalThis.frappe.session = { user: "ao@x.test" };
	globalThis.frappe.call = async ({ args }) => ({ message: { rows: PEOPLE, total: PEOPLE.length, limit: 20, typed: !!args.query, labels: { noun: "person", plural: "people", near: "Your department", rest: "Everyone else", hint: "" } } });
});
afterEach(() => {
	document.body.innerHTML = "";
});

const mountIt = (data, props = {}) => mount(PrepareScreen, { attachTo: document.body, props: { data, pending: false, ...props } });
const tableRows = (w) => w.findAll('[data-testid="bop-committee-draft"] tbody tr').map((r) => r.attributes("data-user"));

// the reader opens Add members, chooses both people, and appoints; the server refuses (no independent member)
async function appointAndBeRefused(w) {
	await w.get('[data-testid="bop-add-member"]').trigger("click");
	await settle();
	await wait(20);
	const input = w.get("#bop-add-member-person");
	await input.trigger("keydown", { key: "Enter" });
	await wait(10);
	await input.trigger("keydown", { key: "Enter" });
	await wait(10);
	await w.get('[data-testid="bop-staged-role-member@x.test"]').setValue("Member");
	await w.get('[data-testid="bop-add-member-confirm"]').trigger("click");
	await settle();
	await w.setProps({ pending: true });
	await w.setProps({ pending: false, refusal: REFUSAL });
	await settle();
}

describe("the committee left in the table by a refused appointment", () => {
	it("is what Appoint sent, the dialog closes on the page's guard, and the table says why a person was refused", async () => {
		const w = mountIt(world("prepared"));
		await appointAndBeRefused(w);
		expect(w.emitted("appoint")[0][0].map((m) => [m.user, m.committee_role])).toEqual([["chair@x.test", "Chair and recorder"], ["member@x.test", "Member"]]);
		expect(w.find('[data-testid="bop-add-member-dialog"]').exists()).toBe(false);
		expect(tableRows(w)).toEqual(["chair@x.test", "member@x.test"]);
		expect(w.get('[data-testid="bop-row-error-member@x.test"]').text()).toBe("Involved in processing this Tender.");
		expect(w.find('[data-testid="bop-row-error-chair@x.test"]').exists()).toBe(false);
		w.unmount();
	});

	it("survives a refresh: the same people and roles come back, and the screen says they are not appointed yet", async () => {
		const first = mountIt(world("prepared"));
		await appointAndBeRefused(first);
		expect(first.get('[data-testid="bop-draft-note"]').text()).toContain("Not appointed yet");
		first.unmount(); // a refresh: the page is rebuilt from the server's answer, which holds no draft

		const again = mountIt(world("prepared"));
		await settle();
		expect(tableRows(again)).toEqual(["chair@x.test", "member@x.test"]);
		expect(again.text()).toContain("Name of chair@x.test");
		expect(again.get('[data-testid="bop-draft-note"]').text()).toContain("kept in this browser");
		await again.get('[data-testid="bop-remove-chair@x.test"]').trigger("click");
		await settle();
		again.unmount();
		expect(tableRows(mountIt(world("prepared")))).toEqual(["member@x.test"]); // a removal is kept too
	});

	it("is kept for this opening and this person only", async () => {
		const first = mountIt(world("prepared"));
		await appointAndBeRefused(first);
		first.unmount();
		const other = world("prepared");
		other.opening.opening_id = "BOC-OTHER-1";
		expect(tableRows(mountIt(other))).toEqual([]);
		globalThis.frappe.session = { user: "someone.else@x.test" };
		expect(tableRows(mountIt(world("prepared")))).toEqual([]);
	});

	it("is gone once the committee is appointed, and a damaged store changes nothing", async () => {
		const first = mountIt(world("prepared"));
		await appointAndBeRefused(first);
		first.unmount();
		const appointed = mountIt(world("appointed")); // the opening now has its committee
		await settle();
		expect(appointed.find('[data-testid="bop-committee-draft"]').exists()).toBe(false);
		appointed.unmount();
		expect(tableRows(mountIt(world("prepared")))).toEqual([]); // and the stale draft was dropped, not kept for later

		const key = "kt.bop.draft.ao@x.test.BOC-MOH-2099-001";
		sessionStorage.setItem(key, "{not json");
		expect(tableRows(mountIt(world("prepared")))).toEqual([]);
		sessionStorage.setItem(key, JSON.stringify([{ user: 5 }, { user: "a@x", committee_role: "Not a role" }]));
		expect(tableRows(mountIt(world("prepared")))).toEqual([]);
	});
});

describe("the dialog while the appointment runs", () => {
	it("stays open on a failure that is not the page's guard, showing it in the dialog, and closes once the committee is appointed", async () => {
		const w = mountIt(world("prepared"));
		await w.get('[data-testid="bop-add-member"]').trigger("click");
		await settle();
		await wait(20);
		await w.get("#bop-add-member-person").trigger("keydown", { key: "Enter" });
		await wait(10);
		await w.get('[data-testid="bop-add-member-confirm"]').trigger("click");
		await w.setProps({ pending: true });
		await w.setProps({ pending: false, error: "The action could not be completed." });
		await settle();
		expect(w.get('[data-testid="bop-add-members-note"]').text()).toBe("The action could not be completed.");
		w.unmount();
	});
});
