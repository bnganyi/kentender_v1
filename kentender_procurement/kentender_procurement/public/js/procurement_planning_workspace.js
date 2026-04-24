// Procurement Planning workbench — Desk shell (Phase D1).

(function () {
	const PP_WS = "Procurement Planning";
	let bindScheduled = false;
	let hooksBound = false;
	let workspaceDomObserver = null;
	let pollStarted = false;
	let activeWorkTab = "mywork";
	let activeQueueId = null;
	let lastRoleKey = null;
	let lastLandingPayload = null;
	let lastPackageListRows = null;
	let selectedPackageName = null;
	let detailFetchSeq = 0;
	const PP_MAX_INLINE_QUEUES = 4;

	function focusPpQueueToolbar() {
		const row = document.getElementById("kt-pp-queue-row");
		const pills = document.getElementById("kt-pp-queue-pills");
		if (row && typeof row.scrollIntoView === "function") {
			row.scrollIntoView({ block: "nearest", behavior: "smooth" });
		}
		if (!pills) {
			return;
		}
		const t = pills.querySelector("[data-toggle=dropdown]") || pills.querySelector("button[data-pp-queue]");
		if (t && typeof t.focus === "function") {
			t.focus();
		}
	}

	function escapeHtml(s) {
		if (s == null || s === undefined) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function slugForTestid(code) {
		const s = String(code || "")
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-+|-+$/g, "");
		return s || "pkg";
	}

	function formatPackageListValue(row) {
		const v = Math.round(Number(row.estimated_value) || 0);
		/* Single currency line is in the KPI strip (Layout spec); list shows numbers only. */
		return escapeHtml(String(v.toLocaleString()));
	}

	function formatDetailMoney(currency, amount) {
		const cur = currency || "KES";
		const v = Math.round(Number(amount) || 0);
		return escapeHtml(cur) + " " + escapeHtml(String(v.toLocaleString()));
	}

	function formatDetailDate(val) {
		if (val == null || val === "") return "—";
		return String(val);
	}

	function detailDlRow(label, value) {
		const v = value == null || value === "" ? "—" : String(value);
		return (
			'<div class="kt-pp-detail-kv">' +
			"<dt>" +
			escapeHtml(label) +
			"</dt><dd>" +
			escapeHtml(v) +
			"</dd></div>"
		);
	}

	function normalizeErrorMessage(raw, fallback) {
		const text = String(raw || fallback || "").trim();
		if (!text) return String(fallback || __("Could not complete action."));
		const parts = text
			.split(/\n+/)
			.map(function (p) {
				return p.trim();
			})
			.filter(Boolean);
		if (!parts.length) return String(fallback || __("Could not complete action."));
		const seen = new Set();
		const uniq = [];
		for (let i = 0; i < parts.length; i++) {
			const key = parts[i].toLowerCase();
			if (seen.has(key)) continue;
			seen.add(key);
			uniq.push(parts[i]);
		}
		return uniq.join("<br>");
	}

	function extractServerErrorMessage(r, fallback) {
		const def = fallback || __("Could not complete action.");
		try {
			if (r && r._server_messages) {
				const sm = JSON.parse(r._server_messages);
				if (Array.isArray(sm)) {
					for (let i = 0; i < sm.length; i++) {
						try {
							const o = JSON.parse(sm[i]);
							if (o && o.message) {
								return normalizeErrorMessage(String(o.message), def);
							}
						} catch (e) {
							/* ignore malformed item */
						}
					}
				}
			}
			if (r && r.message) {
				return normalizeErrorMessage(String(r.message), def);
			}
			return def;
		} catch (e2) {
			return normalizeErrorMessage((r && r.message) || "", def);
		}
	}

	function buildDetailActionButtons(actions) {
		if (!actions) return "";
		const a = actions;
		const parts = [];
		if (a.edit) {
			parts.push(
				'<button type="button" class="btn btn-sm btn-default" data-pp-detail-action="edit" data-testid="pp-action-edit">' +
				escapeHtml(__("Edit Package")) +
				"</button>"
			);
		}
		if (a.add_demand_lines) {
			parts.push(
				'<button type="button" class="btn btn-sm btn-default" data-pp-detail-action="add_demand_lines" data-testid="pp-action-add-demand-lines">' +
				escapeHtml(__("Add Demand Lines")) +
				"</button>"
			);
		}
		if (a.complete) {
			parts.push(
				'<button type="button" class="btn btn-sm btn-primary" data-pp-detail-action="complete" data-testid="pp-action-complete-package">' +
				escapeHtml(__("Complete Package")) +
				"</button>"
			);
		}
		if (a.submit) {
			parts.push(
				'<button type="button" class="btn btn-sm btn-primary" data-pp-detail-action="submit" data-testid="pp-action-submit">' +
				escapeHtml(__("Submit")) +
				"</button>"
			);
		}
		if (a.approve) {
			parts.push(
				'<button type="button" class="btn btn-sm btn-primary" data-pp-detail-action="approve" data-testid="pp-action-approve">' +
				escapeHtml(__("Approve")) +
				"</button>"
			);
		}
		if (a.return) {
			parts.push(
				'<button type="button" class="btn btn-sm btn-default" data-pp-detail-action="return" data-testid="pp-action-return">' +
				escapeHtml(__("Return")) +
				"</button>"
			);
		}
		if (a.reject) {
			parts.push(
				'<button type="button" class="btn btn-sm btn-default" data-pp-detail-action="reject" data-testid="pp-action-reject">' +
				escapeHtml(__("Reject")) +
				"</button>"
			);
		}
		if (a.mark_ready) {
			parts.push(
				'<button type="button" class="btn btn-sm btn-primary" data-pp-detail-action="mark_ready" data-testid="pp-action-mark-ready">' +
				escapeHtml(__("Mark Ready for Tender")) +
				"</button>"
			);
		}
		if (a.release) {
			parts.push(
				'<button type="button" class="btn btn-sm btn-primary" data-pp-detail-action="release" data-testid="pp-action-release-to-tender">' +
				escapeHtml(__("Release to Tender")) +
				"</button>"
			);
		}
		if (!parts.length) return "";
		return (
			'<div class="kt-pp-workbench-actions kt-pp-detail-actions d-flex flex-wrap gap-1 justify-content-end" data-testid="pp-detail-actions-bar">' +
			parts.join("") +
			"</div>"
		);
	}

	function buildPackageDetailHtml(d) {
		const badges = buildBadgeChips(d.badges || {});
		const actionsHtml = buildDetailActionButtons(d.actions || {});
		/* Sticky first row (DIA workbench pattern: `dia-detail-section-f` in demand_intake_workspace.css). */
		const stickyActions = actionsHtml
			? '<section class="kt-pp-detail-section kt-pp-detail-section--sticky-actions" data-testid="pp-detail-section-actions">' +
				'<h4 class="kt-pp-detail-section__title kt-pp-detail-section__title--actions-h">' +
				escapeHtml(__("Actions")) +
				"</h4>" +
				actionsHtml +
				"</section>"
			: "";
		const hdr =
			'<div class="kt-pp-detail-header">' +
			'<div class="kt-pp-detail-header__main">' +
			'<h3 class="kt-pp-detail-title h6 mb-1" data-testid="pp-detail-title">' +
			escapeHtml(d.package_name || "") +
			"</h3>" +
			'<div class="small text-muted mb-1">' +
			'<span class="font-monospace">' +
			escapeHtml(d.package_code || "") +
			"</span>" +
			"</div>" +
			'<div class="kt-pp-detail-header__meta small text-muted d-flex flex-wrap gap-2">' +
			'<span data-testid="pp-detail-template">' +
			escapeHtml(d.template_name || "—") +
			"</span>" +
			'<span data-testid="pp-detail-method">' +
			escapeHtml(d.procurement_method || "—") +
			"</span>" +
			'<span data-testid="pp-detail-contract-type">' +
			escapeHtml(d.contract_type || "—") +
			"</span>" +
			"</div>" +
			(badges ? '<div class="kt-pp-detail-header__badges mt-1">' + badges + "</div>" : "") +
			"</div></div>" +
			'<div class="mb-2 d-flex flex-wrap gap-2 align-items-center">' +
			(d.plan_status
				? '<span class="badge badge-info" data-testid="pp-detail-plan-status">' +
					escapeHtml(__("Plan")) +
					": " +
					escapeHtml(d.plan_status) +
					"</span>"
				: "") +
			'<span class="badge badge-secondary" data-testid="pp-detail-package-status">' +
			escapeHtml(__("Package")) +
			": " +
			escapeHtml(d.status || "") +
			"</span>" +
			(d.method_override_flag
				? ' <span class="badge badge-warning">' + escapeHtml(__("Method override")) + "</span>"
				: "") +
			(d.release_blocked_by_plan
				? '<span class="text-muted small" data-testid="pp-detail-release-blocked-hint">' +
					escapeHtml(
						__(
							"Ready for Tender — release is blocked until the procurement plan is approved."
						)
					) +
					"</span>"
				: "") +
			"</div>";

		const defn = d.definition || {};
		const sec1 =
			'<section class="kt-pp-detail-section" data-testid="pp-detail-section-definition">' +
			'<h4 class="kt-pp-detail-section__title">' +
			escapeHtml(__("1. Package definition")) +
			"</h4>" +
			'<div class="kt-pp-detail-grid">' +
			detailDlRow(__("Package name"), defn.package_name) +
			detailDlRow(__("Package code"), defn.package_code) +
			detailDlRow(__("Template"), defn.template_name) +
			detailDlRow(__("Procurement method"), defn.procurement_method) +
			detailDlRow(__("Contract type"), defn.contract_type) +
			detailDlRow(__("Status"), defn.status) +
			detailDlRow(
				__("Method override"),
				defn.method_override_flag ? __("Yes") : __("No")
			) +
			"</div></section>";

		const fin = d.financial || {};
		const sec2 =
			'<section class="kt-pp-detail-section">' +
			'<h4 class="kt-pp-detail-section__title">' +
			escapeHtml(__("2. Financial and schedule")) +
			"</h4>" +
			'<div class="kt-pp-detail-grid">' +
			'<div class="kt-pp-detail-kv" data-testid="pp-detail-estimated-value"><dt>' +
			escapeHtml(__("Estimated value")) +
			'</dt><dd class="kt-pp-detail-kv__money">' +
			formatDetailMoney(fin.currency, fin.estimated_value) +
			"</dd></div>" +
			detailDlRow(__("Currency"), fin.currency) +
			detailDlRow(__("Schedule start"), formatDetailDate(fin.schedule_start)) +
			detailDlRow(__("Schedule end"), formatDetailDate(fin.schedule_end)) +
			"</div></section>";

		const lines = d.demand_lines || [];
		const canManageDemand = !!(d.actions && d.actions.add_demand_lines);
		let tableRows = "";
		for (let i = 0; i < lines.length; i++) {
			const ln = lines[i];
			const rmBtn =
				canManageDemand && ln.line_name
					? '<button type="button" class="btn btn-xs btn-default" data-pp-detail-action="remove_demand_line" data-pp-line-name="' +
						escapeHtml(ln.line_name) +
						'" data-testid="pp-action-remove-demand-line">' +
						escapeHtml(__("Remove")) +
						"</button>"
					: '<span class="text-muted">—</span>';
			tableRows +=
				"<tr>" +
				"<td>" +
				escapeHtml(ln.demand_id || "") +
				"</td><td>" +
				escapeHtml(ln.demand_title || "") +
				"</td><td>" +
				escapeHtml(ln.department || "") +
				"</td><td>" +
				escapeHtml(ln.budget_line || "") +
				"</td><td>" +
				escapeHtml(ln.demand_status || "") +
				"</td><td class=\"text-end\">" +
				escapeHtml(String(Math.round(Number(ln.amount) || 0).toLocaleString())) +
				"</td><td>" +
				escapeHtml(ln.priority || "") +
				"</td><td class=\"text-end\">" +
				rmBtn +
				"</td></tr>";
		}
		const emptyCta =
			!tableRows && canManageDemand
				? '<div class="kt-pp-empty text-muted small" data-testid="pp-demand-lines-empty">' +
					'<p class="mb-2">' +
					escapeHtml(__("No demand lines added yet.")) +
					"</p>" +
					'<button type="button" class="btn btn-sm btn-primary" data-pp-detail-action="add_demand_lines" data-testid="pp-demand-lines-empty-add">' +
					escapeHtml(__("Add Demand Lines")) +
					"</button>" +
					"</div>"
				: "";
		if (!tableRows) {
			tableRows =
				'<tr><td colspan="8" class="text-muted small">' + escapeHtml(__("No demand lines.")) + "</td></tr>";
		}
		const sec3 =
			'<section class="kt-pp-detail-section" data-testid="pp-detail-demand-lines">' +
			'<h4 class="kt-pp-detail-section__title">' +
			escapeHtml(__("3. Demand lines")) +
			"</h4>" +
			emptyCta +
			'<div class="kt-pp-detail-table-wrap">' +
			'<table class="table table-bordered table-sm mb-0 kt-pp-detail-table">' +
			"<thead><tr>" +
			"<th>" +
			escapeHtml(__("Demand ID")) +
			"</th><th>" +
			escapeHtml(__("Demand title")) +
			"</th><th>" +
			escapeHtml(__("Department")) +
			"</th><th>" +
			escapeHtml(__("Budget line")) +
			"</th><th>" +
			escapeHtml(__("Status")) +
			"</th><th class=\"text-end\">" +
			escapeHtml(__("Amount")) +
			"</th><th>" +
			escapeHtml(__("Priority")) +
			"</th><th class=\"text-end\">" +
			escapeHtml(__("Action")) +
			"</th></tr></thead><tbody>" +
			tableRows +
			"</tbody></table></div>" +
			"</section>";

		const risk = d.risk || {};
		let riskItems = "";
		const rlist = risk.risks || [];
		for (let j = 0; j < rlist.length; j++) {
			const it = rlist[j];
			const rr = (it && it.risk) || "";
			const mm = (it && it.mitigation) || "";
			riskItems +=
				'<li class="small">' +
				"<strong>" +
				escapeHtml(rr) +
				"</strong>" +
				(mm ? " → " + escapeHtml(mm) : "") +
				"</li>";
		}
		if (!riskItems) {
			riskItems = '<li class="text-muted small">' + escapeHtml(__("No risks listed.")) + "</li>";
		}
		const sec4 =
			'<section class="kt-pp-detail-section" data-testid="pp-detail-risk-profile">' +
			'<h4 class="kt-pp-detail-section__title">' +
			escapeHtml(__("4. Risk and mitigation")) +
			"</h4>" +
			'<div class="kt-pp-detail-grid">' +
			detailDlRow(__("Risk profile"), risk.profile_name || risk.profile_code || "—") +
			detailDlRow(__("Risk level"), risk.risk_level || "—") +
			"</div>" +
			'<ul class="kt-pp-detail-list mb-0">' +
			riskItems +
			"</ul></section>";

		const kpi = d.kpi || {};
		let kpiItems = "";
		const mets = kpi.metrics || [];
		for (let k = 0; k < mets.length; k++) {
			kpiItems += "<li class=\"small\">" + escapeHtml(String(mets[k])) + "</li>";
		}
		if (!kpiItems) {
			kpiItems = '<li class="text-muted small">' + escapeHtml(__("No metrics listed.")) + "</li>";
		}
		const sec5 =
			'<section class="kt-pp-detail-section" data-testid="pp-detail-kpi-profile">' +
			'<h4 class="kt-pp-detail-section__title">' +
			escapeHtml(__("5. KPI profile")) +
			"</h4>" +
			'<div class="kt-pp-detail-grid">' +
			detailDlRow(__("Profile"), kpi.profile_name || kpi.profile_code || "—") +
			"</div>" +
			'<ul class="kt-pp-detail-list mb-0">' +
			kpiItems +
			"</ul></section>";

		const dec = d.decision_criteria || {};
		let critRows = "";
		const crits = dec.criteria || [];
		for (let c = 0; c < crits.length; c++) {
			const cr = crits[c];
			const w =
				cr.weight != null && cr.weight !== ""
					? String(cr.weight)
					: "—";
			critRows +=
				"<tr><td>" +
				escapeHtml(cr.criterion || "") +
				"</td><td class=\"text-end\">" +
				escapeHtml(w) +
				"</td></tr>";
		}
		if (!critRows) {
			critRows =
				'<tr><td colspan="2" class="text-muted small">' +
				escapeHtml(__("No criteria listed.")) +
				"</td></tr>";
		}
		const sec6 =
			'<section class="kt-pp-detail-section" data-testid="pp-detail-decision-criteria">' +
			'<h4 class="kt-pp-detail-section__title">' +
			escapeHtml(__("6. Decision criteria")) +
			"</h4>" +
			'<div class="kt-pp-detail-grid">' +
			detailDlRow(__("Profile"), dec.profile_name || dec.profile_code || "—") +
			"</div>" +
			'<div class="kt-pp-detail-table-wrap">' +
			'<table class="table table-bordered table-sm mb-0"><thead><tr><th>' +
			escapeHtml(__("Criterion")) +
			'</th><th class="text-end">' +
			escapeHtml(__("Weight")) +
			"</th></tr></thead><tbody>" +
			critRows +
			"</tbody></table></div></section>";

		const vm = d.vendor_management || {};
		let mon = "";
		const ms = vm.monitoring_summary || [];
		for (let x = 0; x < ms.length; x++) {
			mon += "<li class=\"small font-monospace\">" + escapeHtml(ms[x]) + "</li>";
		}
		if (!mon) mon = '<li class="text-muted small">' + escapeHtml(__("None")) + "</li>";
		let esc = "";
		const es = vm.escalation_summary || [];
		for (let y = 0; y < es.length; y++) {
			esc += "<li class=\"small font-monospace\">" + escapeHtml(es[y]) + "</li>";
		}
		if (!esc) esc = '<li class="text-muted small">' + escapeHtml(__("None")) + "</li>";
		const sec7 =
			'<section class="kt-pp-detail-section" data-testid="pp-detail-vendor-management">' +
			'<h4 class="kt-pp-detail-section__title">' +
			escapeHtml(__("7. Vendor management")) +
			"</h4>" +
			detailDlRow(__("Profile"), vm.profile_name || vm.profile_code || "—") +
			"<p class=\"small text-muted mb-1\">" +
			escapeHtml(__("Monitoring")) +
			"</p>" +
			'<ul class="kt-pp-detail-list mb-2">' +
			mon +
			"</ul>" +
			"<p class=\"small text-muted mb-1\">" +
			escapeHtml(__("Escalation")) +
			"</p>" +
			'<ul class="kt-pp-detail-list mb-0">' +
			esc +
			"</ul></section>";

		const wf = d.workflow || {};
		const sec8 =
			'<section class="kt-pp-detail-section" data-testid="pp-detail-workflow">' +
			'<h4 class="kt-pp-detail-section__title">' +
			escapeHtml(__("8. Workflow and approval")) +
			"</h4>" +
			'<div class="kt-pp-detail-grid">' +
			detailDlRow(__("Status"), wf.status) +
			detailDlRow(__("Created by"), wf.created_by) +
			detailDlRow(__("Approved by"), wf.approved_by) +
			detailDlRow(__("Approved at"), formatDetailDate(wf.approved_at)) +
			detailDlRow(__("Rejected by"), wf.rejected_by) +
			detailDlRow(__("Rejected at"), formatDetailDate(wf.rejected_at)) +
			detailDlRow(__("Planning status"), wf.planning_status) +
			detailDlRow(__("Workflow notes"), wf.workflow_reason) +
			"</div></section>";

		return (
			'<div class="kt-pp-detail-inner" data-pp-detail-package="' +
			escapeHtml(d.name || "") +
			'">' +
			stickyActions +
			hdr +
			sec1 +
			sec2 +
			sec3 +
			sec4 +
			sec5 +
			sec6 +
			sec7 +
			sec8 +
			"</div>"
		);
	}

	function removeDemandLineFromPackage(packageName, lineName, onDone) {
		if (!lineName) return;
		frappe.confirm(__("Remove this demand line from the package?"), function () {
			frappe.call({
				method: "kentender_procurement.procurement_planning.api.package_line_edit.remove_pp_package_line",
				args: { line_name: lineName },
				callback: function (r) {
					const msg = r && r.message;
					if (!msg || msg.ok === false || r.exc) return;
					frappe.show_alert({ message: __("Demand line removed"), indicator: "green" });
					if (typeof onDone === "function") onDone();
				},
			});
		});
	}

	function addDemandRowsToPackage(packageName, rows, onDone) {
		const list = Array.isArray(rows) ? rows : [];
		if (!list.length) return;
		const failures = [];
		let idx = 0;
		function next() {
			if (idx >= list.length) {
				if (failures.length) {
					frappe.msgprint({
						title: __("Some demands were not added"),
						indicator: "orange",
						message: escapeHtml(failures.join("\n")),
					});
				} else {
					frappe.show_alert({
						message: __("Demand lines added"),
						indicator: "green",
					});
				}
				if (typeof onDone === "function") onDone();
				return;
			}
			const row = list[idx++];
			frappe.call({
				method: "kentender_procurement.procurement_planning.api.package_line_edit.add_pp_package_line",
				args: {
					package: packageName,
					demand_id: row.name,
					budget_line_id: row.budget_line_id,
					amount: row.amount,
					department: row.department,
					priority: row.priority || "Normal",
					quantity: 1,
				},
				callback: function (r) {
					const msg = r && r.message;
					if (!msg || msg.ok === false || r.exc) {
						failures.push((row.demand_id || row.name || "") + ": " + __("could not add"));
					}
					next();
				},
				error: function () {
					failures.push((row.demand_id || row.name || "") + ": " + __("could not add"));
					next();
				},
			});
		}
		next();
	}

	function openAddDemandLinesDialog(packageName, onDone) {
		frappe.call({
			method: "kentender_procurement.procurement_planning.api.package_line_edit.list_pp_assignable_demands",
			args: { package: packageName, page_length: 200 },
			callback: function (r) {
				const msg = r && r.message;
				if (!msg || msg.ok === false || r.exc) return;
				const demands = Array.isArray(msg.demands) ? msg.demands : [];
				if (!demands.length) {
					frappe.msgprint({
						title: __("No eligible demand"),
						message: __("No Approved or Planning Ready demand is available for this package in the current plan scope."),
						indicator: "blue",
					});
					return;
				}

				const byId = {};
				for (let i = 0; i < demands.length; i++) {
					const row = demands[i] || {};
					if (row.name) byId[row.name] = row;
				}

				const d = new frappe.ui.Dialog({
					title: __("Add Demand Lines to Package"),
					fields: [
						{
							fieldtype: "HTML",
							fieldname: "help",
							options:
								'<div class="small text-muted mb-2" data-testid="pp-add-demand-dialog-help">' +
								'<p class="mb-1"><strong>' +
								escapeHtml(__("Constraints")) +
								'</strong></p>' +
								'<p class="mb-0">' +
								escapeHtml(__("Approved/Planning Ready only, no duplicate active assignment, same plan scope.")) +
								'</p>' +
								"</div>",
						},
						{ fieldtype: "Data", fieldname: "search", label: __("Search available"), onchange: function () {} },
						{
							fieldtype: "HTML",
							fieldname: "selector",
							options:
								'<div class="kt-pp-demand-assign-picker" data-testid="pp-demand-assign-picker">' +
								'<div class="row">' +
								'<div class="col-sm-6">' +
								'<p class="small text-muted mb-1"><strong>' +
								escapeHtml(__("LEFT: Available demands")) +
								'</strong> <span class="badge badge-secondary" id="kt-pp-demand-available-count">0</span></p>' +
								'<div class="small border rounded" style="max-height:280px; overflow:auto; padding:6px;" id="kt-pp-demand-available"></div>' +
								'</div>' +
								'<div class="col-sm-6">' +
								'<p class="small text-muted mb-1"><strong>' +
								escapeHtml(__("RIGHT: Selected for package")) +
								'</strong> <span class="badge badge-primary" id="kt-pp-demand-selected-count">0</span></p>' +
								'<div class="small border rounded" style="max-height:280px; overflow:auto; padding:6px;" id="kt-pp-demand-selected"></div>' +
								'</div>' +
								'</div>' +
								"</div>",
						},
					],
					primary_action_label: __("Add Selected to Package"),
					primary_action() {
						const picked = Array.from(selectedIds);
						if (!picked.length) {
							frappe.msgprint(__("Select at least one demand line to add."));
							return;
						}
						const rows = picked.map(function (id) {
							return byId[id];
						}).filter(Boolean);
						d.hide();
						addDemandRowsToPackage(packageName, rows, onDone);
					},
				});

				const selectedIds = new Set();
				let filterText = "";

				function rowLabel(row) {
					const money = Math.round(Number(row.amount) || 0).toLocaleString();
					return (
						escapeHtml(row.demand_id || row.name || "") +
						" - " +
						escapeHtml(row.title || __("Untitled demand")) +
						" (" +
						escapeHtml(row.department || "-") +
						", " +
						escapeHtml(money) +
						")"
					);
				}

				function matchesFilter(row) {
					if (!filterText) return true;
					const blob = [row.demand_id, row.title, row.department, row.status]
						.map(function (x) {
							return String(x || "").toLowerCase();
						})
						.join(" ");
					return blob.indexOf(filterText) >= 0;
				}

				function renderPicker() {
					const avail = d.$wrapper.find("#kt-pp-demand-available");
					const sel = d.$wrapper.find("#kt-pp-demand-selected");
					const availCount = d.$wrapper.find("#kt-pp-demand-available-count");
					const selCount = d.$wrapper.find("#kt-pp-demand-selected-count");
					if (!avail.length || !sel.length) return;
					let left = "";
					let right = "";
					let leftN = 0;
					let rightN = 0;
					for (let i = 0; i < demands.length; i++) {
						const row = demands[i];
						if (!row || !row.name) continue;
						if (!matchesFilter(row)) continue;
						const id = row.name;
						const isSelected = selectedIds.has(id);
						const line =
							'<div class="mb-1 d-flex align-items-start justify-content-between gap-2">' +
							'<span>' + rowLabel(row) + '</span>' +
							(isSelected
								? '<button type="button" class="btn btn-xs btn-default" data-pp-picker-action="remove" data-pp-demand-id="' + escapeHtml(id) + '">' + escapeHtml(__("Remove")) + '</button>'
								: '<button type="button" class="btn btn-xs btn-primary" data-pp-picker-action="add" data-pp-demand-id="' + escapeHtml(id) + '">' + escapeHtml(__("Add")) + '</button>') +
							"</div>";
						if (isSelected) {
							right += line;
							rightN += 1;
						} else {
							left += line;
							leftN += 1;
						}
					}
					avail.html(left || '<p class="text-muted mb-0">' + escapeHtml(__("No available demands.")) + '</p>');
					sel.html(right || '<p class="text-muted mb-0">' + escapeHtml(__("No demand selected yet.")) + '</p>');
					if (availCount.length) availCount.text(String(leftN));
					if (selCount.length) selCount.text(String(rightN));
				}

				d.show();
				renderPicker();

				d.$wrapper.on("input", 'input[data-fieldname="search"]', function () {
					filterText = String(this.value || "").trim().toLowerCase();
					renderPicker();
				});
				d.$wrapper.on("click", "[data-pp-picker-action]", function () {
					const id = this.getAttribute("data-pp-demand-id") || "";
					const act = this.getAttribute("data-pp-picker-action") || "";
					if (!id) return;
					if (act === "add") selectedIds.add(id);
					if (act === "remove") selectedIds.delete(id);
					renderPicker();
				});
			},
		});
	}

	function runPpPackageWorkflow(action, packageName, options) {
		if (!packageName || !isPpWorkspaceRoute()) return;
		const WF = "kentender_procurement.procurement_planning.api.workflow.";
		const onDone = function () {
			fetchPackageList();
			renderPackageDetail();
		};
		if (action === "edit") {
			if (typeof frappe !== "undefined" && frappe.set_route) {
				frappe.set_route("Form", "Procurement Package", packageName);
			}
			return;
		}
		if (action === "add_demand_lines") {
			openAddDemandLinesDialog(packageName, onDone);
			return;
		}
		if (action === "remove_demand_line") {
			const lineName = options && options.lineName ? String(options.lineName) : "";
			if (!lineName) return;
			removeDemandLineFromPackage(packageName, lineName, onDone);
			return;
		}
		if (action === "complete") {
			frappe.call({
				method: WF + "complete_package",
				args: { package_id: packageName },
				callback: function (r) {
					if (!r || r.exc) return;
					frappe.show_alert({ message: __("Package completed"), indicator: "green" });
					onDone();
				},
			});
			return;
		}
		if (action === "submit") {
			frappe.call({
				method: WF + "submit_package",
				args: { package_id: packageName },
				callback: function (r) {
					if (!r || r.exc) return;
					frappe.show_alert({ message: __("Submitted"), indicator: "green" });
					onDone();
				},
			});
			return;
		}
		if (action === "approve") {
			frappe.call({
				method: WF + "approve_package",
				args: { package_id: packageName },
				callback: function (r) {
					if (!r || r.exc) return;
					frappe.show_alert({ message: __("Approved"), indicator: "green" });
					onDone();
				},
			});
			return;
		}
		if (action === "mark_ready") {
			frappe.call({
				method: WF + "mark_ready_for_tender",
				args: { package_id: packageName },
				callback: function (r) {
					if (!r || r.exc) return;
					frappe.show_alert({ message: __("Marked ready for tender"), indicator: "green" });
					onDone();
				},
			});
			return;
		}
		if (action === "release") {
			frappe.confirm(__("Release this package to Tendering?"), function () {
				frappe.call({
					method: WF + "release_package_to_tender",
					args: { package_id: packageName },
					callback: function (r) {
						if (!r || r.exc) return;
						frappe.show_alert({ message: __("Released to tender"), indicator: "green" });
						onDone();
					},
				});
			});
			return;
		}
		if (action === "return") {
			frappe.prompt(
				[
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("Return reason"),
						reqd: 1,
					},
				],
				function (vals) {
					frappe.call({
						method: WF + "return_package",
						args: { package_id: packageName, reason: vals.reason },
						callback: function (r) {
							if (!r || r.exc) return;
							frappe.show_alert({ message: __("Returned for revision"), indicator: "green" });
							onDone();
						},
					});
				},
				__("Return package"),
				__("Return")
			);
			return;
		}
		if (action === "reject") {
			frappe.prompt(
				[
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("Reject reason"),
						reqd: 1,
					},
				],
				function (vals) {
					frappe.call({
						method: WF + "reject_package",
						args: { package_id: packageName, reason: vals.reason },
						callback: function (r) {
							if (!r || r.exc) return;
							frappe.show_alert({ message: __("Rejected"), indicator: "green" });
							onDone();
						},
					});
				},
				__("Reject package"),
				__("Reject")
			);
		}
	}

	function runPpPlanWorkflow(action, planId) {
		if (!planId || !isPpWorkspaceRoute()) return;
		const WF = "kentender_procurement.procurement_planning.api.workflow.";
		const onDone = function () {
			loadPpLandingData(null);
		};
		if (action === "submit-plan") {
			const lp = lastLandingPayload || {};
			if (lp.plan_submit_ready === false && (lp.plan_submit_blockers || []).length) {
				frappe.msgprint({
					title: __("Cannot submit plan"),
					message: lp.plan_submit_blockers.join("<br>"),
					indicator: "red",
				});
				return;
			}
			frappe.confirm(__("Submit this procurement plan?"), function () {
				frappe.call({
					method: WF + "submit_plan",
					args: { plan_id: planId },
					callback: function (r) {
						if (!r || r.exc) return;
						frappe.show_alert({ message: __("Plan submitted"), indicator: "green" });
						onDone();
					},
				});
			});
			return;
		}
		if (action === "approve-plan") {
			frappe.confirm(__("Approve this procurement plan?"), function () {
				frappe.call({
					method: WF + "approve_plan",
					args: { plan_id: planId },
					callback: function (r) {
						if (!r || r.exc) return;
						frappe.show_alert({ message: __("Plan approved"), indicator: "green" });
						onDone();
					},
				});
			});
			return;
		}
		if (action === "lock-plan") {
			frappe.confirm(__("Lock this approved procurement plan?"), function () {
				frappe.call({
					method: WF + "lock_plan",
					args: { plan_id: planId },
					callback: function (r) {
						if (!r || r.exc) return;
						frappe.show_alert({ message: __("Plan locked"), indicator: "green" });
						onDone();
					},
				});
			});
			return;
		}
		if (action === "return-plan") {
			frappe.prompt(
				[
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("Return reason"),
						reqd: 1,
					},
				],
				function (vals) {
					frappe.call({
						method: WF + "return_plan",
						args: { plan_id: planId, reason: vals.reason },
						callback: function (r) {
							if (!r || r.exc) return;
							frappe.show_alert({ message: __("Plan returned for revision"), indicator: "green" });
							onDone();
						},
					});
				},
				__("Return plan"),
				__("Return")
			);
			return;
		}
		if (action === "reject-plan") {
			frappe.prompt(
				[
					{
						fieldname: "reason",
						fieldtype: "Small Text",
						label: __("Reject reason"),
						reqd: 1,
					},
				],
				function (vals) {
					frappe.call({
						method: WF + "reject_plan",
						args: { plan_id: planId, reason: vals.reason },
						callback: function (r) {
							if (!r || r.exc) return;
							frappe.show_alert({ message: __("Plan rejected"), indicator: "green" });
							onDone();
						},
					});
				},
				__("Reject plan"),
				__("Reject")
			);
			return;
		}
	}

	function renderPackageDetail() {
		const detailRoot = document.getElementById("kt-pp-detail-root");
		if (!detailRoot) return;
		if (!selectedPackageName) {
			detailRoot.innerHTML =
				'<div class="kt-pp-empty text-muted small">' +
				"<p class=\"mb-0\">" +
				escapeHtml(__("Select a package in the list to review details and take action.")) +
				"</p></div>";
			return;
		}
		const pkgName = selectedPackageName;
		const seq = ++detailFetchSeq;
		detailRoot.innerHTML =
			'<div class="text-muted small py-2" data-testid="pp-detail-loading">' +
			escapeHtml(__("Loading…")) +
			"</div>";
		frappe.call({
			method: "kentender_procurement.procurement_planning.api.package_detail.get_pp_package_detail",
			args: { package: pkgName },
			callback: function (r) {
				if (!isPpWorkspaceRoute()) return;
				if (seq !== detailFetchSeq) return;
				if (pkgName !== selectedPackageName) return;
				const data = r && r.message;
				if (!data || data.ok === false) {
					const err =
						(data && data.message) || __("Could not load package details.");
					detailRoot.innerHTML =
						'<div class="alert alert-warning mb-0 small" role="status" data-testid="pp-detail-error">' +
						escapeHtml(err) +
						"</div>";
					return;
				}
				detailRoot.innerHTML = buildPackageDetailHtml(data);
			},
			error: function () {
				if (!isPpWorkspaceRoute() || !detailRoot) return;
				if (seq !== detailFetchSeq) return;
				if (pkgName !== selectedPackageName) return;
				detailRoot.innerHTML =
					'<p class="text-danger small mb-0" data-testid="pp-detail-error">' +
					escapeHtml(__("Could not load package details.")) +
					"</p>";
			},
		});
	}

	function emptyMessageForQueue(qid) {
		const m = {
			all_packages: __("No packages in this plan yet."),
			draft_packages: __("No draft packages yet."),
			structured_packages: __("No completed packages yet."),
			submitted_packages: __("No submitted packages in this queue yet."),
			pending_approval: __("No packages pending approval."),
			high_risk_packages: __("No high-risk packages in this plan."),
			emergency_packages: __("No emergency packages in this plan."),
			high_risk_escalation: __("No high-risk packages require escalation."),
			method_override: __("No method override cases."),
			ready_for_tender: __("No packages ready for tender."),
			approved_not_handed_off: __("No approved packages pending handoff."),
		};
		return m[qid] || __("No packages in this queue.");
	}

	function workspaceNameMatchesPp(name) {
		if (name == null || name === "") return false;
		if (name === PP_WS) return true;
		try {
			if (typeof frappe !== "undefined" && frappe.router && typeof frappe.router.slug === "function") {
				return frappe.router.slug(String(name)) === frappe.router.slug(PP_WS);
			}
		} catch (e) {
			/* ignore */
		}
		return String(name).toLowerCase().replace(/\s+/g, "-") === "procurement-planning";
	}

	function isPpWorkspaceRoute() {
		try {
			if (typeof frappe !== "undefined" && frappe.router && Array.isArray(frappe.router.current_route)) {
				const r = frappe.router.current_route;
				if (r[0] === "Workspaces" && r.length >= 2) {
					const workspaceName = r[1] === "private" && r.length >= 3 ? r[2] : r[1];
					if (workspaceNameMatchesPp(workspaceName)) return true;
					if (workspaceName) return false;
				}
			}
		} catch (e) {
			/* ignore */
		}
		try {
			const route = frappe.get_route() || [];
			if (route[0] === "Workspaces" && route.length >= 2) {
				const w = route[1] === "private" && route.length >= 3 ? route[2] : route[1];
				if (workspaceNameMatchesPp(w)) return true;
				if (w) return false;
			}
		} catch (e2) {
			/* ignore */
		}
		const loc = window.location;
		const path = ((loc && (loc.pathname + (loc.search || "") + (loc.hash || ""))) || "").toLowerCase();
		if (path.includes("procurement-planning")) {
			return true;
		}
		const dr = (document.body && document.body.getAttribute("data-route")) || "";
		if (dr.includes(PP_WS) || dr.toLowerCase().includes("procurement-planning")) {
			return true;
		}
		return false;
	}

	function syncPpShellClass() {
		document.body.classList.toggle("kt-pp-shell", isPpWorkspaceRoute());
	}

	function removePpLandingIfWrongRoute() {
		document.querySelectorAll(".kt-pp-injected-shell").forEach(function (el) {
			el.remove();
		});
		document.body.classList.remove("kt-pp-shell");
		bindScheduled = false;
		activeQueueId = null;
		lastRoleKey = null;
		lastLandingPayload = null;
		lastPackageListRows = null;
		selectedPackageName = null;
	}

	function getWorkspacesPageRoot() {
		return (
			document.getElementById("page-Workspaces") ||
			document.getElementById("page-workspaces") ||
			document.querySelector('.page-container[data-page-route="Workspaces"]')
		);
	}

	function resolveWorkspaceEditorMount() {
		const root = getWorkspacesPageRoot();
		if (root) {
			let esc = root.querySelector(".layout-main-section .editor-js-container");
			if (!esc) esc = root.querySelector(".editor-js-container");
			if (!esc) {
				const lms = root.querySelector(".layout-main-section");
				if (lms) esc = lms;
			}
			if (esc) return esc;
		}
		const candidates = document.querySelectorAll(".editor-js-container");
		let fallback = null;
		for (let i = 0; i < candidates.length; i++) {
			const el = candidates[i];
			if (!el || !el.isConnected) continue;
			if (!fallback) fallback = el;
			if (el.getClientRects && el.getClientRects().length > 0) return el;
		}
		return fallback;
	}

	function injectPpLandingShell() {
		const deniedRoot = document.getElementById("kt-pp-root");
		if (deniedRoot && deniedRoot.getAttribute("data-pp-access-denied") === "1") {
			return { ok: false, inserted: false };
		}
		if (document.getElementById("kt-pp-list-root")) {
			return { ok: true, inserted: false };
		}
		const esc = resolveWorkspaceEditorMount();
		if (!esc) return { ok: false, inserted: false };
		const wrap = document.createElement("div");
		wrap.id = "kt-pp-root";
		wrap.className = "kt-pp-injected-shell";
		wrap.removeAttribute("data-pp-access-denied");
		wrap.setAttribute("data-testid", "pp-landing-page");
		wrap.innerHTML =
			'<div class="kt-pp-workspace-header kt-pp-workspace-header--compact">' +
			'<div class="kt-pp-header-row">' +
			'<div>' +
			'<h2 class="kt-pp-page-title h5 mb-1" data-testid="pp-page-title">' +
			escapeHtml(__("Procurement Planning")) +
			"</h2>" +
			'<p class="kt-pp-page-intro text-muted small mb-0">' +
			escapeHtml(__("Structure approved demand into compliant procurement packages.")) +
			"</p>" +
			"</div>" +
			'<div class="kt-pp-header-cta d-flex flex-wrap gap-2 align-items-start" data-testid="pp-header-cta">' +
			"</div>" +
			"</div>" +
			"</div>" +
			'<div class="kt-pp-plan-context" data-testid="pp-current-plan-bar" id="kt-pp-plan-bar-host"></div>' +
			'<div class="kt-pp-plan-summary-belt" id="kt-pp-plan-summary-belt" data-testid="pp-plan-summary-belt">' +
			'<div class="kt-pp-plan-summary__label text-muted" data-testid="pp-plan-summary-label">' +
			escapeHtml(__("Plan summary")) +
			"</div>" +
			'<div class="row g-2 align-items-stretch" id="kt-pp-kpi-host"></div>' +
			'<p class="kt-pp-kpi-currency-note text-muted" id="kt-pp-kpi-currency-note" data-testid="pp-kpi-currency-context" hidden></p></div>' +
			'<div class="kt-pp-package-work" data-testid="pp-package-work">' +
			'<div class="kt-pp-package-work__label text-muted" data-testid="pp-package-work-label">' +
			escapeHtml(__("Package work")) +
			"</div>" +
			'<div class="kt-pp-control-bar" data-testid="pp-control-bar">' +
			'<div class="kt-pp-control-bar__row kt-pp-control-bar__row--tabs" data-testid="pp-control-row-tabs">' +
			'<div class="kt-pp-tab-group" role="tablist" aria-label="' +
			escapeHtml(__("Workbench scope")) +
			'">' +
			'<button type="button" class="btn btn-sm btn-default kt-pp-work-tab" data-kt-pp-tab="mywork" data-testid="pp-tab-my-work">' +
			escapeHtml(__("My Work")) +
			"</button>" +
			'<button type="button" class="btn btn-sm btn-default kt-pp-work-tab" data-kt-pp-tab="all" data-testid="pp-tab-all">' +
			escapeHtml(__("All")) +
			"</button>" +
			'<button type="button" class="btn btn-sm btn-default kt-pp-work-tab" data-kt-pp-tab="approved" data-testid="pp-tab-approved">' +
			escapeHtml(__("Approved")) +
			"</button>" +
			'<button type="button" class="btn btn-sm btn-default kt-pp-work-tab" data-kt-pp-tab="ready" data-testid="pp-tab-ready">' +
			escapeHtml(__("Ready for Tender")) +
			"</button>" +
			"</div>" +
			'<div class="kt-pp-search-compact-wrap">' +
			'<div class="kt-pp-search-compact">' +
			'<label class="kt-pp-sr-only" for="kt-pp-list-search">' +
			escapeHtml(__("Search")) +
			'</label><input type="search" class="form-control form-control-sm" id="kt-pp-list-search" data-testid="pp-package-search" placeholder="' +
			escapeHtml(__("Search packages…")) +
			'" />' +
			"</div></div></div>" +
			'<div class="kt-pp-control-bar__row kt-pp-control-bar__row--queues" data-testid="pp-queue-search-line" id="kt-pp-queue-row">' +
			'<div id="kt-pp-queue-pills" class="kt-pp-queue-pills" data-testid="pp-queue-pills"></div>' +
			'<div class="kt-pp-toolbar-queues-right">' +
			'<button type="button" class="kt-pp-scope-hint-btn" id="kt-pp-scope-hint" data-testid="pp-scope-hint" hidden="">' +
			'<span class="kt-pp-scope-hint-glyph" aria-hidden="true">' +
			"\u2139" +
			"</span></button></div></div></div>" +
			'<div class="kt-pp-master-detail kt-pp-master-detail--tight">' +
			'<div class="kt-pp-col-list">' +
			'<div class="kt-pp-section kt-surface">' +
			'<h3 class="kt-pp-section__title mb-1" id="kt-pp-list-title">' +
			escapeHtml(__("Packages")) +
			"</h3>" +
			'<div id="kt-pp-list-root" data-testid="pp-package-list"></div></div></div>' +
			'<div class="kt-pp-col-detail">' +
			'<div class="kt-pp-section kt-surface">' +
			'<div id="kt-pp-detail-root" data-testid="pp-detail-panel"></div></div></div></div></div>';

		const ed = document.getElementById("editorjs");
		if (ed && esc.contains(ed)) esc.insertBefore(wrap, ed);
		else esc.insertBefore(wrap, esc.firstChild);

		ensurePpDelegatedClicks();
		return { ok: true, inserted: true };
	}

	function syncWorkTabButtons() {
		document.querySelectorAll("[data-kt-pp-tab]").forEach(function (btn) {
			const on = btn.getAttribute("data-kt-pp-tab") === activeWorkTab;
			btn.classList.remove("btn-primary");
			btn.classList.add("btn", "btn-sm", "btn-default", "kt-pp-work-tab");
			btn.classList.toggle("kt-pp-work-tab--active", on);
			btn.setAttribute("aria-selected", on ? "true" : "false");
		});
	}

	function renderHeaderCtas(payload) {
		const slot = document.querySelector('[data-testid="pp-header-cta"]');
		if (!slot) return;
		slot.innerHTML = "";
		if (payload && payload.show_new_plan) {
			const b = document.createElement("button");
			b.type = "button";
			b.className = "btn btn-primary btn-sm";
			b.setAttribute("data-testid", "pp-new-plan-button");
			b.setAttribute("data-pp-action", "new-plan");
			b.textContent = __("New Plan");
			slot.appendChild(b);
		}
		if (payload && payload.show_new_package) {
			const b2 = document.createElement("button");
			b2.type = "button";
			b2.className = "btn btn-default btn-sm";
			b2.setAttribute("data-testid", "pp-new-package-button");
			b2.setAttribute("data-pp-action", "new-package");
			b2.textContent = __("New Package");
			slot.appendChild(b2);
		}
		if (payload && payload.show_apply_template) {
			const b3 = document.createElement("button");
			b3.type = "button";
			b3.className = "btn btn-default btn-sm";
			b3.setAttribute("data-testid", "pp-action-apply-template");
			b3.setAttribute("data-pp-action", "apply-template");
			b3.textContent = __("Apply template");
			slot.appendChild(b3);
		}
	}

	function formatKpiValue(row, _currency) {
		const fmt = row.format || "int";
		const v = Number(row.value) || 0;
		if (fmt === "currency") {
			const n = Math.round(v).toLocaleString(undefined, { maximumFractionDigits: 0 });
			return escapeHtml(n);
		}
		return escapeHtml(String(Math.round(v)));
	}

	function applyKpis(payload) {
		const host = document.getElementById("kt-pp-kpi-host");
		if (!host) return;
		const kpis = (payload && payload.kpis) || [];
		const cur = (payload && payload.currency) || "KES";
		const curNote = document.getElementById("kt-pp-kpi-currency-note");
		if (curNote) {
			const hasCurrency = kpis.some(function (k) {
				return k && (k.format || "int") === "currency";
			});
			if (hasCurrency) {
				curNote.textContent = __("All monetary figures in {0}").replace("{0}", cur);
				curNote.hidden = false;
			} else {
				curNote.textContent = "";
				curNote.hidden = true;
			}
		}
		const summaryBelt = document.getElementById("kt-pp-plan-summary-belt");
		if (!kpis.length) {
			host.innerHTML = "";
			if (summaryBelt) {
				summaryBelt.classList.add("kt-pp-plan-summary-belt--empty");
			}
			return;
		}
		if (summaryBelt) {
			summaryBelt.classList.remove("kt-pp-plan-summary-belt--empty");
		}
		let html = "";
		for (let i = 0; i < kpis.length; i++) {
			const k = kpis[i];
			const tid = k.testid || "pp-kpi-" + (k.id || i);
			html +=
				'<div class="col-6 col-md-3">' +
				'<div class="kt-pp-kpi-card kt-surface" data-testid="' +
				escapeHtml(tid) +
				'">' +
				'<div class="kt-pp-kpi-label">' +
				escapeHtml(k.label || "") +
				"</div>" +
				'<div class="kt-pp-kpi-value">' +
				formatKpiValue(k, cur) +
				"</div></div></div>";
		}
		host.innerHTML = html;
	}

	function renderPlanBar(payload) {
		const host = document.getElementById("kt-pp-plan-bar-host");
		if (!host) return;
		const cur = payload && payload.current_plan;
		const plans = (payload && payload.plans) || [];
		if (!cur && !plans.length) {
			host.innerHTML =
				'<div class="kt-pp-plan-context__inner py-1">' +
				'<p class="text-muted small mb-0">' +
				escapeHtml(__("No procurement plan found. Create a plan to start packaging demand.")) +
				"</p></div>";
			return;
		}
		let sel = "";
		if (plans.length > 1) {
			sel =
				'<label class="small text-muted me-2 mb-0 d-inline-flex align-items-center gap-1">' +
				escapeHtml(__("Plan")) +
				' <select class="form-control form-control-sm d-inline-block w-auto" id="kt-pp-plan-select" aria-label="' +
				escapeHtml(__("Current plan")) +
				'">';
			for (let i = 0; i < plans.length; i++) {
				const p = plans[i];
				const selAttr = cur && p.name === cur.name ? " selected" : "";
				sel +=
					'<option value="' +
					escapeHtml(p.name) +
					'"' +
					selAttr +
					">" +
					escapeHtml(p.label || p.plan_code || p.name) +
					"</option>";
			}
			sel += "</select></label>";
		}
		let metaLineFixed = "";
		if (cur) {
			const fy =
				cur.fiscal_year != null && String(cur.fiscal_year).length
					? String(cur.fiscal_year)
					: "";
			metaLineFixed =
				'<span class="kt-pp-plan-code font-monospace">' +
				escapeHtml(cur.plan_code || "") +
				'</span><span class="kt-pp-plan-meta-sep" aria-hidden="true">·</span><span class="kt-pp-plan-name">' +
				escapeHtml(cur.plan_name || "") +
				"</span>" +
				(fy
					? '<span class="kt-pp-plan-meta-sep" aria-hidden="true">·</span><span class="text-muted">' +
						escapeHtml(fy) +
						"</span>"
					: "") +
				'<span class="kt-pp-plan-meta-sep" aria-hidden="true">·</span><span class="text-muted">' +
				escapeHtml(cur.procuring_entity_label || cur.procuring_entity || "") +
				"</span>";
		}
		const stLabel = (cur && cur.status) || "";
		const statusBlock = stLabel
			? '<span class="kt-pp-plan-status badge badge-secondary">' + escapeHtml(stLabel) + "</span>"
			: "";
		let planActs = "";
		if (cur && cur.name) {
			const pid = escapeHtml(cur.name);
			if (payload.show_submit_plan) {
				const dis = payload.plan_submit_ready === false;
				const blk = (payload.plan_submit_blockers || []).join("; ");
				const titleAttr = dis && blk ? ' title="' + escapeHtml(blk) + '"' : "";
				planActs +=
					'<button type="button" class="btn btn-sm ' +
					(dis ? "btn-default" : "btn-primary") +
					'" data-pp-plan-action="submit-plan" data-pp-plan-id="' +
					pid +
					'" data-testid="pp-plan-action-submit"' +
					(dis ? " disabled" : "") +
					titleAttr +
					">" +
					escapeHtml(__("Submit plan")) +
					"</button>";
			}
			if (payload.show_approve_plan) {
				planActs +=
					'<button type="button" class="btn btn-sm btn-primary" data-pp-plan-action="approve-plan" data-pp-plan-id="' +
					pid +
					'" data-testid="pp-plan-action-approve">' +
					escapeHtml(__("Approve plan")) +
					"</button>";
			}
			if (payload.show_return_plan) {
				planActs +=
					'<button type="button" class="btn btn-sm btn-default" data-pp-plan-action="return-plan" data-pp-plan-id="' +
					pid +
					'" data-testid="pp-plan-action-return">' +
					escapeHtml(__("Return plan")) +
					"</button>";
			}
			if (payload.show_reject_plan) {
				planActs +=
					'<button type="button" class="btn btn-sm btn-default" data-pp-plan-action="reject-plan" data-pp-plan-id="' +
					pid +
					'" data-testid="pp-plan-action-reject">' +
					escapeHtml(__("Reject plan")) +
					"</button>";
			}
			if (payload.show_lock_plan) {
				planActs +=
					'<button type="button" class="btn btn-sm btn-default" data-pp-plan-action="lock-plan" data-pp-plan-id="' +
					pid +
					'" data-testid="pp-plan-action-lock">' +
					escapeHtml(__("Lock plan")) +
					"</button>";
			}
		}
		const leftCol =
			'<div class="kt-pp-plan-context__left d-flex flex-wrap align-items-center min-w-0 flex-grow-1 gap-2">' +
			sel +
			(cur ? '<div class="kt-pp-plan-context__meta small">' + metaLineFixed + "</div>" : "") +
			"</div>";
		const rightCol =
			'<div class="kt-pp-plan-context__actions" data-testid="pp-plan-actions">' +
			(statusBlock ? '<span class="kt-pp-plan-context__status-wrap">' + statusBlock + "</span>" : "") +
			(planActs ? '<div class="kt-pp-plan-context__plan-actions">' + planActs + "</div>" : "") +
			"</div>";
		host.innerHTML = cur
			? '<div class="kt-pp-plan-context__inner d-flex flex-wrap align-items-stretch justify-content-between gap-2 w-100">' +
				leftCol +
				rightCol +
				"</div>"
			: '<div class="kt-pp-plan-context__inner d-flex flex-wrap align-items-center">' + sel + "</div>";
		const selEl = document.getElementById("kt-pp-plan-select");
		if (selEl) {
			selEl.addEventListener("change", function () {
				loadPpLandingData(selEl.value || null);
			});
		}
	}

	function updatePpScopeHint() {
		const el = document.getElementById("kt-pp-scope-hint");
		if (!el) {
			return;
		}
		const tab = activeWorkTab;
		const q = activeQueueId || "";
		let msg = "";
		if (tab === "all" && q === "all_packages") {
			msg = __(
				"All packages shows every active package in the current plan (all workflow statuses). Use the other filters to narrow the list."
			);
		} else if (tab === "all" && q) {
			msg = __(
				"Workbench scope is All — this list is a filtered sub-queue. Choose “All packages” to see the full set."
			);
		}
		if (!msg) {
			el.removeAttribute("title");
			el.setAttribute("aria-label", "");
			el.hidden = true;
			return;
		}
		el.setAttribute("title", msg);
		el.setAttribute("aria-label", msg);
		el.hidden = false;
	}

	function renderQueuePills(payload) {
		const host = document.getElementById("kt-pp-queue-pills");
		const titleEl = document.getElementById("kt-pp-list-title");
		const listRootEarly = document.getElementById("kt-pp-list-root");
		if (!host) return;
		const qt = (payload && payload.queue_tabs) || {};
		const list = qt[activeWorkTab] || [];
		if (!list.length) {
			lastPackageListRows = null;
			host.innerHTML =
				'<span class="text-muted small">' + escapeHtml(__("No queues for this tab.")) + "</span>";
			if (titleEl) titleEl.textContent = __("Packages");
			activeQueueId = null;
			if (listRootEarly) {
				listRootEarly.innerHTML =
					'<div class="kt-pp-empty text-muted small" data-testid="pp-package-list-empty">' +
					escapeHtml(__("No queues for this tab.")) +
					"</div>";
			}
			updatePpScopeHint();
			return;
		}
		if (!activeQueueId || !list.some(function (q) { return q.id === activeQueueId; })) {
			activeQueueId = list[0].id;
		}
		const inline = list.slice(0, PP_MAX_INLINE_QUEUES);
		const overflow = list.slice(PP_MAX_INLINE_QUEUES);
		const parts = inline.map(function (q) {
			const on = q.id === activeQueueId;
			const cls =
				"btn btn-sm kt-pp-queue-pill " +
				(on ? "btn-primary is-active" : "btn-default");
			const tid = q.testid || "pp-queue-" + q.id;
			return (
				'<button type="button" class="' +
				cls +
				'" data-pp-queue="' +
				escapeHtml(q.id) +
				'" data-testid="' +
				escapeHtml(tid) +
				'">' +
				escapeHtml(String(q.label || q.id)) +
				"</button>"
			);
		});
		if (overflow.length) {
			const moreOn = overflow.some(function (q) { return q.id === activeQueueId; });
			const moreItems = overflow
				.map(function (q) {
					const on = q.id === activeQueueId;
					const tid = q.testid || "pp-queue-" + q.id;
					return (
						'<li><button type="button" class="kt-pp-queue-more__item' +
						(on ? " is-active" : "") +
						'" data-pp-queue="' +
						escapeHtml(q.id) +
						'" data-testid="' +
						escapeHtml(tid) +
						'" role="menuitem">' +
						escapeHtml(String(q.label || q.id)) +
						"</button></li>"
					);
				})
				.join("");
			parts.push(
				'<div class="btn-group kt-pp-queue-more' +
				(moreOn ? " kt-pp-queue-more--open" : "") +
				'">' +
				'<button type="button" class="btn btn-sm btn-default dropdown-toggle' +
				(moreOn ? " is-active" : "") +
				'" data-toggle="dropdown" data-testid="pp-queue-more-toggle" aria-haspopup="true" aria-expanded="false" aria-label="' +
				escapeHtml(__("More queues")) +
				'">' +
				escapeHtml(__("More")) +
				' <span class="caret"></span></button>' +
				'<ul class="dropdown-menu kt-pp-queue-more__menu" role="menu">' +
				moreItems +
				"</ul></div>"
			);
		}
		host.innerHTML = parts.join("");
		const active = list.find(function (q) { return q.id === activeQueueId; });
		if (titleEl && active) {
			titleEl.textContent = active.label || __("Packages");
		}
		updatePpScopeHint();
		if (lastLandingPayload && lastLandingPayload.ok === true && activeQueueId) {
			fetchPackageList();
		}
	}

	function buildBadgeChips(badges) {
		if (!badges) return "";
		const chips = [];
		if (badges.emergency) {
			chips.push(
				'<span class="kt-pp-badge kt-pp-badge--emergency">' + escapeHtml(__("Emergency")) + "</span>"
			);
		}
		if (badges.high_risk) {
			chips.push(
				'<span class="kt-pp-badge kt-pp-badge--risk">' + escapeHtml(__("High Risk")) + "</span>"
			);
		}
		if (chips.length >= 2) {
			return chips.slice(0, 2).join("");
		}
		if (badges.submitted) {
			chips.push(
				'<span class="kt-pp-badge kt-pp-badge--neutral">' + escapeHtml(__("Submitted")) + "</span>"
			);
		}
		if (chips.length >= 2) {
			return chips.slice(0, 2).join("");
		}
		if (badges.ready) {
			chips.push(
				'<span class="kt-pp-badge kt-pp-badge--ready">' + escapeHtml(__("Ready for Tender")) + "</span>"
			);
		}
		if (chips.length >= 2) {
			return chips.slice(0, 2).join("");
		}
		if (badges.released) {
			chips.push(
				'<span class="kt-pp-badge kt-pp-badge--neutral">' + escapeHtml(__("Released")) + "</span>"
			);
		}
		return chips.slice(0, 2).join("");
	}

	function getPpPackageSearchQuery() {
		const el = document.getElementById("kt-pp-list-search");
		return (el && el.value && el.value.trim()) || "";
	}

	function applyPpClientFilter() {
		if (lastPackageListRows == null) {
			return;
		}
		const q = getPpPackageSearchQuery().toLowerCase();
		const rows = !q
			? lastPackageListRows
			: lastPackageListRows.filter(function (row) {
					const a =
						String(row.package_name || "") +
						" " +
						String(row.package_code || "") +
						" " +
						String(row.procurement_method || "") +
						" " +
						String(row.template_name || "");
					return a.toLowerCase().indexOf(q) !== -1;
				});
		const still = rows.some(function (x) {
			return x.name === selectedPackageName;
		});
		if (!still) {
			selectedPackageName = null;
		}
		renderPackageRows(rows, { clientFiltered: !!q });
		syncPackageRowSelectionHighlight();
		renderPackageDetail();
	}

	function renderPackageRows(rows, opts) {
		const o = opts || {};
		const listRoot = document.getElementById("kt-pp-list-root");
		if (!listRoot) return;
		if (!rows || !rows.length) {
			const hasFilter = o.clientFiltered;
			if (hasFilter) {
				listRoot.innerHTML =
					'<div class="kt-pp-empty text-muted small" data-testid="pp-package-list-empty">' +
					escapeHtml(__("No packages match your search.")) +
					"</div>";
				return;
			}
			const qid = activeQueueId || "";
			const msg = emptyMessageForQueue(qid);
			const showCta =
				lastLandingPayload &&
				lastLandingPayload.show_new_package &&
				(qid === "draft_packages" || qid === "structured_packages" || qid === "all_packages");
			const createCta = showCta
				? '<button type="button" class="btn btn-primary btn-sm" data-pp-action="new-package" data-testid="pp-package-list-cta-create">' +
					escapeHtml(__("Create Package")) +
					"</button>"
				: "";
			const switchCta =
				'<button type="button" class="btn btn-default btn-sm" data-pp-action="empty-focus-queues" data-testid="pp-empty-cta-queues">' +
				escapeHtml(__("Switch queue")) +
				"</button>";
			const cta = '<div class="mt-2 d-flex flex-wrap gap-2 justify-content-center align-items-center">' + createCta + switchCta + "</div>";
			listRoot.innerHTML =
				'<div class="kt-pp-empty kt-pp-empty--v3 text-muted small" data-testid="pp-package-list-empty">' +
				"<p class=\"mb-0 text-center\">" +
				escapeHtml(msg) +
				"</p>" +
				cta +
				"</div>";
			return;
		}
		const planCtx = lastLandingPayload && lastLandingPayload.current_plan;
		let planMetaLine = "";
		if (planCtx) {
			const pCode = String(planCtx.plan_code || "").trim();
			const pFy =
				planCtx.fiscal_year != null && String(planCtx.fiscal_year).trim().length
					? String(planCtx.fiscal_year)
					: "";
			planMetaLine = [pCode, pFy].filter(function (s) { return s; }).join(" · ");
		}
		let html = '<div class="kt-pp-package-list-inner">';
		for (let i = 0; i < rows.length; i++) {
			const row = rows[i];
			const code = row.package_code || "";
			const slug = slugForTestid(code);
			const nm = row.name || "";
			const isOn = nm && nm === selectedPackageName;
			const badgeHtml = buildBadgeChips(row.badges || {});
			const planLine =
				planMetaLine.length > 0
					? '<div class="kt-pp-package-row__plan" data-testid="pp-row-plan-' +
						escapeHtml(slug) +
						'">' +
						escapeHtml(planMetaLine) +
						"</div>"
					: "";
			html +=
				'<button type="button" class="kt-pp-package-row' +
				(isOn ? " is-active" : "") +
				'" data-pp-package-row="1" data-pp-package-name="' +
				escapeHtml(nm) +
				'" data-testid="pp-row-' +
				escapeHtml(slug) +
				'">' +
				'<div class="kt-pp-package-row__primary" data-testid="pp-row-title-' +
				escapeHtml(slug) +
				'">' +
				escapeHtml(row.package_name || "") +
				"</div>" +
				planLine +
				'<div class="kt-pp-package-row__secondary" data-testid="pp-row-method-' +
				escapeHtml(slug) +
				'">' +
				escapeHtml(code) +
				" · " +
				escapeHtml(row.procurement_method || "") +
				"</div>" +
				'<div class="kt-pp-package-row__tertiary" data-testid="pp-row-value-' +
				escapeHtml(slug) +
				'">' +
				formatPackageListValue(row) +
				' · <span data-testid="pp-row-template-' +
				escapeHtml(slug) +
				'">' +
				escapeHtml(row.template_name || "") +
				"</span></div>";
			if (badgeHtml) {
				html += '<div class="kt-pp-package-row__badges">' + badgeHtml + "</div>";
			}
			html += "</button>";
		}
		html += "</div>";
		listRoot.innerHTML = html;
	}

	function syncPackageRowSelectionHighlight() {
		document.querySelectorAll(".kt-pp-package-row").forEach(function (btn) {
			const n = btn.getAttribute("data-pp-package-name");
			btn.classList.toggle("is-active", !!(n && n === selectedPackageName));
		});
	}

	function fetchPackageList() {
		const listRoot = document.getElementById("kt-pp-list-root");
		if (!listRoot || !activeQueueId) return;
		if (!lastLandingPayload || lastLandingPayload.ok !== true) return;
		listRoot.innerHTML =
			'<div class="text-muted small py-2" data-testid="pp-package-list-loading">' +
			escapeHtml(__("Loading…")) +
			"</div>";
		const sel = document.getElementById("kt-pp-plan-select");
		const planArg =
			(sel && sel.value) ||
			(lastLandingPayload.current_plan && lastLandingPayload.current_plan.name) ||
			null;
		frappe.call({
			method: "kentender_procurement.procurement_planning.api.package_list.get_pp_package_list",
			args: {
				plan: planArg,
				queue_id: activeQueueId,
				limit: 100,
			},
			callback: function (r) {
				if (!isPpWorkspaceRoute()) return;
				const data = r && r.message;
				if (!data || data.ok === false) {
					lastPackageListRows = null;
					const err =
						(data && data.message) ||
						__("Could not load packages for this queue.");
					listRoot.innerHTML =
						'<div class="alert alert-warning mb-0 small" role="status">' + escapeHtml(err) + "</div>";
					return;
				}
				if (data.plan === null && data.message) {
					lastPackageListRows = null;
					listRoot.innerHTML =
						'<div class="kt-pp-empty text-muted small" data-testid="pp-package-list-no-plan">' +
						escapeHtml(String(data.message)) +
						"</div>";
					selectedPackageName = null;
					renderPackageDetail();
					return;
				}
				const rows = data.rows || [];
				const stillThere = rows.some(function (x) {
					return x.name === selectedPackageName;
				});
				if (!stillThere) {
					selectedPackageName = null;
				}
				lastPackageListRows = rows;
				applyPpClientFilter();
			},
			error: function () {
				if (!isPpWorkspaceRoute() || !listRoot) return;
				lastPackageListRows = null;
				listRoot.innerHTML =
					'<p class="text-danger small mb-0">' + escapeHtml(__("Could not load package list.")) + "</p>";
			},
		});
	}

	function renderDetailPlaceholder() {
		renderPackageDetail();
	}

	function renderLandingBlocked(payload) {
		const listRoot = document.getElementById("kt-pp-list-root");
		const detailRoot = document.getElementById("kt-pp-detail-root");
		const code = (payload && payload.error_code) || "";
		const msg = (payload && payload.message) || __("Could not load Procurement Planning.");
		const hint =
			code === "PP_ACCESS_DENIED"
				? __("Ask an administrator to assign a Procurement Planning role.")
				: code === "PP_NOT_INSTALLED"
					? __("Run bench migrate after installing the app.")
					: "";
		if (listRoot) {
			listRoot.innerHTML =
				'<div class="alert alert-warning mb-0" data-testid="pp-landing-blocked" role="status">' +
				"<strong>" +
				escapeHtml(__("Procurement Planning cannot load")) +
				"</strong><p class=\"mb-1 small\">" +
				escapeHtml(msg) +
				"</p>" +
				(hint ? '<p class="mb-0 small text-muted">' + escapeHtml(hint) + "</p>" : "") +
				"</div>";
		}
		if (detailRoot) {
			detailRoot.innerHTML =
				'<div class="kt-pp-empty text-muted small" data-testid="pp-detail-blocked">' +
				escapeHtml(__("Fix the issue above, then reload.")) +
				"</div>";
		}
		selectedPackageName = null;
		applyKpis({ kpis: [] });
		const kpiHost = document.getElementById("kt-pp-kpi-host");
		if (kpiHost) kpiHost.innerHTML = "";
		const planBar = document.getElementById("kt-pp-plan-bar-host");
		if (planBar) planBar.innerHTML = "";
	}

	function loadPpLandingData(planName) {
		const listRoot = document.getElementById("kt-pp-list-root");
		const detailRoot = document.getElementById("kt-pp-detail-root");
		if (!listRoot || !detailRoot) return;
		detailFetchSeq += 1;
		selectedPackageName = null;
		listRoot.innerHTML =
			'<div class="text-muted small py-3">' + escapeHtml(__("Loading…")) + "</div>";
		detailRoot.innerHTML = "";
		frappe.call({
			method: "kentender_procurement.procurement_planning.api.landing.get_pp_landing_shell_data",
			args: planName ? { plan: planName } : {},
			callback: function (r) {
				if (!r || !r.message) return;
				const payload = r.message;
				lastLandingPayload = payload;
				if (payload.ok === false) {
					lastRoleKey = payload.role_key || "auditor";
					const ppRoot = document.getElementById("kt-pp-root");
					const msg = payload.message || __("Could not load Procurement Planning.");
					const code = payload.error_code || "";
					if (ppRoot) {
						ppRoot.setAttribute("data-pp-access-denied", "1");
						ppRoot.innerHTML =
							'<div class="alert alert-warning mb-0" data-testid="pp-landing-blocked" role="status">' +
							"<strong>" +
							escapeHtml(__("Procurement Planning")) +
							"</strong>" +
							'<p class="mb-1 small">' +
							escapeHtml(String(msg)) +
							"</p>" +
							(code === "PP_ACCESS_DENIED"
								? '<p class="mb-0 small text-muted">' +
									escapeHtml(
										__(
											"You need a Planning role and read access to procurement plans to use this workbench."
										)
									) +
									"</p>"
								: "") +
							"</div>";
					} else {
						renderHeaderCtas(payload);
						renderLandingBlocked(payload);
					}
					return;
				}
				const okRoot = document.getElementById("kt-pp-root");
				if (okRoot) {
					okRoot.removeAttribute("data-pp-access-denied");
				}
				lastRoleKey = payload.role_key || "planner";
				renderHeaderCtas(payload);
				renderPlanBar(payload);
				applyKpis(payload);
				renderQueuePills(payload);
				renderDetailPlaceholder();
			},
			error: function () {
				if (listRoot) {
					listRoot.innerHTML =
						'<p class="text-danger small">' + escapeHtml(__("Could not load landing data.")) + "</p>";
				}
				applyKpis({ kpis: [] });
			},
		});
	}

	function ensurePpDelegatedClicks() {
		const root = document.getElementById("kt-pp-root");
		if (!root || root.dataset.ppDelegated === "1") return;
		root.dataset.ppDelegated = "1";
		root.addEventListener("click", function (ev) {
			const planAct = ev.target.closest("[data-pp-plan-action]");
			if (planAct && root.contains(planAct)) {
				const pa = planAct.getAttribute("data-pp-plan-action") || "";
				const pid = planAct.getAttribute("data-pp-plan-id") || "";
				if (pa && pid) {
					runPpPlanWorkflow(pa, pid);
				}
				return;
			}
			const act = ev.target.closest("[data-pp-action]");
			if (act && root.contains(act)) {
				const a = act.getAttribute("data-pp-action");
				if (a === "empty-focus-queues") {
					focusPpQueueToolbar();
					return;
				}
				if (a === "new-plan" && typeof frappe !== "undefined" && frappe.model && frappe.set_route) {
					const doc = frappe.model.get_new_doc("Procurement Plan");
					frappe.set_route("Form", doc.doctype, doc.name);
					return;
				}
				if (a === "new-package" && typeof frappe !== "undefined" && frappe.model && frappe.set_route) {
					const cur = lastLandingPayload && lastLandingPayload.current_plan;
					const doc = frappe.model.get_new_doc("Procurement Package");
					if (cur && cur.name) {
						doc.plan_id = cur.name;
					}
					frappe.set_route("Form", doc.doctype, doc.name);
					return;
				}
				if (a === "apply-template") {
					const cur = lastLandingPayload && lastLandingPayload.current_plan;
					if (!cur || !cur.name) {
						frappe.msgprint(__("Select a procurement plan first."));
						return;
					}
					const sel =
						window.kentender_procurement && window.kentender_procurement.pp_template_selector
							? window.kentender_procurement.pp_template_selector
							: null;
					if (!sel || typeof sel.open !== "function") {
						frappe.msgprint(__("Template selector is not available. Reload the page and try again."));
						return;
					}
					sel.open({
						mode: "workbench",
						planName: cur.name,
						on_workbench_done: function () {
							loadPpLandingData(null);
						},
					});
					return;
				}
			}
			const dAct = ev.target.closest("[data-pp-detail-action]");
			if (dAct && root.contains(dAct)) {
				const action = dAct.getAttribute("data-pp-detail-action") || "";
				const wrap = dAct.closest("[data-pp-detail-package]");
				const pn =
					(wrap && wrap.getAttribute("data-pp-detail-package")) || selectedPackageName || "";
				if (action && pn) {
					runPpPackageWorkflow(action, pn);
				}
				return;
			}
			const pkgRow = ev.target.closest("[data-pp-package-row]");
			if (pkgRow && root.contains(pkgRow)) {
				const nm = pkgRow.getAttribute("data-pp-package-name") || "";
				if (nm && nm === selectedPackageName) {
					selectedPackageName = null;
				} else {
					selectedPackageName = nm || null;
				}
				syncPackageRowSelectionHighlight();
				renderPackageDetail();
				return;
			}
			const tabBtn = ev.target.closest("button[data-kt-pp-tab]");
			if (tabBtn && root.contains(tabBtn)) {
				const t = tabBtn.getAttribute("data-kt-pp-tab");
				activeWorkTab = t || "mywork";
				if (activeWorkTab === "all") {
					activeQueueId = "all_packages";
				}
				syncWorkTabButtons();
				renderQueuePills(lastLandingPayload);
				return;
			}
			const qBtn = ev.target.closest("[data-pp-queue]");
			if (qBtn && root.contains(qBtn)) {
				if (qBtn.tagName === "A") {
					ev.preventDefault();
				}
				const qid = qBtn.getAttribute("data-pp-queue");
				if (qid) {
					activeQueueId = qid;
					renderQueuePills(lastLandingPayload);
				}
			}
		});
	}

	function tryBindPpWorkspace() {
		if (!isPpWorkspaceRoute()) return;
		const inj = injectPpLandingShell();
		if (!inj || !inj.ok) return;
		const listRoot = document.getElementById("kt-pp-list-root");
		const detailRoot = document.getElementById("kt-pp-detail-root");
		if (!listRoot || !detailRoot) return;
		if (inj.inserted) {
			activeWorkTab = "mywork";
			activeQueueId = null;
			syncWorkTabButtons();
			loadPpLandingData(null);
		}
		const s = document.getElementById("kt-pp-list-search");
		if (s && s.dataset.ppSearchBound !== "1") {
			s.dataset.ppSearchBound = "1";
			s.addEventListener("input", function () {
				applyPpClientFilter();
			});
		}
	}

	function requestPpBind(delayMs) {
		if (bindScheduled) return;
		bindScheduled = true;
		setTimeout(function () {
			bindScheduled = false;
			tryBindPpWorkspace();
		}, delayMs || 0);
	}

	function schedulePpWorkspaceBind() {
		if (!isPpWorkspaceRoute()) {
			removePpLandingIfWrongRoute();
			return;
		}
		syncPpShellClass();
		if (typeof frappe.after_ajax === "function") {
			frappe.after_ajax(() => requestPpBind(0));
		} else {
			requestPpBind(0);
		}
		requestPpBind(120);
	}

	function ensureWorkspaceDomObserver() {
		if (workspaceDomObserver || typeof MutationObserver === "undefined") return;
		const target = document.body || document.documentElement;
		if (!target) return;
		workspaceDomObserver = new MutationObserver(function () {
			if (!isPpWorkspaceRoute() || document.getElementById("kt-pp-list-root")) return;
			tryBindPpWorkspace();
		});
		workspaceDomObserver.observe(target, { childList: true, subtree: true });
	}

	function bindPpWorkspaceHooks() {
		if (!hooksBound) {
			hooksBound = true;
			if (window.jQuery) {
				window.jQuery(document).on("page-change", schedulePpWorkspaceBind);
				window.jQuery(document).on("app_ready", schedulePpWorkspaceBind);
			}
			if (frappe.router && frappe.router.on) {
				frappe.router.on("change", schedulePpWorkspaceBind);
			}
			ensureWorkspaceDomObserver();
		}
		syncPpShellClass();
		schedulePpWorkspaceBind();
	}

	function ensurePollPpWorkspace() {
		if (pollStarted) return;
		pollStarted = true;
		function tick() {
			if (!isPpWorkspaceRoute()) removePpLandingIfWrongRoute();
			else if (!document.getElementById("kt-pp-list-root")) tryBindPpWorkspace();
			setTimeout(tick, 400);
		}
		tick();
	}

	function kickPpWorkspace() {
		bindPpWorkspaceHooks();
		ensurePollPpWorkspace();
		setTimeout(schedulePpWorkspaceBind, 400);
	}

	function bootstrapPpWorkspace() {
		function whenFrappeExists() {
			if (typeof window.frappe === "undefined") {
				setTimeout(whenFrappeExists, 20);
				return;
			}
			kickPpWorkspace();
			if (typeof frappe.ready === "function") {
				frappe.ready(kickPpWorkspace);
			}
		}
		whenFrappeExists();
		window.addEventListener("load", kickPpWorkspace);
		setTimeout(kickPpWorkspace, 900);
	}

	bootstrapPpWorkspace();
})();
