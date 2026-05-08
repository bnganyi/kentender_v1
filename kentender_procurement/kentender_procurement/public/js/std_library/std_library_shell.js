// STD-LIB-0100–0150 — Official STD Library shell (orchestrator). STD-LIB-0500/0510: load after
// adapters + std_library_api.js + user_messages + wizard shell + detail_renderers (see hooks page_js order).
frappe.provide("kentender_procurement.std_library_shell");

(function () {
	const tabR = kentender_procurement.std_library_detail_renderers;
	const stdApi = kentender_procurement.std_library_api;
	const userMsg = kentender_procurement.std_library_user_messages;
	const TITLE = __("Official STD Library");
	const SUBTITLE = __(
		"Manage official standard tender documents available for tender preparation.",
	);
	const GUIDANCE_TEXT = __(
		"Official STDs are imported as structured packages. Source files are retained as evidence. Active versions are immutable.",
	);
	const DETAIL_EMPTY = __("Select an STD to view details (STD-LIB-0150).");
	const DEFAULT_UNAVAILABLE = __("Unavailable: this action is temporarily not available.");
	const SEARCH_PLACEHOLDER = __(
		"Search by STD title, revision, authority, category, method, or source document",
	);

	const ACTION_CODES = Object.freeze({
		importPackage: "IMPORT_OFFICIAL_STD_PACKAGE",
		registerSource: "REGISTER_SOURCE_DOCUMENT",
		validateLibrary: "VALIDATE_LIBRARY",
	});

	const BUTTON_CONFIG = Object.freeze({
		importPackage: {
			testid: "std-library-import-package-button",
			label: __("Import Official STD Package"),
			handler: function () {
				frappe.set_route("std-engine", "library", "import");
			},
		},
		registerSource: {
			testid: "std-library-register-source-button",
			label: __("Register Source Document"),
			handler: function () {
				frappe.show_alert({
					message: __("Register Source Document panel will open here (STD-LIB-0400)."),
					indicator: "blue",
				});
			},
		},
		validateLibrary: {
			testid: "std-library-validate-library-button",
			label: __("Validate Library"),
			handler: function () {
				frappe.show_alert({
					message: __("Validation summary will open here (STD-LIB-0410)."),
					indicator: "blue",
				});
			},
		},
	});

	const SUMMARY_CARDS = Object.freeze([
		{
			selector: "std-library-card-active",
			queue: "active",
			countKey: "active_count",
			label: __("Active STDs"),
			explanation: __("Available for tenders."),
		},
		{
			selector: "std-library-card-needs-attention",
			queue: "needs_attention",
			countKey: "needs_attention_count",
			label: __("Needs Attention"),
			explanation: __("Imported or validated items needing follow-up."),
		},
		{
			selector: "std-library-card-ready-review",
			queue: "ready_review",
			countKey: "ready_for_review_count",
			label: __("Ready for Review"),
			explanation: __("Validated versions awaiting review or activation."),
		},
		{
			selector: "std-library-card-superseded",
			queue: "superseded",
			countKey: "superseded_count",
			label: __("Superseded"),
			explanation: __("Historical versions replaced by newer revisions."),
		},
		{
			selector: "std-library-card-package-imports",
			queue: "package_imports",
			countKey: "package_import_count",
			label: __("Package Imports"),
			explanation: __("Recent package import activity."),
		},
		{
			selector: "std-library-card-bundle-issues",
			queue: "bundle_issues",
			countKey: "bundle_issue_count",
			label: __("Bundle Preview Issues"),
			explanation: __("Bundle previews requiring correction."),
		},
	]);

	const summaryState = {
		counts: {
			active_count: 0,
			needs_attention_count: 0,
			ready_for_review_count: 0,
			superseded_count: 0,
			package_import_count: 0,
			bundle_issue_count: 0,
		},
		activeQueue: "active",
	};
	const filterState = {
		search: "",
		procurement_category: "",
		procurement_method: "",
		status: [],
		source_authority: "",
		validation_status: [],
		supersession_status: [],
		used_by_tenders: "Any",
		bundle_preview_status: [],
		revision_from: "",
		revision_to: "",
	};
	let templatesResponse = { total_count: 0, rows: [], items: [] };
	let selectedVersionCode = "";
	let selectedDetail = null;
	let activeDetailTab = "summary";
	/** @type {{ section: string }} shared with tab renderers for bundle outline */
	const bundleSectionState = { section: "" };
	const registerSourceState = {
		visible: false,
		saving: false,
		error: "",
		success: "",
		form: {
			source_document_code: "",
			source_title: "",
			source_authority: "",
			revision_label: "",
			source_file: "",
			source_hash: "",
			notes: "",
		},
	};
	const libraryValidationState = {
		visible: false,
		loading: false,
		running: false,
		error: "",
		message: "",
		rows: [],
	};

	/** STD-LIB-0520 — conceptual page state + list load error text */
	const libraryPageState = {
		templatesLoadError: "",
	};

	const DETAIL_TAB_INTERNAL = new Set([
		"summary",
		"validation",
		"bundle-preview",
		"usage",
		"supersession",
		"advanced",
		"audit",
	]);

	function normalizeTabFromUrl(raw) {
		const s = String(raw || "")
			.trim()
			.toLowerCase();
		if (!s) return "summary";
		if (s === "bundle" || s === "bundle_preview") return "bundle-preview";
		if (DETAIL_TAB_INTERNAL.has(s)) return s;
		return "summary";
	}

	function tabToUrlParam(internalTab) {
		return internalTab === "bundle-preview" ? "bundle" : internalTab;
	}

	const FILTER_CONFIG = Object.freeze([
		{
			key: "procurement_category",
			label: __("Procurement Category"),
			type: "select",
			options: ["", "Works", "Goods", "Consultancy", "Non-Consultancy"],
		},
		{
			key: "procurement_method",
			label: __("Procurement Method"),
			type: "select",
			options: ["", "Open Tender", "Restricted Tender", "RFQ", "Direct Procurement"],
		},
		{
			key: "status",
			label: __("Status"),
			type: "multi",
			options: [
				"Imported Draft",
				"Needs Attention",
				"Ready for Review",
				"Under Review",
				"Active",
				"Superseded",
				"Retired",
			],
		},
		{
			key: "source_authority",
			label: __("Source Authority"),
			type: "select",
			options: ["", "PPRA", "MOPW", "KenTender"],
		},
		{
			key: "validation_status",
			label: __("Validation Status"),
			type: "multi",
			options: ["Not Run", "Passed", "Needs Attention", "Blocked"],
		},
		{
			key: "supersession_status",
			label: __("Supersession Status"),
			type: "multi",
			options: ["Current", "Superseded"],
		},
		{
			key: "used_by_tenders",
			label: __("Used by Tenders"),
			type: "select",
			options: ["Any", "Used", "Unused"],
		},
		{
			key: "bundle_preview_status",
			label: __("Bundle Preview Status"),
			type: "multi",
			options: ["Available", "Not Generated", "Failed", "Needs Tender Values"],
		},
	]);

	function set_button_enabled(button, enabled, reason) {
		if (!button) return;
		const testid = button.getAttribute("data-testid") || "std-library-generic-action";
		const descId = `${testid}-sr-reason`;
		let span = document.getElementById(descId);
		button.disabled = !enabled;
		button.setAttribute("aria-disabled", enabled ? "false" : "true");
		if (enabled) {
			button.removeAttribute("title");
			button.removeAttribute("aria-describedby");
			if (span) {
				span.remove();
			}
			return;
		}
		const msg = reason || DEFAULT_UNAVAILABLE;
		if (!span) {
			span = document.createElement("span");
			span.id = descId;
			span.className = "std-library-sr-only";
			button.insertAdjacentElement("afterend", span);
		}
		span.textContent = msg;
		button.setAttribute("aria-describedby", descId);
		button.setAttribute("title", msg);
	}

	function closeLibraryActionSurfaces(wrap) {
		registerSourceState.visible = false;
		libraryValidationState.visible = false;
		registerSourceState.error = "";
		registerSourceState.success = "";
		libraryValidationState.error = "";
		renderRegisterSourcePanel(wrap);
		renderLibraryValidationPanel(wrap);
	}

	function syncLibraryActionModal(wrap) {
		const modal = wrap.querySelector('[data-testid="std-library-action-modal"]');
		const titleEl = wrap.querySelector('[data-testid="std-library-action-modal-title"]');
		if (!modal) return;
		const open = registerSourceState.visible || libraryValidationState.visible;
		modal.classList.toggle("hidden", !open);
		modal.setAttribute("aria-hidden", open ? "false" : "true");
		if (titleEl) {
			if (registerSourceState.visible) {
				titleEl.textContent = __("Register source evidence");
			} else if (libraryValidationState.visible) {
				titleEl.textContent = __("Library-wide validation");
			} else {
				titleEl.textContent = "";
			}
		}
	}

	function ensureLibraryActionModalHandlers(wrap) {
		if (wrap.dataset.stdLibraryActionModalHandlers === "1") return;
		wrap.dataset.stdLibraryActionModalHandlers = "1";
		const backdrop = wrap.querySelector('[data-testid="std-library-action-modal-backdrop"]');
		const closeBtn = wrap.querySelector('[data-testid="std-library-action-modal-close"]');
		backdrop?.addEventListener("click", function () {
			closeLibraryActionSurfaces(wrap);
		});
		closeBtn?.addEventListener("click", function () {
			closeLibraryActionSurfaces(wrap);
		});
		document.addEventListener(
			"keydown",
			function stdLibraryActionModalEsc(ev) {
				if (ev.key !== "Escape") return;
				if (!wrap.isConnected) {
					document.removeEventListener("keydown", stdLibraryActionModalEsc);
					return;
				}
				if (!registerSourceState.visible && !libraryValidationState.visible) return;
				ev.preventDefault();
				closeLibraryActionSurfaces(wrap);
			},
			true,
		);
	}

	function apply_action_policy(wrap, availability) {
		Object.keys(BUTTON_CONFIG).forEach(function (key) {
			const cfg = BUTTON_CONFIG[key];
			const code = ACTION_CODES[key];
			const button = wrap.querySelector(`[data-testid="${cfg.testid}"]`);
			const state = availability[code] || {};
			const allowed = Boolean(state.allowed);
			const message = state.message || DEFAULT_UNAVAILABLE;

			set_button_enabled(button, allowed, message);
			button.onclick = null;
			if (allowed) {
				const handler =
					key === "registerSource"
						? function () {
								const nextOpen = !registerSourceState.visible;
								registerSourceState.visible = nextOpen;
								if (nextOpen) {
									libraryValidationState.visible = false;
								}
								registerSourceState.error = "";
								registerSourceState.success = "";
								renderRegisterSourcePanel(wrap);
								renderLibraryValidationPanel(wrap);
							}
						: key === "validateLibrary"
							? function () {
									const nextOpen = !libraryValidationState.visible;
									libraryValidationState.visible = nextOpen;
									if (nextOpen) {
										registerSourceState.visible = false;
									}
									libraryValidationState.error = "";
									renderLibraryValidationPanel(wrap);
									renderRegisterSourcePanel(wrap);
									if (
										libraryValidationState.visible &&
										!libraryValidationState.rows.length &&
										!libraryValidationState.loading
									) {
										loadLibraryValidationSummary(wrap);
									}
							  }
							: cfg.handler;
				button.addEventListener("click", handler);
			}
		});
	}

	function renderRegisterSourcePanel(wrap) {
		const panel = wrap.querySelector('[data-testid="std-register-source-panel"]');
		if (!panel) return;
		panel.classList.toggle("hidden", !registerSourceState.visible);
		panel.innerHTML = `
<div class="std-register-source-panel-inner">
	<p class="std-library-modal-scope-hint" data-testid="std-register-source-scope-hint">${__(
		"Library-wide evidence record. This does not attach to the STD selected in the list and does not activate a template.",
	)}</p>
	<p class="std-register-source-warning" data-testid="std-register-source-warning">${__(
		"Registering a source document does not make it available for tenders. To make an STD available, import or configure a structured STD package and activate it.",
	)}</p>
	<div class="std-register-source-grid">
		<label class="std-register-source-field">
			<span>${__("Source Document Code")}</span>
			<input class="form-control input-sm" data-testid="std-register-source-code" value="${registerSourceState.form.source_document_code}" />
		</label>
		<label class="std-register-source-field">
			<span>${__("Source Title")}</span>
			<input class="form-control input-sm" data-testid="std-register-source-title" value="${registerSourceState.form.source_title}" />
		</label>
		<label class="std-register-source-field">
			<span>${__("Source Authority")}</span>
			<input class="form-control input-sm" data-testid="std-register-source-authority" value="${registerSourceState.form.source_authority}" />
		</label>
		<label class="std-register-source-field">
			<span>${__("Revision Label")}</span>
			<input class="form-control input-sm" data-testid="std-register-source-revision" value="${registerSourceState.form.revision_label}" />
		</label>
		<label class="std-register-source-field">
			<span>${__("Source File")}</span>
			<input class="form-control input-sm" value="${registerSourceState.form.source_file}" />
		</label>
		<label class="std-register-source-field">
			<span>${__("Source Hash")}</span>
			<input class="form-control input-sm" value="${registerSourceState.form.source_hash}" />
		</label>
		<label class="std-register-source-field std-register-source-field-wide">
			<span>${__("Notes")}</span>
			<textarea class="form-control input-sm">${registerSourceState.form.notes}</textarea>
		</label>
	</div>
	${registerSourceState.error ? `<p class="std-import-step-error">${registerSourceState.error}</p>` : ""}
	${registerSourceState.success ? `<p class="std-register-source-success">${registerSourceState.success}</p>` : ""}
	<div class="std-register-source-actions">
		<button type="button" class="btn btn-default btn-sm" data-testid="std-register-source-cancel">${__(
			"Cancel",
		)}</button>
		<button type="button" class="btn btn-primary btn-sm" data-testid="std-register-source-save" ${
			registerSourceState.saving ? "disabled" : ""
		}>${registerSourceState.saving ? __("Saving...") : __("Save Source Document")}</button>
	</div>
</div>`;

		const mapInputs = [
			["source_document_code", '[data-testid="std-register-source-code"]'],
			["source_title", '[data-testid="std-register-source-title"]'],
			["source_authority", '[data-testid="std-register-source-authority"]'],
			["revision_label", '[data-testid="std-register-source-revision"]'],
		];
		mapInputs.forEach(([key, selector]) => {
			const input = panel.querySelector(selector);
			input?.addEventListener("input", function () {
				registerSourceState.form[key] = String(input.value || "");
				registerSourceState.error = "";
				registerSourceState.success = "";
			});
		});
		const extraInputs = panel.querySelectorAll(".std-register-source-field .form-control");
		if (extraInputs.length >= 7) {
			extraInputs[4].addEventListener("input", function () {
				registerSourceState.form.source_file = String(extraInputs[4].value || "");
			});
			extraInputs[5].addEventListener("input", function () {
				registerSourceState.form.source_hash = String(extraInputs[5].value || "");
			});
			extraInputs[6].addEventListener("input", function () {
				registerSourceState.form.notes = String(extraInputs[6].value || "");
			});
		}
		panel.querySelector('[data-testid="std-register-source-cancel"]')?.addEventListener("click", function () {
			closeLibraryActionSurfaces(wrap);
		});
		panel.querySelector('[data-testid="std-register-source-save"]')?.addEventListener("click", function () {
			if (!stdApi?.registerSourceDocument || registerSourceState.saving) return;
			if (
				!registerSourceState.form.source_document_code ||
				!registerSourceState.form.source_title ||
				!registerSourceState.form.source_authority ||
				!registerSourceState.form.revision_label
			) {
				registerSourceState.error = __("Complete all required fields.");
				renderRegisterSourcePanel(wrap);
				return;
			}
			registerSourceState.saving = true;
			registerSourceState.error = "";
			registerSourceState.success = "";
			renderRegisterSourcePanel(wrap);
			stdApi
				.registerSourceDocument({ ...registerSourceState.form })
				.then((resp) => {
					if (!resp?.ok) {
						throw new Error(resp?.message || __("Unable to register source document."));
					}
					registerSourceState.success = String(
						resp?.message ||
							__(
								"Source document registered as evidence. This does not make an STD available for tenders.",
							),
					);
				})
				.catch((err) => {
					registerSourceState.error = userMsg.sanitizeUserFacingError(
						err?.message,
						__("Unable to register source document."),
					);
				})
				.finally(() => {
					registerSourceState.saving = false;
					renderRegisterSourcePanel(wrap);
				});
		});
		syncLibraryActionModal(wrap);
	}

	function loadLibraryValidationSummary(wrap) {
		if (!stdApi?.getLibraryValidationSummary || libraryValidationState.loading) return;
		libraryValidationState.loading = true;
		libraryValidationState.error = "";
		renderLibraryValidationPanel(wrap);
		stdApi
			.getLibraryValidationSummary()
			.then((resp) => {
				if (!resp?.ok) {
					throw new Error(resp?.message || __("Unable to load validation summary."));
				}
				libraryValidationState.rows = Array.isArray(resp.rows) ? resp.rows : [];
				libraryValidationState.message = String(resp.message || "");
			})
			.catch((err) => {
				libraryValidationState.rows = [];
				libraryValidationState.error = userMsg.sanitizeUserFacingError(
					err?.message,
					__("Unable to load validation summary."),
				);
			})
			.finally(() => {
				libraryValidationState.loading = false;
				renderLibraryValidationPanel(wrap);
			});
	}

	function renderLibraryValidationPanel(wrap) {
		const panel = wrap.querySelector('[data-testid="std-library-validation-summary-panel"]');
		if (!panel) return;
		panel.classList.toggle("hidden", !libraryValidationState.visible);
		panel.innerHTML = `
<div class="std-library-validation-summary-panel-inner">
	<div class="std-library-validation-summary-header">
		<p class="std-library-modal-scope-hint" data-testid="std-library-validation-scope-hint">${__(
			"Summary covers draft and active versions across the library. It is not limited to the row selected in the list.",
		)}</p>
		<button type="button" class="btn btn-default btn-sm" data-testid="std-library-run-validation" ${
			libraryValidationState.running ? "disabled" : ""
		}>${libraryValidationState.running ? __("Running...") : __("Run Validation")}</button>
	</div>
	${
		libraryValidationState.loading
			? `<p class="std-library-validation-summary-state">${__("Loading validation summary...")}</p>`
			: ""
	}
	${libraryValidationState.error ? `<p class="std-import-step-error">${libraryValidationState.error}</p>` : ""}
	${libraryValidationState.message ? `<p class="std-library-validation-summary-state">${libraryValidationState.message}</p>` : ""}
	<div class="std-library-validation-summary-table">
		<div class="std-library-validation-summary-head">
			<span>${__("Version")}</span>
			<span>${__("Status")}</span>
			<span>${__("Last Validated")}</span>
			<span>${__("Result")}</span>
			<span>${__("Blockers")}</span>
			<span>${__("Bundle Status")}</span>
		</div>
		${
			(libraryValidationState.rows || []).length
				? libraryValidationState.rows
						.map(
							(row) =>
								`<button type="button" class="std-library-validation-summary-row" data-testid="std-library-validation-summary-row" data-version-code="${row.version_code || ""}">
					<span>${row.version || ""}</span>
					<span>${row.status || ""}</span>
					<span>${row.last_validated || ""}</span>
					<span>${row.result || ""}</span>
					<span>${Number(row.blockers || 0)}</span>
					<span>${row.bundle_status || ""}</span>
				</button>`,
						)
						.join("")
				: `<p class="std-library-validation-summary-state">${__("No validation rows available.")}</p>`
		}
	</div>
</div>`;

		panel.querySelector('[data-testid="std-library-run-validation"]')?.addEventListener("click", function () {
			if (!stdApi?.validateLibrary || libraryValidationState.running) return;
			libraryValidationState.running = true;
			libraryValidationState.error = "";
			renderLibraryValidationPanel(wrap);
			stdApi
				.validateLibrary()
				.then((resp) => {
					if (!resp?.ok) {
						throw new Error(resp?.message || __("Unable to run library validation."));
					}
					libraryValidationState.rows = Array.isArray(resp.rows) ? resp.rows : [];
					libraryValidationState.message = String(resp.message || "");
				})
				.catch((err) => {
					libraryValidationState.error = userMsg.sanitizeUserFacingError(
						err?.message,
						userMsg.MSG_VALIDATION_FAILED,
					);
				})
				.finally(() => {
					libraryValidationState.running = false;
					renderLibraryValidationPanel(wrap);
				});
		});

		panel.querySelectorAll('[data-version-code]').forEach((rowBtn) => {
			rowBtn.addEventListener("click", function () {
				const versionCode = String(rowBtn.getAttribute("data-version-code") || "");
				const row = (libraryValidationState.rows || []).find(
					(x) => String(x.version_code || "") === versionCode,
				);
				const result = String(row?.result || "").toLowerCase();
				if (!(result === "blocked" || result === "needs attention")) return;
				const matched = (templatesResponse.items || []).find(
					(x) => String(x.version_code || "") === versionCode,
				);
				const item = matched || {
					version_code: versionCode,
					title: String(row?.version || versionCode),
					revision_label: "",
					status: String(row?.status || ""),
					source_authority: "",
					validation_status: String(row?.result || ""),
					bundle_preview_status: String(row?.bundle_status || ""),
				};
				selectedVersionCode = versionCode;
				selectedDetail = null;
				activeDetailTab = "validation";
				writeFiltersToUrl();
				renderLibraryCards(wrap);
				setSelectedDetail(wrap, item);
				if (matched) {
					fetchTemplateDetailForCard(wrap, item);
				}
			});
		});
		syncLibraryActionModal(wrap);
	}

	function readQueueFromUrl() {
		try {
			const q = new URL(window.location.href).searchParams.get("queue");
			const allowed = new Set(SUMMARY_CARDS.map((x) => x.queue));
			return allowed.has(q || "") ? q : "active";
		} catch (err) {
			return "active";
		}
	}

	function writeQueueToUrl(queue) {
		try {
			const url = new URL(window.location.href);
			url.searchParams.set("queue", queue);
			window.history.replaceState(window.history.state, "", url.toString());
		} catch (err) {
			// ignore URL update issues; queue state still updates in-memory
		}
	}

	function readFiltersFromUrl() {
		let params;
		try {
			params = new URL(window.location.href).searchParams;
		} catch (err) {
			return;
		}
		filterState.search = params.get("search") || "";
		filterState.procurement_category = params.get("procurement_category") || "";
		filterState.procurement_method = params.get("procurement_method") || "";
		filterState.status = (params.get("status") || "")
			.split(",")
			.map((x) => x.trim())
			.filter(Boolean);
		filterState.source_authority = params.get("source_authority") || "";
		filterState.validation_status = (params.get("validation_status") || "")
			.split(",")
			.map((x) => x.trim())
			.filter(Boolean);
		filterState.supersession_status = (params.get("supersession_status") || "")
			.split(",")
			.map((x) => x.trim())
			.filter(Boolean);
		filterState.used_by_tenders = params.get("used_by_tenders") || "Any";
		filterState.bundle_preview_status = (params.get("bundle_preview_status") || "")
			.split(",")
			.map((x) => x.trim())
			.filter(Boolean);
		filterState.revision_from = params.get("revision_from") || "";
		filterState.revision_to = params.get("revision_to") || "";
	}

	function readSelectionFromUrl() {
		let params;
		try {
			params = new URL(window.location.href).searchParams;
		} catch (err) {
			selectedVersionCode = "";
			activeDetailTab = "summary";
			return;
		}
		const code =
			String(params.get("std_code") || params.get("version_code") || "").trim() || "";
		selectedVersionCode = code;
		activeDetailTab = code ? normalizeTabFromUrl(params.get("tab")) : "summary";
	}

	function writeFiltersToUrl() {
		try {
			const url = new URL(window.location.href);
			const entries = [
				["search", filterState.search],
				["procurement_category", filterState.procurement_category],
				["procurement_method", filterState.procurement_method],
				["status", filterState.status.join(",")],
				["source_authority", filterState.source_authority],
				["validation_status", filterState.validation_status.join(",")],
				["supersession_status", filterState.supersession_status.join(",")],
				["used_by_tenders", filterState.used_by_tenders],
				["bundle_preview_status", filterState.bundle_preview_status.join(",")],
				["revision_from", filterState.revision_from],
				["revision_to", filterState.revision_to],
			];
			entries.forEach(([k, v]) => {
				if (!v || v === "Any") {
					url.searchParams.delete(k);
				} else {
					url.searchParams.set(k, v);
				}
			});
			url.searchParams.set("queue", summaryState.activeQueue);
			url.searchParams.delete("version_code");
			if (selectedVersionCode) {
				url.searchParams.set("std_code", selectedVersionCode);
				const tabParam = tabToUrlParam(activeDetailTab);
				if (tabParam && activeDetailTab !== "summary") {
					url.searchParams.set("tab", tabParam);
				} else {
					url.searchParams.delete("tab");
				}
			} else {
				url.searchParams.delete("std_code");
				url.searchParams.delete("tab");
			}
			window.history.replaceState(window.history.state, "", url.toString());
		} catch (err) {
			// no-op
		}
	}

	function queueCard(queue) {
		return SUMMARY_CARDS.find((c) => c.queue === queue) || SUMMARY_CARDS[0];
	}

	function updateListQueueContext(wrap) {
		const info = wrap.querySelector('[data-testid="std-library-list-queue-context"]');
		if (!info) return;
		const card = queueCard(summaryState.activeQueue);
		const filtered = Number(templatesResponse.total_count || 0);
		info.textContent = __(`${card.label}: ${filtered} item(s).`);
	}

	function selectorToken(value) {
		return String(value || "")
			.toLowerCase()
			.replace(/[^a-z0-9_-]+/g, "-")
			.replace(/^-+|-+$/g, "");
	}

	function fetchTemplateDetailForCard(wrap, item) {
		if (!selectedVersionCode || !item) return Promise.resolve();
		selectedDetail = null;
		setSelectedDetail(wrap, item);
		return stdApi
			.getStdLibraryTemplate(selectedVersionCode)
			.then((resp) => {
				selectedDetail = resp?.detail || null;
				setSelectedDetail(wrap, item);
			})
			.catch((err) => {
				const msg = userMsg.sanitizeUserFacingError(err?.message, userMsg.FALLBACK_DETAIL_LOAD);
				frappe.show_alert({ message: msg, indicator: "red" });
				selectedDetail = null;
				setSelectedDetail(wrap, item);
			});
	}

	function wireDetailTabKeyboard(detailInner, wrap, item) {
		const tablist = detailInner.querySelector(".std-library-detail-tabs[role='tablist']");
		if (!tablist) return;
		tablist.addEventListener("keydown", function (ev) {
			const keys = ["ArrowRight", "ArrowLeft", "ArrowDown", "ArrowUp", "Home", "End"];
			if (!keys.includes(ev.key)) return;
			const tabButtons = Array.from(tablist.querySelectorAll('[role="tab"]'));
			if (!tabButtons.length) return;
			const idx = tabButtons.findIndex((b) => b.getAttribute("data-detail-tab") === activeDetailTab);
			if (idx < 0) return;
			let next = idx;
			if (ev.key === "ArrowRight" || ev.key === "ArrowDown") {
				ev.preventDefault();
				next = (idx + 1) % tabButtons.length;
			} else if (ev.key === "ArrowLeft" || ev.key === "ArrowUp") {
				ev.preventDefault();
				next = (idx - 1 + tabButtons.length) % tabButtons.length;
			} else if (ev.key === "Home") {
				ev.preventDefault();
				next = 0;
			} else if (ev.key === "End") {
				ev.preventDefault();
				next = tabButtons.length - 1;
			}
			const nextTab = tabButtons[next]?.getAttribute("data-detail-tab");
			if (!nextTab) return;
			ev.preventDefault();
			activeDetailTab = nextTab;
			writeFiltersToUrl();
			setSelectedDetail(wrap, item);
			requestAnimationFrame(function () {
				const panel = wrap.querySelector('[data-testid="std-library-detail-panel"]');
				const activeBtn = panel?.querySelector(`[data-detail-tab="${nextTab}"][role="tab"]`);
				activeBtn?.focus();
			});
		});
	}

	function setSelectedDetail(wrap, item) {
		const detailRegion = wrap.querySelector('[data-testid="std-library-detail-panel"]');
		if (!detailRegion) return;
		detailRegion.innerHTML = "";
		const detailInner = document.createElement("div");
		detailInner.className = "std-library-detail-inner std-library-placeholder-pane";
		if (!item && !selectedDetail) {
			detailInner.textContent = DETAIL_EMPTY;
			detailRegion.appendChild(detailInner);
			return;
		}
		const d = selectedDetail || {};
		const tabs = [
			["summary", "std-library-tab-summary", __("Summary"), false],
			["validation", "std-library-tab-validation", __("Validation"), false],
			["bundle-preview", "std-library-tab-bundle-preview", __("Bundle Preview"), false],
			["usage", "std-library-tab-usage", __("Usage"), false],
			["supersession", "std-library-tab-supersession", __("Supersession"), false],
			["advanced", "std-library-tab-advanced", __("Advanced Technical View"), true],
			["audit", "std-library-tab-audit", __("Audit Trail"), false],
		];
		const activeTabMeta = tabs.find((row) => row[0] === activeDetailTab);
		const activeTestId = activeTabMeta ? activeTabMeta[1] : "std-library-tab-summary";
		const summaryHtml = tabR.renderSummaryTabContent(d);
		const tabContentHtml =
			activeDetailTab === "summary"
				? summaryHtml
				: activeDetailTab === "validation"
					? tabR.renderValidationTabContent(d)
					: activeDetailTab === "bundle-preview"
						? tabR.renderBundlePreviewTabContent(d, bundleSectionState)
						: activeDetailTab === "usage"
							? tabR.renderUsageTabContent(d)
							: activeDetailTab === "supersession"
								? tabR.renderSupersessionTabContent(d)
								: activeDetailTab === "advanced"
									? tabR.renderAdvancedTabContent(d)
									: activeDetailTab === "audit"
										? tabR.renderAuditTabContent(d)
										: `<div class="std-library-tab-placeholder">${__(
												"This tab content will be implemented in a follow-on ticket.",
											)}</div>`;
		const tabsHtml = tabs
			.map(([tabKey, testid, label, secondary]) => {
				const selected = activeDetailTab === tabKey;
				return `<button type="button" id="${testid}" role="tab" class="std-library-detail-tab${
					secondary ? " is-secondary" : ""
				}${selected ? " is-active" : ""}" aria-selected="${selected ? "true" : "false"}" aria-controls="std-library-detail-tabpanel" tabindex="${
					selected ? "0" : "-1"
				}" data-detail-tab="${tabKey}" data-testid="${testid}">${label}</button>`;
			})
			.join("");
		detailInner.innerHTML = `
<div class="std-library-detail-header" data-testid="std-library-detail-header">
	<h4 class="std-library-detail-title">${d.title || item?.title || ""}</h4>
	<div class="std-library-detail-meta"><strong>${__("Version code")}:</strong> ${d.version_code || item?.version_code || ""}</div>
	<div class="std-library-detail-meta"><strong>${__("Revision")}:</strong> ${d.revision_label || item?.revision_label || ""}</div>
	<div class="std-library-detail-meta"><strong>${__("Status")}:</strong> ${d.status || item?.status || ""}</div>
	<div class="std-library-detail-meta"><strong>${__("Authority")}:</strong> ${d.authority || item?.source_authority || ""}</div>
	<div class="std-library-detail-meta"><strong>${__("Validation")}:</strong> ${d.validation_status || item?.validation_status || ""}</div>
	<div class="std-library-detail-meta"><strong>${__("Bundle")}:</strong> ${d.bundle_preview_status || item?.bundle_preview_status || ""}</div>
</div>
<div class="std-library-detail-state-banner" data-testid="std-library-detail-state-banner">${d.state_banner || __("Review this STD version status before proceeding.")}</div>
<div class="std-library-detail-tabs" role="tablist" aria-label="${__("STD version detail tabs")}">${tabsHtml}</div>
<div class="std-library-detail-tab-content" role="tabpanel" id="std-library-detail-tabpanel" aria-labelledby="${activeTestId}">${tabContentHtml}</div>`;
		detailRegion.appendChild(detailInner);
		detailInner.querySelectorAll("[data-detail-tab]").forEach((btn) => {
			btn.addEventListener("click", function () {
				activeDetailTab = btn.getAttribute("data-detail-tab") || "summary";
				writeFiltersToUrl();
				setSelectedDetail(wrap, item);
			});
		});
		wireDetailTabKeyboard(detailInner, wrap, item);
		detailInner.querySelectorAll("[data-outline-target]").forEach((btn) => {
			btn.addEventListener("click", function () {
				bundleSectionState.section = btn.getAttribute("data-outline-target") || "";
				setSelectedDetail(wrap, item);
			});
		});
		detailInner.querySelectorAll(".std-advanced-mapping-blocker").forEach((btn) => {
			btn.addEventListener("click", function () {
				activeDetailTab = btn.getAttribute("data-blocker-target") || "validation";
				writeFiltersToUrl();
				setSelectedDetail(wrap, item);
			});
		});
	}

	function renderCardAction(wrap, item, actionCode, label, selectorKey) {
		const actionState = item.action_availability?.[actionCode] || {};
		const btn = document.createElement("button");
		btn.type = "button";
		btn.className = "btn btn-default btn-xs";
		if (selectorKey) {
			btn.setAttribute("data-testid", `${selectorKey}-${selectorToken(item.version_code)}`);
		}
		btn.textContent = label;
		set_button_enabled(btn, Boolean(actionState.allowed), actionState.message || DEFAULT_UNAVAILABLE);
		btn.addEventListener("click", function (event) {
			event.preventDefault();
			event.stopPropagation();
			if (actionCode === "view_details") {
				selectedVersionCode = String(item.version_code || "");
				selectedDetail = null;
				activeDetailTab = "summary";
				bundleSectionState.section = "";
				writeFiltersToUrl();
				renderLibraryCards(wrap);
				fetchTemplateDetailForCard(wrap, item);
				return;
			}
			frappe.show_alert({
				message: __(`${label} is queued for a future ticket.`),
				indicator: "blue",
			});
		});
		return btn;
	}

	function renderLibraryCards(wrap) {
		const root = wrap.querySelector('[data-testid="std-library-list-cards"]');
		if (!root) return;
		root.innerHTML = "";
		if (libraryPageState.templatesLoadError) {
			const errEl = document.createElement("div");
			errEl.className = "std-library-list-error std-library-placeholder-pane";
			errEl.setAttribute("data-testid", "std-library-list-load-error");
			errEl.setAttribute("role", "alert");
			errEl.setAttribute("aria-live", "polite");
			const msgP = document.createElement("p");
			msgP.textContent = libraryPageState.templatesLoadError;
			const retryBtn = document.createElement("button");
			retryBtn.type = "button";
			retryBtn.className = "btn btn-default btn-sm std-library-list-retry";
			retryBtn.setAttribute("data-testid", "std-library-list-retry");
			retryBtn.textContent = __("Retry");
			retryBtn.addEventListener("click", function () {
				libraryPageState.templatesLoadError = "";
				refreshTemplates(wrap);
			});
			errEl.appendChild(msgP);
			errEl.appendChild(retryBtn);
			root.appendChild(errEl);
			return;
		}
		const items = Array.isArray(templatesResponse.items) ? templatesResponse.items : [];
		if (!items.length) {
			const lines = userMsg.getLibraryListEmptyLines(summaryState.activeQueue);
			const empty = document.createElement("div");
			empty.className = "std-library-list-empty std-library-placeholder-pane";
			empty.setAttribute("data-testid", "std-library-list-empty");
			const titleEl = document.createElement("p");
			titleEl.className = "std-library-list-empty-title";
			titleEl.textContent = lines.title;
			const hintEl = document.createElement("p");
			hintEl.className = "std-library-list-empty-hint";
			hintEl.textContent = lines.hint;
			empty.appendChild(titleEl);
			empty.appendChild(hintEl);
			root.appendChild(empty);
			return;
		}

		items.forEach((item) => {
			const token = selectorToken(item.version_code);
			const card = document.createElement("article");
			card.className = "std-library-template-card";
			card.setAttribute("data-testid", `std-library-card-${token}`);
			card.setAttribute("role", "button");
			card.setAttribute("tabindex", "0");
			const ariaTitle = String(item.title || "").trim() || __("STD template");
			const ariaVer = String(item.version_code || "").trim();
			card.setAttribute(
				"aria-label",
				ariaVer
					? `${ariaTitle}. ${__("Version code")} ${ariaVer}.`
					: ariaTitle,
			);
			if (selectedVersionCode === String(item.version_code || "")) {
				card.classList.add("is-selected");
			}

			const methods = Array.isArray(item.supported_methods) ? item.supported_methods.join(", ") : "";
			card.innerHTML = `
<h4 class="std-library-template-title" data-testid="std-library-card-title-${token}">${item.title || ""}</h4>
<p class="std-library-template-revision">${__("Revision")}: ${item.revision_label || ""}</p>
<p class="std-library-template-status">${__("Status")}: ${item.status || ""}</p>
<p class="std-library-template-meta">${__("Category")}: ${item.procurement_category || ""}</p>
<p class="std-library-template-meta">${__("Methods")}: ${methods || __("Not set")}</p>
<p class="std-library-template-meta">${__("Source Authority")}: ${item.source_authority || ""}</p>
<p class="std-library-template-meta">${__("Validation")}: ${item.validation_status || ""} | ${__("Bundle")}: ${item.bundle_preview_status || ""} | ${__("Used by")}: ${Number(item.used_by_tender_count || 0)}</p>
<p class="std-library-template-meta">${__("Supersession")}: ${item.supersession_status || ""}</p>`;

			const actions = document.createElement("div");
			actions.className = "std-library-template-actions";
			actions.appendChild(
				renderCardAction(wrap, item, "view_details", __("View Details"), "std-library-card-view-details"),
			);
			actions.appendChild(
				renderCardAction(
					wrap,
					item,
					"preview_bundle",
					__("Preview Bundle"),
					"std-library-card-preview-bundle",
				),
			);
			actions.appendChild(
				renderCardAction(wrap, item, "view_usage", __("View Usage"), "std-library-card-view-usage"),
			);
			actions.appendChild(
				renderCardAction(
					wrap,
					item,
					"new_revision",
					__("New Revision"),
					"std-library-card-new-revision",
				),
			);
			card.appendChild(actions);

			card.addEventListener("click", function () {
				selectedVersionCode = String(item.version_code || "");
				selectedDetail = null;
				activeDetailTab = "summary";
				bundleSectionState.section = "";
				writeFiltersToUrl();
				renderLibraryCards(wrap);
				fetchTemplateDetailForCard(wrap, item);
			});
			card.addEventListener("keydown", function (event) {
				if (event.key === "Enter" || event.key === " ") {
					event.preventDefault();
					selectedVersionCode = String(item.version_code || "");
					selectedDetail = null;
					activeDetailTab = "summary";
					bundleSectionState.section = "";
					writeFiltersToUrl();
					renderLibraryCards(wrap);
					fetchTemplateDetailForCard(wrap, item);
				}
			});
			root.appendChild(card);
		});
	}

	function highlightActiveCard(wrap) {
		const root = wrap.querySelector('[data-testid="std-library-summary-cards"]');
		if (!root) return;
		root.querySelectorAll(".std-library-card").forEach((el) => {
			const queue = el.getAttribute("data-queue");
			const active = queue === summaryState.activeQueue;
			el.classList.toggle("is-active", active);
			el.setAttribute("aria-pressed", active ? "true" : "false");
		});
	}

	function setActiveQueue(wrap, queue) {
		summaryState.activeQueue = queue;
		writeFiltersToUrl();
		highlightActiveCard(wrap);
		updateListQueueContext(wrap);
		refreshTemplates(wrap);
	}

	function renderSummaryCards(wrap) {
		const slot = wrap.querySelector('[data-testid="std-library-summary-cards"]');
		if (!slot) return;
		slot.innerHTML = "";
		const grid = document.createElement("div");
		grid.className = "std-library-summary-grid";

		SUMMARY_CARDS.forEach((card) => {
			const count = Number(summaryState.counts[card.countKey] || 0);
			const btn = document.createElement("button");
			btn.type = "button";
			btn.className = "std-library-card btn-reset";
			btn.setAttribute("data-testid", card.selector);
			btn.setAttribute("data-queue", card.queue);
			btn.setAttribute(
				"aria-label",
				`${card.label}: ${count}. ${card.explanation}`,
			);
			btn.innerHTML = `
<span class="std-library-card-count">${count}</span>
<span class="std-library-card-label">${card.label}</span>
<span class="std-library-card-note">${card.explanation}</span>`;
			btn.addEventListener("click", function () {
				setActiveQueue(wrap, card.queue);
			});
			grid.appendChild(btn);
		});

		slot.appendChild(grid);
		highlightActiveCard(wrap);
	}

	function describeFilter(key, value) {
		const labels = {
			search: __("Search"),
			procurement_category: __("Category"),
			procurement_method: __("Method"),
			status: __("Status"),
			source_authority: __("Source"),
			validation_status: __("Validation"),
			supersession_status: __("Supersession"),
			used_by_tenders: __("Used by tenders"),
			bundle_preview_status: __("Bundle"),
			revision_from: __("From"),
			revision_to: __("To"),
		};
		return `${labels[key] || key}: ${value}`;
	}

	function renderFilterChips(wrap) {
		const holder = wrap.querySelector('[data-testid="std-library-active-filter-chips"]');
		if (!holder) return;
		holder.innerHTML = "";
		const entries = [
			["search", filterState.search],
			["procurement_category", filterState.procurement_category],
			["procurement_method", filterState.procurement_method],
			["status", filterState.status.join(", ")],
			["source_authority", filterState.source_authority],
			["validation_status", filterState.validation_status.join(", ")],
			["supersession_status", filterState.supersession_status.join(", ")],
			["used_by_tenders", filterState.used_by_tenders === "Any" ? "" : filterState.used_by_tenders],
			["bundle_preview_status", filterState.bundle_preview_status.join(", ")],
			["revision_from", filterState.revision_from],
			["revision_to", filterState.revision_to],
		].filter(([, v]) => Boolean(v));
		if (!entries.length) {
			holder.textContent = __("No active filters.");
			return;
		}
		entries.forEach(([k, v]) => {
			const chip = document.createElement("span");
			chip.className = "std-library-chip";
			chip.textContent = describeFilter(k, v);
			holder.appendChild(chip);
		});
	}

	function collectMultiValues(selectEl) {
		if (!selectEl) return [];
		return Array.from(selectEl.selectedOptions || [])
			.map((x) => x.value)
			.filter(Boolean);
	}

	function readFilterPanelState(wrap) {
		filterState.search = String(
			wrap.querySelector('[data-testid="std-library-search-input"]')?.value || "",
		).trim();
		FILTER_CONFIG.forEach((cfg) => {
			const el = wrap.querySelector(`[data-filter-key="${cfg.key}"]`);
			if (!el) return;
			if (cfg.type === "multi") {
				filterState[cfg.key] = collectMultiValues(el);
			} else {
				filterState[cfg.key] = String(el.value || "").trim();
			}
		});
	}

	function applyFilterStateToPanel(wrap) {
		const searchInput = wrap.querySelector('[data-testid="std-library-search-input"]');
		if (searchInput) searchInput.value = filterState.search || "";
		FILTER_CONFIG.forEach((cfg) => {
			const el = wrap.querySelector(`[data-filter-key="${cfg.key}"]`);
			if (!el) return;
			if (cfg.type === "multi") {
				const selected = new Set(filterState[cfg.key] || []);
				Array.from(el.options).forEach((opt) => {
					opt.selected = selected.has(opt.value);
				});
			} else {
				el.value = filterState[cfg.key] || "";
			}
		});
	}

	function resetFilters(wrap) {
		filterState.search = "";
		filterState.procurement_category = "";
		filterState.procurement_method = "";
		filterState.status = [];
		filterState.source_authority = "";
		filterState.validation_status = [];
		filterState.supersession_status = [];
		filterState.used_by_tenders = "Any";
		filterState.bundle_preview_status = [];
		filterState.revision_from = "";
		filterState.revision_to = "";
		selectedVersionCode = "";
		selectedDetail = null;
		activeDetailTab = "summary";
		bundleSectionState.section = "";
		applyFilterStateToPanel(wrap);
		renderFilterChips(wrap);
		writeFiltersToUrl();
		refreshTemplates(wrap);
	}

	function renderFilterPanel(wrap) {
		const panel = wrap.querySelector('[data-testid="std-library-filter-panel"]');
		if (!panel) return;
		panel.innerHTML = "";
		const grid = document.createElement("div");
		grid.className = "std-library-filter-grid";
		FILTER_CONFIG.forEach((cfg) => {
			const field = document.createElement("label");
			field.className = "std-library-filter-field";
			const title = document.createElement("span");
			title.className = "std-library-filter-label";
			title.textContent = cfg.label;
			const select = document.createElement("select");
			select.className = "form-control input-sm";
			select.setAttribute("data-filter-key", cfg.key);
			if (cfg.type === "multi") {
				select.multiple = true;
				select.size = Math.min(cfg.options.length, 4);
			}
			cfg.options.forEach((optionValue) => {
				const opt = document.createElement("option");
				opt.value = optionValue;
				opt.textContent = optionValue || __("Any");
				select.appendChild(opt);
			});
			field.appendChild(title);
			field.appendChild(select);
			grid.appendChild(field);
		});

		const dateRange = document.createElement("div");
		dateRange.className = "std-library-filter-date-row";
		dateRange.innerHTML = `
<label class="std-library-filter-field">
	<span class="std-library-filter-label">${__("Revision From")}</span>
	<input type="date" class="form-control input-sm" data-filter-key="revision_from" />
</label>
<label class="std-library-filter-field">
	<span class="std-library-filter-label">${__("Revision To")}</span>
	<input type="date" class="form-control input-sm" data-filter-key="revision_to" />
</label>`;
		panel.appendChild(grid);
		panel.appendChild(dateRange);
		applyFilterStateToPanel(wrap);
	}

	function refreshTemplates(wrap) {
		const params = {
			search: filterState.search,
			procurement_category: filterState.procurement_category,
			procurement_method: filterState.procurement_method,
			status: (filterState.status || []).join(","),
			source_authority: filterState.source_authority,
			validation_status: (filterState.validation_status || []).join(","),
			supersession_status: (filterState.supersession_status || []).join(","),
			used_by_tenders: filterState.used_by_tenders || "Any",
			bundle_preview_status: (filterState.bundle_preview_status || []).join(","),
			revision_from: filterState.revision_from,
			revision_to: filterState.revision_to,
			queue: summaryState.activeQueue,
		};
		return stdApi
			.getStdLibraryTemplates(params)
			.then((resp) => {
				libraryPageState.templatesLoadError = "";
				templatesResponse = resp || { total_count: 0, rows: [], items: [] };
				updateListQueueContext(wrap);
				renderFilterChips(wrap);
				renderLibraryCards(wrap);
				const selected = (templatesResponse.items || []).find(
					(x) => String(x.version_code || "") === selectedVersionCode,
				);
				if (!selected) {
					if (selectedVersionCode) {
						selectedVersionCode = "";
						activeDetailTab = "summary";
						selectedDetail = null;
						bundleSectionState.section = "";
						writeFiltersToUrl();
					} else {
						selectedDetail = null;
					}
					setSelectedDetail(wrap, null);
					return;
				}
				return fetchTemplateDetailForCard(wrap, selected);
			})
			.catch((err) => {
				libraryPageState.templatesLoadError = userMsg.sanitizeUserFacingError(
					err?.message,
					userMsg.FALLBACK_LIST_LOAD,
				);
				templatesResponse = { total_count: 0, rows: [], items: [] };
				if (selectedVersionCode) {
					selectedVersionCode = "";
					activeDetailTab = "summary";
					selectedDetail = null;
					bundleSectionState.section = "";
					writeFiltersToUrl();
				}
				updateListQueueContext(wrap);
				renderFilterChips(wrap);
				renderLibraryCards(wrap);
				setSelectedDetail(wrap, null);
			});
	}

	function build_shell_fragment() {
		const wrap = document.createElement("div");
		wrap.className = "std-library-shell";
		wrap.setAttribute("data-testid", "std-library-page");

		wrap.innerHTML = `
<div class="std-library-shell-inner">
	<header class="std-library-region-a">
		<div class="std-library-header-main">
			<h3 data-testid="std-library-header-title"></h3>
			<p data-testid="std-library-header-subtitle" class="std-library-subtitle"></p>
		</div>
		<div class="std-library-header-actions">
			<button type="button" class="btn btn-primary btn-sm"
				data-testid="std-library-import-package-button"></button>
			<button type="button" class="btn btn-default btn-sm"
				data-testid="std-library-register-source-button"></button>
			<button type="button" class="btn btn-default btn-sm"
				data-testid="std-library-validate-library-button"></button>
		</div>
	</header>

	<section class="std-library-region-b std-library-guidance" data-testid="std-library-guidance-strip"></section>

	<section class="std-library-region-c" data-testid="std-library-summary-cards">
		<div class="std-library-summary-placeholder"></div>
	</section>

	<section class="std-library-region-d std-library-search-row">
		<input type="search" class="form-control input-sm"
			data-testid="std-library-search-input"
			placeholder="" />
		<button type="button" class="btn btn-default btn-sm"
			data-testid="std-library-filter-button"
			aria-expanded="false"
			aria-controls="std-library-filter-panel"></button>
		<button type="button" class="btn btn-default btn-sm"
			data-testid="std-library-clear-filters"></button>
	</section>
	<div class="std-library-filter-panel hidden" id="std-library-filter-panel" data-testid="std-library-filter-panel"></div>
	<div class="std-library-chip-row" data-testid="std-library-active-filter-chips"></div>

	<div class="std-library-region-ef">
		<section class="std-library-region-e" data-testid="std-library-list"></section>
		<aside class="std-library-region-f" data-testid="std-library-detail-panel"></aside>
	</div>
</div>
<div class="std-library-action-modal hidden" data-testid="std-library-action-modal" aria-hidden="true">
	<div class="std-library-action-modal-backdrop" data-testid="std-library-action-modal-backdrop" tabindex="-1"></div>
	<div class="std-library-action-modal-dialog" role="dialog" aria-modal="true" aria-labelledby="std-library-action-modal-title">
		<div class="std-library-action-modal-chrome">
			<h3 class="std-library-action-modal-title" id="std-library-action-modal-title" data-testid="std-library-action-modal-title"></h3>
			<button type="button" class="btn btn-default btn-sm std-library-action-modal-close"
				data-testid="std-library-action-modal-close">${__("Close")}</button>
		</div>
		<div class="std-library-action-modal-body" data-testid="std-library-action-modal-body">
			<div class="std-register-source-panel hidden" data-testid="std-register-source-panel"></div>
			<div class="std-library-validation-summary-panel hidden" data-testid="std-library-validation-summary-panel"></div>
		</div>
	</div>
</div>`;

		wrap.querySelector('[data-testid="std-library-header-title"]').textContent = TITLE;
		wrap.querySelector('[data-testid="std-library-header-subtitle"]').textContent = SUBTITLE;
		wrap.querySelector('[data-testid="std-library-import-package-button"]').textContent =
			BUTTON_CONFIG.importPackage.label;
		wrap.querySelector('[data-testid="std-library-register-source-button"]').textContent =
			BUTTON_CONFIG.registerSource.label;
		wrap.querySelector('[data-testid="std-library-validate-library-button"]').textContent =
			BUTTON_CONFIG.validateLibrary.label;
		wrap.querySelector('[data-testid="std-library-guidance-strip"]').textContent = GUIDANCE_TEXT;
		const searchEl = wrap.querySelector('[data-testid="std-library-search-input"]');
		searchEl.setAttribute("placeholder", SEARCH_PLACEHOLDER);
		searchEl.setAttribute("aria-label", __("Search official STD library"));
		wrap.querySelector('[data-testid="std-library-filter-button"]').textContent = __("Filters");
		wrap.querySelector('[data-testid="std-library-clear-filters"]').textContent =
			__("Clear Filters");

		const listRegion = wrap.querySelector('[data-testid="std-library-list"]');
		const listInner = document.createElement("div");
		listInner.className = "std-library-list-inner";
		listInner.innerHTML = `
<div class="std-library-list-context std-library-placeholder-pane" data-testid="std-library-list-queue-context"></div>
<div class="std-library-list-cards" data-testid="std-library-list-cards"></div>`;
		listRegion.appendChild(listInner);

		const detailRegion = wrap.querySelector('[data-testid="std-library-detail-panel"]');
		const detailInner = document.createElement("div");
		detailInner.className = "std-library-detail-inner std-library-placeholder-pane";
		detailInner.textContent = DETAIL_EMPTY;
		detailRegion.appendChild(detailInner);

		summaryState.activeQueue = readQueueFromUrl();
		readFiltersFromUrl();
		readSelectionFromUrl();
		renderFilterPanel(wrap);
		renderRegisterSourcePanel(wrap);
		renderLibraryValidationPanel(wrap);
		renderSummaryCards(wrap);
		renderFilterChips(wrap);
		updateListQueueContext(wrap);
		renderLibraryCards(wrap);

		ensureLibraryActionModalHandlers(wrap);
		apply_action_policy(wrap, {});
		stdApi
			.getActionAvailability([
				ACTION_CODES.importPackage,
				ACTION_CODES.registerSource,
				ACTION_CODES.validateLibrary,
			])
			.then(function (availability) {
				apply_action_policy(wrap, availability || {});
			})
			.catch(function () {
				apply_action_policy(wrap, {});
			});

		stdApi
			.getStdLibrarySummary()
			.then(function (counts) {
				summaryState.counts = { ...summaryState.counts, ...(counts || {}) };
				renderSummaryCards(wrap);
				updateListQueueContext(wrap);
			})
			.catch(function () {
				renderSummaryCards(wrap);
				updateListQueueContext(wrap);
			});

		refreshTemplates(wrap);

		const searchInput = wrap.querySelector('[data-testid="std-library-search-input"]');
		if (searchInput) {
			searchInput.addEventListener("change", function () {
				readFilterPanelState(wrap);
				writeFiltersToUrl();
				refreshTemplates(wrap);
			});
		}
		const panel = wrap.querySelector('[data-testid="std-library-filter-panel"]');
		const filterBtn = wrap.querySelector('[data-testid="std-library-filter-button"]');
		if (filterBtn && panel) {
			filterBtn.addEventListener("click", function () {
				panel.classList.toggle("hidden");
				filterBtn.setAttribute(
					"aria-expanded",
					panel.classList.contains("hidden") ? "false" : "true",
				);
			});
			panel.addEventListener("change", function () {
				readFilterPanelState(wrap);
				writeFiltersToUrl();
				refreshTemplates(wrap);
			});
		}
		const clearBtn = wrap.querySelector('[data-testid="std-library-clear-filters"]');
		if (clearBtn) {
			clearBtn.addEventListener("click", function () {
				resetFilters(wrap);
			});
		}

		return wrap;
	}


	kentender_procurement.std_library_shell.libraryPageState = libraryPageState;

	kentender_procurement.std_library_shell.mountInto = function (wrapper) {
		if (!wrapper) return;
		const el = typeof wrapper === "string" ? document.querySelector(wrapper) : wrapper;
		if (!el) return;
		while (el.firstChild) {
			el.removeChild(el.firstChild);
		}
		el.appendChild(build_shell_fragment());
	};
	kentender_procurement.std_library_shell.mountImportInto = function (wrapper) {
		if (!wrapper) return;
		const el = typeof wrapper === "string" ? document.querySelector(wrapper) : wrapper;
		if (!el) return;
		const shell = kentender_procurement.std_library_shell;
		const build = shell.buildImportWizardFragment;
		if (typeof build !== "function") {
			frappe.show_alert({
				message: __("Import wizard failed to load. Ensure std_library_import_wizard_shell.js is included before this file."),
				indicator: "red",
			});
			return;
		}
		while (el.firstChild) {
			el.removeChild(el.firstChild);
		}
		el.appendChild(build());
	};
})();
