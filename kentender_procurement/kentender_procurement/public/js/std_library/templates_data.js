// STD-LIB-0130 — client adapter for search/filter templates API.
frappe.provide("kentender_procurement.std_library_templates");

(function () {
	const METHOD =
		"kentender_procurement.tender_management.api.std_library_templates.get_std_library_templates";
	const DETAIL_METHOD =
		"kentender_procurement.tender_management.api.std_library_templates.get_std_library_template_detail";

	kentender_procurement.std_library_templates.fetch = async function (params) {
		try {
			const r = await frappe.call({
				method: METHOD,
				args: params || {},
				type: "GET",
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				rows: Array.isArray(msg.rows) ? msg.rows : [],
				items: Array.isArray(msg.items) ? msg.items : [],
				total_count: Number(msg.total_count || 0),
				queue: msg.queue || null,
				applied_filters: msg.applied_filters || {},
			};
		} catch (err) {
			throw err;
		}
	};

	kentender_procurement.std_library_templates.fetchDetail = async function (versionCode) {
		try {
			const r = await frappe.call({
				method: DETAIL_METHOD,
				args: { version_code: versionCode },
				type: "GET",
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				detail: msg.detail || null,
			};
		} catch (err) {
			throw err;
		}
	};
})();
