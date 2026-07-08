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
		{ value: "RFQ", label: __("Request for Quotation") },
		{ value: "Restricted Tender", label: __("Restricted Tender") },
		{ value: "Direct Procurement", label: __("Direct Procurement") },
	]);

	const CONTRACT_TYPE_OPTIONS = Object.freeze([
		{ value: "Works Contract", label: __("Works Contract") },
		{ value: "Service Level Agreement", label: __("Service Level Agreement") },
		{ value: "Framework Agreement", label: __("Framework Agreement") },
	]);

	const WORKS_SUBTYPE_OPTIONS = Object.freeze([
		{ value: "Building Works", label: __("Building Works") },
		{ value: "Civil Engineering", label: __("Civil Engineering") },
		{ value: "Electrical Installations", label: __("Electrical Installations") },
		{ value: "Plumbing & Mechanical", label: __("Plumbing & Mechanical") },
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

	ui.fieldDate = function fieldDate(key, label, value, opts) {
		const options = opts || {};
		const spanClass = options.half ? "kt-std-cfg-form__half" : "";
		const disabled = options.disabled ? " disabled" : "";
		return `
<div class="kt-std-cfg-field ${spanClass}">
	<label class="kt-std-cfg-field__label">${label}</label>
	<div class="kt-std-cfg-date-wrap">
		<input class="kt-std-cfg-input" type="date" data-kt-std-field="${key}" value="${shared._escapeHtml(value || "")}"${disabled} />
		<span class="material-symbols-outlined kt-std-icon">calendar_today</span>
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
		<div class="kt-std-cfg-progress-card__glow" aria-hidden="true"></div>
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

	function _formatKesAmount(value) {
		const raw = String(value || "").replace(/,/g, "").trim();
		const num = Number(raw);
		if (!raw || Number.isNaN(num)) return String(value || "");
		return num.toLocaleString("en-KE");
	}

	function _fundingPreviewLine(sources) {
		const funding = sources || {};
		const parts = [];
		if (funding.gok_exchequer) parts.push(__("GoK-funded"));
		if (funding.internal_revenue) parts.push(__("internal revenue-funded"));
		if (funding.donor_funded) parts.push(__("donor-funded"));
		if (funding.mixed_funding) parts.push(__("mixed funding"));
		if (!parts.length) return "";
		if (parts.length === 1) return `${parts[0]} ${__("tenders")}`;
		const last = parts.pop();
		return `${parts.join(", ")} ${__("or")} ${last} ${__("tenders")}`;
	}

	function _entityScopeLine(scope) {
		const normalized = String(scope || "").trim();
		if (!normalized || normalized === "All Entities") return __("All procuring entities");
		return `${normalized} ${__("procuring entities")}`;
	}

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
		<button type="button" class="kt-std-cfg-applies-copy" data-testid="kt-std-cfg-applies-copy" data-kt-std-applies-copy aria-label="${__(
			"Copy preview",
		)}">
			<span class="material-symbols-outlined kt-std-icon">content_copy</span>
		</button>
		<p><strong>${__("This STD will apply to:")}</strong></p>
		<ul class="kt-std-cfg-applies-list">${items || `<li>${__("Configure applicability rules to generate preview.")}</li>`}</ul>
	</div>
	<p class="kt-std-cfg-applies-footnote">${__(
		"This reinforces that the configuration is understandable.",
	)}</p>
</div>`;
	};

	ui.bindAppliesCopy = function bindAppliesCopy(host) {
		if (!host) return;
		const btn = host.querySelector("[data-kt-std-applies-copy]");
		if (!btn) return;
		btn.addEventListener("click", function () {
			const list =
				host.querySelector(".kt-std-cfg-applies-panel__list") || host.querySelector(".kt-std-cfg-applies-list");
			const lines = list ? list.querySelectorAll("li") : [];
			const text = Array.from(lines)
				.map(function (li) {
					const span = li.querySelector("span:last-child");
					return ((span && span.textContent) || li.textContent || "").trim();
				})
				.filter(Boolean)
				.join("\n");
			const done = function () {
				frappe.show_alert({ message: __("Applies To preview copied."), indicator: "green" });
			};
			if (navigator.clipboard && navigator.clipboard.writeText) {
				navigator.clipboard.writeText(text).then(done).catch(done);
				return;
			}
			done();
		});
	};

	ui.appliesToPreview = function appliesToPreview(applicability) {
		const data = applicability || {};
		const lines = [
			data.procurement_category && data.procurement_method
				? `${data.procurement_category} ${__("procurement using")} ${data.procurement_method}`
				: "",
			data.works_subtype
				? `${data.works_subtype} ${__("subtype")}`
				: data.contract_type
					? `${data.contract_type} ${__("subtype")}`
					: "",
			_entityScopeLine(data.entity_scope),
			_fundingPreviewLine(data.funding_sources) ||
				(data.funding_source ? `${data.funding_source}-${__("funded tenders")}` : ""),
			data.min_value ? __("Package value from KES {0} upward", [_formatKesAmount(data.min_value)]) : "",
			data.lot_support ? __("Lot bidding allowed") : "",
		].filter(Boolean);
		if (lines.length) return lines;
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
	<span class="kt-std-cfg-navy-banner__watermark material-symbols-outlined kt-std-icon" aria-hidden="true">verified_user</span>
	<div class="kt-std-cfg-navy-banner__body">
		<h3 class="kt-std-cfg-navy-banner__title" data-testid="kt-std-cfg-applicability-banner-title">${shared._escapeHtml(title)}</h3>
		<div class="kt-std-cfg-navy-banner__chip">
			<span class="material-symbols-outlined kt-std-icon">info</span>
			<p>${__("Applies to:")} <strong>${shared._escapeHtml(summaryText || __("Not configured"))}</strong></p>
		</div>
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
	<button type="button" class="kt-std-cfg-conflict__copy" data-testid="kt-std-cfg-conflict-copy" data-kt-std-conflict-copy aria-label="${__(
			"Copy conflict summary",
		)}">
		<span class="material-symbols-outlined kt-std-icon">content_copy</span>
	</button>
</div>`;
	};

	ui.applicabilitySummaryLine = function applicabilitySummaryLine(data) {
		const applicability = data || {};
		const parts = [
			applicability.procurement_category,
			applicability.procurement_method,
			applicability.works_subtype || applicability.contract_type,
			applicability.entity_scope === "All Entities" || !applicability.entity_scope
				? __("All Entities")
				: applicability.entity_scope,
			applicability.min_value
				? __("KES above {0}", [_formatKesAmount(applicability.min_value)])
				: __("KES above threshold"),
		].filter(Boolean);
		return parts.join(" · ");
	};

	ui.testApplicabilitySection = function testApplicabilitySection(testCase, data, applies) {
		const tc = testCase || {};
		const source = data || {};
		const badgeIcon = applies === false ? "cancel" : "check_circle";
		const badgeText = applies === false ? __("This STD does not apply.") : __("This STD applies.");
		const valueDisplay = tc.test_value
			? `KES ${_formatKesAmount(tc.test_value)}`
			: source.min_value
				? `KES ${_formatKesAmount(source.min_value)}`
				: "—";
		return `
<section class="kt-std-cfg-test-section" data-testid="kt-std-cfg-test-section">
	<div class="kt-std-cfg-test-head">
		<h4 class="kt-std-cfg-section-card__title">
			<span class="material-symbols-outlined kt-std-icon">science</span>${__("Test Applicability")}
		</h4>
		<span class="kt-std-cfg-test-badge" data-testid="kt-std-cfg-test-badge">
			<span class="material-symbols-outlined kt-std-icon">${badgeIcon}</span>${badgeText}
		</span>
	</div>
	<div class="kt-std-cfg-test-grid">
		<div class="kt-std-cfg-test-grid__cell"><p>${__("Package Category")}</p><p>${shared._escapeHtml(tc.test_category || source.procurement_category || "—")}</p></div>
		<div class="kt-std-cfg-test-grid__cell"><p>${__("Method")}</p><p>${shared._escapeHtml(tc.test_method || source.procurement_method || "—")}</p></div>
		<div class="kt-std-cfg-test-grid__cell"><p>${__("Subtype")}</p><p>${shared._escapeHtml(tc.test_subtype || source.works_subtype || "—")}</p></div>
		<div class="kt-std-cfg-test-grid__cell"><p>${__("Entity")}</p><p>${shared._escapeHtml(tc.test_entity || (source.entity_codes && source.entity_codes[0]) || source.entity_scope || "—")}</p></div>
		<div class="kt-std-cfg-test-grid__cell kt-std-cfg-test-grid__cell--mono"><p>${__("Value")}</p><p>${shared._escapeHtml(valueDisplay)}</p></div>
		<div class="kt-std-cfg-test-grid__cell"><p>${__("Funding Source")}</p><p>${shared._escapeHtml(tc.test_funding || source.funding_source || "—")}</p></div>
		<div class="kt-std-cfg-test-grid__actions">
			<button type="button" class="kt-std-cfg-test-run-link" data-kt-std-run-test>
				<span class="material-symbols-outlined kt-std-icon">refresh</span>${__("Run New Test")}
			</button>
		</div>
	</div>
</section>`;
	};

	ui.applicabilityLayout = function applicabilityLayout(leftHtml, rightHtml) {
		return `
<div class="kt-std-cfg-applicability-layout">
	<div class="kt-std-cfg-applicability-layout__main">${leftHtml || ""}</div>
	<div class="kt-std-cfg-applicability-layout__side">${rightHtml || ""}</div>
</div>`;
	};

	/** Full Applicability tab canvas — mirrors 3. applicability/code.html section order. */
	ui.applicabilityTabDocument = function applicabilityTabDocument(parts) {
		const p = parts || {};
		return `
<section class="kt-std-cfg-tab-stack" data-testid="kt-std-cfg-applicability">
	${p.banner || ""}
	${p.conflict || ""}
	${p.test || ""}
	${p.formLayout || ""}
	${p.appliesPreview || ""}
	${p.footer || ""}
</section>`;
	};

	ui.fieldFundingCards = function fieldFundingCards(selectedKeys, editable) {
		const selected = selectedKeys || {};
		const disabled = editable ? "" : " disabled";
		const cards = FUNDING_OPTIONS.map(function (opt) {
			const checked = selected[opt.key] ? " checked" : "";
			return `
<label class="kt-std-cfg-funding-card">
	<input type="checkbox" data-kt-std-funding="${opt.key}"${checked}${disabled} />
	<span>${opt.label}</span>
</label>`;
		}).join("");
		return `
<div class="kt-std-cfg-field kt-std-cfg-form__full">
	<label class="kt-std-cfg-field__label">${__("Funding Source")}</label>
	<div class="kt-std-cfg-funding-cards">${cards}</div>
</div>`;
	};

	ui.entityScopeBlock = function entityScopeBlock(data, editable) {
		const scope = String((data && data.entity_scope) || "All Entities");
		const entityCodes = Array.isArray(data && data.entity_codes) ? data.entity_codes : [];
		const pills = (ui.ENTITY_SCOPE_OPTIONS || []).map(function (opt) {
			const active = scope === opt ? " is-active" : "";
			return `<button type="button" class="kt-std-cfg-pill${active}" data-kt-std-entity-scope="${shared._escapeHtml(opt)}"${
				editable ? "" : " disabled"
			}>${shared._escapeHtml(opt)}</button>`;
		}).join("");
		const chips = entityCodes
			.map(function (code) {
				return `<span class="kt-std-cfg-entity-chip" data-kt-std-entity-chip="${shared._escapeHtml(code)}">
					${shared._escapeHtml(code)}
					<button type="button" class="kt-std-cfg-entity-chip__remove" data-kt-std-entity-remove="${shared._escapeHtml(code)}" aria-label="${__(
						"Remove",
					)}"><span class="material-symbols-outlined kt-std-icon">close</span></button>
				</span>`;
			})
			.join("");
		const showPicker = scope === "Specific MDA";
		return `
<div class="kt-std-cfg-entity-scope-block">
	<div class="kt-std-cfg-field kt-std-cfg-form__full">
		<label class="kt-std-cfg-field__label">${__("Entity Scope")}</label>
		<div class="kt-std-cfg-preview-pills" data-testid="kt-std-cfg-entity-scope-pills">${pills}</div>
		<input type="hidden" data-kt-std-field="entity_scope" value="${shared._escapeHtml(scope)}" />
	</div>
	<div class="kt-std-cfg-entity-picker${showPicker ? " is-visible" : ""}" data-testid="kt-std-cfg-entity-picker">
		<label class="kt-std-cfg-field__label">${__("Select Procuring Entities")}</label>
		<div class="kt-std-cfg-entity-picker__box">
			${chips}
			<input class="kt-std-cfg-entity-picker__input" type="text" data-kt-std-entity-input placeholder="${__(
				"Search and add entities...",
			)}"${editable ? "" : " disabled"} />
		</div>
	</div>
</div>`;
	};

	ui.financialLimitsPanel = function financialLimitsPanel(data, editable) {
		const source = data || {};
		const currency = source.currency || "KES";
		const minDisplay = source.min_value
			? __("KES {0} and above", [_formatKesAmount(source.min_value)])
			: __("Not set");
		const maxDisplay = source.max_value ? __("KES {0}", [_formatKesAmount(source.max_value)]) : __("No upper limit");
		const lotChecked = source.lot_support ? " checked" : "";
		const disabled = editable ? "" : " disabled";
		return `
<div class="kt-std-cfg-financial-panel" data-testid="kt-std-cfg-financial-limits">
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Currency")}</label>
		<div class="kt-std-cfg-financial-readout">
			<span class="material-symbols-outlined kt-std-icon">payments</span>
			<input type="hidden" data-kt-std-field="currency" value="${shared._escapeHtml(currency)}" />
			<span>${shared._escapeHtml(currency)} - ${__("Kenya Shilling")}</span>
		</div>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Threshold Basis")}</label>
		<div class="kt-std-cfg-financial-readout kt-std-cfg-financial-readout--basis">
			<span class="material-symbols-outlined kt-std-icon">gavel</span>
			<input type="hidden" data-kt-std-field="threshold_basis" value="${shared._escapeHtml(source.threshold_basis || "")}" />
			<span>${shared._escapeHtml(source.threshold_basis || __("Open Tender threshold for Works"))}</span>
		</div>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Minimum Package Value")}</label>
		<div class="kt-std-cfg-financial-readout kt-std-cfg-financial-readout--locked">
			<input class="kt-std-cfg-input" type="text" data-kt-std-field="min_value" value="${shared._escapeHtml(
				String(source.min_value || ""),
			)}" readonly />
			<span class="kt-std-cfg-financial-readout__display">${shared._escapeHtml(minDisplay)}</span>
			<span class="material-symbols-outlined kt-std-icon">lock</span>
		</div>
		<p class="kt-std-cfg-financial-readout__hint">${__("Derived from regulation threshold table")}</p>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Maximum Package Value")}</label>
		<div class="kt-std-cfg-financial-readout kt-std-cfg-financial-readout--locked">
			<input class="kt-std-cfg-input" type="text" data-kt-std-field="max_value" value="${shared._escapeHtml(
				String(source.max_value || ""),
			)}" readonly />
			<span class="kt-std-cfg-financial-readout__display">${shared._escapeHtml(maxDisplay)}</span>
			<span class="material-symbols-outlined kt-std-icon">all_inclusive</span>
		</div>
	</div>
	<div class="kt-std-cfg-lot-toggle">
		<div>
			<p class="kt-std-cfg-lot-toggle__title">${__("Lot Support")}</p>
			<p class="kt-std-cfg-lot-toggle__sub">${__("Allow multi-lot bidding")}</p>
		</div>
		<label class="kt-std-cfg-switch">
			<input type="checkbox" data-kt-std-field="lot_support"${lotChecked}${disabled} />
			<span class="kt-std-cfg-switch__track" aria-hidden="true"></span>
		</label>
	</div>
</div>`;
	};

	ui.applicabilityAppliesSection = function applicabilityAppliesSection(lines) {
		const items = (lines || []).map(function (line) {
			return `<li><span class="material-symbols-outlined kt-std-icon">check_circle</span><span>${shared._escapeHtml(line)}</span></li>`;
		}).join("");
		return `
<section class="kt-std-cfg-applies-panel" data-testid="kt-std-cfg-applicability-applies-preview">
	<div class="kt-std-cfg-applies-panel__head">
		<h4><span class="material-symbols-outlined kt-std-icon">visibility</span>${__("Applies To Preview")}</h4>
		<button type="button" class="kt-std-cfg-applies-copy" data-testid="kt-std-cfg-applies-copy" data-kt-std-applies-copy aria-label="${__(
			"Copy preview",
		)}">
			<span class="material-symbols-outlined kt-std-icon">content_copy</span>
		</button>
	</div>
	<p class="kt-std-cfg-applies-panel__lead">${__("This STD will apply to:")}</p>
	<ul class="kt-std-cfg-applies-panel__list">${items || `<li>${__("Configure applicability rules to generate preview.")}</li>`}</ul>
	<p class="kt-std-cfg-applies-panel__footnote">${__(
		"This reinforces that the configuration is understandable and correctly mapped to regulatory requirements.",
	)}</p>
</section>`;
	};

	ui.bindConflictCopy = function bindConflictCopy(host) {
		if (!host) return;
		const btn = host.querySelector("[data-kt-std-conflict-copy]");
		const mono = host.querySelector(".kt-std-cfg-conflict__mono");
		if (!btn || !mono) return;
		btn.addEventListener("click", function () {
			const text = (mono.textContent || "").trim();
			const done = function () {
				frappe.show_alert({ message: __("Conflict summary copied."), indicator: "green" });
			};
			if (navigator.clipboard && navigator.clipboard.writeText) {
				navigator.clipboard.writeText(text).then(done).catch(done);
				return;
			}
			done();
		});
	};

	ui.collectEntityCodes = function collectEntityCodes(host) {
		return Array.from(host.querySelectorAll("[data-kt-std-entity-chip]")).map(function (el) {
			return el.getAttribute("data-kt-std-entity-chip") || "";
		}).filter(Boolean);
	};

	ui.syncEntityPickerVisibility = function syncEntityPickerVisibility(host) {
		if (!host) return;
		const scope = (host.querySelector('[data-kt-std-field="entity_scope"]') || {}).value || "";
		const picker = host.querySelector("[data-testid='kt-std-cfg-entity-picker']");
		if (picker) picker.classList.toggle("is-visible", scope === "Specific MDA");
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
	ui.CONTRACT_TYPE_OPTIONS = CONTRACT_TYPE_OPTIONS;
	ui.WORKS_SUBTYPE_OPTIONS = WORKS_SUBTYPE_OPTIONS;
	ui.FUNDING_OPTIONS = FUNDING_OPTIONS;
	ui.ENTITY_SCOPE_OPTIONS = Object.freeze([
		"All Entities",
		"Specific MDA",
		"Counties Only",
		"State Corporations",
	]);

	const TENDER_FIELD_GROUPS = Object.freeze([
		{ key: "tender_identity", label: __("Tender Identity"), icon: "label" },
		{ key: "timetable", label: __("Tender Timetable"), icon: "schedule" },
		{ key: "bid_security", label: __("Bid Security"), icon: "verified_user" },
		{ key: "site_visit", label: __("Site Visit / Pre-Bid Meeting"), icon: "groups" },
		{ key: "clarifications", label: __("Clarifications"), icon: "question_answer" },
		{ key: "lots", label: __("Lots"), icon: "layers" },
		{ key: "delivery_completion", label: __("Delivery / Completion"), icon: "local_shipping" },
		{ key: "contract_conditions", label: __("Contract Conditions"), icon: "description" },
		{ key: "contacts", label: __("Contacts"), icon: "contact_page" },
	]);

	const TENDER_FIELD_TYPE_OPTIONS = Object.freeze(["Text", "Number", "Date", "Date/Time", "Money"]);

	function _fieldGroupKey(row) {
		return String((row && (row.section || row.group)) || "").trim();
	}

	function _fieldRequirementLabel(row) {
		if (row && row.requirement_level) return String(row.requirement_level);
		if (row && row.required === false) return __("Optional");
		if (row && row.system_field) return __("System Generated");
		return __("Always Required");
	}

	function _fieldRequirementClass(label) {
		const text = String(label || "").toLowerCase();
		if (text.includes("system")) return "kt-std-cfg-req-badge--system";
		if (text.includes("conditional")) return "kt-std-cfg-req-badge--conditional";
		if (text.includes("optional")) return "kt-std-cfg-req-badge--optional";
		return "kt-std-cfg-req-badge--required";
	}

	function _fieldTypeClass(fieldType) {
		const text = String(fieldType || "").toLowerCase();
		if (text.includes("money")) return "kt-std-cfg-field-type--money";
		if (text.includes("date")) return "kt-std-cfg-field-type--date";
		if (text.includes("number")) return "kt-std-cfg-field-type--number";
		return "kt-std-cfg-field-type--text";
	}

	function _defaultValueDisplay(value) {
		const text = String(value == null ? "" : value).trim();
		return text ? text : "—";
	}

	ui.TENDER_FIELD_GROUPS = TENDER_FIELD_GROUPS;

	ui.tenderFieldsActionBar = function tenderFieldsActionBar(editable) {
		const disabled = editable ? "" : " disabled";
		return `
<div class="kt-std-cfg-tf-actions" data-testid="kt-std-cfg-tf-actions">
	<button type="button" class="kt-std-cfg-btn" data-kt-std-clone-template${disabled}>${__("Clone Template")}</button>
	<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-add-field="tender_identity"${disabled}>${__(
			"Add New Field",
		)}</button>
</div>`;
	};

	ui.tenderFieldsMatrix = function tenderFieldsMatrix(fields, editable) {
		const allFields = Array.isArray(fields) ? fields : [];
		const rows = TENDER_FIELD_GROUPS.map(function (group) {
			const groupFields = allFields
				.map(function (row, idx) {
					return { row: row, idx: idx };
				})
				.filter(function (entry) {
					return _fieldGroupKey(entry.row) === group.key;
				});
			const groupHeader = `
<tr class="kt-std-cfg-tf-group-row" data-testid="kt-std-cfg-tf-group-${group.key}">
	<td colspan="7">
		<span class="material-symbols-outlined kt-std-icon">${group.icon}</span>
		<span>${shared._escapeHtml(group.label)}</span>
	</td>
</tr>`;
			const fieldRows = groupFields
				.map(function (entry) {
					const row = entry.row || {};
					const reqLabel = _fieldRequirementLabel(row);
					const defaultDisplay = _defaultValueDisplay(row.default_value);
					const systemField = !!row.system_field;
					const deleteBtn =
						!systemField && editable
							? `<button type="button" class="kt-std-cfg-tf-icon-btn kt-std-cfg-tf-icon-btn--danger" data-kt-std-field-delete="${entry.idx}" aria-label="${__(
									"Delete",
								)}"><span class="material-symbols-outlined kt-std-icon">delete</span></button>`
							: "";
					const systemBadge = systemField
						? `<span class="kt-std-cfg-system-field"><span class="material-symbols-outlined kt-std-icon">lock</span>${__(
								"System Field",
							)}</span>`
						: "";
					return `
<tr class="kt-std-cfg-tf-field-row" data-kt-std-field-row="${entry.idx}" data-testid="kt-std-cfg-tf-field-row">
	<td>
		<div class="kt-std-cfg-tf-label-cell">
			<span class="material-symbols-outlined kt-std-icon kt-std-cfg-tf-drag">drag_indicator</span>
			<span>${shared._escapeHtml(row.label || row.code || __("Field"))}</span>
		</div>
	</td>
	<td><span class="kt-std-cfg-field-type ${_fieldTypeClass(row.field_type)}">${shared._escapeHtml(
						row.field_type || __("Text"),
					)}</span></td>
	<td><span class="kt-std-cfg-req-badge ${_fieldRequirementClass(reqLabel)}">${shared._escapeHtml(reqLabel)}</span></td>
	<td class="kt-std-cfg-tf-default">${shared._escapeHtml(defaultDisplay)}</td>
	<td class="kt-std-cfg-tf-muted">${shared._escapeHtml(row.output_surfaces || row.appears_in || "—")}</td>
	<td class="kt-std-cfg-tf-muted">${shared._escapeHtml(row.fill_mode || row.default_source || "—")}</td>
	<td class="kt-std-cfg-tf-actions-cell">
		<div class="kt-std-cfg-tf-row-actions">
			<button type="button" class="kt-std-cfg-tf-icon-btn" data-kt-std-field-edit="${entry.idx}" aria-label="${__(
				"Edit",
			)}"><span class="material-symbols-outlined kt-std-icon">edit</span></button>
			${deleteBtn}
			${systemBadge}
		</div>
	</td>
</tr>`;
				})
				.join("");
			const addRow = `
<tr class="kt-std-cfg-tf-add-row">
	<td colspan="7">
		<button type="button" class="kt-std-cfg-tf-add-link" data-kt-std-add-field="${group.key}"${editable ? "" : " disabled"}>
			<span class="material-symbols-outlined kt-std-icon">add_circle</span>
			${__("Add Field to {0}", [group.label])}
		</button>
	</td>
</tr>`;
			return groupHeader + fieldRows + addRow;
		}).join("");

		return `
<div class="kt-std-cfg-tf-matrix" data-testid="kt-std-cfg-tender-fields-matrix">
	<div class="kt-std-cfg-tf-matrix__head">
		<h3>${__("Standard Tender Fields")}</h3>
		<div class="kt-std-cfg-tf-matrix__tools">
			<label class="kt-std-cfg-tf-matrix__search">
				<span class="material-symbols-outlined kt-std-icon">search</span>
				<input type="search" data-kt-std-tf-search placeholder="${__("Search fields...")}" />
			</label>
			<button type="button" class="kt-std-cfg-tf-icon-btn" data-kt-std-tf-filter aria-label="${__("Filter fields")}">
				<span class="material-symbols-outlined kt-std-icon">filter_list</span>
			</button>
		</div>
	</div>
	<div class="kt-std-cfg-tf-matrix__table-wrap">
		<table class="kt-std-cfg-tf-table">
			<thead>
				<tr>
					<th>${__("Label")}</th>
					<th>${__("Field Type")}</th>
					<th>${__("Required")}</th>
					<th>${__("Default Value")}</th>
					<th>${__("Appears In")}</th>
					<th>${__("Default Source")}</th>
					<th class="kt-std-cfg-tf-actions-head">${__("Actions")}</th>
				</tr>
			</thead>
			<tbody>${rows}</tbody>
		</table>
	</div>
	<div class="kt-std-cfg-tf-add-footer">
		<button type="button" class="kt-std-cfg-tf-add-here" data-kt-std-add-field-here${editable ? "" : " disabled"}>
			<span class="material-symbols-outlined kt-std-icon">add</span>${__("Add Field Here")}
		</button>
	</div>
</div>`;
	};

	ui.tenderFieldsGuidanceRow = function tenderFieldsGuidanceRow() {
		const cards = [
			{
				icon: "rule",
				tone: "primary",
				title: __("Validation Rules"),
				body: __(
					"Fields marked as 'Required' will trigger system alerts if left blank by procurement officers during procurement creation.",
				),
			},
			{
				icon: "dataset",
				tone: "available",
				title: __("Data Integrity"),
				body: __(
					"Field types ensure data is captured in a structured format suitable for the automated Technical JSON generation.",
				),
			},
			{
				icon: "preview",
				tone: "reserved",
				title: __("Interactive Preview"),
				body: __(
					"Use the 'Preview' tab to see how these fields will appear to the end-user in the procurement portal interface.",
				),
			},
		]
			.map(function (card) {
				return `
<div class="kt-std-cfg-tf-guidance-card kt-std-cfg-tf-guidance-card--${card.tone}">
	<div class="kt-std-cfg-tf-guidance-card__icon"><span class="material-symbols-outlined kt-std-icon">${card.icon}</span></div>
	<h4>${shared._escapeHtml(card.title)}</h4>
	<p>${shared._escapeHtml(card.body)}</p>
</div>`;
			})
			.join("");
		return `<div class="kt-std-cfg-tf-guidance" data-testid="kt-std-cfg-tf-guidance">${cards}</div>`;
	};

	ui.tenderFieldsTabDocument = function tenderFieldsTabDocument(parts) {
		const p = parts || {};
		return `
<section class="kt-std-cfg-tab-stack" data-testid="kt-std-cfg-tender-fields">
	${p.actions || ""}
	<div class="kt-std-cfg-tf-layout">
		${p.matrix || ""}
		${p.guidance || ""}
	</div>
	${p.drawer || ""}
	${p.footer || ""}
</section>`;
	};

	ui.fieldDetailDrawerBody = function fieldDetailDrawerBody(row, editable) {
		const source = row || {};
		const disabled = editable ? "" : " disabled";
		const readonly = source.system_field ? " readonly" : "";
		const sectionOptions = TENDER_FIELD_GROUPS.map(function (group) {
			const selected = _fieldGroupKey(source) === group.key ? " selected" : "";
			return `<option value="${shared._escapeHtml(group.key)}"${selected}>${shared._escapeHtml(group.label)}</option>`;
		}).join("");
		const typeOptions = TENDER_FIELD_TYPE_OPTIONS.map(function (opt) {
			const selected = String(source.field_type || "") === opt ? " selected" : "";
			return `<option${selected}>${opt}</option>`;
		}).join("");
		const requiredOptions = [__("Yes"), __("No")].map(function (opt) {
			const selected =
				(opt === __("Yes") && source.required !== false) || (opt === __("No") && source.required === false)
					? " selected"
					: "";
			return `<option${selected}>${opt}</option>`;
		}).join("");
		const previewChecked = source.used_in_preview ? " checked" : "";
		return `
<div class="kt-std-cfg-drawer-form">
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Field Label")}</label>
		<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="label" value="${shared._escapeHtml(
			source.label || "",
		)}"${disabled}${readonly} />
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Field Key / System Name")}</label>
		<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="code" value="${shared._escapeHtml(
			source.code || "",
		)}" readonly />
		<p class="kt-std-cfg-field__hint">${__("System identifier used for data mapping.")}</p>
	</div>
	<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Field Type")}</label>
			<select class="kt-std-cfg-input" data-kt-std-drawer-field="field_type"${disabled}>${typeOptions}</select>
		</div>
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Required Rule")}</label>
			<select class="kt-std-cfg-input" data-kt-std-drawer-field="required_rule"${disabled}>${requiredOptions}</select>
		</div>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Default Value")}</label>
		<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="default_value" value="${shared._escapeHtml(
			source.default_value || "",
		)}" placeholder="${__("Enter default value...")}"${disabled} />
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Help Text")}</label>
		<textarea class="kt-std-cfg-input" data-kt-std-drawer-field="help_text" rows="3" placeholder="${__(
			"Instructions for the user...",
		)}"${disabled}>${shared._escapeHtml(source.help_text || "")}</textarea>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Validation Rule")}</label>
		<textarea class="kt-std-cfg-input kt-std-cfg-input--mono" data-kt-std-drawer-field="validation_rule" rows="2" placeholder="regex:/^[a-zA-Z0-9 ]+$/"${disabled}>${shared._escapeHtml(
			source.validation_rule || "",
		)}</textarea>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Visibility Rule")}</label>
		<textarea class="kt-std-cfg-input kt-std-cfg-input--mono" data-kt-std-drawer-field="visibility_rule" rows="2" placeholder="show_if:tender_type=open"${disabled}>${shared._escapeHtml(
			source.visibility_rule || "",
		)}</textarea>
	</div>
	<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Section")}</label>
			<select class="kt-std-cfg-input" data-kt-std-drawer-field="section"${disabled}>${sectionOptions}</select>
		</div>
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Display Order")}</label>
			<input class="kt-std-cfg-input" type="number" data-kt-std-drawer-field="display_order" value="${shared._escapeHtml(
				String(source.display_order != null ? source.display_order : 1),
			)}"${disabled} />
		</div>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Source")}</label>
		<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="fill_mode" value="${shared._escapeHtml(
			source.fill_mode || source.default_source || "",
		)}" placeholder="${__("Manual Input / API Endpoint")}"${disabled} />
	</div>
	<label class="kt-std-cfg-checkbox">
		<input type="checkbox" data-kt-std-drawer-field="used_in_preview"${previewChecked}${disabled} />
		<span>${__("Used In Preview")}</span>
	</label>
</div>`;
	};

	const SUPPLIER_REQUIREMENT_TYPE_OPTIONS = Object.freeze([
		"Form",
		"Document",
		"Certificate",
		"Declaration",
		"Price Schedule",
	]);

	const SUPPLIER_APPLIES_TO_OPTIONS = Object.freeze([
		"All Suppliers",
		"Local Suppliers",
		"Foreign Suppliers",
		"JV Suppliers",
		"Specific Lot",
	]);

	function _yesNoLabel(value) {
		const text = String(value == null ? "" : value).trim().toLowerCase();
		if (text === "yes" || text === "true" || text === "1") return __("Yes");
		if (text === "no" || text === "false" || text === "0") return __("No");
		return value ? String(value) : __("No");
	}

	function _yesNoBadgeClass(value) {
		const text = String(value == null ? "" : value).trim().toLowerCase();
		return text === "yes" || text === "true" || text === "1"
			? "kt-std-cfg-sr-flag--yes"
			: "kt-std-cfg-sr-flag--no";
	}

	function _requirementTypeClass(requirementType) {
		const text = String(requirementType || "").toLowerCase();
		if (text.includes("certificate")) return "kt-std-cfg-sr-type--certificate";
		if (text.includes("declaration")) return "kt-std-cfg-sr-type--declaration";
		if (text.includes("price")) return "kt-std-cfg-sr-type--price";
		if (text.includes("document")) return "kt-std-cfg-sr-type--document";
		return "kt-std-cfg-sr-type--form";
	}

	ui.SUPPLIER_REQUIREMENT_TYPE_OPTIONS = SUPPLIER_REQUIREMENT_TYPE_OPTIONS;

	ui.supplierRequirementsActionBar = function supplierRequirementsActionBar(editable) {
		const disabled = editable ? "" : " disabled";
		return `
<div class="kt-std-cfg-sr-actions" data-testid="kt-std-cfg-sr-actions">
	<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-add-requirement${disabled}>${__(
			"Add Requirement",
		)}</button>
</div>`;
	};

	ui.supplierRequirementsMatrix = function supplierRequirementsMatrix(rows, editable) {
		const requirements = Array.isArray(rows) ? rows : [];
		const body = requirements
			.map(function (row, idx) {
				const source = row || {};
				const deleteBtn =
					editable && !source.system_requirement
						? `<button type="button" class="kt-std-cfg-sr-icon-btn kt-std-cfg-sr-icon-btn--danger" data-kt-std-requirement-delete="${idx}" aria-label="${__(
								"Delete",
							)}"><span class="material-symbols-outlined kt-std-icon">delete</span></button>`
						: "";
				return `
<tr class="kt-std-cfg-sr-row" data-kt-std-requirement-row="${idx}" data-testid="kt-std-cfg-sr-row">
	<td>
		<div class="kt-std-cfg-sr-name-cell">
			<span class="material-symbols-outlined kt-std-icon">description</span>
			<div>
				<p class="kt-std-cfg-sr-name">${shared._escapeHtml(source.name || source.code || __("Requirement"))}</p>
				<p class="kt-std-cfg-sr-code">${shared._escapeHtml(source.code || "")}</p>
			</div>
		</div>
	</td>
	<td><span class="kt-std-cfg-sr-type ${_requirementTypeClass(source.requirement_type)}">${shared._escapeHtml(
					source.requirement_type || __("Form"),
				)}</span></td>
	<td><span class="kt-std-cfg-sr-flag ${_yesNoBadgeClass(source.mandatory)}">${shared._escapeHtml(
					_yesNoLabel(source.mandatory),
				)}</span></td>
	<td class="kt-std-cfg-sr-muted">${shared._escapeHtml(source.applies_to || __("All Suppliers"))}</td>
	<td><span class="kt-std-cfg-sr-flag ${_yesNoBadgeClass(source.blocks_submission)}">${shared._escapeHtml(
					_yesNoLabel(source.blocks_submission),
				)}</span></td>
	<td><span class="kt-std-cfg-sr-flag ${_yesNoBadgeClass(source.used_in_evaluation)}">${shared._escapeHtml(
					_yesNoLabel(source.used_in_evaluation),
				)}</span></td>
	<td class="kt-std-cfg-sr-actions-cell">
		<div class="kt-std-cfg-sr-row-actions">
			<button type="button" class="kt-std-cfg-sr-icon-btn" data-kt-std-requirement-edit="${idx}" aria-label="${__(
				"Edit",
			)}"><span class="material-symbols-outlined kt-std-icon">edit</span></button>
			${deleteBtn}
		</div>
	</td>
</tr>`;
			})
			.join("");

		return `
<div class="kt-std-cfg-sr-matrix" data-testid="kt-std-cfg-supplier-requirements-matrix">
	<div class="kt-std-cfg-sr-matrix__head">
		<h3>${__("Supplier Submission Requirements")}</h3>
		<div class="kt-std-cfg-sr-matrix__tools">
			<label class="kt-std-cfg-sr-matrix__search">
				<span class="material-symbols-outlined kt-std-icon">search</span>
				<input type="search" data-kt-std-sr-search placeholder="${__("Search requirements...")}" />
			</label>
			<button type="button" class="kt-std-cfg-sr-icon-btn" data-kt-std-sr-filter aria-label="${__(
				"Filter requirements",
			)}">
				<span class="material-symbols-outlined kt-std-icon">filter_list</span>
			</button>
		</div>
	</div>
	<div class="kt-std-cfg-sr-matrix__table-wrap">
		<table class="kt-std-cfg-sr-table">
			<thead>
				<tr>
					<th>${__("Requirement")}</th>
					<th>${__("Type")}</th>
					<th>${__("Mandatory")}</th>
					<th>${__("Applies To")}</th>
					<th>${__("Blocks Submission")}</th>
					<th>${__("Used In Evaluation")}</th>
					<th class="kt-std-cfg-sr-actions-head">${__("Actions")}</th>
				</tr>
			</thead>
			<tbody>${body || `<tr><td colspan="7" class="kt-std-cfg-empty">${__("No supplier requirements yet.")}</td></tr>`}</tbody>
		</table>
	</div>
	<div class="kt-std-cfg-sr-add-footer">
		<button type="button" class="kt-std-cfg-sr-add-here" data-kt-std-add-requirement-here${editable ? "" : " disabled"}>
			<span class="material-symbols-outlined kt-std-icon">add</span>${__("Add Requirement Here")}
		</button>
	</div>
</div>`;
	};

	ui.supplierRequirementsGuidanceRow = function supplierRequirementsGuidanceRow() {
		const cards = [
			{
				icon: "checklist",
				tone: "primary",
				title: __("Submission Checklist"),
				body: __(
					"Mandatory requirements appear on the supplier submission checklist and must be satisfied before bids can be submitted.",
				),
			},
			{
				icon: "rule",
				tone: "available",
				title: __("Validation Rules"),
				body: __(
					"Validation rules enforce file uploads, signatures, expiry dates, and amounts so procurement officers receive complete submissions.",
				),
			},
			{
				icon: "analytics",
				tone: "reserved",
				title: __("Evaluation Linkage"),
				body: __(
					"Requirements marked for evaluation feed into evaluation setup and downstream scoring workflows.",
				),
			},
		]
			.map(function (card) {
				return `
<div class="kt-std-cfg-sr-guidance-card kt-std-cfg-sr-guidance-card--${card.tone}">
	<div class="kt-std-cfg-sr-guidance-card__icon"><span class="material-symbols-outlined kt-std-icon">${card.icon}</span></div>
	<h4>${shared._escapeHtml(card.title)}</h4>
	<p>${shared._escapeHtml(card.body)}</p>
</div>`;
			})
			.join("");
		return `<div class="kt-std-cfg-sr-guidance" data-testid="kt-std-cfg-sr-guidance">${cards}</div>`;
	};

	ui.supplierRequirementsTabDocument = function supplierRequirementsTabDocument(parts) {
		const p = parts || {};
		return `
<section class="kt-std-cfg-tab-stack" data-testid="kt-std-cfg-supplier-requirements">
	${p.actions || ""}
	<div class="kt-std-cfg-sr-layout">
		${p.matrix || ""}
		${p.guidance || ""}
	</div>
	${p.drawer || ""}
	${p.footer || ""}
</section>`;
	};

	ui.requirementDetailDrawerBody = function requirementDetailDrawerBody(row, editable) {
		const source = row || {};
		const disabled = editable ? "" : " disabled";
		const typeOptions = SUPPLIER_REQUIREMENT_TYPE_OPTIONS.map(function (opt) {
			const selected = String(source.requirement_type || "") === opt ? " selected" : "";
			return `<option${selected}>${opt}</option>`;
		}).join("");
		const appliesOptions = SUPPLIER_APPLIES_TO_OPTIONS.map(function (opt) {
			const selected = String(source.applies_to || "") === opt ? " selected" : "";
			return `<option${selected}>${opt}</option>`;
		}).join("");
		const yesNo = function (key) {
			return [__("Yes"), __("No")]
				.map(function (opt) {
					const val = String(source[key] || "").toLowerCase();
					const isYes = val === "yes" || val === "true" || source[key] === true;
					const selected =
						(opt === __("Yes") && isYes) || (opt === __("No") && !isYes && (val === "no" || val === "false"))
							? " selected"
							: "";
					return `<option${selected}>${opt}</option>`;
				})
				.join("");
		};
		const visibilityChecked = source.supplier_visibility !== "Hidden" ? " checked" : "";
		return `
<div class="kt-std-cfg-drawer-form">
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Requirement Name")}</label>
		<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="name" value="${shared._escapeHtml(
			source.name || "",
		)}"${disabled} />
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Requirement Code")}</label>
		<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="code" value="${shared._escapeHtml(
			source.code || "",
		)}" placeholder="${__("FORM_OF_TENDER")}"${disabled} />
	</div>
	<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Requirement Type")}</label>
			<select class="kt-std-cfg-input" data-kt-std-drawer-field="requirement_type"${disabled}>${typeOptions}</select>
		</div>
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Mandatory")}</label>
			<select class="kt-std-cfg-input" data-kt-std-drawer-field="mandatory"${disabled}>${yesNo("mandatory")}</select>
		</div>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Applies To")}</label>
		<select class="kt-std-cfg-input" data-kt-std-drawer-field="applies_to"${disabled}>${appliesOptions}</select>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Validation Rule")}</label>
		<textarea class="kt-std-cfg-input kt-std-cfg-input--mono" data-kt-std-drawer-field="validation_rule" rows="2" placeholder="${__(
			"Signed form required; expiry date required",
		)}"${disabled}>${shared._escapeHtml(source.validation_rule || "")}</textarea>
	</div>
	<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Blocks Submission")}</label>
			<select class="kt-std-cfg-input" data-kt-std-drawer-field="blocks_submission"${disabled}>${yesNo(
				"blocks_submission",
			)}</select>
		</div>
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Used In Evaluation")}</label>
			<select class="kt-std-cfg-input" data-kt-std-drawer-field="used_in_evaluation"${disabled}>${yesNo(
				"used_in_evaluation",
			)}</select>
		</div>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Failure Impact")}</label>
		<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="failure_impact" value="${shared._escapeHtml(
			source.failure_impact || "",
		)}" placeholder="${__("Blocks submission / Warning only")}"${disabled} />
	</div>
	<label class="kt-std-cfg-checkbox">
		<input type="checkbox" data-kt-std-drawer-field="supplier_visible"${visibilityChecked}${disabled} />
		<span>${__("Visible to supplier in submission checklist")}</span>
	</label>
</div>`;
	};

	const FORMS_PREVIEW_MODES = [
		{ key: "tender_manager", label: __("Tender Manager") },
		{ key: "supplier_download", label: __("Supplier Download") },
		{ key: "submission_checklist", label: __("Submission Checklist") },
		{ key: "publication_snapshot", label: __("Publication Snapshot") },
		{ key: "contract_carry_forward", label: __("Contract Carry-Forward") },
	];

	const DOCUMENT_TYPE_OPTIONS = ["PDF", "EXCEL", "WORD", "SYSTEM FORM"];
	const SOURCE_OUTPUT_OPTIONS = ["System Generated", "Uploaded Template", "Manual Upload"];
	const VISIBLE_TO_SUPPLIER_OPTIONS = ["Yes", "No", "After Publication", "Internal Only"];
	const IN_PACKAGE_OPTIONS = ["Yes", "No", "Conditional"];
	const DOCUMENT_STATUS_OPTIONS = ["Approved", "Draft", "Pending Review"];

	function _documentTypeIcon(attachmentType) {
		const text = String(attachmentType || "").toUpperCase();
		if (text.includes("PDF")) return { icon: "picture_as_pdf", tone: "error" };
		if (text.includes("SYSTEM") || text.includes("FORM")) return { icon: "dynamic_form", tone: "committed" };
		if (text.includes("EXCEL") || text.includes("XLS")) return { icon: "table_chart", tone: "available" };
		return { icon: "description", tone: "primary" };
	}

	function _documentStatusClass(status) {
		const text = String(status || "").toLowerCase();
		if (text.includes("approved")) return "kt-std-cfg-fa-status--approved";
		if (text.includes("pending")) return "kt-std-cfg-fa-status--pending";
		return "kt-std-cfg-fa-status--draft";
	}

	function _emphasisClass(value, positive) {
		const text = String(value || "").toLowerCase();
		if (positive && (text === "yes" || text.includes("system generated") || text.includes("approved"))) {
			return "kt-std-cfg-fa-emphasis--positive";
		}
		if (text.includes("after publication") || text.includes("secondary")) {
			return "kt-std-cfg-fa-emphasis--secondary";
		}
		return "";
	}

	ui.FORMS_PREVIEW_MODES = FORMS_PREVIEW_MODES;

	ui.formsAttachmentsDocumentsSection = function formsAttachmentsDocumentsSection(forms, editable, activePreviewIndex) {
		const documents = Array.isArray(forms) ? forms : [];
		const previewIndex = activePreviewIndex == null ? 0 : activePreviewIndex;
		const previewPills = FORMS_PREVIEW_MODES.map(function (mode, idx) {
			const active = idx === previewIndex ? " is-active" : "";
			return `<button type="button" class="kt-std-cfg-fa-pill${active}" data-kt-std-fa-preview-mode="${idx}">${shared._escapeHtml(
				mode.label,
			)}</button>`;
		}).join("");
		const rows = documents
			.map(function (row, idx) {
				const source = row || {};
				const typeMeta = _documentTypeIcon(source.attachment_type);
				const linkedReq = source.linked_requirement || __("None (Main Document)");
				return `
<tr class="kt-std-cfg-fa-doc-row" data-kt-std-document-row="${idx}" data-testid="kt-std-cfg-fa-doc-row">
	<td>
		<div class="kt-std-cfg-fa-name-cell">
			<span class="material-symbols-outlined kt-std-icon kt-std-cfg-fa-doc-icon--${typeMeta.tone}">${typeMeta.icon}</span>
			<span class="kt-std-cfg-fa-doc-name">${shared._escapeHtml(source.label || __("Document"))}</span>
		</div>
	</td>
	<td class="kt-std-cfg-fa-muted">${shared._escapeHtml(source.purpose || "")}</td>
	<td><span class="kt-std-cfg-fa-type">${shared._escapeHtml(source.attachment_type || "")}</span></td>
	<td class="${_emphasisClass(source.source_output || source.source, true)}">${shared._escapeHtml(
					source.source_output || source.source || "",
				)}</td>
	<td class="kt-std-cfg-fa-muted">${shared._escapeHtml(linkedReq)}</td>
	<td class="${_emphasisClass(source.visible_to_supplier)}">${shared._escapeHtml(source.visible_to_supplier || "")}</td>
	<td class="${_emphasisClass(source.in_package, true)}">${shared._escapeHtml(source.in_package || "")}</td>
	<td><span class="kt-std-cfg-fa-status ${_documentStatusClass(source.status)}">${shared._escapeHtml(
					source.status || __("Draft"),
				)}</span></td>
	<td class="kt-std-cfg-fa-actions-cell">
		<div class="kt-std-cfg-fa-row-actions">
			<button type="button" class="kt-std-cfg-fa-action-link" data-kt-std-document-view="${idx}">${__("View")}</button>
			<button type="button" class="kt-std-cfg-fa-action-link" data-kt-std-document-replace="${idx}">${__(
				"Replace",
			)}</button>
			<button type="button" class="kt-std-cfg-fa-action-link" data-kt-std-document-evidence="${idx}">${__(
				"Evidence",
			)}</button>
			<button type="button" class="kt-std-cfg-fa-icon-btn" data-kt-std-document-edit="${idx}" aria-label="${__(
				"Edit",
			)}"><span class="material-symbols-outlined kt-std-icon">edit</span></button>
		</div>
	</td>
</tr>`;
			})
			.join("");
		const uploadDisabled = editable ? "" : " disabled";
		return `
<section class="kt-std-cfg-fa-documents" data-testid="kt-std-cfg-forms-documents">
	<div class="kt-std-cfg-fa-section-head">
		<div>
			<h3>${__("Tender Documents & Templates")}</h3>
			<p>${__("Core documents generated by the system or required as templates.")}</p>
		</div>
		<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-upload-template${uploadDisabled}>
			<span class="material-symbols-outlined kt-std-icon">upload_file</span>${__("Upload Template")}
		</button>
	</div>
	<div class="kt-std-cfg-fa-preview-bar">
		<span class="kt-std-cfg-fa-preview-label">${__("Preview Mode:")}</span>
		<div class="kt-std-cfg-fa-preview-pills">${previewPills}</div>
	</div>
	<div class="kt-std-cfg-fa-table-wrap">
		<table class="kt-std-cfg-fa-table">
			<thead>
				<tr>
					<th>${__("Document Name")}</th>
					<th>${__("Purpose")}</th>
					<th>${__("Type")}</th>
					<th>${__("Source / Output")}</th>
					<th>${__("Linked Requirement")}</th>
					<th>${__("Visible to Supplier")}</th>
					<th>${__("In Package")}</th>
					<th>${__("Status")}</th>
					<th class="kt-std-cfg-fa-actions-head">${__("Actions")}</th>
				</tr>
			</thead>
			<tbody>${rows || `<tr><td colspan="9" class="kt-std-cfg-empty">${__("No documents configured yet.")}</td></tr>`}</tbody>
		</table>
	</div>
</section>`;
	};

	ui.formsAttachmentsSupplierFormsSection = function formsAttachmentsSupplierFormsSection(supplierForms, editable) {
		const forms = Array.isArray(supplierForms) ? supplierForms : [];
		const cards = forms
			.map(function (form, idx) {
				const source = form || {};
				const icon = source.icon || "description";
				return `
<div class="kt-std-cfg-fa-supplier-card" data-kt-std-supplier-form="${idx}" data-testid="kt-std-cfg-fa-supplier-card">
	<div class="kt-std-cfg-fa-supplier-card__head">
		<div class="kt-std-cfg-fa-supplier-card__icon"><span class="material-symbols-outlined kt-std-icon">${icon}</span></div>
		<button type="button" class="kt-std-cfg-fa-supplier-card__menu" aria-label="${__("More options")}">
			<span class="material-symbols-outlined kt-std-icon">more_vert</span>
		</button>
	</div>
	<h4>${shared._escapeHtml(source.label || source.code || __("Form"))}</h4>
	<p>${shared._escapeHtml(
		source.description || __("Interactive form completed by suppliers during submission."),
	)}</p>
	<div class="kt-std-cfg-fa-supplier-card__footer">
		<span class="kt-std-cfg-fa-supplier-card__meta">${shared._escapeHtml(
			String(source.field_count != null ? source.field_count : 0),
		)} ${__("Fields")}</span>
		<button type="button" class="kt-std-cfg-fa-supplier-card__edit" data-kt-std-supplier-form-edit="${idx}">
			${__("Edit Form")}<span class="material-symbols-outlined kt-std-icon">arrow_forward</span>
		</button>
	</div>
</div>`;
			})
			.join("");
		const addDisabled = editable ? "" : " disabled";
		return `
<section class="kt-std-cfg-fa-supplier-forms" data-testid="kt-std-cfg-forms-supplier-forms">
	<div class="kt-std-cfg-fa-section-head">
		<div>
			<h3>${__("Supplier-Facing Forms")}</h3>
			<p>${__("Interactive forms that suppliers complete during the submission phase.")}</p>
		</div>
		<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-add-supplier-form${addDisabled}>
			<span class="material-symbols-outlined kt-std-icon">add</span>${__("Add New Form")}
		</button>
	</div>
	<div class="kt-std-cfg-fa-supplier-grid">
		${cards}
		<button type="button" class="kt-std-cfg-fa-supplier-card kt-std-cfg-fa-supplier-card--add" data-kt-std-add-custom-form${addDisabled}>
			<span class="material-symbols-outlined kt-std-icon">add_circle</span>
			<span>${__("Create Custom Form")}</span>
		</button>
	</div>
</section>`;
	};

	ui.formsAttachmentsInfoRow = function formsAttachmentsInfoRow(missingRequirements) {
		const warnings = Array.isArray(missingRequirements) ? missingRequirements : [];
		const primaryWarning = warnings[0] || {};
		const warningTitle = primaryWarning.label
			? __("Missing Requirements")
			: __("Missing Requirements");
		const warningBody =
			primaryWarning.message ||
			__(
				"Link documents to supplier requirements before submission. Upload or generate missing templates to resolve gaps.",
			);
		const warningActions = primaryWarning.label
			? `<div class="kt-std-cfg-fa-info-card__actions">
			<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--sm kt-std-cfg-btn--primary" data-kt-std-fa-upload-missing>
				<span class="material-symbols-outlined kt-std-icon">upload_file</span>${__(
					"Upload {0}",
					[primaryWarning.label],
				)}
			</button>
			<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--sm" data-kt-std-fa-generate-missing>
				<span class="material-symbols-outlined kt-std-icon">auto_fix</span>${__("Generate from Template")}
			</button>
			<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--sm" data-kt-std-fa-mark-na>${__("Mark Not Applicable")}</button>
		</div>`
			: "";
		return `
<div class="kt-std-cfg-fa-info-row" data-testid="kt-std-cfg-fa-info-row">
	<div class="kt-std-cfg-fa-info-card kt-std-cfg-fa-info-card--primary">
		<span class="material-symbols-outlined kt-std-icon">info</span>
		<div>
			<h4>${__("Attachment Logic")}</h4>
			<p>${__(
				"Attachments linked in this section will be automatically compiled into the final tender package. Ensure all templates are updated to the latest revision before publishing.",
			)}</p>
		</div>
	</div>
	<div class="kt-std-cfg-fa-info-card kt-std-cfg-fa-info-card--warning" data-testid="kt-std-cfg-forms-warn">
		<span class="material-symbols-outlined kt-std-icon">warning</span>
		<div>
			<h4>${warningTitle}</h4>
			<p>${shared._escapeHtml(warningBody)}</p>
			${warningActions}
		</div>
	</div>
</div>`;
	};

	ui.formsAttachmentsTabDocument = function formsAttachmentsTabDocument(parts) {
		const p = parts || {};
		return `
<section class="kt-std-cfg-tab-stack" data-testid="kt-std-cfg-forms">
	<div class="kt-std-cfg-fa-layout">
		${p.documents || ""}
		${p.supplierForms || ""}
		${p.info || ""}
	</div>
	${p.drawer || ""}
	${p.footer || ""}
</section>`;
	};

	ui.documentDetailDrawerBody = function documentDetailDrawerBody(row, editable) {
		const source = row || {};
		const disabled = editable ? "" : " disabled";
		const typeOptions = DOCUMENT_TYPE_OPTIONS.map(function (opt) {
			const selected =
				String(source.attachment_type || "").toUpperCase() === opt.toUpperCase() ? " selected" : "";
			return `<option${selected}>${opt}</option>`;
		}).join("");
		const sourceOptions = SOURCE_OUTPUT_OPTIONS.map(function (opt) {
			const val = String(source.source_output || source.source || "");
			const selected = val === opt ? " selected" : "";
			return `<option${selected}>${opt}</option>`;
		}).join("");
		const visibilityOptions = VISIBLE_TO_SUPPLIER_OPTIONS.map(function (opt) {
			const selected = String(source.visible_to_supplier || "") === opt ? " selected" : "";
			return `<option${selected}>${opt}</option>`;
		}).join("");
		const packageOptions = IN_PACKAGE_OPTIONS.map(function (opt) {
			const selected = String(source.in_package || "") === opt ? " selected" : "";
			return `<option${selected}>${opt}</option>`;
		}).join("");
		const statusClass = _documentStatusClass(source.status);
		return `
<div class="kt-std-cfg-drawer-form">
	<div class="kt-std-cfg-drawer-section">
		<h4 class="kt-std-cfg-drawer-section__title">${__("Document Details")}</h4>
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Document Name")}</label>
			<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="label" value="${shared._escapeHtml(
				source.label || "",
			)}"${disabled} />
		</div>
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Purpose")}</label>
			<textarea class="kt-std-cfg-input" data-kt-std-drawer-field="purpose" rows="2"${disabled}>${shared._escapeHtml(
				source.purpose || "",
			)}</textarea>
		</div>
		<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
			<div class="kt-std-cfg-field">
				<label class="kt-std-cfg-field__label">${__("Document Type")}</label>
				<select class="kt-std-cfg-input" data-kt-std-drawer-field="attachment_type"${disabled}>${typeOptions}</select>
			</div>
			<div class="kt-std-cfg-field">
				<label class="kt-std-cfg-field__label">${__("Source / Output Mode")}</label>
				<select class="kt-std-cfg-input" data-kt-std-drawer-field="source_output"${disabled}>${sourceOptions}</select>
			</div>
		</div>
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Linked Requirement")}</label>
			<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="linked_requirement" value="${shared._escapeHtml(
				source.linked_requirement || "",
			)}" placeholder="${__("None (Main Document)")}"${disabled} />
		</div>
	</div>
	<div class="kt-std-cfg-drawer-section">
		<h4 class="kt-std-cfg-drawer-section__title">${__("Visibility & Package")}</h4>
		<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
			<div class="kt-std-cfg-field">
				<label class="kt-std-cfg-field__label">${__("Visible To Supplier")}</label>
				<select class="kt-std-cfg-input" data-kt-std-drawer-field="visible_to_supplier"${disabled}>${visibilityOptions}</select>
			</div>
			<div class="kt-std-cfg-field">
				<label class="kt-std-cfg-field__label">${__("Included in Package")}</label>
				<select class="kt-std-cfg-input" data-kt-std-drawer-field="in_package"${disabled}>${packageOptions}</select>
			</div>
		</div>
	</div>
	<div class="kt-std-cfg-drawer-section">
		<h4 class="kt-std-cfg-drawer-section__title">${__("Template & Governance")}</h4>
		<div class="kt-std-cfg-fa-template-chip">
			<div class="kt-std-cfg-fa-template-chip__meta">
				<span class="material-symbols-outlined kt-std-icon">description</span>
				<span>${shared._escapeHtml(source.template_file || __("STD_Works_V2.pdf"))}</span>
			</div>
			<button type="button" class="kt-std-cfg-fa-action-link" data-kt-std-document-replace-inline${disabled}>${__(
				"Replace",
			)}</button>
		</div>
		<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
			<div class="kt-std-cfg-field">
				<label class="kt-std-cfg-field__label">${__("Template Version")}</label>
				<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="template_version" value="${shared._escapeHtml(
					source.template_version || "v2.0",
				)}"${disabled} />
			</div>
			<div class="kt-std-cfg-field">
				<label class="kt-std-cfg-field__label">${__("Accepted File Type")}</label>
				<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="accepted_file_type" value="${shared._escapeHtml(
					source.accepted_file_type || ".pdf",
				)}"${disabled} />
			</div>
		</div>
		<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
			<div class="kt-std-cfg-field">
				<label class="kt-std-cfg-field__label">${__("Approval Status")}</label>
				<span class="kt-std-cfg-fa-status ${statusClass}">${shared._escapeHtml(source.status || __("Draft"))}</span>
				<input type="hidden" data-kt-std-drawer-field="status" value="${shared._escapeHtml(source.status || "Draft")}" />
			</div>
			<div class="kt-std-cfg-field">
				<label class="kt-std-cfg-field__label">${__("Last Updated")}</label>
				<input class="kt-std-cfg-input" type="date" data-kt-std-drawer-field="last_updated" value="${shared._escapeHtml(
					source.last_updated || "",
				)}"${disabled} />
			</div>
		</div>
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Replacement Rules")}</label>
			<select class="kt-std-cfg-input" data-kt-std-drawer-field="replacement_rules"${disabled}>
				<option${String(source.replacement_rules || "Allow versioning") === "Allow versioning" ? " selected" : ""}>${__(
					"Allow versioning",
				)}</option>
				<option${String(source.replacement_rules || "") === "Strict overwrite" ? " selected" : ""}>${__(
					"Strict overwrite",
				)}</option>
			</select>
		</div>
		<label class="kt-std-cfg-checkbox">
			<input type="checkbox" data-kt-std-drawer-field="evidence_required"${
				source.evidence_required !== false ? " checked" : ""
			}${disabled} />
			<span>${__("Require upload proof")}</span>
		</label>
	</div>
</div>`;
	};

	const EVALUATION_BASIS_OPTIONS = [
		{ value: "Weighted Aggregate", label: __("Weighted Aggregate") },
		{ value: "Lowest Evaluated Responsive Bid", label: __("Lowest Evaluated Responsive Bid") },
		{ value: "Quality and Cost Based Selection", label: __("Quality and Cost Based Selection") },
		{ value: "Quality Based Selection", label: __("Quality Based Selection") },
		{
			value: "Pass/Fail Technical then Financial Ranking",
			label: __("Pass/Fail Technical then Financial Ranking"),
		},
		{ value: "Framework Qualification", label: __("Framework Qualification") },
	];

	function _stageTypeBadgeClass(evaluationType) {
		const text = String(evaluationType || "").toLowerCase();
		if (text.includes("scored")) return "kt-std-cfg-ev-type--scored";
		return "kt-std-cfg-ev-type--passfail";
	}

	function _stageTypeBadgeLabel(stage) {
		const source = stage || {};
		const text = String(source.evaluation_type || "").toLowerCase();
		if (text.includes("scored")) return __("SCORED SYSTEM");
		return __("PASS / FAIL");
	}

	function _structureSummaryLine(stage) {
		const source = stage || {};
		const name = String(source.name || source.code || "").split(" ")[0];
		const evalType = String(source.evaluation_type || "");
		if (evalType.toLowerCase().includes("scored") && source.minimum_score) {
			return `${name}: ${evalType}, minimum ${source.minimum_score}`;
		}
		if (source.evaluation_method) {
			return `${name}: ${source.evaluation_method}`;
		}
		return `${name}: ${evalType || __("Configured")}`;
	}

	function _formatLastUpdated(value) {
		if (!value) return __("Not set");
		const text = String(value);
		if (text.includes("T")) {
			const dt = new Date(text);
			if (!Number.isNaN(dt.getTime())) {
				return dt
					.toLocaleString("en-GB", {
						day: "2-digit",
						month: "short",
						year: "numeric",
						hour: "2-digit",
						minute: "2-digit",
					})
					.toUpperCase();
			}
		}
		return text;
	}

	function _linkedRequirementChips(requirements) {
		const items = Array.isArray(requirements) ? requirements : [];
		if (!items.length) return `<span class="kt-std-cfg-ev-chip kt-std-cfg-ev-chip--empty">${__("None linked")}</span>`;
		return items
			.map(function (req) {
				const label = typeof req === "string" ? req : req.label || req.name || "";
				return `<span class="kt-std-cfg-ev-chip"><span class="material-symbols-outlined kt-std-icon">link</span>${shared._escapeHtml(
					label,
				)}</span>`;
			})
			.join("");
	}

	ui.EVALUATION_BASIS_OPTIONS = EVALUATION_BASIS_OPTIONS;

	ui.evaluationSetupBasisPanel = function evaluationSetupBasisPanel(data, editable) {
		const source = data || {};
		const disabled = editable ? "" : " disabled";
		const options = EVALUATION_BASIS_OPTIONS.map(function (opt) {
			const selected =
				String(source.governing_basis || source.method || "") === opt.value ? " selected" : "";
			return `<option value="${shared._escapeHtml(opt.value)}"${selected}>${opt.label}</option>`;
		}).join("");
		return `
<div class="kt-std-cfg-ev-basis" data-testid="kt-std-cfg-ev-basis">
	<div class="kt-std-cfg-ev-basis__copy">
		<label class="kt-std-cfg-ev-label">${__("Governing Evaluation Basis")}</label>
		<p>${__("Select the primary methodology that governs the entire evaluation workflow.")}</p>
	</div>
	<div class="kt-std-cfg-ev-basis__select">
		<select class="kt-std-cfg-input" data-kt-std-field="governing_basis"${disabled}>${options}</select>
		<span class="material-symbols-outlined kt-std-icon">unfold_more</span>
	</div>
</div>`;
	};

	ui.evaluationSetupBentoGrid = function evaluationSetupBentoGrid(data, stages) {
		const source = data || {};
		const stageList = Array.isArray(stages) ? stages : [];
		const basis = source.governing_basis || source.method || __("Weighted Aggregate");
		const summaryLines = stageList
			.map(function (stage) {
				const parts = String(stage.name || stage.code || __("Stage")).split(" ");
				const shortName = parts[0] || __("Stage");
				return `
<li class="kt-std-cfg-ev-structure__line">
	<span>${shared._escapeHtml(shortName)}:</span>
	<strong>${shared._escapeHtml(
		stage.evaluation_method ||
			(stage.minimum_score && String(stage.evaluation_type || "").toLowerCase().includes("scored")
				? `${stage.evaluation_type}, minimum ${stage.minimum_score}`
				: stage.evaluation_type || __("Configured")),
	)}</strong>
</li>`;
			})
			.join("");
		return `
<div class="kt-std-cfg-ev-bento" data-testid="kt-std-cfg-ev-bento">
	<div class="kt-std-cfg-ev-total-stages">
		<div>
			<p class="kt-std-cfg-ev-total-stages__label">${__("TOTAL STAGES")}</p>
			<h3>${String(stageList.length).padStart(2, "0")}</h3>
		</div>
		<div class="kt-std-cfg-ev-total-stages__status">
			<span class="material-symbols-outlined kt-std-icon">check_circle</span>
			<span>${source.logic_validated === false ? __("Logic flow pending") : __("Logic flow validated")}</span>
		</div>
	</div>
	<div class="kt-std-cfg-ev-structure">
		<div class="kt-std-cfg-ev-structure__col">
			<p class="kt-std-cfg-ev-label">${__("EVALUATION STRUCTURE")}</p>
			<p class="kt-std-cfg-ev-structure__subtitle">${__("Evaluation Method Summary")}</p>
			<ul class="kt-std-cfg-ev-structure__list">${summaryLines}</ul>
		</div>
		<div class="kt-std-cfg-ev-structure__basis">
			<p class="kt-std-cfg-ev-label">${__("EVALUATION STRUCTURE")}</p>
			<h4>${shared._escapeHtml(basis)}</h4>
			<p>${__(
				"Scoring model: Configured by selected STD and procurement method.",
			)}</p>
			<p>${__(
				"Technical scoring applies only where this STD requires weighted technical evaluation.",
			)}</p>
		</div>
	</div>
</div>`;
	};

	ui.evaluationSetupConflictBanner = function evaluationSetupConflictBanner(conflictCheck) {
		const check = conflictCheck || {};
		const pills = Array.isArray(check.pills) ? check.pills : [];
		const pillHtml = pills
			.map(function (pill) {
				return `<span class="kt-std-cfg-ev-pill">${shared._escapeHtml(pill)}</span>`;
			})
			.join("");
		return `
<div class="kt-std-cfg-ev-conflict" data-testid="kt-std-cfg-ev-conflict">
	<div class="kt-std-cfg-ev-conflict__lead">
		<div class="kt-std-cfg-ev-conflict__icon"><span class="material-symbols-outlined kt-std-icon">check_circle</span></div>
		<div>
			<h4>${__("Rule Conflict Check")}</h4>
			<p>${check.ok === false ? __("Conflicting active STD found for:") : __("No conflicting active STD found for:")}</p>
		</div>
	</div>
	<div class="kt-std-cfg-ev-conflict__pills">${pillHtml}</div>
</div>`;
	};

	ui.evaluationSetupReadyBanner = function evaluationSetupReadyBanner(readinessOk) {
		const ready = readinessOk !== false;
		return `
<div class="kt-std-cfg-ev-ready${ready ? "" : " kt-std-cfg-ev-ready--warn"}" data-testid="kt-std-cfg-ev-ready">
	<div class="kt-std-cfg-ev-ready__lead">
		<div class="kt-std-cfg-ev-ready__icon"><span class="material-symbols-outlined kt-std-icon">check_circle</span></div>
		<div>
			<h4>${ready ? __("Evaluation Setup: Ready") : __("Evaluation Setup: Incomplete")}</h4>
			<p>${
				ready
					? __("All readiness checks passed. Configuration is valid for submission.")
					: __("Complete all stage configuration before submission.")
			}</p>
		</div>
	</div>
	<button type="button" class="kt-std-cfg-ev-ready__copy" aria-label="${__("Copy readiness summary")}">
		<span class="material-symbols-outlined kt-std-icon">content_copy</span>
	</button>
</div>`;
	};

	ui.evaluationSetupStageCard = function evaluationSetupStageCard(stage, idx, editable, isLast) {
		const source = stage || {};
		const linkedLabel =
			source.linked_requirements && source.linked_requirements.length
				? source.minimum_compliance
					? __("Required Documents")
					: source.evaluation_method
						? __("Evaluation Type")
						: __("Linked Requirements")
				: __("Linked Requirements");
		const detailValue = source.minimum_compliance
			? source.minimum_compliance
			: source.minimum_score
				? source.minimum_score
				: source.evaluation_method || source.evaluation_type || "";
		const detailSuffix = source.minimum_score ? __("Min. score required") : "";
		const carryChecked = source.carry_forward !== false ? " is-on" : "";
		const carryDisabled = editable ? "" : " disabled";
		return `
<div class="kt-std-cfg-ev-stage-card" data-kt-std-stage-row="${idx}" data-testid="kt-std-cfg-ev-stage-card">
	<div class="kt-std-cfg-ev-stage-card__rail">
		<span class="material-symbols-outlined kt-std-icon kt-std-cfg-ev-drag">drag_indicator</span>
		<span class="kt-std-cfg-ev-stage-card__index">${idx + 1}</span>
		${isLast ? "" : '<span class="kt-std-cfg-ev-stage-card__connector"></span>'}
	</div>
	<div class="kt-std-cfg-ev-stage-card__body">
		<div class="kt-std-cfg-ev-stage-card__head">
			<div>
				<h4>${shared._escapeHtml(source.name || source.code || __("Stage"))}</h4>
				<p>${shared._escapeHtml(
					source.description || __("Configure evaluation rules and linked supplier requirements."),
				)}</p>
			</div>
			<div class="kt-std-cfg-ev-stage-card__badges">
				<span class="kt-std-cfg-ev-type ${_stageTypeBadgeClass(source.evaluation_type)}">${_stageTypeBadgeLabel(
					source,
				)}</span>
				<button type="button" class="kt-std-cfg-ev-stage-card__configure" data-kt-std-stage-edit="${idx}" aria-label="${__(
					"Configure stage",
				)}"><span class="material-symbols-outlined kt-std-icon">settings</span></button>
			</div>
		</div>
		<div class="kt-std-cfg-ev-stage-card__grid">
			<div>
				<label class="kt-std-cfg-ev-field-label">${linkedLabel}</label>
				<div class="kt-std-cfg-ev-chip-row">${_linkedRequirementChips(source.linked_requirements)}</div>
			</div>
			<div>
				<label class="kt-std-cfg-ev-field-label">${
					source.minimum_compliance
						? __("Minimum Compliance")
						: source.minimum_score
							? __("Passmark Threshold")
							: __("Evaluation Type")
				}</label>
				<p class="kt-std-cfg-ev-stage-card__metric">${shared._escapeHtml(detailValue)}</p>
				${detailSuffix ? `<span class="kt-std-cfg-ev-stage-card__hint">${detailSuffix}</span>` : ""}
			</div>
			<div class="kt-std-cfg-ev-stage-card__carry">
				<span>${shared._escapeHtml(source.carry_forward_label || __("Carry Forward"))}</span>
				<button type="button" class="kt-std-cfg-ev-toggle${carryChecked}" data-kt-std-stage-carry="${idx}"${carryDisabled} aria-pressed="${
					source.carry_forward !== false
				}">
					<span class="kt-std-cfg-ev-toggle__knob"></span>
				</button>
			</div>
		</div>
	</div>
</div>`;
	};

	ui.evaluationSetupStagesSection = function evaluationSetupStagesSection(data, stages, editable) {
		const source = data || {};
		const stageList = Array.isArray(stages) ? stages : [];
		const cards = stageList
			.map(function (stage, idx) {
				return ui.evaluationSetupStageCard(stage, idx, editable, idx === stageList.length - 1);
			})
			.join("");
		const addDisabled = editable ? "" : " disabled";
		return `
<div class="kt-std-cfg-ev-stages" data-testid="kt-std-cfg-ev-stages">
	<div class="kt-std-cfg-ev-stages__head">
		<h3><span class="material-symbols-outlined kt-std-icon">playlist_add_check</span>${__(
			"Sequence of Evaluation Stages",
		)}</h3>
		<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-add-stage${addDisabled}>
			<span class="material-symbols-outlined kt-std-icon">add</span>${__("Add New Stage")}
		</button>
	</div>
	${ui.evaluationSetupConflictBanner(source.conflict_check)}
	${ui.evaluationSetupReadyBanner(source.readiness_ok)}
	<div class="kt-std-cfg-ev-stage-list">${cards || `<p class="kt-std-cfg-empty">${__("No evaluation stages yet.")}</p>`}</div>
</div>`;
	};

	ui.evaluationSetupContextBanner = function evaluationSetupContextBanner(data) {
		const source = data || {};
		return `
<div class="kt-std-cfg-ev-context" data-testid="kt-std-cfg-ev-context">
	<div>
		<p class="kt-std-cfg-ev-context__hint">
			<span class="material-symbols-outlined kt-std-icon">info</span>
			${__("Define the logical sequence and criteria for evaluating supplier bids.")}
		</p>
	</div>
	<div class="kt-std-cfg-ev-context__updated">
		<p>${__("LAST UPDATED")}</p>
		<strong>${shared._escapeHtml(_formatLastUpdated(source.last_updated))}</strong>
	</div>
</div>`;
	};

	ui.evaluationSetupTabDocument = function evaluationSetupTabDocument(parts) {
		const p = parts || {};
		return `
<section class="kt-std-cfg-tab-stack" data-testid="kt-std-cfg-evaluation">
	<div class="kt-std-cfg-ev-layout">
		${p.context || ""}
		${p.basis || ""}
		${p.bento || ""}
		${p.stages || ""}
	</div>
	${p.drawer || ""}
	${p.footer || ""}
</section>`;
	};

	ui.stageDetailDrawerBody = function stageDetailDrawerBody(row, editable) {
		const source = row || {};
		const disabled = editable ? "" : " disabled";
		const stageTypes = ["Preliminary", "Technical", "Financial", "Post-Qualification"];
		const typeOptions = stageTypes
			.map(function (opt) {
				const selected = String(source.stage_type || "") === opt ? " selected" : "";
				return `<option${selected}>${opt}</option>`;
			})
			.join("");
		const isScored = String(source.evaluation_type || "").toLowerCase().includes("scored");
		const linkedItems = Array.isArray(source.linked_requirements) ? source.linked_requirements : [];
		const linkedHtml = linkedItems
			.map(function (req) {
				const label = typeof req === "string" ? req : req.label || "";
				return `<div class="kt-std-cfg-ev-drawer-chip"><span>${shared._escapeHtml(label)}</span></div>`;
			})
			.join("");
		return `
<div class="kt-std-cfg-drawer-form">
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Stage Name")}</label>
		<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="name" value="${shared._escapeHtml(
			source.name || "",
		)}"${disabled} />
	</div>
	<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Stage Type")}</label>
			<select class="kt-std-cfg-input" data-kt-std-drawer-field="stage_type"${disabled}>${typeOptions}</select>
		</div>
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Sequence")}</label>
			<input class="kt-std-cfg-input" type="number" data-kt-std-drawer-field="sequence" value="${shared._escapeHtml(
				String(source.sequence != null ? source.sequence : ""),
			)}"${disabled} />
		</div>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Description")}</label>
		<textarea class="kt-std-cfg-input" data-kt-std-drawer-field="description" rows="2"${disabled}>${shared._escapeHtml(
			source.description || "",
		)}</textarea>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Evaluation Method")}</label>
		<select class="kt-std-cfg-input" data-kt-std-drawer-field="evaluation_type"${disabled}>
			<option${isScored ? "" : " selected"}>${__("Pass / Fail")}</option>
			<option${isScored ? " selected" : ""}>${__("Scored")}</option>
		</select>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Linked Supplier Requirements")}</label>
		<div class="kt-std-cfg-ev-drawer-links">${linkedHtml || `<p class="kt-std-cfg-empty">${__("No requirements linked.")}</p>`}</div>
	</div>
	<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Min Score / Pass Rule")}</label>
			<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="minimum_score" value="${shared._escapeHtml(
				source.minimum_score || "",
			)}" placeholder="75%"${disabled} />
		</div>
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Weight %")}</label>
			<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="weight" value="${shared._escapeHtml(
				source.weight || "",
			)}"${disabled} />
		</div>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Evaluator Instructions")}</label>
		<textarea class="kt-std-cfg-input" data-kt-std-drawer-field="evaluator_instructions" rows="3" placeholder="${__(
			"Enter instructions for the evaluation committee...",
		)}"${disabled}>${shared._escapeHtml(source.evaluator_instructions || "")}</textarea>
	</div>
	<label class="kt-std-cfg-checkbox">
		<input type="checkbox" data-kt-std-drawer-field="carry_forward"${
			source.carry_forward !== false ? " checked" : ""
		}${disabled} />
		<span>${__("Carry forward to next stage")}</span>
	</label>
</div>`;
	};

	const GOVERNING_CONTRACT_FORM_OPTIONS = [
		{
			value: "FIDIC Red Book (Building and Engineering Works)",
			label: __("FIDIC Red Book (Building and Engineering Works)"),
		},
		{ value: "Public Works Contract (Standard Version)", label: __("Public Works Contract (Standard Version)") },
		{
			value: "NEC4 Engineering and Construction Contract",
			label: __("NEC4 Engineering and Construction Contract"),
		},
		{ value: "Design and Build (Lump Sum) Contract", label: __("Design and Build (Lump Sum) Contract") },
	];

	const TERM_TYPE_OPTIONS = ["Financial", "Performance", "Legal", "Administrative"];

	function _termTypeClass(termType) {
		const text = String(termType || "").toLowerCase();
		if (text.includes("performance")) return "kt-std-cfg-ct-type--performance";
		if (text.includes("legal")) return "kt-std-cfg-ct-type--legal";
		return "kt-std-cfg-ct-type--financial";
	}

	function _termFlagClass(value) {
		const text = String(value == null ? "" : value).toLowerCase();
		if (text === "yes" || text === "true" || value === true) return "kt-std-cfg-ct-flag--yes";
		if (text.includes("conditional")) return "kt-std-cfg-ct-flag--conditional";
		if (text.includes("summary") || text.includes("after award")) return "kt-std-cfg-ct-flag--muted";
		if (text === "n/a" || text === "na") return "kt-std-cfg-ct-flag--na";
		return "kt-std-cfg-ct-flag--no";
	}

	function _termFlagIcon(value) {
		const text = String(value == null ? "" : value).toLowerCase();
		if (text === "yes" || text === "true" || value === true) return "check_circle";
		if (text.includes("conditional")) return "help";
		return "cancel";
	}

	function _termFlagLabel(value) {
		if (value === true) return __("Yes");
		if (value === false) return __("No");
		return value ? String(value) : __("No");
	}

	function _termYesNoBadge(value) {
		if (value === true || String(value).toLowerCase() === "yes") {
			return `<span class="kt-std-cfg-ct-badge kt-std-cfg-ct-badge--yes">${__("Yes")}</span>`;
		}
		if (value === false || String(value).toLowerCase() === "no") {
			return `<span class="kt-std-cfg-ct-badge kt-std-cfg-ct-badge--muted">${__("N/A")}</span>`;
		}
		return `<span class="kt-std-cfg-ct-badge">${shared._escapeHtml(String(value))}</span>`;
	}

	ui.GOVERNING_CONTRACT_FORM_OPTIONS = GOVERNING_CONTRACT_FORM_OPTIONS;

	ui.contractTermsContextBanner = function contractTermsContextBanner(data) {
		const source = data || {};
		return `
<div class="kt-std-cfg-ct-context" data-testid="kt-std-cfg-ct-context">
	<div>
		<p class="kt-std-cfg-ct-context__body">${__(
			"Define the contractual terms and financial guardrails that carry forward into the award and contract management phase.",
		)}</p>
	</div>
	<div class="kt-std-cfg-ct-context__status">
		<span class="material-symbols-outlined kt-std-icon">gavel</span>
		<p>${__("STATUS")}</p>
		<strong>${shared._escapeHtml(source.configuration_status || __("In Configuration"))}</strong>
	</div>
</div>`;
	};

	ui.contractTermsGoverningFormPanel = function contractTermsGoverningFormPanel(data, editable) {
		const source = data || {};
		const disabled = editable ? "" : " disabled";
		const options = GOVERNING_CONTRACT_FORM_OPTIONS.map(function (opt) {
			const selected = String(source.governing_contract_form || "") === opt.value ? " selected" : "";
			return `<option value="${shared._escapeHtml(opt.value)}"${selected}>${opt.label}</option>`;
		}).join("");
		return `
<div class="kt-std-cfg-ct-governing" data-testid="kt-std-cfg-ct-governing">
	<label class="kt-std-cfg-ct-governing__label">${__("Governing Contract Form")}</label>
	<div class="kt-std-cfg-ct-governing__select">
		<select class="kt-std-cfg-input" data-kt-std-field="governing_contract_form"${disabled}>${options}</select>
		<span class="material-symbols-outlined kt-std-icon">expand_more</span>
	</div>
	<p class="kt-std-cfg-ct-governing__hint">${__(
		"This selection will automatically pre-populate mandatory legal clauses and standard conditions.",
	)}</p>
</div>`;
	};

	ui.contractTermsMatrixSection = function contractTermsMatrixSection(terms, editable) {
		const rows = Array.isArray(terms) ? terms : [];
		const body = rows
			.map(function (row, idx) {
				const source = row || {};
				const overrideChecked = source.override_allowed ? " checked" : "";
				const overrideDisabled = editable ? "" : " disabled";
				return `
<tr class="kt-std-cfg-ct-term-row" data-kt-std-term-row="${idx}" data-testid="kt-std-cfg-ct-term-row">
	<td class="kt-std-cfg-ct-term-name">${shared._escapeHtml(source.title || __("Term"))}</td>
	<td class="kt-std-cfg-ct-mono">${shared._escapeHtml(source.clause_reference || "")}</td>
	<td><span class="kt-std-cfg-ct-type ${_termTypeClass(source.term_type)}">${shared._escapeHtml(
					source.term_type || "",
				)}</span></td>
	<td><span class="kt-std-cfg-ct-flag ${_termFlagClass(source.required)}"><span class="material-symbols-outlined kt-std-icon">${_termFlagIcon(
					source.required,
				)}</span>${shared._escapeHtml(_termFlagLabel(source.required))}</span></td>
	<td class="kt-std-cfg-ct-mono">${shared._escapeHtml(source.default_value || "")}</td>
	<td>
		<button type="button" class="kt-std-cfg-ct-toggle${overrideChecked ? " is-on" : ""}" data-kt-std-term-override="${idx}"${overrideDisabled} aria-pressed="${!!source.override_allowed}">
			<span class="kt-std-cfg-ct-toggle__knob"></span>
		</button>
	</td>
	<td>${_termYesNoBadge(source.approval_required)}</td>
	<td><span class="kt-std-cfg-ct-flag ${_termFlagClass(source.carries_to_contract)}"><span class="material-symbols-outlined kt-std-icon">${_termFlagIcon(
					source.carries_to_contract,
				)}</span>${shared._escapeHtml(_termFlagLabel(source.carries_to_contract))}</span></td>
	<td>${source.visible_to_supplier === true || String(source.visible_to_supplier).toLowerCase() === "yes"
		? `<span class="kt-std-cfg-ct-flag kt-std-cfg-ct-flag--yes"><span class="material-symbols-outlined kt-std-icon">check_circle</span>${__(
				"Yes",
			)}</span>`
		: `<span class="kt-std-cfg-ct-badge">${shared._escapeHtml(_termFlagLabel(source.visible_to_supplier))}</span>`}</td>
	<td class="kt-std-cfg-ct-actions-cell">
		<button type="button" class="kt-std-cfg-ct-configure" data-kt-std-term-edit="${idx}" aria-label="${__(
			"Configure term",
		)}"><span class="material-symbols-outlined kt-std-icon">settings</span></button>
	</td>
</tr>`;
			})
			.join("");
		const addDisabled = editable ? "" : " disabled";
		return `
<section class="kt-std-cfg-ct-matrix" data-testid="kt-std-cfg-ct-matrix">
	<div class="kt-std-cfg-ct-matrix__head">
		<h3>${__("Contract Terms & Conditions")}</h3>
		<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-add-term${addDisabled}>
			<span class="material-symbols-outlined kt-std-icon">add</span>${__("Add Custom Term")}
		</button>
	</div>
	<div class="kt-std-cfg-ct-table-wrap">
		<table class="kt-std-cfg-ct-table">
			<thead>
				<tr>
					<th>${__("Term Name")}</th>
					<th>${__("Clause Reference")}</th>
					<th>${__("Type")}</th>
					<th>${__("Required")}</th>
					<th>${__("Default Value")}</th>
					<th>${__("Tender-Level Override Allowed")}</th>
					<th>${__("Approval Required for Change")}</th>
					<th>${__("Carries to Contract")}</th>
					<th>${__("Visible to Supplier")}</th>
					<th class="kt-std-cfg-ct-actions-head">${__("Actions")}</th>
				</tr>
			</thead>
			<tbody>${body || `<tr><td colspan="10" class="kt-std-cfg-empty">${__("No contract terms yet.")}</td></tr>`}</tbody>
		</table>
	</div>
</section>`;
	};

	ui.contractTermsReadinessSection = function contractTermsReadinessSection(readiness, issueCount) {
		const items = Array.isArray(readiness) ? readiness : [];
		const issues = issueCount == null ? items.filter(function (i) { return i.status === "warn"; }).length : issueCount;
		const grid = items
			.map(function (item) {
				const icon =
					item.status === "warn" ? "warning" : item.status === "ok" ? "check_circle" : "info";
				const tone =
					item.status === "warn"
						? "kt-std-cfg-ct-readiness-item--warn"
						: "kt-std-cfg-ct-readiness-item--ok";
				return `
<div class="kt-std-cfg-ct-readiness-item ${tone}">
	<span class="material-symbols-outlined kt-std-icon">${icon}</span>
	<span>${shared._escapeHtml(item.label || "")}</span>
</div>`;
			})
			.join("");
		return `
<section class="kt-std-cfg-ct-readiness" data-testid="kt-std-cfg-ct-readiness">
	<div class="kt-std-cfg-ct-readiness__head">
		<h3>${__("Readiness Checklist")}</h3>
	</div>
	<div class="kt-std-cfg-ct-readiness__grid">${grid}</div>
	${
		issues
			? `<div class="kt-std-cfg-ct-issues" data-testid="kt-std-cfg-ct-issues">
		<span class="material-symbols-outlined kt-std-icon">error</span>
		<strong>${__("Contract Terms: {0} issues to resolve", [issues])}</strong>
	</div>`
			: ""
	}
</section>`;
	};

	ui.contractTermsTabDocument = function contractTermsTabDocument(parts) {
		const p = parts || {};
		return `
<section class="kt-std-cfg-tab-stack" data-testid="kt-std-cfg-contract-terms">
	<div class="kt-std-cfg-ct-layout">
		${p.context || ""}
		${p.governing || ""}
		${p.matrix || ""}
		${p.readiness || ""}
	</div>
	${p.drawer || ""}
	${p.footer || ""}
</section>`;
	};

	ui.termDetailDrawerBody = function termDetailDrawerBody(row, editable) {
		const source = row || {};
		const disabled = editable ? "" : " disabled";
		const typeOptions = TERM_TYPE_OPTIONS.map(function (opt) {
			const selected = String(source.term_type || "") === opt ? " selected" : "";
			return `<option${selected}>${opt}</option>`;
		}).join("");
		const requiredOptions = [__("Yes"), __("No"), __("Conditional")]
			.map(function (opt) {
				const selected = String(source.required || "") === opt ? " selected" : "";
				return `<option${selected}>${opt}</option>`;
			})
			.join("");
		return `
<div class="kt-std-cfg-drawer-form">
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Term Name")}</label>
		<input class="kt-std-cfg-input" type="text" data-kt-std-drawer-field="title" value="${shared._escapeHtml(
			source.title || "",
		)}"${disabled} />
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Clause Reference")}</label>
		<input class="kt-std-cfg-input kt-std-cfg-input--mono" type="text" data-kt-std-drawer-field="clause_reference" value="${shared._escapeHtml(
			source.clause_reference || "",
		)}"${disabled} />
	</div>
	<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Type")}</label>
			<select class="kt-std-cfg-input" data-kt-std-drawer-field="term_type"${disabled}>${typeOptions}</select>
		</div>
		<div class="kt-std-cfg-field">
			<label class="kt-std-cfg-field__label">${__("Required")}</label>
			<select class="kt-std-cfg-input" data-kt-std-drawer-field="required"${disabled}>${requiredOptions}</select>
		</div>
	</div>
	<div class="kt-std-cfg-field">
		<label class="kt-std-cfg-field__label">${__("Default Value")}</label>
		<input class="kt-std-cfg-input kt-std-cfg-input--mono" type="text" data-kt-std-drawer-field="default_value" value="${shared._escapeHtml(
			source.default_value || "",
		)}"${disabled} />
	</div>
	<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
		<label class="kt-std-cfg-checkbox">
			<input type="checkbox" data-kt-std-drawer-field="override_allowed"${
				source.override_allowed ? " checked" : ""
			}${disabled} />
			<span>${__("Tender-level override allowed")}</span>
		</label>
		<label class="kt-std-cfg-checkbox">
			<input type="checkbox" data-kt-std-drawer-field="approval_required"${
				source.approval_required ? " checked" : ""
			}${disabled} />
			<span>${__("Approval required for change")}</span>
		</label>
	</div>
	<div class="kt-std-cfg-form kt-std-cfg-form--drawer-two">
		<label class="kt-std-cfg-checkbox">
			<input type="checkbox" data-kt-std-drawer-field="carries_to_contract"${
				source.carries_to_contract === true ||
				String(source.carries_to_contract || "").toLowerCase() === "yes"
					? " checked"
					: ""
			}${disabled} />
			<span>${__("Carries to contract")}</span>
		</label>
		<label class="kt-std-cfg-checkbox">
			<input type="checkbox" data-kt-std-drawer-field="visible_to_supplier"${
				source.visible_to_supplier === true ||
				String(source.visible_to_supplier || "").toLowerCase() === "yes"
					? " checked"
					: ""
			}${disabled} />
			<span>${__("Visible to supplier")}</span>
		</label>
	</div>
</div>`;
	};

	// Harmonized auxiliary tabs (rules, preview, approval, evidence, technical JSON)
	ui.auxLayout = function auxLayout(innerHtml) {
		return `<div class="kt-std-cfg-aux-layout">${innerHtml || ""}</div>`;
	};

	ui.auxSectionPanel = function auxSectionPanel(opts) {
		const o = opts || {};
		const testid = o.testid ? ` data-testid="${o.testid}"` : "";
		const subtitle = o.subtitle
			? `<p class="kt-std-cfg-aux-panel__subtitle">${shared._escapeHtml(o.subtitle)}</p>`
			: "";
		const actions = o.actions ? `<div class="kt-std-cfg-aux-panel__actions">${o.actions}</div>` : "";
		const icon = o.icon
			? `<span class="material-symbols-outlined kt-std-icon">${shared._escapeHtml(o.icon)}</span>`
			: "";
		return `
<section class="kt-std-cfg-aux-panel"${testid}>
	<div class="kt-std-cfg-aux-panel__head">
		<div class="kt-std-cfg-aux-panel__titles">
			<h3>${icon}${shared._escapeHtml(o.title || "")}</h3>
			${subtitle}
		</div>
		${actions}
	</div>
	<div class="kt-std-cfg-aux-panel__body">${o.body || ""}</div>
</section>`;
	};

	ui.auxReadonlyTable = function auxReadonlyTable(columns, rows, emptyMsg, testid) {
		const headers = (columns || [])
			.map(function (col) {
				return `<th>${shared._escapeHtml(col.label || "")}</th>`;
			})
			.join("");
		const body =
			rows && rows.length
				? rows
						.map(function (row) {
							const cells = (columns || [])
								.map(function (col) {
									const val = row && row[col.key] != null ? row[col.key] : "";
									return `<td>${shared._escapeHtml(String(val))}</td>`;
								})
								.join("");
							return `<tr>${cells}</tr>`;
						})
						.join("")
				: `<tr><td colspan="${(columns || []).length || 1}" class="kt-std-cfg-empty">${shared._escapeHtml(
						emptyMsg || __("No records yet."),
					)}</td></tr>`;
		const tid = testid ? ` data-testid="${testid}"` : "";
		return `<div class="kt-std-cfg-aux-table-wrap"><table class="kt-std-cfg-aux-table"${tid}><thead><tr>${headers}</tr></thead><tbody>${body}</tbody></table></div>`;
	};

	ui.rulesValidationsRuleListHtml = function rulesValidationsRuleListHtml(rules) {
		const items = (rules || [])
			.map(function (rule) {
				const when = shared._escapeHtml(rule.when || rule.code || "");
				const then = shared._escapeHtml(rule.then || rule.action || "");
				return `<li class="kt-std-cfg-aux-rule-item">
		<span class="kt-std-cfg-aux-rule-label">${__("When")}</span>
		<span class="kt-std-cfg-aux-rule-when">${when}</span>
		<span class="kt-std-cfg-aux-rule-arrow material-symbols-outlined">arrow_forward</span>
		<span class="kt-std-cfg-aux-rule-label">${__("Then")}</span>
		<span class="kt-std-cfg-aux-rule-then">${then}</span>
	</li>`;
			})
			.join("");
		return `<ul class="kt-std-cfg-aux-rule-list" data-testid="kt-std-cfg-rv-rules-list">${
			items || `<li class="kt-std-cfg-aux-empty">${__("No rules configured yet.")}</li>`
		}</ul>`;
	};

	ui.rulesValidationsRulesSection = function rulesValidationsRulesSection(rules, editable) {
		const composer = editable
			? `<div class="kt-std-cfg-aux-composer">
		<input class="kt-std-cfg-input" type="text" placeholder="${__("When condition…")}" data-kt-std-rule-when />
		<input class="kt-std-cfg-input" type="text" placeholder="${__("Then action…")}" data-kt-std-rule-then />
		<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-add-rule>${__("Add rule")}</button>
	</div>`
			: "";
		return ui.auxSectionPanel({
			icon: "rule",
			title: __("Business Rules"),
			subtitle: __("Define when/then logic applied during tender configuration."),
			testid: "kt-std-cfg-rv-rules",
			body: `${composer}${ui.rulesValidationsRuleListHtml(rules)}`,
		});
	};

	ui.rulesValidationsValidationsSection = function rulesValidationsValidationsSection(validations) {
		const count = (validations || []).length;
		const items = (validations || [])
			.map(function (validation) {
				const label =
					typeof validation === "string"
						? validation
						: validation.message || validation.code || JSON.stringify(validation);
				return `<li>${shared._escapeHtml(String(label))}</li>`;
			})
			.join("");
		return ui.auxSectionPanel({
			icon: "fact_check",
			title: __("Cross-field Validations"),
			subtitle: __("Schema-level checks enforced before approval."),
			testid: "kt-std-cfg-rv-validations",
			body: `<p class="kt-std-cfg-aux-summary">${__("Validations configured: {0}", [count])}</p>
	<ul class="kt-std-cfg-aux-bullet-list">${items || `<li class="kt-std-cfg-aux-empty">${__(
		"No validations configured yet.",
	)}</li>`}</ul>`,
		});
	};

	ui.rulesValidationsTabDocument = function rulesValidationsTabDocument(parts) {
		const p = parts || {};
		return `
<section class="kt-std-cfg-tab-stack" data-testid="kt-std-cfg-rules">
	${ui.auxLayout(`${p.rules || ""}${p.validations || ""}`)}
	${p.footer || ""}
</section>`;
	};

	ui.previewModeBar = function previewModeBar(modes, activeKey) {
		const pills = (modes || [])
			.map(function (mode) {
				const active = mode.key === activeKey ? " is-active" : "";
				return `<button type="button" class="kt-std-cfg-aux-pill${active}" data-kt-std-preview-mode="${shared._escapeHtml(
					mode.key,
				)}">${shared._escapeHtml(mode.label)}</button>`;
			})
			.join("");
		return `<div class="kt-std-cfg-aux-preview-bar" data-testid="kt-std-cfg-preview-modes">
	<span class="kt-std-cfg-aux-preview-label">${__("Preview lens")}</span>
	<div class="kt-std-cfg-aux-preview-pills">${pills}</div>
</div>`;
	};

	ui.previewTabDocument = function previewTabDocument(parts) {
		const p = parts || {};
		return `
<section class="kt-std-cfg-tab-stack" data-testid="kt-std-cfg-preview">
	${ui.auxLayout(`${p.modes || ""}${p.body || ""}`)}
	${p.footer || ""}
</section>`;
	};

	ui.approvalIssueListHtml = function approvalIssueListHtml(issues) {
		const items = (issues || [])
			.map(function (issue) {
				const label =
					typeof issue === "string" ? issue : issue.message || issue.code || JSON.stringify(issue);
				return `<li class="kt-std-cfg-aux-issue-item">
		<span class="material-symbols-outlined kt-std-icon">error</span>
		<span>${shared._escapeHtml(String(label))}</span>
	</li>`;
			})
			.join("");
		return `<ul class="kt-std-cfg-aux-issue-list" data-testid="kt-std-cfg-approval-issues">${
			items || `<li class="kt-std-cfg-aux-empty">${__("No validation issues — ready for governance actions.")}</li>`
		}</ul>`;
	};

	ui.approvalGovernanceSection = function approvalGovernanceSection() {
		return ui.auxSectionPanel({
			icon: "gavel",
			title: __("Governance Actions"),
			subtitle: __("Submit, activate, or retire this STD version after validation passes."),
			testid: "kt-std-cfg-approval-governance",
			body: `<div class="kt-std-cfg-aux-governance">
		<button type="button" class="kt-std-cfg-btn" data-kt-std-return>${__("Return")}</button>
		<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-submit-review>${__(
			"Submit for review",
		)}</button>
		<button type="button" class="kt-std-cfg-btn" data-kt-std-activate>${__("Activate version")}</button>
		<button type="button" class="kt-std-cfg-btn" data-kt-std-retire>${__("Retire")}</button>
	</div>`,
		});
	};

	ui.approvalTabDocument = function approvalTabDocument(parts) {
		const p = parts || {};
		return `
<section class="kt-std-cfg-tab-stack" data-testid="kt-std-cfg-approval">
	${ui.auxLayout(`${p.summary || ""}${p.issues || ""}${p.governance || ""}`)}
	${p.footer || ""}
</section>`;
	};

	ui.evidenceInventorySection = function evidenceInventorySection(rows) {
		return ui.auxSectionPanel({
			icon: "inventory_2",
			title: __("Section Evidence Inventory"),
			subtitle: __("Configured sections and their persisted status for this STD version."),
			testid: "kt-std-cfg-evidence-inventory",
			body: ui.auxReadonlyTable(
				[
					{ key: "section", label: __("Section") },
					{ key: "status", label: __("Status") },
				],
				rows,
				__("No evidence records yet."),
				"kt-std-cfg-table-evidence",
			),
		});
	};

	ui.evidenceTabDocument = function evidenceTabDocument(parts) {
		const p = parts || {};
		return `
<section class="kt-std-cfg-tab-stack" data-testid="kt-std-cfg-evidence">
	${ui.auxLayout(p.inventory || "")}
	${p.footer || ""}
</section>`;
	};

	ui.technicalJsonSection = function technicalJsonSection(jsonText, opts) {
		const o = opts || {};
		const editable = !!o.editable;
		const subtitle = editable
			? __("Editable package JSON for privileged technical administrators. Changes affect the full STD configuration.")
			: __("Read-only export of the full STD configuration package.");
		const body = editable
			? `<div class="kt-std-cfg-aux-technical-toolbar" data-testid="kt-std-cfg-technical-json-toolbar">
		<button type="button" class="kt-std-cfg-btn" data-kt-std-technical-json-validate>${__("Validate JSON")}</button>
		<button type="button" class="kt-std-cfg-btn" data-kt-std-technical-json-revert>${__("Revert")}</button>
		<button type="button" class="kt-std-cfg-btn kt-std-cfg-btn--primary" data-kt-std-technical-json-save>${__(
			"Save package JSON",
		)}</button>
	</div>
	<p class="kt-std-cfg-aux-technical-error hidden" data-testid="kt-std-cfg-technical-json-error"></p>
	<textarea class="kt-std-cfg-readonly kt-std-cfg-aux-code kt-std-cfg-aux-code--editable" data-testid="kt-std-cfg-technical-json-body" data-kt-std-technical-json-editor>${shared._escapeHtml(
				jsonText || "{}",
			)}</textarea>`
			: `<pre class="kt-std-cfg-readonly kt-std-cfg-aux-code" data-testid="kt-std-cfg-technical-json-body">${shared._escapeHtml(
					jsonText || "{}",
				)}</pre>`;
		return ui.auxSectionPanel({
			icon: "data_object",
			title: __("Technical Package JSON"),
			subtitle: subtitle,
			testid: "kt-std-cfg-technical-json-panel",
			body: body,
		});
	};

	ui.technicalJsonTabDocument = function technicalJsonTabDocument(parts) {
		const p = parts || {};
		return `
<section class="kt-std-cfg-tab-stack" data-testid="kt-std-cfg-technical-json">
	${ui.auxLayout(p.body || "")}
	${p.footer || ""}
</section>`;
	};

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
