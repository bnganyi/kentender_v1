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
	const api = kentender_procurement.std_library_api;

	function _summaryAdapter() {
		return kentender_procurement.std_library_summary;
	}

	function _templatesAdapter() {
		return kentender_procurement.std_library_templates;
	}

	function _actionsAdapter() {
		return kentender_procurement.std_library_actions;
	}

	function _importWizardAdapter() {
		return kentender_procurement.std_library_import_wizard;
	}

	/** Client-side default until server exposes draft creation (matches wizard shell). */
	const DEFAULT_IMPORT_CODE = "STD-IMPORT-DRAFT";

	async function loadDetail(versionCode) {
		const tpl = _templatesAdapter();
		if (!tpl?.fetchDetail) return { ok: false, detail: null };
		return tpl.fetchDetail(versionCode);
	}

	api.getStdLibrarySummary = async function () {
		const sum = _summaryAdapter();
		if (!sum?.getSummary) {
			return {
				active_count: 0,
				needs_attention_count: 0,
				ready_for_review_count: 0,
				superseded_count: 0,
				package_import_count: 0,
				bundle_issue_count: 0,
			};
		}
		return sum.getSummary();
	};

	api.getStdLibraryTemplates = async function (filters) {
		const tpl = _templatesAdapter();
		if (!tpl?.fetch) {
			return { ok: false, rows: [], items: [], total_count: 0, queue: null, applied_filters: {} };
		}
		return tpl.fetch(filters || {});
	};

	api.getStdLibraryTemplate = async function (versionCode) {
		const tpl = _templatesAdapter();
		if (!tpl?.fetchDetail) return { ok: false, detail: null };
		return tpl.fetchDetail(versionCode);
	};

	api.getActionAvailability = async function (context) {
		const act = _actionsAdapter();
		if (!act?.getActionAvailability) return { allowed: false, message: __("Unavailable") };
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
		const imp = _importWizardAdapter();
		if (!imp?.selectPackage) return { ok: false };
		return imp.selectPackage(payload || {});
	};

	/** @param {Object} importCodeOrPayload First arg may be full payload (wizard) or import_code string. */
	api.saveSourceEvidence = async function (importCodeOrPayload, payload) {
		const imp = _importWizardAdapter();
		if (!imp?.saveSourceEvidence) return { ok: false };
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
		const imp = _importWizardAdapter();
		return imp?.getDetectedStructure ? imp.getDetectedStructure(importCode) : { ok: false };
	};

	api.validateImport = async function (importCode) {
		const imp = _importWizardAdapter();
		return imp?.runValidation ? imp.runValidation(importCode) : { ok: false };
	};

	api.getImportValidation = async function (importCode) {
		const imp = _importWizardAdapter();
		return imp?.getValidation ? imp.getValidation(importCode) : { ok: false };
	};

	api.generateImportBundlePreview = async function (importCode) {
		const imp = _importWizardAdapter();
		return imp?.generateBundlePreview ? imp.generateBundlePreview(importCode) : { ok: false };
	};

	api.getImportBundlePreview = async function (importCode) {
		const imp = _importWizardAdapter();
		return imp?.getBundlePreview ? imp.getBundlePreview(importCode) : { ok: false };
	};

	api.getImportPlaceholderList = async function (importCode) {
		const imp = _importWizardAdapter();
		return imp?.getPlaceholderList ? imp.getPlaceholderList(importCode) : { ok: false, placeholders: [] };
	};

	api.getFinalReview = async function (importCode) {
		const imp = _importWizardAdapter();
		return imp?.getFinalReview ? imp.getFinalReview(importCode) : { ok: false };
	};

	api.submitImportForReview = async function (importCode) {
		const imp = _importWizardAdapter();
		return imp?.submitReview ? imp.submitReview(importCode) : { ok: false };
	};

	api.activateImport = async function (importCode) {
		const imp = _importWizardAdapter();
		return imp?.activateImport ? imp.activateImport(importCode) : { ok: false };
	};

	api.getPackageSources = async function () {
		const imp = _importWizardAdapter();
		return imp?.getPackageSources ? imp.getPackageSources() : { ok: false, sources: [] };
	};

	api.registerSourceDocument = async function (payload) {
		const imp = _importWizardAdapter();
		return imp?.registerSourceDocument ? imp.registerSourceDocument(payload || {}) : { ok: false };
	};

	api.getLibraryValidationSummary = async function () {
		const imp = _importWizardAdapter();
		return imp?.getLibraryValidationSummary ? imp.getLibraryValidationSummary() : { ok: false, rows: [] };
	};

	api.validateLibrary = async function (payload) {
		const imp = _importWizardAdapter();
		return imp?.runLibraryValidation ? imp.runLibraryValidation(payload || {}) : { ok: false };
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
