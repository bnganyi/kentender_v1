/* ── Create Package Wizard — Backend Wired ────────────────────────────────
 * 3-step wizard (+ success screen): Select Demands → Configure Package →
 * Review and Create → Package Created. Ported from
 * `docs/prompts/procurement planning v4/package wizard/step 1-4/code.html`
 * following the same dedicated-Desk-Page + hand-ported CSS/JS pattern as
 * `create_demand_page.js` (see Package Wizard Frontend Redo plan).
 *
 * API: kentender_procurement.procurement_planning.api.package_wizard.*
 * (PW2-PW6 — all read/compute-only until the final create call; nothing
 * persists before Step 3's "Create Package").
 */

(function () {
  "use strict";

  var API = "kentender_procurement.procurement_planning.api.package_wizard.";
  var HANDOFF_KEY = "kt_pw_wizard_handoff_v1";

  // ── Font loader ────────────────────────────────────────────────────────
  function _ensureFonts() {
    if (document.getElementById("kt-pw-fonts")) return;
    var link = document.createElement("link");
    link.id = "kt-pw-fonts";
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&" +
      "family=Hanken+Grotesk:wght@600;700;800&" +
      "family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap";
    document.head.appendChild(link);
  }

  // ── State ──────────────────────────────────────────────────────────────
  function _freshState() {
    return {
      step: 1,
      planCode: "",
      planName: "",
      // Step 1
      demands: [],
      demandsLoaded: false,
      demandsLoading: false,
      search: "",
      selected: {}, // inclusion_code -> demand row
      selectedOrder: [], // inclusion_code[], preserves pick order
      compatibility: null,
      compatChecking: false,
      // Step 2
      config: {
        package_title: "",
        package_description: "",
        target_release_date: "",
        package_priority: "Normal",
      },
      configSeeded: false,
      configPreview: null,
      docPreview: null,
      configLoading: false,
      // Step 3
      readiness: null,
      readinessLoading: false,
      creating: false,
      // Step 4
      createResult: null,
      _wrapper: null,
    };
  }
  var _state = _freshState();

  // ── Helpers ────────────────────────────────────────────────────────────
  function _esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function _ico(name, fill) {
    var s = fill ? ' style="font-variation-settings:\'FILL\' 1"' : "";
    return '<span class="material-symbols-outlined"' + s + ">" + name + "</span>";
  }
  function _fmtMoney(n, currency) {
    var v = Number(n || 0).toLocaleString("en-KE", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    return (currency || "KES") + " " + v;
  }
  function _fmtCompact(n) {
    var v = Number(n || 0);
    var abs = Math.abs(v);
    var out;
    if (abs >= 1e9) out = (v / 1e9).toFixed(2) + "B";
    else if (abs >= 1e6) out = (v / 1e6).toFixed(2) + "M";
    else if (abs >= 1e3) out = (v / 1e3).toFixed(1) + "K";
    else out = String(Math.round(v));
    return out;
  }
  var _CATEGORY_META = {
    Goods: { css: "goods", icon: "inventory_2" },
    Works: { css: "works", icon: "construction" },
    Services: { css: "services", icon: "engineering" },
    Consultancy: { css: "consult", icon: "psychology" },
  };
  function _categoryMeta(category) {
    return _CATEGORY_META[category] || { css: "goods", icon: "inventory_2" };
  }
  function _statusMeta(status) {
    if (status === "Ready") return { css: "ready", icon: "check_circle", label: "Passed" };
    if (status === "Warning") return { css: "warning", icon: "warning", label: "Warning" };
    return { css: "blocked", icon: "cancel", label: "Blocked" };
  }

  function _resetState() {
    var wrapper = _state._wrapper;
    _state = _freshState();
    _state._wrapper = wrapper;
  }

  // Single-use route handoff — set by pp2_planning_router.js right before
  // `frappe.set_route("create-package-wizard")`. Consumed (removed) on read
  // so a later manual/back-button revisit falls back to full Step 1 list
  // instead of silently replaying a stale pre-selection.
  function _consumeHandoff() {
    var out = { plan_code: "", plan_name: "", initial_inclusion_codes: [] };
    try {
      var raw = window.sessionStorage.getItem(HANDOFF_KEY);
      if (raw) {
        window.sessionStorage.removeItem(HANDOFF_KEY);
        var parsed = JSON.parse(raw);
        if (parsed && typeof parsed === "object") {
          out.plan_code = String(parsed.plan_code || "").trim();
          out.plan_name = String(parsed.plan_name || "").trim();
          out.initial_inclusion_codes = Array.isArray(parsed.initial_inclusion_codes)
            ? parsed.initial_inclusion_codes.filter(Boolean)
            : [];
        }
      }
    } catch (e) {
      /* sessionStorage unavailable — wizard falls back to manual Step 1 selection */
    }
    return out;
  }

  function _selectedCodes() {
    return _state.selectedOrder.slice();
  }

  function _configPayload() {
    return {
      package_title: _state.config.package_title || "",
      package_description: _state.config.package_description || "",
      target_release_date: _state.config.target_release_date || "",
      package_priority: _state.config.package_priority || "Normal",
    };
  }

  // ── Stepper ────────────────────────────────────────────────────────────
  function _stepper(current) {
    var labels = ["Select Demands", "Configure Package", "Review and Create"];
    var html = '<div class="kt-pw-stepper">';
    for (var i = 0; i < 3; i++) {
      var num = i + 1;
      var isDone = num < current;
      var isActive = num === current;
      var dotCls = isDone ? "kt-pw-step-dot--done" : isActive ? "kt-pw-step-dot--active" : "";
      var lblCls = isDone ? "kt-pw-step-label--done" : isActive ? "kt-pw-step-label--active" : "";
      html +=
        '<div class="kt-pw-step">' +
        '<span class="kt-pw-step-dot ' + dotCls + '">' + (isDone ? _ico("check") : num) + "</span>" +
        '<span class="kt-pw-step-label ' + lblCls + '">' + _esc(labels[i]) + "</span>" +
        "</div>";
      if (i < 2) {
        html += '<div class="kt-pw-step-connector' + (isDone ? " kt-pw-step-connector--done" : "") + '"></div>';
      }
    }
    html += "</div>";
    return html;
  }

  // ── STEP 1 — Select Demands ──────────────────────────────────────────────
  function _demandCard(row) {
    var code = row.inclusion_code;
    var isSelected = !!_state.selected[code];
    var cat = _categoryMeta(row.category);
    var strategyLabel = String(row.strategy_label || "").trim();
    var strategyHtml = strategyLabel
      ? (
          '<div class="kt-pw-demand-strategy" data-testid="kt-pw-demand-strategy">' +
            '<div class="kt-pw-demand-meta-label">Strategy alignment</div>' +
            '<div class="kt-pw-demand-meta-value">' + _esc(strategyLabel) + "</div>" +
          "</div>"
        )
      : "";
    return (
      '<div class="kt-pw-demand-card' + (isSelected ? " kt-pw-demand-card--selected" : "") + '" data-testid="kt-pw-demand-card" data-inclusion-code="' + _esc(code) + '">' +
        '<div class="kt-pw-demand-card-accent kt-pw-accent--' + cat.css + '"></div>' +
        '<div style="flex:1; min-width:0;">' +
          '<div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">' +
            '<span class="kt-pw-chip kt-pw-chip--' + cat.css + '">' + _esc((row.category || "").toUpperCase()) + "</span>" +
            '<span class="kt-pw-demand-ref">' + _esc(row.ref || row.demand.code) + "</span>" +
          "</div>" +
          '<h3 class="kt-pw-demand-title" data-testid="kt-pw-demand-title">' + _esc(row.demand.name) + "</h3>" +
          strategyHtml +
          '<div class="kt-pw-demand-meta">' +
            '<div><div class="kt-pw-demand-meta-label">Est. Value</div><div class="kt-pw-demand-meta-value">' + _fmtMoney(row.estimated_value, row.currency) + "</div></div>" +
            '<div><div class="kt-pw-demand-meta-label">Department</div><div class="kt-pw-demand-meta-value">' + _esc(row.department || "—") + "</div></div>" +
            '<div><div class="kt-pw-demand-meta-label">Funding Status</div><div class="kt-pw-funding-ok">' + _ico("check_circle", true) + _esc(row.funding_label) + "</div></div>" +
          "</div>" +
        "</div>" +
        '<div style="display:flex; flex-direction:column; align-items:flex-end; gap:8px;">' +
          '<button type="button" class="kt-pw-select-btn' + (isSelected ? " kt-pw-select-btn--selected" : " kt-pw-select-btn--unselected") + '" data-testid="kt-pw-select-demand" data-select-demand="' + _esc(code) + '">' +
            (isSelected ? _ico("check") + "Selected" : _ico("add") + "Select") +
          "</button>" +
        "</div>" +
      "</div>"
    );
  }

  function _step1DemandList() {
    if (_state.demandsLoading && !_state.demandsLoaded) {
      return '<div class="kt-pw-loading">' + _ico("progress_activity") + "Loading eligible demands…</div>";
    }
    if (!_state.demands.length) {
      return '<div class="kt-pw-empty">No eligible demands found for this plan. Demands must be Approved, funded, and added to the active plan before they can be packaged.</div>';
    }
    return _state.demands.map(_demandCard).join("");
  }

  function _step1Summary() {
    var codes = _selectedCodes();
    var rows = codes.map(function (c) { return _state.selected[c]; }).filter(Boolean);
    var total = rows.reduce(function (s, r) { return s + (Number(r.estimated_value) || 0); }, 0);
    var currency = (rows[0] && rows[0].currency) || "KES";
    var categories = Array.from(new Set(rows.map(function (r) { return r.category; }).filter(Boolean)));
    return (
      '<div class="kt-pw-summary-card">' +
        '<div class="kt-pw-summary-head">' + _ico("shopping_cart_checkout") + "Package Selection Summary</div>" +
        '<div class="kt-pw-summary-body">' +
          '<div class="kt-pw-summary-row"><span class="kt-pw-summary-row-label">Selected Demands</span><span class="kt-pw-summary-row-value">' + rows.length + "</span></div>" +
          '<div class="kt-pw-summary-row"><span class="kt-pw-summary-row-label">Total Estimated Value</span><span class="kt-pw-summary-row-value">' + (rows.length ? currency + " " + _fmtCompact(total) : "—") + "</span></div>" +
          '<div class="kt-pw-summary-row"><span class="kt-pw-summary-row-label">Category</span><span class="kt-pw-summary-row-value">' + (categories.join(" / ") || "—") + "</span></div>" +
          (rows.length
            ? '<div style="background:var(--pw-surface-mid); border-radius:8px; padding:12px 14px;">' +
                '<p style="font-size:11px; font-weight:700; text-transform:uppercase; color:var(--pw-on-muted); margin:0 0 8px;">' + _ico("checklist") + " Quick Preview</p>" +
                "<ul style=\"margin:0; padding:0; list-style:none; display:flex; flex-direction:column; gap:6px;\">" +
                rows.map(function (r) {
                  return '<li style="font-size:13px; color:var(--pw-on-surface); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">• ' + _esc(r.demand.name) + "</li>";
                }).join("") +
                "</ul>" +
              "</div>"
            : "") +
        "</div>" +
      "</div>" +
      '<div class="kt-pw-tip-card">' + _ico("lightbulb") + "<span>Only demands that pass the compatibility checks (same entity, fiscal year, category, method, and funding) can be packaged together.</span></div>"
    );
  }

  function _renderStep1() {
    var codes = _selectedCodes();
    var canProceed = codes.length > 0 && (!_state.compatibility || _state.compatibility.compatible !== false);
    return (
      '<div class="kt-pw-canvas">' +
        '<h1 class="kt-pw-title">Create Package</h1>' +
        '<p class="kt-pw-subtitle">' + _ico("info") + " Active Plan: <strong>" + _esc(_state.planName || _state.planCode) + "</strong></p>" +
        _stepper(1) +
        '<div class="kt-pw-grid">' +
          '<div class="kt-pw-main">' +
            "<div>" +
              '<h2 style="font-size:20px; font-weight:700; color:var(--pw-primary); margin-bottom:4px;">Select Demands</h2>' +
              '<p style="color:var(--pw-on-muted); font-size:13px;">Select approved, funded demands from the active procurement plan to include in this package.</p>' +
            "</div>" +
            '<div style="position:relative;">' +
              '<span class="material-symbols-outlined" style="position:absolute; left:12px; top:50%; transform:translateY(-50%); color:var(--pw-on-muted);">search</span>' +
              '<input type="text" id="kt-pw-search" data-testid="kt-pw-search-input" class="kt-pw-input" style="padding-left:38px;" placeholder="Search by demand title or reference…" value="' + _esc(_state.search) + '"/>' +
            "</div>" +
            (_state.compatibility && _state.compatibility.compatible === false
              ? '<div class="kt-pw-conflict-banner" data-testid="kt-pw-compat-conflict">' + _ico("error") + " These demands cannot be packaged together:<ul>" +
                _state.compatibility.reasons.map(function (r) { return "<li>" + _esc(r) + "</li>"; }).join("") +
                "</ul></div>"
              : "") +
            '<div style="display:flex; flex-direction:column; gap:12px;" data-testid="kt-pw-demand-list">' + _step1DemandList() + "</div>" +
            '<div class="kt-pw-footer">' +
              '<span style="color:var(--pw-on-muted); font-size:12px; display:flex; align-items:center; gap:6px;">' + _ico("info") + " Step 1 of 3: Selection Phase</span>" +
              '<div style="display:flex; gap:12px;">' +
                '<button type="button" class="kt-pw-btn kt-pw-btn--secondary" id="kt-pw-cancel" data-testid="kt-pw-cancel">Cancel</button>' +
                '<button type="button" class="kt-pw-btn kt-pw-btn--primary" id="kt-pw-next-1" data-testid="kt-pw-step1-next"' + (canProceed ? "" : " disabled") + ">Next Section " + _ico("arrow_forward") + "</button>" +
              "</div>" +
            "</div>" +
          "</div>" +
          '<div class="kt-pw-side">' + _step1Summary() + "</div>" +
        "</div>" +
      "</div>"
    );
  }

  function _bindStep1(wrapper) {
    var searchEl = wrapper.querySelector("#kt-pw-search");
    if (searchEl) {
      var t = null;
      searchEl.addEventListener("input", function () {
        _state.search = searchEl.value;
        clearTimeout(t);
        t = setTimeout(function () { _fetchStep1Demands(wrapper); }, 300);
      });
    }
    wrapper.querySelectorAll("[data-select-demand]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        _toggleSelectDemand(wrapper, btn.getAttribute("data-select-demand"));
      });
    });
    var cancel = wrapper.querySelector("#kt-pw-cancel");
    if (cancel) cancel.addEventListener("click", _cancelWizard);
    var next = wrapper.querySelector("#kt-pw-next-1");
    if (next) {
      next.addEventListener("click", function () {
        if (next.disabled || !_selectedCodes().length) return;
        _state.step = 2;
        _render(wrapper);
        _loadStep2(wrapper);
      });
    }
  }

  function _fetchStep1Demands(wrapper) {
    _state.demandsLoading = true;
    if (_state.demandsLoaded) _render(wrapper); // keep list visible, just show it's refreshing via search
    frappe.call({
      method: API + "list_pp_wizard_eligible_demands",
      args: { plan_code: _state.planCode, search: _state.search || "" },
      callback: function (r) {
        _state.demandsLoading = false;
        _state.demandsLoaded = true;
        var msg = (r && r.message) || {};
        if (!msg.ok) {
          frappe.show_alert({ indicator: "red", message: msg.message || __("Could not load eligible demands.") });
          _state.demands = [];
          _render(wrapper);
          return;
        }
        _state.demands = msg.demands || [];
        // Re-key selection rows against fresh data so labels stay current.
        _state.selectedOrder.forEach(function (code) {
          var fresh = _state.demands.filter(function (d) { return d.inclusion_code === code; })[0];
          if (fresh) _state.selected[code] = fresh;
        });
        _applyPreselection();
        _render(wrapper);
      },
    });
  }

  function _applyPreselection() {
    if (!_state.preselectCodes || !_state.preselectCodes.length) return;
    var codes = _state.preselectCodes;
    _state.preselectCodes = null; // one-shot
    codes.forEach(function (code) {
      var row = _state.demands.filter(function (d) { return d.inclusion_code === code; })[0];
      if (row && !_state.selected[code]) {
        _state.selected[code] = row;
        _state.selectedOrder.push(code);
      }
    });
    if (_state.selectedOrder.length > 1) _refreshCompatibility();
  }

  function _toggleSelectDemand(wrapper, code) {
    if (!code) return;
    if (_state.selected[code]) {
      delete _state.selected[code];
      _state.selectedOrder = _state.selectedOrder.filter(function (c) { return c !== code; });
    } else {
      var row = _state.demands.filter(function (d) { return d.inclusion_code === code; })[0];
      if (!row) return;
      _state.selected[code] = row;
      _state.selectedOrder.push(code);
    }
    if (_state.selectedOrder.length > 1) {
      _refreshCompatibility(wrapper);
    } else {
      _state.compatibility = null;
      _render(wrapper);
    }
  }

  function _refreshCompatibility(wrapper) {
    wrapper = wrapper || _state._wrapper;
    _state.compatChecking = true;
    frappe.call({
      method: API + "check_pp_package_compatibility",
      args: { inclusion_codes: JSON.stringify(_selectedCodes()) },
      callback: function (r) {
        _state.compatChecking = false;
        var msg = (r && r.message) || {};
        _state.compatibility = msg.ok ? msg : { compatible: true, reasons: [] };
        _render(wrapper);
      },
    });
  }

  // ── STEP 2 — Configure Package ───────────────────────────────────────────
  function _lineRows() {
    var lines = (_state.configPreview && _state.configPreview.lines) || [];
    return lines.map(function (line) {
      return (
        "<tr>" +
          "<td>" + _esc(line.line_title) + "</td>" +
          "<td><div style=\"display:flex; flex-direction:column;\"><span>" + _esc(line.line_title) + "</span><span style=\"font-size:11px; color:var(--pw-on-muted);\">" + _esc(line.source_demand_item) + "</span></div></td>" +
          "<td>" + _esc(line.scope_quantity) + "</td>" +
          '<td class="right">' + _fmtMoney(line.estimated_value, (_state.configPreview.funding || {}).currency) + "</td>" +
          '<td class="center"><button type="button" class="kt-pw-btn kt-pw-btn--danger" data-testid="kt-pw-remove-line" data-remove-line="' + _esc(line.inclusion_code) + '" title="Remove from package">' + _ico("delete") + "</button></td>" +
        "</tr>"
      );
    }).join("");
  }

  function _step2Warnings() {
    var warnings = (_state.configPreview && _state.configPreview.warnings) || [];
    if (!warnings.length) return "";
    return (
      '<div class="kt-pw-warning-list">' +
      warnings.map(function (w) { return '<div class="kt-pw-warning-item">' + _ico("warning") + _esc(w) + "</div>"; }).join("") +
      "</div>"
    );
  }

  function _renderStep2() {
    if (_state.configLoading && !_state.configPreview) {
      return '<div class="kt-pw-canvas">' + _stepper(2) + '<div class="kt-pw-loading">' + _ico("progress_activity") + "Loading package configuration…</div></div>";
    }
    var preview = _state.configPreview || { category_method: {}, funding: {}, lines: [] };
    var doc = _state.docPreview || {};
    var funding = preview.funding || {};
    var cat = _categoryMeta(preview.category_method.category);
    return (
      '<div class="kt-pw-canvas">' +
        '<h1 class="kt-pw-title">Create Procurement Package</h1>' +
        '<p class="kt-pw-subtitle">Package Wizard • Step 2 of 3</p>' +
        _stepper(2) +
        '<div class="kt-pw-grid">' +
          '<div class="kt-pw-main">' +
            '<section class="kt-pw-card">' +
              '<div class="kt-pw-card-head"><div class="kt-pw-card-title">' + _ico("inventory") + "Package Identity</div></div>" +
              '<div class="kt-pw-field-grid">' +
                '<div class="kt-pw-field kt-pw-field--wide"><label class="kt-pw-label">Package Title</label><input type="text" id="kt-pw-title" data-testid="kt-pw-title-input" class="kt-pw-input" value="' + _esc(_state.config.package_title) + '"/></div>' +
                '<div class="kt-pw-field kt-pw-field--wide"><label class="kt-pw-label">Package Description</label><textarea id="kt-pw-description" data-testid="kt-pw-description-input" class="kt-pw-textarea" placeholder="Enter detailed description of the procurement package…">' + _esc(_state.config.package_description) + "</textarea></div>" +
                '<div class="kt-pw-field"><label class="kt-pw-label">Target Release Date</label><input type="date" id="kt-pw-target-date" data-testid="kt-pw-target-date-input" class="kt-pw-input" value="' + _esc(_state.config.target_release_date) + '"/></div>' +
                '<div class="kt-pw-field"><label class="kt-pw-label">Package Priority</label>' +
                  '<select id="kt-pw-priority" data-testid="kt-pw-priority-select" class="kt-pw-select">' +
                    ["Normal", "High", "Emergency"].map(function (p) {
                      return '<option value="' + p + '"' + (p === _state.config.package_priority ? " selected" : "") + ">" + p + "</option>";
                    }).join("") +
                  "</select>" +
                "</div>" +
              "</div>" +
            "</section>" +
            '<section class="kt-pw-card">' +
              '<div class="kt-pw-card-head"><div class="kt-pw-card-title">' + _ico("settings_suggest") + "Category &amp; Procurement Method</div></div>" +
              '<div style="display:grid; grid-template-columns:1fr 1fr; gap:24px;">' +
                "<div>" +
                  '<div class="kt-pw-field" style="margin-bottom:16px;"><label class="kt-pw-label">Procurement Category</label><span class="kt-pw-chip kt-pw-chip--' + cat.css + '" style="width:fit-content;">' + _ico(cat.icon) + _esc((preview.category_method.category || "").toUpperCase()) + "</span></div>" +
                  '<div class="kt-pw-method-box">' +
                    '<div class="kt-pw-method-box-title"><span>' + _esc(preview.category_method.procurement_method || "—") + "</span>" + _ico("verified", true) + "</div>" +
                    '<p class="kt-pw-method-box-note">' + (preview.category_method.method_basis === "Template" ? "Recommended by procurement template based on category and value." : "Manually confirmed method.") + "</p>" +
                  "</div>" +
                "</div>" +
                '<div style="background:var(--pw-surface-mid); border:1px dashed var(--pw-outline-v); border-radius:12px; padding:20px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; gap:6px;">' +
                  _ico("gavel") +
                  '<p style="font-size:11px; color:var(--pw-on-muted);">Method assigned automatically based on Public Procurement Guidelines</p>' +
                "</div>" +
              "</div>" +
            "</section>" +
            '<section class="kt-pw-card" style="padding:0;">' +
              '<div class="kt-pw-card-head" style="padding:20px 20px 0;"><div class="kt-pw-card-title">' + _ico("list_alt") + "Lines &amp; Lot Allocation</div></div>" +
              '<div style="overflow-x:auto; margin-top:12px;">' +
                '<table class="kt-pw-table"><thead><tr><th>Line Title</th><th>Source Demand Item</th><th>Quantity</th><th class="right">Est. Value</th><th class="center">Action</th></tr></thead>' +
                "<tbody>" + _lineRows() + "</tbody></table>" +
              "</div>" +
            "</section>" +
            '<section class="kt-pw-card">' +
              '<div class="kt-pw-card-head"><div class="kt-pw-card-title">' + _ico("description") + "Document / STD Path</div></div>" +
              '<div class="kt-pw-field-grid">' +
                '<div class="kt-pw-doc-row"><span class="kt-pw-doc-row-label">Required Document Family</span><span class="kt-pw-doc-row-value">' + _esc(doc.required_document_family || "—") + "</span></div>" +
                '<div class="kt-pw-doc-row"><span class="kt-pw-doc-row-label">STD Path</span><span class="kt-pw-doc-row-value">' + (doc.std_path_resolved ? _esc(doc.std_path_label) : "Not resolved") + "</span></div>" +
                '<div class="kt-pw-doc-row"><span class="kt-pw-doc-row-label">Specification Attachments</span><span class="kt-pw-doc-row-value">' + (doc.specification_attachments_count || 0) + " document(s)</span></div>" +
              "</div>" +
              (doc.warnings && doc.warnings.length
                ? '<div class="kt-pw-warning-list" style="margin-top:12px;">' + doc.warnings.map(function (w) { return '<div class="kt-pw-warning-item">' + _ico("warning") + _esc(w) + "</div>"; }).join("") + "</div>"
                : "") +
            "</section>" +
            '<div class="kt-pw-footer">' +
              '<button type="button" class="kt-pw-btn kt-pw-btn--secondary" id="kt-pw-cancel" data-testid="kt-pw-cancel">Cancel</button>' +
              '<div style="display:flex; gap:12px;">' +
                '<button type="button" class="kt-pw-btn kt-pw-btn--secondary" id="kt-pw-back-2" data-testid="kt-pw-step2-back">' + _ico("arrow_back") + "Back</button>" +
                '<button type="button" class="kt-pw-btn kt-pw-btn--primary" id="kt-pw-next-2" data-testid="kt-pw-step2-next">Next: Review &amp; Create ' + _ico("arrow_forward") + "</button>" +
              "</div>" +
            "</div>" +
          "</div>" +
          '<div class="kt-pw-side">' +
            '<div class="kt-pw-summary-panel-dark">' +
              '<div class="kt-pw-summary-hero-label">Total Estimated Value</div>' +
              '<div class="kt-pw-summary-hero">' + (funding.currency || "KES") + " " + _fmtCompact(funding.package_estimated_value) + "</div>" +
              '<div class="kt-pw-summary-row" style="margin-top:12px;"><span class="kt-pw-summary-row-label">Funding Status</span><span class="kt-pw-summary-row-value">' + _esc(funding.funding_status || "—") + "</span></div>" +
              '<div class="kt-pw-summary-row"><span class="kt-pw-summary-row-label">Total Lines</span><span class="kt-pw-summary-row-value">' + ((preview.lines || []).length) + " Items</span></div>" +
            "</div>" +
            '<section class="kt-pw-card"><div class="kt-pw-card-head"><div class="kt-pw-card-title">' + _ico("payments") + "Funding Details</div></div>" +
              (funding.budget_lines && funding.budget_lines.length
                ? funding.budget_lines.map(function (bl) {
                    return (
                      '<div class="kt-pw-summary-row"><span class="kt-pw-summary-row-label">' + _esc(bl.budget_line_name || bl.budget_line_code) + "</span><span class=\"kt-pw-summary-row-value\">" + _fmtMoney(bl.amount_reserved, funding.currency) + "</span></div>"
                    );
                  }).join("")
                : '<p style="font-size:12px; color:var(--pw-on-muted);">No linked budget lines found.</p>') +
              _step2Warnings() +
            "</section>" +
            '<div class="kt-pw-tip-card">' + _ico("lightbulb") + "<span>Ensure the Package Title is descriptive for the tender document. You can remove a demand from this package using the delete action in the lines table.</span></div>" +
          "</div>" +
        "</div>" +
      "</div>"
    );
  }

  function _bindStep2(wrapper) {
    ["kt-pw-title", "kt-pw-description", "kt-pw-target-date", "kt-pw-priority"].forEach(function (id) {
      var el = wrapper.querySelector("#" + id);
      if (!el) return;
      var evt = el.tagName === "SELECT" || el.type === "date" ? "change" : "input";
      el.addEventListener(evt, function () {
        if (id === "kt-pw-title") _state.config.package_title = el.value;
        if (id === "kt-pw-description") _state.config.package_description = el.value;
        if (id === "kt-pw-target-date") _state.config.target_release_date = el.value;
        if (id === "kt-pw-priority") _state.config.package_priority = el.value;
      });
    });
    wrapper.querySelectorAll("[data-remove-line]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        _removeLineFromSelection(wrapper, btn.getAttribute("data-remove-line"));
      });
    });
    var cancel = wrapper.querySelector("#kt-pw-cancel");
    if (cancel) cancel.addEventListener("click", _cancelWizard);
    var back = wrapper.querySelector("#kt-pw-back-2");
    if (back) back.addEventListener("click", function () { _state.step = 1; _render(wrapper); });
    var next = wrapper.querySelector("#kt-pw-next-2");
    if (next) {
      next.addEventListener("click", function () {
        _state.step = 3;
        _render(wrapper);
        _loadStep3(wrapper);
      });
    }
  }

  function _removeLineFromSelection(wrapper, code) {
    if (!code) return;
    delete _state.selected[code];
    _state.selectedOrder = _state.selectedOrder.filter(function (c) { return c !== code; });
    if (!_state.selectedOrder.length) {
      frappe.show_alert({ indicator: "orange", message: __("At least one demand is required — returning to Step 1.") });
      _state.step = 1;
      _render(wrapper);
      return;
    }
    if (_state.selectedOrder.length > 1) _refreshCompatibility();
    _loadStep2(wrapper);
  }

  function _loadStep2(wrapper) {
    _state.configLoading = true;
    var codes = _selectedCodes();
    var payload = _configPayload();
    frappe.call({
      method: API + "get_pp_package_wizard_configuration_preview",
      args: { inclusion_codes: JSON.stringify(codes), config: JSON.stringify(payload) },
      callback: function (r) {
        var msg = (r && r.message) || {};
        if (!msg.ok) {
          _state.configLoading = false;
          frappe.show_alert({ indicator: "red", message: msg.message || __("Could not load package configuration.") });
          return;
        }
        _state.configPreview = msg;
        if (!_state.configSeeded) {
          _state.config.package_title = msg.package_identity.package_title;
          _state.config.package_description = msg.package_identity.package_description;
          _state.config.target_release_date = msg.package_identity.target_release_date || "";
          _state.config.package_priority = msg.package_identity.package_priority || "Normal";
          _state.configSeeded = true;
        }
        frappe.call({
          method: API + "get_pp_package_wizard_document_path_preview",
          args: { inclusion_codes: JSON.stringify(codes), config: JSON.stringify(_configPayload()) },
          callback: function (r2) {
            _state.configLoading = false;
            var msg2 = (r2 && r2.message) || {};
            _state.docPreview = msg2.ok ? msg2 : null;
            _render(wrapper);
          },
        });
      },
    });
  }

  // ── STEP 3 — Review and Create ───────────────────────────────────────────
  function _readinessItem(check) {
    var meta = _statusMeta(check.status);
    return (
      '<div class="kt-pw-readiness-item kt-pw-readiness-item--' + meta.css + '" data-testid="kt-pw-readiness-item" data-status="' + meta.css + '">' +
        _ico(meta.icon, true) +
        "<span>" + _esc(check.label) + (check.message ? " — " + _esc(check.message) : "") + "</span>" +
        '<span class="kt-pw-readiness-status">' + meta.label + "</span>" +
      "</div>"
    );
  }

  function _renderStep3() {
    if (_state.readinessLoading && !_state.readiness) {
      return '<div class="kt-pw-canvas">' + _stepper(3) + '<div class="kt-pw-loading">' + _ico("progress_activity") + "Running readiness checks…</div></div>";
    }
    var preview = _state.configPreview || { package_identity: {}, category_method: {}, funding: {}, lines: [] };
    var readiness = _state.readiness || { checks: [], create_allowed: false, blocking_reasons: [] };
    var funding = preview.funding || {};
    var rows = _selectedCodes().map(function (c) { return _state.selected[c]; }).filter(Boolean);
    return (
      '<div class="kt-pw-canvas">' +
        '<h1 class="kt-pw-title">Create Procurement Package</h1>' +
        '<p class="kt-pw-subtitle">Package Wizard • Step 3 of 3</p>' +
        _stepper(3) +
        '<div class="kt-pw-grid">' +
          '<div class="kt-pw-main">' +
            '<section class="kt-pw-card">' +
              '<div class="kt-pw-card-head"><div class="kt-pw-card-title">' + _ico("badge") + "Package Identity Summary</div><button type=\"button\" class=\"kt-pw-edit-link\" data-edit-step=\"2\">" + _ico("edit") + "Edit</button></div>" +
              '<div style="display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:16px; background:var(--pw-surface-low); padding:14px; border-radius:8px;">' +
                '<div><p class="kt-pw-demand-meta-label">Package Name</p><p class="kt-pw-demand-meta-value">' + _esc(preview.package_identity.package_title) + "</p></div>" +
                '<div><p class="kt-pw-demand-meta-label">Priority</p><p class="kt-pw-demand-meta-value">' + _esc(preview.package_identity.package_priority) + "</p></div>" +
                '<div><p class="kt-pw-demand-meta-label">Target Release</p><p class="kt-pw-demand-meta-value">' + _esc(preview.package_identity.target_release_date || "—") + "</p></div>" +
              "</div>" +
            "</section>" +
            '<section class="kt-pw-card">' +
              '<div class="kt-pw-card-head"><div class="kt-pw-card-title">' + _ico("fact_check") + "Selection Summary</div><button type=\"button\" class=\"kt-pw-edit-link\" data-edit-step=\"1\">" + _ico("edit") + "Edit</button></div>" +
              '<div style="display:flex; flex-direction:column; gap:10px;">' +
                rows.map(function (r) {
                  var cat = _categoryMeta(r.category);
                  return (
                    '<div style="display:flex; justify-content:space-between; align-items:center; padding:12px 14px; background:var(--pw-surface-low); border-radius:8px; border-left:4px solid var(--pw-cat-' + cat.css + ');">' +
                      "<div><p style=\"font-weight:600; margin:0;\">" + _esc(r.demand.name) + '</p><p style="font-size:11px; color:var(--pw-on-muted); margin:2px 0 0;">' + _esc(r.department || "") + "</p></div>" +
                      '<div style="text-align:right;"><p style="font-weight:700; margin:0;">' + _fmtMoney(r.estimated_value, r.currency) + "</p></div>" +
                    "</div>"
                  );
                }).join("") +
              "</div>" +
            "</section>" +
            '<section class="kt-pw-card">' +
              '<div class="kt-pw-card-head"><div class="kt-pw-card-title">' + _ico("account_balance_wallet") + "Lines &amp; Funding Summary</div></div>" +
              '<table class="kt-pw-table"><thead><tr><th>Line Item</th><th>Budget Source</th><th class="right">Value</th></tr></thead><tbody>' +
                (preview.lines || []).map(function (l) {
                  return "<tr><td>" + _esc(l.line_title) + "</td><td>" + _esc(l.budget_line_code || "—") + '</td><td class="right">' + _fmtMoney(l.estimated_value, funding.currency) + "</td></tr>";
                }).join("") +
              "</tbody><tfoot><tr><td colspan=\"2\">Total Package Value</td><td class=\"right\">" + _fmtMoney(funding.package_estimated_value, funding.currency) + "</td></tr></tfoot></table>" +
            "</section>" +
            '<section class="kt-pw-card">' +
              '<div class="kt-pw-card-head"><div class="kt-pw-card-title">' + _ico("task_alt") + "Readiness Preview</div></div>" +
              '<div class="kt-pw-readiness-grid">' + readiness.checks.map(_readinessItem).join("") + "</div>" +
              (readiness.blocking_reasons && readiness.blocking_reasons.length
                ? '<div class="kt-pw-blocking-banner" style="margin-top:14px;">' + _ico("error") + "<div>" +
                  readiness.blocking_reasons.map(function (r) { return "<div>" + _esc(r) + "</div>"; }).join("") +
                  "</div></div>"
                : "") +
            "</section>" +
            '<div class="kt-pw-footer">' +
              '<button type="button" class="kt-pw-btn kt-pw-btn--danger" id="kt-pw-cancel" data-testid="kt-pw-cancel">Cancel</button>' +
              '<div style="display:flex; gap:12px;">' +
                '<button type="button" class="kt-pw-btn kt-pw-btn--secondary" id="kt-pw-back-3" data-testid="kt-pw-step3-back">' + _ico("arrow_back") + "Back</button>" +
                '<button type="button" class="kt-pw-btn kt-pw-btn--primary" id="kt-pw-create" data-testid="kt-pw-create-button"' + (readiness.create_allowed && !_state.creating ? "" : " disabled") + ">" +
                  (_state.creating ? _ico("progress_activity") + "Creating…" : "Create Package " + _ico("chevron_right")) +
                "</button>" +
              "</div>" +
            "</div>" +
          "</div>" +
          '<div class="kt-pw-side">' +
            '<div class="kt-pw-summary-panel-dark">' +
              '<div class="kt-pw-summary-hero-label">Total Estimated Value</div>' +
              '<div class="kt-pw-summary-hero">' + (funding.currency || "KES") + " " + _fmtCompact(funding.package_estimated_value) + "</div>" +
              '<div class="kt-pw-summary-row" style="margin-top:12px;"><span class="kt-pw-summary-row-label">Funding Status</span><span class="kt-pw-summary-row-value">' + _esc(funding.funding_status || "—") + "</span></div>" +
              '<div class="kt-pw-summary-row"><span class="kt-pw-summary-row-label">Total Lines</span><span class="kt-pw-summary-row-value">' + ((preview.lines || []).length) + " Items</span></div>" +
              '<div class="kt-pw-summary-row"><span class="kt-pw-summary-row-label">Procurement Method</span><span class="kt-pw-summary-row-value">' + _esc(preview.category_method.procurement_method || "—") + "</span></div>" +
            "</div>" +
          "</div>" +
        "</div>" +
      "</div>"
    );
  }

  function _bindStep3(wrapper) {
    wrapper.querySelectorAll("[data-edit-step]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        _state.step = Number(btn.getAttribute("data-edit-step"));
        _render(wrapper);
      });
    });
    var cancel = wrapper.querySelector("#kt-pw-cancel");
    if (cancel) cancel.addEventListener("click", _cancelWizard);
    var back = wrapper.querySelector("#kt-pw-back-3");
    if (back) back.addEventListener("click", function () { _state.step = 2; _render(wrapper); });
    var create = wrapper.querySelector("#kt-pw-create");
    if (create) create.addEventListener("click", function () { _submitCreate(wrapper); });
  }

  function _loadStep3(wrapper) {
    _state.readinessLoading = true;
    frappe.call({
      method: API + "get_pp_package_wizard_readiness",
      args: { inclusion_codes: JSON.stringify(_selectedCodes()), config: JSON.stringify(_configPayload()) },
      callback: function (r) {
        _state.readinessLoading = false;
        var msg = (r && r.message) || {};
        _state.readiness = msg.ok ? msg : { checks: [], create_allowed: false, blocking_reasons: [msg.message || __("Could not evaluate readiness.")] };
        _render(wrapper);
      },
    });
  }

  function _submitCreate(wrapper) {
    if (_state.creating) return;
    _state.creating = true;
    _render(wrapper);
    frappe.call({
      method: API + "create_pp_package_from_wizard",
      args: { inclusion_codes: JSON.stringify(_selectedCodes()), config: JSON.stringify(_configPayload()) },
      callback: function (r) {
        _state.creating = false;
        var msg = (r && r.message) || {};
        if (!msg.ok) {
          frappe.show_alert({ indicator: "red", message: msg.message || __("Package could not be created.") });
          _loadStep3(wrapper); // re-validate — server state may have changed
          return;
        }
        _state.createResult = msg;
        _state.step = 4;
        _render(wrapper);
      },
      error: function () {
        _state.creating = false;
        frappe.show_alert({ indicator: "red", message: __("Package could not be created.") });
        _render(wrapper);
      },
    });
  }

  // ── STEP 4 — Success ─────────────────────────────────────────────────────
  function _openPackageUrl(packageCode) {
    var code = String(packageCode || "").trim();
    return code
      ? "/app/package-detail/" + encodeURIComponent(code)
      : "/desk/procurement-planning?queue=draft_packages";
  }

  function _renderStep4() {
    var result = _state.createResult || {};
    var pkg = result.package || {};
    var cat = _categoryMeta(pkg.procurement_category);
    var titles = result.demand_titles || [];
    return (
      '<div class="kt-pw-canvas">' +
        '<div class="kt-pw-success-wrap" data-testid="kt-pw-success">' +
          '<div class="kt-pw-success-icon">' + _ico("check_circle", true) + "</div>" +
          '<h1 class="kt-pw-success-title">Package Created Successfully</h1>' +
          '<p class="kt-pw-success-sub">The new procurement package has been validated and committed to the departmental register.</p>' +
          '<div class="kt-pw-success-card">' +
            '<div class="kt-pw-success-card-head">' +
              '<div class="kt-pw-success-card-icon kt-pw-icon-box--' + cat.css + '">' + _ico(cat.icon) + "</div>" +
              "<div>" +
                '<h3 style="margin:0 0 6px; font-size:18px; color:var(--pw-primary);">' + _esc(pkg.package_name || "") + "</h3>" +
                '<div style="display:flex; flex-wrap:wrap; gap:8px;">' +
                  '<span class="kt-pw-chip" style="background:var(--pw-surface-high); color:var(--pw-on-muted);">' + _esc((result.plan && result.plan.plan_name) || "") + "</span>" +
                  '<span class="kt-pw-chip kt-pw-chip--' + cat.css + '">' + _esc((pkg.procurement_category || "").toUpperCase()) + "</span>" +
                  '<span class="kt-pw-chip" style="background:rgba(16,185,129,0.12); color:var(--pw-success);">' + _esc(pkg.status || "Draft Created").toUpperCase() + "</span>" +
                "</div>" +
              "</div>" +
            "</div>" +
            '<div class="kt-pw-success-meta-grid">' +
              '<div><span class="kt-pw-success-ref">Package Reference</span><span class="kt-pw-demand-meta-value">' + _esc(pkg.package_code || "") + "</span></div>" +
              '<div><span class="kt-pw-success-ref">Estimated Value</span><span class="kt-pw-demand-meta-value">' + _fmtMoney(pkg.estimated_value, pkg.currency) + "</span></div>" +
            "</div>" +
            (titles.length
              ? '<div style="margin-top:16px; padding-top:16px; border-top:1px solid var(--pw-outline-v);"><span class="kt-pw-success-ref">Demands Included</span><p style="font-size:13px; color:var(--pw-on-surface); margin:4px 0 0;">' + titles.map(_esc).join(", ") + "</p></div>"
              : "") +
          "</div>" +
          '<div style="background:var(--pw-surface-low); border-radius:12px; padding:20px; margin-bottom:24px; text-align:left;">' +
            '<h4 style="font-size:12px; text-transform:uppercase; color:var(--pw-primary); font-weight:700; display:flex; align-items:center; gap:8px; margin:0 0 12px;">' + _ico("rocket_launch") + "Next Steps</h4>" +
            '<ol style="margin:0; padding-left:18px; display:flex; flex-direction:column; gap:8px; font-size:13px; color:var(--pw-on-surface);">' +
              "<li><strong>Complete Readiness Checklist:</strong> Upload technical specifications, TORs, and market assessment reports.</li>" +
              "<li><strong>Submit for Review:</strong> Once the package is marked as Ready, route it to the Procurement Unit for approval.</li>" +
            "</ol>" +
          "</div>" +
          '<div class="kt-pw-success-actions">' +
            '<button type="button" class="kt-pw-btn kt-pw-btn--primary" id="kt-pw-open-package" data-testid="kt-pw-open-package">Open Package</button>' +
            '<button type="button" class="kt-pw-btn kt-pw-btn--secondary" id="kt-pw-back-to-workbench" data-testid="kt-pw-back-to-workbench">Back to Workbench</button>' +
          "</div>" +
        "</div>" +
      "</div>"
    );
  }

  function _bindStep4(wrapper) {
    var open = wrapper.querySelector("#kt-pw-open-package");
    if (open) {
      open.addEventListener("click", function () {
        window.location.href = _openPackageUrl((_state.createResult.package || {}).package_code);
      });
    }
    var back = wrapper.querySelector("#kt-pw-back-to-workbench");
    if (back) back.addEventListener("click", function () { window.location.href = "/desk/planning-hub"; });
  }

  // ── Cancel ────────────────────────────────────────────────────────────
  function _cancelWizard() {
    var hasProgress = _selectedCodes().length > 0;
    if (!hasProgress) {
      window.location.href = "/desk/planning-hub";
      return;
    }
    frappe.confirm(
      __("Discard this package and return to the Planning Workbench? Nothing has been saved yet."),
      function () { window.location.href = "/desk/planning-hub"; }
    );
  }

  // ── Render dispatcher ─────────────────────────────────────────────────
  function _render(wrapper) {
    switch (_state.step) {
      case 1:
        wrapper.innerHTML = _renderStep1();
        _bindStep1(wrapper);
        break;
      case 2:
        wrapper.innerHTML = _renderStep2();
        _bindStep2(wrapper);
        break;
      case 3:
        wrapper.innerHTML = _renderStep3();
        _bindStep3(wrapper);
        break;
      case 4:
        wrapper.innerHTML = _renderStep4();
        _bindStep4(wrapper);
        break;
    }
    var main = wrapper.closest ? wrapper.closest(".page-content") : null;
    if (main) main.scrollTop = 0;
    window.scrollTo(0, 0);
  }

  // ── Frappe page registration ─────────────────────────────────────────────
  frappe.pages["create-package-wizard"].on_page_load = function (wrapper) {
    _ensureFonts();
    _state._wrapper = wrapper;
  };

  frappe.pages["create-package-wizard"].on_page_show = function (wrapper) {
    _ensureFonts();
    _state._wrapper = wrapper;
    _resetState();
    var handoff = _consumeHandoff();
    _state.planCode = handoff.plan_code;
    _state.planName = handoff.plan_name;
    _state.preselectCodes = handoff.initial_inclusion_codes;
    if (!_state.planCode) {
      frappe.show_alert({ indicator: "red", message: __("No active procurement plan found. Return to the Planning Workbench and try again.") });
      frappe.set_route("planning-hub");
      return;
    }
    _render(wrapper);
    _fetchStep1Demands(wrapper);
  };
})();
