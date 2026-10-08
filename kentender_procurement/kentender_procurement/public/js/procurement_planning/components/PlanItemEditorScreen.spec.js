// PLN-CHG-001 v1.24 §10.8 — PlanItemEditorScreen component tests (U09),
// verified against Artboards-U09.dc.html.
//
// This screen was cut hardest by v1.22, so most of these tests are about what
// is *not* there: no resolver status or rule version as ordinary fields, no
// plan-level reservation arithmetic, no None / Single lot / Lot count 1 shown
// to prove a stored value exists. What must be there is the handful of
// decisions the Planner actually makes, and every material issue in plain
// sight rather than inside the disclosure.
import { describe, expect, it } from "vitest";
import { mount } from "@vue/test-utils";
import PlanItemEditorScreen from "./PlanItemEditorScreen.vue";

const SOURCES = [
	{
		requirement: "Clinical training laptops for digital health rollout",
		department: "Human Resources Management and Development",
		quantity_number: "100",
		unit_label: "Each",
		required_by_display: "31 Dec 2027",
		amount_display: "KES 20,000,000",
		need_reference_line: "NDS-MOH-2027-0003 · Revision 2",
		budget_line_display: "MOH-BL-HWD-2027",
		classification_readable: true,
	},
	{
		requirement: "Clinical deployment laptops for digital health rollout",
		department: "Digital Health",
		quantity_number: "150",
		unit_label: "Each",
		required_by_display: "31 Dec 2027",
		amount_display: "KES 30,000,000",
		need_reference_line: "NDS-MOH-2027-0004 · Revision 1",
		budget_line_display: "MOH-BL-HWD-2027",
		classification_readable: true,
	},
];

function item(overrides = {}) {
	return {
		outcome: "OK",
		plan_item_id: "PPI-MOH-2027-033",
		record_version: 2,
		mutable: true,
		combined: true,
		is_active: false,
		header: {
			title: "Clinical training and deployment laptops for digital health rollout",
			reference_line: "PPI-MOH-2027-033 · Draft Version 1",
			item_state_badge: "Draft",
		},
		summary_line: "Goods · 250 each · Required by 31 Dec 2027",
		missing_settings: [],
		planned_value_display: "KES 50,000,000",
		aggregation_reason_preview: "Both departments require the same laptop specification for the same…",
		estimate_basis_preview: "Market survey estimate includes delivery, installation…",
		sources: SOURCES,
		identity: {
			title: "Clinical training and deployment laptops for digital health rollout",
			description: "Procure and deploy one common laptop specification.",
			requirement_type: "Goods",
			procurement_category: "Goods",
			aggregation_reason: "Both departments require the same laptop specification for the same national digital-health rollout.",
		},
		classification: {
			procurement_method: "Open Tender",
			admissible_methods: ["Open Tender", "Request for Quotations"],
			strategic_objective: "OBJ-1",
			strategic_objectives: [{ id: "OBJ-1", title: "Strengthen interoperable national digital health services" }],
			objective_path: "Digital health systems › Health policy",
			estimate_basis: "Market survey estimate includes delivery, installation where applicable and other identified incidental costs.",
			estimate_basis_reference: "Market survey working paper",
			method_profile: { profile: "MPR-OPEN-TENDER-V18", verification_status: "Fixture-verified — not production law", found: true },
		},
		preference: {
			reservation_category: "",
			reservation_categories: ["None", "Youth", "Women"],
			county_resident_reservation: false,
			county_control_available: false,
			lotting_indicator: "Single lot",
			lot_count: 0,
		},
		baseline: {
			target_invitation_date: "2027-05-15",
			estimated_delivery_period_days: 60,
			estimated_completion_display: "24 Sep 2027",
			delivery_boundary_ok: true,
			rows: [
				{ milestone: "invitation", label: "Invitation or advertisement", date_display: "15 May 2027", source_boundary: false },
				{ milestone: "delivery_completion", label: "Delivery or implementation completion", date_display: "31 Dec 2027", source_boundary: true },
			],
		},
		scope_lock: { locked: false },
		notices: [],
		blockers: [],
		...overrides,
	};
}

function make(props = {}) {
	return mount(PlanItemEditorScreen, { props: { item: item(), pending: false, errorSummary: "", ...props } });
}

describe("PlanItemEditorScreen — U09 first view", () => {
	it("shows the five decision sections and the derived summary line", () => {
		const w = make();
		const text = w.text();
		expect(text).toContain("Purchase details");
		expect(text).toContain("Included requirements");
		expect(text).toContain("Estimated cost");
		expect(text).toContain("Procurement approach");
		expect(text).toContain("Dates");
		expect(w.find('[data-testid="ppi-summary-line"]').text()).toBe("Goods · 250 each · Required by 31 Dec 2027");
	});

	it("never shows system internals as ordinary business fields", () => {
		const w = make();
		// PLN22-AC-005. The rule version and source check exist, but only
		// inside Supporting details for authorised inspection.
		const supporting = w.find('[data-testid="ppi-supporting"]');
		expect(supporting.attributes("open")).toBeUndefined();
		expect(w.find('[data-testid="ppi-rule-evidence"]').text()).toContain("MPR-OPEN-TENDER-V18");
		expect(w.text()).not.toContain("Procedure — Planning example");
		expect(w.text()).not.toContain("Method support");
	});

	it("omits plan-level reservation arithmetic entirely", () => {
		const w = make();
		// PLN22-AC-006 — that calculation happens once, at plan level.
		expect(w.text()).not.toContain("Required allocation");
		expect(w.text()).not.toContain("Planned qualifying allocation");
		expect(w.text()).not.toContain("Shortfall");
	});

	it("omits None, Single lot, Lot count 1 and an inapplicable county field", () => {
		const w = make();
		expect(w.find('[data-testid="ppi-reservation"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-lot-count"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-county"]').exists()).toBe(false);
		expect(w.text()).not.toContain("Single lot");
		// It can still be added deliberately.
		expect(w.find('[data-testid="ppi-add-reservation"]').exists()).toBe(true);
	});

	it("does not display the fixed single-year horizon", () => {
		const w = make();
		expect(w.text()).not.toContain("Plan horizon");
		expect(w.text()).not.toContain("Single year");
	});

	it("shows the designation when one is set or required", () => {
		const set = make({ item: item({ preference: { ...item().preference, reservation_category: "Youth" } }) });
		expect(set.find('[data-testid="ppi-reservation"]').exists()).toBe(true);

		const required = make({ item: item({ blockers: [{ code: "PLN_RESERVATION_REQUIRED", message: "Choose who this is reserved for." }] }) });
		expect(required.find('[data-testid="ppi-reservation"]').exists()).toBe(true);
	});

	it("shows lots only when there are several", () => {
		const w = make({ item: item({ preference: { ...item().preference, lotting_indicator: "Packaged into lots", lot_count: 3 } }) });
		expect(w.find('[data-testid="ppi-lot-count"]').exists()).toBe(true);
	});
});

describe("PlanItemEditorScreen — included requirements and cost", () => {
	it("lists each source with separate quantity and unit", () => {
		const w = make();
		const rows = w.findAll('[data-testid="ppi-source-row"]');
		expect(rows).toHaveLength(2);
		expect(rows[0].text()).toContain("Human Resources Management and Development");
		expect(rows[0].text()).toContain("100");
		expect(rows[0].text()).toContain("KES 20,000,000");
	});

	it("names each requirement's own need reference, revision and budget line beneath its title", () => {
		// U09's own row: the name leads, the reference sits beneath it in
		// smaller muted text — found live 23 Sep 2026 missing entirely, though
		// the read model already carries both pieces.
		const w = make();
		const rows = w.findAll('[data-testid="ppi-source-row"]');
		expect(rows[0].find(".pln-row-title").text()).toBe("Clinical training laptops for digital health rollout");
		expect(rows[0].find(".pln-row-ref").text()).toBe("NDS-MOH-2027-0003 · Revision 2 · MOH-BL-HWD-2027");
		expect(rows[1].find(".pln-row-ref").text()).toBe("NDS-MOH-2027-0004 · Revision 1 · MOH-BL-HWD-2027");
	});

	it("previews the aggregation reason with a disclosure to the full text", async () => {
		const w = make();
		expect(w.find('[data-testid="ppi-combined"]').text()).toContain("Combined purchase");
		expect(w.find('[data-testid="ppi-full-reason"]').exists()).toBe(false);
		await w.find('[data-testid="ppi-read-reason"]').trigger("click");
		expect(w.find('[data-testid="ppi-full-reason"]').text()).toContain("national digital-health rollout");
	});

	it("derives the planned amount rather than offering it as an input", () => {
		const w = make();
		expect(w.find('[data-testid="ppi-planned-value"]').text()).toBe("KES 50,000,000");
		expect(w.find('[data-testid="ppi-planned-value"]').element.tagName).not.toBe("INPUT");
	});
});

describe("PlanItemEditorScreen — dates", () => {
	it("says the schedule meets the departmental deadline", () => {
		const w = make();
		expect(w.find('[data-testid="ppi-completion"]').text()).toBe("24 Sep 2027");
		expect(w.find('[data-testid="ppi-deadline"]').text()).toBe("31 Dec 2027");
		expect(w.find('[data-testid="ppi-boundary"]').text()).toBe("Expected to meet the departmental deadline");
	});

	it("U09-INVALID-SCHEDULE: blocks Save and offers Review dates", () => {
		const w = make({
			item: item({
				baseline: { ...item().baseline, estimated_completion_display: "2 Jan 2028", delivery_boundary_ok: false },
				blockers: [{ code: "PLN_DELIVERY_BOUNDARY_INSUFFICIENT", message: "Estimated completion is after the department's required date." }],
			}),
		});
		// Said once: the critical notice carries the problem and the recovery
		// action, exactly as U09-INVALID-SCHEDULE draws it, and the ordinary
		// boundary line below the dates stands down rather than repeating it.
		expect(w.find('[data-testid="ppi-review-dates"]').element.closest(".kt-notice").textContent).toContain(
			"Expected completion is after the department's required date.",
		);
		expect(w.find('[data-testid="ppi-boundary"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-save"]').attributes("disabled")).toBeDefined();
		expect(w.find('[data-testid="ppi-review-dates"]').exists()).toBe(true);
	});
});

describe("PlanItemEditorScreen — footer and flagged fields", () => {
	// U09/U09-READY's own footer button — a solid destructive action that
	// opens the Remove confirmation, matching DissolveItemDialog's own
	// primary+danger button, not the outlined secondary+danger treatment a
	// choice-among-options button (like a Decline) correctly uses elsewhere.
	it("Remove purchase is the artboard's solid danger button, not an outlined one", () => {
		const w = make();
		const remove = w.find('[data-testid="ppi-remove"]');
		expect(remove.classes()).toContain("btn-primary");
		expect(remove.classes()).toContain("kt-danger");
		expect(remove.classes()).not.toContain("btn-secondary");
	});

	// A Planner sent here by "Choose a strategic objective" (the current-work
	// note on the Annual Plan screen) should meet the field itself, not a
	// closed disclosure they then have to know to open (found live 23 Sep 2026).
	it("opens Supporting details by default when Strategy is what's blocking the purchase", () => {
		const w = make({
			item: item({ blockers: [{ code: "PLN_OBJECTIVE_INELIGIBLE", field: "strategic_objective", message: "Complete the highlighted purchase details and required evidence." }] }),
		});
		expect(w.find('[data-testid="ppi-supporting"]').attributes("open")).toBeDefined();
		const field = w.find('[data-testid="ppi-objective"]').element.closest(".field");
		expect(field.classList).toContain("pln-field-flagged");
	});

	// The server's blocker list is only current as of the last load; typing
	// into a flagged field should not go on reading as still-broken until
	// the next save re-derives it (found live 23 Sep 2026).
	it("a flagged field drops its highlight once the Planner has changed it", async () => {
		const w = make({
			item: item({
				blockers: [{ code: "PLN_PLAN_CONTENTS_INCOMPLETE", field: "estimate_basis", message: "Complete the highlighted purchase details and required evidence." }],
			}),
		});
		const field = w.find('[data-testid="ppi-estimate-basis"]').element.closest(".field");
		expect(field.classList).toContain("pln-field-flagged");
		await w.find('[data-testid="ppi-estimate-basis"]').setValue("A market survey conducted across three qualified suppliers in the region.");
		expect(field.classList).not.toContain("pln-field-flagged");
	});
});

describe("PlanItemEditorScreen — visible blockers", () => {
	// The PLN-CHG-001 §8 error contract, not invented copy: `get_plan_item`
	// enriches every item blocker with the exact same canonical MESSAGES[code]
	// text the plan-level readiness list already carries (a prior drift left
	// the item-level list without any `message` key at all, so a blocker
	// outside the dates/reservation exclusions rendered as a blank critical
	// notice).
	it("shows a method blocker's real message, not a blank critical notice", () => {
		const w = make({
			item: item({
				blockers: [{ code: "PLN_METHOD_NOT_ADMISSIBLE", field: "procurement_method", message: "The selected method does not meet the applicable procurement conditions." }],
			}),
		});
		const notice = w.find('[data-testid="ppi-blocker"]');
		expect(notice.exists()).toBe(true);
		expect(notice.text()).toContain("The selected method does not meet the applicable procurement conditions.");
	});

	// Found live on PPI-MOH-2027-001, 23 September 2026: `item_blockers`
	// reports one blocker per incomplete field, so a purchase missing both the
	// estimate basis and its supporting document stacked the same sentence
	// twice, one banner above the other.
	it("says one incomplete-contents sentence once, however many fields are missing", () => {
		const w = make({
			item: item({
				blockers: [
					{ code: "PLN_PLAN_CONTENTS_INCOMPLETE", field: "estimate_basis", message: "Complete the highlighted purchase details and required evidence." },
					{ code: "PLN_PLAN_CONTENTS_INCOMPLETE", field: "estimate_basis_reference", message: "Complete the highlighted purchase details and required evidence." },
				],
			}),
		});
		expect(w.findAll('[data-testid="ppi-blocker"]')).toHaveLength(1);
	});

	// …and the sentence is only true if the fields it points at are marked.
	it("marks the fields the blockers name, which is what 'the highlighted' means", () => {
		const w = make({
			item: item({
				blockers: [
					{ code: "PLN_PLAN_CONTENTS_INCOMPLETE", field: "estimate_basis", message: "Complete the highlighted purchase details and required evidence." },
					{ code: "PLN_METHOD_NOT_ADMISSIBLE", field: "procurement_method", message: "The selected method does not meet the applicable procurement conditions." },
				],
			}),
		});
		const flagged = w.findAll(".pln-field-flagged").map((el) => el.get("label").text());
		expect(flagged).toContain("Estimate basis");
		expect(flagged).toContain("Procurement method");
		expect(flagged).not.toContain("Title");
	});

	it("does not duplicate the schedule and reservation blockers, which already have their own dedicated treatment", () => {
		const w = make({
			item: item({
				blockers: [
					{ code: "PLN_SCHEDULE_INVALID", message: "Review the highlighted dates and the rule shown for them." },
					{ code: "PLN_RESERVATION_REQUIRED", message: "Choose who this procurement is reserved for." },
				],
			}),
		});
		expect(w.find('[data-testid="ppi-blocker"]').exists()).toBe(false);
	});
});

describe("PlanItemEditorScreen — material issues stay visible", () => {
	it("C03 — names the missing setting, the action it blocks and its owner", () => {
		const w = make({
			item: item({
				missing_settings: [
					{
						setting: "Applicable procurement method rule",
						affected_action: "Send plan for governance review",
						affected_purchase: "Test procurement package · PPI-MOH-2027-033",
						responsible_role: "Administrator or System Manager",
						note: "",
						lede: "Open Tender cannot be confirmed until the applicable method rule is verified in System setup.",
						can_open_setup: false,
						action: "",
						href: "",
						ask_text: "Ask your KenTender administrator to complete this setting.",
					},
				],
			}),
		});
		const panel = w.find('[data-testid="pln-missing-setting"]');
		expect(panel.text()).toContain("Open Tender cannot be confirmed until the applicable method rule is verified in System setup.");
		expect(panel.text()).toContain("Applicable procurement method rule");
		expect(panel.text()).toContain("Send plan for governance review");
		expect(panel.text()).toContain("Administrator or System Manager");
		// No disabled setup control in Planning — a Planner is told who to ask.
		expect(w.find('[data-testid="pln-open-setup"]').exists()).toBe(false);
		expect(w.find('[data-testid="pln-ask-administrator"]').text()).toBe(
			"Ask your KenTender administrator to complete this setting.",
		);
		// Stated before the field it blocks, not after the whole grid.
		const region = w.find('[data-testid="pln-missing-setting"]').element.closest(".kt-region");
		const html = region.innerHTML;
		expect(html.indexOf("pln-missing-setting")).toBeLessThan(html.indexOf("ppi-method"));
	});

	it("U09-LOCKED: shows the scope restriction as critical and removes the remove control", () => {
		// Kind and copy match the real read model (plan_read.py `_plan_checks`
		// sibling `notices` builder) exactly — a mismatched `kind` string here
		// previously let a scope-locked item render as a quiet warning instead
		// of the critical notice the artboard draws.
		const w = make({
			item: item({
				mutable: false,
				scope_lock: { locked: true },
				notices: [
					{
						kind: "scope_locked",
						heading: "Additional requirements need a separate Plan Item",
						text: "This Plan Item already has an authorised Requisition. Create a separate Plan Item for the additional requirement.",
					},
				],
			}),
		});
		const notice = w.find('[data-testid="ppi-notice"]');
		expect(notice.text()).toContain("already has an authorised Requisition");
		expect(notice.classes()).toContain("is-critical");
		expect(notice.classes()).not.toContain("is-warning");
		expect(w.find('[data-testid="ppi-remove"]').exists()).toBe(false);
		expect(w.find('[data-testid="ppi-save"]').exists()).toBe(false);
	});

	it("also renders a correction hold as critical", () => {
		const w = make({
			item: item({
				notices: [
					{
						kind: "correction_hold",
						heading: "New Requisition authorisations are on hold",
						text: "An unresolved correction request affects this Plan Item. Existing authorised proceedings are unchanged.",
					},
				],
			}),
		});
		expect(w.find('[data-testid="ppi-notice"]').classes()).toContain("is-critical");
	});

	it("keeps a material issue outside Supporting details", () => {
		const w = make({
			item: item({
				notices: [{ kind: "correction_hold", heading: "New Requisition authorisations are on hold", text: "Rebuild this purchase." }],
			}),
		});
		const supporting = w.find('[data-testid="ppi-supporting"]');
		expect(supporting.attributes("open")).toBeUndefined();
		// The notice is in the page body, not inside the disclosure.
		expect(w.find('[data-testid="ppi-notice"]').exists()).toBe(true);
		expect(supporting.text()).not.toContain("Rebuild this purchase.");
	});
});

describe("PlanItemEditorScreen — a method that asks something of the Planner", () => {
	const CONDITIONS = [
		{ condition_id: "VALUE_BAND", kind: "Known fact", description: "Within the low-value band", mandatory: true, result: "Met" },
		{
			condition_id: "CIRCUMSTANCES",
			kind: "Declaration",
			description: "The circumstances permitting direct procurement",
			required_evidence: "Evidence of the circumstances relied on",
			authorisation_actor: "Accounting Officer",
			statutory_reference: "s.103(2)(a)",
			mandatory: true,
			result: "Evidence required",
			evidence_reference: "",
			authorisation_reference: "",
		},
	];

	it("§10.8 — asks only for what the rule requires the Planner to supply", () => {
		const w = make({ item: item({ classification: { ...item().classification, method_profile: { found: true, conditions: CONDITIONS } } }) });
		// A condition that is a fact about the purchase is evaluated, not asked.
		expect(w.find('[data-testid="ppi-condition-VALUE_BAND"]').exists()).toBe(false);
		const asked = w.find('[data-testid="ppi-condition-CIRCUMSTANCES"]');
		expect(asked.text()).toContain("Evidence of the circumstances relied on");
		expect(asked.text()).toContain("Evidence required");
		expect(asked.text()).toContain("s.103(2)(a)");
		expect(w.find('[data-testid="ppi-authorisation-CIRCUMSTANCES"]').exists()).toBe(true);
	});

	it("asks for no authorisation where the rule names nobody to give it", () => {
		const conditions = [{ ...CONDITIONS[1], authorisation_actor: "" }];
		const w = make({ item: item({ classification: { ...item().classification, method_profile: { found: true, conditions } } }) });
		expect(w.find('[data-testid="ppi-evidence-CIRCUMSTANCES"]').exists()).toBe(true);
		expect(w.find('[data-testid="ppi-authorisation-CIRCUMSTANCES"]').exists()).toBe(false);
	});

	it("carries what was supplied into the save", async () => {
		const w = make({ item: item({ classification: { ...item().classification, method_profile: { found: true, conditions: CONDITIONS } } }) });
		await w.find('[data-testid="ppi-evidence-CIRCUMSTANCES"]').setValue("Sole supplier holds exclusive distribution rights.");
		await w.find('[data-testid="ppi-authorisation-CIRCUMSTANCES"]').setValue("AO/2027/DP/1");
		await w.find('[data-testid="ppi-save"]').trigger("click");
		const saved = w.emitted("save")[0][0].method_condition_evidence;
		expect(saved).toContainEqual({
			condition_id: "CIRCUMSTANCES",
			evidence_reference: "Sole supplier holds exclusive distribution rights.",
			authorisation_reference: "AO/2027/DP/1",
		});
	});

	it("offers no input at all to a reader who cannot change the purchase", () => {
		const w = make({ item: item({ mutable: false, classification: { ...item().classification, method_profile: { found: true, conditions: CONDITIONS } } }) });
		expect(w.find('[data-testid="ppi-evidence-CIRCUMSTANCES"]').attributes("disabled")).toBeDefined();
	});
});


// The method list is computed from the rules in force on the purchase's own
// applicable date, not from a stored catalogue. Found live 23 Sep 2026: the
// single backdated rule version that covered these purchases was superseded
// in System setup, every method disappeared at once, and the control rendered
// as an empty dropdown that explained nothing.
describe("a method list with nothing in it", () => {
	const empty = (over) => item({
		classification: { ...item().classification, admissible_methods: [], ...over },
	});

	it("says nothing at all while methods are on offer", () => {
		expect(make({ item: item() }).find('[data-testid="ppi-method-none"]').exists()).toBe(false);
	});

	it("names the date it is judging against and both ways out of it", () => {
		const w = make({ item: empty({ applicability_date: "2026-12-01", applicability_basis: "invitation" }) });
		const text = w.find('[data-testid="ppi-method-none"]').text();
		expect(text).toContain("No procurement method rule is in force on 1 Dec 2026");
		expect(text).toContain("planned invitation date");
		expect(text).toContain("Change the date");
		expect(text).toContain("ask your KenTender administrator");
	});

	it("does not call the financial year's first day a date the purchase was given", () => {
		const w = make({ item: empty({ applicability_date: "2026-07-01", applicability_basis: "fiscal_year" }) });
		const text = w.find('[data-testid="ppi-method-none"]').text();
		expect(text).toContain("1 Jul 2026, the start of this purchase's financial year");
		expect(text).toContain("Set a planned invitation date");
	});

	it("still says something when there is no applicable date to name", () => {
		const w = make({ item: empty({ applicability_date: "", applicability_basis: "fiscal_year" }) });
		expect(w.find('[data-testid="ppi-method-none"]').text()).toBe(
			"No procurement method is available for this purchase yet.",
		);
	});
});

// A Planner set every purchase to None, correctly, and learned only at the
// final refusal that the sum of those answers failed a plan-level rule
// (found live 23 Sep 2026). What None costs is said where None is chosen —
// without repeating the plan-level arithmetic, which lives once on U07.
describe("what a designation of None means", () => {
	const designated = (value) => item({
		preference: { ...item().preference, reservation_category: value },
		blockers: [{ code: "PLN_RESERVATION_REQUIRED", message: "Choose who this procurement is reserved for." }],
	});

	it("says the purchase will not count towards the target", () => {
		const w = make({ item: designated("None") });
		expect(w.find('[data-testid="ppi-reservation-none"]').text()).toBe(
			"Not reserved. This purchase will not count towards the plan's reserved-procurement target.",
		);
	});

	it("says nothing once a designation is chosen", () => {
		const w = make({ item: designated("Youth") });
		expect(w.find('[data-testid="ppi-reservation-none"]').exists()).toBe(false);
	});

	it("still repeats none of the plan-level arithmetic", () => {
		// The purchase's own estimated cost is its own business; what must
		// not appear here is the plan-wide reservation calculation.
		const text = make({ item: designated("None") }).text();
		for (const forbidden of ["Required allocation", "Planned qualifying allocation", "shortfall", "Still required", "Eligible planned procurement"]) {
			expect(text).not.toContain(forbidden);
		}
	});
});


describe("PlanItemEditorScreen — View classification details is offered only where it opens", () => {
	it("shows the link when the server marks a source readable", () => {
		const wrapper = make();
		expect(wrapper.find('[data-testid="ppi-view-classification"]').exists()).toBe(true);
	});

	it("omits the link when no source is readable for this viewer", () => {
		const unreadable = SOURCES.map((row) => ({ ...row, classification_readable: false }));
		const wrapper = make({ item: item({ sources: unreadable }) });
		expect(wrapper.find('[data-testid="ppi-view-classification"]').exists()).toBe(false);
	});
});
