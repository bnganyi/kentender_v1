/**
 * R5-011 — TM2 Tender desk form: procurement hand-offs (navigation summaries only).
 */
(function () {
	frappe.provide("kentender_procurement.Tm2HandoffPanel");

	var LS_INCLUDE_OPTIONAL = "plc_tm2_handoff_include_optional_opening";

	function storageReadOptional() {
		try {
			return localStorage.getItem(LS_INCLUDE_OPTIONAL) === "1";
		} catch (e) {
			return false;
		}
	}

	function storageWriteOptional(flag) {
		try {
			if (flag) {
				localStorage.setItem(LS_INCLUDE_OPTIONAL, "1");
			} else {
				localStorage.removeItem(LS_INCLUDE_OPTIONAL);
			}
		} catch (e) {
			/* ignore */
		}
	}

	function esc(s) {
		return frappe.utils.escape_html(String(s == null ? "" : s));
	}

	function statusPill(status) {
		var s = String(status || "").trim();
		var cls = "gray";
		var low = s.toLowerCase();
		if (low.indexOf("consum") !== -1) {
			cls = "green";
		} else if (low.indexOf("hand") !== -1 || low.indexOf("ready") !== -1) {
			cls = "blue";
		}
		return $('<span class="indicator-pill no-indicator-dot tm2-handoff-status"/>')
			.addClass(cls)
			.attr("data-testid", "tm2-handoff-row-status")
			.text(s || __("Draft"));
	}

	function loadAndPaint($shell, frm, tenderCode, includeOptionalOpening) {
		$shell
			.empty()
			.show()
			.attr("data-testid", "tm2-tender-handoff-panel")
			.append(
				$('<div class="text-muted small" data-testid="tm2-handoff-loading"/>').text(
					__("Loading hand-offs…"),
				),
			);

		frappe.call({
			method:
				"kentender_procurement.procurement_lifecycle.api.journey_api.get_tm2_handoff_panel",
			args: {
				tender_code: tenderCode,
				include_optional_opening: includeOptionalOpening ? 1 : 0,
			},
			freeze: false,
			callback: function (resp) {
				var payload = resp && resp.message;
				paint($shell, payload, frm, tenderCode, includeOptionalOpening);
			},
			error: function () {
				$shell.empty().append(
					$('<div class="alert alert-warning mb-0 small" data-testid="tm2-handoff-panel-error"/>').text(
						__("Unable to load procurement hand-offs for this tender."),
					),
				);
			},
		});
	}

	function paint($shell, payload, frm, tenderCode, includeOptionalOpening) {
		function reload(nextFlag) {
			storageWriteOptional(nextFlag);
			loadAndPaint($shell, frm, tenderCode, nextFlag);
		}

		var $inner = $('<div class="tm2-handoff-inner"/>');
		$inner.append($("<h6/>").addClass("fw-semibold mb-2").text(__("Procurement hand-offs")));
		$inner.append(
			$("<p/>")
				.addClass("small text-muted mb-2")
				.text(
					__(
						"Navigation and evidence summaries only — source TM2 / Planning / STD records remain authoritative.",
					),
				),
		);

		var chkId = "tm2_handoff_optional_" + String(tenderCode).replace(/\W+/g, "-");
		var $row = $('<div class="form-check mb-3 small"/>').attr({
			"data-testid": "tm2-handoff-include-optional-wrap",
		});
		var $chk = $('<input type="checkbox" class="form-check-input"/>').attr({
			id: chkId,
			"data-testid": "tm2-handoff-include-optional",
			checked: includeOptionalOpening ? true : false,
		});
		var $lbl = $('<label class="form-check-label"/>').attr("for", chkId).text(
			 __("Show closing / opening checkpoint hand-offs (when present)"),
		);
		$chk.on("change", function () {
			reload(!!$(this).prop("checked"));
		});
		$row.append($chk, $lbl);
		$inner.append($row);

		var items = payload && payload.handoffs ? payload.handoffs : [];
		var $responsive = $('<div class="table-responsive"/>');
		var $table = $("<table/>")
			.addClass("table table-bordered table-hover table-sm mb-0")
			.attr("data-testid", "tm2-handoff-rows-table");
		var thead =
			"<thead><tr>" +
			"<th>" +
			esc(__("Hand-off")) +
			"</th>" +
			"<th>" +
			esc(__("Status")) +
			"</th>" +
			"<th>" +
			esc(__("Guidance")) +
			"</th>" +
			"<th class='nowrap'>" +
			esc(__("Open")) +
			"</th></tr></thead>";
		var $thead = $(thead);

		var $tbody = $('<tbody data-testid="tm2-handoff-rows-body"/>');
		if (!items.length) {
			var $cell = $('<td colspan="4" class="text-muted small"/>')
				.attr("data-testid", "tm2-handoff-panel-empty")
				.text(
					__(
						"No procurement hand-offs are linked to this tender’s journey yet, or you lack access.",
					),
				);
			$tbody.append($('<tr/>').append($cell));
		}

		items.forEach(function (h) {
			var code = String((h.handoff_code || "").trim());
			var title = String((h.handoff_title || "").trim());

			var $title = $('<div class="fw-semibold"/>')
				.attr("data-testid", "tm2-handoff-row-title")
				.text(title || __("Hand-off"));

			var $code = $('<div class="font-monospace text-muted small mt-1"/>')
				.attr("data-testid", "tm2-handoff-row-code")
				.text(code);

			var $mods = $('<div class="text-muted small mt-1 tm2-handoff-route"/>').text(
				[String(h.source_module || "").trim(), String(h.target_module || "").trim()]
					.filter(Boolean)
					.join(" → "),
			);

			var lines = [];
			(h.summary_lines || []).forEach(function (ln) {
				if (typeof ln === "string" && ln.trim()) {
					lines.push(ln.trim());
				}
			});

			var $list = $('<ul class="small text-muted tm2-handoff-sum mb-0 mt-2"/>').attr({
				"data-testid": "tm2-handoff-row-summary",
			});

			var maxBullets = Math.min(lines.length, 4);
			for (var ix = 0; ix < maxBullets; ix++) {
				$list.append($("<li/>").text(lines[ix]));
			}

			var $lead = $('<div/>').append($title).append($code).append($mods);
			if (lines.length) {
				$lead.append($list);
			}

			var guidance = String((h.next_action || "").trim());
			var $guidanceTd = $('<td class="small align-top tm2-handoff-guidance"/>')
				.attr("data-testid", "tm2-handoff-row-next")
				.text(guidance);

			var $open = $('<button type="button" class="btn btn-xs btn-primary"/>').attr({
				"data-testid": "tm2-handoff-row-open",
				type: "button",
			}).text(__("Open"));

			var $btnTd = $('<td class="align-top"/>');
			var $pillTd = $('<td class="align-top"/>');

			if (code) {
				$open.on("click", function (ev) {
					ev.preventDefault();
					frappe.set_route("Form", "Procurement Handoff Card", code);
				});
				$btnTd.append($open);
			}
			var $pill = $('<div class=""/>').append(statusPill(h.status));
			$pillTd.append($pill);

			var $rowTr = $('<tr class="tm2-handoff-card"/>').attr({
				"data-testid": "tm2-handoff-row",
				"data-handoff-code": code || "",
			});
			var $tdLead = $('<td class="tm2-handoff-row-lead"/>');
			var $leadWrap = $("<div/>").append($lead);
			$tdLead.append($leadWrap);
			$rowTr.append($tdLead, $pillTd, $guidanceTd, $btnTd);
			$tbody.append($rowTr);
		});

		$table.append($thead, $tbody);
		$responsive.append($table);
		$inner.append($responsive);
		$shell.empty().append($inner);
	}

	kentender_procurement.Tm2HandoffPanel = {
		sync: function ($host, frm) {
			var code =
				!frm || !frm.doc || frm.is_new()
					? ""
					: String(frm.doc.tender_code || frm.doc.name || "").trim();

			if (!code) {
				$host.hide().empty();
				return;
			}
			loadAndPaint($host, frm, code, storageReadOptional());
		},
		_readOptionalPreference: storageReadOptional,
		_writeOptionalPreference: storageWriteOptional,
	};
})();
