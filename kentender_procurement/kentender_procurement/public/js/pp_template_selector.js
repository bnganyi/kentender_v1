// D5 — Shared template list + preview modal (Procurement Package form + Planning workbench).

frappe.provide("kentender_procurement.pp_template_selector");

(function () {
	function escapeHtml(s) {
		if (s == null || s === undefined) return "";
		return String(s)
			.replace(/&/g, "&amp;")
			.replace(/</g, "&lt;")
			.replace(/>/g, "&gt;")
			.replace(/"/g, "&quot;");
	}

	function slugForTestid(code) {
		const s = String(code || "")
			.toLowerCase()
			.replace(/[^a-z0-9]+/g, "-")
			.replace(/^-+|-+$/g, "");
		return s || "tpl";
	}

	/**
	 * @param {Object} opt
	 * @param {string} opt.mode - "form" | "workbench"
	 * @param {import('frappe/form').Form} [opt.frm] - when mode=form
	 * @param {string} [opt.planName] - when mode=workbench (Procurement Plan internal name)
	 * @param {function} [opt.on_workbench_done] - callback after apply success
	 */
	kentender_procurement.pp_template_selector.open = function (opt) {
		const mode = opt && opt.mode;
		if (mode !== "form" && mode !== "workbench") {
			return;
		}

		let selectedRow = null;
		let selectedPreview = null;
		const workbenchDemands = [];

		const d = new frappe.ui.Dialog({
			title: mode === "form" ? __("Choose template") : __("Apply template to demands"),
			size: "extra-large",
		});

		const $root = $(
			'<div class="kt-pp-tpl-modal" data-testid="pp-template-selector"></div>'
		);
		$root.append(
			'<div class="row g-0 kt-pp-tpl-modal__main">' +
				'<div class="col-12 col-md-5 border-end pe-md-2 kt-pp-tpl-list-wrap"></div>' +
				'<div class="col-12 col-md-7 ps-md-2 kt-pp-tpl-preview-wrap" data-testid="pp-template-preview"></div>' +
				"</div>"
		);
		if (mode === "workbench") {
			$root.append(
				'<div class="mt-3 border-top pt-3 kt-pp-tpl-demand-block" data-testid="pp-workbench-demands">' +
					'<p class="small text-muted mb-1">' +
					escapeHtml(__("Demands to package (approved or planning ready)")) +
					"</p>" +
					'<ul class="list-unstyled small mb-2" id="kt-pp-tpl-demand-chips"></ul>' +
					'<button type="button" class="btn btn-xs btn-default" id="kt-pp-tpl-add-demand">' +
					escapeHtml(__("Add demand")) +
					"</button>" +
					"</div>"
			);
		}
		$(d.body).empty().append($root);

		function renderPreview() {
			const $pv = $root.find(".kt-pp-tpl-preview-wrap");
			if (!selectedRow) {
				$pv.html(
					'<p class="text-muted small mb-0">' + escapeHtml(__("Select a template.")) + "</p>"
				);
				return;
			}
			$pv.html(
				'<p class="text-muted small py-2">' + escapeHtml(__("Loading preview…")) + "</p>"
			);
			frappe.call({
				method:
					"kentender_procurement.procurement_planning.api.template_selector.get_pp_template_preview",
				args: { template: selectedRow.name },
				callback: function (r) {
					const p = r && r.message;
					if (!p || p.ok === false) {
						$pv.html(
							'<p class="text-danger small">' + escapeHtml((p && p.message) || __("Error")) + "</p>"
						);
						return;
					}
					selectedPreview = p;
					const lb = p.profile_labels || {};
					$pv.html(
						'<div class="kt-pp-tpl-preview-inner">' +
							'<h6 class="mb-1">' +
							escapeHtml(p.template_name || "") +
							"</h6>" +
							'<p class="small text-muted mb-2 font-monospace">' +
							escapeHtml(p.template_code || "") +
							"</p>" +
							'<dl class="row small mb-0">' +
							'<dt class="col-sm-4 text-muted">' +
							escapeHtml(__("Default method")) +
							'</dt><dd class="col-sm-8">' +
							escapeHtml(p.default_method || "") +
							"</dd>" +
							'<dt class="col-sm-4 text-muted">' +
							escapeHtml(__("Contract type")) +
							'</dt><dd class="col-sm-8">' +
							escapeHtml(p.default_contract_type || "") +
							"</dd>" +
							'<dt class="col-sm-4 text-muted">' +
							escapeHtml(__("Applicability")) +
							'</dt><dd class="col-sm-8">' +
							escapeHtml(p.applicability_summary || "") +
							"</dd>" +
							'<dt class="col-sm-4 text-muted">' +
							escapeHtml(__("Grouping")) +
							'</dt><dd class="col-sm-8">' +
							escapeHtml(p.grouping_summary || "") +
							"</dd>" +
							'<dt class="col-sm-4 text-muted">' +
							escapeHtml(__("Risk profile")) +
							'</dt><dd class="col-sm-8">' +
							escapeHtml(lb.risk_profile || "—") +
							"</dd>" +
							'<dt class="col-sm-4 text-muted">' +
							escapeHtml(__("KPI profile")) +
							'</dt><dd class="col-sm-8">' +
							escapeHtml(lb.kpi_profile || "—") +
							"</dd>" +
							'<dt class="col-sm-4 text-muted">' +
							escapeHtml(__("Decision criteria")) +
							'</dt><dd class="col-sm-8">' +
							escapeHtml(lb.decision_criteria_profile || "—") +
							"</dd>" +
							'<dt class="col-sm-4 text-muted">' +
							escapeHtml(__("Vendor management")) +
							'</dt><dd class="col-sm-8">' +
							escapeHtml(lb.vendor_management_profile || "—") +
							"</dd>" +
							"</dl></div>"
					);
				},
			});
		}

		function renderDemandChips() {
			const $ul = $root.find("#kt-pp-tpl-demand-chips");
			$ul.empty();
			for (let i = 0; i < workbenchDemands.length; i++) {
				const id = workbenchDemands[i];
				$ul.append(
					'<li class="d-flex align-items-center gap-1 mb-1"><span class="font-monospace">' +
					escapeHtml(id) +
					'</span> <button type="button" class="btn btn-link btn-sm p-0 text-danger" data-pp-remove-d="' +
					i +
					'">×</button></li>'
				);
			}
			$ul.find("[data-pp-remove-d]").on("click", function () {
				const j = parseInt($(this).attr("data-pp-remove-d"), 10);
				if (Number.isFinite(j)) {
					workbenchDemands.splice(j, 1);
					renderDemandChips();
				}
			});
		}

		$root.find(".kt-pp-tpl-list-wrap").html(
			'<p class="text-muted small">' + escapeHtml(__("Loading…")) + "</p>"
		);
		frappe.call({
			method: "kentender_procurement.procurement_planning.api.template_selector.list_pp_templates",
			callback: function (r) {
				const data = r && r.message;
				if (!data || data.ok === false) {
					$root
						.find(".kt-pp-tpl-list-wrap")
						.html(
							'<p class="text-danger small">' +
							escapeHtml((data && data.message) || __("Could not load templates.")) +
							"</p>"
						);
					return;
				}
				const rows = data.rows || [];
				if (!rows.length) {
					$root
						.find(".kt-pp-tpl-list-wrap")
						.html(
							'<p class="text-muted small">' + escapeHtml(__("No active templates.")) + "</p>"
						);
					return;
				}
				let h = '<div class="d-flex flex-column gap-1 kt-pp-tpl-list">';
				for (let k = 0; k < rows.length; k++) {
					const row = rows[k];
					const slug = slugForTestid(row.template_code);
					const tid = "pp-template-row-" + slug;
					const primary = escapeHtml(row.template_name || "");
					const sec =
						escapeHtml(row.template_code || "") +
						" · " +
						escapeHtml(row.default_method || "") +
						" · " +
						escapeHtml(row.default_contract_type || "");
					const sup = escapeHtml(row.applicability_summary || "");
					h +=
						'<button type="button" class="btn btn-block btn-default text-start p-2 kt-pp-tpl-row" ' +
						"data-pp-tpl-name=\"" +
						escapeHtml(row.name || "") +
						"\" " +
						"data-testid=\"" +
						escapeHtml(tid) +
						'">' +
						'<div class="fw-bold">' +
						primary +
						"</div>" +
						'<div class="small text-muted font-monospace">' +
						sec +
						"</div>" +
						'<div class="small text-muted">' +
						sup +
						"</div>" +
						"</button>";
				}
				h += "</div>";
				$root.find(".kt-pp-tpl-list-wrap").html(h);
				$root.find(".kt-pp-tpl-row").on("click", function () {
					$root.find(".kt-pp-tpl-row").removeClass("btn-primary text-white is-active");
					$(this).addClass("btn-primary text-white is-active");
					const nm = $(this).attr("data-pp-tpl-name") || "";
					selectedRow = { name: nm, template_code: "" };
					const found = rows.find(function (x) { return x.name === nm; });
					if (found) {
						selectedRow = found;
					}
					renderPreview();
				});
			},
		});

		if (mode === "workbench") {
			$root.find("#kt-pp-tpl-add-demand").on("click", function () {
				const d2 = new frappe.ui.Dialog({
					title: __("Add demand"),
					fields: [
						{
							fieldname: "demand_id",
							fieldtype: "Link",
							label: __("Demand"),
							options: "Demand",
							reqd: 1,
							get_query: function () {
								return { filters: { status: ["in", ["Approved", "Planning Ready"]] } };
							},
						},
					],
					primary_action_label: __("Add"),
					primary_action: function () {
						const v = d2.get_values();
						if (!v || !v.demand_id) {
							return;
						}
						if (workbenchDemands.indexOf(v.demand_id) >= 0) {
							frappe.show_alert({ message: __("Already added."), indicator: "orange" });
						} else {
							workbenchDemands.push(v.demand_id);
							renderDemandChips();
						}
						d2.hide();
					},
				});
				d2.show();
			});
		}

		if (mode === "form") {
			d.set_primary_action(__("Use template"), function () {
				if (!selectedRow || !selectedRow.name) {
					frappe.msgprint(__("Select a template first."));
					return;
				}
				if (!selectedPreview || !selectedPreview.profile_links) {
					frappe.msgprint(__("Wait for the preview to load, then try again."));
					return;
				}
				const lnk = selectedPreview.profile_links;
				if (!lnk) {
					return;
				}
				const frm = opt.frm;
				frm.set_value("template_id", lnk.template_id);
				frm.set_value("risk_profile_id", lnk.risk_profile_id || null);
				frm.set_value("kpi_profile_id", lnk.kpi_profile_id || null);
				frm.set_value("decision_criteria_profile_id", lnk.decision_criteria_profile_id || null);
				frm.set_value("vendor_management_profile_id", lnk.vendor_management_profile_id || null);
				d.hide();
				frappe.show_alert({ message: __("Template applied — save the package to persist."), indicator: "green" });
			});
		} else {
			d.set_primary_action(__("Apply template"), function () {
				if (!selectedRow || !selectedRow.name) {
					frappe.msgprint(__("Select a template first."));
					return;
				}
				if (workbenchDemands.length < 1) {
					frappe.msgprint(__("Add at least one demand."));
					return;
				}
				const planName = opt.planName;
				if (!planName) {
					frappe.msgprint(__("No plan in context."));
					return;
				}
				frappe.call({
					method: "kentender_procurement.procurement_planning.api.workflow.apply_template_to_demands",
					args: {
						plan_id: planName,
						template_id: selectedRow.name,
						demand_ids: workbenchDemands,
					},
					callback: function (r) {
						if (r && r.exc) {
							frappe.msgprint({ title: __("Could not apply"), message: __("Check demands and plan state."), indicator: "red" });
							return;
						}
						d.hide();
						frappe.show_alert({ message: __("Template applied to demands."), indicator: "green" });
						if (typeof opt.on_workbench_done === "function") {
							opt.on_workbench_done();
						}
					},
				});
			});
		}
		$(d.get_primary_btn()).attr("data-testid", "pp-template-apply");

		d.show();
	};
})();
