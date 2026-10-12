// Committee and declaration (EVL-CHG-001 v0.4 §9.3; boards D02-A, D02-DELEGATE,
// D02-D, D02-CONFLICT, D02-REPLACE, D02-INELIGIBLE, D02-INTAKE-FIRST,
// D02-DECLARE-FIRST, D02-UNABLE). Appointment and declaration are the only
// setup a viewer does here; none of these screens shows a bid fact.
import { at, cb, ds, f, fi, ra, tb } from "../board/model.js";
import { cmd, guidance, nav, rosterTable } from "./common.js";

const MAX_MEMBERS = 5;

function personOptions(candidates, blank = "Choose a person") {
	return [{ value: "", label: blank }].concat((candidates || []).map((c) => ({ value: c.user, label: c.name })));
}

export function memberRows(form) {
	const count = Math.min(MAX_MEMBERS, Math.max(3, Number(form.member_count || 3)));
	return Array.from({ length: count }, (_x, i) => i);
}

// The department of a chosen person: their home organisation unit as read-only text,
// blank until a person is chosen, or Not recorded with its notice when none is recorded
// (EVL-CHG-001 v0.7 §3, D02-A and D02-NOT-RECORDED). Never an input.
export const NOT_RECORDED_NOTICE = "Department not recorded. Ask your KenTender administrator to record it.";

export function departmentCell(candidates, user) {
	if (!user) return "";
	const person = (candidates || []).find((c) => c.user === user) || {};
	return person.department ? person.department : { text: "Not recorded", note: NOT_RECORDED_NOTICE };
}

// What the appointment also does (EVL-CHG-001 v0.8 §3): the Head of Procurement Function is recorded as the secretary.
export const SECRETARY_NOTE = "The Head of Procurement Function is recorded as the evaluation secretary.";

// D02-A / D02-INTAKE-FIRST: the Accounting Officer's appointment form.
export function appoint(ctx) {
	const { data, form, errors } = ctx;
	const opts = personOptions(ctx.candidates);
	const capacities = [{ value: "Chair", label: "Chair" }, { value: "Member", label: "Member" }];
	const rows = memberRows(form).map((i) => [
		{ select: `m${i}_user`, options: opts, testid: `evl-member-${i}-user`, error: (errors.members || {})[i] },
		departmentCell(ctx.candidates, form[`m${i}_user`]),
		{ select: `m${i}_capacity`, options: capacities, testid: `evl-member-${i}-capacity` },
	]);
	const history = (ctx.record && ctx.record.appointments) || [];
	const blocks = [
		f(["Tender", data.tender], ["Title", data.title]),
		tb(["Person", "Department", "Capacity"], rows, { title: "Committee members", caption: "Each member declares conflicts before viewing bids.", testid: "evl-members" }),
	];
	if (memberRows(form).length < MAX_MEMBERS) blocks.push({ k: "links", links: [{ label: "Add a member", action: "add-member" }], testid: "evl-add-member" });
	blocks.push(ds("Appointment history", history.length ? historyLines(history) : "No earlier appointment."));
	return {
		title: "Appoint evaluation committee", desc: `${data.tender} · ${data.title}`, guidance: guidance(data), blocks,
		pri: cmd("Appoint committee", "appoint_committee", { values: { compose: "members" }, fields: [], versioned: true, after: [] }),
		sec: [nav("Back to tender", "tender")],
		cons: `The appointment reference is created when you appoint the committee. ${SECRETARY_NOTE}`,
	};
}

// Appointment history (EVL-CHG-001 v0.7 §3): each appointment with its generated reference, the appointing officer, the time and the
// roster it produced, each later completion of a Not recorded department and every secretary record (by office, then each written
// delegation, EVL-CHG-001 v0.8 §3). Nothing here is typed by a user.
export function historyLines(history) {
	const lines = [];
	history.forEach((h) => {
		if (h.kind === "Department recorded") {
			lines.push(`Department recorded: ${h.department} for ${h.person} · recorded by ${h.by} · ${h.at}`);
			return;
		}
		if (h.kind === "Secretary by office") {
			lines.push(`Secretary by office · ${h.person} · By office — Head of Procurement Function · appointed on the Accounting Officer's appointment ${h.appointment} · ${h.reference} · ${h.at}`);
			return;
		}
		if (h.kind === "Delegated") {
			lines.push(`Delegated · ${h.person} · written appointment by ${h.by}, Head of Procurement Function · ${h.reference} · ${h.at}`);
			return;
		}
		lines.push(`${h.kind} · ${h.reference} · appointed by ${h.by} · ${h.at}${h.reason ? ` — ${h.reason}` : ""}`);
		if ((h.members || []).length) lines.push(`Members: ${h.members.map((m) => `${m.name} (${m.capacity})`).join(", ")}`);
	});
	return lines;
}

// The current secretary as one read-only fact (EVL-CHG-001 v0.8 §3): who, and how they came to hold the duties.
export function secretaryFact(sec) {
	if (!sec) return "";
	return sec.basis === "By office" ? `${sec.name}, Head of Procurement Function, by office` : `${sec.name}, by written appointment of the Head of Procurement Function`;
}

// D02-DELEGATE: the authorised Head of Procurement Function's written appointment of a procurement officer as secretary
// (section 46(4)(c) of the Act). Reached from the Delegate secretary duties action; no task asks for it, so it states no next
// step and carries no tracker. No department or reference is typed.
export function delegate(ctx) {
	const { data, form } = ctx;
	const sec = (data.committee || {}).secretary || null;
	const chosen = (ctx.candidates || []).find((c) => c.user === (form || {}).secretary);
	const blocks = [
		f(["Tender", data.tender], ["Title", data.title], ["Current secretary", secretaryFact(sec)]),
		fi("Person", "", { select: true, req: true, name: "secretary", options: personOptions(ctx.candidates) }),
	];
	return {
		title: "Delegate secretary duties", desc: "Appoint a procurement officer to act as secretary of this evaluation.",
		guidance: { answer: null, journey: null }, notInvolved: " ", blocks,
		pri: cmd("Delegate secretary duties", "delegate_secretary", { fields: ["secretary"], versioned: true, after: [] }),
		sec: [nav("Back to evaluation", [])],
		cons: `${chosen ? chosen.name : "The person you choose"} will organise the evaluation record. This is your written appointment and a new reference is created. They will have no vote, finding or signature.`,
	};
}

// D02-D / D02-CONFLICT: the member's own declaration (standalone: no tracker).
export function declaration(ctx) {
	const { data, form, user } = ctx;
	const me = ((data.committee || {}).members || []).find((m) => m.user === user) || {};
	const conflict = form.choice === "Declare a conflict";
	const blocks = [
		f(["Tender", data.tender], ["Title", data.title], ["Your capacity", `${me.capacity || "Member"} · ${me.department || ""}`]),
		ra("Declaration", ["No conflict to declare", "Declare a conflict"], conflict ? 1 : 0, { name: "choice" }),
	];
	if (conflict) blocks.push(fi("Describe the conflict", "", { area: true, req: true, rows: 2, name: "conflict_description" }));
	blocks.push(cb("I will keep bid information confidential and use it only for this evaluation.", false, { name: "confidentiality_accepted" }));
	return {
		title: "Your evaluation declaration", desc: `${data.tender} · ${data.title}`,
		guidance: guidance(data, { headline: "Declare any conflict before viewing bids.", journey: false }), blocks,
		pri: cmd("Save declaration", "declare_interest", { fields: ["choice", "conflict_description", "confidentiality_accepted"], after: [] }),
		sec: [nav("Back to evaluation", [])],
		cons: conflict ? "You will not be able to view bids while this conflict is being resolved." : "",
	};
}

// D02-DECLARE-FIRST: an undeclared member after intake sees no bid content.
export function declareFirst(ctx) {
	const { data, user } = ctx;
	const me = ((data.committee || {}).members || []).find((m) => m.user === user) || {};
	return {
		title: data.title, desc: data.tender, guidance: guidance(data),
		blocks: [f(["Your capacity", `${me.capacity || "Member"} · ${me.department || ""}`], ["Appointment", (data.committee || {}).appointment_reference || ""])],
		pri: nav("Complete declaration", "declaration"), sec: [nav("Back to evaluations", "workspace")],
	};
}

// D02-REPLACE / D02-INELIGIBLE: the Accounting Officer replaces a member.
export function replace(ctx) {
	const { data, form, errors } = ctx;
	const members = (data.committee || {}).members || [];
	const blocked = members.find((m) => m.declaration === "Conflict declared" || m.unavailable) || members.find((m) => m.user === form.outgoing) || {};
	const statement = (ctx.record && (ctx.record.declarations || []).filter((d) => d.member === blocked.name && d.choice === "Declare a conflict").slice(-1)[0]) || null;
	const incoming = (ctx.candidates || []).find((c) => c.user === form.incoming) || {};
	const blocks = [
		tb(["Person", "Department", "Capacity", "Declaration"], members.map((m) => [m.name, m.department, m.capacity, m.unavailable ? "Unable to serve" : m.declaration]), { title: "Current committee", sec: true }),
	];
	if (blocked.name) blocks.push(at(blocked.declaration === "Conflict declared" ? `${blocked.name} declared a conflict` : `${blocked.name} recorded inability to serve`, statement ? statement.description || "" : ""));
	blocks.push(
		fi("Incoming person", "", { select: true, req: true, name: "incoming", options: personOptions(ctx.candidates), err: errors.incoming || "", errd: errors.incoming_detail || "" }),
		f(["Department", form.incoming ? (incoming.department || "Not recorded") : ""], ["Capacity", blocked.capacity || "Member"]),
		fi("Reason", "", { area: true, req: true, rows: 2, name: "reason" }),
	);
	return {
		title: "Replace committee member", desc: `${data.tender} · ${data.title}`, guidance: guidance(data), blocks,
		pri: cmd("Replace member", "replace_member", { values: { outgoing: blocked.user, compose: "incoming", capacity: blocked.capacity || "Member" },
			fields: ["incoming", "reason"], versioned: true, after: [] }),
		sec: [nav("Keep current appointment", [])],
		cons: "The new member must declare interests and review the evaluation. Any report being signed will need a new version. The appointment reference is created when you replace the member.",
	};
}

// D02-UNABLE: the member records why they cannot continue.
export function unable(ctx) {
	const { data } = ctx;
	return {
		title: "Committee record", desc: `${data.tender} · ${data.title}`, guidance: guidance(data, { headline: "Record why you cannot continue on the committee." }),
		blocks: [rosterTable(data), fi("Reason", "", { area: true, req: true, rows: 2, name: "reason" })],
		pri: cmd("Record inability to serve", "record_unavailability", { fields: ["reason"], after: [] }),
		sec: [nav("Back to evaluation", [])],
	};
}
