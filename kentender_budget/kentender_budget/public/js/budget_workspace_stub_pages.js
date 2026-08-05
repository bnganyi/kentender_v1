// BUD-UI-03 — Sibling Budget workspace tabs (partial stubs sharing chrome).
(function () {
	"use strict";

	var STUBS = [
		{ slug: "budget-revisions", title: __("Revisions") },
		{ slug: "budget-downstream", title: __("Downstream Usage") },
		{ slug: "budget-review", title: __("Review") },
		{ slug: "budget-audit", title: __("Audit") },
	];

	STUBS.forEach(function (stub) {
		kentender_budget.workspace.registerPage(stub.slug, {
			title: stub.title,
			isStub: true,
		});
	});
})();
