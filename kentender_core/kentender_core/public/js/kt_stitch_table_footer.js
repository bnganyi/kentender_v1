// Shared Stitch Desk list-table footer — Showing X of Y + Rows per page + numbered pager.
// Strategy established this chrome; all Stitch Desk tables must use it (see kentender-stitch-desk-table-footer.mdc).
frappe.provide("kentender_core.ui_fixtures");

/**
 * @param {object} [opts]
 * @param {string} [opts.testid] data-testid on footer root
 * @param {string} [opts.ns] attribute namespace: "kt" → data-kt-table-footer; "str" → data-kt-str-table-footer
 */
kentender_core.ui_fixtures.tablePaginationFooterHtml = function (opts) {
	opts = opts || {};
	var ns = opts.ns || "kt";
	var prefix = ns === "str" ? "kt-str" : "kt";
	var testid = opts.testid || (prefix === "kt-str" ? "kt-str-table-footer" : "kt-table-footer");
	var footAttr = "data-" + prefix + "-table-footer";
	var rangeAttr = "data-" + prefix + "-footer-range";
	var rightAttr = "data-" + prefix + "-footer-right";
	var sizeWrapAttr = "data-" + prefix + "-footer-page-size-wrap";
	var sizeAttr = "data-" + prefix + "-footer-page-size";
	var pagerAttr = "data-" + prefix + "-footer-pager";
	var pagesAttr = "data-" + prefix + "-footer-pages";
	var prevAttr = "data-" + prefix + "-footer-prev";
	var nextAttr = "data-" + prefix + "-footer-next";
	var classNs = prefix === "kt-str" ? "kt-str" : "kt-stitch";

	return (
		'<div class="' +
		classNs +
		'-table-footer bg-surface-bright border-t border-outline-variant p-4 flex flex-wrap justify-between items-center gap-3" data-testid="' +
		testid +
		'" ' +
		footAttr +
		" data-kt-table-footer>" +
		'<span class="text-sm text-on-surface-variant font-medium" ' +
		rangeAttr +
		" data-kt-footer-range>Showing 0 of 0</span>" +
		'<div class="' +
		classNs +
		'-table-footer-right flex items-center gap-3" ' +
		rightAttr +
		">" +
		'<div class="' +
		classNs +
		'-footer-page-size flex items-center gap-2" ' +
		sizeWrapAttr +
		">" +
		'<span class="text-sm text-on-surface-variant font-medium whitespace-nowrap">Rows per page</span>' +
		'<div class="' +
		classNs +
		'-footer-page-size-control relative">' +
		'<select class="' +
		classNs +
		'-footer-page-size-select" ' +
		sizeAttr +
		' data-kt-footer-page-size aria-label="Rows per page">' +
		'<option value="10">10</option>' +
		'<option value="20" selected>20</option>' +
		'<option value="50">50</option>' +
		'<option value="100">100</option>' +
		"</select>" +
		'<span class="material-symbols-outlined ' +
		classNs +
		'-footer-page-size-glyph" aria-hidden="true">expand_more</span>' +
		"</div></div>" +
		'<div class="' +
		classNs +
		'-footer-pager flex items-center gap-2" ' +
		pagerAttr +
		' data-testid="' +
		testid +
		'-pager">' +
		'<button type="button" class="' +
		classNs +
		'-footer-page-btn" ' +
		prevAttr +
		' data-kt-footer-prev disabled aria-label="Previous page">' +
		'<span class="material-symbols-outlined text-[16px]">chevron_left</span></button>' +
		'<div class="' +
		classNs +
		'-footer-pages flex items-center gap-2" ' +
		pagesAttr +
		" data-kt-footer-pages></div>" +
		'<button type="button" class="' +
		classNs +
		'-footer-page-btn" ' +
		nextAttr +
		' data-kt-footer-next disabled aria-label="Next page">' +
		'<span class="material-symbols-outlined text-[16px]">chevron_right</span></button>' +
		"</div></div></div>"
	);
};
