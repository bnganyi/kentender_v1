// PLN-CHG-001 v1.31 §10.12 — PublicationResultScreen component tests (U13).
//
// MVP 1 publication is manual: after statutory approval the Procurement Planner
// records the Treasury submission and the entity-website publication in one
// confirmation, and the system then runs the existing activation checks. The
// four status rows are four facts that do not prove each other; nothing here
// transmits, retries or reconciles (v1.30's technical recovery is retired).
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import PublicationResultScreen from "./PublicationResultScreen.vue";
import { CONFIRM_TURN, PREPARE_CORRECTED_TURN, WAITING_PLANNER, planJourney } from "./guidance.fixtures.js";

// Dates relative to the machine's own today, never hard-coded: the form refuses a date in the future.
const iso = (offsetDays = 0) => {
	const d = new Date();
	d.setDate(d.getDate() + offsetDays);
	return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
};
const TODAY = iso(0);

const STATEMENT = "I confirm that this approved version was submitted to the National Treasury and published on the entity’s website.";

const APPROVED_ROWS = [
	{ label: "Plan approval", state: "Approved", kind: "live" },
	{ label: "Treasury submission", state: "Not yet confirmed", kind: "attention" },
	{ label: "Website publication", state: "Not yet confirmed", kind: "attention" },
	{ label: "Use for procurement", state: "This plan is not yet active", kind: "pending" },
];
const CONFIRMED_ROWS = [
	APPROVED_ROWS[0],
	{ label: "Treasury submission", state: "Confirmed", kind: "live" },
	{ label: "Website publication", state: "Confirmed", kind: "live" },
	{ label: "Use for procurement", state: "Current plan", kind: "live" },
];
const CONFIRMATION = {
	id: "PPC-00001", state: "Current", record_version: 0,
	treasury_submitted_on: iso(-2), treasury_submitted_display: "10 Dec 2026",
	treasury_reference: "MOH/APP/2027/001", treasury_attachment: "/private/files/Treasury-dispatch-evidence-example.pdf",
	website_published_on: iso(-2), website_published_display: "10 Dec 2026",
	public_plan_url: "https://www.moh.example.test/procurement/annual-procurement-plan-2027-28", confirmation_acknowledged: true,
	recorded_by_name: "Mercy Kilonzo", recorded_display: "10 Dec 2026, 15:00 EAT", correction_reason: "",
};

function task(overrides = {}) {
	return {
		outcome: "OK",
		publication: "PUB-PLN-MOH-2027-001-V1",
		plan_reference: "PLN-MOH-2027-001",
		plan_title: "Ministry of Health Annual Procurement Plan 2027/28",
		version: { number: 1, status: "Approved — publication pending", reference: "PLN-MOH-2027-001-V1", record_version: 4 },
		header: { badge: "Awaiting confirmation", badge_kind: "attention" },
		publication_state: "Pending",
		statement: STATEMENT,
		status_rows: APPROVED_ROWS,
		confirmation: null,
		draft: null,
		historical_treasury: null,
		hold: { active: false },
		attempts: [],
		can_confirm: true,
		can_save_draft: true,
		can_correct: false,
		next_step: CONFIRM_TURN,
		journey: planJourney("publication", { holder: "Mercy Kilonzo", reduced: true }),
		...overrides,
	};
}

function make(props = {}) {
	return mount(PublicationResultScreen, { props: { task: task(), pending: false, errorSummary: "", ...props } });
}

async function fillAll(w, { reference = "MOH/APP/2027/001", tick = true } = {}) {
	await w.find('[data-testid="pub-treasury-date"]').setValue(TODAY);
	if (reference) await w.find('[data-testid="pub-treasury-reference"]').setValue(reference);
	await w.find('[data-testid="pub-website-date"]').setValue(TODAY);
	await w.find('[data-testid="pub-public-url"]').setValue("https://www.moh.example.test/plan");
	if (tick) await w.find('[data-testid="pub-statement"]').setValue(true);
}

describe("PublicationResultScreen — U13 awaiting confirmation", () => {
	it("shows four distinct facts in order", () => {
		const w = make();
		const rows = w.findAll('[data-testid="pub-status-row"]');
		expect(rows.map((r) => r.text())).toEqual([
			expect.stringContaining("Plan approval"),
			expect.stringContaining("Treasury submission"),
			expect.stringContaining("Website publication"),
			expect.stringContaining("Use for procurement"),
		]);
		expect(rows[1].text()).toContain("Not yet confirmed");
		expect(rows[3].text()).toContain("This plan is not yet active");
	});

	it("titles the page for the confirmation and replaces the badge with the next step and a one-line tracker", () => {
		const w = make();
		expect(w.find('[data-testid="pub-title"]').text()).toBe("Confirm publication of the annual plan");
		expect(w.text()).toContain("Record that the approved plan was submitted to the National Treasury and published on the entity’s website.");
		expect(w.find('[data-testid="pub-context"] .kt-status').exists()).toBe(false);
		expect(w.find(".kt-page-head .kt-next-step").text()).toBe("Your turn Confirm plan publication");
		expect(w.find(".kt-journey.is-reduced").text()).toBe("Stage 6 of 7: Publication — Mercy Kilonzo");
	});

	it("offers exactly the fields the owner named, in order, with the statement unchecked", () => {
		const w = make();
		const form = w.find('[data-testid="pub-form"]');
		expect(form.text()).toContain("Approved plan");
		expect(form.text()).toContain("PLN-MOH-2027-001");
		expect(form.find('[data-testid="pub-form-download"]').text()).toBe("Download approved plan");
		const labels = form.findAll("label.kt-label").map((l) => l.text());
		expect(labels).toEqual(["Treasury submission date", "Submission reference", "Submission evidence", "Entity website publication date", "Public plan URL"]);
		expect(form.find('[data-testid="pub-statement"]').element.checked).toBe(false);
		expect(form.text()).toContain(STATEMENT);
		// the channel, destination and time-of-day fields of v1.30 are gone
		for (const gone of ["pub-treasury-channel", "pub-treasury-destination", "pub-treasury-dispatch", "pub-treasury-sent"]) {
			expect(w.find(`[data-testid="${gone}"]`).exists()).toBe(false);
		}
	});

	it("keeps Confirm disabled, and says why, until the evidence is complete; a reference alone is enough", async () => {
		const w = make();
		const confirm = w.find('[data-testid="pub-confirm"]');
		expect(confirm.text()).toBe("Confirm plan publication");
		expect(confirm.attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="pub-confirm-hint"]').text()).toBe("Complete every field and tick the confirmation to confirm.");
		await fillAll(w, { tick: false });
		expect(w.find('[data-testid="pub-confirm"]').attributes("disabled")).toBeDefined();
		await w.find('[data-testid="pub-statement"]').setValue(true);
		expect(w.find('[data-testid="pub-confirm"]').attributes("disabled")).toBeUndefined();
	});

	it("needs a reference or an attachment, not both", async () => {
		const w = make();
		await fillAll(w, { reference: "" });
		expect(w.find('[data-testid="pub-confirm"]').attributes("disabled")).toBeDefined();
		await w.find('[data-testid="pub-treasury-reference"]').setValue("MOH/APP/2027/001");
		expect(w.find('[data-testid="pub-confirm"]').attributes("disabled")).toBeUndefined();
	});

	it("emits the confirmation with the entered values and nothing the server records itself", async () => {
		const w = make();
		await fillAll(w);
		await w.find('[data-testid="pub-confirm"]').trigger("click");
		const [values] = w.emitted("confirm")[0];
		expect(values).toEqual({
			treasury_submitted_on: TODAY, treasury_reference: "MOH/APP/2027/001", treasury_attachment: "",
			website_published_on: TODAY, public_plan_url: "https://www.moh.example.test/plan", confirmation_acknowledged: 1,
		});
	});

	it("saves a draft with whatever has been entered, and only then", async () => {
		const w = make();
		expect(w.find('[data-testid="pub-save-draft"]').attributes("disabled")).toBeDefined();
		await w.find('[data-testid="pub-treasury-reference"]').setValue("MOH/APP/2027/001");
		const save = w.find('[data-testid="pub-save-draft"]');
		expect(save.attributes("disabled")).toBeUndefined();
		await save.trigger("click");
		expect(w.emitted("save-draft")[0][0].treasury_reference).toBe("MOH/APP/2027/001");
	});

	it("shows a saved draft in the form and refills only when the draft really changed", async () => {
		const draft = { ...CONFIRMATION, id: "PPC-00009", state: "Draft", record_version: 2, treasury_reference: "DRAFT-REF", treasury_attachment: "" };
		const w = make({ task: task({ draft }) });
		expect(w.find('[data-testid="pub-treasury-reference"]').element.value).toBe("DRAFT-REF");
		await w.find('[data-testid="pub-treasury-reference"]').setValue("TYPED-SINCE");
		// a quiet refresh that carries the same draft must not discard what was typed (AGENTS.md §6.4)
		await w.setProps({ task: task({ draft: { ...draft } }) });
		expect(w.find('[data-testid="pub-treasury-reference"]').element.value).toBe("TYPED-SINCE");
		await w.setProps({ task: task({ draft: { ...draft, record_version: 3, treasury_reference: "SAVED-AGAIN" } }) });
		expect(w.find('[data-testid="pub-treasury-reference"]').element.value).toBe("SAVED-AGAIN");
	});

	it("has no Record Treasury, Publish, Retry or Check control, for anyone", () => {
		for (const overrides of [{}, { can_confirm: false, can_save_draft: false }, { publication_state: "Failed" }, { publication_state: "Indeterminate" }]) {
			const w = make({ task: task(overrides) });
			for (const gone of ["pub-record-treasury", "pub-correct-treasury", "pub-publish", "pub-retry", "pub-reconcile", "pub-unknown", "pub-treasury-dialog"]) {
				expect(w.find(`[data-testid="${gone}"]`).exists()).toBe(false);
			}
		}
	});

	it("header: View approved plan, Download approved plan and Download Plan data, in that order, each wired", async () => {
		const w = make();
		const actions = w.findAll('[data-testid="pub-view-plan"], [data-testid="pub-download-plan"], [data-testid="pub-download-plan-data"]');
		expect(actions.map((a) => a.text())).toEqual(["View approved plan", "Download approved plan", "Download Plan data"]);
		await w.find('[data-testid="pub-download-plan"]').trigger("click");
		await w.find('[data-testid="pub-form-download"]').trigger("click");
		await w.find('[data-testid="pub-download-plan-data"]').trigger("click");
		expect(w.emitted("download-plan")).toHaveLength(2);
		expect(w.emitted("download-plan-data")).toHaveLength(1);
	});
});

describe("PublicationResultScreen — saying what is wrong, and where", () => {
	// Found live 9 Oct 2026: "www.xyz.com" enabled Confirm, was refused with a generic sentence, and nothing
	// said which of five filled-in fields was wrong.
	const URL_PROBLEM = "Enter the address of the published plan, starting with http:// or https://.";
	const field = (w, name) => w.find(`[data-testid="pub-field-${name}"]`);
	const error = (w, name) => w.find(`[data-testid="pub-error-${name}"]`);

	it("rejects an address without http:// or https:// at the field, and keeps Confirm disabled until it is fixed", async () => {
		const w = make();
		await fillAll(w);
		expect(w.find('[data-testid="pub-confirm"]').attributes("disabled")).toBeUndefined();
		await w.find('[data-testid="pub-public-url"]').setValue("www.xyz.com");
		expect(error(w, "public_plan_url").text()).toBe(URL_PROBLEM);
		expect(field(w, "public_plan_url").classes()).toContain("pln-field-flagged");
		expect(w.find('[data-testid="pub-confirm"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="pub-confirm-hint"]').text()).toBe("Fix the highlighted fields to confirm.");
		// the fields that are fine stay quiet
		for (const ok of ["treasury_submitted_on", "treasury_reference", "website_published_on"]) {
			expect(error(w, ok).exists()).toBe(false);
		}
		await w.find('[data-testid="pub-public-url"]').setValue("https://www.xyz.com/plan");
		expect(error(w, "public_plan_url").exists()).toBe(false);
		expect(w.find('[data-testid="pub-confirm"]').attributes("disabled")).toBeUndefined();
	});

	it("applies the same date rules as the server: not in the future, website not before Treasury, Treasury not before approval", async () => {
		const approved = iso(-5);
		const w = make({ task: task({ today: TODAY, version: { number: 1, status: "Approved — publication pending", reference: "PLN-MOH-2027-001-V1", record_version: 4, approved_on: approved } }) });
		await fillAll(w);
		await w.find('[data-testid="pub-treasury-date"]').setValue(iso(-6));
		expect(error(w, "treasury_submitted_on").text()).toContain("The plan was approved on ");
		await w.find('[data-testid="pub-treasury-date"]').setValue(iso(-2));
		await w.find('[data-testid="pub-website-date"]').setValue(iso(-3));
		expect(error(w, "website_published_on").text()).toBe("The website publication date cannot be before the Treasury submission date.");
		await w.find('[data-testid="pub-website-date"]').setValue(iso(1));
		expect(error(w, "website_published_on").text()).toBe("A date in the future cannot be confirmed.");
		expect(w.find('[data-testid="pub-confirm"]').attributes("disabled")).toBeDefined();
		// the server's own date wins over the browser's: today is never "in the future"
		const early = make({ task: task({ today: iso(1) }) });
		await early.find('[data-testid="pub-website-date"]').setValue(iso(1));
		expect(error(early, "website_published_on").exists()).toBe(false);
	});

	it("shows what the server refused at its own field, in place of a summary that names nothing, and clears it on edit", async () => {
		const w = make({ errorSummary: "Public plan URL: " + URL_PROBLEM, errorFields: { public_plan_url: URL_PROBLEM } });
		expect(error(w, "public_plan_url").text()).toBe(URL_PROBLEM);
		expect(field(w, "public_plan_url").classes()).toContain("pln-field-flagged");
		// said once: the summary line stands down while the field carries it
		expect(w.find('[data-testid="pub-error"]').exists()).toBe(false);
		await w.find('[data-testid="pub-public-url"]').setValue("https://www.xyz.com/plan");
		expect(error(w, "public_plan_url").exists()).toBe(false);
	});

	it("still shows a refusal that names no field", () => {
		const w = make({ errorSummary: "This review has changed. Refresh before deciding.", errorFields: {} });
		expect(w.find('[data-testid="pub-error"]').text()).toBe("This review has changed. Refresh before deciding.");
	});

	it("marks a field the server refused in the correction form too", async () => {
		const w = make({
			task: task({
				publication_state: "Confirmed", version: { number: 1, status: "Active", reference: "PLN-MOH-2027-001-V1", record_version: 6 },
				status_rows: CONFIRMED_ROWS, confirmation: CONFIRMATION, can_confirm: false, can_save_draft: false, can_correct: true,
			}),
		});
		await w.find('[data-testid="pub-correct"]').trigger("click");
		await w.find('[data-testid="pub-correct-url"]').setValue("www.xyz.com");
		expect(w.find('[data-testid="pub-correct-error-public_plan_url"]').text()).toBe(URL_PROBLEM);
		expect(w.find('[data-testid="pub-correct-submit"]').attributes("disabled")).toBeDefined();
	});
});

describe("PublicationResultScreen — Save draft keeps unfinished work", () => {
	// Found live 9 Oct 2026: Save draft with an address that did not yet start with https:// saved nothing at all, and
	// nothing said so. A Draft is where unfinished work is kept; the rules apply when the Planner confirms.
	it("stays available while a field breaks a rule, and saves exactly what was typed", async () => {
		const w = make();
		await fillAll(w);
		await w.find('[data-testid="pub-public-url"]').setValue("www.xyz.com");
		expect(w.find('[data-testid="pub-error-public_plan_url"]').exists()).toBe(true);
		expect(w.find('[data-testid="pub-confirm"]').attributes("disabled")).toBeDefined();
		const save = w.find('[data-testid="pub-save-draft"]');
		expect(save.attributes("disabled")).toBeUndefined();
		await save.trigger("click");
		const [values] = w.emitted("save-draft")[0];
		expect(values.public_plan_url).toBe("www.xyz.com");
		expect(values.treasury_reference).toBe("MOH/APP/2027/001");
		expect(values.treasury_submitted_on).toBe(TODAY);
	});

	it("says when the draft was saved and that nothing has been confirmed", () => {
		const none = make();
		expect(none.find('[data-testid="pub-draft-saved"]').exists()).toBe(false);
		const draft = { ...CONFIRMATION, id: "PPC-00009", state: "Draft", record_version: 1, saved_display: "9 Oct 2026, 15:20 EAT", treasury_attachment: "" };
		const w = make({ task: task({ draft }) });
		expect(w.find('[data-testid="pub-draft-saved"]').text()).toBe("Draft saved 9 Oct 2026, 15:20 EAT. Nothing has been confirmed yet.");
	});

	it("says plainly that nothing was saved when the server refused, beside the field it names", () => {
		const w = make({ errorSummary: "Submission evidence: Attach the file again.", errorFields: { treasury_attachment: "Attach the file again. Use a PDF, PNG or JPG of 20 MB or less." } });
		expect(w.find('[data-testid="pub-not-saved"]').text()).toBe("Nothing was saved. Fix the highlighted fields and try again.");
		expect(w.find('[data-testid="pub-error-treasury_attachment"]').exists()).toBe(true);
		expect(make().find('[data-testid="pub-not-saved"]').exists()).toBe(false);
	});
});

describe("PublicationResultScreen — the recorded facts line up", () => {
	// Found live 9 Oct 2026: the address sat in a fourth column of a bottom-aligned row, wrapped to three lines, pushed
	// its neighbours' labels out of line and ran past the card. It is its own full-width fact; the rest share a top edge.
	const confirmed = () => task({
		publication_state: "Confirmed", version: { number: 1, status: "Active", reference: "PLN-MOH-2027-001-V1", record_version: 6 },
		status_rows: CONFIRMED_ROWS, confirmation: { ...CONFIRMATION, public_plan_url: "https://chatgpt.com/c/6ac8ac05-2d08-83ed-86ad-fc5613675d38" },
		can_confirm: false, can_save_draft: false, can_correct: true,
	});

	it("puts the address in a full-width fact of its own and the short facts in one top-aligned grid", () => {
		const w = make({ task: confirmed() });
		const grid = w.find('[data-testid="pub-confirmation"] .pln-facts');
		expect(grid.exists()).toBe(true);
		expect(grid.find('[data-testid="pub-fact-url"]').classes()).toContain("pln-fact-wide");
		expect(grid.find('[data-testid="pub-fact-url"] a').text()).toContain("https://chatgpt.com/c/");
		// the three short dates and the reference live beside each other, never beside the address
		const short = grid.findAll("[data-fact]").map((f) => f.attributes("data-fact"));
		expect(short).toEqual(["treasury_date", "reference", "website_date", "url", "confirmed_by", "confirmed_at"]);
		// no bottom-aligned shared meta row is left holding any of them
		expect(w.find('[data-testid="pub-confirmation"] .kt-meta-row').exists()).toBe(false);
	});

	it("lays out the previous details in the correction form the same way, with room before the fields", async () => {
		const w = make({ task: confirmed() });
		await w.find('[data-testid="pub-correct"]').trigger("click");
		const prior = w.find('[data-testid="pub-correct-prior"]');
		expect(prior.classes()).toContain("pln-facts");
		expect(prior.find(".pln-fact-wide").text()).toContain("https://chatgpt.com/c/");
		expect(w.find(".pln-correct-prior").exists()).toBe(true);
	});
});

describe("PublicationResultScreen — readers who are not the Planner", () => {
	it("sees the waiting line and the facts, never the form or a button", () => {
		const w = make({ task: task({ can_confirm: false, can_save_draft: false, next_step: WAITING_PLANNER }) });
		expect(w.find('[data-testid="pub-form"]').exists()).toBe(false);
		expect(w.find('[data-testid="pub-confirm"]').exists()).toBe(false);
		expect(w.find('[data-testid="pub-save-draft"]').exists()).toBe(false);
		expect(w.find(".kt-page-head .kt-next-step").text()).toContain("Waiting for Mercy Kilonzo (Procurement Planner) to confirm publication");
		expect(w.findAll('[data-testid="pub-status-row"]')).toHaveLength(4);
	});

	it("a hold lets the Planner save a Draft but not confirm", () => {
		const w = make({
			task: task({ can_confirm: false, hold: { active: true, reason: "A material defect was found in the approved content.", kind: "defect" } }),
		});
		expect(w.find('[data-testid="pub-hold"]').text()).toContain("Publication is on hold");
		expect(w.find('[data-testid="pub-save-draft"]').exists()).toBe(true);
		expect(w.find('[data-testid="pub-confirm"]').exists()).toBe(false);
		expect(w.find('[data-testid="pub-status-row"]').text()).toContain("Approved");
	});
});

describe("PublicationResultScreen — confirmed", () => {
	const confirmed = (extra = {}) => task({
		publication_state: "Confirmed", version: { number: 1, status: "Active", reference: "PLN-MOH-2027-001-V1", record_version: 6 },
		status_rows: CONFIRMED_ROWS, confirmation: CONFIRMATION, can_confirm: false, can_save_draft: false, can_correct: true, ...extra,
	});

	it("U13-ACTIVE: shows every confirmed fact separately, and hides the form", () => {
		const w = make({ task: confirmed() });
		expect(w.find('[data-testid="pub-form"]').exists()).toBe(false);
		const rows = w.findAll('[data-testid="pub-status-row"]');
		expect(rows[1].text()).toContain("Confirmed");
		expect(rows[2].text()).toContain("Confirmed");
		expect(rows[3].text()).toContain("Current plan");
		const facts = w.find('[data-testid="pub-confirmation"]');
		expect(facts.text()).toContain("10 Dec 2026");
		expect(facts.text()).toContain("MOH/APP/2027/001");
		expect(facts.text()).toContain("Mercy Kilonzo");
		expect(facts.text()).toContain("10 Dec 2026, 15:00 EAT");
		expect(facts.find("a[href^='https://www.moh.example.test']").exists()).toBe(true);
		expect(w.find('[data-testid="pub-view-evidence"]').text()).toBe("View submission evidence");
	});

	it("U13-PUBLISHED-HELD: keeps the external fact and denies procurement, with the correction still available", () => {
		const w = make({
			task: confirmed({
				version: { number: 1, status: "Published — activation held", reference: "PLN-MOH-2027-001-V1", record_version: 6 },
				status_rows: [...CONFIRMED_ROWS.slice(0, 3), { label: "Use for procurement", state: "Published, but not available for new procurement", kind: "critical" }],
				next_step: PREPARE_CORRECTED_TURN,
			}),
		});
		const rows = w.findAll('[data-testid="pub-status-row"]');
		expect(rows[2].text()).toContain("Confirmed");
		expect(rows[3].text()).toContain("Published, but not available for new procurement");
		expect(w.find('[data-testid="pub-correct"]').text()).toBe("Correct publication details");
		expect(w.find('[data-testid="pub-confirm"]').exists()).toBe(false);
	});

	it("U13-CORRECT-DETAILS: shows the previous details, requires a reason and a change, and says what it does not do", async () => {
		const w = make({ task: confirmed() });
		expect(w.find('[data-testid="pub-correct-form"]').exists()).toBe(false);
		await w.find('[data-testid="pub-correct"]').trigger("click");
		const form = w.find('[data-testid="pub-correct-form"]');
		expect(form.find('[data-testid="pub-correct-prior"]').text()).toContain("MOH/APP/2027/001");
		expect(form.text()).toContain("Correcting these details does not change the approved plan, deactivate an active plan or repeat an approval.");
		const submit = () => w.find('[data-testid="pub-correct-submit"]');
		expect(submit().text()).toBe("Save corrected details");
		expect(submit().attributes("disabled")).toBeDefined();
		await w.find('[data-testid="pub-correct-reference"]').setValue("MOH/APP/2027/002");
		expect(submit().attributes("disabled")).toBeDefined(); // a change but no reason
		await w.find('[data-testid="pub-correct-reason"]').setValue("The reference was typed wrongly.");
		expect(submit().attributes("disabled")).toBeUndefined();
		await submit().trigger("click");
		const [payload] = w.emitted("correct")[0];
		expect(payload.reason).toBe("The reference was typed wrongly.");
		expect(payload.values.treasury_reference).toBe("MOH/APP/2027/002");
		expect(payload.confirmation).toBe("PPC-00001");
	});

	it("only the Planner is offered the correction", () => {
		const w = make({ task: confirmed({ can_correct: false }) });
		expect(w.find('[data-testid="pub-correct"]').exists()).toBe(false);
	});
});

describe("PublicationResultScreen — withdrawal, late start and history", () => {
	it("the Accounting Officer is offered the withdrawal request for unconfirmed content, and the statutory authority the decision", async () => {
		const ao = make({ task: task({ can_confirm: false, can_save_draft: false, can_request_withdrawal: true }) });
		await ao.find('[data-testid="pub-request-withdrawal"]').trigger("click");
		expect(ao.emitted("request-withdrawal")).toHaveLength(1);
		const statutory = make({ task: task({ can_confirm: false, can_save_draft: false, can_decide_withdrawal: true }) });
		await statutory.find('[data-testid="pub-decide-withdrawal"]').trigger("click");
		expect(statutory.emitted("decide-withdrawal")).toHaveLength(1);
	});

	it("§10.14: the Accounting Officer is offered the late-start explanation, and it appends", () => {
		const late = {
			applicable: true, financial_year_started_display: "1 Jul 2027", activated_display: "2 Jul 2027, 09:00 EAT", explanations: [], can_explain: true,
		};
		const w = make({ task: task({ late_activation: late }) });
		const section = w.find('[data-testid="pub-late-activation"]');
		expect(section.exists()).toBe(true);
		expect(section.text()).toContain("Financial year started");
		expect(section.text()).toContain("Plan became active");
		expect(w.find('[data-testid="pub-late-activation-none"]').exists()).toBe(true);
		expect(w.find('[data-testid="pub-explain-late"]').text()).toBe("Explain late start of the annual plan");
		const w2 = make({
			task: task({
				late_activation: {
					...late,
					explanations: [{ id: "LAE-1", reason: "Publication was confirmed after the year began.", actor_name: "Amina Hassan", recorded_display: "3 Jul 2027, 08:00 EAT", superseded: false }],
				},
			}),
		});
		expect(w2.find('[data-testid="pln-late-explanation-history"]').exists()).toBe(true);
		expect(w2.find('[data-testid="pub-explain-late"]').text()).toBe("Add to the explanation");
		const reader = make({ task: task({ late_activation: { ...late, can_explain: false } }) });
		expect(reader.find('[data-testid="pub-explain-late"]').exists()).toBe(false);
		expect(make({ task: task() }).find('[data-testid="pub-late-activation"]').exists()).toBe(false);
	});

	it("shows earlier publication attempts and the earlier Accounting Officer Treasury record as read-only history", () => {
		const w = make({
			task: task({
				attempts: [{ attempt_number: 1, result: "Failed", attempted_display: "10 Dec 2026, 14:55 EAT", external_reference: "" }],
				historical_treasury: {
					submitted_display: "10 Dec 2026, 14:00 EAT", channel: "Official correspondence", destination: "National Treasury",
					dispatch_reference: "MOH/APP/2027/001", recorded_display: "10 Dec 2026, 14:05 EAT", recorded_by_name: "Amina Hassan",
				},
			}),
		});
		const history = w.find('[data-testid="pub-attempts"]');
		expect(history.text()).toContain("Earlier publication attempts");
		expect(history.text()).toContain("Failed");
		expect(history.text()).toContain("MOH/APP/2027/001");
		expect(w.find('[data-testid="pub-retry"]').exists()).toBe(false);
		expect(make({ task: task() }).find('[data-testid="pub-attempts"]').exists()).toBe(false);
	});
});
