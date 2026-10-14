// The two places a committee member is named, now through the shared record picker: the Add member
// dialog (Prepare opening) and the replacement form (after an interruption). Both ask the same source
// the same question — who may take this role on this Tender — and both let the role change the answer.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { mount } from "@vue/test-utils";
import { nextTick } from "vue";
import AddMemberDialog from "./AddMemberDialog.vue";
import ReplacementForm from "./ReplacementForm.vue";

const LABELS = { noun: "person", plural: "people", near: "Your department", rest: "Everyone else", hint: "" };
const person = (id, label, detail, disabled_reason = null) => ({
	id, label, detail, section: "rest", disabled_reason,
	// every row says whether the person could not be the independent member (Kevin prepared the Tender)
	extra: { designation: detail.split(" · ")[0], department: detail.split(" · ")[1] || "", independent_blocker: id === "kevin@x" ? "Involved in processing this Tender." : "" },
});
let calls;
let answer;

beforeEach(() => {
	vi.useFakeTimers();
	calls = [];
	answer = (endpoint, args) => {
		const role = args.context ? JSON.parse(args.context).role : undefined;
		const rows = [
			person("brian@x", "Brian Achieng", "Procurement Officer · Supply Chain Management"),
			person("kevin@x", "Kevin Mwangi", "Budget Officer · Finance", role === "Independent member" ? "Involved in processing this Tender." : null),
			person("zoe@x", "Zoë Mwangi", "Auditor · Internal Audit"),
		];
		if (endpoint === "resolve") return { rows: JSON.parse(args.ids).map((id) => rows.find((r) => r.id === id)).filter(Boolean) };
		const matching = args.query ? rows.filter((r) => `${r.label} ${r.detail} ${r.id}`.toLowerCase().includes(args.query.toLowerCase())) : rows;
		return { rows: matching, total: matching.length, limit: 20, typed: !!args.query, labels: LABELS };
	};
	globalThis.window.frappe = globalThis.frappe;
	globalThis.frappe.call = async ({ method, args }) => {
		calls.push({ method, args });
		return { message: answer(method.split(".").pop(), args) };
	};
});
afterEach(() => {
	vi.useRealTimers();
	document.body.innerHTML = "";
});
const flush = async (ms = 0) => {
	await vi.advanceTimersByTimeAsync(ms);
	await nextTick();
};
const choose = async (w, id) => {
	const input = w.get(`#${id}`);
	await input.trigger("focus");
	await flush();
	await input.trigger("keydown", { key: "Enter" });
	await flush();
};

describe("Add members", () => {
	const make = (props = {}) => mount(AddMemberDialog, { attachTo: document.body, props: { tender: "TDR-1", draft: [], pending: false, error: "", ...props } });
	const input = (w) => w.get("#bop-add-member-person");
	const optionNames = (w) => w.findAll(".kt-picker-name").map((n) => n.text());
	const stagedUsers = (w) => w.findAll(".bop-staged-row").map((r) => r.attributes("data-user"));
	const addActive = async (w) => {
		await input(w).trigger("keydown", { key: "Enter" });
		await flush(10);
	};

	it("shows the list beside the field from the start, asking the server for this Tender with the table's people taken", async () => {
		const w = make();
		await flush(10);
		expect(w.get('[data-testid="kt-picker-list"]').classes()).toContain("is-inline");
		expect(calls[0].method).toBe("kentender_core.api.record_picker.search");
		expect(calls[0].args.source).toBe("bid_opening.committee_member");
		expect(JSON.parse(calls[0].args.context)).toEqual({ tender: "TDR-1", taken: [] });
		expect(w.get('[data-testid="bop-staged-title"]').text()).toBe("To appoint");
		expect(w.get('[data-testid="bop-staged-empty"]').text()).toBe("People you choose appear here.");
		expect(w.get('[data-testid="bop-add-member-confirm"]').text()).toBe("Appoint members");
		expect(w.get('[data-testid="bop-add-member-confirm"]').attributes("disabled")).toBeDefined();
		w.unmount();
	});

	it("adds each choice to To appoint without closing the list, greys the added person, and counts them", async () => {
		const w = make();
		await flush(10);
		await addActive(w); // brian
		await addActive(w); // kevin: the next choosable row
		await addActive(w); // zoe
		expect(stagedUsers(w)).toEqual(["brian@x", "kevin@x", "zoe@x"]);
		expect(w.get('[data-testid="bop-staged-title"]').text()).toBe("To appoint · 3");
		expect(optionNames(w)).toEqual(["Brian Achieng", "Kevin Mwangi", "Zoë Mwangi"]); // the same list, in the same place
		expect(w.findAll(".kt-picker-option").every((o) => o.attributes("aria-disabled") === "true")).toBe(true);
		expect(w.findAll(".kt-picker-reason")[0].text()).toBe("Added to this list");
		expect(w.get('[role="status"][aria-live="polite"]').text()).toBe("Added Zoë Mwangi. 3 to appoint.");
		expect(w.get('[data-testid="bop-add-member-confirm"]').text()).toBe("Appoint 3 members");
		w.unmount();
	});

	it("suggests chair and recorder first, then the independent member, then members, and each role can be changed", async () => {
		const w = make();
		await flush(10);
		await addActive(w);
		await addActive(w);
		await addActive(w);
		const role = (user) => w.get(`[data-testid="bop-staged-role-${user}"]`).element.value;
		expect([role("brian@x"), role("kevin@x"), role("zoe@x")]).toEqual(["Chair and recorder", "Independent member", "Member"]);
		await w.get('[data-testid="bop-staged-role-zoe@x"]').setValue("Recorder");
		expect(role("zoe@x")).toBe("Recorder");
		w.unmount();
	});

	it("says beside a person who could not be the independent member, and will not appoint until their role is changed", async () => {
		const w = make();
		await flush(10);
		await addActive(w); // brian
		await addActive(w); // kevin, suggested Independent member, but involved
		expect(w.get('[data-testid="bop-staged-error-kevin@x"]').text()).toBe("Involved in processing this Tender.");
		expect(w.get('[data-testid="bop-add-member-confirm"]').attributes("disabled")).toBeDefined();
		await w.get('[data-testid="bop-staged-role-kevin@x"]').setValue("Member");
		expect(w.find('[data-testid="bop-staged-error-kevin@x"]').exists()).toBe(false);
		expect(w.get('[data-testid="bop-add-member-confirm"]').attributes("disabled")).toBeUndefined();
		w.unmount();
	});

	it("removing a person takes them off the list and makes them choosable again", async () => {
		const w = make();
		await flush(10);
		await addActive(w);
		await w.get('[data-testid="bop-staged-remove-brian@x"]').trigger("click");
		await flush(10);
		expect(stagedUsers(w)).toEqual([]);
		expect(w.findAll(".kt-picker-option")[0].attributes("aria-disabled")).toBe("false");
		w.unmount();
	});

	it("appoints everyone with one action, handing over names, roles and designations", async () => {
		const w = make();
		await flush(10);
		await addActive(w);
		await addActive(w);
		await w.get('[data-testid="bop-staged-role-kevin@x"]').setValue("Member");
		await w.get('[data-testid="bop-add-member-confirm"]').trigger("click");
		expect(w.emitted("appoint")[0][0]).toEqual([
			{ user: "brian@x", committee_role: "Chair and recorder", full_name: "Brian Achieng", designation: "Procurement Officer" },
			{ user: "kevin@x", committee_role: "Member", full_name: "Kevin Mwangi", designation: "Budget Officer" },
		]);
		w.unmount();
	});

	it("counts the people already in the page's table, who all appoint together", async () => {
		const w = make({ draft: [{ user: "chair@x", committee_role: "Chair and recorder" }, { user: "m@x", committee_role: "Independent member" }] });
		await flush(10);
		expect(JSON.parse(calls[0].args.context).taken).toEqual(["chair@x", "m@x"]); // the table's people are already on the committee
		await addActive(w);
		expect(w.get('[data-testid="bop-add-member-confirm"]').text()).toBe("Appoint 3 members");
		expect(w.get('[data-testid="bop-staged-role-brian@x"]').element.value).toBe("Member"); // the table already has a chair and an independent member
		w.unmount();
	});

	it("is busy while the appointment runs, and shows a failure in the dialog", async () => {
		const busy = make({ pending: true });
		await flush(10);
		await addActive(busy);
		expect(busy.get('[data-testid="bop-add-members-note"]').text()).toBe("Appointing…");
		expect(busy.get('[data-testid="bop-add-member-confirm"]').attributes("disabled")).toBeDefined();
		expect(busy.get('[data-testid="bop-add-members-cancel"]').attributes("disabled")).toBeDefined();
		busy.unmount();
		const failed = make({ error: "The action could not be completed." });
		expect(failed.get('[data-testid="bop-add-members-note"]').text()).toBe("The action could not be completed.");
		failed.unmount();
	});

	it("Esc clears the search first, and only a second Esc closes the dialog", async () => {
		const w = make();
		await flush(10);
		input(w).element.value = "ami";
		await input(w).trigger("input");
		await flush(300);
		await input(w).trigger("keydown", { key: "Escape" });
		await flush(10);
		expect(w.emitted("cancel")).toBeUndefined();
		expect(input(w).element.value).toBe("");
		await w.get('[data-testid="bop-add-member-dialog"]').trigger("keydown", { key: "Escape" });
		expect(w.emitted("cancel")).toHaveLength(1);
		w.unmount();
	});
});

describe("Replacement", () => {
	const members = [
		{ member_user: "chair@x", full_name: "Charles Mutiso", committee_role: "Chair and recorder", present: true },
		{ member_user: "gone@x", full_name: "Grace Gone", committee_role: "Independent member", present: false },
	];
	const make = () => mount(ReplacementForm, { attachTo: document.body, props: { tender: "TDR-1", members, pending: false, error: "" } });

	it("asks for someone to take the absent member's role, with the current committee already taken", async () => {
		const w = make();
		await w.get("#bop-replace-with").trigger("focus");
		await flush();
		expect(JSON.parse(calls[0].args.context)).toEqual({ tender: "TDR-1", role: "Independent member", taken: ["chair@x", "gone@x"] });
		w.unmount();
	});

	it("appoints the successor in the absent member's place, with the reason, once the person and reason are given", async () => {
		const w = make();
		const button = () => w.get('[data-testid="bop-replace-confirm"]');
		expect(button().attributes("disabled")).toBeDefined();
		await choose(w, "bop-replace-with");
		await w.get('[data-testid="bop-replace-reason"]').setValue("Left the organisation");
		expect(button().attributes("disabled")).toBeUndefined();
		await button().trigger("click");
		const { members: sent, reason } = w.emitted("appoint")[0][0];
		expect(reason).toBe("Left the organisation");
		expect(JSON.parse(sent)).toEqual([{ user: "chair@x", committee_role: "Chair and recorder" }, { user: "brian@x", committee_role: "Independent member" }]);
		w.unmount();
	});
});
