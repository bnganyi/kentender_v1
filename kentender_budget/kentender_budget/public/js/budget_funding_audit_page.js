// BUD-UI-12 — Audit History workspace page (shared shell + audit fixture).
(function () {
	"use strict";

	kentender_budget.workspace.registerPage("budget-audit", {
		title: __("Audit"),
		fixtureKey: "audit",
		isStub: false,
	});
})();
