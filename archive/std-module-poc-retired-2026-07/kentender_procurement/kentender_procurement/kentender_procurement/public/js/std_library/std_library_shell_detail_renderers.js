// STD-LIB-0500 — Detail panel tab HTML renderers (library page). Loads before std_library_shell.js.
// STD-LIB-0530: uses std_library_user_messages (loads earlier on std-engine page_js).
frappe.provide("kentender_procurement.std_library_detail_renderers");

(function () {
	const DEFAULT_UNAVAILABLE = __("Unavailable: this action is temporarily not available.");
	const userMsg = kentender_procurement.std_library_user_messages;
	const R = kentender_procurement.std_library_detail_renderers;

	function escHtml(str) {
		return frappe.utils.escape_html(String(str ?? ""));
	}

	R.renderSummaryTabContent = function (detail) {
		const summary = detail?.summary || {};
		const identity = summary.identity || {};
		const source = summary.source_evidence || {};
		const supported = summary.supported_use || {};
		const health = summary.health_summary || {};
		const output = summary.output_summary || {};
		const nextAction = summary.next_action || {};
		const methods = Array.isArray(supported.methods) ? supported.methods.join(", ") : "";
		return `
<section class="std-library-summary-tab" data-testid="std-library-summary-tab">
	<div class="std-library-summary-panel" data-testid="std-library-summary-identity">
		<h5>${__("STD Identity")}</h5>
		<p><strong>${__("Title")}:</strong> ${identity.title || ""}</p>
		<p><strong>${__("Revision")}:</strong> ${identity.revision || ""}</p>
		<p><strong>${__("Authority")}:</strong> ${identity.authority || ""}</p>
		<p><strong>${__("Template family")}:</strong> ${identity.template_family || ""}</p>
	</div>
	<div class="std-library-summary-panel" data-testid="std-library-summary-source-evidence">
		<h5>${__("Source Evidence")}</h5>
		<p><strong>${__("Source document")}:</strong> ${source.source_document || ""}</p>
		<p><strong>${__("Source file")}:</strong> ${source.source_file || ""}</p>
		<p><strong>${__("Source hash")}:</strong> ${source.source_hash || ""}</p>
		<p><strong>${__("Evidence status")}:</strong> ${source.evidence_status || ""}</p>
	</div>
	<div class="std-library-summary-panel" data-testid="std-library-summary-supported-use">
		<h5>${__("Supported Use")}</h5>
		<p><strong>${__("Category")}:</strong> ${supported.category || ""}</p>
		<p><strong>${__("Methods")}:</strong> ${methods || __("Not set")}</p>
		<p><strong>${__("Contract type")}:</strong> ${supported.contract_type || ""}</p>
		<p><strong>${__("Requires BOQ")}:</strong> ${supported.requires_boq || ""}</p>
	</div>
	<div class="std-library-summary-panel" data-testid="std-library-summary-health">
		<h5>${__("Health Summary")}</h5>
		<p><strong>${__("Validation")}:</strong> ${health.validation || ""}</p>
		<p><strong>${__("Bundle Preview")}:</strong> ${health.bundle_preview || ""}</p>
		<p><strong>${__("Generated Models")}:</strong> ${health.generated_models || ""}</p>
	</div>
	<div class="std-library-summary-panel">
		<h5>${__("Output Summary")}</h5>
		<p>${output.line || ""}</p>
	</div>
	<div class="std-library-summary-panel std-library-summary-next-action" data-testid="std-library-summary-next-action">
		<h5>${__("Next Action")}</h5>
		<p><strong>${nextAction.status || ""}:</strong> ${nextAction.action || ""}</p>
	</div>
</section>`;
	};

	R.renderValidationTabContent = function (detail) {
		const validation = detail?.validation || {};
		const categories = Array.isArray(validation.categories) ? validation.categories : [];
		const issues = Array.isArray(validation.issues) ? validation.issues : [];
		return `
<section class="std-library-validation-tab" data-testid="std-library-validation-tab">
	<div class="std-library-validation-overall">
		<strong>${__("Overall Health")}:</strong> ${validation.overall_status || __("Not Run")} (${validation.severity || __("Medium")})
	</div>
	<div class="std-library-validation-categories" data-testid="std-library-validation-categories">
		${categories
			.map(
				(c) =>
					`<div class="std-library-validation-category">
						<span class="std-library-validation-category-name">${c.category || ""}</span>
						<span class="std-library-validation-badge is-${String(c.state || "not-run")
							.toLowerCase()
							.replace(/\s+/g, "-")}">${c.state || __("Not Run")}</span>
					</div>`,
			)
			.join("")}
	</div>
	<div class="std-library-validation-findings" data-testid="std-library-validation-findings">
		<h5>${__("Findings")}</h5>
		<ul>
			${(issues.length ? issues : [__("No validation issues reported.")])
				.map((x) => `<li>${x}</li>`)
				.join("")}
		</ul>
		<p><strong>${__("Remediation")}:</strong> ${validation.remediation || __("No remediation required.")}</p>
	</div>
</section>`;
	};

	/** @param {object} bundleSectionState mutable { section: string } shared with outline click handlers */
	R.renderBundlePreviewTabContent = function (detail, bundleSectionState) {
		const bundle = detail?.bundle_preview || {};
		const statusBar = bundle.status_bar || {};
		const outline = Array.isArray(bundle.outline) ? bundle.outline : [];
		const previewBlocks = Array.isArray(bundle.preview_blocks) ? bundle.preview_blocks : [];
		const placeholders = Array.isArray(bundle.placeholders) ? bundle.placeholders : [];
		const actions = bundle.actions || {};
		const state = bundleSectionState || { section: "" };
		const activeSection =
			state.section && outline.includes(state.section) ? state.section : outline[0] || "";
		if (!state.section && activeSection) {
			state.section = activeSection;
		}

		const showBundleEmpty = outline.length === 0 && previewBlocks.length === 0;

		return `
<section class="std-library-bundle-tab" data-testid="std-library-bundle-tab">
	${
		showBundleEmpty
			? `<div class="std-library-bundle-empty std-library-placeholder-pane" data-testid="std-library-bundle-empty">
		<p class="std-library-bundle-empty-title">${userMsg.MSG_BUNDLE_PREVIEW_EMPTY_TITLE}</p>
		<p class="std-library-bundle-empty-hint">${userMsg.MSG_BUNDLE_PREVIEW_EMPTY_HINT}</p>
	</div>`
			: ""
	}
	<div class="std-bundle-status-bar" data-testid="std-bundle-status-bar">
		<span><strong>${__("Preview status")}:</strong> ${statusBar.preview_status || __("Not Generated")}</span>
		<span><strong>${__("Last generated")}:</strong> ${statusBar.last_generated || __("Not generated yet")}</span>
		<span><strong>${__("Output type")}:</strong> ${statusBar.output_type || __("Template-level preview")}</span>
		<span><strong>${__("Placeholder count")}:</strong> ${Number(statusBar.placeholder_count || 0)}</span>
		<span><strong>${__("Render warnings")}:</strong> ${Number(statusBar.render_warnings || 0)}</span>
	</div>
	<div class="std-bundle-main">
		<nav class="std-bundle-outline" data-testid="std-bundle-outline">
			${outline
				.map(
					(section) =>
						`<button type="button" class="std-bundle-outline-item${
							section === activeSection ? " is-active" : ""
						}" data-outline-target="${escHtml(section)}" aria-current="${
							section === activeSection ? "true" : "false"
						}">${section}</button>`,
				)
				.join("")}
		</nav>
		<div class="std-bundle-preview-pane" data-testid="std-bundle-preview-pane">
			${previewBlocks
				.map((block) => {
					const section = block.section || "";
					return `<article class="std-bundle-preview-block${
						section === activeSection ? " is-active" : ""
					}" data-bundle-section="${section}">
						<h5>${section}</h5>
						<p>${block.content || ""}</p>
					</article>`;
				})
				.join("")}
		</div>
	</div>
	<div class="std-bundle-placeholder-panel" data-testid="std-bundle-placeholder-panel">
		${placeholders
			.map((group) => {
				const rows = Array.isArray(group.rows) ? group.rows : [];
				return `<section class="std-bundle-placeholder-group">
					<h5>${group.group || ""}</h5>
					${rows
						.map(
							(row) => `<div class="std-bundle-placeholder-row">
								<span><strong>${__("Placeholder")}:</strong> ${row.label || ""}</span>
								<span><strong>${__("Filled during")}:</strong> ${row.filled_during || ""}</span>
								<span><strong>${__("Source section")}:</strong> ${row.source_section || ""}</span>
								<span><strong>${__("Output impact")}:</strong> ${row.output_impact || ""}</span>
							</div>`,
						)
						.join("")}
				</section>`;
			})
			.join("")}
	</div>
	<div class="std-bundle-actions">
		${
			actions.generate_preview?.allowed
				? ""
				: `<span id="std-bundle-generate-preview-reason" class="std-library-sr-only">${escHtml(
						actions.generate_preview?.message || DEFAULT_UNAVAILABLE,
					)}</span>`
		}
		<button type="button" class="btn btn-default btn-xs" data-testid="std-bundle-generate-preview" ${
			actions.generate_preview?.allowed ? "" : "disabled"
		} title="${escHtml(actions.generate_preview?.message || DEFAULT_UNAVAILABLE)}" ${
			actions.generate_preview?.allowed ? "" : 'aria-describedby="std-bundle-generate-preview-reason"'
		}>${__("Generate Preview")}</button>
		${
			actions.download_pdf?.visible
				? `${
						actions.download_pdf?.allowed
							? ""
							: `<span id="std-bundle-download-pdf-reason" class="std-library-sr-only">${escHtml(
									actions.download_pdf?.message || DEFAULT_UNAVAILABLE,
								)}</span>`
					}<button type="button" class="btn btn-default btn-xs" data-testid="std-bundle-download-pdf" ${
						actions.download_pdf?.allowed ? "" : "disabled"
					} title="${escHtml(actions.download_pdf?.message || DEFAULT_UNAVAILABLE)}" ${
						actions.download_pdf?.allowed ? "" : 'aria-describedby="std-bundle-download-pdf-reason"'
					}>${__("Download PDF")}</button>`
				: ""
		}
		${
			actions.download_docx?.visible
				? `${
						actions.download_docx?.allowed
							? ""
							: `<span id="std-bundle-download-docx-reason" class="std-library-sr-only">${escHtml(
									actions.download_docx?.message || DEFAULT_UNAVAILABLE,
								)}</span>`
					}<button type="button" class="btn btn-default btn-xs" data-testid="std-bundle-download-docx" ${
						actions.download_docx?.allowed ? "" : "disabled"
					} title="${escHtml(actions.download_docx?.message || DEFAULT_UNAVAILABLE)}" ${
						actions.download_docx?.allowed ? "" : 'aria-describedby="std-bundle-download-docx-reason"'
					}>${__("Download DOCX")}</button>`
				: ""
		}
	</div>
</section>`;
	};

	R.renderUsageRows = function (rows, formatter) {
		const list = Array.isArray(rows) ? rows : [];
		if (!list.length) {
			return `<div class="std-usage-empty">${__("No records found.")}</div>`;
		}
		return list.map(formatter).join("");
	};

	R.renderUsageTabContent = function (detail) {
		const usage = detail?.usage || {};
		const summary = usage.summary || {};
		const tenders = usage.tenders;
		const tenderFormatter = (row) => {
			const linkInner = row.open_route
				? `<a class="std-usage-row-link" href="${escHtml(row.open_route)}" data-testid="std-usage-tender-open-link">${escHtml(row.view_label || __("Open tender"))}</a>`
				: `<span class="std-usage-view-label">${escHtml(row.view_label || "")}</span>`;
			return `<div class="std-usage-row" data-testid="std-usage-tender-row">
			<span class="std-usage-primary"><strong>${__("Title")}:</strong> ${escHtml(row.title || "")} <span class="text-muted">${escHtml(row.code ? `(${row.code})` : "")}</span></span>
			<span><strong>${__("Status")}:</strong> ${escHtml(row.status || "")}</span>
			<span><strong>${__("Procuring entity")}:</strong> ${escHtml(row.procuring_entity || __("Not set"))}</span>
			${linkInner}
		</div>`;
		};
		const journeyFormatter = (row) => {
			const jc = escHtml(row.journey_code || "");
			const title = escHtml(row.title || "");
			const ent = row.procuring_entity ? escHtml(row.procuring_entity) : escHtml(__("Not set"));
			const linkInner = row.open_route
				? `<a class="std-usage-row-link" href="${escHtml(row.open_route)}" data-testid="std-usage-journey-open-link">${escHtml(row.view_label || __("Open journey"))}</a>`
				: `<span class="std-usage-view-label">${escHtml(row.view_label || "")}</span>`;
			return `<div class="std-usage-row" data-testid="std-usage-journey-row">
			<span class="std-usage-primary"><strong>${__("Title")}:</strong> ${title}${jc ? ` <span class="text-muted std-usage-row-code">${jc}</span>` : ""}</span>
			<span><strong>${__("Procuring entity")}:</strong> ${ent}</span>
			${linkInner}
		</div>`;
		};
		return `
<section class="std-library-usage-tab" data-testid="std-library-usage-tab">
	<div class="std-usage-panel" data-testid="std-usage-summary">
		<h5>${__("Usage Summary")}</h5>
		<p><strong>${__("Procurement journeys using this catalogue row")}:</strong> ${Number(summary.journeys_using_count || 0)}</p>
		<p><strong>${__("Linked tenders matching version references")}:</strong> ${Number(summary.tenders_using_count || 0)}</p>
	</div>
	<div class="std-usage-panel" data-testid="std-usage-journey-list">
		<h5>${__("Procurement Journeys")}</h5>
		${R.renderUsageRows(usage.journeys, journeyFormatter)}
	</div>
	<div class="std-usage-panel" data-testid="std-usage-tender-list">
		<h5>${__("Tenders")}</h5>
		${R.renderUsageRows(tenders, tenderFormatter)}
	</div>
	<div class="std-usage-panel" data-testid="std-usage-instance-list">
		<h5>${__("STD Instance References")}</h5>
		${R.renderUsageRows(usage.instances, (row) => `<div class="std-usage-row">
			<span><strong>${__("Instance Code")}:</strong> ${row.code || ""}</span>
			<span><strong>${__("Status")}:</strong> ${row.status || ""}</span>
			<span><strong>${__("Publication State")}:</strong> ${row.publication_state || ""}</span>
			<span class="std-usage-view-label">${__("View STD Instance Read-Only")}</span>
		</div>`)}
	</div>
	<div class="std-usage-panel" data-testid="std-usage-output-list">
		<h5>${__("Published Bundle References")}</h5>
		${R.renderUsageRows(usage.outputs, (row) => `<div class="std-usage-row">
			<span><strong>${__("Output Code")}:</strong> ${row.output_code || ""}</span>
			<span><strong>${__("Version")}:</strong> ${row.version || ""}</span>
			<span class="std-usage-view-label">${__("View Evidence")}</span>
		</div>`)}
	</div>
	<div class="std-usage-panel" data-testid="std-usage-addendum-list">
		<h5>${__("Addendum Impact References")}</h5>
		${R.renderUsageRows(usage.addenda, (row) => `<div class="std-usage-row">
			<span><strong>${__("Addendum Code")}:</strong> ${row.addendum_code || ""}</span>
			<span><strong>${__("Linked Context")}:</strong> ${row.linked_context || ""}</span>
			<span class="std-usage-view-label">${__("View Evidence")}</span>
		</div>`)}
	</div>
</section>`;
	};

	R.renderSupersessionTabContent = function (detail) {
		const supersession = detail?.supersession || {};
		const lineage = supersession.lineage || {};
		const impact = supersession.impact || {};
		const actions = supersession.actions || {};
		return `
<section class="std-library-supersession-tab" data-testid="std-library-supersession-tab">
	<div class="std-supersession-panel" data-testid="std-supersession-lineage">
		<h5>${__("Version Lineage")}</h5>
		<p><strong>${__("Current version")}:</strong> ${lineage.current_version || ""}</p>
		<p><strong>${__("Supersedes")}:</strong> ${lineage.supersedes || __("None")}</p>
		<p><strong>${__("Superseded by")}:</strong> ${lineage.superseded_by || __("None")}</p>
		<p><strong>${__("Reason")}:</strong> ${lineage.reason || ""}</p>
		<p><strong>${__("Effective date")}:</strong> ${lineage.effective_date || ""}</p>
	</div>
	<div class="std-supersession-panel" data-testid="std-supersession-existing-tender-impact">
		<h5>${__("Existing Tender Impact")}</h5>
		<p>${impact.existing_tender_impact || ""}</p>
		<p><strong>${__("New tenders impact")}:</strong> ${impact.new_tenders_impact || ""}</p>
	</div>
	<div class="std-supersession-panel std-supersession-actions">
		${
			actions.create_new_revision?.allowed
				? ""
				: `<span id="std-supersession-create-revision-reason" class="std-library-sr-only">${escHtml(
						actions.create_new_revision?.message || DEFAULT_UNAVAILABLE,
					)}</span>`
		}
		<button type="button" class="btn btn-default btn-xs" data-testid="std-supersession-create-revision" ${
			actions.create_new_revision?.allowed ? "" : "disabled"
		} title="${escHtml(actions.create_new_revision?.message || DEFAULT_UNAVAILABLE)}" ${
			actions.create_new_revision?.allowed ? "" : 'aria-describedby="std-supersession-create-revision-reason"'
		}>${__("Create New Revision")}</button>
	</div>
</section>`;
	};

	R.renderAdvancedTabContent = function (detail) {
		const advanced = detail?.advanced || {};
		const sections = Array.isArray(advanced.sections) ? advanced.sections : [];
		const raw = advanced.raw_package || {};
		const editing = advanced.editing || {};
		const sourceMappings = advanced.source_mappings || {};
		const mappingTargets = Array.isArray(sourceMappings.targets) ? sourceMappings.targets : [];
		const mappingRows = Array.isArray(sourceMappings.rows) ? sourceMappings.rows : [];
		const sectionHtml = {
			sections_clauses: "std-advanced-sections-clauses",
			parameters: "std-advanced-parameters",
			forms: "std-advanced-forms",
			boq_rules: "std-advanced-boq-rules",
			source_mappings: "std-advanced-source-mappings",
			readiness_rules: "std-advanced-readiness-rules",
			generated_models: "std-advanced-generated-models",
		};
		const sectionColumns = {
			sections_clauses: [
				{ key: "code", label: __("Code") },
				{ key: "title", label: __("Title") },
				{ key: "mutability", label: __("Mutability") },
				{ key: "part", label: __("Part") },
			],
			parameters: [
				{ key: "code", label: __("Code") },
				{ key: "label", label: __("Label") },
				{ key: "type", label: __("Type") },
				{ key: "group", label: __("Group") },
			],
			forms: [
				{ key: "code", label: __("Code") },
				{ key: "label", label: __("Label") },
				{ key: "category", label: __("Category") },
				{ key: "required", label: __("Required") },
			],
			boq_rules: [
				{ key: "code", label: __("Code") },
				{ key: "label", label: __("Label") },
				{ key: "type", label: __("Type") },
				{ key: "enabled", label: __("Enabled") },
			],
			readiness_rules: [
				{ key: "code", label: __("Code") },
				{ key: "label", label: __("Label") },
				{ key: "type", label: __("Type") },
				{ key: "enabled", label: __("Enabled") },
			],
			generated_models: [
				{ key: "source", label: __("Source") },
				{ key: "target_label", label: __("Target") },
				{ key: "generated_element", label: __("Generated Element") },
				{ key: "status", label: __("Status") },
			],
		};

		function renderSectionTable(sectionKey, rows) {
			const columns = sectionColumns[sectionKey] || [];
			if (!columns.length || !rows.length) {
				return "";
			}
			return `<table class="std-advanced-section-table" data-testid="std-advanced-section-table-${sectionKey}">
				<thead><tr>${columns.map((c) => `<th>${c.label}</th>`).join("")}</tr></thead>
				<tbody>${rows
					.map(
						(row) =>
							`<tr>${columns
								.map((c) => `<td>${escHtml(row[c.key] != null ? row[c.key] : "")}</td>`)
								.join("")}</tr>`,
					)
					.join("")}</tbody>
			</table>`;
		}
		const status = String(detail?.status || "")
			.trim()
			.toLowerCase();
		const isActive = status === "active";
		const editingExplicitlyDisabled = editing && editing.enabled === false;
		const showReadonlyBanner =
			isActive || editingExplicitlyDisabled || Boolean(editing.force_readonly_banner);
		const readonlyBody =
			(editing.reason || "").trim() ||
			(isActive
				? __(
						"This version is Active. Mapping and structural edits are disabled; create a new revision to change configuration.",
				  )
				: __("Advanced technical surfaces are read-only in this phase."));
		const readonlyBannerHtml = showReadonlyBanner
			? `<div class="alert alert-warning" data-testid="std-advanced-readonly-banner" role="status"><strong>${__(
					"Read-only",
			  )}:</strong> ${escHtml(readonlyBody)}</div>`
			: `<div data-testid="std-advanced-readonly-banner" class="hidden" aria-hidden="true"></div>`;
		const defaultIntro = __(
			"For authorized administrators reviewing structured sections, parameters, mappings, readiness rules, and generated model definitions.",
		);
		const introSource = (advanced.intro_text || "").trim();
		const introParagraph = introSource ? escHtml(introSource) : escHtml(defaultIntro);
		const versionCode = escHtml(String(detail?.version_code || detail?.template_code || "").trim());
		const technicalJsonLink =
			versionCode && (kentender_procurement.std_config_shared || {}).canViewTechnicalJson?.()
				? `<div class="std-advanced-configurator-link">
		<button type="button" class="btn btn-primary btn-sm" data-testid="std-advanced-open-technical-json" data-kt-std-advanced-configure="${versionCode}">${__(
			"Open Technical JSON editor",
		)}</button>
	</div>`
				: "";
		const visibleSections = sections.filter((s) => s.key !== "raw_package_data");
		const projectedRowCounts = visibleSections.map((s) => {
			if (s.key === "source_mappings") {
				return mappingRows.length;
			}
			return Array.isArray(s.rows) ? s.rows.length : 0;
		});
		const totalProjectedRows = projectedRowCounts.reduce((sum, count) => sum + count, 0);
		const hasProjectedRows = totalProjectedRows > 0;
		const disclosureSummary = hasProjectedRows
			? __("Advanced technical internals ({0} items)", [String(totalProjectedRows)])
			: __("Show advanced technical internals");
		const gridHtml = visibleSections
			.map((s) => {
				const tid = sectionHtml[s.key] || "";
				if (s.key === "source_mappings") {
					return `<div class="std-advanced-card std-advanced-source-mappings" data-testid="${tid}">
						<h5>${s.label || ""}</h5>
						<div class="std-advanced-source-mappings-targets">
							${mappingTargets
								.map(
									(t) =>
										`<div class="std-advanced-source-target">${t.label || ""}</div>`,
								)
								.join("")}
						</div>
						<div class="std-advanced-source-mappings-readonly">${__(
							"Read-only mapping surface. Create New Revision to update mappings.",
						)}</div>
						<table class="std-advanced-source-mappings-table">
							<thead>
								<tr>
									<th>${__("Source")}</th>
									<th>${__("Target")}</th>
									<th>${__("Generated Element")}</th>
									<th>${__("Mandatory")}</th>
									<th>${__("Status")}</th>
									<th>${__("Last Validated")}</th>
								</tr>
							</thead>
							<tbody>
								${mappingRows
									.map((row, idx) => {
										const statusClass = String(row.status || "")
											.toLowerCase()
											.replace(/\s+/g, "-");
										const blocker =
											row.validation_blocker && row.status !== "Valid"
												? `<button type="button" class="btn btn-link btn-xs std-advanced-mapping-blocker" data-blocker-target="validation" data-row-index="${idx}">${__(
														"Open validation blocker",
												  )}</button>`
												: "";
										return `<tr>
											<td>${row.source || ""}${blocker}</td>
											<td>${row.target_label || ""}</td>
											<td>${row.generated_element || ""}</td>
											<td>${row.mandatory || ""}</td>
											<td><span class="std-advanced-status is-${statusClass}">${row.status || ""}</span></td>
											<td>${row.last_validated || ""}</td>
										</tr>`;
									})
									.join("")}
							</tbody>
						</table>
					</div>`;
				}
				const rows = Array.isArray(s.rows) ? s.rows : [];
				const tableHtml = renderSectionTable(s.key, rows);
				if (tableHtml) {
					const summary = s.summary ? `<p class="std-advanced-section-summary">${escHtml(s.summary)}</p>` : "";
					return `<div class="std-advanced-card" data-testid="${tid}">
					<h5>${s.label || ""}</h5>
					${summary}
					${tableHtml}
				</div>`;
				}
				return `<div class="std-advanced-card" data-testid="${tid}">
					<h5>${s.label || ""}</h5>
					<p>${__("Shell ready. Detailed internals are implemented in follow-on tickets where applicable.")}</p>
				</div>`;
			})
			.join("");
		return `
<section data-testid="std-advanced-technical-view" class="std-advanced-technical-view-root">
	<section class="std-library-advanced-tab" data-testid="std-library-advanced-tab">
		${readonlyBannerHtml}
		${technicalJsonLink}
		<details class="std-advanced-technical-disclosure"${hasProjectedRows ? " open" : ""}>
			<summary data-testid="std-advanced-technical-view-toggle" class="std-advanced-technical-summary">${disclosureSummary}</summary>
			<div class="std-advanced-technical-disclosure-body">
				<div class="std-advanced-intro" data-testid="std-advanced-intro" role="region" aria-label="${escHtml(
					__("Advanced Technical View introduction"),
				)}">
					<p>${introParagraph}</p>
				</div>
				<div class="std-advanced-grid">
					${gridHtml}
				</div>
			</div>
		</details>
		<details class="std-advanced-raw" data-testid="std-advanced-raw-package-data"${
			raw.collapsed_by_default && !raw.json_text ? "" : " open"
		}>
			<summary>${__("Raw Package Data")} - ${raw.technical_label || __("Technical (Read-Only)")}</summary>
			${
				raw.visible_for_advanced_users
					? raw.json_text
						? `<pre class="std-advanced-raw-json" data-testid="std-advanced-raw-package-json">${escHtml(
								raw.json_text,
						  )}</pre>${raw.truncated ? `<p class="text-muted small">${__("Package JSON truncated for display.")}</p>` : ""}`
						: `<p>${__("Raw package data is technical, hidden by default, and read-only.")}</p>`
					: `<p>${__("Raw package data is hidden for users without advanced permissions.")}</p>`
			}
		</details>
	</section>
</section>`;
	};

	R.renderAuditTabContent = function (detail) {
		const audit = detail?.audit || {};
		const rows = Array.isArray(audit.rows) ? audit.rows : [];
		return `
<section class="std-library-audit-tab" data-testid="std-library-audit-tab">
	<p class="std-audit-readonly">${__("Audit Trail is read-only and shows lifecycle/configuration event history.")}</p>
	<div class="std-audit-table-wrap">
		<table class="std-audit-event-table" data-testid="std-audit-event-table">
			<thead>
				<tr>
					<th>${__("Timestamp")}</th>
					<th>${__("Actor")}</th>
					<th>${__("Event")}</th>
					<th>${__("Object")}</th>
					<th>${__("Result")}</th>
					<th>${__("Reason")}</th>
					<th>${__("Audit Code")}</th>
				</tr>
			</thead>
			<tbody>
				${
					rows.length
						? rows
								.map((row) => {
									const status = String(row.result || "")
										.toLowerCase()
										.replace(/\s+/g, "-");
									return `<tr data-testid="std-audit-event-row">
										<td>${row.timestamp || ""}</td>
										<td>${row.actor || ""}</td>
										<td>${row.event || ""}</td>
										<td>${row.object || ""}</td>
										<td><span class="std-audit-status is-${status}">${row.result || ""}</span></td>
										<td>${row.reason || ""}</td>
										<td>${row.audit_code || ""}</td>
									</tr>`;
								})
								.join("")
						: `<tr data-testid="std-audit-event-row"><td colspan="7">${__(
								"No audit events recorded.",
						  )}</td></tr>`
				}
			</tbody>
		</table>
	</div>
</section>`;
	};
})();
