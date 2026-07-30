/**
 * Technical Proposal and Implementation Plan — subsection editor + review confirm (Website).
 * Mirrors the qualification_and_capability_web.js save-chain / conflict-retry pattern.
 */
(function () {
	function subRoot() {
		return document.querySelector("[data-testid='kt-tp-subsection-root']");
	}

	function reviewRoot() {
		return document.querySelector("[data-testid='kt-tp-review-root']");
	}

	function isReadOnly() {
		var r = subRoot();
		return !!(r && r.getAttribute("data-read-only") === "1");
	}

	function toast(msg) {
		var el =
			document.querySelector("[data-testid='kt-tp-toast']") ||
			document.querySelector("[data-testid='kt-tp-review-toast']");
		if (!el) {
			window.alert(msg);
			return;
		}
		el.textContent = msg;
		el.classList.add("is-visible");
		el.hidden = false;
		clearTimeout(toast._timer);
		toast._timer = setTimeout(function () {
			el.classList.remove("is-visible");
		}, 3200);
	}

	function extractCallError(r, fallback) {
		var msg = fallback || "Save failed";
		if (!r) return msg;
		if (r.message && r.message._error_message) return String(r.message._error_message);
		if (typeof r.message === "string" && r.message) return r.message;
		try {
			if (r._server_messages) {
				var raw = r._server_messages;
				var list = typeof raw === "string" ? JSON.parse(raw) : raw;
				if (Array.isArray(list) && list.length) {
					var first = list[0];
					var obj = typeof first === "string" ? JSON.parse(first) : first;
					if (obj && obj.message) return String(obj.message);
				}
			}
		} catch (e) {
			/* ignore parse errors */
		}
		return msg;
	}

	function call(method, args) {
		return new Promise(function (resolve, reject) {
			if (typeof frappe === "undefined" || !frappe.call) {
				reject(new Error("Session unavailable"));
				return;
			}
			frappe.call({
				method: method,
				args: args,
				callback: function (r) {
					if (r && r.exc) {
						reject(new Error(extractCallError(r, "Save failed")));
						return;
					}
					resolve((r && r.message) || r);
				},
				error: function (err) {
					reject(err instanceof Error ? err : new Error(extractCallError(err, "Save failed")));
				},
			});
		});
	}

	function escapeAttr(value) {
		return String(value == null ? "" : value)
			.replace(/&/g, "&amp;")
			.replace(/"/g, "&quot;")
			.replace(/</g, "&lt;");
	}

	function escapeText(value) {
		return String(value == null ? "" : value)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;");
	}

	function fieldVal(scope, key, prefix) {
		var el = scope ? scope.querySelector("[" + (prefix || "data-d") + "='" + key + "']") : null;
		if (!el) return "";
		return String(el.value != null ? el.value : "").trim();
	}

	/* ---------------------------------------------------------------------
	 * Narrative question cards (approach, warranty, transition, org, testing)
	 * ------------------------------------------------------------------- */

	function collectNarratives(r) {
		var out = {};
		r.querySelectorAll("[data-question]").forEach(function (ta) {
			out[ta.getAttribute("data-question")] = ta.value || "";
		});
		return out;
	}

	function collectEvidenceIds(r) {
		var out = [];
		r.querySelectorAll("[data-tp-evidence-id]").forEach(function (inp) {
			if (inp.checked) {
				var id = inp.getAttribute("data-tp-evidence-id") || "";
				if (id) out.push(id);
			}
		});
		return out;
	}

	function collectHandover(r) {
		var out = [];
		r.querySelectorAll("[data-handover-row]").forEach(function (row) {
			var check = row.querySelector("[data-handover-provided]");
			var titleEl = row.querySelector("[data-handover-title]");
			var reqEl = row.querySelector("[data-handover-required]");
			out.push({
				deliverable_id: row.getAttribute("data-deliverable-id") || "",
				title: titleEl ? String(titleEl.value || "") : "",
				required: reqEl ? Number(reqEl.value || 0) : 0,
				provided: check && check.checked ? 1 : 0,
			});
		});
		return out;
	}

	/* ---------------------------------------------------------------------
	 * Generic record tables (roles, matrix, stages, training, risks, …)
	 * ------------------------------------------------------------------- */

	var RECORD_ID_FIELD = {
		resource_roles: "role_id",
		coordination_matrix: "row_id",
		test_stages: "stage_id",
		training_activities: "activity_id",
		risks: "risk_id",
		assumptions: "assumption_id",
		dependencies: "dependency_id",
		alternatives: "alternative_id",
	};

	var RECORD_FIELDS = {
		resource_roles: ["project_role", "person_id", "providing_org", "delivery_responsibility", "decision_authority"],
		coordination_matrix: [
			"activity_or_deliverable",
			"bidder_responsibility",
			"pe_responsibility",
			"third_party_responsibility",
			"coordination_method",
		],
		test_stages: [
			"test_stage",
			"scope",
			"responsible_party",
			"entry_criteria",
			"expected_output",
			"pe_participation",
			"work_plan_phase",
		],
		training_activities: ["audience", "topic", "delivery_method", "duration", "timing", "responsible_person"],
		risks: ["risk", "potential_effect", "mitigation", "responsible_party", "work_plan_phase"],
		assumptions: ["assumption", "responsible_party", "effect_if_incorrect"],
		dependencies: ["required_input", "responsible_party", "required_by", "affected_activity"],
		alternatives: [
			"title",
			"affected_system_part",
			"description",
			"schedule_impact",
			"price_schedule_ref",
			"supporting_info",
		],
	};

	function personnelOptionsHtml() {
		var tpl = document.querySelector("[data-testid='kt-tp-personnel-options-template']");
		return tpl ? tpl.innerHTML : "<option value=''>Select person…</option>";
	}

	function audienceOptionsHtml() {
		var tpl = document.querySelector("[data-testid='kt-tp-audience-options-template']");
		return tpl ? tpl.innerHTML : "<option value=''>Select audience…</option>";
	}

	var RECORD_SELECT_FIELDS = {
		resource_roles: { person_id: personnelOptionsHtml },
		training_activities: { audience: audienceOptionsHtml },
	};

	var STATUS_REQUIRED = {
		test_stages: ["test_stage", "scope", "responsible_party", "entry_criteria", "expected_output"],
		alternatives: ["title", "affected_system_part", "description"],
	};

	function deriveRegisterRowStatus(kind, vals) {
		vals = vals || {};
		var required = STATUS_REQUIRED[kind] || [];
		var fields = RECORD_FIELDS[kind] || [];
		var requiredOk = required.every(function (f) {
			return String(vals[f] || "").trim();
		});
		var started = fields.some(function (f) {
			return String(vals[f] || "").trim();
		});
		if (requiredOk) return "Complete";
		if (started) return "In Progress";
		return "Not Started";
	}

	function readRowVals(row) {
		var vals = {};
		row.querySelectorAll("[data-r]").forEach(function (el) {
			vals[el.getAttribute("data-r")] = el.value || "";
		});
		return vals;
	}

	function refreshRowStatusBadge(row) {
		var body = row.closest("[data-records-body]");
		if (!body) return;
		var kind = body.getAttribute("data-status-kind");
		if (!kind) return;
		var status = deriveRegisterRowStatus(kind === "test_stage" ? "test_stages" : kind === "alternative" ? "alternatives" : kind, readRowVals(row));
		row.setAttribute("data-row-status", status);
		var badge = row.querySelector("[data-row-status-badge]");
		if (badge) {
			badge.setAttribute("data-status", status);
			badge.textContent = status;
		}
	}

	function statusKindForRecordsKey(key) {
		if (key === "test_stages" || key === "alternatives") return key;
		return "";
	}

	function statusBadgeHtml(rowStatus) {
		return (
			"<td data-tp-status-cell>" +
			"<span class='kt-s600-status' data-status='" +
			escapeAttr(rowStatus) +
			"' data-row-status-badge data-testid='kt-tp-register-status'>" +
			escapeText(rowStatus) +
			"</span></td>"
		);
	}

	function genericRowHtml(key, rec) {
		rec = rec || {};
		var idField = RECORD_ID_FIELD[key] || "record_id";
		var rid = rec[idField] || key + "-" + Math.random().toString(16).slice(2, 10);
		var fields = RECORD_FIELDS[key] || [];
		var selects = RECORD_SELECT_FIELDS[key] || {};
		var readOnly = isReadOnly();
		var statusKind = statusKindForRecordsKey(key);
		var rowStatus = statusKind ? deriveRegisterRowStatus(statusKind, rec) : "";
		var html =
			"<tr data-record-row data-record-id='" +
			rid +
			"'" +
			(rowStatus ? " data-row-status='" + escapeAttr(rowStatus) + "'" : "") +
			">";
		fields.forEach(function (f) {
			if (selects[f]) {
				html +=
					"<td><select data-r='" +
					f +
					"'" +
					(readOnly ? " disabled" : "") +
					">" +
					selects[f]() +
					"</select></td>";
			} else {
				html +=
					"<td><input data-r='" +
					f +
					"' value='" +
					escapeAttr(rec[f] || "") +
					"'" +
					(readOnly ? " disabled" : "") +
					"/></td>";
			}
		});
		// Status must precede Action — otherwise delete lands under the Status header.
		if (statusKind) {
			html += statusBadgeHtml(rowStatus);
		}
		if (!readOnly) {
			html +=
				"<td class='is-right is-actions' data-tp-action-cell>" +
				"<button type='button' class='kt-s600-link' data-tp-remove-row title='Delete'>" +
				"<span class='material-symbols-outlined'>delete</span></button></td>";
		}
		html += "</tr>";
		return html;
	}

	/** Repair rows added by stale JS (Action under Status, empty Action column). */
	function repairRegisterStatusColumns() {
		document.querySelectorAll("[data-records-body][data-status-kind]").forEach(function (body) {
			var kindAttr = body.getAttribute("data-status-kind") || "";
			var key =
				kindAttr === "test_stage"
					? "test_stages"
					: kindAttr === "alternative"
						? "alternatives"
						: statusKindForRecordsKey(body.getAttribute("data-records-body") || "");
			if (!key) return;
			body.querySelectorAll("[data-record-row]").forEach(function (row) {
				if (row.querySelector("[data-row-status-badge]")) {
					refreshRowStatusBadge(row);
					return;
				}
				var actionTd = row.querySelector("td.is-actions, td[data-tp-action-cell]");
				var status = deriveRegisterRowStatus(key, readRowVals(row));
				row.setAttribute("data-row-status", status);
				var tmp = document.createElement("tbody");
				tmp.innerHTML = "<tr>" + statusBadgeHtml(status) + "</tr>";
				var statusTd = tmp.querySelector("td");
				if (!statusTd) return;
				if (actionTd) {
					row.insertBefore(statusTd, actionTd);
				} else {
					row.appendChild(statusTd);
				}
			});
		});
	}

	function collectRecords(key) {
		var body = document.querySelector("[data-records-body='" + key + "']");
		if (!body) return [];
		var idField = RECORD_ID_FIELD[key] || "record_id";
		var out = [];
		body.querySelectorAll("[data-record-row]").forEach(function (row) {
			var rec = {};
			rec[idField] = row.getAttribute("data-record-id") || "";
			row.querySelectorAll("[data-r]").forEach(function (el) {
				rec[el.getAttribute("data-r")] = el.value || "";
				if (el.getAttribute("data-r") === "person_id" && el.tagName === "SELECT" && el.selectedOptions && el.selectedOptions[0]) {
					rec.person_name = String(el.selectedOptions[0].textContent || "").trim();
				}
			});
			out.push(rec);
		});
		return out;
	}

	var ADD_BUTTON_KEYS = {
		"data-tp-add-role": "resource_roles",
		"data-tp-add-matrix-row": "coordination_matrix",
		"data-tp-add-stage": "test_stages",
		"data-tp-add-training": "training_activities",
		"data-tp-add-risk": "risks",
		"data-tp-add-assumption": "assumptions",
		"data-tp-add-dependency": "dependencies",
		"data-tp-add-alternative": "alternatives",
	};

	/* ---------------------------------------------------------------------
	 * Implementation work plan — activities table + right-hand drawer
	 * ------------------------------------------------------------------- */

	function calcCompletion(start, dur) {
		var s = parseInt(start, 10);
		var d = parseInt(dur, 10);
		if (!s || !d || s < 1 || d < 1) return null;
		return s + d - 1;
	}

	function activityRows() {
		var body = document.querySelector("[data-records-body='activities']");
		return body ? body.querySelectorAll("[data-record-row]") : [];
	}

	function activityLabel(row) {
		var name = (row.querySelector("[data-a='activity']") || {}).value || "";
		return name || row.getAttribute("data-record-id") || "";
	}

	function isNoneDependency(depId) {
		var d = String(depId == null ? "" : depId).trim().toLowerCase();
		return !d || d === "none" || d === "null" || d === "n/a" || d === "na" || d === "-" || d === "—" || d === "–";
	}

	function dependencyLabel(depId) {
		if (isNoneDependency(depId)) return "";
		var row = document.querySelector(
			"[data-records-body='activities'] [data-record-id='" + String(depId).replace(/'/g, "\\'") + "']"
		);
		// Never expose internal activity ids in the matrix — show name or Missing.
		return row ? activityLabel(row) : "Missing";
	}

	function collectActivityOptions(excludeId) {
		var out = [];
		activityRows().forEach(function (row) {
			var id = row.getAttribute("data-record-id") || "";
			if (id && id === excludeId) return;
			out.push({ id: id, label: activityLabel(row) });
		});
		return out;
	}

	function collectActivities(r) {
		var body = r.querySelector("[data-records-body='activities']");
		if (!body) return [];
		var out = [];
		body.querySelectorAll("[data-record-row]").forEach(function (row) {
			var rec = { activity_id: row.getAttribute("data-record-id") || "" };
			row.querySelectorAll("[data-a]").forEach(function (el) {
				rec[el.getAttribute("data-a")] = el.value || "";
			});
			out.push(rec);
		});
		return out;
	}

	function deriveActivityRowStatus(vals, knownIds) {
		vals = vals || {};
		var name = String(vals.activity || "").trim();
		var end = calcCompletion(vals.start_week, vals.duration_weeks);
		var role = String(vals.project_role || "").trim();
		var dep = String(vals.dependency_id || "").trim();
		var started = !!(
			name ||
			vals.start_week ||
			vals.duration_weeks ||
			role ||
			dep ||
			String(vals.deliverable || "").trim() ||
			String(vals.milestone || "").trim()
		);
		if (dep && knownIds && knownIds.indexOf(dep) < 0) return "Needs Attention";
		if (name && end && role) return "Complete";
		if (started) {
			if (name && (!end || !role)) return "Needs Attention";
			return "In Progress";
		}
		return "Not Started";
	}

	function activityRowHtml(vals) {
		vals = vals || {};
		var completion = calcCompletion(vals.start_week, vals.duration_weeks);
		var knownIds = collectActivityOptions("").map(function (o) {
			return o.id;
		});
		if (vals.activity_id && knownIds.indexOf(vals.activity_id) < 0) {
			knownIds.push(vals.activity_id);
		}
		var rowStatus = vals.row_status || deriveActivityRowStatus(vals, knownIds);
		var readOnly = isReadOnly();
		var actions = "";
		if (!readOnly) {
			if (rowStatus === "Needs Attention") {
				actions =
					"<td class='is-right is-actions'>" +
					"<button type='button' class='kt-s600-btn kt-s600-btn--danger kt-tp-resolve-btn' data-tp-edit-activity data-testid='kt-tp-resolve-activity'>Resolve</button>" +
					"</td>";
			} else {
				actions =
					"<td class='is-right is-actions'>" +
					"<button type='button' class='kt-s600-link' data-tp-edit-activity title='Edit'><span class='material-symbols-outlined'>edit</span></button>" +
					"<button type='button' class='kt-s600-link' data-tp-remove-row title='Delete'><span class='material-symbols-outlined'>delete</span></button>" +
					"</td>";
			}
		}
		var milestoneHtml = vals.milestone
			? "<span class='kt-tp-milestone'><span class='material-symbols-outlined'>verified</span>" +
				escapeText(vals.milestone) +
				"</span>"
			: "—";
		return (
			"<tr data-record-row data-record-id='" +
			escapeAttr(vals.activity_id) +
			"' data-row-status='" +
			escapeAttr(rowStatus) +
			"'" +
			(rowStatus === "Needs Attention" ? " class='kt-tp-row-attention'" : "") +
			">" +
			"<td class='is-strong' data-cell='activity'>" +
			(escapeText(vals.activity) || "—") +
			"</td>" +
			"<td class='kt-s600-help' data-cell='deliverable'>" +
			(escapeText(vals.deliverable) || "—") +
			"</td>" +
			"<td class='is-center kt-s600-mono' data-cell='start_week'>" +
			(vals.start_week ? "W" + escapeText(vals.start_week) : "—") +
			"</td>" +
			"<td class='is-center kt-s600-mono' data-cell='duration_weeks'>" +
			(vals.duration_weeks ? escapeText(vals.duration_weeks) + "w" : "—") +
			"</td>" +
			"<td class='is-center kt-s600-mono' data-cell='completion_week' data-testid='kt-tp-completion-week'>" +
			(completion ? "W" + completion : "—") +
			"</td>" +
			"<td data-cell='dependency_id'>" +
			(escapeText(dependencyLabel(vals.dependency_id)) || "—") +
			"</td>" +
			"<td data-cell='milestone'>" +
			milestoneHtml +
			"</td>" +
			"<td data-cell='project_role'>" +
			(escapeText(vals.project_role) || "—") +
			"</td>" +
			"<td><span class='kt-s600-status' data-status='" +
			escapeAttr(rowStatus) +
			"' data-testid='kt-tp-activity-status'>" +
			escapeText(rowStatus) +
			"</span></td>" +
			actions +
			"<td hidden>" +
			"<input data-a='activity' value='" + escapeAttr(vals.activity) + "'/>" +
			"<input data-a='deliverable' value='" + escapeAttr(vals.deliverable) + "'/>" +
			"<input data-a='start_week' value='" + escapeAttr(vals.start_week) + "'/>" +
			"<input data-a='duration_weeks' value='" + escapeAttr(vals.duration_weeks) + "'/>" +
			"<input data-a='dependency_id' value='" + escapeAttr(vals.dependency_id) + "'/>" +
			"<input data-a='milestone' value='" + escapeAttr(vals.milestone) + "'/>" +
			"<input data-a='project_role' value='" + escapeAttr(vals.project_role) + "'/>" +
			"</td>" +
			"</tr>"
		);
	}

	function activityDrawerHtml(vals) {
		vals = vals || {};
		var options = collectActivityOptions(vals.activity_id)
			.map(function (o) {
				return (
					"<option value='" +
					escapeAttr(o.id) +
					"'" +
					(vals.dependency_id === o.id ? " selected" : "") +
					">" +
					escapeText(o.label) +
					"</option>"
				);
			})
			.join("");
		var completion = calcCompletion(vals.start_week || "1", vals.duration_weeks || "1");
		return (
			"<div class='kt-s600-drawer-fields' data-testid='kt-tp-activity-form'>" +
			"<div class='kt-s600-field'><label>Activity name</label>" +
			"<input data-d='activity' value='" +
			escapeAttr(vals.activity) +
			"' placeholder='e.g. System Integration'/></div>" +
			"<div class='kt-s600-field'><label>Deliverable</label>" +
			"<textarea data-d='deliverable' rows='2'>" +
			escapeText(vals.deliverable) +
			"</textarea></div>" +
			"<div class='kt-s600-field-row'>" +
			"<div class='kt-s600-field'><label>Start week</label>" +
			"<input data-d='start_week' inputmode='numeric' value='" +
			escapeAttr(vals.start_week || "1") +
			"'/></div>" +
			"<div class='kt-s600-field'><label>Duration (weeks)</label>" +
			"<input data-d='duration_weeks' inputmode='numeric' value='" +
			escapeAttr(vals.duration_weeks || "1") +
			"'/></div>" +
			"</div>" +
			"<div class='kt-s600-field'><label>Completion week (calculated)</label>" +
			"<div class='kt-tp-calc-field' data-testid='kt-tp-completion-preview'>" +
			(completion ? "Week " + completion : "—") +
			"</div></div>" +
			"<div class='kt-s600-field'><label>Dependency</label>" +
			"<select data-d='dependency_id'><option value=''>None</option>" +
			options +
			"</select></div>" +
			"<div class='kt-s600-field'><label>Milestone name</label>" +
			"<input data-d='milestone' value='" +
			escapeAttr(vals.milestone) +
			"' placeholder='e.g. Phase 1 completion'/></div>" +
			"<div class='kt-s600-field'><label>Responsible role</label>" +
			"<input data-d='project_role' value='" +
			escapeAttr(vals.project_role) +
			"' placeholder='e.g. Project Manager'/></div>" +
			"</div>"
		);
	}

	/* ---------------------------------------------------------------------
	 * Shared right-hand drawer (activity editor today; extensible)
	 * ------------------------------------------------------------------- */

	function drawerEls() {
		return {
			drawer: document.querySelector("[data-testid='kt-tp-drawer']"),
			backdrop: document.querySelector("[data-testid='kt-tp-drawer-backdrop']"),
			title: document.querySelector("[data-testid='kt-tp-drawer-title']"),
			subtitle: document.querySelector("[data-testid='kt-tp-drawer-subtitle']"),
			body: document.querySelector("[data-testid='kt-tp-drawer-body']"),
			confirm: document.querySelector("[data-testid='kt-tp-drawer-confirm']"),
		};
	}

	var drawerState = { mode: null, meta: null };

	function openDrawer(title, subtitle, html, mode, meta) {
		var d = drawerEls();
		if (!d.drawer || !d.body) return;
		d.title.textContent = title || "Record";
		if (d.subtitle) {
			d.subtitle.textContent = subtitle || "";
			d.subtitle.hidden = !subtitle;
		}
		d.body.innerHTML = html;
		drawerState = { mode: mode, meta: meta || null };
		d.drawer.hidden = false;
		d.drawer.setAttribute("aria-hidden", "false");
		if (d.backdrop) d.backdrop.hidden = false;
	}

	function closeDrawer() {
		var d = drawerEls();
		if (!d.drawer) return;
		d.drawer.hidden = true;
		d.drawer.setAttribute("aria-hidden", "true");
		if (d.backdrop) d.backdrop.hidden = true;
		if (d.body) d.body.innerHTML = "";
		drawerState = { mode: null, meta: null };
	}

	function openActivityDrawer(vals, row) {
		openDrawer(
			row ? "Edit activity" : "Add Activity",
			row ? vals.activity : "",
			activityDrawerHtml(vals),
			"activity",
			{ activity_id: vals.activity_id, row: row || null }
		);
	}

	function confirmDrawer() {
		var d = drawerEls();
		var body = d.body;
		if (!body || !drawerState.mode) {
			closeDrawer();
			return;
		}
		if (drawerState.mode === "activity") {
			var form = body.querySelector("[data-testid='kt-tp-activity-form']") || body;
			var meta = drawerState.meta || {};
			var vals = {
				activity_id: meta.activity_id || "act-" + Math.random().toString(16).slice(2, 10),
				activity: fieldVal(form, "activity"),
				deliverable: fieldVal(form, "deliverable"),
				start_week: fieldVal(form, "start_week") || "1",
				duration_weeks: fieldVal(form, "duration_weeks") || "1",
				dependency_id: isNoneDependency(fieldVal(form, "dependency_id"))
					? ""
					: fieldVal(form, "dependency_id"),
				milestone: fieldVal(form, "milestone"),
				project_role: fieldVal(form, "project_role"),
			};
			if (!vals.activity) {
				toast("Enter an activity name");
				return;
			}
			var tbody = document.querySelector("[data-records-body='activities']");
			if (!tbody) {
				closeDrawer();
				return;
			}
			if (meta.row && meta.row.isConnected) meta.row.remove();
			tbody.insertAdjacentHTML("beforeend", activityRowHtml(vals));
			closeDrawer();
			saveAndMaybeContinue(false);
			return;
		}
		closeDrawer();
	}

	/* ---------------------------------------------------------------------
	 * Payload collection by renderer
	 * ------------------------------------------------------------------- */

	function collectPayload(r) {
		var renderer = r.getAttribute("data-renderer");
		if (renderer === "project_organization_and_coordination") {
			return {
				bucket: {
					narratives: collectNarratives(r),
					resource_roles: collectRecords("resource_roles"),
					coordination_matrix: collectRecords("coordination_matrix"),
				},
			};
		}
		if (renderer === "technical_approach" || renderer === "warranty_defect_repair_and_support") {
			var narrativeBucket = { narratives: collectNarratives(r) };
			if (renderer === "technical_approach") {
				narrativeBucket.evidence_ids = collectEvidenceIds(r);
			}
			return { bucket: narrativeBucket };
		}
		if (renderer === "transition_and_handover") {
			return {
				bucket: {
					narratives: collectNarratives(r),
					handover_deliverables: collectHandover(r),
				},
			};
		}
		if (renderer === "implementation_work_plan") {
			return { bucket: { activities: collectActivities(r) } };
		}
		if (renderer === "training_and_knowledge_transfer") {
			return { bucket: { training_activities: collectRecords("training_activities") } };
		}
		if (renderer === "testing_and_quality_assurance") {
			return {
				bucket: {
					narratives: collectNarratives(r),
					test_stages: collectRecords("test_stages"),
				},
			};
		}
		if (renderer === "risks_assumptions_and_dependencies") {
			return {
				bucket: {
					risks: collectRecords("risks"),
					assumptions: collectRecords("assumptions"),
					dependencies: collectRecords("dependencies"),
				},
			};
		}
		if (renderer === "technical_alternatives") {
			return { bucket: { alternatives: collectRecords("alternatives") } };
		}
		return { bucket: {} };
	}

	/* ---------------------------------------------------------------------
	 * Save chain + KT_TP_CONFLICT retry (mirrors qualification pattern)
	 * ------------------------------------------------------------------- */

	function applyProgressDto(out) {
		var r = subRoot();
		if (!r || !out) return;
		var progEl = r.querySelector("[data-testid='kt-tp-sub-progress']");
		if (progEl && out.progress_text) progEl.textContent = out.progress_text;
		var statusEl = r.querySelector("[data-testid='kt-tp-sub-status']");
		if (statusEl && out.status) {
			statusEl.textContent = out.status;
			statusEl.setAttribute("data-status", out.status);
		}
		var issueEl = r.querySelector("[data-testid='kt-tp-sub-issue']");
		if (issueEl) {
			if (out.issue) {
				issueEl.textContent = out.issue;
				issueEl.hidden = false;
			} else {
				issueEl.textContent = "";
				issueEl.hidden = true;
			}
		}
		[
			"kt-tp-approach-progress-text",
			"kt-tp-warranty-progress-text",
			"kt-tp-transition-progress-text",
			"kt-tp-work-plan-progress-text",
		].forEach(function (tid) {
			var el = r.querySelector("[data-testid='" + tid + "']");
			if (el && out.progress_text) el.textContent = out.progress_text;
		});
	}

	var saveChain = Promise.resolve();

	function saveAndMaybeContinue(goOverview) {
		var r = subRoot();
		if (!r || r.getAttribute("data-read-only") === "1") return;
		var navigate = !!goOverview;
		saveChain = saveChain
			.then(function () {
				return runSave(navigate);
			})
			.catch(function () {
				/* keep the queue alive after unexpected rejections */
			});
	}

	function isConflictError(err) {
		var msg = (err && err.message) || "";
		return /updated elsewhere|reload and try again|KT_TP_CONFLICT/i.test(msg);
	}

	function runSave(goOverview, isRetry) {
		var r = subRoot();
		if (!r || r.getAttribute("data-read-only") === "1") return Promise.resolve();
		var btns = r.querySelectorAll("[data-tp-save]");
		var confirmBtn = document.querySelector("[data-testid='kt-tp-drawer-confirm']");
		btns.forEach(function (b) {
			b.disabled = true;
		});
		if (confirmBtn) confirmBtn.disabled = true;
		var payload = collectPayload(r);
		var expected = isRetry ? null : r.getAttribute("data-bid-modified") || null;
		return call("kentender_procurement.tender_configurations.save_technical_proposal_subsection", {
			published_tender_ref: r.getAttribute("data-publication-ref"),
			subsection_key: r.getAttribute("data-subsection-key"),
			payload: payload,
			expected_modified: expected,
		})
			.then(function (out) {
				if (out && out.bid_modified) r.setAttribute("data-bid-modified", out.bid_modified);
				toast("Saved");
				if (goOverview) {
					window.location.href = r.getAttribute("data-section-url") || r.getAttribute("data-workspace-url");
				} else if (out) {
					applyProgressDto(out);
				}
			})
			.catch(function (err) {
				if (!isRetry && isConflictError(err)) {
					try {
						if (typeof frappe !== "undefined" && frappe.hide_msgprint) {
							frappe.hide_msgprint();
						}
						document
							.querySelectorAll(".modal.show .btn-modal-close, .msgprint-dialog .btn-modal-close")
							.forEach(function (el) {
								el.click();
							});
					} catch (e) {
						/* ignore */
					}
					return runSave(goOverview, true);
				}
				toast((err && err.message) || "Could not save");
			})
			.finally(function () {
				btns.forEach(function (b) {
					b.disabled = false;
				});
				if (confirmBtn) confirmBtn.disabled = false;
			});
	}

	/* ---------------------------------------------------------------------
	 * Review page — integration/interoperability confirmation
	 * ------------------------------------------------------------------- */

	function syncConfirmButton() {
		var r = reviewRoot();
		if (!r) return;
		var cb = r.querySelector("[data-testid='kt-tp-confirm-checkbox']");
		var completeBtn = r.querySelector("[data-testid='kt-tp-confirm-btn']");
		var draftBtn = r.querySelector("[data-testid='kt-tp-save-draft']");
		var locked = r.getAttribute("data-confirmed") === "1";
		var checked = !!(cb && cb.checked);
		// Complete stays available after confirm so bidders can return to the overview.
		if (completeBtn) completeBtn.disabled = !(locked || checked);
		if (draftBtn) draftBtn.disabled = locked || !checked;
		if (locked && cb) {
			cb.checked = true;
			cb.disabled = true;
		}
	}

	function applyConfirmUi(out) {
		var r = reviewRoot();
		if (!r) return;
		r.setAttribute("data-confirmed", "1");
		if (out && out.bid_modified) r.setAttribute("data-bid-modified", out.bid_modified);
		var cb = r.querySelector("[data-testid='kt-tp-confirm-checkbox']");
		if (cb) {
			cb.checked = true;
			cb.disabled = true;
		}
		var meta = r.querySelector("[data-testid='kt-tp-confirm-meta']");
		var conf = (out && out.integration_confirmation) || {};
		if (!meta) {
			var card = r.querySelector("[data-testid='kt-tp-confirm-card']");
			if (card) {
				meta = document.createElement("p");
				meta.className = "kt-s600-help kt-tp-confirm-meta";
				meta.setAttribute("data-testid", "kt-tp-confirm-meta");
				card.appendChild(meta);
			}
		}
		if (meta) {
			meta.textContent =
				"Confirmed by " + (conf.user || "") + (conf.timestamp ? " · " + conf.timestamp : "");
		}
		syncConfirmButton();
	}

	function goToSectionOverview() {
		var r = reviewRoot();
		if (!r) return;
		var dest =
			r.getAttribute("data-section-url") ||
			r.getAttribute("data-workspace-url") ||
			"/";
		window.location.href = dest;
	}

	function runConfirm(options, isRetry) {
		var opts = options || {};
		var navigate = !!opts.navigate;
		var r = reviewRoot();
		if (!r) return Promise.resolve();
		if (r.getAttribute("data-confirmed") === "1") {
			if (navigate) {
				toast("Section complete — returning to overview…");
				window.setTimeout(goToSectionOverview, 200);
			} else {
				toast("Confirmation already saved");
			}
			return Promise.resolve();
		}
		var completeBtn = r.querySelector("[data-testid='kt-tp-confirm-btn']");
		var draftBtn = r.querySelector("[data-testid='kt-tp-save-draft']");
		if (completeBtn) completeBtn.disabled = true;
		if (draftBtn) draftBtn.disabled = true;
		var expected = isRetry ? null : r.getAttribute("data-bid-modified") || null;
		return call("kentender_procurement.tender_configurations.confirm_technical_proposal_integration", {
			published_tender_ref: r.getAttribute("data-publication-ref"),
			expected_modified: expected,
		})
			.then(function (out) {
				applyConfirmUi(out);
				if (navigate) {
					toast("Section complete — returning to overview…");
					window.setTimeout(goToSectionOverview, 350);
					return;
				}
				toast("Confirmation saved");
			})
			.catch(function (err) {
				if (!isRetry && isConflictError(err)) {
					return runConfirm(opts, true);
				}
				toast((err && err.message) || "Could not confirm");
				syncConfirmButton();
			});
	}

	function requireConfirmCheckbox() {
		var r = reviewRoot();
		if (!r) return false;
		if (r.getAttribute("data-confirmed") === "1") return true;
		var cb = r.querySelector("[data-testid='kt-tp-confirm-checkbox']");
		if (!cb || !cb.checked) {
			toast("Please confirm integration responsibility before saving.");
			return false;
		}
		return true;
	}

	function initReviewPage() {
		var r = reviewRoot();
		if (!r) return;
		var cb = r.querySelector("[data-testid='kt-tp-confirm-checkbox']");
		if (cb) cb.addEventListener("change", syncConfirmButton);
		syncConfirmButton();
	}

	/* ---------------------------------------------------------------------
	 * Global event delegation
	 * ------------------------------------------------------------------- */

	document.addEventListener("click", function (ev) {
		var t = ev.target;
		if (!t) return;

		if (t.closest("[data-tp-save='draft']")) {
			ev.preventDefault();
			saveAndMaybeContinue(false);
		}
		if (t.closest("[data-tp-save='continue']")) {
			ev.preventDefault();
			saveAndMaybeContinue(true);
		}

		if (t.closest("[data-tp-drawer-confirm]")) {
			ev.preventDefault();
			confirmDrawer();
		} else if (
			t.closest("[data-tp-drawer-close]") ||
			t.closest("[data-tp-drawer-cancel]") ||
			t.closest("[data-testid='kt-tp-drawer-backdrop']")
		) {
			ev.preventDefault();
			closeDrawer();
		}

		if (t.closest("[data-tp-remove-row]")) {
			ev.preventDefault();
			var row = t.closest("[data-record-row]");
			if (row) row.remove();
		}

		Object.keys(ADD_BUTTON_KEYS).forEach(function (attr) {
			if (t.closest("[" + attr + "]")) {
				ev.preventDefault();
				var key = ADD_BUTTON_KEYS[attr];
				var body = document.querySelector("[data-records-body='" + key + "']");
				if (body) body.insertAdjacentHTML("beforeend", genericRowHtml(key, {}));
			}
		});

		if (t.closest("[data-tp-add-activity]")) {
			ev.preventDefault();
			openActivityDrawer({});
		}
		if (t.closest("[data-tp-edit-activity]")) {
			ev.preventDefault();
			var arow = t.closest("[data-record-row]");
			if (!arow) return;
			var avals = { activity_id: arow.getAttribute("data-record-id") || "" };
			arow.querySelectorAll("[data-a]").forEach(function (el) {
				avals[el.getAttribute("data-a")] = el.value || "";
			});
			openActivityDrawer(avals, arow);
		}
	});

	document.addEventListener("input", function (ev) {
		var t = ev.target;
		if (!t) return;
		if (t.matches("[data-testid='kt-tp-activity-form'] [data-d='start_week'], [data-testid='kt-tp-activity-form'] [data-d='duration_weeks']")) {
			var form = t.closest("[data-testid='kt-tp-activity-form']");
			var preview = form ? form.querySelector("[data-testid='kt-tp-completion-preview']") : null;
			if (preview) {
				var completion = calcCompletion(fieldVal(form, "start_week"), fieldVal(form, "duration_weeks"));
				preview.textContent = completion ? "Week " + completion : "—";
			}
		}
		if (t.matches("[data-r]") && t.closest("[data-status-kind]")) {
			var statusRow = t.closest("[data-record-row]");
			if (statusRow) refreshRowStatusBadge(statusRow);
		}
	});

	document.addEventListener("click", function (ev) {
		var t = ev.target;
		if (!t) return;
		if (t.closest("[data-tp-review-save='draft']") || t.closest("[data-testid='kt-tp-save-draft']")) {
			ev.preventDefault();
			if (!requireConfirmCheckbox()) return;
			runConfirm({ navigate: false });
			return;
		}
		if (t.closest("[data-tp-review-save='complete']") || t.closest("[data-testid='kt-tp-confirm-btn']")) {
			ev.preventDefault();
			if (!requireConfirmCheckbox()) return;
			runConfirm({ navigate: true });
		}
	});

	document.addEventListener("DOMContentLoaded", function () {
		repairRegisterStatusColumns();
		initReviewPage();
	});
})();
