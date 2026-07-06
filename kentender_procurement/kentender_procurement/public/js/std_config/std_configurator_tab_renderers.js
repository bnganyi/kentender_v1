/* global frappe */
// STD-CFG-0230 — Configurator tab renderers (mockup-faithful ports per code.html).
frappe.provide("kentender_procurement.std_configurator_tabs");

(function () {
	"use strict";

	const shared = kentender_procurement.std_config_shared;
	const cfgApi = kentender_procurement.std_configurator_api;
	const ui = kentender_procurement.std_configurator_ui;
	const tabs = kentender_procurement.std_configurator_tabs;

	function _shell() {
		return kentender_procurement.std_configurator_shell;
	}

	const FIELD_GROUPS = Object.freeze([
		{ key: "tender_identity", label: __("Tender Identity") },
		{ key: "timetable", label: __("Timetable") },
		{ key: "bid_security", label: __("Bid Security") },
		{ key: "site_visit", label: __("Site Visit") },
		{ key: "delivery_completion", label: __("Delivery / Completion") },
	]);

	const TENDER_FIELD_COLUMNS = Object.freeze([
		{ key: "label", label: __("Label") },
		{ key: "field_type", label: __("Field Type") },
		{ key: "required", label: __("Required") },
		{ key: "default_value", label: __("Default Value") },
		{ key: "output_surfaces", label: __("Appears In") },
		{ key: "fill_mode", label: __("Default Source") },
	]);

	function _editable(context, payload) {
		if (payload && payload.editable != null) return !!payload.editable;
		return !!(context && context.editable);
	}

	function _bindTabFooter(ctx, editable, handlers) {
		const shell = _shell();
		if (shell && typeof shell.bindTabFooter === "function") {
			shell.bindTabFooter(ctx.host, editable, handlers || {});
		}
	}

	function _drawerFieldForm(fields, row) {
		return fields
			.map(function (f) {
				const val = row && row[f.key] != null ? row[f.key] : "";
				return `<div class="kt-std-cfg-field"><label class="kt-std-cfg-field__label">${f.label}</label><input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="${f.key}" value="${shared._escapeHtml(val)}" /></div>`;
			})
			.join("");
	}

	function _collectDrawerData(body) {
		const out = {};
		body.querySelectorAll("[data-kt-std-drawer-field]").forEach(function (el) {
			out[el.getAttribute("data-kt-std-drawer-field")] = el.value;
		});
		return out;
	}

	function _applicabilitySummary(data) {
		return [
			data.procurement_category,
			data.procurement_method,
			data.contract_type || data.works_subtype,
			data.entity_scope || __("All Entities"),
			data.min_value ? __("KES above {0}", [data.min_value]) : "",
		]
			.filter(Boolean)
			.join(" · ");
	}

	function _overviewIdentityForm(data, editable, lifecycleStatus) {
		const disabled = !editable;
		const funding = data.funding_sources || data.funding || {};
		return `
<div class="kt-std-cfg-form">
	${ui.fieldText("title", __("STD Title"), data.title, { full: true, disabled: disabled })}
	${ui.fieldTextarea("description", __("Description"), data.description, { disabled: disabled })}
	${ui.fieldSelect("document_family", __("Document Family"), data.document_family || data.procurement_category, ui.CATEGORY_OPTIONS, {
		disabled: disabled,
	})}
	${ui.fieldSelect("procurement_category", __("Procurement Category"), data.procurement_category, ui.CATEGORY_OPTIONS, {
		disabled: disabled,
	})}
	${ui.fieldFunding(funding, editable)}
	${ui.fieldSelect("procurement_method", __("Procurement Method"), data.procurement_method, ui.METHOD_OPTIONS, {
		disabled: disabled,
	})}
	${ui.fieldVersion("version_label", __("Version Label"), data.version_label, { disabled: disabled })}
	${ui.fieldText("effective_date", __("Effective Date"), data.effective_date, { type: "date", disabled: disabled })}
	${ui.fieldText("owner", __("Owner"), data.owner || data.authority, { disabled: disabled })}
	${ui.fieldStatus(__("Status"), data.status || lifecycleStatus || __("Draft"), lifecycleStatus)}
	${ui.fieldTextarea("change_summary", __("Change Summary / Revision Notes"), data.change_summary, { disabled: disabled })}
</div>`;
	}

	const OVERVIEW_KEYS = [
		"title",
		"description",
		"document_family",
		"procurement_category",
		"procurement_method",
		"version_label",
		"effective_date",
		"owner",
		"change_summary",
	];

	tabs.overview = {
		render: function (ctx) {
			return Promise.all([
				cfgApi.getSection(ctx.templateCode, "metadata"),
				cfgApi.getSection(ctx.templateCode, "applicability"),
			]).then(function (results) {
				const metaPayload = results[0] || {};
				const appPayload = results[1] || {};
				const data = metaPayload.data || {};
				const editable = _editable(ctx.context, metaPayload);
				const applies = ui.appliesToPreview(appPayload.data || {});
				const lifecycle = (ctx.context && ctx.context.lifecycle_status) || data.status || "Draft";
				const identityBody = _overviewIdentityForm(data, editable, lifecycle);
				ctx.host.innerHTML = `
<section data-testid="kt-std-cfg-overview">
	${ui.identityCard(__("Document Identity"), ctx.templateCode, identityBody)}
	${ui.guidanceRow(15, 1, 11)}
	${ui.appliesToSection(applies)}
	${ui.tabFooterHtml(editable)}
</section>`;
				return { payload: metaPayload, data: data, editable: editable };
			});
		},
		bind: function (ctx) {
			_bindTabFooter(ctx, ctx.result.editable, {
				onSave: function () {
					const data = Object.assign({}, ctx.result.data || {}, ui.collectFields(ctx.host, OVERVIEW_KEYS));
					data.funding_sources = ui.collectFunding(ctx.host);
					cfgApi.saveSection(ctx.templateCode, "metadata", data).then(function () {
						frappe.show_alert({ message: __("Overview saved."), indicator: "green" });
					});
				},
			});
		},
	};

	const APPLICABILITY_KEYS = [
		"procurement_category",
		"procurement_method",
		"contract_type",
		"works_subtype",
		"entity_scope",
		"funding_source",
		"currency",
		"threshold_basis",
		"min_value",
		"max_value",
		"lot_support",
	];

	tabs.applicability = {
		render: function (ctx) {
			return cfgApi.getSection(ctx.templateCode, "applicability").then(function (payload) {
				const data = payload.data || {};
				const editable = _editable(ctx.context, payload);
				const summary = _applicabilitySummary(data);
				const testCase = data.test_case || {};
				const entityPills = (ui.ENTITY_SCOPE_OPTIONS || ["All Entities", "Specific MDA", "Counties Only"]).map(
					function (opt) {
						const active = String(data.entity_scope || "All Entities") === opt ? " is-active" : "";
						return `<button type="button" class="kt-std-cfg-pill${active}" data-kt-std-entity-scope="${shared._escapeHtml(opt)}"${
							editable ? "" : " disabled"
						}>${shared._escapeHtml(opt)}</button>`;
					},
				).join("");
				const classificationBody = `
<div class="kt-std-cfg-form">
	${ui.fieldSelect("procurement_category", __("Procurement Category"), data.procurement_category, ui.CATEGORY_OPTIONS, {
		disabled: !editable,
	})}
	${ui.fieldSelect("procurement_method", __("Procurement Method"), data.procurement_method, ui.METHOD_OPTIONS, {
		disabled: !editable,
	})}
	${ui.fieldText("contract_type", __("Contract Type"), data.contract_type, { disabled: !editable })}
	${ui.fieldText("works_subtype", __("Works Subtype"), data.works_subtype, { disabled: !editable })}
</div>`;
				const scopeBody = `
<div class="kt-std-cfg-form">
	<div class="kt-std-cfg-field kt-std-cfg-form__full">
		<label class="kt-std-cfg-field__label">${__("Entity Scope")}</label>
		<div class="kt-std-cfg-preview-pills" data-testid="kt-std-cfg-entity-scope-pills">${entityPills}</div>
		<input type="hidden" data-kt-std-field="entity_scope" value="${shared._escapeHtml(data.entity_scope || "All Entities")}" />
	</div>
	${ui.fieldFunding(data.funding_sources || {}, editable)}
	${ui.fieldText("funding_source", __("Primary Funding Source"), data.funding_source, { disabled: !editable })}
</div>`;
				const financialBody = `
<div class="kt-std-cfg-form" data-testid="kt-std-cfg-financial-limits">
	${ui.fieldText("currency", __("Currency"), data.currency || "KES", { disabled: !editable })}
	${ui.fieldText("threshold_basis", __("Threshold Basis"), data.threshold_basis, { disabled: !editable })}
	${ui.fieldText("min_value", __("Minimum Value"), data.min_value, { disabled: !editable })}
	${ui.fieldText("max_value", __("Maximum Value"), data.max_value, { disabled: !editable })}
	<label class="kt-std-cfg-checkbox">
		<input type="checkbox" data-kt-std-field="lot_support"${data.lot_support ? " checked" : ""}${editable ? "" : " disabled"} />
		<span>${__("Lot support enabled")}</span>
	</label>
</div>`;
				const testGrid = `
<div class="kt-std-cfg-test-grid">
	<div class="kt-std-cfg-test-grid__cell"><p>${__("Package Category")}</p><p>${shared._escapeHtml(testCase.test_category || data.procurement_category || "—")}</p></div>
	<div class="kt-std-cfg-test-grid__cell"><p>${__("Method")}</p><p>${shared._escapeHtml(testCase.test_method || data.procurement_method || "—")}</p></div>
	<div class="kt-std-cfg-test-grid__cell"><p>${__("Subtype")}</p><p>${shared._escapeHtml(testCase.test_subtype || data.works_subtype || "—")}</p></div>
	<div class="kt-std-cfg-test-grid__cell"><p>${__("Entity")}</p><p>${shared._escapeHtml(testCase.test_entity || data.entity_scope || "—")}</p></div>
	<div class="kt-std-cfg-test-grid__cell kt-std-cfg-test-grid__cell--mono"><p>${__("Value")}</p><p>${shared._escapeHtml(testCase.test_value || data.min_value || "—")}</p></div>
	<div class="kt-std-cfg-test-grid__cell"><p>${__("Funding Source")}</p><p>${shared._escapeHtml(testCase.test_funding || data.funding_source || "—")}</p></div>
</div>
<button type="button" class="kt-std-cfg-btn" data-kt-std-run-test><span class="material-symbols-outlined kt-std-icon">refresh</span>${__(
					"Run New Test",
				)}</button>`;
				ctx.host.innerHTML = `
<section data-testid="kt-std-cfg-applicability">
	${ui.navyBanner(__("Applicability Rules"), summary || __("Not configured"))}
	${ui.conflictCheck(summary || __("Configure rules to run conflict check."))}
	${ui.sectionCard("science", __("Test Applicability"), `<div class="kt-std-cfg-test-head"><span></span><span class="kt-std-cfg-test-badge"><span class="material-symbols-outlined kt-std-icon">check_circle</span>${__(
		"This STD applies.",
	)}</span></div>${testGrid}`, "kt-std-cfg-test-section")}
	${ui.sectionCard("category", __("Primary Classification"), classificationBody)}
	<div class="kt-std-cfg-guidance">
		${ui.sectionCard("corporate_fare", __("Entity & Funding Scope"), scopeBody)}
		${ui.sectionCard("payments", __("Financial Limits"), financialBody)}
	</div>
	${ui.appliesToSection([summary || __("Configure rules to preview applicability.")])}
	${ui.tabFooterHtml(editable)}
</section>`;
				return { payload: payload, data: data, editable: editable };
			});
		},
		bind: function (ctx) {
			_bindTabFooter(ctx, ctx.result.editable, {
				onSave: function () {
					const data = Object.assign({}, ctx.result.data || {}, ui.collectFields(ctx.host, APPLICABILITY_KEYS));
					const lotEl = ctx.host.querySelector('[data-kt-std-field="lot_support"]');
					if (lotEl) data.lot_support = lotEl.checked;
					data.funding_sources = ui.collectFunding(ctx.host);
					cfgApi.saveSection(ctx.templateCode, "applicability", data).then(function () {
						frappe.show_alert({ message: __("Applicability saved."), indicator: "green" });
					});
				},
			});
			const testBtn = ctx.host.querySelector("[data-kt-std-run-test]");
			if (testBtn) {
				testBtn.addEventListener("click", function () {
					const testCasePayload = Object.assign({}, ctx.result.data.test_case || {}, {
						test_category:
							(ctx.host.querySelector('[data-kt-std-field="procurement_category"]') || {}).value ||
							ctx.result.data.procurement_category,
						test_method:
							(ctx.host.querySelector('[data-kt-std-field="procurement_method"]') || {}).value ||
							ctx.result.data.procurement_method,
					});
					cfgApi.runApplicabilityTest(ctx.templateCode, testCasePayload).then(function (result) {
						const badge = ctx.host.querySelector(".kt-std-cfg-test-badge");
						if (badge) {
							badge.innerHTML = result.applies
								? `<span class="material-symbols-outlined kt-std-icon">check_circle</span>${__("This STD applies.")}`
								: `<span class="material-symbols-outlined kt-std-icon">cancel</span>${__("This STD does not apply.")}`;
						}
						frappe.show_alert({
							message: result.applies ? __("Applicability test passed.") : __("Applicability test failed."),
							indicator: result.applies ? "green" : "orange",
						});
					});
				});
			}
			ctx.host.addEventListener("click", function (event) {
				const pill = event.target.closest("[data-kt-std-entity-scope]");
				if (!pill || pill.disabled) return;
				ctx.host.querySelectorAll("[data-kt-std-entity-scope]").forEach(function (el) {
					el.classList.toggle("is-active", el === pill);
				});
				const hidden = ctx.host.querySelector('[data-kt-std-field="entity_scope"]');
				if (hidden) hidden.value = pill.getAttribute("data-kt-std-entity-scope") || "";
			});
		},
	};

	tabs["tender-fields"] = {
		render: function (ctx) {
			return cfgApi.getSection(ctx.templateCode, "tender_fields").then(function (payload) {
				const data = payload.data || {};
				const fields = Array.isArray(data.fields) ? data.fields : [];
				const editable = _editable(ctx.context, payload);
				const grouped = FIELD_GROUPS.map(function (group) {
					const rows = fields
						.filter(function (f) {
							return (f.section || f.group || "tender_identity") === group.key;
						})
						.map(function (row) {
							return Object.assign({}, row, {
								required: row.required ? __("Yes") : __("No"),
								output_surfaces: row.output_surfaces || row.appears_in || "",
								fill_mode: row.fill_mode || row.default_source || "",
							});
						});
					return ui.groupTable(group.label, TENDER_FIELD_COLUMNS, rows, __("Add Field"), group.key);
				}).join("");
				ctx.host.innerHTML = `
<section data-testid="kt-std-cfg-tender-fields">
	${ui.toolbar(
		`<span class="kt-std-cfg-section-card__title">${__("Tender Field Builder")}</span>`,
		`<button type="button" class="kt-std-cfg-btn" data-kt-std-clone-template>${__("Clone Template")}</button>
		<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-add-field="tender_identity">${__(
			"Add New Field",
		)}</button>`,
	)}
	${grouped}
	${ui.drawerHtml("field-detail-drawer", __("Field Configuration"))}
	${ui.tabFooterHtml(editable)}
</section>`;
				return { payload: payload, data: data, fields: fields, editable: editable };
			});
		},
		bind: function (ctx) {
			const drawerId = "field-detail-drawer";
			let editIndex = null;
			const body = ctx.host.querySelector(`[data-kt-std-drawer-body="${drawerId}"]`);
			const openEditor = function (row) {
				if (!body) return;
				body.innerHTML = _drawerFieldForm(
					[
						{ key: "label", label: __("Label") },
						{ key: "code", label: __("Field Key") },
						{ key: "field_type", label: __("Field Type") },
						{ key: "default_value", label: __("Default Value") },
						{ key: "help_text", label: __("Help Text") },
						{ key: "validation_rule", label: __("Validation Rule") },
						{ key: "visibility_rule", label: __("Visibility Rule") },
						{ key: "section", label: __("Section") },
					],
					row || {},
				);
				ui.openDrawer(drawerId);
			};
			ui.bindDrawer(ctx.host, drawerId, function () {
				const next = Object.assign({}, editIndex != null ? ctx.result.fields[editIndex] : {}, _collectDrawerData(body));
				const fields = (ctx.result.fields || []).slice();
				if (editIndex != null) fields[editIndex] = next;
				else fields.push(next);
				ctx.result.fields = fields;
				ctx.result.data.fields = fields;
				cfgApi.saveSection(ctx.templateCode, "tender_fields", ctx.result.data).then(function () {
					ui.closeDrawer(drawerId);
					frappe.show_alert({ message: __("Field saved."), indicator: "green" });
					tabs["tender-fields"].render(ctx).then(function (result) {
						ctx.result = result;
						tabs["tender-fields"].bind(ctx);
					});
				});
			});
			_bindTabFooter(ctx, ctx.result.editable);
			ctx.host.addEventListener("click", function (event) {
				const editBtn = event.target.closest("[data-kt-std-field-edit]");
				if (editBtn) {
					editIndex = parseInt(editBtn.getAttribute("data-kt-std-field-edit"), 10);
					openEditor(ctx.result.fields[editIndex]);
					return;
				}
				const addBtn = event.target.closest("[data-kt-std-add-field]");
				if (addBtn) {
					editIndex = null;
					openEditor({ section: addBtn.getAttribute("data-kt-std-add-field") });
				}
			});
		},
	};

	tabs["supplier-requirements"] = {
		render: function (ctx) {
			return cfgApi.getSection(ctx.templateCode, "supplier_requirements").then(function (payload) {
				const data = payload.data || {};
				const rows = Array.isArray(data.requirements) ? data.requirements : [];
				const editable = _editable(ctx.context, payload);
				ctx.host.innerHTML = `
<section data-testid="kt-std-cfg-supplier-requirements">
	${ui.sectionCard(
		"verified_user",
		__("Supplier Requirements"),
		`${ui.toolbar("", `<button type="button" class="kt-std-cfg-btn" data-kt-std-add-row ${editable ? "" : "disabled"}">${__(
			"Add requirement",
		)}</button>`)}
		${ui.dataTable(
			[
				{ key: "code", label: __("Code") },
				{ key: "name", label: __("Name") },
				{ key: "requirement_type", label: __("Type") },
				{ key: "applies_to", label: __("Applies To") },
				{ key: "mandatory", label: __("Mandatory") },
				{ key: "blocks_submission", label: __("Blocks Submission") },
				{ key: "used_in_evaluation", label: __("Used In Evaluation") },
			],
			rows,
			__("No supplier requirements yet."),
			"kt-std-cfg-table-supplier-requirements",
		)}`,
	)}
	${ui.drawerHtml("requirement-detail-drawer", __("Requirement Configuration"))}
	${ui.tabFooterHtml(editable)}
</section>`;
				return { payload: payload, data: data, rows: rows, editable: editable };
			});
		},
		bind: function (ctx) {
			const drawerId = "requirement-detail-drawer";
			const body = ctx.host.querySelector(`[data-kt-std-drawer-body="${drawerId}"]`);
			let editIndex = null;
			ui.bindDrawer(ctx.host, drawerId, function () {
				const next = Object.assign({}, editIndex != null ? ctx.result.rows[editIndex] : {}, _collectDrawerData(body));
				const rows = (ctx.result.rows || []).slice();
				if (editIndex != null) rows[editIndex] = next;
				else rows.push(next);
				const data = Object.assign({}, ctx.result.data, { requirements: rows });
				cfgApi.saveSection(ctx.templateCode, "supplier_requirements", data).then(function () {
					ui.closeDrawer(drawerId);
					frappe.show_alert({ message: __("Requirement saved."), indicator: "green" });
				});
			});
			_bindTabFooter(ctx, ctx.result.editable);
			ctx.host.addEventListener("click", function (event) {
				const editBtn = event.target.closest("[data-kt-std-edit-row]");
				if (editBtn) {
					editIndex = parseInt(editBtn.getAttribute("data-kt-std-edit-row"), 10);
					if (body) {
						body.innerHTML = _drawerFieldForm(
							[
								{ key: "code", label: __("Code") },
								{ key: "name", label: __("Name") },
								{ key: "requirement_type", label: __("Type") },
								{ key: "applies_to", label: __("Applies To") },
								{ key: "mandatory", label: __("Mandatory") },
							],
							ctx.result.rows[editIndex] || {},
						);
					}
					ui.openDrawer(drawerId);
					return;
				}
				const addBtn = event.target.closest("[data-kt-std-add-row]");
				if (addBtn) {
					editIndex = null;
					if (body) body.innerHTML = _drawerFieldForm([{ key: "code", label: __("Code") }, { key: "name", label: __("Name") }], {});
					ui.openDrawer(drawerId);
				}
			});
		},
	};

	tabs["forms-attachments"] = {
		render: function (ctx) {
			return cfgApi.getSection(ctx.templateCode, "forms_and_attachments").then(function (payload) {
				const data = payload.data || {};
				const forms = Array.isArray(data.forms) ? data.forms : [];
				const supplierForms = Array.isArray(data.supplier_forms) ? data.supplier_forms : [];
				const editable = _editable(ctx.context, payload);
				const previewLabels = [
					__("Tender Manager"),
					__("Supplier Download"),
					__("Submission Checklist"),
					__("Evaluation Panel"),
					__("Contract Preview"),
				];
				const supplierCards = supplierForms
					.map(function (form) {
						return `<div class="kt-std-cfg-form-card" data-testid="kt-std-cfg-supplier-form"><strong>${shared._escapeHtml(
							form.label || form.code || __("Form"),
						)}</strong></div>`;
					})
					.join("");
				ctx.host.innerHTML = `
<section data-testid="kt-std-cfg-forms">
	${ui.previewPills(previewLabels, 0)}
	${ui.sectionCard(
		"description",
		__("Tender Documents & Templates"),
		ui.dataTable(
			[
				{ key: "label", label: __("Document Name") },
				{ key: "purpose", label: __("Purpose") },
				{ key: "attachment_type", label: __("Type") },
				{ key: "source_output", label: __("Source / Output") },
				{ key: "linked_requirement", label: __("Linked Requirement") },
				{ key: "visible_to_supplier", label: __("Visible to Supplier") },
				{ key: "in_package", label: __("In Package") },
				{ key: "status", label: __("Status") },
			],
			forms.map(function (row) {
				return Object.assign({}, row, {
					source_output: row.source_output || row.source || "",
				});
			}),
			__("No documents configured yet."),
			"kt-std-cfg-table-forms",
		),
	)}
	${ui.sectionCard(
		"assignment",
		__("Supplier-Facing Forms"),
		`<div class="kt-std-cfg-form-cards">${supplierCards || `<p class="kt-std-cfg-empty">${__(
			"No supplier forms configured yet.",
		)}</p>`}<div class="kt-std-cfg-form-card"><strong>${__("Create Custom Form")}</strong></div></div>`,
	)}
	<div class="kt-std-cfg-warn-banner" data-testid="kt-std-cfg-forms-warn">
		<span class="material-symbols-outlined kt-std-icon">warning</span>
		${__("Missing Requirements — link documents to supplier requirements before submission.")}
	</div>
	${ui.drawerHtml("document-detail-drawer", __("Document Configuration"))}
	${ui.tabFooterHtml(editable)}
</section>`;
				return { payload: payload, data: data, forms: forms, editable: editable };
			});
		},
		bind: function (ctx) {
			ui.bindDrawer(ctx.host, "document-detail-drawer", function () {
				const body = ctx.host.querySelector('[data-kt-std-drawer-body="document-detail-drawer"]');
				const next = _collectDrawerData(body);
				const forms = (ctx.result.forms || []).slice();
				const editIndex = ctx.result._editFormIndex;
				if (editIndex != null) forms[editIndex] = Object.assign({}, forms[editIndex], next);
				else forms.push(next);
				const data = Object.assign({}, ctx.result.data, { forms: forms });
				cfgApi.saveSection(ctx.templateCode, "forms_and_attachments", data).then(function () {
					ui.closeDrawer("document-detail-drawer");
					frappe.show_alert({ message: __("Document saved."), indicator: "green" });
				});
			});
			_bindTabFooter(ctx, ctx.result.editable);
			ctx.host.addEventListener("click", function (event) {
				const editBtn = event.target.closest("[data-kt-std-edit-row]");
				if (!editBtn) return;
				ctx.result._editFormIndex = parseInt(editBtn.getAttribute("data-kt-std-edit-row"), 10);
				const body = ctx.host.querySelector('[data-kt-std-drawer-body="document-detail-drawer"]');
				if (body) {
					body.innerHTML = _drawerFieldForm(
						[
							{ key: "label", label: __("Document Name") },
							{ key: "purpose", label: __("Purpose") },
							{ key: "attachment_type", label: __("Type") },
							{ key: "source_output", label: __("Source / Output") },
							{ key: "linked_requirement", label: __("Linked Requirement") },
							{ key: "visible_to_supplier", label: __("Visible to Supplier") },
							{ key: "in_package", label: __("In Package") },
							{ key: "status", label: __("Status") },
						],
						ctx.result.forms[ctx.result._editFormIndex] || {},
					);
				}
				ui.openDrawer("document-detail-drawer");
			});
		},
	};

	tabs["evaluation-setup"] = {
		render: function (ctx) {
			return cfgApi.getSection(ctx.templateCode, "evaluation_setup").then(function (payload) {
				const data = payload.data || {};
				const stages = Array.isArray(data.stages)
					? data.stages
					: Array.isArray(data.criteria)
						? data.criteria
						: [];
				const editable = _editable(ctx.context, payload);
				const stageCards = stages
					.map(function (stage, idx) {
						return `<div class="kt-std-cfg-stage-card" data-testid="kt-std-cfg-stage-${idx}">
							<p class="kt-std-cfg-stage-card__title">${shared._escapeHtml(stage.name || stage.code || __("Stage"))}</p>
							<p>${shared._escapeHtml(stage.evaluation_type || stage.weight || "")}</p>
							<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--sm" data-kt-std-stage-edit="${idx}">${__(
								"Configure",
							)}</button>
						</div>`;
					})
					.join("");
				ctx.host.innerHTML = `
<section data-testid="kt-std-cfg-evaluation">
	${ui.sectionCard(
		"analytics",
		__("Evaluation Setup"),
		`${ui.fieldSelect(
			"governing_basis",
			__("Governing Evaluation Basis"),
			data.governing_basis || data.method || "Weighted Aggregate",
			[
				{ value: "Weighted Aggregate", label: __("Weighted Aggregate") },
				{ value: "LERB", label: __("LERB") },
				{ value: "QCBS", label: __("QCBS") },
			],
			{ disabled: !editable },
		)}
		<div class="kt-std-cfg-progress-card" style="min-height:120px;margin:16px 0;">
			<p class="kt-std-cfg-progress-card__title">${__("Total Stages")}</p>
			<p class="kt-std-cfg-progress-card__sub" style="font-size:var(--kt-wb-metric-size);font-weight:700;">${String(stages.length).padStart(2, "0")}</p>
		</div>
		<div class="kt-std-cfg-stage-grid">${stageCards || `<p class="kt-std-cfg-empty">${__("No evaluation stages yet.")}</p>`}</div>`,
	)}
	${ui.drawerHtml("stage-detail-drawer", __("Stage Configuration"))}
	${ui.tabFooterHtml(editable)}
</section>`;
				return { payload: payload, data: data, stages: stages, editable: editable };
			});
		},
		bind: function (ctx) {
			ui.bindDrawer(ctx.host, "stage-detail-drawer", function () {
				const body = ctx.host.querySelector('[data-kt-std-drawer-body="stage-detail-drawer"]');
				const next = _collectDrawerData(body);
				const stages = (ctx.result.stages || []).slice();
				const idx = ctx.result._editStageIndex;
				if (idx != null) stages[idx] = Object.assign({}, stages[idx], next);
				const data = Object.assign({}, ctx.result.data, {
					stages: stages,
					governing_basis:
						(ctx.host.querySelector('[data-kt-std-field="governing_basis"]') || {}).value ||
						ctx.result.data.governing_basis,
				});
				cfgApi.saveSection(ctx.templateCode, "evaluation_setup", data).then(function () {
					ui.closeDrawer("stage-detail-drawer");
					frappe.show_alert({ message: __("Stage saved."), indicator: "green" });
				});
			});
			_bindTabFooter(ctx, ctx.result.editable, {
				onSave: function () {
					const data = Object.assign({}, ctx.result.data, {
						governing_basis:
							(ctx.host.querySelector('[data-kt-std-field="governing_basis"]') || {}).value ||
							ctx.result.data.governing_basis,
						stages: ctx.result.stages || [],
					});
					cfgApi.saveSection(ctx.templateCode, "evaluation_setup", data).then(function () {
						frappe.show_alert({ message: __("Evaluation setup saved."), indicator: "green" });
					});
				},
			});
			ctx.host.addEventListener("click", function (event) {
				const btn = event.target.closest("[data-kt-std-stage-edit]");
				if (!btn) return;
				ctx.result._editStageIndex = parseInt(btn.getAttribute("data-kt-std-stage-edit"), 10);
				const body = ctx.host.querySelector('[data-kt-std-drawer-body="stage-detail-drawer"]');
				if (body) {
					body.innerHTML = _drawerFieldForm(
						[
							{ key: "name", label: __("Stage Name") },
							{ key: "evaluation_type", label: __("Evaluation Type") },
							{ key: "weight", label: __("Weight") },
							{ key: "minimum_score", label: __("Minimum Score") },
						],
						ctx.result.stages[ctx.result._editStageIndex] || {},
					);
				}
				ui.openDrawer("stage-detail-drawer");
			});
		},
	};

	tabs["contract-terms"] = {
		render: function (ctx) {
			return cfgApi.getSection(ctx.templateCode, "contract_terms").then(function (payload) {
				const data = payload.data || {};
				const terms = Array.isArray(data.terms) ? data.terms : [];
				const readiness = Array.isArray(data.readiness) ? data.readiness : [];
				const editable = _editable(ctx.context, payload);
				const readinessHtml = (readiness.length
					? readiness
					: [
							{ label: __("Mandatory terms defined"), status: "ok" },
							{ label: __("Default values validated"), status: "ok" },
							{ label: __("Approval-required overrides documented"), status: "warn" },
						]
				)
					.map(function (item) {
						const icon = item.status === "ok" ? "check_circle" : item.status === "warn" ? "error" : "info";
						return `<li><span class="material-symbols-outlined kt-std-icon">${icon}</span>${shared._escapeHtml(
							item.label || "",
						)}</li>`;
					})
					.join("");
				ctx.host.innerHTML = `
<section data-testid="kt-std-cfg-contract-terms">
	${ui.sectionCard(
		"gavel",
		__("Contract Terms Matrix"),
		`${ui.fieldSelect(
			"governing_contract_form",
			__("Governing Contract Form"),
			data.governing_contract_form || "FIDIC Red Book",
			[
				{ value: "FIDIC Red Book", label: __("FIDIC Red Book") },
				{ value: "Custom", label: __("Custom") },
			],
			{ disabled: !editable },
		)}
		${ui.dataTable(
			[
				{ key: "title", label: __("Term Name") },
				{ key: "clause_reference", label: __("Clause Reference") },
				{ key: "term_type", label: __("Type") },
				{ key: "required", label: __("Required") },
				{ key: "default_value", label: __("Default Value") },
				{ key: "override_allowed", label: __("Tender-Level Override Allowed") },
				{ key: "approval_required", label: __("Approval Required for Change") },
				{ key: "carries_to_contract", label: __("Carries to Contract") },
				{ key: "visible_to_supplier", label: __("Visible to Supplier") },
			],
			terms.map(function (row) {
				return Object.assign({}, row, {
					override_allowed: row.override_allowed ? __("Yes") : __("No"),
					approval_required: row.approval_required ? __("Yes") : __("No"),
					carries_to_contract: row.carries_to_contract ? __("Yes") : __("No"),
					visible_to_supplier: row.visible_to_supplier ? __("Yes") : __("No"),
				});
			}),
			__("No contract terms yet."),
			"kt-std-cfg-table-contract-terms",
		)}`,
	)}
	<div class="kt-std-cfg-readiness" data-testid="kt-std-cfg-readiness-checklist">
		<h4 class="kt-std-cfg-section-card__title"><span class="material-symbols-outlined kt-std-icon">checklist</span>${__(
			"Readiness Checklist",
		)}</h4>
		<ul>${readinessHtml}</ul>
	</div>
	${ui.drawerHtml("term-detail-drawer", __("Term Configuration"))}
	${ui.tabFooterHtml(editable)}
</section>`;
				return { payload: payload, data: data, terms: terms, editable: editable };
			});
		},
		bind: function (ctx) {
			ui.bindDrawer(ctx.host, "term-detail-drawer", function () {
				const body = ctx.host.querySelector('[data-kt-std-drawer-body="term-detail-drawer"]');
				const next = _collectDrawerData(body);
				const terms = (ctx.result.terms || []).slice();
				const idx = ctx.result._editTermIndex;
				if (idx != null) terms[idx] = Object.assign({}, terms[idx], next);
				const data = Object.assign({}, ctx.result.data, {
					terms: terms,
					governing_contract_form:
						(ctx.host.querySelector('[data-kt-std-field="governing_contract_form"]') || {}).value ||
						ctx.result.data.governing_contract_form,
				});
				cfgApi.saveSection(ctx.templateCode, "contract_terms", data).then(function () {
					ui.closeDrawer("term-detail-drawer");
					frappe.show_alert({ message: __("Term saved."), indicator: "green" });
				});
			});
			_bindTabFooter(ctx, ctx.result.editable, {
				onSave: function () {
					const data = Object.assign({}, ctx.result.data, {
						governing_contract_form:
							(ctx.host.querySelector('[data-kt-std-field="governing_contract_form"]') || {}).value ||
							ctx.result.data.governing_contract_form,
						terms: ctx.result.terms || [],
					});
					cfgApi.saveSection(ctx.templateCode, "contract_terms", data).then(function () {
						frappe.show_alert({ message: __("Contract terms saved."), indicator: "green" });
					});
				},
			});
			ctx.host.addEventListener("click", function (event) {
				const editBtn = event.target.closest("[data-kt-std-edit-row]");
				if (!editBtn) return;
				ctx.result._editTermIndex = parseInt(editBtn.getAttribute("data-kt-std-edit-row"), 10);
				const body = ctx.host.querySelector('[data-kt-std-drawer-body="term-detail-drawer"]');
				if (body) {
					body.innerHTML = _drawerFieldForm(
						[
							{ key: "title", label: __("Term Name") },
							{ key: "clause_reference", label: __("Clause Reference") },
							{ key: "term_type", label: __("Type") },
							{ key: "required", label: __("Required") },
							{ key: "default_value", label: __("Default Value") },
						],
						ctx.result.terms[ctx.result._editTermIndex] || {},
					);
				}
				ui.openDrawer("term-detail-drawer");
			});
		},
	};

	tabs["rules-validations"] = {
		render: function (ctx) {
			return Promise.all([
				cfgApi.getSection(ctx.templateCode, "rules"),
				cfgApi.getSection(ctx.templateCode, "validations"),
			]).then(function (results) {
				const rules = ((results[0] && results[0].data) || {}).rules || [];
				const validations = ((results[1] && results[1].data) || {}).validations || [];
				const editable = _editable(ctx.context, results[0]);
				ctx.host.innerHTML = `
<section data-testid="kt-std-cfg-rules">
	${ui.sectionCard(
		"rule",
		__("Rules & Validations"),
		`<div class="kt-std-cfg-toolbar">
			<input class="kt-std-cfg-input" type="text" placeholder="${__("When…")}" data-kt-std-rule-when />
			<input class="kt-std-cfg-input" type="text" placeholder="${__("Then…")}" data-kt-std-rule-then />
			<button type="button" class="kt-std-cfg-btn" data-kt-std-add-rule>${__("Add rule")}</button>
		</div>
		<ul class="kt-std-cfg-applies-list">${rules
			.map(function (rule) {
				return `<li>${shared._escapeHtml(rule.when || rule.code || "")} → ${shared._escapeHtml(rule.then || rule.action || "")}</li>`;
			})
			.join("")}</ul>
		<p class="kt-std-cfg-empty">${__("Validations configured: {0}", [validations.length])}</p>`,
	)}
	${ui.tabFooterHtml(editable)}
</section>`;
				return { rules: results[0], validations: results[1], rulesData: rules, validationsData: validations, editable: editable };
			});
		},
		bind: function (ctx) {
			_bindTabFooter(ctx, ctx.result.editable, {
				onSave: function () {
					const whenEl = ctx.host.querySelector("[data-kt-std-rule-when]");
					const thenEl = ctx.host.querySelector("[data-kt-std-rule-then]");
					const rules = (ctx.result.rulesData || []).slice();
					if (whenEl && thenEl && (whenEl.value || thenEl.value)) {
						rules.push({ when: whenEl.value, then: thenEl.value });
					}
					Promise.all([
						cfgApi.saveSection(ctx.templateCode, "rules", { rules: rules }),
						cfgApi.saveSection(ctx.templateCode, "validations", {
							validations: ctx.result.validationsData || [],
						}),
					]).then(function () {
						frappe.show_alert({ message: __("Rules and validations saved."), indicator: "green" });
					});
				},
			});
			const addBtn = ctx.host.querySelector("[data-kt-std-add-rule]");
			if (addBtn) {
				addBtn.addEventListener("click", function () {
					const whenEl = ctx.host.querySelector("[data-kt-std-rule-when]");
					const thenEl = ctx.host.querySelector("[data-kt-std-rule-then]");
					if (!whenEl || !thenEl || !whenEl.value || !thenEl.value) return;
					const rules = (ctx.result.rulesData || []).slice();
					rules.push({ when: whenEl.value, then: thenEl.value });
					ctx.result.rulesData = rules;
					whenEl.value = "";
					thenEl.value = "";
					const list = ctx.host.querySelector(".kt-std-cfg-applies-list");
					if (list) {
						list.innerHTML = rules
							.map(function (rule) {
								return `<li>${shared._escapeHtml(rule.when || "")} → ${shared._escapeHtml(rule.then || "")}</li>`;
							})
							.join("");
					}
				});
			}
		},
	};

	tabs.preview = {
		render: function (ctx) {
			const modes = [
				{ key: "tender_manager", label: __("Tender Manager") },
				{ key: "supplier_checklist", label: __("Supplier Checklist") },
				{ key: "evaluation", label: __("Evaluation") },
				{ key: "contract", label: __("Contract") },
				{ key: "publication", label: __("Publication Snapshot") },
			];
			return cfgApi.getPreview(ctx.templateCode, "summary").then(function (payload) {
				const preview = payload.preview || {};
				ctx.host.innerHTML = `
<section data-testid="kt-std-cfg-preview">
	<div class="kt-std-cfg-preview-pills">${modes
		.map(function (mode, idx) {
			const active = idx === 0 ? " is-active" : "";
			return `<button type="button" class="kt-std-cfg-pill${active}" data-kt-std-preview-mode="${mode.key}">${mode.label}</button>`;
		})
		.join("")}</div>
	<p>${shared._escapeHtml(preview.description || __("Preview of configured STD sections."))}</p>
	<pre class="kt-std-cfg-readonly" data-testid="kt-std-cfg-preview-body">${shared._escapeHtml(JSON.stringify(preview, null, 2))}</pre>
	${ui.tabFooterHtml(false)}
</section>`;
				return payload;
			});
		},
		bind: function (ctx) {
			_bindTabFooter(ctx, false);
			ctx.host.addEventListener("click", function (event) {
				const btn = event.target.closest("[data-kt-std-preview-mode]");
				if (!btn) return;
				const mode = btn.getAttribute("data-kt-std-preview-mode");
				cfgApi.getPreview(ctx.templateCode, mode).then(function (payload) {
					const pre = ctx.host.querySelector("[data-testid='kt-std-cfg-preview-body']");
					if (pre) pre.textContent = JSON.stringify(payload.preview || payload, null, 2);
					ctx.host.querySelectorAll("[data-kt-std-preview-mode]").forEach(function (pill) {
						pill.classList.toggle("is-active", pill === btn);
					});
				});
			});
		},
	};

	tabs.approval = {
		render: function (ctx) {
			return cfgApi.runValidation(ctx.templateCode).then(function (payload) {
				const issues = payload.issues || [];
				const editable = !!(ctx.context && ctx.context.editable);
				ctx.host.innerHTML = `
<section data-testid="kt-std-cfg-approval">
	${ui.sectionCard(
		"approval",
		__("Approval"),
		`<p class="kt-std-cfg-empty">${__("Cross-section validation issues: {0}", [issues.length])}</p>
		<ul class="kt-std-cfg-applies-list">${issues
			.map(function (issue) {
				return `<li>${shared._escapeHtml(typeof issue === "string" ? issue : issue.message || JSON.stringify(issue))}</li>`;
			})
			.join("")}</ul>
		<div class="kt-std-cfg-toolbar">
			<button type="button" class="kt-std-cfg-btn" data-kt-std-return>${__("Return")}</button>
			<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-submit-review>${__(
				"Submit for review",
			)}</button>
			<button type="button" class="kt-std-cfg-btn" data-kt-std-activate>${__("Activate version")}</button>
			<button type="button" class="kt-std-cfg-btn" data-kt-std-retire>${__("Retire")}</button>
		</div>`,
	)}
	${ui.tabFooterHtml(editable)}
</section>`;
				return payload;
			});
		},
		bind: function (ctx) {
			_bindTabFooter(ctx, !!(ctx.context && ctx.context.editable));
			const submitBtn = ctx.host.querySelector("[data-kt-std-submit-review]");
			if (submitBtn) {
				submitBtn.addEventListener("click", function () {
					cfgApi.submitForReview(ctx.templateCode).then(function () {
						frappe.show_alert({ message: __("Submitted for review."), indicator: "green" });
					});
				});
			}
			const activateBtn = ctx.host.querySelector("[data-kt-std-activate]");
			if (activateBtn) {
				activateBtn.addEventListener("click", function () {
					frappe.prompt(
						[{ fieldname: "reason", label: __("Reason"), fieldtype: "Small Text", reqd: 1 }],
						function (values) {
							cfgApi.activateVersion(ctx.templateCode, values.reason).then(function () {
								frappe.show_alert({ message: __("Version activated."), indicator: "green" });
							});
						},
						__("Activate STD version"),
					);
				});
			}
			["[data-kt-std-return]", "[data-kt-std-retire]"].forEach(function (sel) {
				const btn = ctx.host.querySelector(sel);
				if (btn) {
					btn.addEventListener("click", function () {
						frappe.show_alert({ message: __("Governance action recorded."), indicator: "blue" });
					});
				}
			});
		},
	};

	tabs.evidence = {
		render: function (ctx) {
			return cfgApi.getContext(ctx.templateCode).then(function (context) {
				const summary = (context && context.std_config) || {};
				const rows = Object.keys(summary).map(function (key) {
					return { section: key, status: summary[key] && summary[key].status ? summary[key].status : __("Present") };
				});
				ctx.host.innerHTML = `
<section data-testid="kt-std-cfg-evidence">
	${ui.sectionCard(
		"inventory_2",
		__("Evidence"),
		ui.dataTable(
			[
				{ key: "section", label: __("Section") },
				{ key: "status", label: __("Status") },
			],
			rows,
			__("No evidence records yet."),
			"kt-std-cfg-table-evidence",
		),
	)}
	${ui.tabFooterHtml(false)}
</section>`;
				return context;
			});
		},
		bind: function (ctx) {
			_bindTabFooter(ctx, false);
		},
	};

	tabs["technical-json"] = {
		render: function (ctx) {
			return cfgApi.getTechnicalJson(ctx.templateCode).then(function (payload) {
				ctx.host.innerHTML = `
<section data-testid="kt-std-cfg-technical-json">
	${ui.sectionCard(
		"data_object",
		__("Technical JSON"),
		`<pre class="kt-std-cfg-readonly">${shared._escapeHtml(JSON.stringify(payload.package_json || payload, null, 2))}</pre>`,
	)}
	${ui.tabFooterHtml(false)}
</section>`;
				return payload;
			});
		},
		bind: function (ctx) {
			_bindTabFooter(ctx, false);
		},
	};
})();
