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
          (isEditable ? '<button class="kt-wbx-add-item-btn" data-action="open_form" data-edit="1">' + _ico("add") + 'Add Item</button>' : '') +
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
            '<div>' +
              '<div class="kt-wbx-strategy-item-label">Budget Line</div>' +
              '<div class="kt-wbx-strategy-item-value">' + _esc(b.budget_line_label || b.budget_line || "\u2014") + '</div>' +
            '</div>' +
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
    var name = _state.name;
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

    wrapper.addEventListener("click", function(e) {
      var btn = e.target.closest("[data-action]");
      if (!btn) return;
      var action = btn.getAttribute("data-action");
      var method = btn.getAttribute("data-method");
      var reasonType = btn.getAttribute("data-reason");
      var clientAction = btn.getAttribute("data-client");

      // open_form / Add Item
      if (action === "open_form" || clientAction === "open_form") {
        frappe.set_route("Form", "Demand", name);
        return;
      }

      // Banner actions without a dedicated button method
      if (action === "return_approved_to_finance") {
        frappe.prompt(
          [{ label: "Reason", fieldname: "reason", fieldtype: "Small Text", reqd: 1 }],
          function(vals) { _callLifecycle(L + "return_approved_to_finance", { demand_name: name, reason: vals.reason }); },
          "Send back to Finance", "Submit"
        );
        return;
      }
      if (action === "mark_planning_ready") {
        frappe.confirm("Confirm this demand is ready for planning?", function() {
          _callLifecycle(L + "mark_planning_ready", { demand_name: name });
        });
        return;
      }

      if (!method) return;

      // Prompt-based actions
      if (reasonType === "return") {
        frappe.prompt(
          [{ label: "Reason for return", fieldname: "reason", fieldtype: "Small Text", reqd: 1 }],
          function(vals) { _callLifecycle(method, { demand_name: name, reason: vals.reason }, _reload); },
          "Return for Correction", "Submit"
        );
        return;
      }
      if (reasonType === "rejection") {
        frappe.prompt(
          [{ label: "Rejection reason", fieldname: "reason", fieldtype: "Small Text", reqd: 1 }],
          function(vals) { _callLifecycle(method, { demand_name: name, rejection_reason: vals.reason }, _reload); },
          "Reject Demand", "Reject"
        );
        return;
      }
      if (reasonType === "cancellation") {
        frappe.prompt(
          [{ label: "Cancellation reason", fieldname: "reason", fieldtype: "Small Text", reqd: 1 }],
          function(vals) { _callLifecycle(method, { demand_name: name, reason: vals.reason }, _reload); },
          "Cancel Demand", "Confirm"
        );
        return;
      }

      // Confirm-based actions
      if (action === "approve_finance") {
        frappe.confirm(
          "Approve this demand and reserve the budget?",
          function() { _callLifecycle(method, { demand_name: name }, _reload); }
        );
        return;
      }

      // Direct actions (submit, approve_hod)
      _callLifecycle(method, { demand_name: name }, _reload);
    });

    var backBtn = wrapper.querySelector("#kt-wbx-back-btn");
    if (backBtn) backBtn.addEventListener("click", function() { frappe.set_route("demand-hub"); });
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
        frappe.app.sidebar.setup("Demand Intake and Approval");
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
