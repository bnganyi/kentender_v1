// Shared DS Stitch Desk recipes — design_system_refactor sample_code_1/2.
// Prefer these class names; see kt_stitch_desk_chrome.css.
frappe.provide("kentender_core.ui_fixtures");

/**
 * Form section title (sample_1): Manrope h3 + bottom border.
 * @param {string} label
 * @param {object} [opts]
 * @param {string} [opts.tag] default h3
 * @param {string} [opts.extraClass]
 */
kentender_core.ui_fixtures.dsSectionTitleHtml = function (label, opts) {
	opts = opts || {};
	var tag = opts.tag || "h3";
	var extra = opts.extraClass ? " " + opts.extraClass : "";
	return (
		"<" +
		tag +
		' class="kt-ds-section-title font-headline-sm text-headline-sm text-on-surface' +
		extra +
		'">' +
		frappe.utils.escape_html(label) +
		"</" +
		tag +
		">"
	);
};

/**
 * Muted table thead row class string (sample_2).
 */
kentender_core.ui_fixtures.dsTableHeadRowClass = function () {
	return "kt-ds-table-head border-b border-subtle bg-surface-container-low";
};

/**
 * Toolbar / list filter band class string (sample_2).
 */
kentender_core.ui_fixtures.dsToolbarBandClass = function () {
	return "kt-ds-toolbar-band p-4 border-b border-subtle";
};

/**
 * Data block card class string.
 */
kentender_core.ui_fixtures.dsDataBlockClass = function () {
	return "kt-ds-data-block bg-surface-container-lowest border border-subtle rounded-lg shadow-sm overflow-hidden";
};
