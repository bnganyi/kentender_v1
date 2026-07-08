// STD-LIB-0120 — client adapter for summary card counts.
frappe.provide("kentender_procurement.std_library_summary");

(function () {
	const METHOD =
		"kentender_procurement.tender_management.api.std_library_summary.get_std_library_summary_counts";

	const ZERO = Object.freeze({
		active_count: 0,
		needs_attention_count: 0,
		ready_for_review_count: 0,
		superseded_count: 0,
		package_import_count: 0,
		bundle_issue_count: 0,
	});

	kentender_procurement.std_library_summary.getSummary = async function () {
		try {
			const r = await frappe.call({
				method: METHOD,
				type: "GET",
			});
			const message = (r && r.message) || {};
			return {
				active_count: Number(message.active_count || 0),
				needs_attention_count: Number(message.needs_attention_count || 0),
				ready_for_review_count: Number(message.ready_for_review_count || 0),
				superseded_count: Number(message.superseded_count || 0),
				package_import_count: Number(message.package_import_count || 0),
				bundle_issue_count: Number(message.bundle_issue_count || 0),
			};
		} catch (err) {
			return { ...ZERO };
		}
	};
})();
