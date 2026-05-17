// Copyright (c) 2026, KenTender and contributors
// Doc 9 §22.2 — primary Tender Management UX is the workbench, not raw DocType forms.
//
// R5-010 / R5-011 — Module journey header + Procurement hand-offs on the TM2 desk Form.
// R6-002 — `BusinessReadinessSummary.mount` → `read_business_readiness_summary` (loading / error UX).

(function () {
	function businessTenderCode(frm) {
		if (!frm.doc || frm.is_new()) {
			return "";
		}
		return String(frm.doc.tender_code || frm.doc.name || "").trim();
	}

	function ensureModuleJourneyContextHost(frm) {
		if (frm._plc_tm2_module_journey_host_wrap) {
			return;
		}
		const $wrap = $(
			'<div class="kt-plc-module-journey-context mb-3" data-testid="tm2-tender-module-journey-context"></div>',
		);
		const $inner = $('<div class="kt-tm2-module-journey-context-inner"></div>').appendTo(
			$wrap,
		);
		$(frm.wrapper).prepend($wrap);
		frm._plc_tm2_module_journey_host_wrap = $wrap;
		frm._plc_tm2_module_journey_inner = $inner;
	}

	function ensureBusinessReadinessHost(frm) {
		ensureModuleJourneyContextHost(frm);
		if (frm._plc_tm2_br_host) {
			return frm._plc_tm2_br_host;
		}
		const $br = $('<div class="mb-3"></div>').attr(
			"data-testid",
			"tm2-tender-business-readiness-host",
		);
		frm._plc_tm2_module_journey_host_wrap.after($br);
		frm._plc_tm2_br_host = $br;
		return $br;
	}

	function ensureTm2HandoffShell(frm) {
		ensureModuleJourneyContextHost(frm);
		if (frm._plc_tm2_handoff_shell) {
			return frm._plc_tm2_handoff_shell;
		}
		const $hand = $('<div class="tm2-tender-handoff-panel-slot mb-3"></div>').attr(
			"data-testid",
			"tm2-tender-handoff-panel",
		);
		const $anchor = frm._plc_tm2_br_host || frm._plc_tm2_module_journey_host_wrap;
		$anchor.after($hand);
		frm._plc_tm2_handoff_shell = $hand;
		return $hand;
	}

	function syncBusinessReadinessSummary(frm) {
		const $br = ensureBusinessReadinessHost(frm);
		const code = businessTenderCode(frm);

		if (!code) {
			$br.hide().empty();
			return;
		}

		if (
			typeof kentender_procurement === "undefined" ||
			!kentender_procurement.BusinessReadinessSummary ||
			typeof kentender_procurement.BusinessReadinessSummary.mount !== "function"
		) {
			$br.hide().empty();
			return;
		}

		$br.show();
		kentender_procurement.BusinessReadinessSummary.mount($br, {
			object_type: "TM2 Tender",
			object_code: code,
		});
	}

	function syncModuleJourneyContextHeader(frm) {
		ensureModuleJourneyContextHost(frm);
		const $wrap = frm._plc_tm2_module_journey_host_wrap;
		const $inner = frm._plc_tm2_module_journey_inner;
		const code = businessTenderCode(frm);

		if (!code) {
			$wrap.hide();
			$inner.empty();
			if (frm._plc_tm2_br_host) {
				frm._plc_tm2_br_host.hide().empty();
			}
			if (frm._plc_tm2_handoff_shell) {
				frm._plc_tm2_handoff_shell.hide().empty();
			}
			return;
		}

		if (
			typeof kentender_procurement === "undefined" ||
			!kentender_procurement.ModuleJourneyContextHeader ||
			typeof kentender_procurement.ModuleJourneyContextHeader.render !== "function"
		) {
			$wrap.hide();
			$inner.empty();
			if (frm._plc_tm2_br_host) {
				frm._plc_tm2_br_host.hide().empty();
			}
			return;
		}

		$wrap.show();
		kentender_procurement.ModuleJourneyContextHeader.render($inner, {
			object_type: "TM2 Tender",
			object_code: code,
		});
	}

	frappe.ui.form.on("TM2 Tender", {
		refresh(frm) {
			frm.clear_custom_buttons();
			frm.add_custom_button(
				__("Open Tender Management"),
				() => {
					frappe.set_route("tender-management-v2");
				},
				__("Workbench"),
			);

			const code = businessTenderCode(frm);

			syncModuleJourneyContextHeader(frm);
			syncBusinessReadinessSummary(frm);

			const $hos = ensureTm2HandoffShell(frm);
			if (!code) {
				if ($hos) {
					$hos.hide().empty();
				}
				return;
			}

			if (
				typeof kentender_procurement !== "undefined" &&
				kentender_procurement.Tm2HandoffPanel &&
				typeof kentender_procurement.Tm2HandoffPanel.sync === "function"
			) {
				kentender_procurement.Tm2HandoffPanel.sync($hos, frm);
			} else if ($hos) {
				$hos.hide().empty();
			}
		},
	});
})();
