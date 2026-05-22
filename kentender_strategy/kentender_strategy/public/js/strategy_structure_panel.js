// In-workspace Structure tab — hybrid outline + tables (4-level hierarchy).

frappe.provide("kentender_strategy.strategy_structure_panel");

(function () {
	const SUB_TABS = [
		{ id: "overview", label: __("Overview"), testId: "structure-subtab-overview" },
		{ id: "programs", label: __("Programs"), testId: "structure-subtab-programs" },
		{ id: "subprograms", label: __("Sub-programs"), testId: "structure-subtab-subprograms" },
		{ id: "indicators", label: __("Indicators"), testId: "structure-subtab-indicators" },
		{ id: "targets", label: __("Targets"), testId: "structure-subtab-targets" },
	];

	function esc(s) {
		return frappe.utils.escape_html(s == null ? "" : String(s));
	}

	function typeBadge(nodeType) {
		const map = {
			Program: "P",
			SubProgram: "SP",
			Indicator: "IND",
			Target: "TGT",
		};
		return map[nodeType] || "?";
	}

	function nodeTypeSlug(nodeType) {
		const map = {
			Program: "program",
			SubProgram: "subprogram",
			Indicator: "indicator",
			Target: "target",
		};
		return map[nodeType] || "unknown";
	}

	function nestNodes(flat) {
		const byParent = {};
		flat.forEach((n) => {
			const p = n.parent || "";
			if (!byParent[p]) byParent[p] = [];
			byParent[p].push(n);
		});
		function walk(parentId) {
			return (byParent[parentId] || []).map((n) => ({ ...n, children: walk(n.name) }));
		}
		return walk("");
	}

	function parentTitle(flat, parentId) {
		if (!parentId) return "";
		const p = flat.find((n) => n.name === parentId);
		return p ? p.title || p.name : parentId;
	}

	class StructurePanel {
		constructor($host, planName) {
			this.$host = $host;
			this.planName = planName;
			this.activeSubTab = "overview";
			this.flatNodes = [];
			this.readOnly = false;
			this.planStatus = "Draft";
		}

		mount() {
			this.$host.html(
				`<div class="kt-strategy-structure-panel" data-testid="strategy-structure-panel">
					<div class="kt-strategy-structure-subtabs mb-2" data-testid="strategy-structure-subtabs"></div>
					<div class="kt-strategy-structure-body" data-testid="strategy-structure-body"></div>
				</div>`,
			);
			this.$subtabs = this.$host.find(".kt-strategy-structure-subtabs");
			this.$body = this.$host.find(".kt-strategy-structure-body");
			this.bindEvents();
			this.load();
		}

		bindEvents() {
			const me = this;
			this.$host.on("click", ".kt-strategy-structure-subtab", function () {
				me.activeSubTab = $(this).attr("data-subtab") || "overview";
				me.renderSubTabs();
				me.renderBody();
			});
			this.$host.on("click", "[data-add-node-type]", function () {
				me.promptCreate($(this).attr("data-add-node-type"));
			});
			this.$host.on("click", "[data-edit-node]", function () {
				me.promptEdit($(this).attr("data-edit-node"));
			});
		}

		load() {
			const me = this;
			return frappe
				.call({
					method: "kentender_strategy.api.strategy_builder.get_strategy_tree",
					args: { plan_name: me.planName },
				})
				.then((r) => {
					const payload = r.message || {};
					me.flatNodes = payload.nodes || [];
					me.planStatus = (payload.plan && payload.plan.status) || "Draft";
					me.readOnly =
						me.planStatus !== "Draft" ||
						!(frappe.model && frappe.model.can_write && frappe.model.can_write("Strategic Plan"));
					me.renderSubTabs();
					me.renderBody();
				});
		}

		renderSubTabs() {
			let html = '<div class="kt-secondary-tabs" role="tablist">';
			for (let i = 0; i < SUB_TABS.length; i++) {
				const t = SUB_TABS[i];
				const on = this.activeSubTab === t.id;
				html +=
					'<button type="button" class="kt-secondary-tab kt-strategy-structure-subtab' +
					(on ? " is-active kt-secondary-tab-active" : "") +
					'" data-subtab="' +
					esc(t.id) +
					'" data-testid="' +
					esc(t.testId) +
					'" role="tab" aria-selected="' +
					(on ? "true" : "false") +
					'">' +
					esc(t.label) +
					"</button>";
			}
			html += "</div>";
			this.$subtabs.html(html);
		}

		renderBody() {
			if (this.activeSubTab === "overview") {
				this.$body.html(this.renderOverview());
				return;
			}
			const typeMap = {
				programs: "Program",
				subprograms: "SubProgram",
				indicators: "Indicator",
				targets: "Target",
			};
			const nodeType = typeMap[this.activeSubTab];
			this.$body.html(this.renderTable(nodeType));
		}

		renderOverview() {
			const tree = nestNodes(this.flatNodes);
			function walk(nodes, depth) {
				let html = "";
				nodes.forEach((n) => {
					const nodeType = nodeTypeSlug(n.node_type);
					html +=
						'<div class="kt-strategy-outline-row kt-strategy-outline-row--' +
						esc(nodeType) +
						'" style="--kt-outline-depth:' +
						esc(String(depth)) +
						'" data-testid="structure-outline-' +
						esc(n.name) +
						'">' +
						'<span class="kt-strategy-outline-row__left">' +
						'<span class="kt-strategy-type-token kt-strategy-type-token--' +
						esc(nodeType) +
						'" data-testid="structure-token-' +
						esc(n.name) +
						'">' +
						esc(typeBadge(n.node_type)) +
						"</span> " +
						'<span class="kt-strategy-outline-title kt-strategy-outline-title--' +
						esc(nodeType) +
						'">' +
						esc(n.title) +
						"</span>" +
						"</span>" +
						(n.code
							? '<span class="kt-strategy-outline-code" data-testid="structure-code-' +
								esc(n.name) +
								'">(' +
								esc(n.code) +
								")</span>"
							: "") +
						"</div>";
					if (n.children && n.children.length) html += walk(n.children, depth + 1);
				});
				return html;
			}
			if (!tree.length) {
				return (
					'<p class="text-muted small" data-testid="structure-overview-empty">' +
					esc(__("No structure yet. Add a Program to begin.")) +
					"</p>"
				);
			}
			return '<div class="kt-strategy-outline" data-testid="structure-overview">' + walk(tree, 0) + "</div>";
		}

		renderTable(nodeType) {
			const rows = this.flatNodes.filter((n) => n.node_type === nodeType);
			const addLabels = {
				Program: __("Add Program"),
				SubProgram: __("Add Sub-program"),
				Indicator: __("Add Indicator"),
				Target: __("Add Target"),
			};
			let html =
				'<div class="d-flex justify-content-between align-items-center mb-2">' +
				"<h6 class=\"mb-0\">" +
				esc(nodeType === "SubProgram" ? __("Sub-programs") : nodeType === "Indicator" ? __("Indicators") : nodeType + "s") +
				"</h6>";
			if (!this.readOnly) {
				html +=
					'<button type="button" class="btn btn-default btn-xs kt-context-action" data-add-node-type="' +
					esc(nodeType) +
					'" data-testid="structure-add-' +
					esc(nodeType.toLowerCase()) +
					'">' +
					'<span aria-hidden="true">+</span> ' +
					esc(addLabels[nodeType] || __("Add")) +
					"</button>";
			}
			html += "</div>";
			if (!rows.length) {
				html +=
					'<p class="text-muted small" data-testid="structure-table-empty-' +
					esc(nodeType.toLowerCase()) +
					'">' +
					esc(__("None yet.")) +
					"</p>";
				return html;
			}
			html += '<div class="table-responsive"><table class="table table-sm table-bordered"><thead><tr>';
			if (nodeType === "Program") {
				html += "<th>" + esc(__("Code")) + "</th><th>" + esc(__("Name")) + "</th>";
			} else if (nodeType === "SubProgram") {
				html += "<th>" + esc(__("Code")) + "</th><th>" + esc(__("Name")) + "</th><th>" + esc(__("Parent Program")) + "</th>";
			} else if (nodeType === "Indicator") {
				html += "<th>" + esc(__("Code")) + "</th><th>" + esc(__("Name")) + "</th><th>" + esc(__("Sub-program")) + "</th>";
			} else {
				html += "<th>" + esc(__("Name")) + "</th><th>" + esc(__("Indicator")) + "</th><th>" + esc(__("Period")) + "</th>";
			}
			if (!this.readOnly) {
				html += "<th>" + esc(__("Actions")) + "</th>";
			}
			html += "</tr></thead><tbody>";
			rows.forEach((n) => {
				html += '<tr data-testid="structure-row-' + esc(n.name) + '">';
				if (nodeType === "Target") {
					html +=
						"<td>" +
						esc(n.title) +
						"</td><td>" +
						esc(parentTitle(this.flatNodes, n.parent)) +
						"</td><td>" +
						esc(n.target_year || n.target_period_type || "—") +
						"</td>";
				} else if (nodeType === "Indicator") {
					html +=
						"<td>" +
						esc(n.code || "—") +
						"</td><td>" +
						esc(n.title) +
						"</td><td>" +
						esc(parentTitle(this.flatNodes, n.parent)) +
						"</td>";
				} else if (nodeType === "SubProgram") {
					html +=
						"<td>" +
						esc(n.code || "—") +
						"</td><td>" +
						esc(n.title) +
						"</td><td>" +
						esc(parentTitle(this.flatNodes, n.parent)) +
						"</td>";
				} else {
					html += "<td>" + esc(n.code || "—") + "</td><td>" + esc(n.title) + "</td>";
				}
				if (!this.readOnly) {
					html +=
						'<td class="text-right"><button type="button" class="btn btn-xs btn-link kt-row-action" data-edit-node="' +
						esc(n.name) +
						'" data-testid="structure-edit-' +
						esc(n.name) +
						'">' +
						esc(__("Edit")) +
						"</button></td>";
				}
				html += "</tr>";
			});
			html += "</tbody></table></div>";
			return html;
		}

		parentNodeType(nodeType) {
			if (nodeType === "SubProgram") return "Program";
			if (nodeType === "Indicator") return "SubProgram";
			if (nodeType === "Target") return "Indicator";
			return null;
		}

		parentCandidates(nodeType) {
			const parentType = this.parentNodeType(nodeType);
			if (!parentType) return [];
			return this.flatNodes.filter((n) => n.node_type === parentType);
		}

		parentOptionLabel(node) {
			if (!node) return "";
			const code = node.code ? " (" + node.code + ")" : "";
			return (node.title || node.name) + code;
		}

		parentFieldLabel(nodeType) {
			if (nodeType === "SubProgram") return __("Program");
			if (nodeType === "Indicator") return __("Sub-program");
			if (nodeType === "Target") return __("Indicator");
			return __("Parent");
		}

		emitStructureChanged() {
			document.dispatchEvent(
				new CustomEvent("kt-strategy-structure-changed", {
					detail: { plan_name: this.planName },
				}),
			);
		}

		applyTargetFieldVisibility(d) {
			const measurementType = d.get_value("measurement_type") || "Numeric";
			const periodType = d.get_value("target_period_type") || "Annual";
			const numeric = ["Numeric", "Percentage", "Currency"].includes(measurementType);
			d.set_df_property("target_value", "hidden", numeric ? 0 : 1);
			d.set_df_property("target_unit", "hidden", numeric ? 0 : 1);
			d.set_df_property("target_value_text", "hidden", numeric ? 1 : 0);
			d.set_df_property("baseline_value_numeric", "hidden", numeric ? 0 : 1);
			d.set_df_property("target_year", "hidden", periodType === "Annual" ? 0 : 1);
			d.set_df_property("target_due_date", "hidden", periodType === "Milestone Date" ? 0 : 1);
		}

		openNodeDialog(nodeType, nodeName) {
			if (this.readOnly) {
				frappe.msgprint(__("You have read-only access to this plan."));
				return;
			}
			const me = this;
			const isEdit = !!nodeName;
			const existing = isEdit ? this.flatNodes.find((n) => n.name === nodeName) : null;
			const parentOptions = me.parentCandidates(nodeType);
			const parentOptionMap = {};
			if (nodeType !== "Program" && !parentOptions.length) {
				frappe.msgprint(__("Create the parent level first."));
				return;
			}
			const fields = [];
			if (nodeType !== "Program") {
				const parentLabels = parentOptions.map((n) => {
					const label = me.parentOptionLabel(n);
					parentOptionMap[label] = n.name;
					return label;
				});
				const defaultParentName = existing && existing.parent ? existing.parent : parentOptions[0].name;
				const defaultParent = parentLabels.find((lbl) => parentOptionMap[lbl] === defaultParentName) || parentLabels[0];
				fields.push({
					fieldname: "section_link",
					fieldtype: "Section Break",
					label: __("Hierarchy Link"),
				});
				fields.push({
					fieldname: "parent_name",
					fieldtype: "Select",
					label: me.parentFieldLabel(nodeType),
					reqd: 1,
					options: parentLabels.join("\n"),
					default: defaultParent,
				});
			}
			fields.push(
				{
					fieldname: "section_definition",
					fieldtype: "Section Break",
					label: nodeType === "Indicator" ? __("Indicator Definition") : __("Definition"),
				},
				{
					fieldname: "node_title",
					fieldtype: "Data",
					label: __("Title"),
					reqd: 1,
					default: existing ? existing.title : "",
				},
				{
					fieldname: "node_description",
					fieldtype: "Small Text",
					label: __("Description"),
					default: existing ? existing.description || "" : "",
				},
			);
			if (nodeType === "Target") {
				fields.push(
					{
						fieldname: "section_measurement",
						fieldtype: "Section Break",
						label: __("Measurement"),
					},
					{
						fieldname: "measurement_type",
						fieldtype: "Select",
						label: __("Measurement Type"),
						options: ["Numeric", "Percentage", "Currency", "Milestone", "Boolean"].join("\n"),
						default: existing ? existing.measurement_type || "Numeric" : "Numeric",
					},
					{
						fieldname: "target_period_type",
						fieldtype: "Select",
						label: __("Target Period Type"),
						options: ["Annual", "End of Plan", "Milestone Date"].join("\n"),
						default: existing ? existing.target_period_type || "Annual" : "Annual",
					},
					{
						fieldname: "section_timeframe_colbreak",
						fieldtype: "Column Break",
					},
					{
						fieldname: "target_year",
						fieldtype: "Int",
						label: __("Target Year"),
						default: existing ? existing.target_year : new Date().getFullYear(),
					},
					{
						fieldname: "target_due_date",
						fieldtype: "Date",
						label: __("Target Due Date"),
						default: existing ? existing.target_due_date : "",
					},
					{
						fieldname: "target_value",
						fieldtype: "Float",
						label: __("Target Value"),
						default: existing ? existing.target_value_numeric : 1,
					},
					{
						fieldname: "target_unit",
						fieldtype: "Data",
						label: __("Unit"),
						default: existing ? existing.target_unit || "" : "Unit",
					},
					{
						fieldname: "target_value_text",
						fieldtype: "Small Text",
						label: __("Target Value (Text)"),
						default: existing ? existing.target_value_text || "" : "",
					},
					{
						fieldname: "section_baseline",
						fieldtype: "Section Break",
						label: __("Baseline"),
					},
					{
						fieldname: "baseline_value_numeric",
						fieldtype: "Float",
						label: __("Baseline Value"),
						default: existing ? existing.baseline_value_numeric : null,
					},
					{
						fieldname: "baseline_value_text",
						fieldtype: "Small Text",
						label: __("Baseline Notes"),
						default: existing ? existing.baseline_value_text || "" : "",
					},
					{
						fieldname: "baseline_year",
						fieldtype: "Int",
						label: __("Baseline Year"),
						default: existing ? existing.baseline_year : null,
					},
				);
			}
			const titles = {
				Program: __("New Program"),
				SubProgram: __("New Sub-program"),
				Indicator: __("New Indicator"),
				Target: __("New Target"),
			};
			const d = new frappe.ui.Dialog({
				title: isEdit ? __("Edit {0}", [nodeType]) : titles[nodeType] || __("New"),
				fields: fields,
				primary_action_label: isEdit ? __("Update") : __("Save"),
				primary_action(values) {
					const payload = {
						node_title: values.node_title,
						node_description: values.node_description || "",
					};
					if (values.parent_name && parentOptionMap[values.parent_name]) {
						payload.parent_name = parentOptionMap[values.parent_name];
					}
					if (nodeType === "Target") {
						payload.measurement_type = values.measurement_type || "Numeric";
						payload.target_period_type = values.target_period_type || "Annual";
						payload.target_year = values.target_year;
						payload.target_due_date = values.target_due_date;
						payload.target_value_numeric = values.target_value;
						payload.target_value_text = values.target_value_text || "";
						payload.target_unit = values.target_unit || "";
						payload.baseline_value_numeric = values.baseline_value_numeric;
						payload.baseline_value_text = values.baseline_value_text || "";
						payload.baseline_year = values.baseline_year;
					}
					frappe.call({
						method: isEdit
							? "kentender_strategy.api.strategy_builder.update_strategy_node"
							: "kentender_strategy.api.strategy_builder.create_strategy_node",
						args: {
							plan_name: me.planName,
							parent_name:
								nodeType === "Program"
									? null
									: parentOptionMap[values.parent_name] || values.parent_name || null,
							node_type: nodeType,
							node_name: nodeName,
							initial_data: payload,
							data: payload,
						},
						callback() {
							d.hide();
							me.load();
							me.emitStructureChanged();
							frappe.show_alert({
								message: isEdit ? __("Updated") : __("Saved"),
								indicator: "green",
							});
						},
					});
				},
			});
			d.show();
			if (nodeType === "Target") {
				this.applyTargetFieldVisibility(d);
				d.get_field("measurement_type").$input.on("change", () => this.applyTargetFieldVisibility(d));
				d.get_field("target_period_type").$input.on("change", () => this.applyTargetFieldVisibility(d));
			}
		}

		promptCreate(nodeType) {
			this.openNodeDialog(nodeType, null);
		}

		promptEdit(nodeName) {
			const node = this.flatNodes.find((n) => n.name === nodeName);
			if (!node) return;
			this.openNodeDialog(node.node_type, nodeName);
		}
	}

	kentender_strategy.strategy_structure_panel = {
		mount(hostEl, planName) {
			if (!hostEl || !planName) return;
			const $host = $(hostEl);
			$host.empty();
			const panel = new StructurePanel($host, planName);
			panel.mount();
			return panel;
		},
	};
})();
