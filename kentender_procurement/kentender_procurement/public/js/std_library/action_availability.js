// STD-LIB-0110 — client adapter for header action availability.
frappe.provide("kentender_procurement.std_library_actions");

(function () {
	const METHOD =
		"kentender_procurement.tender_management.api.std_library_action_availability.get_std_library_action_availability";
	const DEFAULT_DENIAL = __("Unavailable: this action is temporarily not available.");

	function denied(action_code, message, denial_code) {
		return {
			action_code: action_code,
			allowed: false,
			denial_code: denial_code || "STD_ACTION_UNAVAILABLE",
			message: message || DEFAULT_DENIAL,
			risk_level: "High",
		};
	}

	function normalize(rows, requested_codes) {
		const out = {};
		(rows || []).forEach(function (row) {
			if (!row || !row.action_code) return;
			out[row.action_code] = {
				action_code: row.action_code,
				allowed: Boolean(row.allowed),
				denial_code: row.denial_code || null,
				message: row.message || DEFAULT_DENIAL,
				risk_level: row.risk_level || "High",
			};
		});

		(requested_codes || []).forEach(function (code) {
			if (!out[code]) {
				out[code] = denied(code, DEFAULT_DENIAL, "STD_ACTION_NOT_RETURNED");
			}
		});
		return out;
	}

	kentender_procurement.std_library_actions.getActionAvailability = async function (action_codes) {
		const codes = Array.isArray(action_codes) ? action_codes : [];
		try {
			const r = await frappe.call({
				method: METHOD,
				// Send a plain comma-separated list so Python receives stable action codes.
				args: { action_codes: codes.join(",") },
				type: "GET",
			});
			const payload = (r && r.message) || {};
			const rows = payload.actions || [];
			return normalize(rows, codes);
		} catch (err) {
			const fallback = {};
			codes.forEach(function (code) {
				fallback[code] = denied(code, DEFAULT_DENIAL, "STD_ACTION_REQUEST_FAILED");
			});
			return fallback;
		}
	};
})();
