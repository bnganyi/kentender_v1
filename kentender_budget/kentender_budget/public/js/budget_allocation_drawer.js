// Allocation create/edit drawer — in-workbench modal (Strategy pattern).

frappe.provide("kentender_budget.budget_allocation_drawer");

(function () {
	function esc(value) {
		return frappe.utils.escape_html(value == null ? "" : String(value));
	}

	function stripInternalIdFromDescription(description) {
		const raw = String(description || "").trim();
		if (!raw) return raw;
		return raw.replace(/^[a-z0-9]{8,}\s*,\s*/i, "");
	}

	function formatReferenceDisplay(label, code) {
		const cleanLabel = String(label || "").trim();
		const cleanCode = String(code || "").trim();
		if (!cleanLabel && !cleanCode) return "—";
		if (!cleanCode) return cleanLabel || "—";
		return cleanLabel + " (" + cleanCode + ")";
	}

	function hierarchyLabel(line) {
		const prog = line.program_label || line.program || "";
		const sub = line.sub_program_label || line.sub_program || "";
		if (sub && sub !== prog) return prog + " / " + sub;
		return prog || "—";
	}

	function splitNotesForDisplay(notes) {
		const raw = String(notes || "").trim();
		if (!raw) return { description: "", technical: "" };
		const seedMatch = raw.match(/^(.*?)(WORKS master seed[^.]*\.?.*)$/i);
		if (seedMatch) {
			return {
				description: seedMatch[1].trim().replace(/\.\s*$/, ""),
				technical: seedMatch[2].trim(),
			};
		}
		const approvalMatch = raw.match(/^(.*?)(Approved by:\s*USER-[^\s]+ on .+)$/i);
		if (approvalMatch) {
			return {
				description: approvalMatch[1].trim().replace(/\.\s*$/, ""),
				technical: approvalMatch[2].trim(),
			};
		}
		return { description: raw, technical: "" };
	}

	function emitPanelChanged(budgetName) {
		document.dispatchEvent(
			new CustomEvent("kt-budget-panel-changed", {
				detail: { budget_name: budgetName || "" },
			}),
		);
	}

	function patchAwesompleteDescriptions(d, fieldnames) {
		fieldnames.forEach(function (fieldname) {
			const control = d.fields_dict[fieldname];
			if (!control || !control.awesomplete || typeof control.awesomplete.get_item !== "function") {
				return;
			}
			const originalGetItem = control.awesomplete.get_item.bind(control.awesomplete);
			control.awesomplete.get_item = function (value) {
				const item = originalGetItem(value);
				if (!item || !item.description) return item;
				return Object.assign({}, item, {
					description: stripInternalIdFromDescription(item.description),
				});
			};
		});
	}

	function bindHierarchyQueries(d, strategicPlan) {
		const programField = d.get_field("program");
		const subProgramField = d.get_field("sub_program");
		const objectiveField = d.get_field("output_indicator");
		const targetField = d.get_field("performance_target");
		if (!programField) return;

		programField.get_query = function () {
			return { filters: strategicPlan ? { strategic_plan: strategicPlan } : {} };
		};
		subProgramField.get_query = function () {
			const program = d.get_value("program");
			return { filters: program ? { program } : { name: ["=", ""] } };
		};
		objectiveField.get_query = function () {
			const program = d.get_value("program");
			const filters = {};
			if (strategicPlan) filters.strategic_plan = strategicPlan;
			if (program) filters.program = program;
			return { filters };
		};
		targetField.get_query = function () {
			const program = d.get_value("program");
			const objective = d.get_value("output_indicator");
			const filters = {};
			if (strategicPlan) filters.strategic_plan = strategicPlan;
			if (program) filters.program = program;
			if (objective) filters.objective = objective;
			return Object.keys(filters).length ? { filters } : { filters: { name: ["=", ""] } };
		};
		programField.df.onchange = function () {
			d.set_value("sub_program", "");
			d.set_value("output_indicator", "");
			d.set_value("performance_target", "");
		};
		subProgramField.df.onchange = function () {
			d.set_value("output_indicator", "");
			d.set_value("performance_target", "");
		};
		objectiveField.df.onchange = function () {
			d.set_value("performance_target", "");
		};
	}

	function buildStrategicAlignmentHtml(line) {
		if (!line) return "";
		const summary = hierarchyLabel(line);
		const rows = [
			[__("Program"), formatReferenceDisplay(line.program_label || line.program, line.program_code)],
			[__("Sub-program"), formatReferenceDisplay(line.sub_program_label || line.sub_program, line.sub_program_code)],
			[
				__("Indicator"),
				formatReferenceDisplay(line.output_indicator_label || line.output_indicator, line.output_indicator_code),
			],
			[
				__("Target"),
				formatReferenceDisplay(line.performance_target_label || line.performance_target, line.performance_target_code),
			],
		];
		let detailRows = "";
		for (let i = 0; i < rows.length; i++) {
			if (!rows[i][1] || rows[i][1] === "—") continue;
			detailRows +=
				"<div><span class=\"text-muted\">" +
				esc(rows[i][0]) +
				":</span> " +
				esc(rows[i][1]) +
				"</div>";
		}
		if (!detailRows) return "";
		return (
			'<details class="kt-budget-strategic-alignment mb-2" data-testid="budget-allocation-strategic-alignment">' +
			"<summary class=\"small\">" +
			esc(__("Strategic alignment")) +
			": " +
			esc(summary) +
			"</summary>" +
			'<div class="small mt-1">' +
			detailRows +
			"</div></details>"
		);
	}

	function resolveBudgetLineName(values) {
		const program = values.program;
		const subProgram = values.sub_program;
		const tasks = [];
		if (program) {
			tasks.push(
				frappe.db.get_value("Strategy Program", program, "program_title").then(function (r) {
					return (r && r.message && r.message.program_title) || program;
				}),
			);
		}
		if (subProgram) {
			tasks.push(
				frappe.db.get_value("Sub Program", subProgram, "title").then(function (r) {
					return (r && r.message && r.message.title) || subProgram;
				}),
			);
		}
		return Promise.all(tasks).then(function (parts) {
			if (parts.length === 2) return parts[0] + " / " + parts[1];
			if (parts.length === 1) return parts[0];
			return program || __("Allocation");
		});
	}

	function saveAllocation(budgetName, payload, onSaved) {
		frappe.call({
			method: "kentender_budget.api.builder.upsert_budget_line",
			args: payload,
			callback: function () {
				frappe.show_alert({ message: __("Allocation saved"), indicator: "green" });
				emitPanelChanged(budgetName);
				if (onSaved) onSaved();
			},
		});
	}

	kentender_budget.budget_allocation_drawer = {
		splitNotesForDisplay: splitNotesForDisplay,
		hierarchyLabel: hierarchyLabel,

		openCreate(budgetName, strategicPlan, onSaved) {
			const d = new frappe.ui.Dialog({
				title: __("Add Allocation"),
				fields: [
					{
						fieldname: "section_hierarchy",
						fieldtype: "Section Break",
						label: __("Hierarchy link"),
					},
					{
						fieldname: "program",
						label: __("Program"),
						fieldtype: "Link",
						options: "Strategy Program",
						reqd: 1,
					},
					{
						fieldname: "sub_program",
						label: __("Sub-Program"),
						fieldtype: "Link",
						options: "Sub Program",
					},
					{
						fieldname: "output_indicator",
						label: __("Output Indicator"),
						fieldtype: "Link",
						options: "Strategy Objective",
					},
					{
						fieldname: "performance_target",
						label: __("Performance Target"),
						fieldtype: "Link",
						options: "Strategy Target",
					},
					{
						fieldname: "section_allocation",
						fieldtype: "Section Break",
						label: __("Allocation"),
					},
					{
						fieldname: "amount_allocated",
						label: __("Allocated Amount"),
						fieldtype: "Currency",
						reqd: 1,
						default: 0,
					},
					{
						fieldname: "funding_source",
						label: __("Funding Source"),
						fieldtype: "Link",
						options: "Funding Source",
					},
					{
						fieldname: "notes",
						label: __("Notes"),
						fieldtype: "Small Text",
					},
				],
				primary_action_label: __("Save Allocation"),
				primary_action: function (values) {
					resolveBudgetLineName(values).then(function (budgetLineName) {
						saveAllocation(
							budgetName,
							Object.assign(
								{ budget_name: budgetName, lines_filter: "active", budget_line_name: budgetLineName },
								values,
							),
							function () {
								d.hide();
								if (onSaved) onSaved();
							},
						);
					});
				},
			});
			d.$wrapper.attr("data-testid", "budget-allocation-drawer");
			bindHierarchyQueries(d, strategicPlan);
			patchAwesompleteDescriptions(d, [
				"program",
				"sub_program",
				"output_indicator",
				"performance_target",
				"funding_source",
			]);
			d.show();
		},

		openEdit(line, budgetName, readOnly, onSaved) {
			if (!line || !budgetName) return;
			const notesParts = splitNotesForDisplay(line.notes);
			const alignmentHtml = buildStrategicAlignmentHtml(line);
			const d = new frappe.ui.Dialog({
				title: readOnly ? __("View Allocation") : __("Edit Allocation"),
				fields: [
					{
						fieldname: "section_hierarchy",
						fieldtype: "HTML",
						options:
							alignmentHtml ||
							'<div class="small text-muted mb-2">' +
								esc(__("Program / Sub-program")) +
								": " +
								esc(hierarchyLabel(line)) +
								"</div>",
					},
					{
						fieldname: "section_allocation",
						fieldtype: "Section Break",
						label: __("Allocation"),
					},
					{
						fieldname: "amount_allocated",
						label: __("Allocated Amount"),
						fieldtype: "Currency",
						reqd: 1,
						default: line.amount_allocated || 0,
						read_only: readOnly ? 1 : 0,
					},
					{
						fieldname: "funding_source",
						label: __("Funding Source"),
						fieldtype: "Link",
						options: "Funding Source",
						default: line.funding_source || "",
						read_only: readOnly ? 1 : 0,
					},
					{
						fieldname: "notes",
						label: __("Notes"),
						fieldtype: "Small Text",
						default: notesParts.description || line.notes || "",
						read_only: readOnly ? 1 : 0,
					},
				],
				primary_action_label: readOnly ? __("Close") : __("Save Allocation"),
				primary_action: function (values) {
					if (readOnly) {
						d.hide();
						return;
					}
					saveAllocation(
						budgetName,
						{
							budget_name: budgetName,
							budget_line_id: line.name,
							budget_line_name: line.budget_line_name || hierarchyLabel(line),
							amount_allocated: values.amount_allocated,
							funding_source: values.funding_source,
							program: line.program,
							sub_program: line.sub_program,
							output_indicator: line.output_indicator,
							performance_target: line.performance_target,
							notes: values.notes,
							lines_filter: "active",
						},
						function () {
							d.hide();
							if (onSaved) onSaved();
						},
					);
				},
			});
			d.$wrapper.attr("data-testid", "budget-allocation-drawer");
			if (notesParts.technical) {
				d.fields_dict.section_hierarchy.$wrapper.append(
					'<details class="small text-muted mt-2"><summary>' +
						esc(__("Technical reference")) +
						"</summary><div>" +
						esc(notesParts.technical) +
						"</div></details>",
				);
			}
			if (!readOnly && line.can_remove) {
				d.set_secondary_action_label(__("Remove"));
				d.set_secondary_action(function () {
					frappe.confirm(__("Remove this allocation?"), function () {
						frappe.call({
							method: "kentender_budget.api.builder.remove_budget_line",
							args: {
								budget_name: budgetName,
								budget_line_id: line.name,
								lines_filter: "active",
							},
							callback: function () {
								d.hide();
								frappe.show_alert({ message: __("Allocation removed"), indicator: "green" });
								emitPanelChanged(budgetName);
								if (onSaved) onSaved();
							},
						});
					});
				});
			}
			const closeBtn = d.$wrapper.find(".btn-modal-close");
			closeBtn.attr("data-testid", "budget-allocation-drawer-close");
			d.show();
		},
	};
})();
