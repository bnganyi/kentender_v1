/* global frappe */
// STD-CFG-0230 — mockup-faithful markup helpers (shared across all configurator tabs).
frappe.provide("kentender_procurement.std_configurator_ui");

(function () {
	"use strict";

	const shared = kentender_procurement.std_config_shared;
	const ui = kentender_procurement.std_configurator_ui;

	const CATEGORY_OPTIONS = Object.freeze([
		{ value: "Works", label: __("Works") },
		{ value: "Goods", label: __("Goods") },
		{ value: "Services", label: __("Services") },
		{ value: "Consultancy", label: __("Consultancy") },
	]);

	const METHOD_OPTIONS = Object.freeze([
		{ value: "Open Tender", label: __("Open Tender") },
		{ value: "RFQ", label: __("RFQ") },
		{ value: "Restricted Tender", label: __("Restricted Tender") },
	]);

	const FUNDING_OPTIONS = Object.freeze([
		{ key: "gok_exchequer", label: __("GoK / Exchequer") },
		{ key: "internal_revenue", label: __("Internal Revenue") },
		{ key: "donor_funded", label: __("Donor Funded") },
		{ key: "mixed_funding", label: __("Mixed Funding") },
	]);

	ui.tabFooterHtml = function tabFooterHtml(editable) {
		const disabled = editable ? "" : " disabled";
		return `
<div class="kt-std-cfg-tab-footer" data-testid="kt-std-cfg-footer-actions">
	<div class="kt-std-cfg-tab-footer__left">
		<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--ghost" data-kt-std-footer-cancel${disabled}>
			<span class="material-symbols-outlined kt-std-icon">delete_sweep</span>${__("Cancel Draft")}
		</button>
	</div>
	<div class="kt-std-cfg-tab-footer__right">
		<button type="button" class="kt-std-cfg-btn" data-kt-std-footer-save${disabled}>${__("Save Draft")}</button>
		<button type="button" class="kt-std-cfg-btn" data-kt-std-footer-preview>
			<span class="material-symbols-outlined kt-std-icon">visibility</span>${__("Preview")}
		</button>
		<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-footer-submit${disabled}>
			${__("Submit for Review")}<span class="material-symbols-outlined kt-std-icon">send</span>
		</button>
	</div>
</div>`;
	};

	ui.bindFooter = function bindFooter(root, handlers) {
		if (!root || !handlers) return;
		const map = {
			"[data-kt-std-footer-cancel]": handlers.onCancel,
			"[data-kt-std-footer-save]": handlers.onSave,
			"[data-kt-std-footer-preview]": handlers.onPreview,
			"[data-kt-std-footer-submit]": handlers.onSubmit,
		};
		Object.keys(map).forEach(function (selector) {
			const btn = root.querySelector(selector);
			if (btn && typeof map[selector] === "function") {
				btn.addEventListener("click", map[selector]);
			}
		});
	};

	ui.identityCard = function identityCard(title, refCode, bodyHtml) {
		return `
<div class="kt-std-cfg-block" data-testid="kt-std-cfg-identity-card">
	<div class="kt-std-cfg-block__head">
		<h3 class="kt-std-cfg-block__title">
			<span class="material-symbols-outlined kt-std-icon">info</span>${shared._escapeHtml(title)}
		</h3>
		<span class="kt-std-cfg-ref-badge">REF: ${shared._escapeHtml(refCode || "—")}</span>
	</div>
	<div class="kt-std-cfg-block__body">${bodyHtml}</div>
</div>`;
	};

	ui.fieldText = function fieldText(key, label, value, opts) {
		const options = opts || {};
		const spanClass = options.full ? "kt-std-cfg-form__full" : options.half ? "kt-std-cfg-form__half" : "";
		const disabled = options.disabled ? " disabled" : "";
		const type = options.type || "text";
		return `
<div class="kt-std-cfg-field ${spanClass}">
	<label class="kt-std-cfg-field__label">${label}</label>
	<input class="kt-std-cfg-input" type="${type}" data-kt-std-field="${key}" value="${shared._escapeHtml(value || "")}"${disabled} />
</div>`;
	};

	ui.fieldTextarea = function fieldTextarea(key, label, value, opts) {
		const options = opts || {};
		const disabled = options.disabled ? " disabled" : "";
		return `
<div class="kt-std-cfg-field kt-std-cfg-form__full">
	<label class="kt-std-cfg-field__label">${label}</label>
	<textarea class="kt-std-cfg-textarea" data-kt-std-field="${key}" rows="4"${disabled}>${shared._escapeHtml(value || "")}</textarea>
</div>`;
	};

	ui.fieldSelect = function fieldSelect(key, label, value, selectOptions, opts) {
		const options = opts || {};
		const spanClass = options.half ? "kt-std-cfg-form__half" : "";
		const disabled = options.disabled ? " disabled" : "";
		const optsHtml = (selectOptions || [])
			.map(function (opt) {
				const sel = String(value) === String(opt.value) ? " selected" : "";
				return `<option value="${shared._escapeHtml(opt.value)}"${sel}>${opt.label}</option>`;
			})
			.join("");
		return `
<div class="kt-std-cfg-field ${spanClass}">
	<label class="kt-std-cfg-field__label">${label}</label>
	<div class="kt-std-cfg-select-wrap">
		<select class="kt-std-cfg-select" data-kt-std-field="${key}"${disabled}>${optsHtml}</select>
		<span class="material-symbols-outlined kt-std-icon">expand_more</span>
	</div>
</div>`;
	};

	ui.fieldVersion = function fieldVersion(key, label, value, opts) {
		const disabled = opts && opts.disabled ? " disabled" : "";
		return `
<div class="kt-std-cfg-field kt-std-cfg-form__half">
	<label class="kt-std-cfg-field__label">${label}</label>
	<div class="kt-std-cfg-version-input">
		<span class="kt-std-cfg-version-input__prefix">v</span>
		<input class="kt-std-cfg-input" type="text" data-kt-std-field="${key}" value="${shared._escapeHtml(value || "")}"${disabled} />
	</div>
</div>`;
	};

	ui.fieldStatus = function fieldStatus(label, statusText, lifecycleStatus) {
		const lc = String(lifecycleStatus || statusText || "").toLowerCase();
		const dotClass = lc === "active" ? " kt-std-cfg-status-readout__dot--active" : "";
		return `
<div class="kt-std-cfg-field kt-std-cfg-form__half">
	<label class="kt-std-cfg-field__label">${label}</label>
	<div class="kt-std-cfg-status-readout">
		<span class="kt-std-cfg-status-readout__dot${dotClass}"></span>
		<strong>${shared._escapeHtml(statusText || __("Draft"))}</strong>
	</div>
</div>`;
	};

	ui.fieldFunding = function fieldFunding(selectedKeys, editable) {
		const selected = selectedKeys || {};
		const disabled = editable ? "" : " disabled";
		const boxes = FUNDING_OPTIONS.map(function (opt) {
			const checked = selected[opt.key] ? " checked" : "";
			return `
<label class="kt-std-cfg-checkbox">
	<input type="checkbox" data-kt-std-funding="${opt.key}"${checked}${disabled} />
	<span>${opt.label}</span>
</label>`;
		}).join("");
		return `
<div class="kt-std-cfg-field kt-std-cfg-form__full">
	<label class="kt-std-cfg-field__label">${__("Funding Source")}</label>
	<div class="kt-std-cfg-checkbox-grid">${boxes}</div>
</div>`;
	};

	ui.guidanceRow = function guidanceRow(progressPct, sectionIndex, sectionTotal) {
		const pct = Math.max(0, Math.min(100, progressPct || 0));
		return `
<div class="kt-std-cfg-guidance">
	<div class="kt-std-cfg-progress-card" data-testid="kt-std-cfg-progress-card">
		<div>
			<p class="kt-std-cfg-progress-card__title">${__("Configuration Progress")}</p>
			<p class="kt-std-cfg-progress-card__sub">${__("Overview & Identity {0}% complete", [pct >= 15 ? 100 : pct])}</p>
		</div>
		<div>
			<div class="kt-std-cfg-progress-card__bar"><span style="width:${pct}%"></span></div>
			<p class="kt-std-cfg-progress-card__meta">${__(
				"Section {0} of {1} Sections",
				[sectionIndex || 1, sectionTotal || 11],
			)}</p>
		</div>
	</div>
	<div class="kt-std-cfg-tip-card">
		<div class="kt-std-cfg-tip-card__icon"><span class="material-symbols-outlined kt-std-icon">lightbulb</span></div>
		<div>
			<p class="kt-std-cfg-tip-card__title">${__("Expert Tip: Version Control")}</p>
			<p class="kt-std-cfg-tip-card__body">${__(
				"Use logical versioning (v2.1) to track minor updates. Significant structural changes to evaluation criteria or document sections should typically trigger a major version update (e.g., v3.0) to maintain audit trails.",
			)}</p>
		</div>
	</div>
</div>`;
	};

	ui.appliesToSection = function appliesToSection(lines) {
		const items = (lines || []).map(function (line) {
			return `<li>${shared._escapeHtml(line)}</li>`;
		}).join("");
		return `
<div data-testid="kt-std-cfg-applies-to-preview">
	<div class="kt-std-cfg-applies-head">
		<h3>${__("Applies To Preview")}</h3>
		<span>(${__("Generated based on current rules")})</span>
	</div>
	<div class="kt-std-cfg-applies-box">
		<p><strong>${__("This STD will apply to:")}</strong></p>
		<ul class="kt-std-cfg-applies-list">${items || `<li>${__("Configure applicability rules to generate preview.")}</li>`}</ul>
	</div>
</div>`;
	};

	ui.appliesToPreview = function appliesToPreview(applicability) {
		const data = applicability || {};
		const rules = Array.isArray(data.rules) ? data.rules : [];
		if (rules.length) {
			return rules
				.map(function (rule) {
					const parts = [
						rule.procurement_category,
						rule.procurement_method,
						rule.contract_type || rule.works_subtype,
						rule.entity_scope,
						rule.funding_source,
						rule.min_value ? __("KES above {0}", [rule.min_value]) : "",
						rule.lot_support ? __("Lot bidding allowed") : "",
					].filter(Boolean);
					return parts.join(" · ") || rule.name || rule.code;
				})
				.filter(Boolean);
		}
		const defaults = [
			data.procurement_category && data.procurement_method
				? `${data.procurement_category} procurement using ${data.procurement_method}`
				: "",
			data.works_subtype ? `${data.works_subtype} subtype` : "",
			data.entity_scope ? `${data.entity_scope} procuring entities` : __("All procuring entities"),
			data.funding_source ? `${data.funding_source}-funded tenders` : "",
			data.min_value ? __("Package value from KES {0} upward", [data.min_value]) : "",
			data.lot_support ? __("Lot bidding allowed") : "",
		].filter(Boolean);
		if (defaults.length) return defaults;
		return [__("Configure applicability rules to generate preview.")];
	};

	ui.collectFields = function collectFields(host, keys) {
		const out = {};
		(keys || []).forEach(function (key) {
			const el = host.querySelector(`[data-kt-std-field="${key}"]`);
			if (!el) return;
			if (el.type === "checkbox") out[key] = el.checked;
			else out[key] = el.value;
		});
		return out;
	};

	ui.collectFunding = function collectFunding(host) {
		const out = {};
		host.querySelectorAll("[data-kt-std-funding]").forEach(function (el) {
			out[el.getAttribute("data-kt-std-funding")] = el.checked;
		});
		return out;
	};

	ui.lifecycleBadge = function lifecycleBadge(lifecycleStatus) {
		const lc = String(lifecycleStatus || "Draft");
		if (lc.toLowerCase() === "active") return __("ACTIVE");
		if (lc.toLowerCase().includes("submitted") || lc.toLowerCase().includes("review")) return __("SUBMITTED");
		return __("DRAFT");
	};

	ui.userInitials = function userInitials() {
		const user = (frappe.boot && frappe.boot.user) || {};
		const name = String(user.full_name || user.name || "AD").trim();
		const parts = name.split(/\s+/).filter(Boolean);
		if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
		return name.slice(0, 2).toUpperCase();
	};

	ui.navyBanner = function navyBanner(title, summaryText) {
		return `
<div class="kt-std-cfg-navy-banner" data-testid="kt-std-cfg-applicability-banner">
	<span class="kt-std-cfg-navy-banner__watermark material-symbols-outlined kt-std-icon">verified_user</span>
	<h3 class="kt-std-cfg-navy-banner__title">${shared._escapeHtml(title)}</h3>
	<div class="kt-std-cfg-navy-banner__chip">
		<span class="material-symbols-outlined kt-std-icon">info</span>
		<p>${__("Applies to:")} <strong>${shared._escapeHtml(summaryText || __("Not configured"))}</strong></p>
	</div>
</div>`;
	};

	ui.conflictCheck = function conflictCheck(summaryText) {
		return `
<div class="kt-std-cfg-conflict" data-testid="kt-std-cfg-conflict-check">
	<div>
		<div class="kt-std-cfg-conflict__head">
			<span class="material-symbols-outlined kt-std-icon">rule_settings</span>${__("Rule Conflict Check")}
		</div>
		<p class="kt-std-cfg-conflict__lead">${__("No conflicting active STD found for:")}</p>
		<p class="kt-std-cfg-conflict__mono">${shared._escapeHtml(summaryText || __("Configure rules to run conflict check."))}</p>
	</div>
	<button type="button" class="kt-std-cfg-conflict__copy" aria-label="${__("Copy")}">
		<span class="material-symbols-outlined kt-std-icon">content_copy</span>
	</button>
</div>`;
	};

	ui.sectionCard = function sectionCard(icon, title, bodyHtml, testid) {
		const tid = testid ? ` data-testid="${testid}"` : "";
		return `
<section class="kt-std-cfg-section-card"${tid}>
	<h4 class="kt-std-cfg-section-card__title">
		<span class="material-symbols-outlined kt-std-icon">${icon}</span>${shared._escapeHtml(title)}
	</h4>
	${bodyHtml}
</section>`;
	};

	ui.toolbar = function toolbar(leftHtml, rightHtml) {
		return `
<div class="kt-std-cfg-toolbar">
	<div class="kt-std-cfg-toolbar__left">${leftHtml || ""}</div>
	<div class="kt-std-cfg-toolbar__right">${rightHtml || ""}</div>
</div>`;
	};

	ui.previewPills = function previewPills(labels, activeIndex) {
		return `<div class="kt-std-cfg-preview-pills">${(labels || [])
			.map(function (label, idx) {
				const active = idx === (activeIndex || 0) ? " is-active" : "";
				return `<button type="button" class="kt-std-cfg-pill${active}">${shared._escapeHtml(label)}</button>`;
			})
			.join("")}</div>`;
	};

	ui.dataTable = function dataTable(columns, rows, emptyMsg, testid) {
		const headers = (columns || [])
			.map(function (col) {
				return `<th>${col.label}</th>`;
			})
			.join("");
		const body =
			rows && rows.length
				? rows
						.map(function (row, idx) {
							const cells = columns
								.map(function (col) {
									const val = row && row[col.key] != null ? row[col.key] : "";
									return `<td>${shared._escapeHtml(String(val))}</td>`;
								})
								.join("");
							return `<tr data-row-index="${idx}">${cells}<td class="kt-std-cfg-table__actions"><button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--sm" data-kt-std-edit-row="${idx}">${__(
								"Edit",
							)}</button></td></tr>`;
						})
						.join("")
				: `<tr><td colspan="${(columns || []).length + 1}" class="kt-std-cfg-empty">${emptyMsg}</td></tr>`;
		return `<div class="kt-std-cfg-table-wrap"><table class="kt-std-cfg-data-table" data-testid="${testid}"><thead><tr>${headers}<th>${__(
			"Actions",
		)}</th></tr></thead><tbody>${body}</tbody></table></div>`;
	};

	ui.groupTable = function groupTable(groupLabel, columns, rows, addLabel, groupKey) {
		const headers = columns
			.map(function (col) {
				return `<th>${col.label}</th>`;
			})
			.join("");
		const body =
			rows && rows.length
				? rows
						.map(function (row, idx) {
							const cells = columns
								.map(function (col) {
									const val = row && row[col.key] != null ? row[col.key] : "";
									return `<td>${shared._escapeHtml(String(val))}</td>`;
								})
								.join("");
							return `<tr data-field-index="${idx}">${cells}<td><button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--sm" data-kt-std-field-edit="${idx}">${__(
								"Edit",
							)}</button></td></tr>`;
						})
						.join("")
				: `<tr><td colspan="${columns.length + 1}" class="kt-std-cfg-empty">${__("No fields in this group yet.")}</td></tr>`;
		return `
<div class="kt-std-cfg-group">
	<div class="kt-std-cfg-group__head">
		<span>${shared._escapeHtml(groupLabel)}</span>
		<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--sm" data-kt-std-add-field="${groupKey}">${shared._escapeHtml(
			addLabel || __("Add Field"),
		)}</button>
	</div>
	<div class="kt-std-cfg-table-wrap"><table class="kt-std-cfg-data-table"><thead><tr>${headers}<th></th></tr></thead><tbody>${body}</tbody></table></div>
</div>`;
	};

	ui.METHOD_OPTIONS = METHOD_OPTIONS;
	ui.FUNDING_OPTIONS = FUNDING_OPTIONS;
	ui.ENTITY_SCOPE_OPTIONS = Object.freeze([
		"All Entities",
		"Specific MDA",
		"Counties Only",
		"State Corporations",
	]);

	// Drawer helpers
	ui.drawerHtml = function drawerHtml(id, title) {
		const drawerId = shared._escapeHtml(id || "kt-std-cfg-drawer");
		return `
<div class="kt-std-cfg-drawer-backdrop" data-kt-std-drawer-backdrop="${drawerId}"></div>
<aside class="kt-std-cfg-drawer" id="${drawerId}" data-testid="${drawerId}" aria-hidden="true">
	<div class="kt-std-cfg-drawer__header">
		<h3 class="kt-std-cfg-block__title">${shared._escapeHtml(title || "")}</h3>
		<button type="button" class="kt-std-cfg-btn" data-kt-std-drawer-close="${drawerId}">${__("Close")}</button>
	</div>
	<div class="kt-std-cfg-drawer__body" data-kt-std-drawer-body="${drawerId}"></div>
	<div class="kt-std-cfg-drawer__footer">
		<button type="button" class="kt-std-cfg-btn" data-kt-std-drawer-close="${drawerId}">${__("Cancel")}</button>
		<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-drawer-save="${drawerId}">${__(
			"Save",
		)}</button>
	</div>
</aside>`;
	};

	ui.openDrawer = function openDrawer(id) {
		const drawer = document.getElementById(id);
		const backdrop = document.querySelector(`[data-kt-std-drawer-backdrop="${id}"]`);
		if (drawer) {
			drawer.classList.add("is-open");
			drawer.setAttribute("aria-hidden", "false");
		}
		if (backdrop) backdrop.classList.add("is-open");
	};

	ui.closeDrawer = function closeDrawer(id) {
		const drawer = document.getElementById(id);
		const backdrop = document.querySelector(`[data-kt-std-drawer-backdrop="${id}"]`);
		if (drawer) {
			drawer.classList.remove("is-open");
			drawer.setAttribute("aria-hidden", "true");
		}
		if (backdrop) backdrop.classList.remove("is-open");
	};

	ui.bindDrawer = function bindDrawer(host, id, onSave) {
		if (!host) return;
		host.addEventListener("click", function (event) {
			if (event.target.closest(`[data-kt-std-drawer-close="${id}"]`)) {
				ui.closeDrawer(id);
				return;
			}
			if (event.target.closest(`[data-kt-std-drawer-backdrop="${id}"]`)) {
				ui.closeDrawer(id);
				return;
			}
			if (event.target.closest(`[data-kt-std-drawer-save="${id}"]`) && typeof onSave === "function") {
				onSave();
			}
		});
	};
})();
