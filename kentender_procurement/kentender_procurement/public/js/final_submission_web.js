/**
 * Final Submission Website — validate again, submit confirm dialog, receipt print/download.
 */
(function () {
	"use strict";

	function root() {
		return (
			document.querySelector("[data-testid='kt-fs-rav-root']") ||
			document.querySelector("[data-testid='kt-fs-submit-root']") ||
			document.querySelector("[data-testid='kt-fs-receipt-root']") ||
			document.querySelector("[data-testid='kt-fs-fbr-root']")
		);
	}

	function pubRef(el) {
		return (el && el.getAttribute("data-publication-ref")) || "";
	}

	function call(method, args) {
		if (typeof frappe === "undefined" || !frappe.call) {
			return Promise.reject(new Error("frappe.call unavailable"));
		}
		return new Promise(function (resolve, reject) {
			frappe.call({
				method: method,
				args: args || {},
				callback: function (r) {
					if (r && r.exc) {
						reject(r);
						return;
					}
					resolve((r && r.message) || r);
				},
				error: reject,
			});
		});
	}

	function wireValidateAgain() {
		var btn = document.querySelector("[data-testid='kt-fs-rav-validate']");
		if (!btn) return;
		btn.addEventListener("click", function () {
			var el = root();
			var ref = pubRef(el);
			if (!ref) {
				window.location.reload();
				return;
			}
			btn.disabled = true;
			call("kentender_procurement.tender_configurations.get_bid_submission_readiness", {
				published_tender_ref: ref,
			})
				.then(function () {
					window.location.reload();
				})
				.catch(function () {
					btn.disabled = false;
					window.location.reload();
				});
		});
	}

	function wireSubmit() {
		var host = document.querySelector("[data-testid='kt-fs-submit-root']");
		if (!host) return;
		var declare = document.getElementById("kt-fs-declare");
		var submitBtn = document.getElementById("kt-fs-submit-btn");
		var dialog = document.getElementById("kt-fs-confirm-dialog");
		if (!declare || !submitBtn || !dialog) return;

		function syncEnabled() {
			var can = host.getAttribute("data-can-submit") === "1" && declare.checked;
			submitBtn.disabled = !can;
			submitBtn.classList.toggle("is-disabled", !can);
			var hint = host.querySelector("[data-testid='kt-fs-submit-hint']");
			if (hint) {
				hint.classList.toggle("is-hidden", declare.checked);
				hint.textContent = declare.checked ? "" : "Awaiting Confirmation";
			}
		}
		declare.addEventListener("change", syncEnabled);
		syncEnabled();

		submitBtn.addEventListener("click", function () {
			if (submitBtn.disabled) return;
			if (typeof dialog.showModal === "function") {
				dialog.showModal();
			} else {
				dialog.setAttribute("open", "open");
			}
		});

		host.querySelectorAll("[data-action='cancel-submit']").forEach(function (el) {
			el.addEventListener("click", function () {
				if (typeof dialog.close === "function") dialog.close();
				else dialog.removeAttribute("open");
			});
		});

		var confirmBtn = host.querySelector("[data-testid='kt-fs-confirm-submit']");
		if (confirmBtn) {
			confirmBtn.addEventListener("click", function () {
				var ref = pubRef(host);
				confirmBtn.disabled = true;
				call("kentender_procurement.tender_configurations.submit_electronic_bid", {
					published_tender_ref: ref,
					declaration_confirmed: 1,
				})
					.then(function (receipt) {
						var url =
							(receipt && receipt.workspace_url
								? "/tenders/" + ref + "/submission-receipt"
								: "/tenders/" + ref + "/submission-receipt");
						window.location.assign(url);
					})
					.catch(function (err) {
						confirmBtn.disabled = false;
						var msg = "Submission failed.";
						try {
							if (err && err.message) msg = String(err.message);
						} catch (_e) {}
						if (typeof frappe !== "undefined" && frappe.msgprint) {
							frappe.msgprint(msg);
						} else {
							alert(msg);
						}
					});
			});
		}
	}

	function wireReceipt() {
		var host = document.querySelector("[data-testid='kt-fs-receipt-root']");
		if (!host) return;
		var printBtn = host.querySelector("[data-action='print-receipt']");
		var downloadBtn = host.querySelector("[data-action='download-receipt']");
		if (printBtn) {
			printBtn.addEventListener("click", function () {
				window.print();
			});
		}
		if (downloadBtn) {
			downloadBtn.addEventListener("click", function () {
				var node = document.getElementById("kt-fs-receipt-print");
				if (!node) {
					window.print();
					return;
				}
				var blob = new Blob(
					[
						"<!DOCTYPE html><html><head><meta charset='utf-8'><title>Submission Receipt</title>",
						"<style>body{font-family:Public Sans,sans-serif;padding:24px;color:#191c1e}",
						"h1{font-size:28px} .row{display:flex;justify-content:space-between;margin:6px 0;border-bottom:1px solid #eee;padding:6px 0}",
						"</style></head><body>",
						node.innerHTML,
						"</body></html>",
					],
					{ type: "text/html" }
				);
				var a = document.createElement("a");
				a.href = URL.createObjectURL(blob);
				a.download = "submission-receipt.html";
				document.body.appendChild(a);
				a.click();
				a.remove();
				URL.revokeObjectURL(a.href);
			});
		}
	}

	function boot() {
		wireValidateAgain();
		wireSubmit();
		wireReceipt();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", boot);
	} else {
		boot();
	}
})();
