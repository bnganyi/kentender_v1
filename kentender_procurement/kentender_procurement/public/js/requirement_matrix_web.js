/**
 * A4 Requirement Matrix — groups, list, 560px drawer, merge-save.
 */
(function () {
	var METHOD_MATRIX = "kentender_procurement.tender_configurations.get_requirement_matrix";
	var METHOD_DRAWER = "kentender_procurement.tender_configurations.get_requirement_drawer";
	var METHOD_SAVE = "kentender_procurement.tender_configurations.save_requirement_response";

	var state = {
		publicationRef: "",
		sectionKey: "",
		group: "",
		q: "",
		status: "",
		page: 1,
		pageSize: 10,
		matrix: null,
		drawer: null,
		selectedRequirementId: "",
		sealed: false,
		/** field_key → list of mock file dicts (draft until save) */
		draftFiles: {},
	};

	function normalizeFileList(val) {
		if (!val) return [];
		if (Array.isArray(val)) {
			return val.filter(function (f) {
				return f && (f.file_name || f.mock || f.url);
			});
		}
		if (typeof val === "object" && (val.file_name || val.mock || val.url)) {
			return [val];
		}
		return [];
	}

	function formatBytes(n) {
		var size = Number(n) || 0;
		if (size < 1024) return size + " B";
		if (size < 1024 * 1024) return Math.round(size / 1024) + " KB";
		return (size / (1024 * 1024)).toFixed(1) + " MB";
	}

	function renderFileListHtml(files) {
		if (!files || !files.length) {
			return (
				'<p class="kt-a4-file-empty" data-testid="kt-a4-file-empty">No files attached yet.</p>'
			);
		}
		return (
			'<ul class="kt-a4-file-list" data-testid="kt-a4-file-list">' +
			files
				.map(function (f, idx) {
					var name = f.file_name || "Attachment";
					var meta = formatBytes(f.byte_size);
					return (
						'<li class="kt-a4-file-chip" data-testid="kt-a4-file-chip" data-file-index="' +
						idx +
						'">' +
						'<span class="material-symbols-outlined kt-a4-file-chip-icon" aria-hidden="true">description</span>' +
						'<span class="kt-a4-file-chip-body">' +
						'<span class="kt-a4-file-chip-name" data-testid="kt-a4-file-name">' +
						escapeHtml(name) +
						"</span>" +
						'<span class="kt-a4-file-chip-meta">' +
						escapeHtml(meta) +
						"</span></span>" +
						'<button type="button" class="kt-a4-file-remove" data-testid="kt-a4-file-remove" ' +
						'data-file-index="' +
						idx +
						'" aria-label="Remove ' +
						escapeHtml(name) +
						'">' +
						'<span class="material-symbols-outlined" aria-hidden="true">close</span>' +
						"</button></li>"
					);
				})
				.join("") +
			"</ul>"
		);
	}

	function refreshFileField(fieldKey) {
		var host = document.querySelector(
			'.kt-a4-file-mock[data-field-key="' + fieldKey + '"]'
		);
		if (!host) return;
		var listHost = host.querySelector("[data-kt-a4-file-list-host]");
		if (listHost) {
			listHost.innerHTML = renderFileListHtml(state.draftFiles[fieldKey] || []);
		}
		host.classList.toggle("has-files", (state.draftFiles[fieldKey] || []).length > 0);
	}

	function root() {
		return document.querySelector('[data-testid="kt-a4-matrix-root"]');
	}

	function storageKey() {
		return "kt-a4-filters:" + state.publicationRef + ":" + state.sectionKey;
	}

	function persistFilters() {
		try {
			sessionStorage.setItem(
				storageKey(),
				JSON.stringify({
					group: state.group,
					q: state.q,
					status: state.status,
					page: state.page,
					requirementId: state.selectedRequirementId || "",
				})
			);
		} catch (e) {
			/* ignore */
		}
	}

	function restoreFilters() {
		try {
			var raw = sessionStorage.getItem(storageKey());
			if (!raw) return null;
			return JSON.parse(raw);
		} catch (e) {
			return null;
		}
	}

	function call(method, args) {
		return new Promise(function (resolve, reject) {
			if (typeof frappe === "undefined" || !frappe.call) {
				reject(new Error("frappe.call unavailable"));
				return;
			}
			frappe.call({
				method: method,
				args: args,
				callback: function (r) {
					resolve(r.message);
				},
				error: function (err) {
					reject(err);
				},
			});
		});
	}

	function statusClass(status) {
		return "kt-a4-status--" + String(status || "").toLowerCase().replace(/\s+/g, "-");
	}

	function escapeHtml(s) {
		return String(s == null ? "" : s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function renderGroups(groups, selected) {
		var host = document.querySelector('[data-testid="kt-a4-group-list"]');
		if (!host) return;
		host.innerHTML = (groups || [])
			.map(function (g) {
				var active = g.group_key === selected ? " is-active" : "";
				var statusBit =
					g.status && g.status !== "Not Started"
						? '<span class="kt-a4-group-status ' +
							statusClass(g.status) +
							'" data-testid="kt-a4-group-status">' +
							escapeHtml(g.status) +
							"</span>"
						: "";
				return (
					'<button type="button" class="kt-a4-group-btn' +
					active +
					'" data-testid="kt-a4-group" data-group-key="' +
					escapeHtml(g.group_key) +
					'" data-group-status="' +
					escapeHtml(g.status) +
					'">' +
					'<span class="kt-a4-group-title">' +
					escapeHtml(g.title) +
					"</span>" +
					'<span class="kt-a4-group-meta"><span data-testid="kt-a4-group-progress">' +
					escapeHtml(g.progress_label) +
					"</span>" +
					statusBit +
					"</span></button>"
				);
			})
			.join("");
	}

	function renderRows(rows) {
		var body = document.querySelector('[data-testid="kt-a4-requirements-body"]');
		if (!body) return;
		if (!rows || !rows.length) {
			body.innerHTML =
				'<tr><td colspan="6" class="kt-a4-empty" data-testid="kt-a4-empty">No requirements match the current filters.</td></tr>';
			return;
		}
		body.innerHTML = rows
			.map(function (r) {
				var selected =
					r.requirement_id === state.selectedRequirementId ? " is-selected" : "";
				var actionMod =
					r.status === "Not Started"
						? " kt-a4-row-action--start"
						: r.status === "Needs Attention" || r.status === "In Progress"
							? " kt-a4-row-action--continue"
							: " kt-a4-row-action--review";
				var titleClass =
					"kt-a4-row-title" + (r.has_short_title ? " kt-a4-row-title--short" : "");
				var detail =
					r.subtitle
						? '<p class="kt-a4-row-detail" data-testid="kt-a4-row-detail">' +
							escapeHtml(r.subtitle) +
							"</p>"
						: "";
				return (
					'<tr data-testid="kt-a4-requirement-row" data-requirement-id="' +
					escapeHtml(r.requirement_id) +
					'" data-status="' +
					escapeHtml(r.status) +
					'" class="' +
					selected.trim() +
					'">' +
					'<td class="kt-a4-mono">' +
					escapeHtml(r.requirement_id) +
					"</td>" +
					"<td><strong class=\"" +
					titleClass +
					'" data-testid="kt-a4-row-title">' +
					escapeHtml(r.title) +
					"</strong>" +
					detail +
					"</td>" +
					'<td><span class="kt-a4-pill">' +
					escapeHtml(r.mandatory_label) +
					"</span></td>" +
					'<td class="kt-a4-summary">' +
					escapeHtml(r.response_summary) +
					"</td>" +
					"<td><span class=\"kt-a4-status " +
					statusClass(r.status) +
					'" data-testid="kt-a4-row-status"><span class="kt-a4-status-dot" aria-hidden="true"></span>' +
					escapeHtml(r.status) +
					"</span></td>" +
					'<td class="kt-a4-right"><button type="button" class="kt-a4-row-action' +
					actionMod +
					'" data-testid="kt-a4-row-action" data-requirement-id="' +
					escapeHtml(r.requirement_id) +
					'">' +
					escapeHtml(r.action_label) +
					"</button></td></tr>"
				);
			})
			.join("");
	}

	function applyMatrix(matrix) {
		state.matrix = matrix;
		state.group = matrix.selected_group || state.group;
		state.page = (matrix.pagination && matrix.pagination.page) || state.page;
		var progress = document.querySelector('[data-testid="kt-a4-progress-label"]');
		if (progress) progress.textContent = matrix.progress_label || "";
		var bar = document.querySelector('[data-testid="kt-a4-progress-bar"]');
		if (bar) bar.style.width = (matrix.progress_percent || 0) + "%";
		var current = document.querySelector('[data-testid="kt-a4-current-group"]');
		if (current) {
			current.innerHTML =
				"Current View: <strong>" + escapeHtml(matrix.selected_group || "—") + "</strong>";
		}
		var last = document.querySelector('[data-testid="kt-a4-last-saved"]');
		if (last) last.textContent = matrix.last_saved_display || "—";
		var pageLabel = document.querySelector('[data-testid="kt-a4-page-label"]');
		var p = matrix.pagination || {};
		if (pageLabel) {
			pageLabel.textContent = p.total
				? "Showing " + p.from + "–" + p.to + " of " + p.total
				: "0 requirements";
		}
		var prev = document.querySelector('[data-testid="kt-a4-page-prev"]');
		var next = document.querySelector('[data-testid="kt-a4-page-next"]');
		if (prev) prev.disabled = !p.page || p.page <= 1;
		if (next) next.disabled = !p.page || p.page >= (p.total_pages || 1);
		renderGroups(matrix.groups, matrix.selected_group);
		renderRows(matrix.rows);
		persistFilters();
	}

	function fieldControlHtml(field, value) {
		var key = field.field_key || "";
		var label = field.label || key;
		var req = field.required ? ' <span class="kt-a4-req">*</span>' : "";
		if (field.unsupported) {
			return (
				'<div class="kt-a4-field"><div class="kt-a4-unsupported" data-testid="kt-a4-unsupported">' +
				escapeHtml(field.unsupported_message || "Unsupported response type") +
				"</div></div>"
			);
		}
		var control = field.control || "text";
		var html = '<div class="kt-a4-field" data-field-key="' + escapeHtml(key) + '">';
		html += "<label>" + escapeHtml(label) + req + "</label>";
		if (field.help_text) {
			html +=
				'<p class="kt-a4-field-help" data-testid="kt-a4-field-help-' +
				escapeHtml(key) +
				'">' +
				escapeHtml(field.help_text) +
				"</p>";
		}
		var fieldError = field.error
			? '<p class="kt-a4-field-error" data-testid="kt-a4-field-error-' +
				escapeHtml(key) +
				'"><span class="material-symbols-outlined" aria-hidden="true">error</span>' +
				escapeHtml(field.error) +
				"</p>"
			: "";
		if (control === "yes_no") {
			var yesActive = value === "Yes" ? " is-active" : "";
			var noActive = value === "No" ? " is-active" : "";
			html +=
				'<div class="kt-a4-yesno" data-testid="kt-a4-yesno">' +
				'<button type="button" data-value="Yes" class="' +
				yesActive.trim() +
				'">Yes</button>' +
				'<button type="button" data-value="No" class="' +
				noActive.trim() +
				'">No</button>' +
				'<input type="hidden" name="' +
				escapeHtml(key) +
				'" value="' +
				escapeHtml(value || "") +
				'" /></div>' +
				fieldError;
		} else if (control === "textarea") {
			html +=
				'<textarea name="' +
				escapeHtml(key) +
				'" data-testid="kt-a4-field-' +
				escapeHtml(key) +
				'">' +
				escapeHtml(value || "") +
				"</textarea>" +
				fieldError;
		} else if (control === "file") {
			var files = normalizeFileList(value);
			state.draftFiles[key] = files.slice();
			html +=
				'<div class="kt-a4-file-mock' +
				(files.length ? " has-files" : "") +
				'" data-testid="kt-a4-file" data-field-key="' +
				escapeHtml(key) +
				'">' +
				'<div class="kt-a4-file-drop" data-testid="kt-a4-file-drop">' +
				'<span class="material-symbols-outlined" aria-hidden="true">upload_file</span>' +
				'<span class="kt-a4-file-drop-label">Click to upload or drag and drop</span>' +
				'<span class="kt-a4-file-hint">PDF, DOCX or JPG (Max 10MB). You can add multiple files.</span>' +
				'<input type="file" multiple accept=".pdf,.doc,.docx,.jpg,.jpeg,.png,application/pdf,image/*" data-field-key="' +
				escapeHtml(key) +
				'" data-testid="kt-a4-file-input" />' +
				"</div>" +
				'<div data-kt-a4-file-list-host>' +
				renderFileListHtml(files) +
				"</div></div>" +
				fieldError;
		} else {
			html +=
				'<input type="text" name="' +
				escapeHtml(key) +
				'" value="' +
				escapeHtml(value || "") +
				'" data-testid="kt-a4-field-' +
				escapeHtml(key) +
				'" />' +
				fieldError;
		}
		html += "</div>";
		return html;
	}

	function openDrawerUi(drawer) {
		state.drawer = drawer;
		state.selectedRequirementId = drawer.requirement_id || "";
		state.draftFiles = {};
		var panel = document.querySelector('[data-testid="kt-a4-drawer"]');
		if (!panel) return;
		panel.hidden = false;
		panel.setAttribute("aria-hidden", "false");
		var title = panel.querySelector('[data-testid="kt-a4-drawer-title"]');
		var pos = panel.querySelector('[data-testid="kt-a4-drawer-position"]');
		var statusRow = panel.querySelector('[data-testid="kt-a4-drawer-status-row"]');
		var statusEl = panel.querySelector('[data-testid="kt-a4-drawer-status"]');
		var attentionEl = panel.querySelector('[data-testid="kt-a4-drawer-attention"]');
		var body = panel.querySelector('[data-testid="kt-a4-drawer-body"]');
		var headerLabel = drawer.header_title || drawer.title || drawer.requirement_id || "";
		if (title) title.textContent = headerLabel;
		if (pos) pos.textContent = drawer.position_label || "";
		if (statusRow && statusEl) {
			if (drawer.status) {
				statusRow.hidden = false;
				statusEl.className = "kt-a4-drawer-status " + statusClass(drawer.status);
				statusEl.innerHTML =
					'<span class="kt-a4-status-dot" aria-hidden="true"></span>' +
					escapeHtml(drawer.status);
				if (attentionEl) {
					if (drawer.show_attention) {
						attentionEl.hidden = false;
						attentionEl.className =
							"kt-a4-drawer-attention " + statusClass("Needs Attention");
						attentionEl.innerHTML =
							'<span class="kt-a4-status-dot" aria-hidden="true"></span>Needs Attention';
					} else {
						attentionEl.hidden = true;
						attentionEl.textContent = "";
					}
				}
			} else {
				statusRow.hidden = true;
			}
		}
		var resp = drawer.response || {};
		var parts = [];
		var description = drawer.description || "";
		if (description) {
			parts.push(
				'<div class="kt-a4-description" data-testid="kt-a4-drawer-description">' +
					"<h3>Description</h3>" +
					"<p>" +
					escapeHtml(description) +
					"</p></div>"
			);
		}
		(drawer.fields || []).forEach(function (f) {
			var key = f.field_key || "";
			parts.push(fieldControlHtml(f, resp[key]));
		});
		if (body) body.innerHTML = parts.join("");
		var prevBtn = panel.querySelector('[data-testid="kt-a4-drawer-prev"]');
		if (prevBtn) prevBtn.disabled = !drawer.prev_requirement_id;
		document.querySelectorAll('[data-testid="kt-a4-requirement-row"]').forEach(function (tr) {
			tr.classList.toggle(
				"is-selected",
				tr.getAttribute("data-requirement-id") === state.selectedRequirementId
			);
		});
		persistFilters();
	}

	function closeDrawer() {
		var panel = document.querySelector('[data-testid="kt-a4-drawer"]');
		if (!panel) return;
		panel.hidden = true;
		panel.setAttribute("aria-hidden", "true");
		state.selectedRequirementId = "";
		persistFilters();
	}

	function collectPayload() {
		var body = document.querySelector('[data-testid="kt-a4-drawer-body"]');
		if (!body) return {};
		var payload = {};
		body.querySelectorAll("[name]").forEach(function (el) {
			payload[el.getAttribute("name")] = el.value;
		});
		body.querySelectorAll(".kt-a4-file-mock[data-field-key]").forEach(function (host) {
			var key = host.getAttribute("data-field-key");
			payload[key] = (state.draftFiles[key] || []).slice();
		});
		return payload;
	}

	function addFilesFromInput(input) {
		var key = input.getAttribute("data-field-key") || "";
		if (!key) return;
		var list = (state.draftFiles[key] || []).slice();
		var incoming = input.files || [];
		for (var i = 0; i < incoming.length; i++) {
			var file = incoming[i];
			var dup = list.some(function (f) {
				return (
					f.file_name === file.name &&
					Number(f.byte_size || 0) === Number(file.size || 0)
				);
			});
			if (dup) continue;
			list.push({
				file_name: file.name,
				content_type: file.type || "application/octet-stream",
				byte_size: file.size || 0,
				mock: 1,
				uploaded_at: new Date().toISOString(),
			});
		}
		state.draftFiles[key] = list;
		input.value = "";
		refreshFileField(key);
	}

	function removeDraftFile(fieldKey, index) {
		var list = (state.draftFiles[fieldKey] || []).slice();
		if (index < 0 || index >= list.length) return;
		list.splice(index, 1);
		state.draftFiles[fieldKey] = list;
		refreshFileField(fieldKey);
	}

	function reloadMatrix() {
		return call(METHOD_MATRIX, {
			published_tender_ref: state.publicationRef,
			section_key: state.sectionKey,
			group: state.group,
			q: state.q,
			status: state.status,
			page: state.page,
			page_size: state.pageSize,
		}).then(applyMatrix);
	}

	function openRequirement(requirementId) {
		return call(METHOD_DRAWER, {
			published_tender_ref: state.publicationRef,
			section_key: state.sectionKey,
			requirement_id: requirementId,
		}).then(openDrawerUi);
	}

	function saveResponse(thenNext) {
		if (state.sealed || !state.selectedRequirementId) return Promise.resolve();
		var payload = collectPayload();
		return call(METHOD_SAVE, {
			published_tender_ref: state.publicationRef,
			section_key: state.sectionKey,
			requirement_id: state.selectedRequirementId,
			payload: payload,
		}).then(function (out) {
			if (out && out.matrix) applyMatrix(out.matrix);
			if (thenNext && out && out.drawer && out.drawer.next_requirement_id) {
				return openRequirement(out.drawer.next_requirement_id);
			}
			if (out && out.drawer) openDrawerUi(out.drawer);
			return out;
		});
	}

	function bind() {
		var el = root();
		if (!el || el.dataset.bound === "1") return;
		el.dataset.bound = "1";

		state.publicationRef = el.getAttribute("data-publication-ref") || "";
		state.sectionKey = el.getAttribute("data-section-key") || "";
		state.group = el.getAttribute("data-selected-group") || "";
		state.sealed = el.getAttribute("data-bid-sealed") === "1";

		var boot = document.getElementById("kt-a4-bootstrap");
		if (boot) {
			try {
				state.matrix = JSON.parse(boot.textContent || "{}");
				state.page = (state.matrix.pagination && state.matrix.pagination.page) || 1;
				state.q = (state.matrix.filters && state.matrix.filters.q) || "";
				state.status = (state.matrix.filters && state.matrix.filters.status) || "";
			} catch (e) {
				/* ignore */
			}
		}

		var saved = restoreFilters();
		if (saved) {
			if (saved.group) state.group = saved.group;
			if (saved.q != null) state.q = saved.q;
			if (saved.status != null) state.status = saved.status;
			if (saved.page) state.page = saved.page;
			var search = el.querySelector('[data-testid="kt-a4-search"]');
			var statusSel = el.querySelector('[data-testid="kt-a4-status-filter"]');
			if (search) search.value = state.q || "";
			if (statusSel) statusSel.value = state.status || "";
			if (
				saved.group !== (state.matrix && state.matrix.selected_group) ||
				saved.q ||
				saved.status ||
				(saved.page && saved.page !== 1)
			) {
				reloadMatrix();
			}
			// Do not auto-open the drawer from session — only Start / Continue / Review.
		}

		el.addEventListener("click", function (e) {
			var groupBtn = e.target.closest('[data-testid="kt-a4-group"]');
			if (groupBtn) {
				state.group = groupBtn.getAttribute("data-group-key") || "";
				state.page = 1;
				reloadMatrix();
				return;
			}
			var action = e.target.closest('[data-testid="kt-a4-row-action"]');
			if (action) {
				openRequirement(action.getAttribute("data-requirement-id") || "");
				return;
			}
			// Rows are not clickable — drawer opens only via Start / Continue / Review (and drawer nav).
			if (e.target.closest('[data-testid="kt-a4-drawer-close"]')) {
				closeDrawer();
				return;
			}
			if (e.target.closest('[data-testid="kt-a4-drawer-prev"]')) {
				var prevId = state.drawer && state.drawer.prev_requirement_id;
				if (prevId) openRequirement(prevId);
				return;
			}
			if (e.target.closest('[data-testid="kt-a4-drawer-save"]')) {
				saveResponse(false);
				return;
			}
			if (e.target.closest('[data-testid="kt-a4-drawer-save-next"]')) {
				saveResponse(true);
				return;
			}
			if (e.target.closest('[data-testid="kt-a4-save-section"]')) {
				reloadMatrix();
				return;
			}
			if (e.target.closest('[data-testid="kt-a4-page-prev"]')) {
				if (state.page > 1) {
					state.page -= 1;
					reloadMatrix();
				}
				return;
			}
			if (e.target.closest('[data-testid="kt-a4-page-next"]')) {
				state.page += 1;
				reloadMatrix();
				return;
			}
			var removeBtn = e.target.closest('[data-testid="kt-a4-file-remove"]');
			if (removeBtn) {
				e.preventDefault();
				e.stopPropagation();
				var mock = removeBtn.closest(".kt-a4-file-mock");
				var fk = mock && mock.getAttribute("data-field-key");
				var idx = parseInt(removeBtn.getAttribute("data-file-index") || "-1", 10);
				if (fk) removeDraftFile(fk, idx);
				return;
			}
			var yesNo = e.target.closest(".kt-a4-yesno button");
			if (yesNo) {
				var wrap = yesNo.closest(".kt-a4-yesno");
				wrap.querySelectorAll("button").forEach(function (b) {
					b.classList.remove("is-active");
				});
				yesNo.classList.add("is-active");
				var hidden = wrap.querySelector('input[type="hidden"]');
				if (hidden) hidden.value = yesNo.getAttribute("data-value") || "";
			}
		});

		var searchInput = el.querySelector('[data-testid="kt-a4-search"]');
		var statusFilter = el.querySelector('[data-testid="kt-a4-status-filter"]');
		var searchTimer = null;
		if (searchInput) {
			searchInput.addEventListener("input", function () {
				clearTimeout(searchTimer);
				searchTimer = setTimeout(function () {
					state.q = searchInput.value || "";
					state.page = 1;
					reloadMatrix();
				}, 250);
			});
		}
		if (statusFilter) {
			statusFilter.addEventListener("change", function () {
				state.status = statusFilter.value || "";
				state.page = 1;
				reloadMatrix();
			});
		}

		el.addEventListener("change", function (e) {
			var input = e.target.closest('.kt-a4-file-mock input[type="file"]');
			if (!input) return;
			addFilesFromInput(input);
		});
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", bind);
	} else {
		bind();
	}
})();
