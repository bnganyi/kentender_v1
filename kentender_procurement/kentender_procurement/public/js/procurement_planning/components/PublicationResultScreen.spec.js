// PLN-CHG-001 v1.24 §10.12 — PublicationResultScreen component tests (U13),
// ported from Artboards-U12-U13.dc.html.
//
// Four facts that do not prove each other, and two rules about the actions: an
// unknown external result is never shown as failure and never offers a blind
// retry, and the AO's business action is not the technical operator's.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import PublicationResultScreen from "./PublicationResultScreen.vue";
import { RETRY_TURN, TREASURY_TURN, WAITING_OPERATOR, planJourney } from "./guidance.fixtures.js";

const APPROVED_ROWS = [
	{ label: "Plan approval", state: "Approved", kind: "live" },
	{ label: "Treasury submission", state: "Details not yet recorded", kind: "attention" },
	{ label: "Website publication", state: "Not started", kind: "pending" },
	{ label: "Use for procurement", state: "This plan is not yet active", kind: "pending" },
];

function task(overrides = {}) {
	return {
		outcome: "OK",
		publication: "PUB-PLN-MOH-2027-001-V1",
		plan_reference: "PLN-MOH-2027-001",
		version: { number: 1, status: "Approved — publication pending" },
		header: { badge: "Awaiting dispatch", badge_kind: "attention" },
		publication_state: "Pending",
		status_rows: APPROVED_ROWS,
		treasury_evidence: null,
		hold: { active: false },
		attempts: [],
		can_record_treasury: true,
		can_retry: false,
		can_publish: false,
		can_reconcile: false,
		next_step: TREASURY_TURN,
		journey: planJourney("publication", { holder: "Amina Hassan", reduced: true }),
		...overrides,
	};
}

function make(props = {}) {
	return mount(PublicationResultScreen, { props: { task: task(), pending: false, errorSummary: "", ...props } });
}

describe("PublicationResultScreen — U13 BASE", () => {
	it("shows four distinct facts in order", () => {
		const w = make();
		const rows = w.findAll('[data-testid="pub-status-row"]');
		expect(rows).toHaveLength(4);
		expect(rows.map((r) => r.text())).toEqual([
			expect.stringContaining("Plan approval"),
			expect.stringContaining("Treasury submission"),
			expect.stringContaining("Website publication"),
			expect.stringContaining("Use for procurement"),
		]);
		expect(rows[3].text()).toContain("This plan is not yet active");
	});

	it("replaces the header state badge with the next step and a one-line tracker", () => {
		const w = make();
		expect(w.find('[data-testid="pub-context"] .kt-status').exists()).toBe(false);
		expect(w.find(".kt-page-head .kt-next-step").text()).toBe("Your turn Record the Treasury submission");
		expect(w.find(".kt-journey.is-reduced").text()).toBe("Stage 6 of 7: Publication — Amina Hassan");
		expect(w.find('[data-testid="pub-responsible"]').exists()).toBe(false);
	});

	it("offers the AO the record action and no technical controls", () => {
		const w = make();
		expect(w.find('[data-testid="pub-record-treasury"]').text()).toBe("Record Treasury submission");
		expect(w.find('[data-testid="pub-retry"]').exists()).toBe(false);
		expect(w.find('[data-testid="pub-reconcile"]').exists()).toBe(false);
	});

	it("§10.12 header: offers View approved plan, Download approved plan and Download Plan data, in that order", async () => {
		const w = make();
		const actions = w.findAll('[data-testid="pub-view-plan"], [data-testid="pub-download-plan"], [data-testid="pub-download-plan-data"]');
		expect(actions.map((a) => a.text())).toEqual(["View approved plan", "Download approved plan", "Download Plan data"]);
		await w.find('[data-testid="pub-download-plan"]').trigger("click");
		expect(w.emitted("download-plan")).toBeTruthy();
		await w.find('[data-testid="pub-download-plan-data"]').trigger("click");
		expect(w.emitted("download-plan-data")).toBeTruthy();
	});
});

describe("PublicationResultScreen — recorded evidence", () => {
	it("U13-EVIDENCE-RECORDED: shows every field, with dispatch and recording distinct", async () => {
		const w = make({
			task: task({
				status_rows: [
					APPROVED_ROWS[0],
					{ label: "Treasury submission", state: "Recorded", kind: "live" },
					APPROVED_ROWS[2],
					APPROVED_ROWS[3],
				],
				treasury_evidence: {
					recorded: true,
					submitted_display: "10 Dec 2026, 14:00 EAT",
					channel: "Official correspondence",
					destination: "National Treasury",
					dispatch_reference: "MOH/APP/2027/001",
					recorded_display: "10 Dec 2026, 14:05 EAT",
					recorded_by_name: "Amina Hassan",
					supporting_attachment: "Treasury-dispatch-evidence-example.pdf",
				},
			}),
		});
		const evidence = w.find('[data-testid="pub-treasury-evidence"]');
		expect(evidence.text()).toContain("10 Dec 2026, 14:00 EAT");
		expect(evidence.text()).toContain("Official correspondence");
		// Destination is its own labelled field, not folded into the channel.
		expect(evidence.text()).toContain("National Treasury");
		expect(evidence.text()).toContain("MOH/APP/2027/001");
		expect(evidence.text()).toContain("Amina Hassan");
		// Recording it once does not offer to record it again.
		expect(w.find('[data-testid="pub-record-treasury"]').exists()).toBe(false);
		expect(w.find('[data-testid="pub-correct-treasury"]').text()).toBe("Correct submission details");
		// §10.12 — enabled once there is something to view.
		const viewEvidence = w.find('[data-testid="pub-view-evidence"]');
		expect(viewEvidence.text()).toBe("View submission evidence");
		await viewEvidence.trigger("click");
		expect(w.emitted("view-evidence")).toBeTruthy();
	});

	it("offers no View submission evidence link when no file was recorded", () => {
		const w = make({
			task: task({
				treasury_evidence: {
					recorded: true,
					submitted_display: "10 Dec 2026, 14:00 EAT",
					channel: "Official correspondence",
					destination: "National Treasury",
					dispatch_reference: "MOH/APP/2027/001",
					recorded_by_name: "Amina Hassan",
					supporting_attachment: "",
				},
			}),
		});
		expect(w.find('[data-testid="pub-view-evidence"]').exists()).toBe(false);
	});
});

describe("PublicationResultScreen — failure is not uncertainty", () => {
	it("U13-FAILED: offers retry to a technical operator only", () => {
		const technical = make({
			task: task({
				publication_state: "Failed",
				header: { badge: "Publication failed", badge_kind: "critical" },
				status_rows: [
					APPROVED_ROWS[0],
					{ label: "Treasury submission", state: "Recorded", kind: "live" },
					{ label: "Website publication", state: "The plan was not published", kind: "critical" },
					APPROVED_ROWS[3],
				],
				treasury_evidence: { recorded: true, submitted_display: "x", channel: "y", dispatch_reference: "z", recorded_by_name: "Amina Hassan" },
				can_record_treasury: false,
				can_retry: true,
				next_step: RETRY_TURN,
			}),
		});
		expect(technical.find('[data-testid="pub-retry"]').text()).toBe("Retry publication");
		// O4 — the one exception: the technical operator's turn.
		expect(technical.find(".kt-page-head .kt-next-step").text()).toBe("Your turn Retry publication");
		expect(technical.find('[data-testid="pub-reconcile"]').exists()).toBe(false);

		// A reader who is not that operator is told whose action it is.
		const reader = make({
			task: task({ publication_state: "Failed", can_record_treasury: false, can_retry: false, treasury_evidence: { recorded: true, recorded_by_name: "Amina Hassan" }, next_step: WAITING_OPERATOR }),
		});
		expect(reader.find('[data-testid="pub-retry"]').exists()).toBe(false);
		// v1.27 — the waiting line names whose it is and since when, replacing
		// the "Responsible role" sentence.
		expect(reader.find(".kt-page-head .kt-next-step").text()).toContain("Waiting for an authorised technical operator to retry publication");
		expect(reader.find(".kt-page-head .kt-next-step").text()).toContain("since 10 Dec 2026, 11:55 EAT");
		expect(reader.find('[data-testid="pub-responsible"]').exists()).toBe(false);

		// And the Accounting Officer is still told whose the recovery is, even
		// though they hold a Treasury action of their own on the same screen.
		const ao = make({
			task: task({ publication_state: "Failed", can_record_treasury: true, can_retry: false, treasury_evidence: null, next_step: WAITING_OPERATOR }),
		});
		expect(ao.find('[data-testid="pub-retry"]').exists()).toBe(false);
		expect(ao.find(".kt-page-head .kt-next-step").text()).toContain("authorised technical operator");
	});

	it("§10.14: the Accounting Officer is offered the late-start explanation, and it appends", () => {
		const late = {
			applicable: true,
			financial_year_started_display: "1 Jul 2027",
			activated_display: "2 Jul 2027, 09:00 EAT",
			explanations: [],
			can_explain: true,
		};
		const w = make({ task: task({ late_activation: late }) });
		const section = w.find('[data-testid="pub-late-activation"]');
		expect(section.exists()).toBe(true);
		expect(section.text()).toContain("Financial year started");
		expect(section.text()).toContain("Plan became active");
		expect(w.find('[data-testid="pub-late-activation-none"]').exists()).toBe(true);
		expect(w.find('[data-testid="pub-explain-late"]').text()).toBe("Explain late start of the annual plan");

		// A recorded explanation is kept and shown; the action then adds to it.
		const w2 = make({
			task: task({
				late_activation: {
					...late,
					explanations: [{ id: "LAE-1", reason: "Acknowledgement arrived after the year began.", actor_name: "Amina Hassan", recorded_display: "3 Jul 2027, 08:00 EAT", superseded: false }],
				},
			}),
		});
		expect(w2.find('[data-testid="pln-late-explanation-history"]').exists()).toBe(true);
		expect(w2.find('[data-testid="pub-explain-late"]').text()).toBe("Add to the explanation");

		// A reader who is not the Accounting Officer sees the fact, not the action.
		const reader = make({ task: task({ late_activation: { ...late, can_explain: false } }) });
		expect(reader.find('[data-testid="pub-late-activation"]').exists()).toBe(true);
		expect(reader.find('[data-testid="pub-explain-late"]').exists()).toBe(false);

		// Not late at all: the whole section is absent, not an empty heading.
		const ordinary = make({ task: task() });
		expect(ordinary.find('[data-testid="pub-late-activation"]').exists()).toBe(false);
	});

	it("U13-UNKNOWN: says it is unconfirmed, and reconciles rather than retrying blind", () => {
		const w = make({
			task: task({
				publication_state: "Indeterminate",
				header: { badge: "Result unknown — reconcile", badge_kind: "attention" },
				status_rows: [
					APPROVED_ROWS[0],
					{ label: "Treasury submission", state: "Recorded", kind: "live" },
					{ label: "Website publication", state: "We could not confirm whether publication succeeded.", kind: "attention" },
					APPROVED_ROWS[3],
				],
				treasury_evidence: { recorded: true, recorded_by_name: "Amina Hassan" },
				can_record_treasury: false,
				can_reconcile: true,
			}),
		});
		expect(w.find('[data-testid="pub-unknown"]').text()).toContain("Check the existing attempt before trying again.");
		expect(w.find('[data-testid="pub-reconcile"]').text()).toBe("Check publication result");
		// Never a blind retry on an unknown outcome.
		expect(w.find('[data-testid="pub-retry"]').exists()).toBe(false);
		// And never rendered as a failure.
		expect(w.text()).not.toContain("The plan was not published");
	});
});

describe("PublicationResultScreen — published states", () => {
	it("U13-ACTIVE: publication and procurement availability are separate rows", () => {
		const w = make({
			task: task({
				publication_state: "Acknowledged",
				version: { number: 1, status: "Active" },
				status_rows: [
					APPROVED_ROWS[0],
					{ label: "Treasury submission", state: "Recorded", kind: "live" },
					{ label: "Website publication", state: "Published", kind: "live" },
					{ label: "Use for procurement", state: "Current plan", kind: "live" },
				],
				treasury_evidence: { recorded: true, recorded_by_name: "Amina Hassan" },
				can_record_treasury: false,
			}),
		});
		const rows = w.findAll('[data-testid="pub-status-row"]');
		expect(rows[2].text()).toContain("Published");
		expect(rows[3].text()).toContain("Current plan");
	});

	it("U13-PUBLISHED-HELD: keeps the external fact and denies procurement", () => {
		const w = make({
			task: task({
				publication_state: "Acknowledged",
				version: { number: 1, status: "Published — activation held" },
				status_rows: [
					APPROVED_ROWS[0],
					{ label: "Treasury submission", state: "Recorded", kind: "live" },
					{ label: "Website publication", state: "Published", kind: "live" },
					{ label: "Use for procurement", state: "Published, but not available for new procurement", kind: "critical" },
				],
				treasury_evidence: { recorded: true, recorded_by_name: "Amina Hassan" },
				can_record_treasury: false,
			}),
		});
		const rows = w.findAll('[data-testid="pub-status-row"]');
		expect(rows[2].text()).toContain("Published");
		expect(rows[3].text()).toContain("Published, but not available for new procurement");
	});

	it("a hold is shown as a control over transmission, not a lost approval", () => {
		const w = make({
			task: task({ hold: { active: true, reason: "A material defect was found in the approved content.", kind: "defect" } }),
		});
		expect(w.find('[data-testid="pub-hold"]').text()).toContain("Publication is on hold");
		expect(w.find('[data-testid="pub-status-row"]').text()).toContain("Approved");
	});
});


describe("PublicationResultScreen — the Head of Procurement Function publishes (RG-01)", () => {
	const evidence = { recorded: true, submitted_display: "x", channel: "y", dispatch_reference: "z", recorded_by_name: "Amina Hassan" };

	it("offers Publish only where the server says the Head may, and emits it", async () => {
		const head = make({ task: task({ can_record_treasury: false, can_publish: true, treasury_evidence: evidence }) });
		const button = head.find('[data-testid="pub-publish"]');
		expect(button.text()).toBe("Publish annual plan");
		await button.trigger("click");
		expect(head.emitted("publish")).toHaveLength(1);

		const reader = make({ task: task({ can_record_treasury: false, can_publish: false, treasury_evidence: evidence }) });
		expect(reader.find('[data-testid="pub-publish"]').exists()).toBe(false);
	});

	it("is disabled while a command is pending", () => {
		const head = make({ task: task({ can_record_treasury: false, can_publish: true, treasury_evidence: evidence }), pending: true });
		expect(head.find('[data-testid="pub-publish"]').attributes("disabled")).toBeDefined();
	});
});
