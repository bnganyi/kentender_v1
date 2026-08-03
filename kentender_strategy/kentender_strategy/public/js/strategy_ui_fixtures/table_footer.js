// Shared Strategy list-table footer (range + Rows per page + numbered pager).
frappe.provide("kentender_strategy.ui_fixtures");

kentender_strategy.ui_fixtures.tablePaginationFooterHtml = function () {
	return (
		'<div class="kt-str-table-footer bg-surface-bright border-t border-outline-variant p-4 flex flex-wrap justify-between items-center gap-3" data-testid="kt-str-table-footer" data-kt-str-table-footer>' +
		'<span class="text-label-sm text-on-surface-variant font-medium" data-kt-str-footer-range>Showing 0 of 0</span>' +
		'<div class="kt-str-table-footer-right flex items-center gap-3" data-kt-str-footer-right>' +
		'<div class="kt-str-footer-page-size flex items-center gap-2" data-kt-str-footer-page-size-wrap>' +
		'<span class="text-label-sm text-on-surface-variant font-medium whitespace-nowrap">' +
		"Rows per page" +
		"</span>" +
		'<div class="kt-str-footer-page-size-control relative">' +
		'<select class="kt-str-footer-page-size-select" data-kt-str-footer-page-size aria-label="Rows per page">' +
		'<option value="10">10</option>' +
		'<option value="20" selected>20</option>' +
		'<option value="50">50</option>' +
		'<option value="100">100</option>' +
		"</select>" +
		'<span class="material-symbols-outlined kt-str-footer-page-size-glyph" aria-hidden="true">expand_more</span>' +
		"</div>" +
		"</div>" +
		'<div class="kt-str-footer-pager flex items-center gap-2" data-kt-str-footer-pager data-testid="kt-str-footer-pager">' +
		'<button type="button" class="kt-str-footer-page-btn" data-kt-str-footer-prev disabled aria-label="Previous page">' +
		'<span class="material-symbols-outlined text-[16px]">chevron_left</span>' +
		"</button>" +
		'<div class="kt-str-footer-pages flex items-center gap-2" data-kt-str-footer-pages></div>' +
		'<button type="button" class="kt-str-footer-page-btn" data-kt-str-footer-next disabled aria-label="Next page">' +
		'<span class="material-symbols-outlined text-[16px]">chevron_right</span>' +
		"</button>" +
		"</div>" +
		"</div>" +
		"</div>"
	);
};
