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
		return ui.applicabilitySummaryLine(data);
	}

	function _overviewIdentityForm(data, editable, lifecycleStatus) {
		const disabled = !editable;
		const funding = data.funding_sources || data.funding || {};
		return `
<div class="kt-std-cfg-form" data-testid="kt-std-cfg-identity-form">
	${ui.fieldText("title", __("STD Title"), data.title, { full: true, disabled: disabled })}
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
	${ui.fieldDate("effective_date", __("Effective Date"), data.effective_date, { disabled: disabled })}
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
<section class="kt-std-cfg-tab-stack" data-testid="kt-std-cfg-overview">
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
			ui.bindAppliesCopy(ctx.host);
		},
	};

	const APPLICABILITY_KEYS = [
		"procurement_category",
		"procurement_method",
		"contract_type",
		"works_subtype",
		"entity_scope",
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
				const appliesLines = ui.appliesToPreview(data);
				const classificationBody = `
<div class="kt-std-cfg-form kt-std-cfg-form--classification">
	${ui.fieldSelect("procurement_category", __("Procurement Category"), data.procurement_category, ui.CATEGORY_OPTIONS, {
		disabled: !editable,
	})}
	${ui.fieldSelect("procurement_method", __("Procurement Method"), data.procurement_method, ui.METHOD_OPTIONS, {
		disabled: !editable,
	})}
	${ui.fieldSelect("contract_type", __("Contract Type"), data.contract_type, ui.CONTRACT_TYPE_OPTIONS, {
		disabled: !editable,
	})}
	${ui.fieldSelect("works_subtype", __("Works Subtype"), data.works_subtype, ui.WORKS_SUBTYPE_OPTIONS, {
		disabled: !editable,
	})}
</div>`;
				const scopeBody = `
<div class="kt-std-cfg-form kt-std-cfg-form--scope">
	${ui.entityScopeBlock(data, editable)}
	${ui.fieldFundingCards(data.funding_sources || {}, editable)}
</div>`;
				ctx.host.innerHTML = ui.applicabilityTabDocument({
					banner: ui.navyBanner(__("Applicability Rules"), summary || __("Not configured")),
					conflict: ui.conflictCheck(summary || __("Configure rules to run conflict check.")),
					test: ui.testApplicabilitySection(data.test_case, data, true),
					formLayout: ui.applicabilityLayout(
						`${ui.sectionCard("category", __("Primary Classification"), classificationBody, "kt-std-cfg-classification")}
						${ui.sectionCard("corporate_fare", __("Entity & Funding Scope"), scopeBody, "kt-std-cfg-entity-funding")}`,
						ui.sectionCard(
							"payments",
							__("Financial Limits"),
							ui.financialLimitsPanel(data, editable),
							"kt-std-cfg-financial-limits-card",
						),
					),
					appliesPreview: ui.applicabilityAppliesSection(appliesLines),
					footer: ui.tabFooterHtml(editable),
				});
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
					data.entity_codes = ui.collectEntityCodes(ctx.host);
					cfgApi.saveSection(ctx.templateCode, "applicability", data).then(function () {
						frappe.show_alert({ message: __("Applicability saved."), indicator: "green" });
					});
				},
			});
			ui.bindConflictCopy(ctx.host);
			ui.bindAppliesCopy(ctx.host);
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
						test_subtype:
							(ctx.host.querySelector('[data-kt-std-field="works_subtype"]') || {}).value ||
							ctx.result.data.works_subtype,
						test_entity:
							(ui.collectEntityCodes(ctx.host)[0] ||
								(ctx.host.querySelector('[data-kt-std-field="entity_scope"]') || {}).value ||
								ctx.result.data.entity_scope),
					});
					cfgApi.runApplicabilityTest(ctx.templateCode, testCasePayload).then(function (result) {
						const badge = ctx.host.querySelector("[data-testid='kt-std-cfg-test-badge']");
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
				if (pill && !pill.disabled) {
					ctx.host.querySelectorAll("[data-kt-std-entity-scope]").forEach(function (el) {
						el.classList.toggle("is-active", el === pill);
					});
					const hidden = ctx.host.querySelector('[data-kt-std-field="entity_scope"]');
					if (hidden) hidden.value = pill.getAttribute("data-kt-std-entity-scope") || "";
					ui.syncEntityPickerVisibility(ctx.host);
					return;
				}
				const removeBtn = event.target.closest("[data-kt-std-entity-remove]");
				if (removeBtn) {
					const chip = removeBtn.closest("[data-kt-std-entity-chip]");
					if (chip) chip.remove();
				}
			});
			const entityInput = ctx.host.querySelector("[data-kt-std-entity-input]");
			if (entityInput) {
				entityInput.addEventListener("keydown", function (event) {
					if (event.key !== "Enter") return;
					event.preventDefault();
					const value = String(entityInput.value || "").trim();
					if (!value) return;
					const box = ctx.host.querySelector(".kt-std-cfg-entity-picker__box");
					if (!box) return;
					const chip = document.createElement("span");
					chip.className = "kt-std-cfg-entity-chip";
					chip.setAttribute("data-kt-std-entity-chip", value);
					chip.innerHTML = `${shared._escapeHtml(value)}<button type="button" class="kt-std-cfg-entity-chip__remove" data-kt-std-entity-remove="${shared._escapeHtml(
						value,
					)}" aria-label="${__("Remove")}"><span class="material-symbols-outlined kt-std-icon">close</span></button>`;
					box.insertBefore(chip, entityInput);
					entityInput.value = "";
				});
			}
		},
	};

	tabs["tender-fields"] = {
		render: function (ctx) {
			return cfgApi.getSection(ctx.templateCode, "tender_fields").then(function (payload) {
				const data = payload.data || {};
				const fields = Array.isArray(data.fields) ? data.fields : [];
				const editable = _editable(ctx.context, payload);
				ctx.host.innerHTML = ui.tenderFieldsTabDocument({
					actions: ui.tenderFieldsActionBar(editable),
					matrix: ui.tenderFieldsMatrix(fields, editable),
					guidance: ui.tenderFieldsGuidanceRow(),
					drawer: ui.drawerHtml("field-detail-drawer", __("Field Details")),
					footer: ui.tabFooterHtml(editable),
				});
				return { payload: payload, data: data, fields: fields, editable: editable };
			});
		},
		bind: function (ctx) {
			const drawerId = "field-detail-drawer";
			let editIndex = null;
			const body = ctx.host.querySelector(`[data-kt-std-drawer-body="${drawerId}"]`);

			function _collectFieldDrawerData(drawerBody) {
				const out = {};
				if (!drawerBody) return out;
				drawerBody.querySelectorAll("[data-kt-std-drawer-field]").forEach(function (el) {
					const key = el.getAttribute("data-kt-std-drawer-field");
					if (!key) return;
					if (el.type === "checkbox") out[key] = el.checked;
					else out[key] = el.value;
				});
				if (out.required_rule != null) {
					out.required = String(out.required_rule).toLowerCase() !== "no";
					delete out.required_rule;
				}
				if (out.section) {
					out.group = out.section;
				}
				return out;
			}

			const openEditor = function (row, index) {
				if (!body) return;
				editIndex = index == null ? null : index;
				body.innerHTML = ui.fieldDetailDrawerBody(row || {}, ctx.result.editable);
				ui.openDrawer(drawerId);
			};

			ui.bindDrawer(ctx.host, drawerId, function () {
				const next = Object.assign(
					{},
					editIndex != null ? ctx.result.fields[editIndex] : {},
					_collectFieldDrawerData(body),
				);
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
				const deleteBtn = event.target.closest("[data-kt-std-field-delete]");
				if (deleteBtn && ctx.result.editable) {
					const idx = parseInt(deleteBtn.getAttribute("data-kt-std-field-delete"), 10);
					const fields = (ctx.result.fields || []).slice();
					if (!Number.isNaN(idx)) fields.splice(idx, 1);
					ctx.result.fields = fields;
					ctx.result.data.fields = fields;
					cfgApi.saveSection(ctx.templateCode, "tender_fields", ctx.result.data).then(function () {
						frappe.show_alert({ message: __("Field removed."), indicator: "green" });
						tabs["tender-fields"].render(ctx).then(function (result) {
							ctx.result = result;
							tabs["tender-fields"].bind(ctx);
						});
					});
					return;
				}
				const editBtn = event.target.closest("[data-kt-std-field-edit]");
				if (editBtn) {
					const idx = parseInt(editBtn.getAttribute("data-kt-std-field-edit"), 10);
					openEditor(ctx.result.fields[idx], idx);
					return;
				}
				const row = event.target.closest("[data-kt-std-field-row]");
				if (row && !event.target.closest("button")) {
					const idx = parseInt(row.getAttribute("data-kt-std-field-row"), 10);
					openEditor(ctx.result.fields[idx], idx);
					return;
				}
				const addBtn = event.target.closest("[data-kt-std-add-field]");
				if (addBtn && !addBtn.disabled) {
					const section = addBtn.getAttribute("data-kt-std-add-field") || "tender_identity";
					openEditor({ section: section, group: section, required: true }, null);
					return;
				}
				const addHereBtn = event.target.closest("[data-kt-std-add-field-here]");
				if (addHereBtn && !addHereBtn.disabled) {
					openEditor({ section: "tender_identity", group: "tender_identity", required: true }, null);
					return;
				}
				const cloneBtn = event.target.closest("[data-kt-std-clone-template]");
				if (cloneBtn && !cloneBtn.disabled) {
					frappe.show_alert({ message: __("Clone template is not available in this draft."), indicator: "orange" });
				}
			});
			const searchInput = ctx.host.querySelector("[data-kt-std-tf-search]");
			if (searchInput) {
				searchInput.addEventListener("input", function () {
					const query = String(searchInput.value || "")
						.trim()
						.toLowerCase();
					ctx.host.querySelectorAll(".kt-std-cfg-tf-field-row").forEach(function (row) {
						const text = (row.textContent || "").toLowerCase();
						row.style.display = !query || text.includes(query) ? "" : "none";
					});
				});
			}
		},
	};

	tabs["supplier-requirements"] = {
		render: function (ctx) {
			return cfgApi.getSection(ctx.templateCode, "supplier_requirements").then(function (payload) {
				const data = payload.data || {};
				const rows = Array.isArray(data.requirements) ? data.requirements : [];
				const editable = _editable(ctx.context, payload);
				ctx.host.innerHTML = ui.supplierRequirementsTabDocument({
					actions: ui.supplierRequirementsActionBar(editable),
					matrix: ui.supplierRequirementsMatrix(rows, editable),
					guidance: ui.supplierRequirementsGuidanceRow(),
					drawer: ui.drawerHtml("requirement-detail-drawer", __("Requirement Details")),
					footer: ui.tabFooterHtml(editable),
				});
				return { payload: payload, data: data, rows: rows, editable: editable };
			});
		},
		bind: function (ctx) {
			const drawerId = "requirement-detail-drawer";
			let editIndex = null;
			const body = ctx.host.querySelector(`[data-kt-std-drawer-body="${drawerId}"]`);

			function _collectRequirementDrawerData(drawerBody) {
				const out = {};
				if (!drawerBody) return out;
				drawerBody.querySelectorAll("[data-kt-std-drawer-field]").forEach(function (el) {
					const key = el.getAttribute("data-kt-std-drawer-field");
					if (!key) return;
					if (el.type === "checkbox") out[key] = el.checked;
					else out[key] = el.value;
				});
				if ("supplier_visible" in out) {
					out.supplier_visibility = out.supplier_visible ? __("Visible") : __("Hidden");
					delete out.supplier_visible;
				}
				return out;
			}

			const openEditor = function (row, index) {
				if (!body) return;
				editIndex = index == null ? null : index;
				const drawerRow = Object.assign({}, row || {});
				if (drawerRow.supplier_visibility == null && drawerRow.supplier_visible == null) {
					drawerRow.supplier_visible = true;
				} else {
					drawerRow.supplier_visible =
						String(drawerRow.supplier_visibility || "").toLowerCase() !== "hidden";
				}
				body.innerHTML = ui.requirementDetailDrawerBody(drawerRow, ctx.result.editable);
				ui.openDrawer(drawerId);
			};

			ui.bindDrawer(ctx.host, drawerId, function () {
				const next = Object.assign(
					{},
					editIndex != null ? ctx.result.rows[editIndex] : {},
					_collectRequirementDrawerData(body),
				);
				const rows = (ctx.result.rows || []).slice();
				if (editIndex != null) rows[editIndex] = next;
				else rows.push(next);
				ctx.result.rows = rows;
				const data = Object.assign({}, ctx.result.data, { requirements: rows });
				cfgApi.saveSection(ctx.templateCode, "supplier_requirements", data).then(function () {
					ui.closeDrawer(drawerId);
					frappe.show_alert({ message: __("Requirement saved."), indicator: "green" });
					tabs["supplier-requirements"].render(ctx).then(function (result) {
						ctx.result = result;
						tabs["supplier-requirements"].bind(ctx);
					});
				});
			});
			_bindTabFooter(ctx, ctx.result.editable);
			ctx.host.addEventListener("click", function (event) {
				const deleteBtn = event.target.closest("[data-kt-std-requirement-delete]");
				if (deleteBtn && ctx.result.editable) {
					const idx = parseInt(deleteBtn.getAttribute("data-kt-std-requirement-delete"), 10);
					const rows = (ctx.result.rows || []).slice();
					if (!Number.isNaN(idx)) rows.splice(idx, 1);
					ctx.result.rows = rows;
					const data = Object.assign({}, ctx.result.data, { requirements: rows });
					cfgApi.saveSection(ctx.templateCode, "supplier_requirements", data).then(function () {
						frappe.show_alert({ message: __("Requirement removed."), indicator: "green" });
						tabs["supplier-requirements"].render(ctx).then(function (result) {
							ctx.result = result;
							tabs["supplier-requirements"].bind(ctx);
						});
					});
					return;
				}
				const editBtn = event.target.closest("[data-kt-std-requirement-edit]");
				if (editBtn) {
					const idx = parseInt(editBtn.getAttribute("data-kt-std-requirement-edit"), 10);
					openEditor(ctx.result.rows[idx], idx);
					return;
				}
				const row = event.target.closest("[data-kt-std-requirement-row]");
				if (row && !event.target.closest("button")) {
					const idx = parseInt(row.getAttribute("data-kt-std-requirement-row"), 10);
					openEditor(ctx.result.rows[idx], idx);
					return;
				}
				const addBtn = event.target.closest("[data-kt-std-add-requirement]");
				if (addBtn && !addBtn.disabled) {
					openEditor(
						{
							mandatory: __("Yes"),
							applies_to: __("All Suppliers"),
							blocks_submission: __("Yes"),
							used_in_evaluation: __("No"),
							requirement_type: __("Form"),
						},
						null,
					);
					return;
				}
				const addHereBtn = event.target.closest("[data-kt-std-add-requirement-here]");
				if (addHereBtn && !addHereBtn.disabled) {
					openEditor(
						{
							mandatory: __("Yes"),
							applies_to: __("All Suppliers"),
							blocks_submission: __("Yes"),
							used_in_evaluation: __("No"),
							requirement_type: __("Form"),
						},
						null,
					);
				}
			});
			const searchInput = ctx.host.querySelector("[data-kt-std-sr-search]");
			if (searchInput) {
				searchInput.addEventListener("input", function () {
					const query = String(searchInput.value || "")
						.trim()
						.toLowerCase();
					ctx.host.querySelectorAll(".kt-std-cfg-sr-row").forEach(function (row) {
						const text = (row.textContent || "").toLowerCase();
						row.style.display = !query || text.includes(query) ? "" : "none";
					});
				});
			}
		},
	};

	tabs["forms-attachments"] = {
		render: function (ctx) {
			return cfgApi.getSection(ctx.templateCode, "forms_and_attachments").then(function (payload) {
				const data = payload.data || {};
				const forms = Array.isArray(data.forms) ? data.forms : [];
				const supplierForms = Array.isArray(data.supplier_forms) ? data.supplier_forms : [];
				const missingRequirements = Array.isArray(data.missing_requirements) ? data.missing_requirements : [];
				const editable = _editable(ctx.context, payload);
				const previewIndex = ctx._faPreviewIndex == null ? 0 : ctx._faPreviewIndex;
				ctx.host.innerHTML = ui.formsAttachmentsTabDocument({
					documents: ui.formsAttachmentsDocumentsSection(forms, editable, previewIndex),
					supplierForms: ui.formsAttachmentsSupplierFormsSection(supplierForms, editable),
					info: ui.formsAttachmentsInfoRow(missingRequirements),
					drawer: ui.drawerHtml("document-detail-drawer", __("Document Configuration")),
					footer: ui.tabFooterHtml(editable),
				});
				return {
					payload: payload,
					data: data,
					forms: forms,
					supplierForms: supplierForms,
					missingRequirements: missingRequirements,
					previewIndex: previewIndex,
					editable: editable,
				};
			});
		},
		bind: function (ctx) {
			const drawerId = "document-detail-drawer";
			let editIndex = null;
			const body = ctx.host.querySelector(`[data-kt-std-drawer-body="${drawerId}"]`);

			function _collectDocumentDrawerData(drawerBody) {
				const out = {};
				if (!drawerBody) return out;
				drawerBody.querySelectorAll("[data-kt-std-drawer-field]").forEach(function (el) {
					const key = el.getAttribute("data-kt-std-drawer-field");
					if (!key) return;
					if (el.type === "checkbox") out[key] = el.checked;
					else out[key] = el.value;
				});
				return out;
			}

			const openEditor = function (row, index) {
				if (!body) return;
				editIndex = index == null ? null : index;
				body.innerHTML = ui.documentDetailDrawerBody(row || {}, ctx.result.editable);
				ui.openDrawer(drawerId);
			};

			const rerender = function (previewIndex) {
				ctx._faPreviewIndex = previewIndex == null ? ctx.result.previewIndex || 0 : previewIndex;
				return tabs["forms-attachments"].render(ctx).then(function (result) {
					ctx.result = result;
					tabs["forms-attachments"].bind(ctx);
				});
			};

			ui.bindDrawer(ctx.host, drawerId, function () {
				const next = Object.assign(
					{},
					editIndex != null ? ctx.result.forms[editIndex] : {},
					_collectDocumentDrawerData(body),
				);
				const forms = (ctx.result.forms || []).slice();
				if (editIndex != null) forms[editIndex] = next;
				else forms.push(next);
				ctx.result.forms = forms;
				const data = Object.assign({}, ctx.result.data, { forms: forms });
				cfgApi.saveSection(ctx.templateCode, "forms_and_attachments", data).then(function () {
					ui.closeDrawer(drawerId);
					frappe.show_alert({ message: __("Document saved."), indicator: "green" });
					rerender(ctx.result.previewIndex);
				});
			});
			_bindTabFooter(ctx, ctx.result.editable);
			ctx.host.addEventListener("click", function (event) {
				const previewBtn = event.target.closest("[data-kt-std-fa-preview-mode]");
				if (previewBtn) {
					const idx = parseInt(previewBtn.getAttribute("data-kt-std-fa-preview-mode"), 10);
					ctx.host.querySelectorAll("[data-kt-std-fa-preview-mode]").forEach(function (pill) {
						pill.classList.toggle(
							"is-active",
							parseInt(pill.getAttribute("data-kt-std-fa-preview-mode"), 10) === idx,
						);
					});
					ctx.result.previewIndex = idx;
					return;
				}
				const editBtn = event.target.closest("[data-kt-std-document-edit]");
				if (editBtn) {
					const idx = parseInt(editBtn.getAttribute("data-kt-std-document-edit"), 10);
					openEditor(ctx.result.forms[idx], idx);
					return;
				}
				const row = event.target.closest("[data-kt-std-document-row]");
				if (row && !event.target.closest("button")) {
					const idx = parseInt(row.getAttribute("data-kt-std-document-row"), 10);
					openEditor(ctx.result.forms[idx], idx);
					return;
				}
				const viewBtn = event.target.closest("[data-kt-std-document-view]");
				if (viewBtn) {
					const idx = parseInt(viewBtn.getAttribute("data-kt-std-document-view"), 10);
					openEditor(ctx.result.forms[idx], idx);
					return;
				}
				const replaceBtn = event.target.closest("[data-kt-std-document-replace]");
				if (replaceBtn) {
					frappe.show_alert({ message: __("Template replace is not available in this draft."), indicator: "orange" });
					return;
				}
				const evidenceBtn = event.target.closest("[data-kt-std-document-evidence]");
				if (evidenceBtn) {
					frappe.show_alert({ message: __("Evidence upload is not available in this draft."), indicator: "orange" });
					return;
				}
				const uploadBtn = event.target.closest("[data-kt-std-upload-template]");
				if (uploadBtn && !uploadBtn.disabled) {
					frappe.show_alert({ message: __("Upload template is not available in this draft."), indicator: "orange" });
					return;
				}
				const addSupplierBtn = event.target.closest("[data-kt-std-add-supplier-form]");
				if (addSupplierBtn && !addSupplierBtn.disabled) {
					frappe.show_alert({ message: __("Supplier form builder is not available in this draft."), indicator: "orange" });
					return;
				}
				const addCustomBtn = event.target.closest("[data-kt-std-add-custom-form]");
				if (addCustomBtn && !addCustomBtn.disabled) {
					frappe.show_alert({ message: __("Custom form builder is not available in this draft."), indicator: "orange" });
					return;
				}
				const editSupplierBtn = event.target.closest("[data-kt-std-supplier-form-edit]");
				if (editSupplierBtn) {
					frappe.show_alert({ message: __("Supplier form editor is not available in this draft."), indicator: "orange" });
					return;
				}
				if (
					event.target.closest("[data-kt-std-fa-upload-missing]") ||
					event.target.closest("[data-kt-std-fa-generate-missing]") ||
					event.target.closest("[data-kt-std-fa-mark-na]")
				) {
					frappe.show_alert({ message: __("Resolve missing requirements from Contract Terms or upload flow."), indicator: "blue" });
				}
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
				ctx.host.innerHTML = ui.evaluationSetupTabDocument({
					context: ui.evaluationSetupContextBanner(data),
					basis: ui.evaluationSetupBasisPanel(data, editable),
					bento: ui.evaluationSetupBentoGrid(data, stages),
					stages: ui.evaluationSetupStagesSection(data, stages, editable),
					drawer: ui.drawerHtml("stage-detail-drawer", __("Stage Configuration")),
					footer: ui.tabFooterHtml(editable),
				});
				return { payload: payload, data: data, stages: stages, editable: editable };
			});
		},
		bind: function (ctx) {
			const drawerId = "stage-detail-drawer";
			let editIndex = null;
			const body = ctx.host.querySelector(`[data-kt-std-drawer-body="${drawerId}"]`);

			function _collectStageDrawerData(drawerBody) {
				const out = {};
				if (!drawerBody) return out;
				drawerBody.querySelectorAll("[data-kt-std-drawer-field]").forEach(function (el) {
					const key = el.getAttribute("data-kt-std-drawer-field");
					if (!key) return;
					if (el.type === "checkbox") out[key] = el.checked;
					else out[key] = el.value;
				});
				return out;
			}

			const openEditor = function (row, index) {
				if (!body) return;
				editIndex = index == null ? null : index;
				body.innerHTML = ui.stageDetailDrawerBody(row || {}, ctx.result.editable);
				ui.openDrawer(drawerId);
			};

			const rerender = function () {
				return tabs["evaluation-setup"].render(ctx).then(function (result) {
					ctx.result = result;
					tabs["evaluation-setup"].bind(ctx);
				});
			};

			ui.bindDrawer(ctx.host, drawerId, function () {
				const next = Object.assign(
					{},
					editIndex != null ? ctx.result.stages[editIndex] : {},
					_collectStageDrawerData(body),
				);
				const stages = (ctx.result.stages || []).slice();
				if (editIndex != null) stages[editIndex] = next;
				else stages.push(next);
				ctx.result.stages = stages;
				const data = Object.assign({}, ctx.result.data, {
					stages: stages,
					governing_basis:
						(ctx.host.querySelector('[data-kt-std-field="governing_basis"]') || {}).value ||
						ctx.result.data.governing_basis,
				});
				cfgApi.saveSection(ctx.templateCode, "evaluation_setup", data).then(function () {
					ui.closeDrawer(drawerId);
					frappe.show_alert({ message: __("Stage saved."), indicator: "green" });
					rerender();
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
				const editBtn = event.target.closest("[data-kt-std-stage-edit]");
				if (editBtn) {
					const idx = parseInt(editBtn.getAttribute("data-kt-std-stage-edit"), 10);
					openEditor(ctx.result.stages[idx], idx);
					return;
				}
				const row = event.target.closest("[data-kt-std-stage-row]");
				if (row && !event.target.closest("button")) {
					const idx = parseInt(row.getAttribute("data-kt-std-stage-row"), 10);
					openEditor(ctx.result.stages[idx], idx);
					return;
				}
				const carryBtn = event.target.closest("[data-kt-std-stage-carry]");
				if (carryBtn && !carryBtn.disabled && ctx.result.editable) {
					const idx = parseInt(carryBtn.getAttribute("data-kt-std-stage-carry"), 10);
					const stages = (ctx.result.stages || []).slice();
					const current = Object.assign({}, stages[idx]);
					current.carry_forward = !carryBtn.classList.contains("is-on");
					stages[idx] = current;
					ctx.result.stages = stages;
					const data = Object.assign({}, ctx.result.data, { stages: stages });
					cfgApi.saveSection(ctx.templateCode, "evaluation_setup", data).then(function () {
						rerender();
					});
					return;
				}
				const addBtn = event.target.closest("[data-kt-std-add-stage]");
				if (addBtn && !addBtn.disabled) {
					openEditor(
						{
							evaluation_type: __("Pass / Fail"),
							sequence: (ctx.result.stages || []).length + 1,
							carry_forward: true,
						},
						null,
					);
				}
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
				ctx.host.innerHTML = ui.contractTermsTabDocument({
					context: ui.contractTermsContextBanner(data),
					governing: ui.contractTermsGoverningFormPanel(data, editable),
					matrix: ui.contractTermsMatrixSection(terms, editable),
					readiness: ui.contractTermsReadinessSection(readiness, data.readiness_issue_count),
					drawer: ui.drawerHtml("term-detail-drawer", __("Term Configuration")),
					footer: ui.tabFooterHtml(editable),
				});
				return { payload: payload, data: data, terms: terms, readiness: readiness, editable: editable };
			});
		},
		bind: function (ctx) {
			const drawerId = "term-detail-drawer";
			let editIndex = null;
			const body = ctx.host.querySelector(`[data-kt-std-drawer-body="${drawerId}"]`);

			function _collectTermDrawerData(drawerBody) {
				const out = {};
				if (!drawerBody) return out;
				drawerBody.querySelectorAll("[data-kt-std-drawer-field]").forEach(function (el) {
					const key = el.getAttribute("data-kt-std-drawer-field");
					if (!key) return;
					if (el.type === "checkbox") out[key] = el.checked;
					else out[key] = el.value;
				});
				if ("carries_to_contract" in out) {
					out.carries_to_contract = out.carries_to_contract ? __("Yes") : __("No");
				}
				if ("visible_to_supplier" in out) {
					out.visible_to_supplier = out.visible_to_supplier ? __("Yes") : __("No");
				}
				return out;
			}

			const openEditor = function (row, index) {
				if (!body) return;
				editIndex = index == null ? null : index;
				const drawerRow = Object.assign({}, row || {});
				if (typeof drawerRow.carries_to_contract === "string") {
					drawerRow.carries_to_contract =
						String(drawerRow.carries_to_contract).toLowerCase() === "yes" ||
						String(drawerRow.carries_to_contract).toLowerCase() === "conditional";
				}
				if (typeof drawerRow.visible_to_supplier === "string") {
					drawerRow.visible_to_supplier = String(drawerRow.visible_to_supplier).toLowerCase() === "yes";
				}
				body.innerHTML = ui.termDetailDrawerBody(drawerRow, ctx.result.editable);
				ui.openDrawer(drawerId);
			};

			const rerender = function () {
				return tabs["contract-terms"].render(ctx).then(function (result) {
					ctx.result = result;
					tabs["contract-terms"].bind(ctx);
				});
			};

			ui.bindDrawer(ctx.host, drawerId, function () {
				const next = Object.assign(
					{},
					editIndex != null ? ctx.result.terms[editIndex] : {},
					_collectTermDrawerData(body),
				);
				const terms = (ctx.result.terms || []).slice();
				if (editIndex != null) terms[editIndex] = next;
				else terms.push(next);
				ctx.result.terms = terms;
				const data = Object.assign({}, ctx.result.data, {
					terms: terms,
					governing_contract_form:
						(ctx.host.querySelector('[data-kt-std-field="governing_contract_form"]') || {}).value ||
						ctx.result.data.governing_contract_form,
				});
				cfgApi.saveSection(ctx.templateCode, "contract_terms", data).then(function () {
					ui.closeDrawer(drawerId);
					frappe.show_alert({ message: __("Term saved."), indicator: "green" });
					rerender();
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
				const editBtn = event.target.closest("[data-kt-std-term-edit]");
				if (editBtn) {
					const idx = parseInt(editBtn.getAttribute("data-kt-std-term-edit"), 10);
					openEditor(ctx.result.terms[idx], idx);
					return;
				}
				const row = event.target.closest("[data-kt-std-term-row]");
				if (row && !event.target.closest("button")) {
					const idx = parseInt(row.getAttribute("data-kt-std-term-row"), 10);
					openEditor(ctx.result.terms[idx], idx);
					return;
				}
				const overrideBtn = event.target.closest("[data-kt-std-term-override]");
				if (overrideBtn && !overrideBtn.disabled && ctx.result.editable) {
					const idx = parseInt(overrideBtn.getAttribute("data-kt-std-term-override"), 10);
					const terms = (ctx.result.terms || []).slice();
					const current = Object.assign({}, terms[idx]);
					current.override_allowed = !overrideBtn.classList.contains("is-on");
					terms[idx] = current;
					ctx.result.terms = terms;
					const data = Object.assign({}, ctx.result.data, { terms: terms });
					cfgApi.saveSection(ctx.templateCode, "contract_terms", data).then(function () {
						rerender();
					});
					return;
				}
				const addBtn = event.target.closest("[data-kt-std-add-term]");
				if (addBtn && !addBtn.disabled) {
					openEditor({ term_type: __("Financial"), required: __("Yes") }, null);
				}
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
				ctx.host.innerHTML = ui.rulesValidationsTabDocument({
					rules: ui.rulesValidationsRulesSection(rules, editable),
					validations: ui.rulesValidationsValidationsSection(validations),
					footer: ui.tabFooterHtml(editable),
				});
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
					const list = ctx.host.querySelector("[data-testid='kt-std-cfg-rv-rules-list']");
					if (list) {
						list.outerHTML = ui.rulesValidationsRuleListHtml(rules);
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
				const description = preview.description || __("Preview of configured STD sections.");
				ctx.host.innerHTML = ui.previewTabDocument({
					modes: ui.previewModeBar(modes, "tender_manager"),
					body: ui.auxSectionPanel({
						icon: "preview",
						title: __("Bundle Preview"),
						subtitle: description,
						testid: "kt-std-cfg-preview-body-panel",
						body: `<pre class="kt-std-cfg-readonly kt-std-cfg-aux-code" data-testid="kt-std-cfg-preview-body">${shared._escapeHtml(
							JSON.stringify(preview, null, 2),
						)}</pre>`,
					}),
					footer: ui.tabFooterHtml(false),
				});
				return { payload: payload, modes: modes };
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
				const issueTone = issues.length ? "warn" : "ok";
				ctx.host.innerHTML = ui.approvalTabDocument({
					summary: `<div class="kt-std-cfg-aux-status-banner kt-std-cfg-aux-status-banner--${issueTone}" data-testid="kt-std-cfg-approval-summary">
	<span class="material-symbols-outlined kt-std-icon">${issues.length ? "warning" : "check_circle"}</span>
	<div>
		<strong>${issues.length ? __("Validation issues found") : __("Validation passed")}</strong>
		<p>${__("Cross-section validation issues: {0}", [issues.length])}</p>
	</div>
</div>`,
					issues: ui.auxSectionPanel({
						icon: "playlist_add_check",
						title: __("Validation Issues"),
						subtitle: __("Resolve blocking issues before submitting for review."),
						testid: "kt-std-cfg-approval-issues-panel",
						body: ui.approvalIssueListHtml(issues),
					}),
					governance: ui.approvalGovernanceSection(),
					footer: ui.tabFooterHtml(editable),
				});
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
				ctx.host.innerHTML = ui.evidenceTabDocument({
					inventory: ui.evidenceInventorySection(rows),
					footer: ui.tabFooterHtml(false),
				});
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
				const jsonText = JSON.stringify(payload.package_json || payload, null, 2);
				const editable = !!(payload.editable || (ctx.context && ctx.context.can_edit_technical_json));
				ctx.host.innerHTML = ui.technicalJsonTabDocument({
					body: ui.technicalJsonSection(jsonText, { editable: editable }),
					footer: ui.tabFooterHtml(editable),
				});
				return {
					payload: payload,
					jsonText: jsonText,
					editable: editable,
				};
			});
		},
		bind: function (ctx) {
			const editable = !!(ctx.result && ctx.result.editable);
			_bindTabFooter(ctx, editable, {
				onSave: function () {
					const editor = ctx.host.querySelector("[data-kt-std-technical-json-editor]");
					if (!editor) return;
					let parsed;
					try {
						parsed = JSON.parse(editor.value || "{}");
					} catch (err) {
						const errEl = ctx.host.querySelector("[data-testid='kt-std-cfg-technical-json-error']");
						if (errEl) {
							errEl.textContent = __("Invalid JSON: {0}", [String(err.message || err)]);
							errEl.classList.remove("hidden");
						}
						return;
					}
					cfgApi.saveTechnicalJson(ctx.templateCode, parsed).then(function (res) {
						ctx.result.jsonText = JSON.stringify(res.package_json || parsed, null, 2);
						ctx.result.payload = res;
						const errEl = ctx.host.querySelector("[data-testid='kt-std-cfg-technical-json-error']");
						if (errEl) {
							errEl.textContent = "";
							errEl.classList.add("hidden");
						}
						if (editor) {
							editor.value = ctx.result.jsonText;
						}
						frappe.show_alert({
							message: __("Technical package JSON saved."),
							indicator: "green",
						});
					});
				},
			});
			const validateBtn = ctx.host.querySelector("[data-kt-std-technical-json-validate]");
			if (validateBtn) {
				validateBtn.addEventListener("click", function () {
					const editor = ctx.host.querySelector("[data-kt-std-technical-json-editor]");
					const errEl = ctx.host.querySelector("[data-testid='kt-std-cfg-technical-json-error']");
					if (!editor) return;
					try {
						JSON.parse(editor.value || "{}");
						if (errEl) {
							errEl.textContent = __("JSON is valid.");
							errEl.classList.remove("hidden");
						}
					} catch (err) {
						if (errEl) {
							errEl.textContent = __("Invalid JSON: {0}", [String(err.message || err)]);
							errEl.classList.remove("hidden");
						}
					}
				});
			}
			const revertBtn = ctx.host.querySelector("[data-kt-std-technical-json-revert]");
			if (revertBtn) {
				revertBtn.addEventListener("click", function () {
					const editor = ctx.host.querySelector("[data-kt-std-technical-json-editor]");
					const errEl = ctx.host.querySelector("[data-testid='kt-std-cfg-technical-json-error']");
					if (editor && ctx.result && ctx.result.jsonText) {
						editor.value = ctx.result.jsonText;
					}
					if (errEl) {
						errEl.textContent = "";
						errEl.classList.add("hidden");
					}
				});
			}
			const saveBtn = ctx.host.querySelector("[data-kt-std-technical-json-save]");
			if (saveBtn) {
				saveBtn.addEventListener("click", function () {
					const footerSave = ctx.host.querySelector("[data-kt-std-footer-save]");
					if (footerSave) footerSave.click();
				});
			}
		},
	};
})();
