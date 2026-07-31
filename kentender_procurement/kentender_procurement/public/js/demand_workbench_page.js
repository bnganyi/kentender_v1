/* ── DIA Demand Workbench ─────────────────────────────────────────────────── */
/* Live data from get_dia_demand_detail, get_demand_audit_data, get_demand_attachments */

(function () {
  "use strict";

  // ── Font loader ──────────────────────────────────────────────────────────
  function _ensureFonts() {
    if (document.getElementById("kt-wbx-fonts")) return;
    var link = document.createElement("link");
    link.id = "kt-wbx-fonts";
    link.rel = "stylesheet";
    link.href =
      "https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&" +
      "family=Manrope:wght@600;700;800&" +
      "family=JetBrains+Mono:wght@400;500&" +
      "family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap";
    document.head.appendChild(link);
  }

  // ── State ────────────────────────────────────────────────────────────────
  var _state = {
    name:         null,
    detail:       null,
    audit:        null,
    attachments:  null,
    loadError:    null,
    actionPending: false,
    _wrapper:     null,
    _pendingCount: 0,
  };

  // ── Helpers ──────────────────────────────────────────────────────────────
  function _esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#39;");
  }

  function _ico(name, fill) {
    var style = fill ? ' style="font-variation-settings:\'FILL\' 1"' : '';
    return '<span class="material-symbols-outlined"' + style + '>' + name + '</span>';
  }

  function _fmt(amount, currency) {
    var n = parseFloat(amount);
    if (isNaN(n)) return "\u2014";
    var c = currency || "KES";
    return c + " " + n.toLocaleString("en-KE", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
  }

  function _fmtDate(s) {
    if (!s) return "\u2014";
    try {
      // Handle Frappe datetime strings: "YYYY-MM-DD HH:MM:SS.ffffff"
      var clean = String(s).replace(" ", "T").replace(/\.\d+$/, "");
      var d = new Date(clean);
      if (isNaN(d.getTime())) return String(s);
      return d.toLocaleDateString("en-KE", { day: "numeric", month: "short", year: "numeric" });
    } catch (e) { return s; }
  }

  function _fmtFileSize(bytes) {
    if (!bytes) return "";
    var b = parseFloat(bytes);
    if (b >= 1048576) return (b / 1048576).toFixed(1) + " MB";
    if (b >= 1024)    return (b / 1024).toFixed(0) + " KB";
    return b + " B";
  }

  // ── Dialog helpers ───────────────────────────────────────────────────────
  /**
   * _showConfirmDialog(opts, onConfirm)
   * opts: { icon, iconClass, title, subtitle, desc, contextRows, alertText,
   *         confirmLabel, confirmClass, cancelLabel }
   */
  function _showConfirmDialog(opts, onConfirm) {
    var backdrop = document.createElement("div");
    backdrop.className = "kt-wbx-dlg-backdrop";

    var contextHtml = "";
    if (opts.contextRows && opts.contextRows.length) {
      contextHtml = '<div class="kt-wbx-dlg-context">';
      opts.contextRows.forEach(function(r) {
        contextHtml +=
          '<div class="kt-wbx-dlg-ctx-row">' +
            '<span class="kt-wbx-dlg-ctx-label">' + _esc(r.label) + '</span>' +
            '<span class="kt-wbx-dlg-ctx-value' + (r.amount ? ' kt-wbx-dlg-ctx-value--amount' : '') + '">' + _esc(r.value) + '</span>' +
          '</div>';
      });
      contextHtml += '</div>';
    }

    var alertHtml = opts.alertText
      ? '<div class="kt-wbx-dlg-alert">' +
          '<span class="material-symbols-outlined">info</span>' +
          '<span>' + _esc(opts.alertText) + '</span>' +
        '</div>'
      : "";

    backdrop.innerHTML =
      '<div class="kt-wbx-dlg" role="dialog" aria-modal="true">' +
        '<div class="kt-wbx-dlg-header">' +
          '<div class="kt-wbx-dlg-icon ' + (opts.iconClass || 'kt-wbx-dlg-icon--primary') + '">' +
            '<span class="material-symbols-outlined" style="font-variation-settings:\'FILL\' 1">' + (opts.icon || 'help') + '</span>' +
          '</div>' +
          '<div class="kt-wbx-dlg-title-wrap">' +
            '<div class="kt-wbx-dlg-title">' + _esc(opts.title || 'Confirm') + '</div>' +
            (opts.subtitle ? '<div class="kt-wbx-dlg-subtitle">' + _esc(opts.subtitle) + '</div>' : '') +
          '</div>' +
          '<button class="kt-wbx-dlg-close" aria-label="Close">' +
            '<span class="material-symbols-outlined">close</span>' +
          '</button>' +
        '</div>' +
        '<div class="kt-wbx-dlg-body">' +
          (opts.desc ? '<div class="kt-wbx-dlg-desc">' + opts.desc + '</div>' : '') +
          contextHtml +
          alertHtml +
        '</div>' +
        '<div class="kt-wbx-dlg-footer">' +
          '<button class="kt-wbx-dlg-btn kt-wbx-dlg-btn--cancel">' + _esc(opts.cancelLabel || 'Cancel') + '</button>' +
          '<button class="kt-wbx-dlg-btn ' + (opts.confirmClass || 'kt-wbx-dlg-btn--primary') + '">' +
            (opts.confirmIcon ? '<span class="material-symbols-outlined">' + opts.confirmIcon + '</span>' : '') +
            _esc(opts.confirmLabel || 'Confirm') +
          '</button>' +
        '</div>' +
      '</div>';

    function _close() { if (backdrop.parentNode) backdrop.parentNode.removeChild(backdrop); }

    backdrop.querySelector(".kt-wbx-dlg-close").addEventListener("click", _close);
    backdrop.querySelector(".kt-wbx-dlg-btn--cancel").addEventListener("click", _close);
    backdrop.querySelector(".kt-wbx-dlg-btn:last-child").addEventListener("click", function() {
      _close();
      onConfirm();
    });
    backdrop.addEventListener("click", function(e) { if (e.target === backdrop) _close(); });
    document.addEventListener("keydown", function _esc_key(e) {
      if (e.key === "Escape") { _close(); document.removeEventListener("keydown", _esc_key); }
    });

    document.body.appendChild(backdrop);
    setTimeout(function() {
      var btn = backdrop.querySelector(".kt-wbx-dlg-btn:last-child");
      if (btn) btn.focus();
    }, 50);
  }

  /**
   * _showPromptDialog(opts, onConfirm)
   * opts: { icon, iconClass, title, subtitle, desc, contextRows,
   *         fieldLabel, fieldPlaceholder, confirmLabel, confirmClass, cancelLabel,
   *         isDanger }
   * onConfirm(value) — called with trimmed textarea value
   */
  function _showPromptDialog(opts, onConfirm) {
    var backdrop = document.createElement("div");
    backdrop.className = "kt-wbx-dlg-backdrop";

    var contextHtml = "";
    if (opts.contextRows && opts.contextRows.length) {
      contextHtml = '<div class="kt-wbx-dlg-context">';
      opts.contextRows.forEach(function(r) {
        contextHtml +=
          '<div class="kt-wbx-dlg-ctx-row">' +
            '<span class="kt-wbx-dlg-ctx-label">' + _esc(r.label) + '</span>' +
            '<span class="kt-wbx-dlg-ctx-value">' + _esc(r.value) + '</span>' +
          '</div>';
      });
      contextHtml += '</div>';
    }

    backdrop.innerHTML =
      '<div class="kt-wbx-dlg" role="dialog" aria-modal="true">' +
        '<div class="kt-wbx-dlg-header">' +
          '<div class="kt-wbx-dlg-icon ' + (opts.iconClass || 'kt-wbx-dlg-icon--primary') + '">' +
            '<span class="material-symbols-outlined" style="font-variation-settings:\'FILL\' 1">' + (opts.icon || 'edit_note') + '</span>' +
          '</div>' +
          '<div class="kt-wbx-dlg-title-wrap">' +
            '<div class="kt-wbx-dlg-title">' + _esc(opts.title || 'Provide details') + '</div>' +
            (opts.subtitle ? '<div class="kt-wbx-dlg-subtitle">' + _esc(opts.subtitle) + '</div>' : '') +
          '</div>' +
          '<button class="kt-wbx-dlg-close" aria-label="Close">' +
            '<span class="material-symbols-outlined">close</span>' +
          '</button>' +
        '</div>' +
        '<div class="kt-wbx-dlg-body">' +
          (opts.desc ? '<div class="kt-wbx-dlg-desc">' + opts.desc + '</div>' : '') +
          contextHtml +
          '<div class="kt-wbx-dlg-field">' +
            '<label class="kt-wbx-dlg-label">' + _esc(opts.fieldLabel || 'Reason') + '<span class="kt-wbx-dlg-req">*</span></label>' +
            '<textarea class="kt-wbx-dlg-textarea" placeholder="' + _esc(opts.fieldPlaceholder || 'Enter reason…') + '"></textarea>' +
            '<span class="kt-wbx-dlg-field-err">Please provide a reason before proceeding.</span>' +
          '</div>' +
        '</div>' +
        '<div class="kt-wbx-dlg-footer">' +
          '<button class="kt-wbx-dlg-btn kt-wbx-dlg-btn--cancel">' + _esc(opts.cancelLabel || 'Cancel') + '</button>' +
          '<button class="kt-wbx-dlg-btn ' + (opts.confirmClass || 'kt-wbx-dlg-btn--primary') + '">' +
            (opts.confirmIcon ? '<span class="material-symbols-outlined">' + opts.confirmIcon + '</span>' : '') +
            _esc(opts.confirmLabel || 'Submit') +
          '</button>' +
        '</div>' +
      '</div>';

    var textarea  = backdrop.querySelector(".kt-wbx-dlg-textarea");
    var errEl     = backdrop.querySelector(".kt-wbx-dlg-field-err");
    var submitBtn = backdrop.querySelector(".kt-wbx-dlg-footer .kt-wbx-dlg-btn:last-child");

    function _close() { if (backdrop.parentNode) backdrop.parentNode.removeChild(backdrop); }

    backdrop.querySelector(".kt-wbx-dlg-close").addEventListener("click", _close);
    backdrop.querySelector(".kt-wbx-dlg-btn--cancel").addEventListener("click", _close);
    backdrop.addEventListener("click", function(e) { if (e.target === backdrop) _close(); });
    document.addEventListener("keydown", function _esc_key(e) {
      if (e.key === "Escape") { _close(); document.removeEventListener("keydown", _esc_key); }
    });

    textarea.addEventListener("input", function() {
      if (textarea.value.trim()) {
        textarea.classList.remove("is-error");
        errEl.classList.remove("is-visible");
      }
    });

    submitBtn.addEventListener("click", function() {
      var val = textarea.value.trim();
      if (!val) {
        textarea.classList.add("is-error");
        errEl.classList.add("is-visible");
        textarea.focus();
        return;
      }
      _close();
      onConfirm(val);
    });

    document.body.appendChild(backdrop);
    setTimeout(function() { textarea.focus(); }, 50);
  }

  /**
   * _showBudgetLinePicker(demandName, currentLine, onSaved)
   * A search-as-you-type dialog for selecting and saving a Budget Line.
   */
  function _showBudgetLinePicker(demandName, currentLine, onSaved) {
    var BL_API  = "kentender_budget.api.dia_budget_control.search_budget_lines";
    var BUD_API = "kentender_budget.api.dia_budget_control.get_budgets_for_picker";
    var SET_API = "kentender_procurement.demand_intake.api.lifecycle.set_budget_line";

    // Scope picker to the demand's own procuring entity to prevent cross-entity mismatches
    var _pe = (_state.detail && _state.detail.a && _state.detail.a.procuring_entity)
              ? _state.detail.a.procuring_entity : null;

    var backdrop = document.createElement("div");
    backdrop.className = "kt-wbx-dlg-backdrop";

    var _step = 1;
    var _selectedBudget = null;   // { name, budget_name, fiscal_year, entity_name }
    var _selectedLineId = null;
    var _searchTimer   = null;

    function _fmtKes(n) {
      var v = parseFloat(n);
      if (isNaN(v)) return "\u2014";
      if (v >= 1e9) return "KES " + (v / 1e9).toFixed(1) + "B";
      if (v >= 1e6) return "KES " + (v / 1e6).toFixed(1) + "M";
      return "KES " + v.toLocaleString("en-KE", { minimumFractionDigits: 0, maximumFractionDigits: 0 });
    }

    // ── Shared shell ──────────────────────────────────────────────────────
    backdrop.innerHTML =
      '<div class="kt-wbx-dlg" role="dialog" aria-modal="true" style="max-width:500px">' +
        '<div class="kt-wbx-dlg-header">' +
          '<div class="kt-wbx-dlg-icon kt-wbx-dlg-icon--primary kt-wbx-blp-icon">' +
            '<span class="material-symbols-outlined" style="font-variation-settings:\'FILL\' 1">account_balance_wallet</span>' +
          '</div>' +
          '<div class="kt-wbx-dlg-title-wrap">' +
            '<div class="kt-wbx-dlg-title kt-wbx-blp-title">Select Budget</div>' +
            '<div class="kt-wbx-dlg-subtitle kt-wbx-blp-subtitle">Step 1 of 2 — Choose the budget envelope</div>' +
          '</div>' +
          '<button class="kt-wbx-dlg-close" aria-label="Close">' +
            '<span class="material-symbols-outlined">close</span>' +
          '</button>' +
        '</div>' +
        '<div class="kt-wbx-dlg-body" style="gap:10px">' +
          '<div class="kt-wbx-bl-search-wrap">' +
            '<span class="material-symbols-outlined kt-wbx-bl-search-icon">search</span>' +
            '<input type="text" class="kt-wbx-bl-search-input kt-wbx-blp-search" placeholder="Search budgets…" autocomplete="off">' +
          '</div>' +
          '<div class="kt-wbx-bl-results kt-wbx-blp-results"></div>' +
        '</div>' +
        '<div class="kt-wbx-dlg-footer">' +
          '<button class="kt-wbx-dlg-btn kt-wbx-dlg-btn--cancel kt-wbx-blp-back">Cancel</button>' +
          '<button class="kt-wbx-dlg-btn kt-wbx-dlg-btn--primary kt-wbx-blp-next" disabled>' +
            'Next <span class="material-symbols-outlined">arrow_forward</span>' +
          '</button>' +
        '</div>' +
      '</div>';

    var titleEl    = backdrop.querySelector(".kt-wbx-blp-title");
    var subtitleEl = backdrop.querySelector(".kt-wbx-blp-subtitle");
    var searchEl   = backdrop.querySelector(".kt-wbx-blp-search");
    var resultsEl  = backdrop.querySelector(".kt-wbx-blp-results");
    var backBtn    = backdrop.querySelector(".kt-wbx-blp-back");
    var nextBtn    = backdrop.querySelector(".kt-wbx-blp-next");

    function _close() { if (backdrop.parentNode) backdrop.parentNode.removeChild(backdrop); }

    // ── Step 1: Budget list ───────────────────────────────────────────────
    function _renderBudgets(rows) {
      if (!rows || !rows.length) {
        resultsEl.innerHTML = '<div class="kt-wbx-bl-empty">No budgets found.</div>';
        return;
      }
      resultsEl.innerHTML = rows.map(function(r) {
        var sel = (_selectedBudget && r.name === _selectedBudget.name) ? " kt-wbx-bl-item--selected" : "";
        return (
          '<button class="kt-wbx-bl-item kt-wbx-bl-item--budget' + sel + '" data-bud-id="' + _esc(r.name) + '" data-bud-json="' + _esc(JSON.stringify(r)) + '">' +
            '<div class="kt-wbx-bl-item-name">' + _esc(r.budget_name || r.name) + '</div>' +
            '<div class="kt-wbx-bl-item-meta">' +
              '<span>' + _esc(r.entity_name || r.procuring_entity || "") + '</span>' +
              (r.fiscal_year ? '<span>FY ' + _esc(String(r.fiscal_year)) + '</span>' : '') +
              '<span class="kt-wbx-bl-item-status kt-wbx-bl-item-status--' + _esc((r.status || "").toLowerCase()) + '">' + _esc(r.status || "") + '</span>' +
            '</div>' +
          '</button>'
        );
      }).join("");
    }

    function _fetchBudgets(q) {
      resultsEl.innerHTML = '<div class="kt-wbx-bl-loading"><span class="material-symbols-outlined" style="font-size:16px;vertical-align:-3px">hourglass_top</span> Loading…</div>';
      frappe.call({
        method: BUD_API,
        args: { query: q, procuring_entity: _pe, limit: 15 },
        callback: function(r) {
          _renderBudgets((r && r.message && r.message.results) ? r.message.results : []);
        },
      });
    }

    // ── Step 2: Budget Line list ──────────────────────────────────────────
    function _renderLines(rows) {
      if (!rows || !rows.length) {
        resultsEl.innerHTML = '<div class="kt-wbx-bl-empty">No active budget lines in this budget.</div>';
        return;
      }
      resultsEl.innerHTML = rows.map(function(r) {
        var avail = parseFloat(r.amount_available) || 0;
        var availCls = avail > 0 ? " kt-wbx-bl-avail--ok" : " kt-wbx-bl-avail--low";
        var sel = (r.name === _selectedLineId) ? " kt-wbx-bl-item--selected" : "";
        return (
          '<button class="kt-wbx-bl-item' + sel + '" data-bl-id="' + _esc(r.name) + '">' +
            '<div class="kt-wbx-bl-item-name">' + _esc(r.budget_line_name || r.name) + '</div>' +
            '<div class="kt-wbx-bl-item-meta">' +
              '<span>' + _esc(r.budget_line_code || r.name) + '</span>' +
              '<span class="kt-wbx-bl-avail' + availCls + '">Available: ' + _esc(_fmtKes(avail)) + '</span>' +
            '</div>' +
          '</button>'
        );
      }).join("");
    }

    function _fetchLines(q) {
      resultsEl.innerHTML = '<div class="kt-wbx-bl-loading"><span class="material-symbols-outlined" style="font-size:16px;vertical-align:-3px">hourglass_top</span> Loading…</div>';
      frappe.call({
        method: BL_API,
        args: { query: q, budget_id: _selectedBudget ? _selectedBudget.name : null, procuring_entity: _pe, limit: 20 },
        callback: function(r) {
          _renderLines((r && r.message && r.message.results) ? r.message.results : []);
        },
      });
    }

    // ── Navigation ────────────────────────────────────────────────────────
    function _goStep1() {
      _step = 1;
      _selectedLineId = null;
      titleEl.textContent = "Select Budget";
      subtitleEl.textContent = "Step 1 of 2 \u2014 Choose the budget envelope";
      searchEl.value = "";
      searchEl.placeholder = "Search budgets\u2026";
      backBtn.textContent = "Cancel";
      nextBtn.innerHTML = 'Next <span class="material-symbols-outlined">arrow_forward</span>';
      nextBtn.disabled = !_selectedBudget;
      nextBtn.className = "kt-wbx-dlg-btn kt-wbx-dlg-btn--primary kt-wbx-blp-next";
      _fetchBudgets("");
      setTimeout(function() { searchEl.focus(); }, 30);
    }

    function _goStep2() {
      _step = 2;
      titleEl.textContent = "Select Budget Line";
      subtitleEl.textContent = "Step 2 of 2 \u2014 " + (_selectedBudget ? _esc(_selectedBudget.budget_name) : "");
      searchEl.value = "";
      searchEl.placeholder = "Search lines\u2026";
      backBtn.innerHTML = '<span class="material-symbols-outlined">arrow_back</span> Back';
      nextBtn.innerHTML = '<span class="material-symbols-outlined">link</span> Save Budget Line';
      nextBtn.disabled = true;
      nextBtn.className = "kt-wbx-dlg-btn kt-wbx-dlg-btn--success kt-wbx-blp-next";
      _fetchLines("");
      setTimeout(function() { searchEl.focus(); }, 30);
    }

    // ── Events ────────────────────────────────────────────────────────────
    searchEl.addEventListener("input", function() {
      clearTimeout(_searchTimer);
      _searchTimer = setTimeout(function() {
        if (_step === 1) _fetchBudgets(searchEl.value.trim());
        else _fetchLines(searchEl.value.trim());
      }, 280);
    });

    resultsEl.addEventListener("click", function(e) {
      if (_step === 1) {
        var item = e.target.closest("[data-bud-id]");
        if (!item) return;
        try { _selectedBudget = JSON.parse(item.getAttribute("data-bud-json")); } catch (x) {}
        nextBtn.disabled = false;
        resultsEl.querySelectorAll("[data-bud-id]").forEach(function(el) {
          el.classList.toggle("kt-wbx-bl-item--selected", el.getAttribute("data-bud-id") === _selectedBudget.name);
        });
      } else {
        var item2 = e.target.closest("[data-bl-id]");
        if (!item2) return;
        _selectedLineId = item2.getAttribute("data-bl-id");
        nextBtn.disabled = false;
        resultsEl.querySelectorAll("[data-bl-id]").forEach(function(el) {
          el.classList.toggle("kt-wbx-bl-item--selected", el.getAttribute("data-bl-id") === _selectedLineId);
        });
      }
    });

    backBtn.addEventListener("click", function() {
      if (_step === 2) _goStep1();
      else _close();
    });

    nextBtn.addEventListener("click", function() {
      if (_step === 1) {
        if (_selectedBudget) _goStep2();
      } else {
        if (!_selectedLineId) return;
        nextBtn.disabled = true;
        frappe.call({
          method: SET_API,
          args: { demand_name: demandName, budget_line: _selectedLineId },
          callback: function() {
            _close();
            if (onSaved) onSaved(_selectedLineId);
          },
          error: function(r) {
            nextBtn.disabled = false;
            frappe.msgprint({
              title: "Could not save",
              message: (r && r.message) ? r.message : "An error occurred.",
              indicator: "red",
            });
          },
        });
      }
    });

    backdrop.querySelector(".kt-wbx-dlg-close").addEventListener("click", _close);
    backdrop.addEventListener("click", function(e) { if (e.target === backdrop) _close(); });
    document.addEventListener("keydown", function _esc_key(e) {
      if (e.key === "Escape") { _close(); document.removeEventListener("keydown", _esc_key); }
    });

    document.body.appendChild(backdrop);
    _goStep1();
  }

  // ── Badge helpers ────────────────────────────────────────────────────────
  var _STATUS_BADGE = {
    "Draft":                      { cls: "kt-wbx-badge--draft",    lbl: "Draft" },
    "Pending HoD Approval":       { cls: "kt-wbx-badge--pending",  lbl: "HoD Review" },
    "Pending Finance Approval":   { cls: "kt-wbx-badge--reserved", lbl: "Funding Review" },
    "Approved":                   { cls: "kt-wbx-badge--approved", lbl: "Approved" },
    "Planning Ready":             { cls: "kt-wbx-badge--approved", lbl: "Planning Ready" },
    "Rejected":                   { cls: "kt-wbx-badge--rejected", lbl: "Rejected" },
    "Cancelled":                  { cls: "kt-wbx-badge--rejected", lbl: "Cancelled" },
  };

  var _PRIORITY_BADGE = {
    "High":     { cls: "kt-wbx-badge--high",   lbl: "High Priority" },
    "Medium":   { cls: "kt-wbx-badge--medium", lbl: "Medium Priority" },
    "Low":      { cls: "kt-wbx-badge--low",    lbl: "Low Priority" },
    "Critical": { cls: "kt-wbx-badge--high",   lbl: "Critical" },
  };

  var _STATUSES_EDITABLE = ["Draft", "Rejected"];

  // ── Timeline stage config ────────────────────────────────────────────────
  var _TL_STAGES = [
    { key: "draft",    label: "Draft Created",          auditLabel: "Draft created",           activeStatuses: [] },
    { key: "submit",   label: "Submitted for Approval", auditLabel: "Submitted for approval",  activeStatuses: ["Pending HoD Approval"] },
    { key: "hod",      label: "Departmental Review",    auditLabel: "HoD approved",            activeStatuses: ["Pending HoD Approval"] },
    { key: "finance",  label: "Finance & Budget Review",auditLabel: "Finance approved",        activeStatuses: ["Pending Finance Approval"] },
    { key: "final",    label: "Final Approval",         auditLabel: "Marked planning ready",   activeStatuses: ["Approved", "Planning Ready"] },
  ];

  // ── W4: Build timeline from audit data ───────────────────────────────────
  function _buildTimeline(detail, audit) {
    var status = ((detail || {}).a || {}).status || "";
    var tlEvents = ((audit || {}).timeline) || [];

    function _findAuditEvent(auditLabel) {
      for (var i = 0; i < tlEvents.length; i++) {
        if ((tlEvents[i].label || "").toLowerCase() === auditLabel.toLowerCase())
          return tlEvents[i];
      }
      return null;
    }

    var steps = [];
    // Draft created is always done if demand exists
    var draftEvt = _findAuditEvent("Draft created");
    steps.push({
      label: "Draft Created",
      actor: draftEvt ? (draftEvt.detail || "") : "",
      date: draftEvt ? (draftEvt.at || null) : null,
      state: "done",
    });

    // Submitted
    var submitEvt = _findAuditEvent("Submitted for approval");
    steps.push({
      label: "Submitted for Approval",
      actor: submitEvt ? (submitEvt.detail || "") : "",
      date: submitEvt ? (submitEvt.at || null) : null,
      state: submitEvt ? "done"
             : status === "Pending HoD Approval" ? "active"
             : "locked",
    });

    // HoD
    var hodEvt = _findAuditEvent("HoD approved");
    var hodReturn = _findAuditEvent("Returned for correction");
    var hodActive = (status === "Pending HoD Approval" && submitEvt);
    var hodNote = hodReturn ? (hodReturn.note || "") : null;
    steps.push({
      label: "Departmental Review",
      actor: hodEvt ? (hodEvt.detail || "") : (hodActive ? "Pending HoD Approver" : ""),
      date: hodEvt ? (hodEvt.at || null) : null,
      state: hodEvt ? "done" : hodActive ? "active" : "locked",
      note: hodNote,
    });

    // Finance
    var finEvt = _findAuditEvent("Finance approved");
    var finActive = (status === "Pending Finance Approval");
    steps.push({
      label: "Finance & Budget Review",
      actor: finEvt ? (finEvt.detail || "") : (finActive ? "Pending Finance Officer" : ""),
      date: finEvt ? (finEvt.at || null) : null,
      state: finEvt ? "done" : finActive ? "active" : "locked",
    });

    // Final
    var finalEvt = _findAuditEvent("Marked planning ready");
    var finalDone = (status === "Planning Ready") || !!finalEvt;
    var finalActive = (status === "Approved" && !finalEvt);
    steps.push({
      label: "Final Approval",
      actor: finalEvt ? (finalEvt.detail || "") : (finalActive ? "Procurement Authority" : "Procurement Authority"),
      date: finalEvt ? (finalEvt.at || null) : null,
      state: finalDone ? "done" : finalActive ? "active" : "locked",
    });

    return steps;
  }

  // ── W6: State-aware banner ───────────────────────────────────────────────
  function _bannerConfig(detail) {
    var status = ((detail || {}).a || {}).status || "";
    var blocked = !!(detail || {}).integrity_blocked;

    if (status === "Pending HoD Approval") {
      return { msg: "Awaiting departmental review and approval.", action: null };
    }
    if (status === "Pending Finance Approval") {
      return {
        msg: "Pending Finance signature for fund reservation. Please validate the budget line before approving.",
        action: { label: "Request Urgent Review", icon: "send" },
      };
    }
    if (status === "Approved" && blocked) {
      return {
        msg: "Budget reservation has an integrity issue. Please review and return to Finance if needed.",
        action: { label: "Send back to Finance", icon: "undo", id: "return_approved_to_finance" },
      };
    }
    if (status === "Approved") {
      return {
        msg: "Demand is fully approved. Confirm planning readiness when ready to proceed.",
        action: { label: "Confirm Planning Ready", icon: "check_circle", id: "mark_planning_ready" },
      };
    }
    if (status === "Rejected") {
      return { msg: "This demand was rejected. The requisitioner can edit and resubmit.", action: null };
    }
    if (status === "Cancelled") {
      return { msg: "This demand has been cancelled.", action: null };
    }
    return null;
  }

  // ── Render skeleton ──────────────────────────────────────────────────────
  function _renderSkeleton(wrapper) {
    wrapper.innerHTML =
      '<div class="kt-wbx-canvas">' +
        '<div class="kt-wbx-nav"><div class="kt-wbx-skeleton kt-wbx-skel-sub" style="width:180px"></div></div>' +
        '<div class="kt-wbx-main">' +
          '<div class="kt-wbx-header">' +
            '<div class="kt-wbx-skeleton kt-wbx-skel-title"></div>' +
            '<div class="kt-wbx-skeleton kt-wbx-skel-sub" style="margin-top:8px"></div>' +
          '</div>' +
          '<div class="kt-wbx-bento">' +
            '<div class="kt-wbx-skeleton kt-wbx-skel-card"></div>' +
            '<div class="kt-wbx-skeleton kt-wbx-skel-card"></div>' +
            '<div class="kt-wbx-skeleton kt-wbx-skel-card"></div>' +
          '</div>' +
          '<div class="kt-wbx-body">' +
            '<div class="kt-wbx-left">' +
              '<div class="kt-wbx-card"><div class="kt-wbx-skeleton kt-wbx-skel-card" style="margin:16px"></div></div>' +
              '<div class="kt-wbx-card"><div class="kt-wbx-skeleton kt-wbx-skel-row" style="margin:16px"></div></div>' +
            '</div>' +
            '<div class="kt-wbx-right">' +
              '<div class="kt-wbx-skeleton kt-wbx-skel-card" style="height:240px"></div>' +
              '<div class="kt-wbx-skeleton kt-wbx-skel-card" style="height:240px;margin-top:16px"></div>' +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>';
  }

  // ── Render inline error ──────────────────────────────────────────────────
  function _renderError(wrapper, msg, code) {
    var isAccess = code === "DIA_ACCESS_DENIED";
    var isNotFound = code === "NOT_FOUND";
    var icon = isAccess ? "lock" : isNotFound ? "search_off" : "error_outline";
    var hint = isAccess ? "You do not have permission to access this demand."
              : isNotFound ? "This demand does not exist or may have been deleted."
              : (msg || "An unexpected error occurred. Please try again.");
    wrapper.innerHTML =
      '<div class="kt-wbx-canvas">' +
        '<div class="kt-wbx-nav">' +
          '<button class="kt-wbx-back" id="kt-wbx-back-btn">' + _ico("arrow_back") + 'Demand Hub</button>' +
        '</div>' +
        '<div class="kt-wbx-main" style="align-items:center;padding-top:80px">' +
          '<div class="kt-wbx-error-card">' +
            '<div class="kt-wbx-error-icon">' + _ico(icon) + '</div>' +
            '<div class="kt-wbx-error-title">' + _esc(isAccess ? "Access Denied" : isNotFound ? "Not Found" : "Error") + '</div>' +
            '<div class="kt-wbx-error-msg">' + _esc(hint) + '</div>' +
            '<button class="kt-wbx-btn kt-wbx-btn--ghost" id="kt-wbx-back-btn2">' + _ico("arrow_back") + 'Back to Hub</button>' +
          '</div>' +
        '</div>' +
      '</div>';
    [wrapper.querySelector("#kt-wbx-back-btn"), wrapper.querySelector("#kt-wbx-back-btn2")].forEach(function(b) {
      if (b) b.addEventListener("click", function() { frappe.set_route("demand-hub"); });
    });
  }

  // ── Render full page ─────────────────────────────────────────────────────
  function _renderPage(wrapper, detail, audit, attachments) {
    var a   = detail.a || {};
    var b   = detail.b || {};
    var c   = detail.c || {};
    var d   = detail.d || {};
    var cur = detail.currency || "KES";
    var isEditable = _STATUSES_EDITABLE.indexOf(a.status) >= 0;

    // badges
    var sb = _STATUS_BADGE[a.status] || { cls: "kt-wbx-badge--pending", lbl: a.status || "Unknown" };
    var pb = _PRIORITY_BADGE[a.priority_level] || null;
    var badges =
      '<div class="kt-wbx-badges">' +
        '<span class="kt-wbx-badge ' + sb.cls + '">' + _esc(sb.lbl) + '</span>' +
        (pb ? '<span class="kt-wbx-badge ' + pb.cls + '">' + _esc(pb.lbl) + '</span>' : '') +
      '</div>';

    // title block
    var titleBlock =
      '<div>' +
        badges +
        '<h1 class="kt-wbx-title">' + _esc(a.title || "Demand") + '</h1>' +
        '<p class="kt-wbx-subtitle">' +
          _ico("account_balance") +
          _esc(a.requesting_department_label || a.requesting_department || "") +
          (a.demand_id ? '<span style="opacity:0.45;margin:0 6px">&bull;</span><span style="font-family:\'JetBrains Mono\',monospace;font-size:12px;opacity:0.7">' + _esc(a.demand_id) + '</span>' : '') +
        '</p>' +
      '</div>';

    // action buttons (role/state-aware from API)
    var actions = detail.actions || [];
    var actHtml = '<div class="kt-wbx-actions">';
    actions.forEach(function(act) {
      var cls = act.primary ? "kt-wbx-btn--primary" : act.danger ? "kt-wbx-btn--danger" : "kt-wbx-btn--ghost";
      var icon = act.id === "open_form" ? (act.edit ? "edit" : "visibility")
               : act.id === "submit_demand" ? "send"
               : act.id === "approve_hod" || act.id === "approve_finance" ? "account_balance"
               : act.id === "return_from_hod" || act.id === "return_from_finance" || act.id === "return_approved_to_finance" ? "undo"
               : act.id === "reject_from_hod" || act.id === "reject_from_finance" ? "cancel"
               : act.id === "cancel_demand" ? "block"
               : act.id === "mark_planning_ready" ? "check_circle"
               : "arrow_forward";
      actHtml +=
        '<button class="kt-wbx-btn ' + cls + '" data-action="' + _esc(act.id) + '"' +
          (act.method ? ' data-method="' + _esc(act.method) + '"' : '') +
          (act.reason ? ' data-reason="' + _esc(act.reason) + '"' : '') +
          (act.client_action ? ' data-client="' + _esc(act.client_action) + '"' : '') +
          (act.edit !== undefined ? ' data-edit="' + (act.edit ? "1" : "0") + '"' : '') +
        '>' + _ico(icon) + _esc(act.label) + '</button>';
    });
    actHtml += '</div>';

    // bento cards
    var bento =
      '<div class="kt-wbx-bento">' +
        '<div class="kt-wbx-card kt-wbx-bento-card">' +
          '<div class="kt-wbx-bento-icon kt-wbx-bento-icon--primary">' + _ico("payments", true) + '</div>' +
          '<div><div class="kt-wbx-bento-label">Estimated Value</div>' +
          '<div class="kt-wbx-bento-value">' + _esc(_fmt(c.total_amount, cur)) + '</div></div>' +
        '</div>' +
        '<div class="kt-wbx-card kt-wbx-bento-card">' +
          '<div class="kt-wbx-bento-icon kt-wbx-bento-icon--secondary">' + _ico("calendar_today") + '</div>' +
          '<div><div class="kt-wbx-bento-label">Required By Date</div>' +
          '<div class="kt-wbx-bento-value">' + _esc(_fmtDate(a.required_by_date)) + '</div></div>' +
        '</div>' +
        '<div class="kt-wbx-card kt-wbx-bento-card">' +
          '<div class="kt-wbx-bento-icon kt-wbx-bento-icon--tertiary">' + _ico("inventory_2") + '</div>' +
          '<div><div class="kt-wbx-bento-label">Procurement Category</div>' +
          '<div class="kt-wbx-bento-value">' + _esc(a.requisition_type || "\u2014") + '</div></div>' +
        '</div>' +
      '</div>';

    // demand items table
    var rows = (d.rows || []);
    var itemRows = rows.map(function(it) {
      var qty = it.quantity ? (it.quantity + (it.uom ? " " + it.uom : "")) : (it.uom || "\u2014");
      return (
        '<tr>' +
          '<td><div class="kt-wbx-item-name">' + _esc(it.item_description || "") + '</div>' +
              '<div class="kt-wbx-item-meta">' + _esc(it.category || "") + '</div></td>' +
          '<td><span class="kt-wbx-item-qty">' + _esc(qty) + '</span></td>' +
          '<td><span class="kt-wbx-item-total">' + _esc(_fmt(it.line_total, cur)) + '</span></td>' +
        '</tr>'
      );
    }).join("");
    var totalAmt = rows.reduce(function(s, it) { return s + (parseFloat(it.line_total) || 0); }, 0);
    var itemsSection =
      '<div class="kt-wbx-card" style="padding:0;overflow:hidden;">' +
        '<div class="kt-wbx-section-head">' +
          '<span class="kt-wbx-section-title">' + _ico("list_alt") + 'Demand Items (' + rows.length + ')</span>' +
          (isEditable ? '<button class="kt-wbx-add-item-btn" data-action="edit_wizard" data-edit="1">' + _ico("add") + 'Add Item</button>' : '') +
        '</div>' +
        '<table class="kt-wbx-items-table">' +
          '<thead><tr><th>Description</th><th>Qty / Scope</th><th>Total Estimate</th></tr></thead>' +
          '<tbody>' + (itemRows || '<tr><td colspan="3" style="padding:16px;color:var(--wbx-on-muted);text-align:center">No items recorded</td></tr>') + '</tbody>' +
          '<tfoot class="kt-wbx-items-foot"><tr>' +
            '<td colspan="2" class="kt-wbx-items-total-label">Total Estimated Value</td>' +
            '<td class="kt-wbx-items-total-value">' + _esc(_fmt(totalAmt, cur)) + '</td>' +
          '</tr></tfoot>' +
        '</table>' +
      '</div>';

    // justification
    var benSummary = (a.beneficiary_summary || "").trim();
    var specSummary = (a.specification_summary || "").trim();
    var justBody = "";
    if (benSummary) {
      justBody += '<div class="kt-wbx-just-block"><div class="kt-wbx-just-label">Beneficiary Summary</div>' +
        '<div class="kt-wbx-just-text">' + _esc(benSummary) + '</div></div>';
    }
    if (specSummary) {
      justBody += '<div class="kt-wbx-just-block"><div class="kt-wbx-just-label">Specification / Scope</div>' +
        '<div class="kt-wbx-just-text">' + _esc(specSummary) + '</div></div>';
    }
    var justSection = justBody
      ? '<div class="kt-wbx-card" style="padding:0;overflow:hidden;">' +
          '<div class="kt-wbx-section-head"><span class="kt-wbx-section-title">' + _ico("fact_check") + 'Justification</span></div>' +
          '<div class="kt-wbx-just-body">' + justBody + '</div>' +
        '</div>'
      : '';

    // attachments
    var atts = attachments || [];
    var attItems = atts.map(function(f) {
      var ext = (f.name || "").split(".").pop().toLowerCase();
      var icon = (ext === "pdf") ? "picture_as_pdf" : (ext === "xlsx" || ext === "xls") ? "table_chart" : "attach_file";
      var sizeFmt = f.size ? _fmtFileSize(f.size) : "";
      var meta = (f.category ? f.category + (sizeFmt ? " \u2022 " + sizeFmt : "") : sizeFmt) || "";
      return (
        '<a class="kt-wbx-att-item" href="' + _esc(f.url || "#") + '" target="_blank">' +
          '<div class="kt-wbx-att-icon">' + _ico(icon) + '</div>' +
          '<div class="kt-wbx-att-info">' +
            '<div class="kt-wbx-att-name">' + _esc(f.name || "") + '</div>' +
            (meta ? '<div class="kt-wbx-att-meta">' + _esc(meta) + '</div>' : '') +
          '</div>' +
          '<div class="kt-wbx-att-dl">' + _ico("download") + '</div>' +
        '</a>'
      );
    }).join("");
    var attSection =
      '<div class="kt-wbx-card" style="padding:0;overflow:hidden;">' +
        '<div class="kt-wbx-section-head">' +
          '<span class="kt-wbx-section-title">' + _ico("attachment") + 'Attachments (' + atts.length + ')</span>' +
        '</div>' +
        (atts.length ? '<div class="kt-wbx-att-grid">' + attItems + '</div>'
          : '<div style="padding:16px;color:var(--wbx-on-muted);font-size:13px">No attachments uploaded.</div>') +
      '</div>';

    // strategic context
    var resStatus = (b.reservation_status || "").trim();
    var resChipCls = resStatus === "Reserved" ? "kt-wbx-res-chip--reserved"
                   : resStatus === "Released" ? "kt-wbx-res-chip--available"
                   : "kt-wbx-res-chip--none";
    var allocated = parseFloat(c.available_budget_at_check) || 0;
    var demanded  = parseFloat(c.total_amount) || 0;
    var pct = (allocated + demanded) > 0 ? Math.round(demanded / (allocated + demanded) * 100) : 90;

    // Budget Line row: show a "Link" action for Finance Reviewers when demand awaits finance approval
    var isPendingFinance = (a.status === "Pending Finance Approval");
    var budgetLineValue  = b.budget_line_label || b.budget_line;
    var budgetLineRowHtml;
    if (isPendingFinance) {
      budgetLineRowHtml =
        '<div class="kt-wbx-strategy-item-label">Budget Line</div>' +
        '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">' +
          '<div class="kt-wbx-strategy-item-value">' +
            (budgetLineValue ? _esc(budgetLineValue) : '<span style="color:var(--wbx-on-faint);font-style:italic">Not linked</span>') +
          '</div>' +
          '<button class="kt-wbx-budget-link-btn" data-action="link_budget_line" title="Link budget line">' +
            '<span class="material-symbols-outlined">link</span>' +
            (budgetLineValue ? 'Change' : 'Link') +
          '</button>' +
        '</div>';
    } else {
      budgetLineRowHtml =
        '<div class="kt-wbx-strategy-item-label">Budget Line</div>' +
        '<div class="kt-wbx-strategy-item-value">' + _esc(budgetLineValue || "\u2014") + '</div>';
    }

    var stratSection =
      '<div class="kt-wbx-strategy">' +
        '<div class="kt-wbx-strategy-head">Linked Strategic Context</div>' +
        '<div class="kt-wbx-strategy-items">' +
          '<div class="kt-wbx-strategy-row">' +
            '<div class="kt-wbx-strategy-icon">' + _ico("center_focus_strong") + '</div>' +
            '<div>' +
              '<div class="kt-wbx-strategy-item-label">Strategy Objective</div>' +
              '<div class="kt-wbx-strategy-item-value">' + _esc(b.strategic_plan_label || b.strategic_plan || "\u2014") + '</div>' +
              (b.program_label ? '<div style="font-size:12px;opacity:0.65;margin-top:2px">' + _esc(b.program_label) + '</div>' : '') +
            '</div>' +
          '</div>' +
          '<div class="kt-wbx-strategy-row">' +
            '<div class="kt-wbx-strategy-icon">' + _ico("account_balance_wallet") + '</div>' +
            '<div style="min-width:0;flex:1">' + budgetLineRowHtml + '</div>' +
          '</div>' +
          '<div class="kt-wbx-funding-block">' +
            '<div class="kt-wbx-funding-row">' +
              '<span class="kt-wbx-funding-label">Funding Status</span>' +
              (resStatus ? '<span class="kt-wbx-res-chip ' + resChipCls + '">' + _esc(resStatus) + '</span>' : '') +
            '</div>' +
            '<div class="kt-wbx-funding-amount">' + _esc(_fmt(demanded, cur)) + '</div>' +
            '<div class="kt-wbx-funding-bar"><div class="kt-wbx-funding-bar-fill" style="width:' + pct + '%"></div></div>' +
            '<div class="kt-wbx-funding-meta">' +
              (c.available_budget_at_check != null ? '<span>Available at check: ' + _esc(_fmt(c.available_budget_at_check, cur)) + '</span>' : '') +
              (c.reservation_reference ? '<span>Ref: ' + _esc(c.reservation_reference) + '</span>' : '') +
            '</div>' +
          '</div>' +
        '</div>' +
      '</div>';

    // timeline
    var tlSteps = _buildTimeline(detail, audit);
    var tlHtml = tlSteps.map(function(t) {
      var iconCls = t.state === "done" ? "kt-wbx-tl-icon--done" : t.state === "active" ? "kt-wbx-tl-icon--active" : "kt-wbx-tl-icon--locked";
      var icon    = t.state === "done" ? "check" : t.state === "active" ? "pending" : "lock";
      var dimCls  = t.state === "locked" ? " kt-wbx-tl-step--dim" : "";
      return (
        '<div class="kt-wbx-tl-step' + dimCls + '">' +
          '<div class="kt-wbx-tl-icon ' + iconCls + '">' + _ico(icon) + '</div>' +
          '<div class="kt-wbx-tl-body">' +
            '<div class="kt-wbx-tl-label">' + _esc(t.label) + '</div>' +
            (t.actor ? '<div class="kt-wbx-tl-actor">' + _esc(t.actor) + '</div>' : '') +
            (t.date ? '<div class="kt-wbx-tl-date">' + _esc(_fmtDate(t.date)) + '</div>' : '') +
            (t.state === "active" ? '<div class="kt-wbx-tl-badge">In Progress</div>' : '') +
            (t.note ? '<div class="kt-wbx-tl-note">' + _ico("info") + _esc(t.note) + '</div>' : '') +
          '</div>' +
        '</div>'
      );
    }).join("");
    var timelineSection =
      '<div class="kt-wbx-card" style="padding:0;overflow:hidden;">' +
        '<div class="kt-wbx-section-head"><span class="kt-wbx-section-title">' + _ico("timeline") + 'Approval Timeline</span></div>' +
        '<div class="kt-wbx-timeline-wrap"><div class="kt-wbx-timeline"><div class="kt-wbx-timeline-vline"></div>' + tlHtml + '</div></div>' +
      '</div>';

    // banner
    var bannerCfg = _bannerConfig(detail);
    var bannerSection = "";
    if (bannerCfg) {
      bannerSection =
        '<div class="kt-wbx-action-banner">' +
          '<p class="kt-wbx-action-banner-msg">' + _esc(bannerCfg.msg) + '</p>' +
          (bannerCfg.action
            ? '<button class="kt-wbx-action-banner-btn"' +
                (bannerCfg.action.id ? ' data-action="' + _esc(bannerCfg.action.id) + '"' : '') +
              '>' + _ico(bannerCfg.action.icon || "send") + _esc(bannerCfg.action.label) + '</button>'
            : '') +
        '</div>';
    }

    wrapper.innerHTML =
      '<div class="kt-wbx-canvas">' +
        '<div class="kt-wbx-nav">' +
          '<button class="kt-wbx-back" id="kt-wbx-back-btn">' + _ico("arrow_back") + 'Demand Hub</button>' +
          '<span class="kt-wbx-nav-sep">/</span>' +
          '<span class="kt-wbx-nav-crumb">' + _esc(a.title || "Demand") + '</span>' +
        '</div>' +
        '<div class="kt-wbx-main">' +
          '<div class="kt-wbx-header">' +
            '<div class="kt-wbx-title-row">' + titleBlock + actHtml + '</div>' +
          '</div>' +
          bento +
          '<div class="kt-wbx-body">' +
            '<div class="kt-wbx-left">' + itemsSection + justSection + attSection + '</div>' +
            '<div class="kt-wbx-right">' + stratSection + timelineSection + bannerSection + '</div>' +
          '</div>' +
        '</div>' +
      '</div>';

    _bindEvents(wrapper, detail);
  }

  // ── W5: Bind events ──────────────────────────────────────────────────────
  function _bindEvents(wrapper, detail) {
    var L = "kentender_procurement.demand_intake.api.lifecycle.";

    function _reload() {
      _state.detail = null;
      _state.audit  = null;
      _state.attachments = null;
      _renderSkeleton(wrapper);
      _loadAll(wrapper);
    }

    function _callLifecycle(method, args, cb) {
      _state.actionPending = true;
      frappe.call({
        method: method,
        args: args,
        callback: function(r) {
          _state.actionPending = false;
          if (r && r.message && r.message.status) {
            if (cb) cb(r.message);
            else _reload();
          }
        },
        error: function(r) {
          _state.actionPending = false;
          frappe.msgprint({
            title: "Action Failed",
            message: (r && r.message) ? r.message : "An error occurred. Please try again.",
            indicator: "red",
          });
        },
      });
    }

    // Guard: only bind the click listener once per wrapper instance.
    // _bindEvents is called on every demand load, so without this guard
    // multiple stale listeners accumulate and fire stale captured names.
    if (!wrapper.dataset.wbxEventsBound) {
      wrapper.dataset.wbxEventsBound = "1";

      wrapper.addEventListener("click", function(e) {
        // Always read _state.name at click time — never from a captured closure.
        var name = _state.name;
        var btn = e.target.closest("[data-action]");
        if (!btn) return;
        var action = btn.getAttribute("data-action");
        var method = btn.getAttribute("data-method");
        var reasonType = btn.getAttribute("data-reason");
        var clientAction = btn.getAttribute("data-client");

        // open_form — route editable (Draft/Rejected) demands back to the
        // Create Demand wizard; do NOT open the raw Frappe DocType form.
        // Non-editable "View demand" is redundant (user is already in the
        // workbench) so it is a no-op.
        if (action === "open_form" || clientAction === "open_form") {
          var isEdit = btn.getAttribute("data-edit") === "1";
          if (isEdit && frappe.set_route) {
            frappe.set_route("create-demand", name);
          }
          return;
        }

        // edit_wizard — "Add Item" button routes to Create Demand wizard step 2
        if (action === "edit_wizard") {
          if (frappe.set_route) frappe.set_route("create-demand", name);
          return;
        }

        // link_budget_line — Finance Reviewer links a budget line
        if (action === "link_budget_line") {
          var lbl = (_state.detail && _state.detail.b) ? _state.detail.b.budget_line : null;
          _showBudgetLinePicker(name, lbl, function() { _reload(); });
          return;
        }

        // Banner actions without a dedicated button method
        if (action === "return_approved_to_finance") {
          var ratfDetail = _state.detail || {};
          var ratfA = ratfDetail.a || {};
          _showPromptDialog({
            icon: "reply",
            iconClass: "kt-wbx-dlg-icon--warning",
            title: "Send Back to Finance",
            subtitle: "Return for budget re-review",
            desc: "Describe why this demand needs to be returned to the Finance Officer before it can be approved.",
            contextRows: [
              { label: "Demand", value: ratfA.title || name },
              { label: "Reference", value: name },
            ],
            fieldLabel: "Reason for return",
            fieldPlaceholder: "e.g. Budget allocation needs correction…",
            confirmLabel: "Send Back",
            confirmClass: "kt-wbx-dlg-btn--primary",
            confirmIcon: "reply",
          }, function(val) {
            _callLifecycle(L + "return_approved_to_finance", { demand_name: name, reason: val });
          });
          return;
        }
        if (action === "mark_planning_ready") {
          var mprDetail = _state.detail || {};
          var mprA = mprDetail.a || {};
          _showConfirmDialog({
            icon: "checklist",
            iconClass: "kt-wbx-dlg-icon--success",
            title: "Mark as Planning Ready",
            subtitle: "Advance to procurement planning",
            desc: "Confirm this demand has passed departmental review and is ready to be incorporated into the procurement plan.",
            contextRows: [
              { label: "Demand", value: mprA.title || name },
              { label: "Reference", value: name },
            ],
            confirmLabel: "Mark Ready",
            confirmClass: "kt-wbx-dlg-btn--success",
            confirmIcon: "task_alt",
          }, function() {
            _callLifecycle(L + "mark_planning_ready", { demand_name: name });
          });
          return;
        }

        if (!method) return;

        // Prompt-based actions
        if (reasonType === "return") {
          var retDetail = _state.detail || {};
          var retA = retDetail.a || {};
          _showPromptDialog({
            icon: "undo",
            iconClass: "kt-wbx-dlg-icon--warning",
            title: "Return for Correction",
            subtitle: "Send demand back to the requester",
            desc: "Explain what needs to be corrected. The requester will see this reason and can resubmit after making changes.",
            contextRows: [
              { label: "Demand", value: retA.title || name },
              { label: "Reference", value: name },
            ],
            fieldLabel: "Reason for return",
            fieldPlaceholder: "e.g. Items list needs updating…",
            confirmLabel: "Return",
            confirmClass: "kt-wbx-dlg-btn--primary",
            confirmIcon: "undo",
          }, function(val) {
            _callLifecycle(method, { demand_name: name, reason: val }, _reload);
          });
          return;
        }
        if (reasonType === "rejection") {
          var rejDetail = _state.detail || {};
          var rejA = rejDetail.a || {};
          _showPromptDialog({
            icon: "cancel",
            iconClass: "kt-wbx-dlg-icon--danger",
            title: "Reject Demand",
            subtitle: "Permanently reject this demand",
            desc: "Provide a clear rejection reason. The requester will be notified and the demand will be closed.",
            contextRows: [
              { label: "Demand", value: rejA.title || name },
              { label: "Reference", value: name },
            ],
            fieldLabel: "Rejection reason",
            fieldPlaceholder: "e.g. Out of scope for this financial year…",
            confirmLabel: "Reject",
            confirmClass: "kt-wbx-dlg-btn--danger",
            confirmIcon: "cancel",
          }, function(val) {
            _callLifecycle(method, { demand_name: name, rejection_reason: val }, _reload);
          });
          return;
        }
        if (reasonType === "cancellation") {
          var canDetail = _state.detail || {};
          var canA = canDetail.a || {};
          _showPromptDialog({
            icon: "block",
            iconClass: "kt-wbx-dlg-icon--danger",
            title: "Cancel Demand",
            subtitle: "Cancel this demand",
            desc: "State the reason this demand is being cancelled. This action cannot be undone.",
            contextRows: [
              { label: "Demand", value: canA.title || name },
              { label: "Reference", value: name },
            ],
            fieldLabel: "Cancellation reason",
            fieldPlaceholder: "e.g. Requirements have changed…",
            confirmLabel: "Cancel Demand",
            confirmClass: "kt-wbx-dlg-btn--danger",
            confirmIcon: "block",
          }, function(val) {
            _callLifecycle(method, { demand_name: name, reason: val }, _reload);
          });
          return;
        }

        // Confirm-based actions
        if (action === "approve_finance") {
          var afDetail = _state.detail || {};
          var afA = afDetail.a || {};
          var afB = afDetail.b || {};
          var afC = afDetail.c || {};
          var afCur = afDetail.currency || "KES";

          // Guard: budget line must be linked before approval
          if (!afB.budget_line) {
            _showConfirmDialog({
              icon: "account_balance_wallet",
              iconClass: "kt-wbx-dlg-icon--warning",
              title: "Budget Line Required",
              subtitle: "Cannot approve without a budget line",
              desc: "A Budget Line must be linked to this demand before you can approve and reserve funds. Please link a budget line first.",
              contextRows: [
                { label: "Demand", value: afA.title || name },
                { label: "Reference", value: name },
              ],
              confirmLabel: "Link Budget Line",
              confirmClass: "kt-wbx-dlg-btn--primary",
              confirmIcon: "link",
              cancelLabel: "Dismiss",
            }, function() {
              _showBudgetLinePicker(name, null, function() { _reload(); });
            });
            return;
          }

          _showConfirmDialog({
            icon: "savings",
            iconClass: "kt-wbx-dlg-icon--success",
            title: "Approve & Reserve Budget",
            subtitle: "Finance approval",
            desc: "Approving this demand will lock a budget reservation for the estimated amount. The funds will be earmarked until the demand is fulfilled or cancelled.",
            contextRows: [
              { label: "Demand", value: afA.title || name },
              { label: "Reference", value: name },
              { label: "Budget Line", value: afB.budget_line_label || afB.budget_line },
              { label: "Amount", value: _fmt(afC.total_amount, afCur), amount: true },
            ],
            alertText: "Once approved, the reserved funds will reduce available budget until this demand is closed.",
            confirmLabel: "Approve & Reserve",
            confirmClass: "kt-wbx-dlg-btn--success",
            confirmIcon: "lock",
          }, function() {
            _callLifecycle(method, { demand_name: name }, _reload);
          });
          return;
        }

        // Direct actions (submit, approve_hod)
        _callLifecycle(method, { demand_name: name }, _reload);
      });

      var backBtn = wrapper.querySelector("#kt-wbx-back-btn");
      if (backBtn) backBtn.addEventListener("click", function() { frappe.set_route("demand-hub"); });
    }
  }

  // ── W8: Robust route parsing ─────────────────────────────────────────────
  function _demandFromRoute() {
    try {
      var route = frappe.get_route ? frappe.get_route() : [];
      if (Array.isArray(route) && route[1]) return String(route[1]).trim();
    } catch (e) {}
    // fallback: parse from pathname or hash
    var paths = [window.location.pathname, window.location.hash];
    for (var i = 0; i < paths.length; i++) {
      var m = paths[i].match(/demand-workbench\/([^/?#]+)/);
      if (m && m[1]) return decodeURIComponent(m[1]).trim();
    }
    return null;
  }

  // ── W1: Load all data (3 parallel frappe.call) ───────────────────────────
  function _loadAll(wrapper) {
    var name = _state.name;
    var received = 0;
    var total = 3;

    function _tryRender() {
      received += 1;
      if (received < total) return;
      // All three responses received
      if (_state.loadError) {
        _renderError(wrapper, _state.loadError.msg, _state.loadError.code);
        return;
      }
      _renderPage(wrapper, _state.detail, _state.audit, _state.attachments);
    }

    // 1 — detail
    frappe.call({
      method: "kentender_procurement.demand_intake.api.dia_detail.get_dia_demand_detail",
      args: { name: name },
      callback: function(r) {
        var msg = r && r.message ? r.message : {};
        if (!msg.ok) {
          _state.loadError = { msg: msg.message || "Could not load demand.", code: msg.error_code };
        } else {
          _state.detail = msg;
        }
        _tryRender();
      },
      error: function() {
        _state.loadError = { msg: "Network error loading demand.", code: "NETWORK_ERROR" };
        _tryRender();
      },
    });

    // 2 — audit
    frappe.call({
      method: "kentender_procurement.demand_intake.api.audit.get_demand_audit_data",
      args: { demand_name: name },
      callback: function(r) {
        _state.audit = (r && r.message) ? r.message : {};
        _tryRender();
      },
      error: function() {
        _state.audit = {};
        _tryRender();
      },
    });

    // 3 — attachments
    frappe.call({
      method: "kentender_procurement.demand_intake.api.dia_detail.get_demand_attachments",
      args: { demand_name: name },
      callback: function(r) {
        var msg = r && r.message ? r.message : {};
        _state.attachments = msg.ok ? (msg.attachments || []) : [];
        _tryRender();
      },
      error: function() {
        _state.attachments = [];
        _tryRender();
      },
    });
  }

  // ── Frappe page registration ─────────────────────────────────────────────
  frappe.pages["demand-workbench"].on_page_load = function (wrapper) {
    _ensureFonts();
    _state._wrapper = wrapper;
  };

  frappe.pages["demand-workbench"].on_page_show = function (wrapper) {
    document.body.classList.add("kt-wbx-shell");

    setTimeout(function () {
      if (frappe.app && frappe.app.sidebar && typeof frappe.app.sidebar.setup === "function") {
        frappe.app.sidebar.setup("Procurement");
      }
    }, 0);

    var name = _demandFromRoute();
    _state._wrapper = wrapper;

    if (!name) {
      _renderError(wrapper, "No demand specified in route.", "MISSING_NAME");
      return;
    }

    // Re-render if demand changed or data is stale
    if (name !== _state.name || (!_state.detail && !_state.actionPending)) {
      _state.name        = name;
      _state.detail      = null;
      _state.audit       = null;
      _state.attachments = null;
      _state.loadError   = null;
      _state.actionPending = false;
      _renderSkeleton(wrapper);
      _loadAll(wrapper);
    }
  };

  frappe.pages["demand-workbench"].on_page_hide = function () {
    document.body.classList.remove("kt-wbx-shell");
  };

})();
