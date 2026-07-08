// STD-LIB-0500 — Package import wizard shell (StdPackageImportWizardPage). Loads before std_library_shell.js.
// STD-LIB-0510: HTTP via kentender_procurement.std_library_api (after import_wizard_data + std_library_api).
frappe.provide("kentender_procurement.std_library_shell");

(function () {
	const shell = kentender_procurement.std_library_shell;
	const stdApi = kentender_procurement.std_library_api;
	const userMsg = kentender_procurement.std_library_user_messages;
	function safeErr(raw, fallback) {
		return userMsg.sanitizeUserFacingError(raw, fallback);
	}
	const IMPORT_STEPS = Object.freeze([
		__("1. Select Package (STD-LIB-0210)"),
		__("2. Confirm Source Evidence (STD-LIB-0220)"),
		__("3. Review Detected Structure (STD-LIB-0230)"),
		__("4. Validate Structured Model (STD-LIB-0240)"),
		__("5. Preview Tender Bundle (STD-LIB-0250)"),
		__("6. Submit for Review / Activate (STD-LIB-0260)"),
	]);

	shell.buildImportWizardFragment = function () {
		const wrap = document.createElement("div");
		wrap.className = "std-package-import-shell";
		wrap.setAttribute("data-testid", "std-package-import-page");
		const state = {
			currentStep: 0,
			highestUnlockedStep: 0,
			importCode: "STD-IMPORT-DRAFT",
			packageSources: [],
			step1: {
				package_source: "",
				package_entry: "",
				package_type: "",
				expected_std_category: "",
				package_version: "",
				error: "",
			},
			step2: {
				source_authority: "",
				source_title: "",
				source_revision: "",
				source_file: "",
				source_hash: "",
				prepared_by: "",
				review_status: "",
				notes: "",
				error: "",
			},
			step3: {
				summary: null,
				technical_details: null,
				detailsExpanded: false,
				loading: false,
				error: "",
			},
			step4: {
				validation: null,
				loading: false,
				error: "",
			},
			step5: {
				outline: [],
				sections: [],
				placeholders: [],
				actions: {},
				message: "",
				loading: false,
				error: "",
			},
			step6: {
				summary: null,
				blockers: [],
				actions: {},
				confirmationText: {},
				status: "",
				loading: false,
				submitting: false,
				activating: false,
				finalized: false,
				error: "",
			},
			stepValidity: [false, false, false, false, false, false],
		};

		const stepBodyForPlaceholder = () => `
			<h4>${IMPORT_STEPS[state.currentStep]}</h4>
			<p>${__(
				"This step shell is implemented in STD-LIB-0200. Detailed fields and validation are implemented in the corresponding step ticket.",
			)}</p>
		`;

		const getSelectedSource = () =>
			(state.packageSources || []).find((x) => x.value === state.step1.package_source) || null;
		const getEntriesForSource = () => (getSelectedSource()?.entries || []).filter(Boolean);
		const getSelectedEntry = () =>
			(getEntriesForSource() || []).find((x) => x.value === state.step1.package_entry) || null;
		const applyStep1Validity = () => {
			const s = state.step1;
			const metadataReady = Boolean(s.package_type && s.expected_std_category && s.package_version);
			state.stepValidity[0] = Boolean(s.package_source && s.package_entry && metadataReady);
			if (!state.stepValidity[0] && state.currentStep > 0) {
				state.currentStep = 0;
			}
		};
		const hydrateMetadata = (metadata) => {
			const md = metadata || {};
			state.step1.package_type = String(md.package_type || "");
			state.step1.expected_std_category = String(md.expected_std_category || "");
			state.step1.package_version = String(md.package_version || "");
			applyStep1Validity();
		};
		const applyStep2Validity = () => {
			const s = state.step2;
			const requiredReady = Boolean(
				s.source_authority && s.source_title && s.source_revision && s.review_status,
			);
			const fileHashPairValid = Boolean(
				(!s.source_file && !s.source_hash) || (s.source_file && s.source_hash),
			);
			state.stepValidity[1] = Boolean(requiredReady && fileHashPairValid && !s.error);
		};
		const applyStep3Validity = () => {
			const s = state.step3;
			state.stepValidity[2] = Boolean(!s.loading && !s.error && s.summary);
		};
		const applyStep4Validity = () => {
			const s = state.step4;
			const validation = s.validation || {};
			const categories = Array.isArray(validation.categories) ? validation.categories : [];
			state.stepValidity[3] = Boolean(!s.loading && !s.error && validation.result && categories.length);
		};
		const applyStep5Validity = () => {
			const s = state.step5;
			state.stepValidity[4] = Boolean(
				!s.loading &&
					!s.error &&
					Array.isArray(s.outline) &&
					s.outline.length &&
					Array.isArray(s.placeholders) &&
					s.placeholders.length,
			);
		};
		const applyStep6Validity = () => {
			const s = state.step6;
			const summary = s.summary || {};
			const requiredFieldsReady = Boolean(
				summary.std_title &&
					summary.revision &&
					summary.source_authority &&
					summary.source_evidence_status &&
					summary.validation_result &&
					summary.bundle_preview_status &&
					summary.generated_model_status,
			);
			const blockers = Array.isArray(s.blockers) ? s.blockers : [];
			const actionAllowed = Boolean(s.actions?.can_submit_review || s.actions?.can_activate);
			state.stepValidity[5] = Boolean(
				!s.loading && !s.error && requiredFieldsReady && !blockers.length && actionAllowed && s.finalized,
			);
		};
		const step1Body = () => {
			const entries = getEntriesForSource();
			return `
<div class="std-import-step1" data-testid="std-import-step1">
	<p class="std-import-step1-intro">${__("Select a structured STD package source.")}</p>
	<div class="std-import-form-grid">
		<label class="std-import-field">
			<span>${__("Package Source")}</span>
			<select class="form-control" data-testid="std-import-package-source-select">
				<option value="">${__("Select package source")}</option>
				${(state.packageSources || [])
					.map((source) => `<option value="${source.value}">${source.label}</option>`)
					.join("")}
			</select>
		</label>
		<label class="std-import-field">
			<span>${__("Package File or Registry Entry")}</span>
			<select class="form-control" data-testid="std-import-package-file-picker" ${
				state.step1.package_source ? "" : "disabled"
			}>
				<option value="">${__("Select package file/entry")}</option>
				${entries.map((entry) => `<option value="${entry.value}">${entry.label}</option>`).join("")}
			</select>
		</label>
	</div>
	<div class="std-import-warning" data-testid="std-import-raw-file-warning">
		${__(
			"Raw PDF, Word, or spreadsheet files may be attached as evidence but cannot by themselves create a working STD template. A structured STD package is required.",
		)}
	</div>
	${state.step1.error ? `<div role="alert" aria-live="polite" class="std-import-step-error">${state.step1.error}</div>` : ""}
	<div class="std-import-metadata-grid">
		<div class="std-import-metadata-card">
			<span>${__("Package Type")}</span>
			<strong data-testid="std-import-package-type">${state.step1.package_type || "—"}</strong>
		</div>
		<div class="std-import-metadata-card">
			<span>${__("Expected STD Category")}</span>
			<strong data-testid="std-import-package-category">${state.step1.expected_std_category || "—"}</strong>
		</div>
		<div class="std-import-metadata-card">
			<span>${__("Package Version")}</span>
			<strong data-testid="std-import-package-version">${state.step1.package_version || "—"}</strong>
		</div>
	</div>
</div>`;
		};
		const step2Body = () => `
<div class="std-import-step2" data-testid="std-import-step2">
	<p class="std-import-step2-intro">${__("Confirm the official source document and evidence metadata.")}</p>
	<div class="std-import-form-grid">
		<label class="std-import-field">
			<span>${__("Source Authority")}</span>
			<input class="form-control" data-testid="std-import-source-authority" value="${state.step2.source_authority}" />
		</label>
		<label class="std-import-field">
			<span>${__("Source Document Title")}</span>
			<input class="form-control" data-testid="std-import-source-title" value="${state.step2.source_title}" />
		</label>
		<label class="std-import-field">
			<span>${__("Revision Label")}</span>
			<input class="form-control" data-testid="std-import-source-revision" value="${state.step2.source_revision}" />
		</label>
		<label class="std-import-field">
			<span>${__("Review Status")}</span>
			<select class="form-control" data-testid="std-import-source-review-status">
				<option value="">${__("Select review status")}</option>
				${["Draft", "Under Review", "Approved"]
					.map((status) => `<option value="${status}" ${state.step2.review_status === status ? "selected" : ""}>${status}</option>`)
					.join("")}
			</select>
		</label>
		<label class="std-import-field">
			<span>${__("Source Evidence File")}</span>
			<input class="form-control" data-testid="std-import-source-file" value="${state.step2.source_file}" />
		</label>
		<label class="std-import-field">
			<span>${__("Source Hash")}</span>
			<input class="form-control" data-testid="std-import-source-hash" value="${state.step2.source_hash}" />
		</label>
		<label class="std-import-field">
			<span>${__("Prepared By")}</span>
			<input class="form-control" data-testid="std-import-source-prepared-by" value="${state.step2.prepared_by}" />
		</label>
		<label class="std-import-field">
			<span>${__("Notes")}</span>
			<textarea class="form-control" data-testid="std-import-source-notes">${state.step2.notes}</textarea>
		</label>
	</div>
	<div class="std-import-guidance" data-testid="std-import-source-guidance">
		${__(
			"The official document is retained as evidence. The structured package provides the system-readable template used for validation and generation.",
		)}
	</div>
	${state.step2.error ? `<div role="alert" aria-live="polite" class="std-import-step-error">${state.step2.error}</div>` : ""}
</div>`;
		const step3Body = () => {
			const s = state.step3;
			const summary = s.summary || {};
			const details = s.technical_details || {};
			return `
<div class="std-import-step3">
	<h4 data-testid="std-import-detected-structure">${__("Detected Structure")}</h4>
	${
		s.loading
			? `<p class="std-import-step3-loading">${__("Loading detected structure summary...")}</p>`
			: ""
	}
	${s.error ? `<div role="alert" aria-live="polite" class="std-import-step-error">${s.error}</div>` : ""}
	${
		!s.loading && !s.error && summary
			? `
	<div class="std-import-detected-summary">
		<div class="std-import-detected-row" data-testid="std-import-detected-sections"><span>${__(
			"Parts and Sections",
		)}</span><strong>${summary.parts_sections || "—"}</strong></div>
		<div class="std-import-detected-row"><span>${__("Locked Legal Text")}</span><strong>${summary.locked_legal_text || "—"}</strong></div>
		<div class="std-import-detected-row" data-testid="std-import-detected-parameters"><span>${__(
			"Parameters",
		)}</span><strong>${summary.parameters || "—"}</strong></div>
		<div class="std-import-detected-row" data-testid="std-import-detected-forms"><span>${__(
			"Forms",
		)}</span><strong>${summary.forms || "—"}</strong></div>
		<div class="std-import-detected-row" data-testid="std-import-detected-boq-rules"><span>${__(
			"BOQ Rules",
		)}</span><strong>${summary.boq_rules || "—"}</strong></div>
		<div class="std-import-detected-row" data-testid="std-import-detected-mappings"><span>${__(
			"Source Mappings",
		)}</span><strong>${summary.source_mappings || "—"}</strong></div>
		<div class="std-import-detected-row"><span>${__("Readiness Rules")}</span><strong>${summary.readiness_rules || "—"}</strong></div>
	</div>
	<button type="button" class="btn btn-default btn-sm" data-testid="std-import-expand-technical-details">${
		s.detailsExpanded ? __("Hide technical details") : __("Expand technical details")
	}</button>
	${
		s.detailsExpanded
			? `<div class="std-import-detected-technical">
			<p><strong>${__("Sections:")}</strong> ${(details.sections || []).join(", ") || "—"}</p>
			<p><strong>${__("Parameter groups:")}</strong> ${(details.parameter_groups || []).join(", ") || "—"}</p>
			<p><strong>${__("Form categories:")}</strong> ${(details.form_categories || []).join(", ") || "—"}</p>
			<p><strong>${__("Mapping coverage counts:")}</strong> ${JSON.stringify(details.mapping_coverage || {})}</p>
		</div>`
			: ""
	}
	`
			: ""
	}
</div>`;
		};
		const step4Body = () => {
			const s = state.step4;
			const validation = s.validation || {};
			const categories = Array.isArray(validation.categories) ? validation.categories : [];
			const blockers = Array.isArray(validation.blockers) ? validation.blockers : [];
			const categoryValue = (key) => categories.find((x) => x.key === key)?.status || "—";
			return `
<div class="std-import-step4">
	<div class="std-import-validation-summary" data-testid="std-import-validation-summary">
		<h4>${__("Validation Result")}: ${validation.result || "—"}</h4>
		<p>${validation.summary || ""}</p>
	</div>
	${
		s.loading
			? `<p class="std-import-step4-loading">${__("Running server-side validation...")}</p>`
			: ""
	}
	${s.error ? `<div role="alert" aria-live="polite" class="std-import-step-error">${s.error}</div>` : ""}
	${
		!s.loading
			? `<div class="std-import-validation-categories">
		<div class="std-import-validation-row" data-testid="std-import-validation-category-sections"><span>${__(
			"Sections",
		)}</span><strong>${categoryValue("sections")}</strong></div>
		<div class="std-import-validation-row"><span>${__("Locked Legal Text")}</span><strong>${categoryValue(
			"locked_legal_text",
		)}</strong></div>
		<div class="std-import-validation-row" data-testid="std-import-validation-category-parameters"><span>${__(
			"Parameters",
		)}</span><strong>${categoryValue("parameters")}</strong></div>
		<div class="std-import-validation-row" data-testid="std-import-validation-category-forms"><span>${__(
			"Forms",
		)}</span><strong>${categoryValue("forms")}</strong></div>
		<div class="std-import-validation-row" data-testid="std-import-validation-category-boq"><span>${__(
			"BOQ Rules",
		)}</span><strong>${categoryValue("boq_rules")}</strong></div>
		<div class="std-import-validation-row" data-testid="std-import-validation-category-mappings"><span>${__(
			"Source Mappings",
		)}</span><strong>${categoryValue("source_mappings")}</strong></div>
		<div class="std-import-validation-row" data-testid="std-import-validation-category-models"><span>${__(
			"Generated Models",
		)}</span><strong>${categoryValue("generated_models")}</strong></div>
		<div class="std-import-validation-row" data-testid="std-import-validation-category-bundle"><span>${__(
			"Bundle Rendering",
		)}</span><strong>${categoryValue("bundle_rendering")}</strong></div>
	</div>`
			: ""
	}
	<div class="std-import-validation-blockers" data-testid="std-import-validation-blockers">
		${
			blockers.length
				? blockers
						.map(
							(b) =>
								`<div class="std-import-validation-blocker"><p><strong>${b.category || __("Category")}:</strong> ${b.reason || ""}</p><p><strong>${__(
									"Fix",
								)}:</strong> ${b.fix_path || ""}</p><p><strong>${__("Code")}:</strong> ${b.code || ""}</p></div>`,
						)
						.join("")
				: `<p>${__("No blockers detected.")}</p>`
		}
	</div>
</div>`;
		};
		const step5Body = () => {
			const s = state.step5;
			return `
<div class="std-import-step5" data-testid="std-import-bundle-preview">
	${
		s.loading
			? `<p class="std-import-step5-loading">${__("Loading bundle preview...")}</p>`
			: ""
	}
	${s.error ? `<div role="alert" aria-live="polite" class="std-import-step-error">${s.error}</div>` : ""}
	${s.message ? `<p class="std-import-step5-message">${s.message}</p>` : ""}
	<div class="std-import-step5-layout">
		<nav class="std-import-bundle-outline" data-testid="std-import-bundle-outline">
			${(s.outline || [])
				.map(
					(row, idx) =>
						`<div class="std-import-bundle-outline-row" data-testid="std-import-bundle-section-${idx + 1}">${row.title || ""}</div>`,
				)
				.join("")}
		</nav>
		<section class="std-import-bundle-preview-pane">
			${(s.sections || [])
				.map(
					(row) =>
						`<article class="std-import-bundle-preview-block"><h5>${row.title || ""}</h5><p>${row.preview || ""}</p></article>`,
				)
				.join("")}
		</section>
	</div>
	<div class="std-import-placeholder-list" data-testid="std-import-placeholder-list">
		${(s.placeholders || []).map((p) => `<div class="std-import-placeholder-row">${p}</div>`).join("")}
	</div>
	<div class="std-import-step5-actions">
		<button type="button" class="btn btn-default btn-sm" data-testid="std-import-preview-browser" ${
			s.actions.preview_in_browser ? "" : "disabled"
		}>${__("Preview in Browser")}</button>
		<button type="button" class="btn btn-default btn-sm" data-testid="std-import-download-pdf" ${
			s.actions.download_pdf ? "" : "disabled"
		}>${__("Download Preview PDF")}</button>
		<button type="button" class="btn btn-default btn-sm" data-testid="std-import-download-docx" ${
			s.actions.download_docx ? "" : "disabled"
		}>${__("Download Preview DOCX")}</button>
	</div>
</div>`;
		};
		const step6Body = () => {
			const s = state.step6;
			const summary = s.summary || {};
			const blockers = Array.isArray(s.blockers) ? s.blockers : [];
			return `
<div class="std-import-step6">
	${
		s.loading
			? `<p class="std-import-step6-loading">${__("Loading final review summary...")}</p>`
			: ""
	}
	${s.error ? `<div role="alert" aria-live="polite" class="std-import-step-error">${s.error}</div>` : ""}
	<div class="std-import-final-summary" data-testid="std-import-final-summary">
		<div class="std-import-final-row"><span>${__("STD Title")}</span><strong>${summary.std_title || "—"}</strong></div>
		<div class="std-import-final-row"><span>${__("Revision")}</span><strong>${summary.revision || "—"}</strong></div>
		<div class="std-import-final-row"><span>${__("Source Authority")}</span><strong>${summary.source_authority || "—"}</strong></div>
		<div class="std-import-final-row"><span>${__("Source Evidence")}</span><strong>${summary.source_evidence_status || "—"}</strong></div>
		<div class="std-import-final-row"><span>${__("Validation Result")}</span><strong>${summary.validation_result || "—"}</strong></div>
		<div class="std-import-final-row"><span>${__("Bundle Preview")}</span><strong>${summary.bundle_preview_status || "—"}</strong></div>
		<div class="std-import-final-row"><span>${__("Generated Models")}</span><strong>${summary.generated_model_status || "—"}</strong></div>
		<div class="std-import-final-row"><span>${__("Warnings")}</span><strong>${(summary.warnings || []).join(", ") || "—"}</strong></div>
	</div>
	<div class="std-import-final-blockers" data-testid="std-import-final-blockers">
		${
			blockers.length
				? blockers
						.map(
							(b) =>
								`<div class="std-import-final-blocker"><p><strong>${__("Reason")}:</strong> ${b.reason || ""}</p><p><strong>${__(
									"Fix",
								)}:</strong> ${b.fix_path || ""}</p></div>`,
						)
						.join("")
				: `<p>${__("No finalization blockers detected.")}</p>`
		}
	</div>
	<div class="std-import-final-confirmation" data-testid="std-import-final-confirmation">
		${
			s.actions?.can_activate
				? `<p>${s.confirmationText.activate || ""}</p>`
				: `<p>${s.confirmationText.submit || ""}</p>`
		}
		${
			s.actions?.can_activate
				? `<p>${__("This will activate the STD version for future tenders. Active versions are immutable.")}</p>`
				: ""
		}
	</div>
	<div class="std-import-step6-actions">
		<button type="button" class="btn btn-default btn-sm" data-testid="std-import-submit-review" ${
			s.actions?.can_submit_review && !s.submitting ? "" : "disabled"
		}>${s.submitting ? __("Submitting...") : __("Submit for Review")}</button>
		<button type="button" class="btn btn-primary btn-sm" data-testid="std-import-activate" ${
			s.actions?.can_activate && !s.activating ? "" : "disabled"
		}>${s.activating ? __("Activating...") : __("Activate")}</button>
	</div>
	${s.status ? `<p class="std-import-step6-status">${s.status}</p>` : ""}
</div>`;
		};
		const loadSources = () => {
			if (state.packageSources.length) return Promise.resolve();
			if (!stdApi?.getPackageSources) return Promise.resolve();
			return stdApi.getPackageSources().then((resp) => {
				state.packageSources = Array.isArray(resp?.sources) ? resp.sources : [];
			});
		};
		const detectStep1Metadata = () => {
			const s = state.step1;
			if (!s.package_source || !s.package_entry) return Promise.resolve();
			if (!stdApi?.selectPackage) return Promise.resolve();
			return stdApi
				.selectPackage({
					import_code: state.importCode,
					package_source: s.package_source,
					package_entry: s.package_entry,
				})
				.then((resp) => {
					if (resp?.ok && resp?.metadata) {
						state.step1.error = "";
						if (resp.import_code) {
							state.importCode = String(resp.import_code);
						}
						hydrateMetadata(resp.metadata);
						const selectedEntry = getSelectedEntry();
						if (!state.step2.source_title) {
							state.step2.source_title = String(selectedEntry?.label || state.step1.package_entry || "");
						}
						if (!state.step2.source_revision) {
							state.step2.source_revision = String(resp.metadata.package_version || "");
						}
						if (!state.step2.source_authority) {
							if (state.step1.package_source === "BUILTIN_SEED_PACKAGE") {
								state.step2.source_authority = "PPRA";
							} else if (state.step1.package_source === "CONNECTED_REGISTRY") {
								state.step2.source_authority = "Connected Registry";
							} else {
								state.step2.source_authority = "Uploaded Source";
							}
						}
						if (!state.step2.review_status) {
							state.step2.review_status = "Draft";
						}
						applyStep2Validity();
					} else {
						state.step1.error = safeErr(
							resp?.message,
							__("Unable to detect package metadata."),
						);
						hydrateMetadata(null);
					}
				});
		};
		const isStepComplete = (idx) => Boolean(state.stepValidity[idx]);
		const saveStep2Evidence = () => {
			applyStep2Validity();
			if (!state.stepValidity[1] || !stdApi?.saveSourceEvidence) {
				return Promise.resolve();
			}
			return stdApi
				.saveSourceEvidence({
					import_code: state.importCode,
					source_authority: state.step2.source_authority,
					source_title: state.step2.source_title,
					source_revision: state.step2.source_revision,
					source_file: state.step2.source_file,
					source_hash: state.step2.source_hash,
					prepared_by: state.step2.prepared_by,
					review_status: state.step2.review_status,
					notes: state.step2.notes,
				})
				.then((resp) => {
					if (resp?.ok) {
						state.step2.error = "";
					} else {
						state.step2.error = safeErr(resp?.message, __("Unable to save source evidence."));
						state.stepValidity[1] = false;
					}
				});
		};
		const loadStep3DetectedStructure = () => {
			if (state.step3.loading || state.step3.summary || !stdApi?.getDetectedStructure) {
				return Promise.resolve();
			}
			state.step3.loading = true;
			applyStep3Validity();
			return stdApi
				.getDetectedStructure(state.importCode)
				.then((resp) => {
					if (resp?.ok && resp?.summary) {
						state.step3.error = "";
						state.step3.summary = resp.summary;
						state.step3.technical_details = resp.technical_details || {};
					} else {
						state.step3.error = safeErr(
							resp?.message,
							__("Unable to load detected structure summary."),
						);
						state.step3.summary = null;
						state.step3.technical_details = null;
					}
				})
				.finally(() => {
					state.step3.loading = false;
					applyStep3Validity();
				});
		};
		const loadStep4Validation = () => {
			if (state.step4.loading || state.step4.validation || !stdApi?.validateImport || !stdApi?.getImportValidation) {
				return Promise.resolve();
			}
			state.step4.loading = true;
			applyStep4Validity();
			return stdApi
				.validateImport(state.importCode)
				.then((resp) => {
					if (!resp?.ok) {
						throw new Error(resp?.message || __("Unable to run validation."));
					}
					return stdApi.getImportValidation(state.importCode);
				})
				.then((resp) => {
					if (resp?.ok && resp?.validation) {
						state.step4.error = "";
						state.step4.validation = resp.validation;
					} else {
						state.step4.error = safeErr(
							resp?.message,
							__("Unable to load validation summary."),
						);
						state.step4.validation = null;
					}
				})
				.catch((err) => {
					state.step4.error = safeErr(err?.message, userMsg.MSG_VALIDATION_FAILED);
					state.step4.validation = null;
				})
				.finally(() => {
					state.step4.loading = false;
					applyStep4Validity();
				});
		};
		const loadStep5BundlePreview = () => {
			if (
				state.step5.loading ||
				(state.step5.outline || []).length ||
				!stdApi?.generateImportBundlePreview ||
				!stdApi?.getImportBundlePreview ||
				!stdApi?.getImportPlaceholderList
			) {
				return Promise.resolve();
			}
			state.step5.loading = true;
			applyStep5Validity();
			return stdApi
				.generateImportBundlePreview(state.importCode)
				.then((resp) => {
					if (!resp?.ok) {
						throw new Error(resp?.message || __("Unable to generate bundle preview."));
					}
					return Promise.all([
						stdApi.getImportBundlePreview(state.importCode),
						stdApi.getImportPlaceholderList(state.importCode),
					]);
				})
				.then(([bundleResp, placeholdersResp]) => {
					if (!bundleResp?.ok || !placeholdersResp?.ok) {
						throw new Error(
							bundleResp?.message ||
								placeholdersResp?.message ||
								__("Unable to load bundle preview."),
						);
					}
					state.step5.error = "";
					state.step5.outline = bundleResp.outline || [];
					state.step5.sections = bundleResp.sections || [];
					state.step5.actions = bundleResp.actions || {};
					state.step5.message = String(bundleResp.message || "");
					state.step5.placeholders = placeholdersResp.placeholders || [];
				})
				.catch((err) => {
					state.step5.error = safeErr(
						err?.message,
						__("Bundle preview is currently unavailable. Please try again."),
					);
					state.step5.outline = [];
					state.step5.sections = [];
					state.step5.actions = {};
					state.step5.message = "";
					state.step5.placeholders = [];
				})
				.finally(() => {
					state.step5.loading = false;
					applyStep5Validity();
				});
		};
		const loadStep6FinalReview = () => {
			if (state.step6.loading || state.step6.summary || !stdApi?.getFinalReview) {
				return Promise.resolve();
			}
			state.step6.loading = true;
			applyStep6Validity();
			return stdApi
				.getFinalReview(state.importCode)
				.then((resp) => {
					if (!resp?.ok) {
						throw new Error(resp?.message || __("Unable to load final review summary."));
					}
					state.step6.error = "";
					state.step6.summary = resp.summary || {};
					state.step6.blockers = resp.blockers || [];
					state.step6.actions = resp.actions || {};
					state.step6.confirmationText = resp.confirmation_text || {};
					state.step6.status = String(resp.status || "");
				})
				.catch((err) => {
					state.step6.error = safeErr(err?.message, __("Unable to load final review summary."));
					state.step6.summary = null;
					state.step6.blockers = [];
					state.step6.actions = {};
					state.step6.confirmationText = {};
					state.step6.status = "";
				})
				.finally(() => {
					state.step6.loading = false;
					applyStep6Validity();
				});
		};

		const render = () => {
			wrap.innerHTML = `
<div class="std-package-import-inner">
	<header class="std-package-import-header">
		<h3>${__("Import Official STD Package")}</h3>
		<p>${__("Use the structured package workflow. Raw document uploads are evidence-only and not runtime package imports.")}</p>
	</header>
	<div class="std-package-import-stepper" data-testid="std-package-import-stepper" role="group" aria-label="${__(
		"Import wizard steps",
	)}">
		${IMPORT_STEPS.map((label, idx) => {
			const stepState =
				idx === state.currentStep ? "is-active" : idx < state.currentStep ? "is-complete" : "is-pending";
			const locked = idx > state.highestUnlockedStep;
			return `<button type="button" class="std-package-import-step ${stepState}" data-step-index="${idx}" ${
				locked ? "disabled" : ""
			} title="${locked ? __("Complete prior steps first") : ""}">${label}</button>`;
		}).join("")}
	</div>
	<section class="std-package-import-step-body">
		${
			state.currentStep === 0
				? step1Body()
				: state.currentStep === 1
					? step2Body()
					: state.currentStep === 2
						? step3Body()
						: state.currentStep === 3
							? step4Body()
							: state.currentStep === 4
								? step5Body()
								: state.currentStep === 5
									? step6Body()
						: stepBodyForPlaceholder()
		}
	</section>
	<footer class="std-package-import-actions">
		<button type="button" class="btn btn-default btn-sm" data-testid="std-package-import-cancel">${__(
			"Cancel",
		)}</button>
		<button type="button" class="btn btn-default btn-sm" data-testid="std-package-import-back" ${
			state.currentStep === 0 ? "disabled" : ""
		}>${__("Back")}</button>
		<button type="button" class="btn btn-default btn-sm" data-testid="std-package-import-save-draft">${__(
			"Save Draft",
		)}</button>
		<button type="button" class="btn btn-primary btn-sm" data-testid="std-package-import-next" ${
			state.currentStep >= IMPORT_STEPS.length - 1 || !isStepComplete(state.currentStep) ? "disabled" : ""
		}>${__("Next")}</button>
	</footer>
</div>`;

			wrap.querySelectorAll("[data-step-index]").forEach((btn) => {
				btn.addEventListener("click", function () {
					const target = Number(btn.getAttribute("data-step-index"));
					if (Number.isNaN(target)) return;
					if (target > state.highestUnlockedStep) return;
					state.currentStep = target;
					render();
				});
			});
			if (state.currentStep === 0) {
				const sourceInput = wrap.querySelector('[data-testid="std-import-package-source-select"]');
				const fileInput = wrap.querySelector('[data-testid="std-import-package-file-picker"]');
				sourceInput?.addEventListener("change", function () {
					state.step1.package_source = String(sourceInput.value || "");
					state.step1.package_entry = "";
					state.step1.error = "";
					hydrateMetadata(null);
					render();
				});
				fileInput?.addEventListener("change", function () {
					state.step1.package_entry = String(fileInput.value || "");
					state.step1.error = "";
					hydrateMetadata(null);
					detectStep1Metadata().finally(render);
				});
			}
			if (state.currentStep === 1) {
				const fields = [
					["source_authority", '[data-testid="std-import-source-authority"]'],
					["source_title", '[data-testid="std-import-source-title"]'],
					["source_revision", '[data-testid="std-import-source-revision"]'],
					["source_file", '[data-testid="std-import-source-file"]'],
					["source_hash", '[data-testid="std-import-source-hash"]'],
					["prepared_by", '[data-testid="std-import-source-prepared-by"]'],
					["review_status", '[data-testid="std-import-source-review-status"]'],
					["notes", '[data-testid="std-import-source-notes"]'],
				];
				fields.forEach(([key, selector]) => {
					const input = wrap.querySelector(selector);
					const sync = function () {
						state.step2[key] = String(input.value || "");
						state.step2.error = "";
						applyStep2Validity();
						saveStep2Evidence().finally(render);
					};
					input?.addEventListener("change", sync);
					if (input?.tagName !== "SELECT") {
						input?.addEventListener("input", sync);
					}
				});
				applyStep2Validity();
			}
			if (state.currentStep === 2) {
				wrap
					.querySelector('[data-testid="std-import-expand-technical-details"]')
					?.addEventListener("click", function () {
						state.step3.detailsExpanded = !state.step3.detailsExpanded;
						render();
					});
				if (!state.step3.summary && !state.step3.loading) {
					loadStep3DetectedStructure().finally(render);
				}
			}
			if (state.currentStep === 3) {
				if (!state.step4.validation && !state.step4.loading) {
					loadStep4Validation().finally(render);
				}
			}
			if (state.currentStep === 4) {
				if (!(state.step5.outline || []).length && !state.step5.loading) {
					loadStep5BundlePreview().finally(render);
				}
			}
			if (state.currentStep === 5) {
				if (!state.step6.summary && !state.step6.loading) {
					loadStep6FinalReview().finally(render);
				}
				wrap.querySelector('[data-testid="std-import-submit-review"]')?.addEventListener("click", function () {
					if (!stdApi?.submitImportForReview || !state.step6.actions?.can_submit_review) return;
					state.step6.submitting = true;
					render();
					stdApi.submitImportForReview(state.importCode)
						.then((resp) => {
							if (!resp?.ok) {
								throw new Error(resp?.message || __("Unable to submit for review."));
							}
							state.step6.error = "";
							state.step6.status = String(resp.status || __("Submitted for Review"));
							state.step6.finalized = true;
							state.step6.actions.can_submit_review = false;
						})
						.catch((err) => {
							state.step6.error = safeErr(err?.message, __("Unable to submit for review."));
						})
						.finally(() => {
							state.step6.submitting = false;
							applyStep6Validity();
							render();
						});
				});
				wrap.querySelector('[data-testid="std-import-activate"]')?.addEventListener("click", function () {
					if (!stdApi?.activateImport || !state.step6.actions?.can_activate) return;
					state.step6.activating = true;
					render();
					stdApi.activateImport(state.importCode)
						.then((resp) => {
							if (!resp?.ok) {
								throw new Error(resp?.message || __("Unable to activate this import."));
							}
							state.step6.error = "";
							state.step6.status = String(resp.status || __("Activated"));
							state.step6.finalized = true;
							state.step6.actions.can_activate = false;
						})
						.catch((err) => {
							state.step6.error = safeErr(err?.message, __("Unable to activate this import."));
						})
						.finally(() => {
							state.step6.activating = false;
							applyStep6Validity();
							render();
						});
				});
			}
			wrap.querySelector('[data-testid="std-package-import-cancel"]')?.addEventListener("click", function () {
				frappe.set_route("std-engine", "library");
			});
			wrap.querySelector('[data-testid="std-package-import-back"]')?.addEventListener("click", function () {
				state.currentStep = Math.max(0, state.currentStep - 1);
				render();
			});
			wrap.querySelector('[data-testid="std-package-import-save-draft"]')?.addEventListener("click", function () {
				frappe.show_alert({ message: __("Draft saved for import wizard shell."), indicator: "blue" });
			});
			wrap.querySelector('[data-testid="std-package-import-next"]')?.addEventListener("click", function () {
				if (!isStepComplete(state.currentStep)) return;
				state.currentStep = Math.min(IMPORT_STEPS.length - 1, state.currentStep + 1);
				state.highestUnlockedStep = Math.max(state.highestUnlockedStep, state.currentStep);
				render();
			});
		};
		loadSources().finally(render);
		return wrap;
	};
})();
