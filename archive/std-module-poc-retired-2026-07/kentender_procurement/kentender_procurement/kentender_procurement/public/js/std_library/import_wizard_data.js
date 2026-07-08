// STD-LIB-0210 — client adapter for import wizard Step 1 APIs.
frappe.provide("kentender_procurement.std_library_import_wizard");

(function () {
	const SOURCES_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.get_std_library_package_sources";
	const SELECT_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.select_std_library_import_package";
	const SOURCE_EVIDENCE_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.save_std_library_source_evidence";
	const DETECTED_STRUCTURE_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.get_std_library_detected_structure";
	const RUN_VALIDATION_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.run_std_library_import_validation";
	const GET_VALIDATION_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.get_std_library_import_validation";
	const GENERATE_BUNDLE_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.generate_std_library_bundle_preview";
	const GET_BUNDLE_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.get_std_library_bundle_preview";
	const GET_PLACEHOLDERS_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.get_std_library_placeholder_list";
	const GET_FINAL_REVIEW_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.get_std_library_import_final_review";
	const SUBMIT_REVIEW_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.submit_std_library_import_review";
	const ACTIVATE_IMPORT_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.activate_std_library_import";
	const REGISTER_SOURCE_DOCUMENT_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.register_std_library_source_document";
	const GET_LIBRARY_VALIDATION_SUMMARY_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.get_std_library_validation_summary";
	const RUN_LIBRARY_VALIDATION_METHOD =
		"kentender_procurement.tender_management.api.std_library_import_wizard.run_std_library_validation";

	kentender_procurement.std_library_import_wizard.getPackageSources = async function () {
		try {
			const r = await frappe.call({
				method: SOURCES_METHOD,
				type: "GET",
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				sources: Array.isArray(msg.sources) ? msg.sources : [],
			};
		} catch (err) {
			return { ok: false, sources: [] };
		}
	};

	kentender_procurement.std_library_import_wizard.selectPackage = async function (payload) {
		try {
			const r = await frappe.call({
				method: SELECT_METHOD,
				args: payload || {},
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				import_code: msg.import_code || "",
				metadata: msg.metadata || null,
				selection: msg.selection || null,
			};
		} catch (err) {
			const message = err?.message || __("Unable to detect package metadata.");
			return { ok: false, import_code: "", metadata: null, selection: null, message };
		}
	};

	kentender_procurement.std_library_import_wizard.saveSourceEvidence = async function (payload) {
		try {
			const r = await frappe.call({
				method: SOURCE_EVIDENCE_METHOD,
				args: payload || {},
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				import_code: msg.import_code || "",
				source_evidence: msg.source_evidence || null,
			};
		} catch (err) {
			const message = err?.message || __("Unable to save source evidence.");
			return { ok: false, import_code: "", source_evidence: null, message };
		}
	};

	kentender_procurement.std_library_import_wizard.getDetectedStructure = async function (import_code) {
		try {
			const r = await frappe.call({
				method: DETECTED_STRUCTURE_METHOD,
				args: { import_code: import_code || "" },
				type: "GET",
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				import_code: msg.import_code || "",
				summary: msg.summary || null,
				technical_details: msg.technical_details || null,
			};
		} catch (err) {
			const message = err?.message || __("Unable to load detected structure.");
			return { ok: false, import_code: "", summary: null, technical_details: null, message };
		}
	};

	kentender_procurement.std_library_import_wizard.runValidation = async function (import_code) {
		try {
			const r = await frappe.call({
				method: RUN_VALIDATION_METHOD,
				args: { import_code: import_code || "" },
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				import_code: msg.import_code || "",
				validation: msg.validation || null,
			};
		} catch (err) {
			const message = err?.message || __("Unable to run validation.");
			return { ok: false, import_code: "", validation: null, message };
		}
	};

	kentender_procurement.std_library_import_wizard.getValidation = async function (import_code) {
		try {
			const r = await frappe.call({
				method: GET_VALIDATION_METHOD,
				args: { import_code: import_code || "" },
				type: "GET",
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				import_code: msg.import_code || "",
				validation: msg.validation || null,
			};
		} catch (err) {
			const message = err?.message || __("Unable to load validation summary.");
			return { ok: false, import_code: "", validation: null, message };
		}
	};

	kentender_procurement.std_library_import_wizard.generateBundlePreview = async function (import_code) {
		try {
			const r = await frappe.call({
				method: GENERATE_BUNDLE_METHOD,
				args: { import_code: import_code || "" },
			});
			const msg = (r && r.message) || {};
			return { ok: Boolean(msg.ok), import_code: msg.import_code || "", status: msg.status || "" };
		} catch (err) {
			const message = err?.message || __("Unable to generate bundle preview.");
			return { ok: false, import_code: "", status: "", message };
		}
	};

	kentender_procurement.std_library_import_wizard.getBundlePreview = async function (import_code) {
		try {
			const r = await frappe.call({
				method: GET_BUNDLE_METHOD,
				args: { import_code: import_code || "" },
				type: "GET",
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				import_code: msg.import_code || "",
				outline: Array.isArray(msg.outline) ? msg.outline : [],
				sections: Array.isArray(msg.sections) ? msg.sections : [],
				actions: msg.actions || {},
				message: msg.message || "",
			};
		} catch (err) {
			const message = err?.message || __("Unable to load bundle preview.");
			return { ok: false, import_code: "", outline: [], sections: [], actions: {}, message };
		}
	};

	kentender_procurement.std_library_import_wizard.getPlaceholderList = async function (import_code) {
		try {
			const r = await frappe.call({
				method: GET_PLACEHOLDERS_METHOD,
				args: { import_code: import_code || "" },
				type: "GET",
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				import_code: msg.import_code || "",
				placeholders: Array.isArray(msg.placeholders) ? msg.placeholders : [],
			};
		} catch (err) {
			const message = err?.message || __("Unable to load placeholder list.");
			return { ok: false, import_code: "", placeholders: [], message };
		}
	};

	kentender_procurement.std_library_import_wizard.getFinalReview = async function (import_code) {
		try {
			const r = await frappe.call({
				method: GET_FINAL_REVIEW_METHOD,
				args: { import_code: import_code || "" },
				type: "GET",
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				import_code: msg.import_code || "",
				summary: msg.summary || {},
				blockers: Array.isArray(msg.blockers) ? msg.blockers : [],
				actions: msg.actions || {},
				status: msg.status || "",
				confirmation_text: msg.confirmation_text || {},
			};
		} catch (err) {
			const message = err?.message || __("Unable to load final review summary.");
			return {
				ok: false,
				import_code: "",
				summary: {},
				blockers: [],
				actions: {},
				status: "",
				confirmation_text: {},
				message,
			};
		}
	};

	kentender_procurement.std_library_import_wizard.submitReview = async function (import_code) {
		try {
			const r = await frappe.call({
				method: SUBMIT_REVIEW_METHOD,
				args: { import_code: import_code || "" },
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				import_code: msg.import_code || "",
				status: msg.status || "",
				message: msg.message || "",
				denial_code: msg.denial_code || null,
			};
		} catch (err) {
			const message = err?.message || __("Unable to submit for review.");
			return { ok: false, import_code: "", status: "", message, denial_code: null };
		}
	};

	kentender_procurement.std_library_import_wizard.activateImport = async function (import_code) {
		try {
			const r = await frappe.call({
				method: ACTIVATE_IMPORT_METHOD,
				args: { import_code: import_code || "" },
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				import_code: msg.import_code || "",
				status: msg.status || "",
				message: msg.message || "",
				denial_code: msg.denial_code || null,
			};
		} catch (err) {
			const message = err?.message || __("Unable to activate this STD import.");
			return { ok: false, import_code: "", status: "", message, denial_code: null };
		}
	};

	kentender_procurement.std_library_import_wizard.registerSourceDocument = async function (payload) {
		try {
			const r = await frappe.call({
				method: REGISTER_SOURCE_DOCUMENT_METHOD,
				args: payload || {},
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				source_document: msg.source_document || null,
				message: msg.message || "",
				denial_code: msg.denial_code || null,
			};
		} catch (err) {
			const message = err?.message || __("Unable to register source document.");
			return { ok: false, source_document: null, message, denial_code: null };
		}
	};

	kentender_procurement.std_library_import_wizard.getLibraryValidationSummary = async function () {
		try {
			const r = await frappe.call({
				method: GET_LIBRARY_VALIDATION_SUMMARY_METHOD,
				type: "GET",
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				rows: Array.isArray(msg.rows) ? msg.rows : [],
				message: msg.message || "",
				errors: [],
			};
		} catch (err) {
			const message = err?.message || __("Unable to load validation summary.");
			return { ok: false, rows: [], message, errors: [message] };
		}
	};

	kentender_procurement.std_library_import_wizard.runLibraryValidation = async function (payload) {
		try {
			const r = await frappe.call({
				method: RUN_LIBRARY_VALIDATION_METHOD,
				args: payload || {},
			});
			const msg = (r && r.message) || {};
			return {
				ok: Boolean(msg.ok),
				rows: Array.isArray(msg.rows) ? msg.rows : [],
				message: msg.message || "",
				errors: [],
			};
		} catch (err) {
			const message = err?.message || __("Unable to run library validation.");
			return { ok: false, rows: [], message, errors: [message] };
		}
	};
})();
