// BUD-UI-10 — Downstream Usage workspace page (shared shell + downstream fixture).
(function () {
	"use strict";

	kentender_budget.workspace.registerPage("budget-downstream", {
		title: __("Downstream Usage"),
		fixtureKey: "downstream",
		isStub: false,
	});
})();
