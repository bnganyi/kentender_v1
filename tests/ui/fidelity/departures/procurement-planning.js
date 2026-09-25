/**
 * Structure Procurement Planning builds that no artboard draws.
 *
 * A departure is legitimate — a board is a drawing made at a point in time,
 * and some of what the product needs was learned afterwards. What is not
 * legitimate is a departure nobody wrote down. The register in
 * `docs/mvp-1-r1/04_planning/PLN-CHG-001_FOLLOW_UPS.md` names four landmark
 * exemptions — `U14_EXECUTION_COLUMNS`, `U11_DECISION_TABLE`,
 * `U09_SCHEDULE_LABELS`, `U09_REMOVE_ACTION` — that exist nowhere in the code
 * any more. They were lost in the v1.23→v1.24 rewrite of the fidelity spec and
 * nobody noticed, which is exactly the failure this file exists to stop.
 *
 * Each entry carries what it is, why it is there and who decided. `testid` is
 * the handle: a `data-testid` survives a re-port in a way a DOM path does not.
 *
 * Keyed `Component#variant`. An entry is only consulted for its own variant,
 * so an addition legitimate on one state is not silently excused on another.
 */
export const DEPARTURES = {
	"AnnualPlanScreen#U07": [
		{
			testid: "ppl-project-name",
			because:
				"A whole-plan project name, offered as a control on a Draft. §10.6 omits the field " +
				"when blank — which is the state U07's own fixture is drawn in — so the board shows " +
				"the Add-a-project-name control instead and never the field itself. Found by the " +
				"browser gate, which takes the control up before comparing; the component fixture " +
				"leaves it blank and so never renders it.",
			authority: "PLN-CHG-001 §10.6 — Project name is omitted when blank",
		},
		{
			testid: "ppl-current-work",
			because:
				"The board writes each purchase's outstanding work as plain text in its own column. " +
				"On a real plan the column is the only thing distinguishing a purchase that is ready " +
				"from one that is not, and plain text made them read alike (found live 23 Sep 2026).",
			authority: "Owner review of the U07 purchases table, 23 September 2026",
		},
		{
			testid: "ppl-history",
			replaces: ["disclosure > disclosure-body > table"],
			because:
				"Same disclosure, different body: the board draws a table of acceptances, the build " +
				"draws the shared timeline. See ppl-history-timeline below for why.",
			authority: "PLN-CHG-001 §9.4 shared timeline pattern",
		},
		{
			testid: "ppl-history-timeline",
			because:
				"The board draws a table in the Changes-and-history disclosure. A plan built from " +
				"several departments' acceptances read as a dense wall of text; the timeline is the " +
				"established cross-module pattern for exactly this list (Departmental Needs, Strategy, Tenders).",
			authority: "PLN-CHG-001 §9.4 shared timeline pattern",
		},
		{
			testid: "ppl-incomplete-notice",
			because:
				"Names how many purchases are not yet ready, beside the table whose column says so. " +
				"The board draws no notice inside the Purchases region.",
			authority: "Owner review of U07, 23 September 2026",
		},
		{
			testid: "ppl-submission-issues",
			because:
				"Everything still standing between the plan and submission, for the one actor who holds " +
				"that action. Without it they met the blockers one at a time, because the server raised " +
				"only the first and discarded the rest.",
			authority: "Owner review of the Sign-and-submit refusal, 23 September 2026",
		},
	],
	// The board drew this state with every requirement allocated and no
	// history worth showing, so it draws neither section. A real plan has
	// both; the sections are the same ones U07 draws, in the same order.
	"AnnualPlanScreen#U07-FINANCE-COMPLETE": [
		{
			testid: "ppl-requirements",
			because: "The board's U07-FINANCE-COMPLETE fixture has nothing left to add, so it omits the section entirely. U07 draws it.",
			authority: "Board fixture state, not a structural choice",
		},
		{
			testid: "ppl-history",
			because: "The board's U07-FINANCE-COMPLETE fixture draws no Changes-and-history disclosure. U07 draws it.",
			authority: "Board fixture state, not a structural choice",
		},
		{
			testid: "ppl-current-work",
			because: "As U07 above — the purchases table's own outstanding-work column.",
			authority: "Owner review of the U07 purchases table, 23 September 2026",
		},
	],
	// PLN v1.27 §10.6 — the two new update variants (UPDATE-OVER-BUDGET
	// fixture): the same history departure as U07.
	"AnnualPlanScreen#U07-UPDATE-OVER-BUDGET": [
		{
			testid: "ppl-history-timeline",
			because:
				"The update's Changes and history draws the changed-purchases table (built) plus one " +
				"provenance line; the build keeps the shared acceptance timeline beneath the table, as " +
				"on U07, rather than a paragraph per acceptance.",
			authority: "PLN-CHG-001 §9.4 shared timeline pattern (as AnnualPlanScreen#U07)",
		},
	],
	"AnnualPlanScreen#U07-WAITING-BUDGET-REVISION": [
		{
			testid: "ppl-history-timeline",
			because:
				"The update's Changes and history draws the changed-purchases table (built) plus one " +
				"provenance line; the build keeps the shared acceptance timeline beneath the table, as " +
				"on U07, rather than a paragraph per acceptance.",
			authority: "PLN-CHG-001 §9.4 shared timeline pattern (as AnnualPlanScreen#U07)",
		},
	],
	// PLN v1.27 §10.5 — the grouped-requirements review (owner decision 25 Sep).
	// PLN v1.27 §10.4 — U02–U05 variants that abbreviate the summary strip.
	"DppPlanScreen#U02-CLOSED": [
		{
			testid: "pln-dpp-summary",
			because:
				"This variant's board is drawn from its parent and leaves out the summary strip " +
				"(requirements, cost, requirements needing details) that U02-AUTHOR-DRAFT and U05-HOD " +
				"draw; the build keeps the same strip on every U02–U05 state, so the counts do not " +
				"appear and disappear between states of one plan.",
			authority: "PLN-CHG-001 §10.4 U02 summary strip, inherited by its variants",
		},
	],
	"DppPlanScreen#U05-CORRECTION": [
		{
			testid: "pln-dpp-summary",
			because:
				"This variant's board is drawn from its parent and leaves out the summary strip " +
				"(requirements, cost, requirements needing details) that U02-AUTHOR-DRAFT and U05-HOD " +
				"draw; the build keeps the same strip on every U02–U05 state, so the counts do not " +
				"appear and disappear between states of one plan.",
			authority: "PLN-CHG-001 §10.4 U02 summary strip, inherited by its variants",
		},
	],
	"DppValidationScreen#U06": [
		{
			testid: "pln-review-row",
			replaces: ["region > group"],
			because:
				"The board draws each certified requirement as bare lines with its budget line and the " +
				"Planner's classification in one group. Three requirements read as one undivided stack of " +
				"titles, selects and budget lines, so each requirement is its own numbered block: the " +
				"department's facts (budget line included) together, then the Planner's decision in its own strip.",
			authority: "Owner decision on the U06 review layout, 25 September 2026",
		},
	],
	"DppValidationScreen#U06-SEGREGATION": [
		{
			testid: "pln-review-row",
			replaces: ["region > table"],
			because:
				"The board draws the certifier's read-only view as a table; the build keeps the same " +
				"grouped requirement blocks as the Planner's review (without any classification control), " +
				"so the two readings of one submission look alike.",
			authority: "Owner decision on the U06 review layout, 25 September 2026",
		},
	],
	// PLN v1.27 §10.10 U11-PLANNER — the reader layout, "same complete content".
	"PublicationResultScreen#U13": [
		{
			testid: "pub-context",
			because:
				"The U13 board stacks the plan title, reference and version as three unstyled lines; " +
				"U13-FAILED-AO and every other Planning header draw the one `.kt-page-scope` line, " +
				"which the build uses on every U13 state (found live 24 Sep 2026).",
			authority: "PLN-CHG-001 §10.12 header; U13-FAILED-AO board",
		},
	],
	"ReviewScreen#U11-PLANNER": [
		{
			testid: "rev-no-issues",
			because:
				"The reader boards (U11-READER, U11-PLANNER) leave the Decision summary's " +
				"'No blocking issues' line out; §10.10 gives a reader the same complete content as " +
				"the deciding actor, and that line is part of the Decision summary.",
			authority: "PLN-CHG-001 §10.10 U11-READER ('Same complete content')",
		},
	],
	"ReviewScreen#U11-AO": [
		{
			testid: "rev-no-issues",
			because:
				"Either no blocking issues, or the exact issues — never neither. The board draws the " +
				"issue list only; a decision screen that says nothing when there is nothing wrong " +
				"leaves the reviewer unable to tell 'checked and clear' from 'not checked'.",
			authority: "PLN-CHG-001 §10.10 — the decision never precedes a hidden material issue",
		},
		{
			omits: ["notice"],
			because:
				"The board opens with an information notice stating what this decision does and does " +
				"not do. The build states the same sentence once, in the decision block with the " +
				"actions it qualifies, rather than twice on one screen.",
			authority: "Build choice, recorded 24 September 2026 — pending design review",
		},
		{
			omits: ["region > table > meta-row"],
			because:
				"The board draws one purchase row already expanded to show its detail. Live, the row " +
				"detail opens on request; the container exists, in the same place, once a row is opened.",
			authority: "Board fixture state, not a structural choice",
		},
	],
	"FinanceTaskScreen#U10": [
		{
			omits: ["notice"],
			because:
				"As U11-AO: the board's opening information notice says what confirming means, and " +
				"the build says it once in the decision block beside the actions it qualifies " +
				"(`fnt-consequence`).",
			authority: "Build choice, recorded 24 September 2026 — pending design review",
		},
	],
	"SourceEvidenceScreen#U12": [
		{
			path: "region.is-secondary > group",
			because:
				"The board groups the certification and the Procurement review as two blocks; the " +
				"build adds a third for the acceptance that links them, which the read model supplies " +
				"and the board's fixture did not.",
			authority: "Build choice, recorded 24 September 2026 — pending design review",
		},
	],
	"WorkspaceScreen#U01-HOD": [
		{
			testid: "pln-own-plan-region",
			because:
				"U01-HOD draws the departmental actor's required decision and the register beneath it. " +
				"The build states their own plan's position between the two, which U01-DEPARTMENT-AUTHOR " +
				"draws and this variant's fixture had no plan for.",
			authority: "Board fixture state, not a structural choice",
		},
		{
			omits: ["region.is-secondary > table"],
			because:
				"The register table renders from the departmental-plan list; this variant's fixture " +
				"drives the actor's own plan instead, so the register is empty and states that.",
			authority: "Board fixture state, not a structural choice",
		},
		{
			path: "region.is-secondary",
			because:
				"The build's own-plan position and the register are separate secondary sections; " +
				"U01-HOD's fixture draws only the register.",
			authority: "Board fixture state, not a structural choice",
		},
		{
			path: "region.is-secondary > group",
			because:
				"The own-plan position states its facts in a group rule, as U01-CURRENT-UPDATE draws " +
				"for the same block.",
			authority: "Artboards-U01 U01-CURRENT-UPDATE",
		},
	],
};

/** The variants whose contract is checked at component level, so a screen
 *  cannot quietly stop being covered. */
export const COVERED = [
	"AnnualPlanScreen#U07",
	"AnnualPlanScreen#U07-FINANCE-COMPLETE",
	"AnnualPlanScreen#U07-UPDATE-OVER-BUDGET",
	"AnnualPlanScreen#U07-WAITING-BUDGET-REVISION",
	"DppPlanScreen#U02-AUTHOR-DRAFT",
	"DppPlanScreen#U02-CLOSED",
	"DppPlanScreen#U05-HOD",
	"DppPlanScreen#U05-CORRECTION",
	"DppValidationScreen#U06",
	"DppValidationScreen#U06-SEGREGATION",
	"WorkspaceScreen#U01",
	"WorkspaceScreen#U01-CURRENT-UPDATE-OVER-BUDGET",
	"WorkspaceScreen#U01-CURRENT-UPDATE-WAITING-BUDGET",
	"WorkspaceScreen#U01-HOD",
	"FinanceTaskScreen#U10",
	"PublicationResultScreen#U13",
	"ReviewScreen#U11-AO",
	"ReviewScreen#U11-PLANNER",
	"SourceEvidenceScreen#U12",
	"ProgressScreen#U14",
	"CorrectionRequestsScreen#U16",
];
