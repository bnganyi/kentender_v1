/**
 * Qualification category screens — Stitch tables + drawers (Website).
 */
(function () {
	function root() {
		return document.querySelector("[data-testid='kt-s600-category-root']");
	}

	function toast(msg) {
		var el = document.querySelector("[data-testid='kt-s600-toast']");
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

	function setPendingPosition(positionId, title, req) {
		var r = root();
		if (!r) return;
		if (positionId) r.setAttribute("data-pending-position-id", positionId);
		else r.removeAttribute("data-pending-position-id");
		if (title) r.setAttribute("data-pending-position-title", title);
		else r.removeAttribute("data-pending-position-title");
		if (req) r.setAttribute("data-pending-position-req", req);
		else r.removeAttribute("data-pending-position-req");
	}

	function getPendingPosition() {
		var r = root();
		var fromMeta = (drawerState.meta && drawerState.meta.positionId) || "";
		var fromRoot = r ? r.getAttribute("data-pending-position-id") || "" : "";
		var form = document.querySelector("[data-testid='kt-s600-new-person-form']");
		var fromForm = form ? form.getAttribute("data-assign-position-id") || "" : "";
		return fromForm || fromMeta || fromRoot || "";
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

	function drawerEls() {
		return {
			drawer: document.querySelector("[data-testid='kt-s600-drawer']"),
			backdrop: document.querySelector("[data-testid='kt-s600-drawer-backdrop']"),
			title: document.querySelector("[data-testid='kt-s600-drawer-title']"),
			subtitle: document.querySelector("[data-testid='kt-s600-drawer-subtitle']"),
			body: document.querySelector("[data-testid='kt-s600-drawer-body']"),
			confirm: document.querySelector("[data-testid='kt-s600-drawer-confirm']"),
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
		if (d.confirm) {
			if (mode === "project") d.confirm.textContent = "Save project";
			else if (mode === "assign") d.confirm.textContent = "Assign person";
			else if (mode === "partner") d.confirm.textContent = "Save Partner Details";
			else if (mode === "new_person") d.confirm.textContent = "Save person";
			else d.confirm.textContent = "Save";
		}
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

	function collectRecordsFromTable(key) {
		var body = document.querySelector("[data-records-body='" + key + "']");
		if (!body) return [];
		var out = [];
		body.querySelectorAll("[data-record-row]").forEach(function (row) {
			var rec = { record_id: row.getAttribute("data-record-id") || "" };
			row.querySelectorAll("[data-r]").forEach(function (inp) {
				rec[inp.getAttribute("data-r")] = inp.value || "";
			});
			if (key === "non_performing") {
				rec.title = rec.contract || "";
			} else if (key === "pending_litigation") {
				rec.title = rec.matter || "";
			} else {
				rec.title = rec.case_number || "";
			}
			out.push(rec);
		});
		return out;
	}

	function collectContract(r) {
		var sel = r.querySelector("[data-field='member_id']");
		var memberId = (sel && sel.value) || "lead";
		var members = {};
		var row = { member_id: memberId };
		["non_performing", "pending_litigation", "litigation_history"].forEach(function (key) {
			var checked = r.querySelector("input[name='" + key + "']:checked");
			row[key] = checked ? checked.value : null;
			row[key + "_records"] = collectRecordsFromTable(key);
		});
		members[memberId] = row;
		return { bucket: { members: members } };
	}

	function recomputeTurnoverAvg(r) {
		var total = 0;
		var n = 0;
		r.querySelectorAll("[data-to-row]").forEach(function (row) {
			var amt = parseFloat((row.querySelector("[data-to='amount']") || {}).value || "");
			if (!isNaN(amt) && amt > 0) {
				total += amt;
				n += 1;
				var eq = row.querySelector("[data-to-equiv]");
				if (eq) eq.textContent = amt.toLocaleString(undefined, { maximumFractionDigits: 2 });
			}
		});
		var avg = n ? total / n : 0;
		var hidden = r.querySelector("[data-field='turnover_amount']");
		if (hidden) hidden.value = avg ? String(Math.round(avg * 100) / 100) : "";
		var cur = r.querySelector("[data-field='turnover_currency']");
		if (cur) cur.value = "KES";
		var label = r.querySelector("[data-testid='kt-s600-avg-turnover']");
		if (label) label.textContent = avg ? avg.toLocaleString(undefined, { maximumFractionDigits: 2 }) : "0.00";
	}

	function collectFinancial(r) {
		var years = [];
		r.querySelectorAll("[data-fy-row]").forEach(function (row) {
			years.push({
				year: (row.querySelector("[data-fy='year']") || {}).value || "",
				currency: (row.querySelector("[data-fy='currency']") || {}).value || "KES",
				total_assets: (row.querySelector("[data-fy='assets']") || {}).value || "",
				total_liabilities: (row.querySelector("[data-fy='liabilities']") || {}).value || "",
				net_worth: (row.querySelector("[data-fy='net_worth']") || {}).value || "",
				statement_attached: !!(row.querySelector("[data-fy='attached']") || {}).checked,
				file_name: (row.querySelector("[data-fy='file']") || {}).value || "",
			});
		});
		recomputeTurnoverAvg(r);
		var tYears = [];
		r.querySelectorAll("[data-to-row]").forEach(function (row) {
			tYears.push({
				year: (row.querySelector("[data-to='year']") || {}).value || "",
				currency: (row.querySelector("[data-to='currency']") || {}).value || "KES",
				amount: (row.querySelector("[data-to='amount']") || {}).value || "",
			});
		});
		var lines = [];
		r.querySelectorAll("[data-res-row]").forEach(function (row) {
			lines.push({
				resource_type: (row.querySelector("[data-res='type']") || {}).value || "",
				provider: (row.querySelector("[data-res='provider']") || {}).value || "",
				amount: (row.querySelector("[data-res='amount']") || {}).value || "",
				currency: (row.querySelector("[data-res='currency']") || {}).value || "KES",
				evidence_id: (row.querySelector("[data-res='evidence']") || {}).value || "",
				file_name: (row.querySelector("[data-res='evidence']") || {}).value || "",
			});
		});
		var firstAmt = lines.length ? lines[0].amount : "";
		return {
			bucket: {
				financial_years: years,
				turnover: {
					years: tYears,
					average_amount: (r.querySelector("[data-field='turnover_amount']") || {}).value || "",
					currency: (r.querySelector("[data-field='turnover_currency']") || {}).value || "KES",
				},
				resources: {
					lines: lines,
					amount: firstAmt,
					currency: lines.length ? lines[0].currency : "KES",
					evidence_id: lines.length ? lines[0].evidence_id : "",
				},
			},
		};
	}

	function collectExperience(r) {
		var projects = [];
		var seen = {};
		r.querySelectorAll("[data-project-row]").forEach(function (row) {
			var id = row.getAttribute("data-project-id") || "";
			if (id && seen[id]) return;
			if (id) seen[id] = true;
			projects.push({
				project_id: id,
				contract_id: (row.querySelector("[data-p='contract_id']") || {}).value || "",
				description: (row.querySelector("[data-p='description']") || {}).value || "",
				procuring_entity: (row.querySelector("[data-p='pe']") || {}).value || "",
				start_year: (row.querySelector("[data-p='start_year']") || {}).value || "",
				start_month: (row.querySelector("[data-p='start_month']") || {}).value || "1",
				end_year: (row.querySelector("[data-p='end_year']") || {}).value || "",
				end_month: (row.querySelector("[data-p='end_month']") || {}).value || "12",
				use_for_general: !!(row.querySelector("[data-p='general']") || {}).checked,
				use_for_specific: !!(row.querySelector("[data-p='specific']") || {}).checked,
				role: (row.querySelector("[data-p='role']") || {}).value || "",
				amount: (row.querySelector("[data-p='amount']") || {}).value || "",
				currency: (row.querySelector("[data-p='currency']") || {}).value || "KES",
				similarity_notes: (row.querySelector("[data-p='similarity']") || {}).value || "",
			});
		});
		var generalIds = [];
		var specificIds = [];
		projects.forEach(function (p) {
			if (p.use_for_general) generalIds.push(p.project_id);
			if (p.use_for_specific) specificIds.push(p.project_id);
		});
		return {
			projects: projects,
			bucket: {
				general_project_ids: generalIds,
				specific_project_ids: specificIds,
			},
		};
	}

	function collectPersonnel(r) {
		var personnel = [];
		r.querySelectorAll("[data-person-row]").forEach(function (row) {
			personnel.push({
				person_id: row.getAttribute("data-person-id") || "",
				full_name: (row.querySelector("[data-per='name']") || {}).value || "",
				years_experience: (row.querySelector("[data-per='years']") || {}).value || "",
				qualifications: (row.querySelector("[data-per='qual']") || {}).value || "",
				cv_attached: !!(row.querySelector("[data-per='cv']") || {}).checked,
				providing_member: (row.querySelector("[data-per='member']") || {}).value || "",
			});
		});
		var assignments = {};
		r.querySelectorAll("[data-position-assign]").forEach(function (sel) {
			var pos = sel.getAttribute("data-position-assign");
			if (pos && sel.value) assignments[pos] = sel.value;
		});
		return { personnel: personnel, bucket: { assignments: assignments } };
	}

	function collectPartners(r) {
		var items = {};
		var orgs = [];
		r.querySelectorAll("[data-partner-item]").forEach(function (block) {
			var iid = block.getAttribute("data-partner-item");
			var provider = (block.querySelector("input[name='provider_" + iid + "']:checked") || {}).value || "";
			var orgId = (block.querySelector("[data-field='organization_id']") || {}).value || "";
			var orgName = (block.querySelector("[data-field='organization_name']") || {}).value || "";
			var role = (block.querySelector("[data-field='org_role']") || {}).value || "Manufacturer";
			if (provider === "other" && orgName && !orgId) {
				orgId = "org-" + Math.random().toString(16).slice(2, 10);
				block.querySelector("[data-field='organization_id']").value = orgId;
			}
			if (provider === "other" && orgId) {
				orgs.push({
					organization_id: orgId,
					legal_name: orgName,
					name: orgName,
					role: role,
				});
			}
			var criteria = {};
			block.querySelectorAll("[data-crit]").forEach(function (critEl) {
				var cid = critEl.getAttribute("data-crit");
				criteria[cid] = {
					complete: !!(critEl.querySelector("[data-crit-complete]") || {}).checked,
					evidence_id: (critEl.querySelector("[data-crit-evidence]") || {}).value || "",
					tender_specific: critEl.getAttribute("data-tender-specific") === "1",
					source_tender_ref: critEl.getAttribute("data-pub-ref") || "",
				};
			});
			items[iid] = {
				provider: provider,
				organization_id: orgId,
				organization_name: orgName,
				criteria_responses: criteria,
			};
		});
		var external = !!(r.querySelector("[data-field='external_provider']") || {}).checked;
		return {
			organizations: orgs,
			flags: { external_provider_selected: external ? 1 : 0 },
			bucket: { items: items },
		};
	}

	function collectPayload(r) {
		var key = r.getAttribute("data-category-key");
		if (key === "contract_performance_and_litigation") return collectContract(r);
		if (key === "financial_capability") return collectFinancial(r);
		if (key === "experience") return collectExperience(r);
		if (key === "key_personnel") return collectPersonnel(r);
		if (key === "delivery_partners") return collectPartners(r);
		return { bucket: {} };
	}

	function fieldVal(scope, key, prefix) {
		var el = scope ? scope.querySelector("[" + (prefix || "data-d") + "='" + key + "']") : null;
		if (!el) return "";
		return String(el.value != null ? el.value : "").trim();
	}

	function projectRowComplete(vals, tableKind) {
		var contract = String((vals && vals.contract_id) || "").trim();
		var endYear = String((vals && vals.end_year) || "").trim();
		var startYear = String((vals && vals.start_year) || "").trim();
		if (!contract || !endYear) return false;
		if (tableKind === "general" && !startYear) return false;
		return true;
	}

	function setStatusPill(el, complete) {
		if (!el) return;
		setRowStatus(el, complete ? "Complete" : "In Progress");
	}

	function setRowStatus(el, status) {
		if (!el) return;
		var s = status || "Not Started";
		el.setAttribute("data-status", s);
		if (s === "Complete") el.textContent = "Complete";
		else if (s === "Needs Attention") el.textContent = "Needs attention";
		else if (s === "Not Started") el.textContent = "Not started";
		else el.textContent = "In progress";
	}

	function personRowComplete(prow) {
		if (!prow) return false;
		var name = fieldVal(prow, "name", "data-per");
		var years = fieldVal(prow, "years", "data-per");
		var qual = fieldVal(prow, "qual", "data-per");
		var cv = !!(prow.querySelector("[data-per='cv']") || {}).checked;
		return !!(name && years && (cv || qual));
	}

	function syncPersonnelProgressFromDom() {
		var r = root();
		if (!r || r.getAttribute("data-category-key") !== "key_personnel") return;
		var rows = r.querySelectorAll("[data-position-row]");
		var total = rows.length;
		var done = 0;
		var unassigned = 0;
		var incomplete = 0;
		var dup = false;
		var used = {};
		var allowDup = allowsDuplicatePersonnel();
		rows.forEach(function (row) {
			var sel = row.querySelector("[data-position-assign]");
			var personId = sel ? sel.value || "" : "";
			var st = row.querySelector(".kt-s600-status");
			if (!personId) {
				unassigned += 1;
				setRowStatus(st, "Not Started");
				return;
			}
			if (!allowDup && used[personId]) {
				dup = true;
				setRowStatus(st, "Needs Attention");
				return;
			}
			used[personId] = true;
			var prow = r.querySelector("[data-person-row][data-person-id='" + personId + "']");
			if (personRowComplete(prow)) {
				done += 1;
				setRowStatus(st, "Complete");
			} else {
				incomplete += 1;
				setRowStatus(st, "In Progress");
			}
		});
		var progressText = done + " of " + total + " positions complete";
		var catProg = r.querySelector("[data-testid='kt-s600-cat-progress']");
		if (catProg) catProg.textContent = progressText;
		var boxProg = r.querySelector("[data-testid='kt-s600-personnel-progress-text']");
		if (!boxProg) {
			var box = r.querySelector("[data-testid='kt-s600-personnel-progress'] strong");
			if (box) box.textContent = progressText;
		} else {
			boxProg.textContent = progressText;
		}
		var status = "Not Started";
		var issue = "";
		if (dup || incomplete) {
			status = "Needs Attention";
			issue = dup
				? "The same person cannot fill multiple positions for this tender."
				: incomplete +
					" assigned position" +
					(incomplete === 1 ? "" : "s") +
					" still need a complete personnel profile.";
		} else if (total > 0 && done >= total) {
			status = "Complete";
		} else if (done > 0 || unassigned < total) {
			status = "In Progress";
			if (unassigned) {
				issue =
					unassigned +
					" required position" +
					(unassigned === 1 ? "" : "s") +
					" remain unassigned.";
			}
		}
		var chip = r.querySelector("[data-testid='kt-s600-cat-status']");
		if (chip) {
			chip.textContent = status;
			chip.setAttribute("data-status", status);
		}
		var issueEl = r.querySelector("[data-testid='kt-s600-cat-issue']");
		if (issueEl) {
			issueEl.textContent = issue;
			issueEl.hidden = !issue;
		}
	}

	function statusPillHtml(complete) {
		if (complete) {
			return '<span class="kt-s600-status" data-status="Complete">Complete</span>';
		}
		return '<span class="kt-s600-status" data-status="In Progress">In progress</span>';
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

	function removeProjectRows(projectId) {
		if (!projectId) return;
		document.querySelectorAll('[data-project-id="' + projectId + '"]').forEach(function (row) {
			row.remove();
		});
	}

	function tableKindForRow(row) {
		if (!row) return "general";
		var host = row.closest("[data-project-table]") || row.parentElement;
		var kind = host ? host.getAttribute("data-project-table") : "";
		return kind === "specific" ? "specific" : "general";
	}

	function syncExperienceStatusesFromDom() {
		var r = root();
		if (!r || r.getAttribute("data-category-key") !== "experience") return;
		r.querySelectorAll("[data-project-row]").forEach(function (row) {
			var kind = tableKindForRow(row);
			var vals = {
				contract_id: fieldVal(row, "contract_id", "data-p"),
				start_year: fieldVal(row, "start_year", "data-p"),
				end_year: fieldVal(row, "end_year", "data-p"),
			};
			setStatusPill(row.querySelector(".kt-s600-status"), projectRowComplete(vals, kind));
		});
	}

	function applyExperienceDto(out) {
		var r = root();
		if (!r || !out || r.getAttribute("data-category-key") !== "experience") return;
		var yearCount = out.qualifying_year_count != null ? out.qualifying_year_count : 0;
		var years = Array.isArray(out.qualifying_years) ? out.qualifying_years : [];
		var minYears = out.min_qualifying_years != null ? out.min_qualifying_years : 5;
		var minSpec = out.min_specific_projects != null ? out.min_specific_projects : 2;
		var specCount = out.specific_count != null ? out.specific_count : 0;
		var yearEl = r.querySelector("[data-kt-year-count]");
		if (yearEl) yearEl.textContent = String(yearCount);
		var yearList = r.querySelector("[data-kt-year-list]");
		if (yearList) yearList.textContent = years.length ? "(" + years.join(", ") + ")" : "";
		var genChip = r.querySelector("[data-kt-general-chip-text]");
		if (genChip) {
			genChip.textContent = yearCount + " of " + minYears + " qualifying years evidenced";
		}
		var specCountEl = r.querySelector("[data-kt-specific-count]");
		if (specCountEl) specCountEl.textContent = String(specCount);
		var specChip = r.querySelector("[data-kt-specific-chip-text]");
		if (specChip) {
			specChip.textContent = specCount + " of " + minSpec + " required records";
		}
		var byId = {};
		(Array.isArray(out.projects) ? out.projects : []).forEach(function (p) {
			if (p && p.project_id) byId[String(p.project_id)] = p;
		});
		r.querySelectorAll("[data-project-row]").forEach(function (row) {
			var pid = row.getAttribute("data-project-id") || "";
			var p = byId[pid];
			var kind = tableKindForRow(row);
			if (p && kind === "general") {
				var yearsCell = row.querySelector("td.kt-s600-mono");
				if (yearsCell && Array.isArray(p.qualifying_years)) {
					yearsCell.textContent = p.qualifying_years.join(", ") || "—";
				}
			}
			// Prefer DOM field values so a partial DTO cannot leave a filled row as In Progress.
			var vals = {
				contract_id:
					fieldVal(row, "contract_id", "data-p") ||
					(p && (p.contract_id || p.description)) ||
					"",
				start_year: fieldVal(row, "start_year", "data-p") || (p && p.start_year) || "",
				end_year: fieldVal(row, "end_year", "data-p") || (p && p.end_year) || "",
			};
			setStatusPill(row.querySelector(".kt-s600-status"), projectRowComplete(vals, kind));
		});
		var chip = r.querySelector("[data-testid='kt-s600-cat-status']");
		if (chip && out.status) {
			chip.textContent = out.status;
			chip.setAttribute("data-status", out.status);
		}
		var prog = r.querySelector("[data-testid='kt-s600-cat-progress']");
		if (prog && out.progress_text) prog.textContent = out.progress_text;
	}

	function applyCategoryProgressDto(out) {
		var r = root();
		if (!r || !out) return;
		var chip = r.querySelector("[data-testid='kt-s600-cat-status']");
		if (chip && out.status) {
			chip.textContent = out.status;
			chip.setAttribute("data-status", out.status);
		}
		var prog = r.querySelector("[data-testid='kt-s600-cat-progress']");
		if (prog && out.progress_text) prog.textContent = out.progress_text;
		var issue = r.querySelector("[data-testid='kt-s600-cat-issue']");
		if (issue) {
			if (out.issue) {
				issue.textContent = out.issue;
				issue.hidden = false;
			} else {
				issue.textContent = "";
				issue.hidden = true;
			}
		}
		var persProg =
			r.querySelector("[data-testid='kt-s600-personnel-progress-text']") ||
			r.querySelector("[data-testid='kt-s600-personnel-progress'] strong");
		if (persProg && out.progress_text) persProg.textContent = out.progress_text;
		var partnersProg =
			r.querySelector("[data-testid='kt-s600-partners-progress-text']") ||
			r.querySelector("[data-testid='kt-s600-partners-progress'] strong");
		if (partnersProg && out.progress_text) partnersProg.textContent = out.progress_text;
		if (r.getAttribute("data-category-key") === "key_personnel") {
			syncPersonnelProgressFromDom();
		}
	}

	function allowsDuplicatePersonnel() {
		var r = root();
		return !!(r && r.getAttribute("data-allow-duplicate-personnel") === "1");
	}

	function positionTitle(positionId) {
		var row = document.querySelector("[data-position-row][data-position-id='" + positionId + "']");
		if (!row) return positionId || "";
		var btn = row.querySelector("[data-s600-assign]");
		if (btn && btn.getAttribute("data-position-title")) {
			return btn.getAttribute("data-position-title");
		}
		var titleCell = row.querySelector("td.is-strong");
		return (titleCell && titleCell.textContent.trim()) || positionId || "";
	}

	function findOtherAssignment(personId, exceptPositionId) {
		if (!personId) return null;
		var found = null;
		document.querySelectorAll("[data-position-assign]").forEach(function (sel) {
			if (found) return;
			var pos = sel.getAttribute("data-position-assign");
			if (pos === exceptPositionId) return;
			if (sel.value && sel.value === personId) {
				found = { positionId: pos, title: positionTitle(pos) };
			}
		});
		return found;
	}

	function duplicatePersonnelMessage(personId, exceptPositionId) {
		if (allowsDuplicatePersonnel()) return "";
		var other = findOtherAssignment(personId, exceptPositionId);
		if (!other) return "";
		return (
			"This person is already assigned to " +
			(other.title || "another position") +
			". Choose a different person."
		);
	}

	function ensurePersonOption(positionId, personId, label) {
		document.querySelectorAll("[data-position-assign]").forEach(function (sel) {
			var has = false;
			Array.prototype.forEach.call(sel.options, function (opt) {
				if (opt.value === personId) has = true;
			});
			if (!has) {
				var opt = document.createElement("option");
				opt.value = personId;
				opt.textContent = label || personId;
				sel.appendChild(opt);
			}
		});
		var sel = document.querySelector(
			'[data-position-assign="' + String(positionId).replace(/"/g, '\\"') + '"]'
		);
		if (sel) sel.value = personId;
		return !!sel;
	}

	function assignPersonToPosition(positionId, personId, label) {
		if (!positionId) {
			toast("No position selected for assignment. Close and click Assign person again.");
			return false;
		}
		if (!personId) {
			toast("Select a person to assign");
			return false;
		}
		var dupMsg = duplicatePersonnelMessage(personId, positionId);
		if (dupMsg) {
			toast(dupMsg);
			return false;
		}
		if (!ensurePersonOption(positionId, personId, label)) {
			toast("Could not find that position in the matrix.");
			return false;
		}
		var row = document.querySelector(
			'[data-position-row][data-position-id="' + String(positionId).replace(/"/g, '\\"') + '"]'
		);
		if (!row) {
			toast("Could not find that position in the matrix.");
			return false;
		}
		var nameEl = row.querySelector("[data-assigned-name]");
		if (nameEl) nameEl.textContent = label || personId;
		var action = row.querySelector("[data-s600-assign]");
		if (action) action.textContent = "Change";
		syncPersonnelProgressFromDom();
		return true;
	}

	function createPersonRecord(vals) {
		var phost = document.querySelector("[data-testid='kt-s600-person-list']");
		if (!phost) return null;
		var pid = "per-" + Math.random().toString(16).slice(2, 10);
		var wrap = document.createElement("div");
		wrap.setAttribute("data-person-row", "");
		wrap.setAttribute("data-person-id", pid);
		wrap.innerHTML =
			'<input data-per="name" value="' +
			escapeAttr(vals.name) +
			'"/>' +
			'<input data-per="years" value="' +
			escapeAttr(vals.years) +
			'"/>' +
			'<textarea data-per="qual">' +
			escapeText(vals.qual) +
			"</textarea>" +
			'<input data-per="member" value="' +
			escapeAttr(vals.member) +
			'"/>' +
			'<input type="checkbox" data-per="cv" checked />';
		phost.appendChild(wrap);
		document.querySelectorAll("[data-position-assign]").forEach(function (sel) {
			var has = false;
			Array.prototype.forEach.call(sel.options, function (opt) {
				if (opt.value === pid) has = true;
			});
			if (!has) {
				var opt = document.createElement("option");
				opt.value = pid;
				opt.textContent = vals.name || pid;
				sel.appendChild(opt);
			}
		});
		return pid;
	}

	function openAssignDrawer(positionId, meta) {
		var btnMeta = meta || {};
		var title = btnMeta.positionTitle || positionTitle(positionId) || "";
		var req = btnMeta.positionReq || "";
		setPendingPosition(positionId, title, req);
		var cards = "";
		document.querySelectorAll("[data-person-row]").forEach(function (prow) {
			var pid = prow.getAttribute("data-person-id");
			var pname = fieldVal(prow, "name", "data-per") || pid;
			var complete = personRowComplete(prow);
			var other = findOtherAssignment(pid, positionId);
			var blocked = !complete || (!!other && !allowsDuplicatePersonnel());
			var detail = !complete
				? "Incomplete"
				: other && !allowsDuplicatePersonnel()
					? "Assigned to " + (other.title || "another position")
					: "Profile Complete";
			cards +=
				'<label class="kt-s600-person-card' +
				(blocked ? " is-disabled" : "") +
				'" data-testid="kt-s600-person-card">' +
				'<input type="radio" name="assign_person" value="' +
				escapeAttr(pid) +
				'" data-label="' +
				escapeAttr(pname) +
				'" ' +
				(blocked ? "disabled" : "") +
				"/>" +
				"<div><strong>" +
				(pname || pid) +
				"</strong><span>" +
				detail +
				"</span></div></label>";
		});
		openDrawer(
			"Assign person",
			title + (req ? " — " + req : ""),
			'<div class="kt-s600-drawer-fields">' +
				'<button type="button" class="kt-s600-btn kt-s600-btn--ghost" data-s600-new-person data-testid="kt-s600-new-person">' +
				'<span class="material-symbols-outlined">person_add</span> Add new person</button>' +
				'<h4 class="kt-s600-eyebrow">Saved personnel</h4>' +
				'<div data-saved-list class="kt-s600-person-list">' +
				(cards || "<p class='kt-s600-help'>No saved personnel yet. Add a new person.</p>") +
				"</div></div>",
			"assign",
			{
				positionId: positionId,
				positionTitle: title,
				positionReq: req,
			}
		);
	}

	function openNewPersonDrawer() {
		var pos = getPendingPosition();
		var r = root();
		var title =
			(drawerState.meta && drawerState.meta.positionTitle) ||
			(r && r.getAttribute("data-pending-position-title")) ||
			positionTitle(pos) ||
			"";
		var req =
			(drawerState.meta && drawerState.meta.positionReq) ||
			(r && r.getAttribute("data-pending-position-req")) ||
			"";
		if (!pos) {
			toast("Open Assign person on a position first, then add a new person.");
			return;
		}
		setPendingPosition(pos, title, req);
		openDrawer(
			"Add new person",
			title || "Key personnel",
			'<div class="kt-s600-drawer-fields" data-testid="kt-s600-new-person-form" data-assign-position-id="' +
				escapeAttr(pos) +
				'">' +
				'<p class="kt-s600-form-error" data-testid="kt-s600-drawer-form-error" role="alert" hidden></p>' +
				'<p class="kt-s600-help">This person will be assigned to <strong>' +
				escapeText(title || pos) +
				"</strong> when you save.</p>" +
				'<div class="kt-s600-field"><label for="kt-s600-person-name">Full name</label>' +
				'<input id="kt-s600-person-name" data-d="name" autocomplete="name" required/></div>' +
				'<div class="kt-s600-field"><label for="kt-s600-person-years">Years of experience</label>' +
				'<input id="kt-s600-person-years" data-d="years" inputmode="numeric" required/></div>' +
				'<div class="kt-s600-field"><label for="kt-s600-person-qual">Qualifications</label>' +
				'<textarea id="kt-s600-person-qual" data-d="qual" rows="2" required></textarea></div>' +
				'<div class="kt-s600-field"><label for="kt-s600-person-member">Providing member</label>' +
				'<input id="kt-s600-person-member" data-d="member" placeholder="Lead bidder or JV member"/></div>' +
				"</div>",
			"new_person",
			{
				positionId: pos,
				positionTitle: title,
				positionReq: req,
			}
		);
		var nameInput = document.getElementById("kt-s600-person-name");
		if (nameInput) nameInput.focus();
	}

	function setDrawerFormError(form, msg) {
		if (!form) {
			toast(msg);
			return;
		}
		var err = form.querySelector("[data-testid='kt-s600-drawer-form-error']");
		if (!err) {
			err = document.createElement("p");
			err.className = "kt-s600-form-error";
			err.setAttribute("data-testid", "kt-s600-drawer-form-error");
			err.setAttribute("role", "alert");
			form.insertBefore(err, form.firstChild);
		}
		err.textContent = msg;
		err.hidden = false;
		toast(msg);
	}

	function clearDrawerFormError(form) {
		if (!form) return;
		var err = form.querySelector("[data-testid='kt-s600-drawer-form-error']");
		if (err) {
			err.textContent = "";
			err.hidden = true;
		}
	}

	function saveNewPersonAndAssign() {
		var body = drawerEls().body;
		if (!body) return false;
		var form = body.querySelector("[data-testid='kt-s600-new-person-form']") || body;
		clearDrawerFormError(form);
		var vals = {
			name: fieldVal(form, "name"),
			years: fieldVal(form, "years"),
			qual: fieldVal(form, "qual"),
			member: fieldVal(form, "member"),
		};
		if (!vals.name) {
			setDrawerFormError(form, "Enter the person's full name");
			var nameEl = form.querySelector("[data-d='name']");
			if (nameEl) nameEl.focus();
			return false;
		}
		if (!vals.years) {
			setDrawerFormError(form, "Enter years of experience");
			var yearsEl = form.querySelector("[data-d='years']");
			if (yearsEl) yearsEl.focus();
			return false;
		}
		if (!/^\d+(\.\d+)?$/.test(vals.years)) {
			setDrawerFormError(form, "Years of experience must be a number");
			var yearsBad = form.querySelector("[data-d='years']");
			if (yearsBad) yearsBad.focus();
			return false;
		}
		if (!vals.qual) {
			setDrawerFormError(form, "Enter qualifications (required for a complete profile)");
			var qualEl = form.querySelector("[data-d='qual']");
			if (qualEl) qualEl.focus();
			return false;
		}
		var pos = getPendingPosition();
		if (!pos) {
			setDrawerFormError(
				form,
				"No position selected. Close this drawer and click Assign person on a row."
			);
			return false;
		}
		var pid = createPersonRecord(vals);
		if (!pid) {
			setDrawerFormError(form, "Could not save the person record on this page.");
			return false;
		}
		if (!assignPersonToPosition(pos, pid, vals.name)) {
			// Keep drawer open so the user can fix the issue (e.g. duplicate).
			// assignPersonToPosition already toasted the reason.
			var toastEl = document.querySelector("[data-testid='kt-s600-toast']");
			setDrawerFormError(
				form,
				(toastEl && toastEl.textContent) || "Could not assign this person to the position."
			);
			return false;
		}
		closeDrawer();
		setPendingPosition("", "", "");
		saveAndMaybeContinue(false);
		return true;
	}

	var saveChain = Promise.resolve();

	function saveAndMaybeContinue(goOverview) {
		var r = root();
		if (!r || r.getAttribute("data-read-only") === "1") return;
		var navigate = !!goOverview;
		// Serialize saves — overlapping calls reuse a stale expected_modified and the
		// later save is rejected while the matrix still looks assigned (lost on reload).
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
		return /updated elsewhere|reload and try again|KT_QUAL_CONFLICT/i.test(msg);
	}

	function runSave(goOverview, isRetry) {
		var r = root();
		if (!r || r.getAttribute("data-read-only") === "1") return Promise.resolve();
		var btn = r.querySelectorAll("[data-s600-save]");
		var confirmBtn = document.querySelector("[data-testid='kt-s600-drawer-confirm']");
		btn.forEach(function (b) {
			b.disabled = true;
		});
		if (confirmBtn) confirmBtn.disabled = true;
		// Collect immediately before each attempt so retries include the latest DOM.
		var payload = collectPayload(r);
		var expected = isRetry ? null : r.getAttribute("data-bid-modified") || null;
		return call("kentender_procurement.tender_configurations.save_qualification_category", {
			published_tender_ref: r.getAttribute("data-publication-ref"),
			category_key: r.getAttribute("data-category-key"),
			payload: payload,
			expected_modified: expected,
		})
			.then(function (out) {
				if (out && out.bid_modified) {
					r.setAttribute("data-bid-modified", out.bid_modified);
				}
				toast("Saved");
				if (goOverview) {
					window.location.href = r.getAttribute("data-section-url") || r.getAttribute("data-workspace-url");
				} else if (out) {
					if (r.getAttribute("data-category-key") === "experience") {
						applyExperienceDto(out);
						syncExperienceStatusesFromDom();
					} else {
						applyCategoryProgressDto(out);
					}
				}
			})
			.catch(function (err) {
				if (!isRetry && isConflictError(err)) {
					// Prior category auto-save often finishes after navigation; retry once
					// without the stale token so the current matrix is not lost.
					try {
						if (typeof frappe !== "undefined" && frappe.hide_msgprint) {
							frappe.hide_msgprint();
						}
						document.querySelectorAll(".modal.show .btn-modal-close, .msgprint-dialog .btn-modal-close").forEach(function (el) {
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
				btn.forEach(function (b) {
					b.disabled = false;
				});
				if (confirmBtn) confirmBtn.disabled = false;
			});
	}

	function recordRowHtml(key) {
		if (key === "non_performing") {
			return (
				"<tr data-record-row data-record-id='rec-" +
				Math.random().toString(16).slice(2, 8) +
				"'>" +
				"<td><input data-r='contract' /></td>" +
				"<td><input data-r='client' /></td>" +
				"<td><input data-r='currency' value='KES' /></td>" +
				"<td class='is-num'><input data-r='amount' /></td>" +
				"<td><input data-r='status' /></td>" +
				"<td class='is-actions'><button type='button' class='kt-s600-link' data-s600-remove-row><span class='material-symbols-outlined'>delete</span></button></td>" +
				"</tr>"
			);
		}
		if (key === "pending_litigation") {
			return (
				"<tr data-record-row data-record-id='rec-" +
				Math.random().toString(16).slice(2, 8) +
				"'>" +
				"<td><input data-r='matter' /></td>" +
				"<td><input data-r='other_party' /></td>" +
				"<td><input data-r='currency' value='KES' /></td>" +
				"<td class='is-num'><input data-r='amount' /></td>" +
				"<td><input data-r='status' /></td>" +
				"<td class='is-actions'><button type='button' class='kt-s600-link' data-s600-remove-row><span class='material-symbols-outlined'>delete</span></button></td>" +
				"</tr>"
			);
		}
		return (
			"<tr data-record-row data-record-id='rec-" +
			Math.random().toString(16).slice(2, 8) +
			"'>" +
			"<td><input data-r='case_number' /></td>" +
			"<td><input data-r='outcome' /></td>" +
			"<td><input data-r='currency' value='KES' /></td>" +
			"<td class='is-num'><input data-r='amount' /></td>" +
			"<td><input data-r='date' /></td>" +
			"<td class='is-actions'><button type='button' class='kt-s600-link' data-s600-remove-row><span class='material-symbols-outlined'>delete</span></button></td>" +
			"</tr>"
		);
	}

	function syncMemberNames() {
		var sel = document.querySelector("[data-testid='kt-s600-member-select']");
		if (!sel) return;
		var name = sel.options[sel.selectedIndex] ? sel.options[sel.selectedIndex].text : "—";
		document.querySelectorAll("[data-member-name]").forEach(function (el) {
			el.textContent = name || "—";
		});
		var initial = document.querySelector("[data-testid='kt-s600-contract-initial']");
		var disclosure = document.querySelector("[data-testid='kt-s600-contract-disclosure']");
		if (initial && disclosure) {
			var has = !!sel.value;
			initial.hidden = has;
			disclosure.hidden = !has;
		}
	}

	function projectDrawerHtml(vals, kind) {
		vals = vals || {};
		var genOn = kind === "general" || vals.general;
		var specOn = kind === "specific" || vals.specific;
		return (
			'<div class="kt-s600-drawer-fields" data-testid="kt-s600-project-drawer-form">' +
			'<section class="kt-s600-drawer-section">' +
			'<h3 class="kt-s600-drawer-section__title">Contract</h3>' +
			'<div class="kt-s600-field"><label>Contract identification</label>' +
			'<input data-d="contract_id" placeholder="e.g. IFMIS Integration Hub" value="' +
			(vals.contract_id || "") +
			'"/></div>' +
			'<div class="kt-s600-field"><label>Brief description</label>' +
			'<textarea data-d="description" rows="3" placeholder="Short description of the works or services">' +
			(vals.description || "") +
			"</textarea></div>" +
			'<div class="kt-s600-field"><label>Procuring entity</label>' +
			'<input data-d="pe" placeholder="Client / procuring entity" value="' +
			(vals.pe || "") +
			'"/></div>' +
			'<div class="kt-s600-field"><label>Role in the contract</label>' +
			'<input data-d="role" placeholder="e.g. Prime supplier, Sub-contractor" value="' +
			(vals.role || "") +
			'"/></div>' +
			"</section>" +
			'<section class="kt-s600-drawer-section">' +
			'<h3 class="kt-s600-drawer-section__title">Contract period</h3>' +
			'<p class="kt-s600-drawer-section__hint">Qualifying years use the nine-month calendar-year rule.</p>' +
			'<div class="kt-s600-period-grid">' +
			'<div class="kt-s600-field"><label>Start month</label>' +
			'<input data-d="start_month" inputmode="numeric" maxlength="2" placeholder="MM" value="' +
			(vals.start_month || "1") +
			'"/></div>' +
			'<div class="kt-s600-field"><label>Start year</label>' +
			'<input data-d="start_year" inputmode="numeric" maxlength="4" placeholder="YYYY" value="' +
			(vals.start_year || "") +
			'"/></div>' +
			'<div class="kt-s600-field"><label>End month</label>' +
			'<input data-d="end_month" inputmode="numeric" maxlength="2" placeholder="MM" value="' +
			(vals.end_month || "12") +
			'"/></div>' +
			'<div class="kt-s600-field"><label>End year</label>' +
			'<input data-d="end_year" inputmode="numeric" maxlength="4" placeholder="YYYY" value="' +
			(vals.end_year || "") +
			'"/></div>' +
			"</div></section>" +
			'<section class="kt-s600-drawer-section">' +
			'<h3 class="kt-s600-drawer-section__title">Value &amp; similarity</h3>' +
			'<div class="kt-s600-period-grid kt-s600-period-grid--value">' +
			'<div class="kt-s600-field"><label>Contract amount</label>' +
			'<input data-d="amount" inputmode="decimal" placeholder="0.00" value="' +
			(vals.amount || "") +
			'"/></div>' +
			'<div class="kt-s600-field"><label>Currency</label>' +
			'<input data-d="currency" value="' +
			(vals.currency || "KES") +
			'"/></div></div>' +
			'<div class="kt-s600-field"><label>Similarity details</label>' +
			'<textarea data-d="similarity" rows="3" placeholder="Amount, size, complexity, methods / technology, key activities">' +
			(vals.similarity || "") +
			"</textarea></div>" +
			"</section>" +
			'<section class="kt-s600-drawer-section">' +
			'<h3 class="kt-s600-drawer-section__title">Apply to</h3>' +
			'<div class="kt-s600-scope-chips" role="group" aria-label="Experience scope">' +
			'<label class="kt-s600-scope-chip' +
			(genOn ? " is-on" : "") +
			'"><input type="checkbox" data-d="general" ' +
			(genOn ? "checked" : "") +
			"/><span>General experience</span></label>" +
			'<label class="kt-s600-scope-chip' +
			(specOn ? " is-on" : "") +
			'"><input type="checkbox" data-d="specific" ' +
			(specOn ? "checked" : "") +
			"/><span>Specific experience</span></label>" +
			"</div></section></div>"
		);
	}

	function appendProjectRow(kind, vals) {
		var tableKind = kind === "specific" ? "specific" : "general";
		var body = document.querySelector("[data-project-table='" + tableKind + "']");
		if (!body) return;
		var id = vals.project_id || "proj-" + Math.random().toString(16).slice(2, 10);
		vals.project_id = id;
		var tr = document.createElement("tr");
		tr.setAttribute("data-project-row", "");
		tr.setAttribute("data-project-id", id);
		tr.setAttribute("data-use-general", vals.general ? "1" : "0");
		tr.setAttribute("data-use-specific", vals.specific ? "1" : "0");
		var period =
			vals.start_year && vals.end_year
				? (vals.start_month || 1) + "/" + vals.start_year + " – " + (vals.end_month || 12) + "/" + vals.end_year
				: "—";
		var complete = projectRowComplete(vals, tableKind);
		var cid = escapeAttr(vals.contract_id || "");
		var desc = escapeAttr(vals.description || "");
		var pe = escapeAttr(vals.pe || "");
		var role = escapeAttr(vals.role || "");
		var sim = escapeAttr(vals.similarity || "");
		var hidden =
			'<td hidden>' +
			'<input data-p="contract_id" value="' +
			cid +
			'"/>' +
			'<input data-p="description" value="' +
			desc +
			'"/>' +
			'<input data-p="pe" value="' +
			pe +
			'"/>' +
			'<input data-p="start_year" value="' +
			escapeAttr(vals.start_year || "") +
			'"/>' +
			'<input data-p="start_month" value="' +
			escapeAttr(vals.start_month || "1") +
			'"/>' +
			'<input data-p="end_year" value="' +
			escapeAttr(vals.end_year || "") +
			'"/>' +
			'<input data-p="end_month" value="' +
			escapeAttr(vals.end_month || "12") +
			'"/>' +
			'<input data-p="role" value="' +
			role +
			'"/>' +
			'<input data-p="amount" value="' +
			escapeAttr(vals.amount || "") +
			'"/>' +
			'<input data-p="currency" value="' +
			escapeAttr(vals.currency || "KES") +
			'"/>' +
			'<input data-p="similarity" value="' +
			sim +
			'"/>' +
			'<input type="checkbox" data-p="general" ' +
			(vals.general ? "checked" : "") +
			"/>" +
			'<input type="checkbox" data-p="specific" ' +
			(tableKind === "specific" || vals.specific ? "checked" : "") +
			"/>" +
			"</td>";
		if (tableKind === "general") {
			tr.innerHTML =
				'<td class="is-strong">' +
				(vals.contract_id || "—") +
				"</td><td>" +
				period +
				'</td><td class="kt-s600-mono">—</td><td>' +
				(vals.pe || "—") +
				"</td><td>" +
				(vals.role || "—") +
				'</td><td class="is-center">' +
				statusPillHtml(complete) +
				"</td>" +
				'<td class="is-right is-actions"><button type="button" class="kt-s600-link" data-s600-edit-project><span class="material-symbols-outlined">edit</span></button>' +
				'<button type="button" class="kt-s600-link" data-s600-remove-project><span class="material-symbols-outlined">delete</span></button></td>' +
				hidden;
		} else {
			tr.innerHTML =
				'<td class="is-strong">' +
				(vals.contract_id || "—") +
				"</td><td>" +
				(vals.end_year ? (vals.end_month || 12) + "/" + vals.end_year : "—") +
				"</td><td>" +
				(vals.role || "—") +
				'</td><td class="kt-s600-mono">' +
				(vals.amount ? (vals.currency || "KES") + " " + vals.amount : "—") +
				'</td><td class="is-italic">' +
				(vals.similarity || "—") +
				'</td><td class="is-center">' +
				statusPillHtml(complete) +
				"</td>" +
				'<td class="is-right is-actions"><button type="button" class="kt-s600-link" data-s600-edit-project><span class="material-symbols-outlined">edit</span></button>' +
				'<button type="button" class="kt-s600-link" data-s600-remove-project><span class="material-symbols-outlined">delete</span></button></td>' +
				hidden;
		}
		body.appendChild(tr);
	}

	function confirmDrawer() {
		var d = drawerEls();
		var body = d.body;
		if (!body) {
			toast("Drawer is not ready. Close and try again.");
			return;
		}
		if (!drawerState.mode) {
			// Never silently dismiss — that was the "second click closes, nothing assigned" bug.
			if (d.drawer && !d.drawer.hidden) {
				toast("Save did not run (drawer state lost). Close and click Assign person again.");
				return;
			}
			closeDrawer();
			return;
		}
		if (drawerState.mode === "project") {
			var form = body.querySelector("[data-testid='kt-s600-project-drawer-form']") || body;
			var meta = drawerState.meta || {};
			var vals = {
				project_id: meta.project_id || "",
				contract_id: fieldVal(form, "contract_id"),
				description: fieldVal(form, "description"),
				pe: fieldVal(form, "pe"),
				start_year: fieldVal(form, "start_year"),
				start_month: fieldVal(form, "start_month") || "1",
				end_year: fieldVal(form, "end_year"),
				end_month: fieldVal(form, "end_month") || "12",
				role: fieldVal(form, "role"),
				amount: fieldVal(form, "amount"),
				currency: fieldVal(form, "currency") || "KES",
				similarity: fieldVal(form, "similarity"),
				general: !!(form.querySelector("[data-d='general']") || {}).checked,
				specific: !!(form.querySelector("[data-d='specific']") || {}).checked,
			};
			if (!vals.project_id) {
				vals.project_id = "proj-" + Math.random().toString(16).slice(2, 10);
			}
			removeProjectRows(vals.project_id);
			if (meta.row && meta.row.isConnected) {
				meta.row.remove();
			}
			if (vals.general) appendProjectRow("general", vals);
			if (vals.specific) appendProjectRow("specific", vals);
			if (!vals.general && !vals.specific) {
				vals.general = meta.kind !== "specific";
				vals.specific = meta.kind === "specific";
				appendProjectRow(meta.kind || "general", vals);
			}
			syncExperienceStatusesFromDom();
			closeDrawer();
			saveAndMaybeContinue(false);
			return;
		}
		if (drawerState.mode === "assign") {
			var chosen = body.querySelector("input[name='assign_person']:checked");
			var pos = getPendingPosition();
			if (!chosen) {
				toast("Select a person to assign, or add a new person.");
				return;
			}
			if (!assignPersonToPosition(pos, chosen.value, chosen.getAttribute("data-label") || chosen.value)) {
				return;
			}
			closeDrawer();
			setPendingPosition("", "", "");
			saveAndMaybeContinue(false);
			return;
		}
		if (drawerState.mode === "partner") {
			var itemId = drawerState.meta && drawerState.meta.itemId;
			var block = document.querySelector("[data-partner-item='" + itemId + "']");
			if (block) {
				var name = (body.querySelector("[data-d='org_name']") || {}).value || "";
				var role = (body.querySelector("[data-d='org_role']") || {}).value || "Manufacturer";
				block.querySelector("[data-field='organization_name']").value = name;
				block.querySelector("[data-field='org_role']").value = role;
				var disp = block.querySelector("[data-org-display]");
				if (disp) disp.textContent = name || "—";
				var other = block.querySelector("input[name='provider_" + itemId + "'][value='other']");
				if (other) other.checked = true;
				body.querySelectorAll("[data-d-crit]").forEach(function (row) {
					var cid = row.getAttribute("data-d-crit");
					var host = block.querySelector("[data-crit='" + cid + "']");
					if (!host) return;
					var complete = !!(row.querySelector("[data-d-complete]") || {}).checked;
					var evidence = (row.querySelector("[data-d-evidence]") || {}).value || "";
					var cb = host.querySelector("[data-crit-complete]");
					var ev = host.querySelector("[data-crit-evidence]");
					if (cb) cb.checked = complete;
					if (ev) ev.value = evidence;
				});
			}
			closeDrawer();
			return;
		}
		if (drawerState.mode === "new_person") {
			saveNewPersonAndAssign();
			return;
		}
		closeDrawer();
	}

	document.addEventListener("click", function (ev) {
		var t = ev.target;
		if (!t) return;
		if (t.closest("[data-s600-save='draft']")) {
			ev.preventDefault();
			saveAndMaybeContinue(false);
		}
		if (t.closest("[data-s600-save='continue']")) {
			ev.preventDefault();
			saveAndMaybeContinue(true);
		}
		if (t.closest("[data-s600-drawer-confirm]")) {
			ev.preventDefault();
			confirmDrawer();
		} else if (
			t.closest("[data-s600-drawer-close]") ||
			t.closest("[data-s600-drawer-cancel]") ||
			t.closest("[data-testid='kt-s600-drawer-backdrop']")
		) {
			ev.preventDefault();
			closeDrawer();
		}
		if (t.closest("[data-s600-add-record]")) {
			ev.preventDefault();
			var key = t.closest("[data-s600-add-record]").getAttribute("data-s600-add-record");
			var body = document.querySelector("[data-records-body='" + key + "']");
			if (body) body.insertAdjacentHTML("beforeend", recordRowHtml(key));
		}
		if (t.closest("[data-s600-remove-row]")) {
			ev.preventDefault();
			var row = t.closest("[data-record-row]");
			if (row) row.remove();
		}
		if (t.closest("[data-s600-add-resource]")) {
			ev.preventDefault();
			var rbody = document.querySelector("[data-testid='kt-s600-resources-body']");
			if (!rbody) return;
			var empty = rbody.querySelector("[data-res-empty]");
			if (empty) empty.remove();
			rbody.insertAdjacentHTML(
				"beforeend",
				"<tr data-res-row>" +
					"<td><input data-res='type' /></td>" +
					"<td><input data-res='provider' /></td>" +
					"<td><input data-res='amount' /></td>" +
					"<td><input data-res='currency' value='KES' /></td>" +
					"<td class='is-right'><input data-res='evidence' /></td>" +
					"</tr>"
			);
		}
		if (t.closest("[data-s600-add-project]")) {
			ev.preventDefault();
			var kind = t.closest("[data-s600-add-project]").getAttribute("data-s600-add-project") || "general";
			openDrawer(
				"Add project",
				kind === "specific" ? "Specific experience" : "General experience",
				projectDrawerHtml(null, kind),
				"project",
				{ kind: kind }
			);
		}
		if (t.closest("[data-s600-edit-project]")) {
			ev.preventDefault();
			var prow = t.closest("[data-project-row]");
			if (!prow) return;
			var vals = {
				project_id: prow.getAttribute("data-project-id"),
				contract_id: (prow.querySelector("[data-p='contract_id']") || {}).value || "",
				description: (prow.querySelector("[data-p='description']") || {}).value || "",
				pe: (prow.querySelector("[data-p='pe']") || {}).value || "",
				start_year: (prow.querySelector("[data-p='start_year']") || {}).value || "",
				start_month: (prow.querySelector("[data-p='start_month']") || {}).value || "1",
				end_year: (prow.querySelector("[data-p='end_year']") || {}).value || "",
				end_month: (prow.querySelector("[data-p='end_month']") || {}).value || "12",
				role: (prow.querySelector("[data-p='role']") || {}).value || "",
				amount: (prow.querySelector("[data-p='amount']") || {}).value || "",
				currency: (prow.querySelector("[data-p='currency']") || {}).value || "KES",
				similarity: (prow.querySelector("[data-p='similarity']") || {}).value || "",
				general: !!(prow.querySelector("[data-p='general']") || {}).checked,
				specific: !!(prow.querySelector("[data-p='specific']") || {}).checked,
			};
			openDrawer("Edit project", vals.contract_id || "", projectDrawerHtml(vals), "project", {
				kind: vals.specific && !vals.general ? "specific" : "general",
				row: prow,
				project_id: vals.project_id,
			});
		}
		if (t.closest("[data-s600-remove-project]")) {
			ev.preventDefault();
			var del = t.closest("[data-project-row]");
			if (!del) return;
			var delId = del.getAttribute("data-project-id");
			if (delId) removeProjectRows(delId);
			else del.remove();
		}
		if (t.closest("[data-s600-assign]")) {
			ev.preventDefault();
			var btn = t.closest("[data-s600-assign]");
			openAssignDrawer(btn.getAttribute("data-s600-assign"), {
				positionTitle: btn.getAttribute("data-position-title") || "",
				positionReq: btn.getAttribute("data-position-req") || "",
			});
		}
		if (t.closest("[data-s600-new-person]")) {
			ev.preventDefault();
			ev.stopPropagation();
			openNewPersonDrawer();
		}
		if (t.closest("[data-s600-edit-partner]")) {
			ev.preventDefault();
			var itemId = t.closest("[data-s600-edit-partner]").getAttribute("data-s600-edit-partner");
			var block = document.querySelector("[data-partner-item='" + itemId + "']");
			if (!block) return;
			var orgName = (block.querySelector("[data-field='organization_name']") || {}).value || "";
			var role = (block.querySelector("[data-field='org_role']") || {}).value || "Manufacturer";
			var critRows = "";
			block.querySelectorAll("[data-crit]").forEach(function (critEl) {
				var title = (critEl.querySelector("[data-crit-title]") || {}).textContent || critEl.getAttribute("data-crit");
				var complete = !!(critEl.querySelector("[data-crit-complete]") || {}).checked;
				var evidence = (critEl.querySelector("[data-crit-evidence]") || {}).value || "";
				critRows +=
					"<tr data-d-crit='" +
					critEl.getAttribute("data-crit") +
					"'><td>" +
					title +
					"</td><td><input data-d-evidence value='" +
					evidence +
					"'/></td><td><label><input type='checkbox' data-d-complete " +
					(complete ? "checked" : "") +
					"/> Complete</label></td></tr>";
			});
			openDrawer(
				"Partner Record" + (orgName ? ": " + orgName : ""),
				"Required information and evidence",
				'<div class="kt-s600-drawer-fields">' +
					'<div class="kt-s600-field"><label>Legal name</label><input data-d="org_name" value="' +
					orgName +
					'"/></div>' +
					'<div class="kt-s600-field"><label>Role</label><select data-d="org_role">' +
					"<option" +
					(role === "Manufacturer" ? " selected" : "") +
					">Manufacturer</option>" +
					"<option" +
					(role === "Vendor" ? " selected" : "") +
					">Vendor</option>" +
					"<option" +
					(role === "Subcontractor" ? " selected" : "") +
					">Subcontractor</option></select></div>" +
					'<table class="kt-s600-data-table"><thead><tr><th>Requirement</th><th>Response or evidence</th><th>Status</th></tr></thead><tbody>' +
					(critRows || "<tr><td colspan='3'>No criteria configured</td></tr>") +
					"</tbody></table></div>",
				"partner",
				{ itemId: itemId }
			);
			var conf = document.querySelector("[data-testid='kt-s600-drawer-confirm']");
			if (conf) conf.textContent = "Save Partner Details";
		}
	});

	document.addEventListener("change", function (ev) {
		var t = ev.target;
		if (!t) return;
		if (t.matches(".kt-s600-scope-chip input")) {
			var chip = t.closest(".kt-s600-scope-chip");
			if (chip) chip.classList.toggle("is-on", !!t.checked);
		}
		if (t.matches("[data-testid='kt-s600-member-select']")) {
			syncMemberNames();
		}
		if (t.matches("input[type=radio]")) {
			var name = t.getAttribute("name") || "";
			["non_performing", "pending_litigation", "litigation_history"].forEach(function (key) {
				if (name !== key) return;
				var yes = document.querySelector("[data-yes-panel='" + key + "']");
				var no = document.querySelector("[data-no-panel='" + key + "']");
				if (yes) yes.hidden = t.value !== "yes";
				if (no) no.hidden = t.value !== "no";
			});
		}
		if (t.matches("[data-to-amount]") || t.matches("[data-to='amount']")) {
			var r = root();
			if (r) recomputeTurnoverAvg(r);
		}
	});

	document.addEventListener("DOMContentLoaded", function () {
		syncMemberNames();
		var r = root();
		if (r && r.getAttribute("data-category-key") === "financial_capability") {
			recomputeTurnoverAvg(r);
		}
	});
})();
