frappe.provide("kentender_procurement.planning_fixtures");

(function () {
	"use strict";
	kentender_procurement.planning_fixtures.emptyUpdateCancel = function () {
		return '<div class="kt-pln-05b-backdrop" data-kt-pln-05b role="presentation">' +
			'<section class="kt-pln-05b" role="dialog" aria-modal="true" aria-labelledby="kt-pln-05b-title" aria-describedby="kt-pln-05b-copy">' +
			'<div class="kt-pln-05b-head"><h3 id="kt-pln-05b-title">Cancel empty Plan update?</h3></div>' +
			'<div class="kt-pln-05b-body"><p id="kt-pln-05b-copy" data-kt-pln-05b-copy></p>' +
			'<dl class="kt-pln-05b-summary"><div><dt>Current Approved Version</dt><dd data-kt-pln-05b-approved></dd></div>' +
			'<div><dt>Approved value</dt><dd class="font-data-md" data-kt-pln-05b-value></dd></div>' +
			'<div class="kt-pln-05b-divider"><dt>Draft Version</dt><dd data-kt-pln-05b-draft></dd></div>' +
			'<div><dt>Effective changes</dt><dd class="font-data-md" data-kt-pln-05b-changes></dd></div></dl>' +
			'<div class="kt-pln-05b-info"><span class="material-symbols-outlined" aria-hidden="true">info</span><p data-kt-pln-05b-info></p></div>' +
			'<p class="kt-pln-05b-error" data-kt-pln-05b-error role="alert" hidden></p></div>' +
			'<div class="kt-pln-05b-actions"><button type="button" data-kt-pln-05b-keep>Keep draft</button>' +
			'<button type="button" class="kt-pln-05b-confirm" data-kt-pln-05b-confirm>Cancel empty update</button></div>' +
			'</section></div>';
	};
})();
