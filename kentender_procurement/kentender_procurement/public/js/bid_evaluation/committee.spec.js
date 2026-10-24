// EVL-CHG-001 v0.8 §3, §9.3 (D02-A, D02-NOT-RECORDED, D02-DELEGATE, D02-REPLACE), EVL-A18, EVL-A19, EVL-A20:
// the department is read-only text from the person's home organisation unit and the
// appointment reference is never a field.
import { describe, expect, it } from "vitest";

import { NOT_RECORDED_NOTICE, SECRETARY_NOTE, appoint, delegate, departmentCell, historyLines, replace, secretaryFact } from "./screens/committee.js";

// A person chosen in the shared record picker leaves their id, name and facts in the form (`<field>__label`, `<field>__extra`),
// so the screen reads the department from the choice itself, never from a list of everyone.
const HR = "Human Resources Management and Development";
const form = {
	m0_user: "grace", m0_user__label: "Grace Wambui", m0_user__extra: { department: HR },
	m1_user: "esther", m1_user__label: "Esther Muthoni", m1_user__extra: { department: "" },
};
const data = { tender: "TND-MOH-2027-033", title: "Supply of laptops", guidance: {}, committee: { members: [] }, viewer: {} };

const names = (board) => JSON.stringify(board).match(/"name":"[^"]+"/g) || [];

describe("the department of a chosen person", () => {
	it("is blank until a person is chosen", () => {
		expect(departmentCell(undefined, "")).toBe("");
	});
	it("is the home unit's name as plain text", () => {
		expect(departmentCell({ department: HR }, "grace")).toBe(HR);
	});
	it("reads Not recorded with its notice when no home unit is recorded", () => {
		expect(departmentCell({ department: "" }, "esther")).toEqual({ text: "Not recorded", note: NOT_RECORDED_NOTICE });
		expect(departmentCell(undefined, "esther")).toEqual({ text: "Not recorded", note: NOT_RECORDED_NOTICE });
		expect(NOT_RECORDED_NOTICE).toBe("Department not recorded. Ask your KenTender administrator to record it.");
	});
});

describe("the appointment forms", () => {
	const ctx = { data, form, errors: {}, record: { appointments: [] } };

	it("D02-A has no department input and no appointment-reference field", () => {
		const board = appoint(ctx);
		const text = JSON.stringify(board);
		expect(text).not.toContain("appointment_reference");
		expect(text).not.toContain("_department");
		expect(board.pri.fields || board.pri.spec?.fields || []).not.toContain("appointment_reference");
		expect(board.cons).toBe("The appointment reference is created when you appoint the committee. The Head of Procurement Function is recorded as the evaluation secretary.");
		expect(SECRETARY_NOTE).toBe("The Head of Procurement Function is recorded as the evaluation secretary.");
		expect(text).not.toContain("assign_secretary");
	});
	it("D02-A shows each chosen person's department as text beside the person", () => {
		const table = appoint(ctx).blocks.find((b) => b.k === "table");
		expect(table.rows[0][1]).toBe(HR);
		expect(table.rows[1][1]).toEqual({ text: "Not recorded", note: NOT_RECORDED_NOTICE });
		expect(table.rows[2][1]).toBe("");
	});
	it("D02-A names each person with the shared picker, for this Tender, with the other rows already taken", () => {
		const table = appoint(ctx).blocks.find((b) => b.k === "table");
		expect(table.rows[0][0]).toMatchObject({ picker: "m0_user", source: "bid_evaluation.committee_member", testid: "evl-member-0-user",
			context: { tender_reference: "TND-MOH-2027-033", mode: "appoint", taken: ["esther"] } });
		expect(table.rows[1][0].context.taken).toEqual(["grace"]);
		expect(table.rows[2][0].context.taken).toEqual(["grace", "esther"]);
		expect(table.rows[0][0]).toMatchObject({ value: "grace", chosenLabel: "Grace Wambui" });
		expect(table.rows.every((r) => !("select" in r[0]))).toBe(true); // the person column no longer a dropdown; Capacity (Chair or Member) stays one
	});
	it("D02-DELEGATE and D02-REPLACE take no typed department or reference", () => {
		const sec = delegate({ data: { ...data, committee: { members: [], secretary: { name: "Charles Mutiso", basis: "By office" }, can_delegate: true } }, form: { secretary: "brian", secretary__label: "Brian Wafula" } });
		const text = JSON.stringify(sec);
		expect(text).not.toContain("appointment_reference");
		expect(text).not.toContain("department");
		expect(sec.title).toBe("Delegate secretary duties");
		const person = sec.blocks.find((b) => b.picker);
		expect(person).toMatchObject({ picker: true, name: "secretary", source: "bid_evaluation.secretary", context: { tender_reference: "TND-MOH-2027-033" } });
		expect(sec.pri.args.method).toBe("delegate_secretary");
		expect(sec.pri.args.fields).toEqual(["secretary"]);
		expect(sec.guidance).toEqual({ answer: null, journey: null });
		expect(sec.cons).toBe("Brian Wafula will organise the evaluation record. This is your written appointment and a new reference is created. They will have no vote, finding or signature.");
		expect(sec.blocks[0].rows || sec.blocks[0].pairs || JSON.stringify(sec.blocks[0])).toContain("Charles Mutiso, Head of Procurement Function, by office");
		const rep = replace({ data: { ...data, committee: { members: [{ user: "m", name: "M", capacity: "Member", department: "ICT", declaration: "Conflict declared" }] } }, form: { incoming: "grace", incoming__label: "Grace Wambui", incoming__extra: { department: HR } }, errors: {}, record: {} });
		expect(JSON.stringify(rep)).not.toContain("appointment_reference");
		expect(rep.blocks.find((b) => b.picker)).toMatchObject({ picker: true, name: "incoming", source: "bid_evaluation.committee_member", context: { tender_reference: "TND-MOH-2027-033", mode: "replace" } });
		expect(JSON.stringify(rep.blocks)).toContain(HR); // the incoming person's department, from the choice
		expect(JSON.stringify(rep.pri)).not.toContain("department");
	});
	it("names the current secretary and how they hold the duties", () => {
		expect(secretaryFact({ name: "Charles Mutiso", basis: "By office" })).toBe("Charles Mutiso, Head of Procurement Function, by office");
		expect(secretaryFact({ name: "Brian Wafula", basis: "Written appointment" })).toBe("Brian Wafula, by written appointment of the Head of Procurement Function");
		expect(secretaryFact(null)).toBe("");
	});
});

describe("the appointment history", () => {
	it("shows the reference, the appointing officer, the time and the roster, then each completed department", () => {
		const lines = historyLines([
			{ kind: "Initial", reference: "MOH/EVAL/033/2027", by: "Amina Hassan", at: "11 Jun 2027, 09:00 EAT", members: [{ name: "Grace Wambui", capacity: "Chair" }, { name: "Peter Mugo", capacity: "Member" }] },
			{ kind: "Department recorded", person: "Esther Muthoni", department: "Finance", by: "Administrator", at: "11 Jun 2027, 09:30 EAT" },
		]);
		expect(lines).toEqual([
			"Initial · MOH/EVAL/033/2027 · appointed by Amina Hassan · 11 Jun 2027, 09:00 EAT",
			"Members: Grace Wambui (Chair), Peter Mugo (Member)",
			"Department recorded: Finance for Esther Muthoni · recorded by Administrator · 11 Jun 2027, 09:30 EAT",
		]);
	});
	it("lists the secretary by office and each written delegation, never editing the earlier", () => {
		const lines = historyLines([
			{ kind: "Secretary by office", person: "Charles Mutiso", appointment: "MOH/EVAL/033/2027", reference: "MOH/EVAL/SEC/033/2027", by: "Amina Hassan", at: "11 Jun 2027, 09:00 EAT" },
			{ kind: "Delegated", person: "Brian Wafula", reference: "MOH/EVAL/SEC/033/2027-R1", by: "Charles Mutiso", at: "11 Jun 2027, 09:05 EAT" },
		]);
		expect(lines).toEqual([
			"Secretary by office · Charles Mutiso · By office — Head of Procurement Function · appointed on the Accounting Officer's appointment MOH/EVAL/033/2027 · MOH/EVAL/SEC/033/2027 · 11 Jun 2027, 09:00 EAT",
			"Delegated · Brian Wafula · written appointment by Charles Mutiso, Head of Procurement Function · MOH/EVAL/SEC/033/2027-R1 · 11 Jun 2027, 09:05 EAT",
		]);
	});
});
