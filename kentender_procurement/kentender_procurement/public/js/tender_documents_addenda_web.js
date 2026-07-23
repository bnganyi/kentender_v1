/**
 * A3 Tender Documents & Addenda — Acknowledge Tender Documents.
 */
(function () {
	function root() {
		return document.querySelector('[data-testid="kt-a3-documents-root"]');
	}

	function acknowledge(ref) {
		if (!ref || typeof frappe === "undefined" || !frappe.call) {
			window.location.reload();
			return;
		}
		frappe.call({
			method: "kentender_procurement.tender_configurations.acknowledge_tender_documents",
			args: { published_tender_ref: ref },
			freeze: true,
			freeze_message: "Saving acknowledgement…",
			callback: function () {
				window.location.reload();
			},
			error: function (err) {
				var msg =
					(err && err.message) ||
					(err && err._server_messages) ||
					"Could not save acknowledgement.";
				if (frappe.msgprint) {
					frappe.msgprint({ title: "Error", message: msg, indicator: "red" });
				} else {
					alert(msg);
				}
			},
		});
	}

	function bind() {
		var el = root();
		if (!el) return;
		var btn = el.querySelector('[data-testid="kt-a3-acknowledge"]');
		if (!btn || btn.dataset.bound === "1") return;
		btn.dataset.bound = "1";
		btn.addEventListener("click", function (e) {
			e.preventDefault();
			var ref = btn.getAttribute("data-publication-ref") || el.getAttribute("data-publication-ref");
			acknowledge(ref);
		});
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", bind);
	} else {
		bind();
	}
})();
