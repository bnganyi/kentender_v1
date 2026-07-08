/* global frappe */
// STD-CFG-0200 — STD Library import wizard (design-faithful six-step shell).
frappe.provide("kentender_procurement.std_library_import_page");

(function () {
	"use strict";

	const shared = kentender_procurement.std_config_shared;
	const page = kentender_procurement.std_library_import_page;
	const WIZARD_API = "kentender_procurement.tender_management.api.std_library_import_wizard";

	const IMPORT_STEPS = Object.freeze([
		{ key: "select", label: __("1. Select Package") },
		{ key: "evidence", label: __("2. Confirm Source Evidence") },
		{ key: "structure", label: __("3. Review Detected Structure") },
		{ key: "validate", label: __("4. Validate Structured Model") },
		{ key: "preview", label: __("5. Preview Tender Bundle") },
		{ key: "review", label: __("6. Submit for Review / Activate") },
	]);

	function _legacyApi() {
		return kentender_procurement.std_library_api || null;
	}

	function _callImport(method, args) {
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: WIZARD_API + "." + method,
				args: args || {},
				callback: function (r) {
					resolve((r && r.message) || {});
				},
				error: function (err) {
					reject(err);
				},
			});
		});
	}

	function _stepsHtml(currentStep) {
		return IMPORT_STEPS.map(function (step, idx) {
			const active = idx === currentStep ? " is-active" : "";
			return `<li class="kt-std-lib-import-step${active}" data-step="${idx}">${step.label}</li>`;
		}).join("");
	}

	function _html(currentStep) {
		return `
<div class="kt-std-lib-root kt-std-lib-import" data-testid="kt-std-lib-import-root">
	<div class="kt-std-lib-header">
		<div>
			<p class="kt-std-lib-eyebrow">${__("KenTender Procurement System")}</p>
			<h1 class="kt-std-lib-title">${__("Import Official STD Package")}</h1>
			<p class="kt-std-lib-subtitle">${__(
				"Six-step wizard to import, validate, and submit an official STD package.",
			)}</p>
		</div>
		<div class="kt-std-lib-actions">
			<button type="button" class="kt-std-lib-btn" data-kt-std-import-back>${__("Back to library")}</button>
		</div>
	</div>
	<ol class="kt-std-lib-import-steps" data-testid="kt-std-lib-import-steps">${_stepsHtml(currentStep)}</ol>
	<div class="kt-std-lib-import-body" data-testid="kt-std-lib-import-body">
		<p class="kt-std-lib-kpi-label">${IMPORT_STEPS[currentStep].label}</p>
		<div data-kt-std-import-content></div>
		<p data-kt-std-import-status>${__("Ready.")}</p>
	</div>
	<div class="kt-std-lib-import-actions">
		<button type="button" class="kt-std-lib-btn" data-kt-std-import-prev ${currentStep === 0 ? "disabled" : ""}>${__(
			"Previous",
		)}</button>
		<button type="button" class="kt-std-lib-btn kt-std-lib-btn--primary" data-kt-std-import-next ${currentStep >= IMPORT_STEPS.length - 1 ? "disabled" : ""}>${__(
			"Next",
		)}</button>
	</div>
</div>`;
	}

	function _renderStepContent(root, state) {
		const content = root.querySelector("[data-kt-std-import-content]");
		const status = root.querySelector("[data-kt-std-import-status]");
		if (status) status.textContent = state.message || __("Ready.");
		if (!content) return;
		const step = state.currentStep;
		if (step === 0) {
			const packages = (state.packages || []).map(function (pkg) {
				return `<li>${shared._escapeHtml(pkg.label || pkg.code || pkg.name || "")}</li>`;
			}).join("");
			content.innerHTML = `<ul class="kt-std-cfg-checklist">${packages || `<li>${__("Loading package sources…")}</li>`}</ul>`;
			return;
		}
		if (step === 1) {
			content.innerHTML = `<div class="kt-std-cfg-form-grid"><div class="kt-std-cfg-field"><label>${__(
				"Source document",
			)}</label><input type="text" data-kt-std-evidence-doc value="${shared._escapeHtml(
				state.source_document || "",
			)}" /></div></div>`;
			return;
		}
		if (step === 2) {
			const sections = (state.structure && state.structure.sections) || [];
			content.innerHTML = `<ul class="kt-std-cfg-checklist">${sections
				.map(function (s) {
					return `<li>${shared._escapeHtml(s.label || s.name || s)}</li>`;
				})
				.join("") || `<li>${__("No structure detected yet.")}</li>`}</ul>`;
			return;
		}
		if (step === 3) {
			const findings = (state.validation && state.validation.findings) || [];
			content.innerHTML = `<pre class="kt-std-cfg-readonly">${shared._escapeHtml(
				JSON.stringify(findings.length ? findings : state.validation || {}, null, 2),
			)}</pre>`;
			return;
		}
		if (step === 4) {
			const outline = (state.preview && state.preview.outline) || [];
			content.innerHTML = `<ul class="kt-std-cfg-checklist">${outline
				.map(function (line) {
					return `<li>${shared._escapeHtml(typeof line === "string" ? line : line.section || "")}</li>`;
				})
				.join("") || `<li>${__("Bundle preview not generated yet.")}</li>`}</ul>`;
			return;
		}
		content.innerHTML = `<pre class="kt-std-cfg-readonly">${shared._escapeHtml(
			JSON.stringify(state.finalReview || {}, null, 2),
		)}</pre>`;
	}

	function _renderStep(root, state) {
		const steps = root.querySelector("[data-testid='kt-std-lib-import-steps']");
		if (steps) steps.innerHTML = _stepsHtml(state.currentStep);
		const prevBtn = root.querySelector("[data-kt-std-import-prev]");
		const nextBtn = root.querySelector("[data-kt-std-import-next]");
		if (prevBtn) prevBtn.disabled = state.currentStep === 0;
		if (nextBtn) nextBtn.disabled = state.currentStep >= IMPORT_STEPS.length - 1;
		_renderStepContent(root, state);
	}

	function _loadStepData(state) {
		const step = state.currentStep;
		if (step === 0) {
			return _callImport("get_std_library_package_sources").then(function (res) {
				state.packages = res.packages || res.items || [];
				state.message = __("Select an official package to import.");
			});
		}
		if (step === 1) {
			return Promise.resolve();
		}
		if (step === 2) {
			return _callImport("get_std_library_detected_structure", { import_code: state.importCode }).then(function (res) {
				state.structure = res.structure || res;
				state.message = __("Review detected STD structure.");
			});
		}
		if (step === 3) {
			return _callImport("run_std_library_import_validation", { import_code: state.importCode }).then(function (res) {
				state.validation = res;
				state.message = res.message || __("Validation complete.");
			});
		}
		if (step === 4) {
			return _callImport("generate_std_library_bundle_preview", { import_code: state.importCode }).then(function (res) {
				state.preview = res.preview || res;
				state.message = res.message || __("Bundle preview generated.");
			});
		}
		if (step === 5) {
			return _callImport("get_std_library_import_final_review", { import_code: state.importCode }).then(function (res) {
				state.finalReview = res.review || res;
				state.message = __("Review import summary before submission.");
			});
		}
		return Promise.resolve();
	}

	function _runStepAction(state) {
		const legacy = _legacyApi();
		const step = state.currentStep;
		if (step === 0 && legacy && legacy.createPackageImportDraft) {
			return legacy.createPackageImportDraft().then(function (res) {
				state.importCode = res.import_code || state.importCode;
				state.message = __("Draft created: {0}", [state.importCode]);
			});
		}
		if (step === 1) {
			const docInput = document.querySelector("[data-kt-std-evidence-doc]");
			const sourceDoc = docInput ? docInput.value : state.source_document || "";
			return _callImport("save_std_library_source_evidence", {
				import_code: state.importCode,
				source_document: sourceDoc,
			}).then(function (res) {
				state.source_document = sourceDoc;
				state.message = res.message || __("Source evidence saved.");
			});
		}
		return _loadStepData(state);
	}

	function _bind(root, state) {
		root.addEventListener("click", function (event) {
			if (event.target.closest("[data-kt-std-import-back]")) {
				frappe.set_route("std-library");
				return;
			}
			if (event.target.closest("[data-kt-std-import-prev]")) {
				state.currentStep = Math.max(0, state.currentStep - 1);
				_loadStepData(state)
					.then(function () {
						_renderStep(root, state);
					})
					.catch(function () {
						_renderStep(root, state);
					});
				return;
			}
			if (event.target.closest("[data-kt-std-import-next]")) {
				_runStepAction(state)
					.then(function () {
						state.currentStep = Math.min(IMPORT_STEPS.length - 1, state.currentStep + 1);
						return _loadStepData(state);
					})
					.then(function () {
						_renderStep(root, state);
					})
					.catch(function (err) {
						state.message = (err && err.message) || String(err);
						_renderStep(root, state);
					});
			}
		});
	}

	page.mount = function mount(wrapper) {
		shared._ensureFonts();
		if (!wrapper) return;
		if (wrapper.querySelector("[data-testid='kt-std-lib-import-root']")) return;
		const state = {
			currentStep: 0,
			importCode: "STD-IMPORT-DRAFT",
			message: "",
			packages: [],
		};
		wrapper.innerHTML = _html(state.currentStep);
		const root = wrapper.querySelector("[data-testid='kt-std-lib-import-root']");
		_bind(root, state);
		_loadStepData(state)
			.then(function () {
				_renderStep(root, state);
			})
			.catch(function () {
				_renderStep(root, state);
			});
	};
})();
