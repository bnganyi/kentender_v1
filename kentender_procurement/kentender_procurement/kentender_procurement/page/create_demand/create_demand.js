/* ── Create Demand Wizard — Backend Wired ───────────────────────────────── */
/* 4-step wizard: Describe → Items → Review → Success                       */
/* API: save_demand_draft (create/update) + submit_demand (lifecycle)        */

(function () {
  "use strict";

  // ── Font loader ──────────────────────────────────────────────────────────
  function _ensureFonts() {
    if (document.getElementById("kt-cd-fonts")) return;
    var link = document.createElement("link");
    link.id = "kt-cd-fonts";
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
    step: 1,
    // Step 1 form values (preserved across back navigation)
    form1: {
      title: "",
      dept: "",
      category: "",
      priority: false,
      justification: "",
      entity: "",
      requiredBy: "",
    },
    // Step 2 items: [{ desc, qty, unitPrice }]
    items: [],
    // Backend refs
    demandName: null,
    demandId: null,
    // Loading guards
    saving: false,
    submitting: false,
    // Submission readiness from backend
    readiness: null,
    // Live meta for dropdowns
    departments: [],
    procuringEntities: [],
    _wrapper: null,
  };

  // ── Format / escape helpers ──────────────────────────────────────────────
  function _esc(s) {
    return String(s || "")
      .replace(/&/g, "&amp;").replace(/</g, "&lt;")
      .replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  }
  function _ico(name, fill) {
    var s = fill ? ' style="font-variation-settings:\'FILL\' 1"' : "";
    return '<span class="material-symbols-outlined"' + s + ">" + name + "</span>";
  }
  function _fmt(n) {
    return Number(n || 0).toLocaleString("en-KE", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
  function _calcTotal() {
    return _state.items.reduce(function (s, it) {
      return s + (parseFloat(it.qty) || 0) * (parseFloat(it.unitPrice) || 0);
    }, 0);
  }

  // ── Stepper HTML ─────────────────────────────────────────────────────────
  function _stepper(current) {
    var labels = ["Describe Need", "Add Items", "Review & Submit"];
    var html = '<div class="kt-cd-stepper">';
    for (var i = 0; i < 3; i++) {
      var num = i + 1;
      var isDone = num < current;
      var isActive = num === current;
      var dotCls = isDone
        ? "kt-cd-step-dot--done"
        : isActive
        ? "kt-cd-step-dot--active"
        : "kt-cd-step-dot--inactive";
      var lblCls = isDone
        ? "kt-cd-step-label--done"
        : isActive
        ? "kt-cd-step-label--active"
        : "kt-cd-step-label--inactive";
      var itemCls = !isDone && !isActive ? " kt-cd-step-item--inactive" : "";
      html +=
        '<div class="kt-cd-step-item' +
        itemCls +
        '">' +
        '<div class="kt-cd-step-dot ' +
        dotCls +
        '">' +
        (isDone ? _ico("check") : num) +
        "</div>" +
        '<span class="kt-cd-step-label ' +
        lblCls +
        '">' +
        _esc(labels[i]) +
        "</span>" +
        "</div>";
      if (i < 2) {
        var lineCls = isDone ? "kt-cd-step-line--done" : "";
        html += '<div class="kt-cd-step-line ' + lineCls + '"></div>';
      }
    }
    html += "</div>";
    return html;
  }

  // ── Dropdown option builders ─────────────────────────────────────────────
  function _deptOptions() {
    if (!_state.departments.length) {
      return '<option value="">Loading departments...</option>';
    }
    var html = '<option value="">Select Department...</option>';
    _state.departments.forEach(function (d) {
      var val = d.value || d.name || d;
      var lbl = d.label || val;
      var sel = val === _state.form1.dept ? " selected" : "";
      html += '<option value="' + _esc(val) + '"' + sel + ">" + _esc(lbl) + "</option>";
    });
    return html;
  }

  function _entityOptions() {
    if (!_state.procuringEntities.length) {
      return '<option value="">Loading entities...</option>';
    }
    var html = '<option value="">Select Procuring Entity...</option>';
    _state.procuringEntities.forEach(function (e) {
      var sel = e === _state.form1.entity ? " selected" : "";
      html += '<option value="' + _esc(e) + '"' + sel + ">" + _esc(e) + "</option>";
    });
    return html;
  }

  function _categoryOptions() {
    var cats = ["Goods", "Works", "Services", "Consultancy"];
    var html = '<option value="">Select Category...</option>';
    cats.forEach(function (c) {
      var sel = c === _state.form1.category ? " selected" : "";
      html += '<option value="' + c + '"' + sel + ">" + c + "</option>";
    });
    return html;
  }

  // ── STEP 1 HTML ──────────────────────────────────────────────────────────
  function _renderStep1() {
    var charCount = (_state.form1.justification || "").length;
    return (
      '<div class="kt-cd-canvas">' +
        '<nav class="kt-cd-breadcrumb">' +
          '<span>Workbench</span>' + _ico("chevron_right") +
          '<span class="kt-cd-breadcrumb-active">Create New Demand</span>' +
        "</nav>" +
        '<h2 class="kt-cd-page-title">Initiate Demand Request</h2>' +
        '<p class="kt-cd-page-sub">Formalize your department\'s needs. Provide clear context to help Finance and Procurement reviewers understand the strategic value of this request.</p>' +

        _stepper(1) +

        '<div class="kt-cd-card">' +
          '<div class="kt-cd-card-head">' +
            '<span class="kt-cd-card-head-title">Step 1: Primary Need Details</span>' +
            (_state.demandName
              ? '<div class="kt-cd-autosave-chip"><div class="kt-cd-autosave-dot"></div>DRAFT SAVED</div>'
              : "") +
          "</div>" +
          '<div class="kt-cd-card-body">' +
            '<form class="kt-cd-form" id="kt-cd-form-1" onsubmit="return false">' +

              '<div class="kt-cd-grid-2">' +
                // title (full width)
                '<div class="kt-cd-full-col">' +
                  '<label class="kt-cd-field-label">Demand Title <span style="color:var(--kt-red,#ef4444)">*</span></label>' +
                  '<input class="kt-cd-input" type="text" id="kt-cd-title"' +
                    ' placeholder="e.g., Annual Hospital Infrastructure Renovation - Block B"' +
                    ' value="' + _esc(_state.form1.title) + '"/>' +
                  '<p class="kt-cd-input-hint">Enter a clear, descriptive name for audit and planning purposes.</p>' +
                "</div>" +

                // department
                '<div>' +
                  '<label class="kt-cd-field-label">Requesting Department</label>' +
                  '<div class="kt-cd-select-wrap">' +
                    '<select class="kt-cd-select" id="kt-cd-dept">' +
                      _deptOptions() +
                    "</select>" +
                    _ico("expand_more") +
                  "</div>" +
                "</div>" +

                // category
                '<div>' +
                  '<label class="kt-cd-field-label">Procurement Category</label>' +
                  '<div class="kt-cd-select-wrap">' +
                    '<select class="kt-cd-select" id="kt-cd-category">' +
                      _categoryOptions() +
                    "</select>" +
                    _ico("expand_more") +
                  "</div>" +
                "</div>" +

                // procuring entity
                '<div>' +
                  '<label class="kt-cd-field-label">Procuring Entity <span style="color:var(--kt-red,#ef4444)">*</span></label>' +
                  '<div class="kt-cd-select-wrap">' +
                    '<select class="kt-cd-select" id="kt-cd-entity">' +
                      _entityOptions() +
                    "</select>" +
                    _ico("expand_more") +
                  "</div>" +
                "</div>" +

                // required by date
                '<div>' +
                  '<label class="kt-cd-field-label">Required By Date <span style="color:var(--kt-red,#ef4444)">*</span></label>' +
                  '<input class="kt-cd-input" type="date" id="kt-cd-required-by"' +
                    ' value="' + _esc(_state.form1.requiredBy) + '"/>' +
                  '<p class="kt-cd-input-hint">When does your department need this procured by?</p>' +
                "</div>" +

              "</div>" +

              // priority toggle
              '<div class="kt-cd-priority-block">' +
                '<div class="kt-cd-priority-text">' +
                  "<h4>Mark as High Priority?</h4>" +
                  "<p>Emergency or High-priority demands require additional justification and may trigger expedited approval paths.</p>" +
                "</div>" +
                '<div class="kt-cd-toggle-row">' +
                  '<span class="kt-cd-toggle-lbl">Normal</span>' +
                  '<label class="kt-cd-toggle-switch">' +
                    '<input type="checkbox" id="kt-cd-priority"' +
                    (_state.form1.priority ? " checked" : "") +
                    ">" +
                    '<span class="kt-cd-toggle-slider"></span>' +
                  "</label>" +
                  '<span class="kt-cd-toggle-lbl kt-cd-toggle-lbl--high">High</span>' +
                "</div>" +
              "</div>" +

              // justification
              "<div>" +
                '<label class="kt-cd-field-label">Business Justification</label>' +
                '<textarea class="kt-cd-textarea" id="kt-cd-justify" rows="5" ' +
                  'placeholder="Detail why this procurement is necessary. Reference specific departmental targets, strategic needs, or current deficiencies...">' +
                  _esc(_state.form1.justification) +
                "</textarea>" +
                '<div class="kt-cd-char-row">' +
                  "<span>Minimum 100 characters recommended</span>" +
                  '<span id="kt-cd-char-count">' + charCount + " / 2000</span>" +
                "</div>" +
              "</div>" +

            "</form>" +
          "</div>" +
          '<div class="kt-cd-card-foot">' +
            '<button class="kt-cd-btn kt-cd-btn--ghost" id="kt-cd-discard">' +
              _ico("close") + "Discard Draft" +
            "</button>" +
            '<button class="kt-cd-btn kt-cd-btn--primary" id="kt-cd-next-1"' +
              (_state.saving ? " disabled" : "") + ">" +
              (_state.saving
                ? _ico("hourglass_empty") + "Saving..."
                : "Next: Add Items " + _ico("arrow_forward")) +
            "</button>" +
          "</div>" +
        "</div>" +

        '<div class="kt-cd-guidance">' +
          '<div class="kt-cd-guidance-bg-icon">' + _ico("description", true) + "</div>" +
          '<div class="kt-cd-guidance-text">' +
            "<h5>Guidance: Describing the Need</h5>" +
            "<p>The Department Approver needs to understand the \"Why\" before they look at the \"What\". Ensure your justification aligns with the current fiscal year's strategic goals. You don't need to worry about budget lines yet—Finance will handle the coding in the next phase.</p>" +
          "</div>" +
        "</div>" +
      "</div>"
    );
  }

  // ── STEP 2 HTML ──────────────────────────────────────────────────────────
  function _itemRows() {
    return _state.items
      .map(function (it, idx) {
        var n = String(idx + 1).padStart(2, "0");
        var lineTotal = (parseFloat(it.qty) || 0) * (parseFloat(it.unitPrice) || 0);
        return (
          "<tr>" +
            '<td><span class="kt-cd-tbl-num">' + n + "</span></td>" +
            '<td><input class="kt-cd-tbl-input" type="text" data-row="' + idx + '" data-col="desc" value="' + _esc(it.desc) + '"/></td>' +
            '<td><input class="kt-cd-tbl-input" type="number" data-row="' + idx + '" data-col="qty" value="' + (it.qty || 0) + '"/></td>' +
            '<td><input class="kt-cd-tbl-input mono" type="number" step="0.01" data-row="' + idx + '" data-col="unitPrice" value="' + (it.unitPrice || 0) + '"/></td>' +
            '<td class="right"><span class="kt-cd-tbl-total">' + _fmt(lineTotal) + "</span></td>" +
            '<td class="right"><button class="kt-cd-del-btn" data-del="' + idx + '">' + _ico("delete") + "</button></td>" +
          "</tr>"
        );
      })
      .join("");
  }

  function _renderStep2() {
    var total = _calcTotal();
    var titleDisplay = _state.form1.title || "New Demand";
    return (
      '<div class="kt-cd-canvas">' +
        '<nav class="kt-cd-breadcrumb">' +
          "<span>Workbench</span>" + _ico("chevron_right") +
          "<span>New Demand</span>" + _ico("chevron_right") +
          '<span class="kt-cd-breadcrumb-active">Add Items</span>' +
        "</nav>" +
        '<h2 class="kt-cd-page-title">Create Procurement Demand</h2>' +
        '<p class="kt-cd-page-sub" style="margin-bottom:24px">Project: ' + _esc(titleDisplay) + "</p>" +

        _stepper(2) +

        '<div class="kt-cd-items-card">' +
          '<div class="kt-cd-items-head">' +
            '<div class="kt-cd-items-head-text"><h3>Demand Items</h3><p>List all required goods or services for this demand.</p></div>' +
            '<button class="kt-cd-btn kt-cd-btn--outline-primary" id="kt-cd-add-row">' +
              _ico("add") + "Add New Row" +
            "</button>" +
          "</div>" +
          '<div class="kt-cd-table-wrap">' +
            '<table class="kt-cd-items-table">' +
              "<thead><tr>" +
                '<th style="width:48px">#</th>' +
                "<th>Item Description</th>" +
                '<th style="width:100px">Qty</th>' +
                '<th style="width:160px">Unit Price (KES)</th>' +
                '<th style="width:160px" class="right">Total Est.</th>' +
                '<th style="width:48px"></th>' +
              "</tr></thead>" +
              '<tbody id="kt-cd-items-body">' +
                _itemRows() +
                // new row entry
                '<tr class="kt-cd-new-row">' +
                  '<td><span class="kt-cd-tbl-num">0' + (_state.items.length + 1) + "</span></td>" +
                  '<td><input class="kt-cd-new-row-input" type="text" id="kt-cd-new-desc" placeholder="Add next item description..."/></td>' +
                  '<td><input class="kt-cd-new-row-input" type="number" id="kt-cd-new-qty" placeholder="0"/></td>' +
                  '<td><input class="kt-cd-new-row-input mono" type="number" step="0.01" id="kt-cd-new-unit" placeholder="0.00"/></td>' +
                  '<td class="right"><span class="kt-cd-tbl-zero">0.00</span></td>' +
                  '<td class="right"><button class="kt-cd-save-btn" id="kt-cd-save-row">' + _ico("save") + "</button></td>" +
                "</tr>" +
              "</tbody>" +
            "</table>" +
          "</div>" +
          '<div class="kt-cd-items-summary">' +
            '<div class="kt-cd-total-block">' +
              '<div class="kt-cd-total-label">Total Estimated Value</div>' +
              '<div class="kt-cd-total-value">KES ' + _fmt(total) + "</div>" +
            "</div>" +
          "</div>" +
        "</div>" +

        '<div class="kt-cd-nav-row">' +
          '<button class="kt-cd-btn kt-cd-btn--ghost" id="kt-cd-back-2">' +
            _ico("arrow_back") + "Back to Need Details" +
          "</button>" +
          '<div class="kt-cd-nav-right">' +
            '<button class="kt-cd-btn kt-cd-btn--primary" id="kt-cd-next-2"' +
              (_state.saving ? " disabled" : "") + ">" +
              (_state.saving
                ? _ico("hourglass_empty") + "Saving..."
                : "Next: Review &amp; Submit " + _ico("arrow_forward")) +
            "</button>" +
          "</div>" +
        "</div>" +
      "</div>"
    );
  }

  // ── STEP 3 HTML ──────────────────────────────────────────────────────────
  function _reviewItemRows() {
    if (!_state.items.length) {
      return '<tr><td colspan="4" style="text-align:center;color:var(--kt-text-muted)">No items added</td></tr>';
    }
    return _state.items
      .map(function (it) {
        var lineTotal = (parseFloat(it.qty) || 0) * (parseFloat(it.unitPrice) || 0);
        return (
          "<tr>" +
            '<td><div class="kt-cd-review-item-name">' + _esc(it.desc) + "</div></td>" +
            '<td class="right"><span class="kt-cd-review-mono">' + (it.qty || 0) + "</span></td>" +
            '<td class="right"><span class="kt-cd-review-mono">KES ' + _fmt(it.unitPrice) + "</span></td>" +
            '<td class="right"><span class="kt-cd-review-mono-bold">KES ' + _fmt(lineTotal) + "</span></td>" +
          "</tr>"
        );
      })
      .join("");
  }

  function _readinessPanel() {
    if (!_state.readiness) {
      return (
        '<div class="kt-cd-funding-ok" style="color:var(--kt-text-muted)">' +
          _ico("hourglass_empty") +
          "<p>Loading readiness checks...</p>" +
        "</div>"
      );
    }
    var checks = _state.readiness.checks || [];
    var ready = _state.readiness.ready;
    var rows = checks
      .map(function (c) {
        var icon = c.ok ? _ico("check_circle") : _ico("cancel");
        var color = c.ok ? "var(--kt-green,#10B981)" : "var(--kt-red,#ef4444)";
        return (
          '<div class="kt-cd-funding-row" style="gap:8px;align-items:center">' +
            '<span style="color:' + color + ';display:flex">' + icon + "</span>" +
            "<span>" + _esc(c.label || c.id) + "</span>" +
          "</div>"
        );
      })
      .join("");

    return (
      '<div class="kt-cd-funding-head">' +
        _ico("checklist") + "<h3>Submission Readiness</h3>" +
      "</div>" +
      rows +
      (ready
        ? '<div class="kt-cd-funding-ok" style="margin-top:12px">' +
            _ico("check_circle") +
            "<p>All checks passed. Ready to submit for approval.</p>" +
          "</div>"
        : '<div style="margin-top:12px;padding:10px 12px;background:var(--kt-red-bg,#fef2f2);border-radius:6px;color:var(--kt-red,#ef4444);font-size:13px">' +
            "Please resolve the issues above before submitting." +
          "</div>")
    );
  }

  function _renderStep3() {
    var total = _calcTotal();
    var f = _state.form1;
    var readyToSubmit = _state.readiness ? _state.readiness.ready : false;

    return (
      '<div class="kt-cd-canvas">' +
        '<h2 class="kt-cd-page-title">Review &amp; Submit Demand</h2>' +
        '<p class="kt-cd-page-sub">Verify the procurement details before finalizing the strategic demand.</p>' +
        _stepper(3) +

        '<div class="kt-cd-review-layout">' +
          // left column
          '<div class="kt-cd-review-left">' +
            // general info card
            '<div class="kt-cd-review-card">' +
              '<div class="kt-cd-review-card-head">' +
                "<div>" +
                  '<div class="kt-cd-review-meta-label">General Information</div>' +
                  '<h2 class="kt-cd-review-card-title">Demand Particulars</h2>' +
                "</div>" +
                '<button class="kt-cd-edit-link" id="kt-cd-edit-1">' + _ico("edit") + " EDIT</button>" +
              "</div>" +
              '<div class="kt-cd-review-grid">' +
                "<div><div class=\"kt-cd-review-field-label\">Demand Title</div><div class=\"kt-cd-review-field-value\">" + _esc(f.title) + "</div></div>" +
                "<div><div class=\"kt-cd-review-field-label\">Department</div><div class=\"kt-cd-review-field-value\">" + _esc(f.dept || "—") + "</div></div>" +
                "<div><div class=\"kt-cd-review-field-label\">Category</div>" +
                  '<div class="kt-cd-review-cat-row">' + _ico("category") + "<span>" + _esc(f.category || "—") + "</span></div>" +
                "</div>" +
                "<div><div class=\"kt-cd-review-field-label\">Procuring Entity</div><div class=\"kt-cd-review-field-value\">" + _esc(f.entity || "—") + "</div></div>" +
                "<div><div class=\"kt-cd-review-field-label\">Required By</div><div class=\"kt-cd-review-field-value\">" + _esc(f.requiredBy || "—") + "</div></div>" +
                "<div><div class=\"kt-cd-review-field-label\">Priority</div><div class=\"kt-cd-review-field-value\">" + (f.priority ? "High" : "Normal") + "</div></div>" +
                (f.justification
                  ? '<div class="kt-cd-full"><div class="kt-cd-review-field-label">Justification</div>' +
                    '<div class="kt-cd-review-field-body">' + _esc(f.justification) + "</div></div>"
                  : "") +
              "</div>" +
            "</div>" +

            // itemized list card
            '<div class="kt-cd-review-card">' +
              '<div class="kt-cd-review-card-head">' +
                "<div>" +
                  '<div class="kt-cd-review-meta-label">Resource Allocation</div>' +
                  '<h2 class="kt-cd-review-card-title">Itemized List</h2>' +
                "</div>" +
                '<button class="kt-cd-edit-link" id="kt-cd-edit-2">' + _ico("edit") + " EDIT</button>" +
              "</div>" +
              '<div class="kt-cd-table-wrap">' +
                '<table class="kt-cd-review-table">' +
                  "<thead><tr>" +
                    "<th>Item Description</th>" +
                    '<th class="right">Qty</th>' +
                    '<th class="right">Unit Price</th>' +
                    '<th class="right">Total Estimate</th>' +
                  "</tr></thead>" +
                  "<tbody>" + _reviewItemRows() + "</tbody>" +
                "</table>" +
              "</div>" +
            "</div>" +
          "</div>" +

          // right column
          '<div class="kt-cd-review-right">' +
            // financial summary
            '<div class="kt-cd-financial-card">' +
              '<div class="kt-cd-financial-card-bg"></div>' +
              '<div class="kt-cd-financial-label">Total Estimated Value</div>' +
              '<div class="kt-cd-financial-amount">KES ' + _fmt(total) + "</div>" +
              '<div class="kt-cd-financial-rows">' +
                '<div class="kt-cd-financial-row"><span>Subtotal</span><span>KES ' + _fmt(total) + "</span></div>" +
                '<div class="kt-cd-financial-row kt-cd-financial-divider"><span>VAT / Tax</span><span>Assessed by Finance</span></div>' +
              "</div>" +
            "</div>" +

            // readiness / funding check
            '<div class="kt-cd-funding-card" id="kt-cd-readiness-panel">' +
              _readinessPanel() +
            "</div>" +
          "</div>" +
        "</div>" +

        // sticky footer
        '<div class="kt-cd-sticky-foot">' +
          '<button class="kt-cd-btn kt-cd-btn--ghost" id="kt-cd-back-3">' +
            _ico("arrow_back") + "Back to Items" +
          "</button>" +
          '<div class="kt-cd-sticky-foot-right">' +
            '<button class="kt-cd-btn kt-cd-btn--submit" id="kt-cd-submit"' +
              (!readyToSubmit || _state.submitting ? " disabled" : "") + ">" +
              (_state.submitting
                ? _ico("hourglass_empty") + "Submitting..."
                : "SUBMIT DEMAND " + _ico("send")) +
            "</button>" +
          "</div>" +
        "</div>" +
      "</div>" +

      // processing overlay
      '<div class="kt-cd-overlay" id="kt-cd-overlay">' +
        '<div class="kt-cd-overlay-card">' +
          '<div id="kt-cd-overlay-loading">' +
            '<div class="kt-cd-spinner"></div>' +
            '<div class="kt-cd-overlay-title">Processing Demand...</div>' +
            '<div class="kt-cd-overlay-sub">Validating and routing for approval.</div>' +
          "</div>" +
        "</div>" +
      "</div>"
    );
  }

  // ── STEP 4 HTML ──────────────────────────────────────────────────────────
  function _renderStep4() {
    var ts = new Date();
    var tsStr =
      ts.toLocaleDateString("en-KE", { month: "short", day: "numeric" }) +
      ", " +
      String(ts.getHours()).padStart(2, "0") +
      ":" +
      String(ts.getMinutes()).padStart(2, "0");
    var refDisplay = _state.demandId || _state.demandName || "—";
    return (
      '<div class="kt-cd-canvas">' +
        '<div class="kt-cd-bg-glow" style="top:-80px;right:-80px;width:300px;height:300px;background:#00a2fd"></div>' +
        '<div class="kt-cd-bg-glow" style="top:50%;left:-80px;width:220px;height:220px;background:#d7e2ff"></div>' +

        '<div class="kt-cd-success-wrap active">' +
          '<div class="kt-cd-success-card">' +
            '<div class="kt-cd-success-icon-wrap">' +
              '<div class="kt-cd-success-glow"></div>' +
              '<div class="kt-cd-success-circle">' +
                '<span class="material-symbols-outlined" style="font-variation-settings:\'wght\' 700;font-size:52px;color:#fff">check_circle</span>' +
              "</div>" +
            "</div>" +
            '<h1 class="kt-cd-success-title">Demand Submitted Successfully</h1>' +
            '<p class="kt-cd-success-sub">Your demand <span class="kt-cd-ref-chip">Ref: ' +
              _esc(refDisplay) +
            "</span> has been sent to the Department Approver for review.</p>" +
            '<div class="kt-cd-milestone">' +
              '<div class="kt-cd-milestone-head">' +
                '<span class="kt-cd-milestone-tag-label">Next Milestone</span>' +
                '<span class="kt-cd-pending-chip">Pending Approval</span>' +
              "</div>" +
              '<div class="kt-cd-milestone-body">' +
                '<div class="kt-cd-milestone-accent"></div>' +
                '<div class="kt-cd-milestone-text">' +
                  "<h3>Department Head Review</h3>" +
                  "<p>Your Department Approver will review and escalate to Finance.</p>" +
                "</div>" +
              "</div>" +
            "</div>" +
            '<div class="kt-cd-success-actions">' +
              '<button class="kt-cd-btn kt-cd-btn--primary" id="kt-cd-go-hub">' +
                _ico("dashboard") + "Go to Demand Hub" +
              "</button>" +
              (_state.demandName
                ? '<button class="kt-cd-btn kt-cd-btn--ghost" id="kt-cd-view-demand">' +
                    _ico("open_in_new") + "View Demand" +
                  "</button>"
                : "") +
            "</div>" +
            '<div class="kt-cd-success-footer">' +
              '<div class="kt-cd-footer-item"><div class="kt-cd-footer-icon">' + _ico("history") + '</div><div><div class="kt-cd-footer-label">Timestamp</div><div class="kt-cd-footer-val">' + tsStr + "</div></div></div>" +
              '<div class="kt-cd-footer-item"><div class="kt-cd-footer-icon">' + _ico("badge") + '</div><div><div class="kt-cd-footer-label">Reference</div><div class="kt-cd-footer-val">' + _esc(refDisplay) + "</div></div></div>" +
              '<div class="kt-cd-footer-item"><div class="kt-cd-footer-icon">' + _ico("pending_actions") + '</div><div><div class="kt-cd-footer-label">Status</div><div class="kt-cd-footer-val">Pending HoD Approval</div></div></div>' +
            "</div>" +
          "</div>" +
        "</div>" +
      "</div>"
    );
  }

  // ── Confetti particles ───────────────────────────────────────────────────
  function _spawnParticles() {
    var colors = ["#00346f", "#10B981", "#00a2fd"];
    for (var i = 0; i < 18; i++) {
      (function () {
        var p = document.createElement("div");
        var size = Math.random() * 8 + 4;
        p.className = "kt-cd-particle";
        p.style.cssText = [
          "width:" + size + "px",
          "height:" + size + "px",
          "background-color:" + colors[Math.floor(Math.random() * colors.length)],
          "left:" + Math.random() * 100 + "vw",
          "top:-20px",
          "animation-delay:" + Math.random() * 4 + "s",
          "animation-duration:" + (Math.random() * 6 + 6) + "s",
        ].join(";");
        document.body.appendChild(p);
        setTimeout(function () {
          if (p.parentNode) p.parentNode.removeChild(p);
        }, 14000);
      })();
    }
  }

  // ── Render ────────────────────────────────────────────────────────────────
  function _render(wrapper) {
    document.querySelectorAll(".kt-cd-particle").forEach(function (p) {
      if (p.parentNode) p.parentNode.removeChild(p);
    });
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
        _spawnParticles();
        break;
    }
    var ms = document.querySelector(".main-section");
    if (ms) ms.scrollTop = 0;
  }

  // ── Load dropdown meta (fire-and-forget) ─────────────────────────────────
  function _loadMeta(wrapper) {
    frappe.call({
      method:
        "kentender_procurement.demand_intake.api.queue_list.get_dia_queue_filter_meta",
      callback: function (r) {
        if (r && r.message && r.message.ok && r.message.departments) {
          _state.departments = r.message.departments || [];
          var sel = wrapper.querySelector("#kt-cd-dept");
          if (sel) {
            var cur = sel.value;
            sel.innerHTML = _deptOptions();
            if (cur) sel.value = cur;
          }
        }
      },
    });
    frappe.call({
      method: "frappe.client.get_list",
      args: {
        doctype: "Procuring Entity",
        fields: ["name"],
        limit: 50,
        order_by: "name asc",
      },
      callback: function (r) {
        if (r && r.message) {
          _state.procuringEntities = (r.message || []).map(function (x) {
            return x.name;
          });
          var sel = wrapper.querySelector("#kt-cd-entity");
          if (sel) {
            var cur = sel.value;
            sel.innerHTML = _entityOptions();
            if (cur) sel.value = cur;
          }
        }
      },
    });
  }

  // ── Bind Step 1 ──────────────────────────────────────────────────────────
  function _bindStep1(wrapper) {
    // char counter
    var ta = wrapper.querySelector("#kt-cd-justify");
    var cc = wrapper.querySelector("#kt-cd-char-count");
    if (ta && cc) {
      ta.addEventListener("input", function () {
        _state.form1.justification = ta.value;
        cc.textContent = ta.value.length + " / 2000";
      });
    }
    // priority toggle
    var toggle = wrapper.querySelector("#kt-cd-priority");
    if (toggle) {
      toggle.addEventListener("change", function () {
        _state.form1.priority = toggle.checked;
      });
    }
    // discard
    var discard = wrapper.querySelector("#kt-cd-discard");
    if (discard) {
      discard.addEventListener("click", function () {
        if (frappe && frappe.set_route) frappe.set_route("demand-hub");
      });
    }
    // next → save draft
    var next = wrapper.querySelector("#kt-cd-next-1");
    if (next) {
      next.addEventListener("click", function () {
        if (_state.saving) return;

        var titleEl = wrapper.querySelector("#kt-cd-title");
        var deptEl = wrapper.querySelector("#kt-cd-dept");
        var catEl = wrapper.querySelector("#kt-cd-category");
        var entityEl = wrapper.querySelector("#kt-cd-entity");
        var rbyEl = wrapper.querySelector("#kt-cd-required-by");
        var justEl = wrapper.querySelector("#kt-cd-justify");
        var priorityEl = wrapper.querySelector("#kt-cd-priority");

        var title = (titleEl ? titleEl.value : "").trim();
        var entity = entityEl ? entityEl.value : "";
        var requiredBy = rbyEl ? rbyEl.value : "";

        if (!title) {
          if (titleEl) titleEl.focus();
          frappe.msgprint({
            title: "Required",
            message: "Please enter a Demand Title.",
            indicator: "orange",
          });
          return;
        }
        if (!entity) {
          frappe.msgprint({
            title: "Required",
            message: "Please select a Procuring Entity.",
            indicator: "orange",
          });
          return;
        }
        if (!requiredBy) {
          frappe.msgprint({
            title: "Required",
            message: "Please select a Required By Date.",
            indicator: "orange",
          });
          return;
        }

        // Persist form values in state
        _state.form1.title = title;
        _state.form1.dept = deptEl ? deptEl.value : "";
        _state.form1.category = catEl ? catEl.value : "";
        _state.form1.entity = entity;
        _state.form1.requiredBy = requiredBy;
        _state.form1.justification = justEl ? justEl.value : "";
        _state.form1.priority = priorityEl ? priorityEl.checked : false;

        _state.saving = true;
        _render(wrapper);

        frappe.call({
          method:
            "kentender_procurement.demand_intake.api.create_demand.save_demand_draft",
          args: {
            title: _state.form1.title,
            requesting_department: _state.form1.dept || null,
            requisition_type: _state.form1.category || null,
            procuring_entity: _state.form1.entity || null,
            required_by_date: _state.form1.requiredBy || null,
            priority_level: _state.form1.priority ? "High" : "Normal",
            beneficiary_summary: _state.form1.justification || null,
            demand_name: _state.demandName || null,
          },
          callback: function (r) {
            _state.saving = false;
            if (r && r.message && r.message.ok) {
              _state.demandName = r.message.demand_name;
              _state.demandId = r.message.demand_id || null;
              _state.step = 2;
              _render(wrapper);
            } else {
              _render(wrapper);
              frappe.msgprint({
                title: "Save Failed",
                message:
                  (r && r.message && r.message.message) ||
                  "Could not save demand. Please try again.",
                indicator: "red",
              });
            }
          },
          error: function (r) {
            _state.saving = false;
            _render(wrapper);
            frappe.msgprint({
              title: "Save Failed",
              message:
                (r && r.message) || "An error occurred. Please try again.",
              indicator: "red",
            });
          },
        });
      });
    }
  }

  // ── Bind Step 2 ──────────────────────────────────────────────────────────
  function _bindStep2(wrapper) {
    // live-edit existing rows
    wrapper.querySelectorAll("[data-col]").forEach(function (inp) {
      inp.addEventListener("change", function () {
        var row = parseInt(inp.getAttribute("data-row"));
        var col = inp.getAttribute("data-col");
        if (!isNaN(row) && _state.items[row]) {
          if (col === "desc") _state.items[row].desc = inp.value;
          if (col === "qty") _state.items[row].qty = parseFloat(inp.value) || 0;
          if (col === "unitPrice") _state.items[row].unitPrice = parseFloat(inp.value) || 0;
          // Refresh totals
          var tds = inp.closest("tr").querySelectorAll("td");
          var totalCell = tds[tds.length - 2].querySelector(".kt-cd-tbl-total");
          if (totalCell) {
            totalCell.textContent = _fmt(
              (_state.items[row].qty || 0) * (_state.items[row].unitPrice || 0)
            );
          }
        }
      });
    });

    // delete row
    wrapper.querySelectorAll("[data-del]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var idx = parseInt(btn.getAttribute("data-del"));
        _state.items.splice(idx, 1);
        wrapper.innerHTML = _renderStep2();
        _bindStep2(wrapper);
      });
    });

    // save new row
    var saveBtn = wrapper.querySelector("#kt-cd-save-row");
    if (saveBtn) {
      saveBtn.addEventListener("click", function () {
        var descEl = wrapper.querySelector("#kt-cd-new-desc");
        var qtyEl = wrapper.querySelector("#kt-cd-new-qty");
        var unitEl = wrapper.querySelector("#kt-cd-new-unit");
        var desc = descEl ? descEl.value.trim() : "";
        var qty = qtyEl ? parseFloat(qtyEl.value) || 0 : 0;
        var unitPrice = unitEl ? parseFloat(unitEl.value) || 0 : 0;
        if (!desc) {
          if (descEl) descEl.focus();
          return;
        }
        _state.items.push({ desc: desc, qty: qty, unitPrice: unitPrice });
        wrapper.innerHTML = _renderStep2();
        _bindStep2(wrapper);
      });
    }

    // Add New Row → focus new desc
    var addBtn = wrapper.querySelector("#kt-cd-add-row");
    if (addBtn) {
      addBtn.addEventListener("click", function () {
        var nd = wrapper.querySelector("#kt-cd-new-desc");
        if (nd) nd.focus();
      });
    }

    // back → step 1 (no API call needed, state preserved)
    var back = wrapper.querySelector("#kt-cd-back-2");
    if (back) {
      back.addEventListener("click", function () {
        _state.step = 1;
        _render(wrapper);
      });
    }

    // next → save items + fetch readiness
    var next = wrapper.querySelector("#kt-cd-next-2");
    if (next) {
      next.addEventListener("click", function () {
        if (_state.saving) return;
        if (!_state.items.length) {
          frappe.msgprint({
            title: "Items Required",
            message: "Please add at least one item before proceeding.",
            indicator: "orange",
          });
          return;
        }
        if (!_state.demandName) {
          frappe.msgprint({
            title: "Error",
            message: "Demand reference missing. Please go back to Step 1.",
            indicator: "red",
          });
          return;
        }

        _state.saving = true;
        _render(wrapper);

        var itemsPayload = JSON.stringify(
          _state.items.map(function (it) {
            return {
              desc: it.desc,
              qty: it.qty,
              unit_price: it.unitPrice,
            };
          })
        );

        frappe.call({
          method:
            "kentender_procurement.demand_intake.api.create_demand.save_demand_draft",
          args: {
            demand_name: _state.demandName,
            items: itemsPayload,
          },
          callback: function (r) {
            _state.saving = false;
            if (r && r.message && r.message.ok) {
              if (r.message.demand_id) {
                _state.demandId = r.message.demand_id;
              }
              // Fetch submission readiness before showing step 3
              frappe.call({
                method:
                  "kentender_procurement.demand_intake.api.review.get_demand_submission_readiness",
                args: { demand_name: _state.demandName },
                callback: function (rr) {
                  _state.readiness =
                    rr && rr.message ? rr.message : null;
                  _state.step = 3;
                  _render(wrapper);
                },
                error: function () {
                  _state.readiness = null;
                  _state.step = 3;
                  _render(wrapper);
                },
              });
            } else {
              _render(wrapper);
              frappe.msgprint({
                title: "Save Failed",
                message:
                  (r && r.message && r.message.message) ||
                  "Could not save items. Please try again.",
                indicator: "red",
              });
            }
          },
          error: function (r) {
            _state.saving = false;
            _render(wrapper);
            frappe.msgprint({
              title: "Save Failed",
              message:
                (r && r.message) || "An error occurred. Please try again.",
              indicator: "red",
            });
          },
        });
      });
    }
  }

  // ── Bind Step 3 ──────────────────────────────────────────────────────────
  function _bindStep3(wrapper) {
    var e1 = wrapper.querySelector("#kt-cd-edit-1");
    if (e1) e1.addEventListener("click", function () { _state.step = 1; _render(wrapper); });
    var e2 = wrapper.querySelector("#kt-cd-edit-2");
    if (e2) e2.addEventListener("click", function () { _state.step = 2; _render(wrapper); });

    var back = wrapper.querySelector("#kt-cd-back-3");
    if (back) back.addEventListener("click", function () { _state.step = 2; _render(wrapper); });

    var submit = wrapper.querySelector("#kt-cd-submit");
    if (submit) {
      submit.addEventListener("click", function () {
        if (_state.submitting) return;
        if (!_state.demandName) {
          frappe.msgprint({
            title: "Error",
            message: "Demand reference missing. Please restart the wizard.",
            indicator: "red",
          });
          return;
        }

        var overlay = wrapper.querySelector("#kt-cd-overlay");
        if (overlay) overlay.classList.add("active");
        _state.submitting = true;

        frappe.call({
          method:
            "kentender_procurement.demand_intake.api.lifecycle.submit_demand",
          args: { demand_name: _state.demandName },
          callback: function (r) {
            _state.submitting = false;
            if (overlay) overlay.classList.remove("active");
            if (r && r.message && r.message.status) {
              // Update demandId if not yet set
              if (!_state.demandId) {
                _state.demandId = r.message.name || _state.demandName;
              }
              _state.step = 4;
              _render(wrapper);
            } else {
              frappe.msgprint({
                title: "Submit Failed",
                message:
                  (r && r.message) || "Could not submit demand. Please try again.",
                indicator: "red",
              });
            }
          },
          error: function (r) {
            _state.submitting = false;
            if (overlay) overlay.classList.remove("active");
            frappe.msgprint({
              title: "Submit Failed",
              message:
                (r && r.message) || "An error occurred during submission.",
              indicator: "red",
            });
          },
        });
      });
    }
  }

  // ── Bind Step 4 ──────────────────────────────────────────────────────────
  function _bindStep4(wrapper) {
    var hubBtn = wrapper.querySelector("#kt-cd-go-hub");
    if (hubBtn) {
      hubBtn.addEventListener("click", function () {
        if (frappe && frappe.set_route) frappe.set_route("demand-hub");
      });
    }
    var viewBtn = wrapper.querySelector("#kt-cd-view-demand");
    if (viewBtn) {
      viewBtn.addEventListener("click", function () {
        if (frappe && frappe.set_route && _state.demandName) {
          frappe.set_route("demand-workbench", _state.demandName);
        }
      });
    }
  }

  // ── Reset wizard state for a fresh create flow ───────────────────────────
  function _resetState() {
    _state.step = 1;
    _state.form1 = {
      title: "", dept: "", category: "", priority: false,
      justification: "", entity: "", requiredBy: "",
    };
    _state.items = [];
    _state.demandName = null;
    _state.demandId = null;
    _state.saving = false;
    _state.submitting = false;
    _state.readiness = null;
  }

  // ── Frappe page registration ─────────────────────────────────────────────
  frappe.pages["create-demand"].on_page_load = function (wrapper) {
    _ensureFonts();
    _state._wrapper = wrapper;
  };

  frappe.pages["create-demand"].on_page_show = function (wrapper) {
    _ensureFonts();
    _state._wrapper = wrapper;
    _resetState();
    _render(wrapper);
    // Fire-and-forget meta load; dropdowns update in-place when responses arrive
    _loadMeta(wrapper);
  };

  frappe.pages["create-demand"].on_page_hide = function () {
    document.querySelectorAll(".kt-cd-particle").forEach(function (p) {
      if (p.parentNode) p.parentNode.removeChild(p);
    });
  };
})();
