// STD-LIB-0530 — Pack §25 user-facing copy and safe error strings (loads after std_library_api.js).
frappe.provide("kentender_procurement.std_library_user_messages");

(function () {
	const U = kentender_procurement.std_library_user_messages;

	U.MSG_NO_OFFICIAL_STDS_TITLE = __("No official STDs are available.");
	U.MSG_NO_OFFICIAL_STDS_HINT = __(
		"Import an official structured STD package before tenders can use standard documents.",
	);

	U.MSG_NO_ACTIVE_TITLE = __("No active STD versions are available.");
	U.MSG_NO_ACTIVE_HINT = __(
		"An STD must be imported, validated, reviewed, and activated before tenders can use it.",
	);

	U.MSG_NO_NEEDS_ATTENTION_TITLE = __("No STD versions currently require attention.");

	U.MSG_VALIDATION_FAILED = __(
		"Validation could not complete. Review the validation details or contact a system administrator if the issue persists.",
	);

	U.MSG_BUNDLE_PREVIEW_EMPTY_TITLE = __("No bundle preview has been generated yet.");
	U.MSG_BUNDLE_PREVIEW_EMPTY_HINT = __(
		"Generate a preview to review the recombined tender document.",
	);

	U.FALLBACK_LIST_LOAD = __("Unable to load the library list. Try again or contact a system administrator.");
	U.FALLBACK_DETAIL_LOAD = __("Unable to load STD details. Try again or contact a system administrator.");
	U.FALLBACK_GENERIC = __("Something went wrong. Try again or contact a system administrator.");

	function looksLikeTechnicalError(text) {
		const s = String(text || "");
		if (!s.trim()) return true;
		if (/Traceback|File "[^"]+",\s*line|^\s*at\s+/im.test(s)) return true;
		if (s.length > 600 && /^[\s\n\r]*[\[{]/.test(s)) return true;
		return false;
	}

	/**
	 * @param {unknown} raw
	 * @param {string} [fallback] translated fallback when raw is empty or unsafe
	 * @returns {string}
	 */
	U.sanitizeUserFacingError = function (raw, fallback) {
		const fb = fallback || U.FALLBACK_GENERIC;
		if (raw == null || raw === undefined) return fb;
		const s = String(raw).trim();
		if (!s) return fb;
		if (looksLikeTechnicalError(s)) return fb;
		if (s.length > 400) return s.slice(0, 397) + "…";
		return s;
	};

	/**
	 * @param {string} queue summary card queue key
	 * @returns {{ title: string, hint: string }}
	 */
	U.getLibraryListEmptyLines = function (queue) {
		switch (queue) {
			case "active":
				return { title: U.MSG_NO_ACTIVE_TITLE, hint: U.MSG_NO_ACTIVE_HINT };
			case "needs_attention":
				return {
					title: U.MSG_NO_NEEDS_ATTENTION_TITLE,
					hint: __("Use Import Official STD Package or adjust filters to find other versions."),
				};
			case "ready_review":
				return {
					title: __("No STD versions are ready for review."),
					hint: __("Validated versions awaiting review or activation will appear in this queue."),
				};
			case "superseded":
				return {
					title: __("No superseded STD versions match this view."),
					hint: __("Historical versions replaced by newer revisions appear here when applicable."),
				};
			case "package_imports":
				return {
					title: __("No recent package import activity matches this view."),
					hint: U.MSG_NO_OFFICIAL_STDS_HINT,
				};
			case "bundle_issues":
				return {
					title: __("No bundle preview issues require attention."),
					hint: __("STD versions with bundle preview problems that need correction appear here."),
				};
			default:
				return { title: U.MSG_NO_OFFICIAL_STDS_TITLE, hint: U.MSG_NO_OFFICIAL_STDS_HINT };
		}
	};
})();
