/**
 * Host-agnostic schema-driven electronic bidder workspace renderer.
 * Desk PoC and future /supplier mounts call mount() with the same API adapter.
 */
(function (root) {
	"use strict";

	var NS = (root.kentender_procurement = root.kentender_procurement || {});
	var EB = (NS.electronic_bid = NS.electronic_bid || {});

	function esc(v) {
		var d = document.createElement("div");
		d.textContent = v == null ? "" : String(v);
		return d.innerHTML;
	}

	function ensureStyles() {
		if (document.getElementById("kt-eb-renderer-css")) return;
		var style = document.createElement("style");
		style.id = "kt-eb-renderer-css";
		style.textContent =
			".kt-eb-root{display:flex;gap:16px;min-height:480px;font-family:inherit}" +
			".kt-eb-nav{width:240px;flex:0 0 240px;border-right:1px solid #e5e7eb;padding:8px 0}" +
			".kt-eb-nav button{display:block;width:100%;text-align:left;border:0;background:transparent;padding:8px 12px;cursor:pointer;font-size:13px}" +
			".kt-eb-nav button.is-active{background:#eff6ff;color:#1d4ed8;font-weight:600}" +
			".kt-eb-nav button.has-data{border-left:3px solid #22c55e}" +
			".kt-eb-main{flex:1;min-width:0;padding:8px 16px}" +
			".kt-eb-toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;align-items:center}" +
			".kt-eb-field{margin:0 0 12px}" +
			".kt-eb-field label{display:block;font-size:12px;font-weight:600;margin-bottom:4px}" +
			".kt-eb-field input,.kt-eb-field textarea,.kt-eb-field select{width:100%;max-width:640px}" +
			".kt-eb-matrix-meta{font-size:12px;color:#6b7280;margin-bottom:8px}" +
			".kt-eb-row{border:1px solid #e5e7eb;border-radius:6px;padding:10px;margin-bottom:8px}" +
			".kt-eb-errors{background:#fef2f2;border:1px solid #fecaca;color:#991b1b;padding:10px;border-radius:6px;margin-bottom:12px}" +
			".kt-eb-receipt{background:#ecfdf5;border:1px solid #a7f3d0;padding:12px;border-radius:6px;margin-bottom:12px}" +
			".kt-eb-badge{display:inline-block;padding:2px 8px;border-radius:999px;background:#e5e7eb;font-size:11px}";
		document.head.appendChild(style);
	}

	function deepClone(obj) {
		return JSON.parse(JSON.stringify(obj || {}));
	}

	function sectionByKey(schema, key) {
		var sections = (schema && schema.sections) || [];
		for (var i = 0; i < sections.length; i++) {
			if (sections[i].key === key) return sections[i];
		}
		return null;
	}

	function renderField(field, value, readOnly, onChange) {
		var type = (field.type || "text").toLowerCase();
		var key = field.field_key;
		var wrap = document.createElement("div");
		wrap.className = "kt-eb-field";
		wrap.setAttribute("data-field-key", key);
		var lab = document.createElement("label");
		lab.textContent = field.label || key;
		wrap.appendChild(lab);
		var input;
		if (type === "checkbox") {
			input = document.createElement("input");
			input.type = "checkbox";
			input.checked = !!value;
			input.disabled = !!readOnly;
			input.addEventListener("change", function () {
				onChange(key, !!input.checked);
			});
		} else if (type === "narrative" || type === "file_or_narrative") {
			input = document.createElement("textarea");
			input.rows = 3;
			input.value = value == null ? "" : String(value);
			input.disabled = !!readOnly;
			input.addEventListener("input", function () {
				onChange(key, input.value);
			});
		} else if (type === "file") {
			input = document.createElement("button");
			input.type = "button";
			input.className = "btn btn-xs btn-default";
			input.textContent = value && value.file_name ? "Mock uploaded: " + value.file_name : "Attach mock evidence";
			input.disabled = !!readOnly;
			input.addEventListener("click", function () {
				onChange(key, {
					file_name: key + "-evidence.pdf",
					content_type: "application/pdf",
					byte_size: 1024,
					mock: true,
					uploaded_at: new Date().toISOString(),
				});
				input.textContent = "Mock uploaded: " + key + "-evidence.pdf";
			});
		} else if (type === "submit") {
			input = document.createElement("span");
			input.className = "kt-eb-badge";
			input.textContent = "Use Submit & Seal in the toolbar";
		} else {
			input = document.createElement("input");
			input.type = type === "money" ? "number" : "text";
			if (type === "money") input.step = "0.01";
			input.value = value == null ? "" : String(value);
			input.disabled = !!readOnly;
			input.addEventListener("input", function () {
				onChange(key, input.value);
			});
		}
		wrap.appendChild(input);
		return wrap;
	}

	function renderRequirements(section, responses, readOnly, onRowChange) {
		var host = document.createElement("div");
		var reqs = section.requirements || [];
		var meta = document.createElement("div");
		meta.className = "kt-eb-matrix-meta";
		meta.setAttribute("data-testid", "kt-eb-section-count");
		meta.textContent = reqs.length + " items in this section";
		host.appendChild(meta);
		var template = section.response_fields_per_requirement || [
			{ field_key: "compliant_yes_no", label: "Compliant (Yes/No)", type: "text" },
			{ field_key: "compliance_statement", label: "Compliance statement", type: "narrative" },
			{ field_key: "upload", label: "Upload / evidence", type: "file" },
			{ field_key: "structured_response", label: "Response", type: "narrative" },
			{ field_key: "e_declaration", label: "E-declaration", type: "checkbox" },
		];
		// Progressive: render first 25 + remaining as compact rows with required fields only for performance
		var limit = Math.min(reqs.length, 40);
		for (var i = 0; i < reqs.length; i++) {
			var req = reqs[i];
			var rid = req.requirement_id || req.id;
			var rowResp = (responses && responses[rid]) || {};
			var row = document.createElement("div");
			row.className = "kt-eb-row";
			row.setAttribute("data-requirement-id", rid);
			var title = document.createElement("strong");
			title.textContent = rid + " — " + (req.requirement_title || req.criterion || "");
			row.appendChild(title);
			var fields = section.key === "technical_compliance_matrix" ? template : template;
			if (i >= limit && section.key === "technical_compliance_matrix") {
				// Compact: only yes/no + statement for remaining rows (still editable)
				fields = [
					{ field_key: "compliant_yes_no", label: "Compliant (Yes/No)", type: "text" },
					{ field_key: "compliance_statement", label: "Compliance statement", type: "narrative" },
				];
			}
			fields.forEach(function (field) {
				row.appendChild(
					renderField(field, rowResp[field.field_key], readOnly, function (fk, val) {
						onRowChange(rid, fk, val);
					})
				);
			});
			host.appendChild(row);
		}
		return host;
	}

	function renderPrice(section, responses, readOnly, onChange) {
		var host = document.createElement("div");
		var lines = section.price_lines || [];
		var meta = document.createElement("div");
		meta.className = "kt-eb-matrix-meta";
		meta.setAttribute("data-testid", "kt-eb-price-count");
		meta.textContent = lines.length + " price lines";
		host.appendChild(meta);
		var lineResp = (responses && responses.lines) || responses || {};
		lines.forEach(function (line) {
			var lid = line.line_id;
			var row = document.createElement("div");
			row.className = "kt-eb-row";
			row.setAttribute("data-price-line-id", lid);
			var title = document.createElement("strong");
			title.textContent = lid + " — " + (line.module_or_item || "");
			row.appendChild(title);
			var vals = lineResp[lid] || {};
			if (line.unit_cost_required) {
				row.appendChild(
					renderField(
						{ field_key: "unit_cost", label: "Unit cost", type: "money" },
						vals.unit_cost,
						readOnly,
						function (_k, v) {
							onChange(["lines", lid, "unit_cost"], v);
						}
					)
				);
			}
			row.appendChild(
				renderField(
					{ field_key: "total_cost", label: "Total cost", type: "money" },
					vals.total_cost,
					readOnly,
					function (_k, v) {
						onChange(["lines", lid, "total_cost"], v);
					}
				)
			);
			host.appendChild(row);
		});
		var summary = (responses && responses.summary) || {};
		(section.summary_fields || []).forEach(function (field) {
			host.appendChild(
				renderField(field, summary[field.field_key], readOnly, function (fk, v) {
					onChange(["summary", fk], v);
				})
			);
		});
		return host;
	}

	function setPath(obj, path, value) {
		var cur = obj;
		for (var i = 0; i < path.length - 1; i++) {
			var p = path[i];
			if (!cur[p] || typeof cur[p] !== "object") cur[p] = {};
			cur = cur[p];
		}
		cur[path[path.length - 1]] = value;
	}

	/**
	 * @param {HTMLElement} hostEl
	 * @param {{ schema, responses, readOnly, bidId, receipt, errors, api }} opts
	 * api: { saveSection(sectionKey, payload), validate(), submit(), fillForTests() }
	 */
	function mount(hostEl, opts) {
		ensureStyles();
		opts = opts || {};
		var schema = opts.schema || { sections: [] };
		var state = {
			activeKey: ((schema.sections || [])[0] || {}).key || "",
			responses: deepClone(opts.responses || {}),
			readOnly: !!opts.readOnly,
			bidId: opts.bidId || null,
			receipt: opts.receipt || null,
			errors: opts.errors || [],
			busy: false,
		};
		var api = opts.api || {};

		function paint() {
			hostEl.innerHTML = "";
			var root = document.createElement("div");
			root.className = "kt-eb-root";
			root.setAttribute("data-testid", "kt-eb-workspace");

			var nav = document.createElement("nav");
			nav.className = "kt-eb-nav";
			nav.setAttribute("data-testid", "kt-eb-section-nav");
			(schema.sections || []).forEach(function (sec) {
				var btn = document.createElement("button");
				btn.type = "button";
				btn.textContent = sec.label || sec.key;
				btn.setAttribute("data-section-key", sec.key);
				if (sec.key === state.activeKey) btn.classList.add("is-active");
				if (state.responses[sec.key] && Object.keys(state.responses[sec.key]).length) {
					btn.classList.add("has-data");
				}
				btn.addEventListener("click", function () {
					state.activeKey = sec.key;
					paint();
				});
				nav.appendChild(btn);
			});

			var main = document.createElement("div");
			main.className = "kt-eb-main";
			main.setAttribute("data-testid", "kt-eb-section-panel");

			var toolbar = document.createElement("div");
			toolbar.className = "kt-eb-toolbar";
			function btn(label, testid, handler, primary) {
				var b = document.createElement("button");
				b.type = "button";
				b.className = primary ? "btn btn-sm btn-primary" : "btn btn-sm btn-default";
				b.textContent = label;
				b.setAttribute("data-testid", testid);
				b.disabled = state.busy || (state.readOnly && testid !== "kt-eb-validate");
				if (state.readOnly && (testid === "kt-eb-save" || testid === "kt-eb-submit" || testid === "kt-eb-fill")) {
					b.disabled = true;
				}
				b.addEventListener("click", handler);
				return b;
			}
			toolbar.appendChild(
				btn("Save section", "kt-eb-save", function () {
					if (!api.saveSection) return;
					state.busy = true;
					paint();
					Promise.resolve(api.saveSection(state.activeKey, state.responses[state.activeKey] || {}))
						.then(function (res) {
							if (res && res.responses) state.responses = res.responses;
							state.busy = false;
							paint();
						})
						.catch(function () {
							state.busy = false;
							paint();
						});
				})
			);
			toolbar.appendChild(
				btn("Validate", "kt-eb-validate", function () {
					if (!api.validate) return;
					Promise.resolve(api.validate()).then(function (res) {
						state.errors = (res && res.errors) || [];
						paint();
					});
				})
			);
			toolbar.appendChild(
				btn(
					"Submit & Seal",
					"kt-eb-submit",
					function () {
						if (!api.submit) return;
						state.busy = true;
						paint();
						Promise.resolve(api.submit())
							.then(function (res) {
								state.receipt = res;
								state.readOnly = true;
								state.busy = false;
								state.errors = [];
								paint();
							})
							.catch(function (err) {
								state.busy = false;
								state.errors = [{ message: (err && err.message) || "Submit failed" }];
								paint();
							});
					},
					true
				)
			);
			if (api.fillForTests) {
				toolbar.appendChild(
					btn("Fill PoC answers", "kt-eb-fill", function () {
						Promise.resolve(api.fillForTests()).then(function (res) {
							if (res && res.responses) state.responses = res.responses;
							paint();
						});
					})
				);
			}
			var badge = document.createElement("span");
			badge.className = "kt-eb-badge";
			badge.setAttribute("data-testid", "kt-eb-status");
			badge.textContent = state.readOnly ? "Sealed" : "Draft";
			toolbar.appendChild(badge);
			main.appendChild(toolbar);

			if (state.receipt && state.receipt.receipt_code) {
				var rec = document.createElement("div");
				rec.className = "kt-eb-receipt";
				rec.setAttribute("data-testid", "kt-eb-receipt");
				rec.innerHTML =
					"<strong>Submission receipt</strong><br/>Code: " +
					esc(state.receipt.receipt_code) +
					"<br/>Seal: " +
					esc(state.receipt.seal_hash || "") +
					"<br/>Sealed at: " +
					esc(state.receipt.sealed_at || "");
				main.appendChild(rec);
			}

			if (state.errors && state.errors.length) {
				var err = document.createElement("div");
				err.className = "kt-eb-errors";
				err.setAttribute("data-testid", "kt-eb-errors");
				err.innerHTML =
					"<strong>" +
					state.errors.length +
					" validation issue(s)</strong><ul>" +
					state.errors
						.slice(0, 12)
						.map(function (e) {
							return "<li>" + esc(e.message || e.code || "") + "</li>";
						})
						.join("") +
					"</ul>";
				main.appendChild(err);
			}

			var section = sectionByKey(schema, state.activeKey) || {};
			var heading = document.createElement("h3");
			heading.textContent = section.label || state.activeKey;
			heading.setAttribute("data-testid", "kt-eb-section-title");
			main.appendChild(heading);

			var secResp = state.responses[state.activeKey] || {};
			if (section.requirements) {
				main.appendChild(
					renderRequirements(section, secResp, state.readOnly, function (rid, fk, val) {
						if (!state.responses[state.activeKey]) state.responses[state.activeKey] = {};
						if (!state.responses[state.activeKey][rid]) state.responses[state.activeKey][rid] = {};
						state.responses[state.activeKey][rid][fk] = val;
					})
				);
			} else if (section.price_lines) {
				if (!state.responses[state.activeKey]) state.responses[state.activeKey] = { lines: {}, summary: {} };
				main.appendChild(
					renderPrice(section, state.responses[state.activeKey], state.readOnly, function (path, val) {
						setPath(state.responses[state.activeKey], path, val);
					})
				);
			} else {
				(section.fields || []).forEach(function (field) {
					main.appendChild(
						renderField(field, secResp[field.field_key], state.readOnly, function (fk, val) {
							if (!state.responses[state.activeKey]) state.responses[state.activeKey] = {};
							state.responses[state.activeKey][fk] = val;
						})
					);
				});
			}

			root.appendChild(nav);
			root.appendChild(main);
			hostEl.appendChild(root);
		}

		paint();
		return {
			getResponses: function () {
				return deepClone(state.responses);
			},
			setActiveSection: function (key) {
				state.activeKey = key;
				paint();
			},
			setReceipt: function (receipt) {
				state.receipt = receipt;
				state.readOnly = true;
				paint();
			},
		};
	}

	EB.mount = mount;
	EB.SECTION_ORDER = [
		"tender_document_acknowledgement",
		"form_of_tender",
		"confidential_business_questionnaire",
		"preliminary_documents",
		"technical_qualification",
		"technical_compliance_matrix",
		"implementation_plan",
		"price_schedule",
		"contract_terms_acknowledgement",
		"final_declaration_and_submit",
	];
})(typeof window !== "undefined" ? window : globalThis);
