// STD Tender Binding — Tender Management STD panel (STD-CURSOR-1108)

frappe.ui.form.on("STD Tender Binding", {
	refresh: function (frm) {
		if (!frm || frm.is_new()) return;
		const tc = String(frm.doc.tender_code || "").trim();
		if (!tc) return;
		const hostId = "kt-tm-std-panel-root";
		if (frm._kt_tm_std_panel_host) {
			var wrap = frm._kt_tm_std_panel_host;
		} else {
			const $box = $(frm.wrapper).find(".form-layout").first();
			if (!$box.length) return;
			const $host = $('<div class="form-section"></div>');
			$box.prepend($host);
			const el = $('<div id="' + hostId + '" data-testid="tm-std-panel-root" class="kt-std-surface p-3 mb-3"></div>').appendTo($host)[0];
			frm._kt_tm_std_panel_host = el;
			var wrap = el;
		}
		function esc(v) {
			if (v == null) return "";
			return String(v)
				.replace(/&/g, "&amp;")
				.replace(/</g, "&lt;")
				.replace(/>/g, "&gt;")
				.replace(/"/g, "&quot;");
		}
		wrap.innerHTML =
			'<p class="small text-muted mb-0" data-testid="tm-std-panel-loading">' + esc(__("Loading STD panel…")) + "</p>";
		frappe.call({
			method: "kentender_procurement.std_engine.api.tender_std_panel.get_tender_std_panel_data",
			args: { tender_code: tc },
			callback: function (r) {
				if (!r || r.exc) {
					wrap.innerHTML = '<p class="text-danger small">' + esc(__("Could not load STD panel.")) + "</p>";
					return;
				}
				const d = (r && r.message) || {};
				if (!d.ok) {
					wrap.innerHTML = '<p class="text-danger small">' + esc(String(d.message || __("Not permitted"))) + "</p>";
					return;
				}
				const outs = d.generated_outputs || {};
				let h = '<h4 class="h6 mb-2" data-testid="tm-std-panel-title">' + esc(__("STD Configuration")) + "</h4>";
				h += '<ul class="list-unstyled small mb-2" data-testid="tm-std-panel-tree">';
				h += "<li>" + esc(__("Template version")) + ": " + esc(String(d.template_version_code || "—")) + "</li>";
				h += "<li>" + esc(__("Applicability profile")) + ": " + esc(String(d.profile_code || "—")) + "</li>";
				h += "<li>" + esc(__("STD instance")) + ": " + esc(String(d.std_instance_code || "—")) + "</li>";
				h += "<li>" + esc(__("Instance status")) + ": " + esc(String(d.instance_status || "—")) + "</li>";
				h += "<li>" + esc(__("Readiness")) + ": " + esc(String(d.readiness_status || "—")) + "</li>";
				h +=
					"<li>" +
					esc(__("Generated outputs")) +
					": Bundle " +
					esc(String(outs.bundle || "—")) +
					", DSM " +
					esc(String(outs.dsm || "—")) +
					", DOM " +
					esc(String(outs.dom || "—")) +
					", DEM " +
					esc(String(outs.dem || "—")) +
					", DCM " +
					esc(String(outs.dcm || "—")) +
					"</li>";
				h += "</ul>";
				const bl = d.blockers || [];
				if (bl.length) {
					h += '<div class="alert alert-warning small mb-2" data-testid="tm-std-panel-blockers"><strong>' + esc(__("Blockers")) + "</strong><ul>";
					for (let i = 0; i < bl.length; i++) {
						h += "<li>" + esc(String(bl[i])) + "</li>";
					}
					h += "</ul></div>";
				}
				if (!d.std_instance_code) {
					h +=
						'<p class="small text-muted mb-2" data-testid="tm-std-panel-create-hint">' +
						esc(__("Create or bind an STD instance for this tender (authorized operators).")) +
						"</p>";
				}
				h +=
					'<a class="btn btn-xs btn-default" href="/app/std-engine" data-testid="tm-std-panel-open-std">' +
					esc(__("Open STD Engine")) +
					"</a> ";
				h +=
					'<span class="btn btn-xs btn-default disabled" data-testid="tm-std-panel-request-addendum">' +
					esc(__("Request Addendum Impact")) +
					"</span>";
				if (d.hide_manual_attachment_ui) {
					h +=
						'<p class="small text-muted mt-2" data-testid="tm-std-panel-hide-legacy">' +
						esc(__("Manual STD attachment-as-source UI is hidden for STD v2.")) +
						"</p>";
				}
				wrap.innerHTML = h;
			},
		});
	},
});
