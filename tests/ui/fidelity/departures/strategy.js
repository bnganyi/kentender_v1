/**
 * Structure Strategy Alignment builds that its v1.8 STR-DES boards do not draw.
 *
 * Same shape as the Planning, Departmental Needs and Budget registries: what it
 * is, why it is there, and who decided. Anything unregistered fails, and an
 * entry that stops matching fails too.
 *
 * Strategy's boards are single-state — no `<sc-if>` switchers — so each one is
 * compared exactly as exported, with no state to resolve. Two of this module's
 * screens draw one board across two live scopes (the inline target editor and
 * the return dialog); those are asserted as two ordered sequences by the spec
 * beside this file, and their structure is compared per scope.
 */
/**
 * Every STR-DES board draws its tab row as a bare `<div>` with the layout
 * inlined and inline-styled `<button>`s inside it; the live screens use the
 * design system's own `.kt-tabs`/`.kt-tab`.
 */
const TABS_USE_THE_DESIGN_SYSTEM_CLASS = [
	{
		path: "card+blueprint > tabs",
		because:
			"The board draws `<div style=\"display:flex;gap:…;border-bottom:…\">` holding buttons " +
			"that carry their whole appearance inline — no class at all. `.kt-tabs` and `.kt-tab` " +
			"are real rules in kt_industry_tokens.css, and using them instead of copying the inline " +
			"styles is the standing rule for this codebase, not a departure from the design: it is " +
			"the same composition expressed in the system's own vocabulary. Reverting to the inline " +
			"form would be a fork of the token file by another name.",
		authority: "AGENTS.md §6.6 — kt_industry_tokens.css is the one canonical design system; `.kt-tabs`/`.kt-tab` at lines 499–520",
	},
];

export const DEPARTURES = {
	"PortfolioScreen#STR-DES-01": TABS_USE_THE_DESIGN_SYSTEM_CLASS,
	"PortfolioScreen#STR-DES-02": TABS_USE_THE_DESIGN_SYSTEM_CLASS,
	"PlanWorkspaceScreen#STR-DES-03": TABS_USE_THE_DESIGN_SYSTEM_CLASS,
	"PlanWorkspaceScreen#STR-DES-04": TABS_USE_THE_DESIGN_SYSTEM_CLASS,
	"ApprovalTaskScreen#STR-DES-06": TABS_USE_THE_DESIGN_SYSTEM_CLASS,
	"ApprovalTaskScreen#STR-DES-07": TABS_USE_THE_DESIGN_SYSTEM_CLASS,
	"ApprovalTaskScreen#STR-DES-08": TABS_USE_THE_DESIGN_SYSTEM_CLASS,
	"ApprovalTaskScreen#STR-DES-09": TABS_USE_THE_DESIGN_SYSTEM_CLASS,
};

/**
 * The screens whose structure is compared against a board. A screen with a
 * board that is not in this list is not done.
 */
export const COVERED = ["PortfolioScreen", "PlanWorkspaceScreen", "ApprovalTaskScreen"];
