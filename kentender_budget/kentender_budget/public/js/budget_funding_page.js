// BUD-CHG-001 v1.3 §10/D5 — BUD-UI-01/02/03/04/05, all under one Page
// ("budget-funding") sharing the /app/budget-funding URL prefix; the root
// Budget.vue branches on route segments to pick the screen.
//
// Not the spec's literal "/app/budget" — Frappe's client router
// (frappe/public/js/frappe/router.js `setup()`) unconditionally registers
// every readable doctype's own slug into `this.routes` and resolves a bare
// `/app/<slug>` against that map before ever falling back to a same-named
// Page; this collision poisons every route under that prefix, not just the
// workspace, since `/app/budget/<id>` etc. also resolve against the
// doctype first. The original collision (KenTender's own `Budget` DocType)
// was resolved by Phase 2's rename to `Procurement Budget` — but Phase 3
// restored ERPNext's own real `Budget` DocType (module "Accounts") into the
// name it freed, so the collision is permanent, not a temporary workaround:
// confirmed live, `Budget` still resolves to a DocType, just ERPNext's own
// one now. "budget-funding" has no such collision and stays the route
// prefix for good (D5, tracker decision log).
kentender_core.desk_page.register("budget-funding", {
	title: __("Budget & Funding"),
	bundles: ["kt_industry_page_rail.bundle.js", "budget_funding.bundle.js"],
	mount: (el) => frappe.kt_mount_budget_funding(el),
	sidebarWorkspaceKey: "procurement",
});
