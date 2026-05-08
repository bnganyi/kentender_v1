// STD-LIB-0510 — Central facade over STD Engine Desk adapters (types via JSDoc; delegates only).
frappe.provide("kentender_procurement.std_library_api");

/**
 * @typedef {Object} StdLibrarySummary
 * @property {number} active_count
 * @property {number} needs_attention_count
 * @property {number} ready_for_review_count
 * @property {number} superseded_count
 * @property {number} package_import_count
 * @property {number} bundle_issue_count
 */

/**
 * @typedef {Object} StdLibraryTemplateListItem
 * @property {string} [version_code]
 * @property {string} [title]
 * @property {string} [revision_label]
 * @property {string} [status]
 * @property {Object} [action_availability]
 */

/**
 * @typedef {Object} StdLibraryTemplateDetail
 * @property {string} [title]
 * @property {string} [version_code]
 * @property {Object} [summary]
 * @property {Object} [validation]
 * @property {Object} [bundle_preview]
 * @property {Object} [usage]
 * @property {Object} [supersession]
 * @property {Object} [advanced]
 * @property {Object} [audit]
 */

/**
 * @typedef {Object} StdLibrarySourceEvidence
 * @property {string} [source_document]
 * @property {string} [source_file]
 * @property {string} [evidence_status]
 */

/**
 * @typedef {Object} StdLibraryValidationSummary
 * @property {boolean} ok
 * @property {Array<Object>} rows
 * @property {string} [message]
 */

/**
 * @typedef {Object} StdValidationCategory
 * @property {string} [category]
 * @property {string} [state]
 */

/**
 * @typedef {Object} StdValidationFinding
 * @property {string} [text]
 */

/**
 * @typedef {Object} StdBundlePreview
 * @property {Object} [status_bar]
 * @property {Array<string>} [outline]
 * @property {Array<Object>} [preview_blocks]
 * @property {Array<Object>} [placeholders]
 */

/**
 * @typedef {Object} StdBundlePlaceholder
 * @property {string} [group]
 * @property {Array<Object>} [rows]
 */

/**
 * @typedef {Object} StdUsageSummary
 * @property {number} [tenders_using_count]
 */

/**
 * @typedef {Object} StdSupersessionSummary
 * @property {Object} [lineage]
 * @property {Object} [impact]
 */

/**
 * @typedef {Object} StdAdvancedTechnicalData
 * @property {Array<Object>} [sections]
 * @property {Object} [raw_package]
 */

/**
 * @typedef {Object} StdAuditEvent
 * @property {string} [timestamp]
 * @property {string} [actor]
 * @property {string} [event]
 */

/**
 * @typedef {Object} StdPackageImportDraft
 * @property {boolean} ok
 * @property {string} import_code
 */

/**
 * @typedef {Object} StdPackageDetectedStructure
 * @property {boolean} ok
 * @property {Object|null} [summary]
 */

/**
 * @typedef {Object} StdActionAvailability
 * @property {boolean} [allowed]
 * @property {string} [message]
 * @property {string|null} [denial_code]
 */

(function () {
	const sum = kentender_procurement.std_library_summary;
	const tpl = kentender_procurement.std_library_templates;
	const act = kentender_procurement.std_library_actions;
	const imp = kentender_procurement.std_library_import_wizard;
	const api = kentender_procurement.std_library_api;

	/** Client-side default until server exposes draft creation (matches wizard shell). */
	const DEFAULT_IMPORT_CODE = "STD-IMPORT-DRAFT";

	async function loadDetail(versionCode) {
		if (!tpl?.fetchDetail) return { ok: false, detail: null };
		return tpl.fetchDetail(versionCode);
	}

	api.getStdLibrarySummary = async function () {
		return sum.getSummary();
	};

	api.getStdLibraryTemplates = async function (filters) {
		return tpl.fetch(filters || {});
	};

	api.getStdLibraryTemplate = async function (versionCode) {
		return tpl.fetchDetail(versionCode);
	};

	api.getActionAvailability = async function (context) {
		return act.getActionAvailability(context);
	};

	/**
	 * Stub: no dedicated draft DocType API yet; matches wizard initial `importCode`.
	 * @returns {Promise<StdPackageImportDraft>}
	 */
	api.createPackageImportDraft = async function () {
		return { ok: true, import_code: DEFAULT_IMPORT_CODE };
	};

	api.selectPackage = async function (payload) {
		return imp.selectPackage(payload || {});
	};

	/** @param {Object} importCodeOrPayload First arg may be full payload (wizard) or import_code string. */
	api.saveSourceEvidence = async function (importCodeOrPayload, payload) {
		if (payload !== undefined && payload !== null && typeof payload === "object") {
			const base = { ...payload };
			if (importCodeOrPayload != null && importCodeOrPayload !== "") {
				base.import_code = String(importCodeOrPayload);
			}
			return imp.saveSourceEvidence(base);
		}
		return imp.saveSourceEvidence(importCodeOrPayload || {});
	};

	api.getDetectedStructure = async function (importCode) {
		return imp.getDetectedStructure(importCode);
	};

	api.validateImport = async function (importCode) {
		return imp.runValidation(importCode);
	};

	api.getImportValidation = async function (importCode) {
		return imp.getValidation(importCode);
	};

	api.generateImportBundlePreview = async function (importCode) {
		return imp.generateBundlePreview(importCode);
	};

	api.getImportBundlePreview = async function (importCode) {
		return imp.getBundlePreview(importCode);
	};

	api.getImportPlaceholderList = async function (importCode) {
		return imp.getPlaceholderList(importCode);
	};

	api.getFinalReview = async function (importCode) {
		return imp.getFinalReview(importCode);
	};

	api.submitImportForReview = async function (importCode) {
		return imp.submitReview(importCode);
	};

	api.activateImport = async function (importCode) {
		return imp.activateImport(importCode);
	};

	api.getPackageSources = async function () {
		return imp.getPackageSources();
	};

	api.registerSourceDocument = async function (payload) {
		return imp.registerSourceDocument(payload || {});
	};

	api.getLibraryValidationSummary = async function () {
		return imp.getLibraryValidationSummary();
	};

	api.validateLibrary = async function (payload) {
		return imp.runLibraryValidation(payload || {});
	};

	/**
	 * Projection of `get_std_library_template_detail` — not a separate HTTP endpoint.
	 * @param {string} versionCode
	 * @returns {Promise<{ ok: boolean, validation: Object|null, detail: Object|null }>}
	 */
	api.getTemplateValidation = async function (versionCode) {
		const r = await loadDetail(versionCode);
		const d = r?.detail || null;
		return { ok: Boolean(r?.ok && d), validation: d ? d.validation || null : null, detail: d };
	};

	/**
	 * Same payload source as {@link api.getTemplateValidation}; naming aligns with pack (read-only snapshot).
	 */
	api.validateTemplate = async function (versionCode) {
		return api.getTemplateValidation(versionCode);
	};

	api.generateTemplateBundlePreview = async function (versionCode) {
		const r = await loadDetail(versionCode);
		const d = r?.detail || null;
		return { ok: Boolean(r?.ok && d), bundle_preview: d ? d.bundle_preview || null : null, detail: d };
	};

	api.getTemplateBundlePreview = async function (versionCode) {
		return api.generateTemplateBundlePreview(versionCode);
	};

	api.getTemplatePlaceholders = async function (versionCode) {
		const r = await loadDetail(versionCode);
		const d = r?.detail || null;
		const bp = d?.bundle_preview || {};
		const ph = Array.isArray(bp.placeholders) ? bp.placeholders : [];
		return { ok: Boolean(r?.ok && d), placeholders: ph, detail: d };
	};

	api.getTemplateUsage = async function (versionCode) {
		const r = await loadDetail(versionCode);
		const d = r?.detail || null;
		return { ok: Boolean(r?.ok && d), usage: d ? d.usage || null : null, detail: d };
	};

	api.getTemplateSupersession = async function (versionCode) {
		const r = await loadDetail(versionCode);
		const d = r?.detail || null;
		return { ok: Boolean(r?.ok && d), supersession: d ? d.supersession || null : null, detail: d };
	};

	api.createTemplateRevision = async function (_versionCode) {
		return {
			ok: false,
			message: __("Create revision is handled via desk actions when implemented."),
		};
	};

	api.getTemplateAudit = async function (versionCode) {
		const r = await loadDetail(versionCode);
		const d = r?.detail || null;
		return { ok: Boolean(r?.ok && d), audit: d ? d.audit || null : null, detail: d };
	};
})();
