// Shared Strategy list-table footer (range + Page Size + page-of-pages).
frappe.provide("kentender_strategy.ui_fixtures");

kentender_strategy.ui_fixtures.tablePaginationFooterHtml = function () {
	return (
		'<div class="bg-surface-container-low border-t border-outline-variant p-3 flex flex-wrap justify-between items-center gap-3 text-sm text-on-surface-variant" data-testid="kt-str-table-footer" data-kt-str-table-footer>' +
		'<span class="text-body-md text-on-surface-variant" data-kt-str-footer-range>Showing 0 of 0 records</span>' +
		'<div class="flex items-center gap-3">' +
		'<label class="flex items-center gap-2 text-body-md text-on-surface-variant whitespace-nowrap">' +
		"<span>Page Size</span>" +
		'<select class="bg-surface-container-lowest border border-outline-variant rounded-md py-1 pl-2 pr-7 text-sm text-on-surface focus:ring-primary focus:border-primary outline-none cursor-pointer" data-kt-str-footer-page-size aria-label="Page Size">' +
		'<option value="10" selected>10</option>' +
		'<option value="20">20</option>' +
		'<option value="50">50</option>' +
		'<option value="100">100</option>' +
		"</select>" +
		"</label>" +
		'<div class="flex items-center border border-outline-variant rounded-md overflow-hidden bg-surface-container-lowest" data-kt-str-footer-pager>' +
		'<button type="button" class="p-1.5 hover:bg-surface-container disabled:opacity-40 transition-colors" data-kt-str-footer-prev disabled aria-label="Previous page">' +
		'<span class="material-symbols-outlined text-[18px]">chevron_left</span>' +
		"</button>" +
		'<span class="px-3 text-body-md text-on-surface tabular-nums whitespace-nowrap" data-kt-str-footer-page>1 of 1</span>' +
		'<button type="button" class="p-1.5 hover:bg-surface-container disabled:opacity-40 transition-colors" data-kt-str-footer-next disabled aria-label="Next page">' +
		'<span class="material-symbols-outlined text-[18px]">chevron_right</span>' +
		"</button>" +
		"</div>" +
		"</div>" +
		"</div>"
	);
};
