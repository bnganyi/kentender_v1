// Strategy Builder — two-pane hierarchy editor for one Strategic Plan.
frappe.provide("kentender_strategy.strategy_builder");

(function () {
	function planFromRoute() {
		const r = frappe.get_route() || [];
		return r.length > 1 ? r[1] : null;
	}

	function nestNodes(flat) {
		const byParent = {};
		flat.forEach((n) => {
			const p = n.parent || "";
			if (!byParent[p]) {
				byParent[p] = [];
			}
			byParent[p].push(n);
		});
		function walk(parentId) {
			return (byParent[parentId] || []).map((n) => ({
				...n,
				children: walk(n.name),
			}));
		}
		return walk("");
	}

	class StrategyBuilder {
		constructor($wrapper) {
			this.$wrapper = $wrapper;
			this.planName = null;
			this.flatNodes = [];
			this.nodeByName = {};
			this.selectedName = null;
			this.creatingMode = null;
		}

		init() {
			this.planName = planFromRoute();
			if (!this.planName) {
				this.$wrapper.html(
					`<div class="alert alert-warning">${__("Open this page from a Strategic Plan (missing plan in the URL).")}</div>`,
				);
				return;
			}
			this.renderShell();
			const me = this;
			$(document).off("page-change.kt_sb_plan").on("page-change.kt_sb_plan", () => {
				const r = frappe.get_route() || [];
				if (r[0] !== "strategy-builder") {
					return;
				}
				const next = r[1] || null;
				if (next && next !== me.planName) {
					me.planName = next;
					me.selectedName = null;
					me.loadTree();
				}
			});
			this.loadTree();
		}

		renderShell() {
			this.$wrapper.html(`
				<div class="kt-strategy-builder" data-testid="strategy-builder-page">
					<div class="page-head-content pb-2">
						<div class="kt-sb-readiness text-muted small mb-2" data-testid="strategy-readiness"></div>
					</div>
					<div class="row kt-sb-row">
						<div class="col-md-4 border-end">
							<div class="kt-sb-tree-pane" data-testid="strategy-tree-pane">
								<div class="btn-group mb-3 flex-wrap" role="group">
									<button type="button" class="btn btn-xs btn-primary" data-testid="add-program-button">${__("Add Program")}</button>
									<button type="button" class="btn btn-xs btn-default" data-testid="add-objective-button" disabled>${__("Add Objective")}</button>
									<button type="button" class="btn btn-xs btn-default" data-testid="add-target-button" disabled>${__("Add Target")}</button>
								</div>
								<div class="kt-sb-tree-list"></div>
							</div>
						</div>
						<div class="col-md-8">
							<div class="kt-sb-editor-pane" data-testid="strategy-editor-pane">
								<div class="kt-sb-empty-editor text-muted" data-testid="empty-editor-hint">${__(
									"Select a node from the left, or create a new Program to begin.",
								)}</div>
								<div class="kt-sb-editor-form" style="display:none;">
									<div class="mb-2"><span class="badge" data-testid="selected-node-type"></span></div>
									<div class="form-group">
										<label>${__("Title")}</label>
										<input type="text" class="form-control" data-testid="node-title-input" />
									</div>
									<div class="form-group">
										<label>${__("Description")}</label>
										<textarea class="form-control" rows="3" data-testid="node-description-input"></textarea>
									</div>
									<div class="kt-sb-target-fields" style="display:none;">
										<div class="form-group">
											<label>${__("Target Year")}</label>
											<input type="number" class="form-control" data-testid="target-year-input" />
										</div>
										<div class="form-group">
											<label>${__("Target Value")}</label>
											<input type="number" step="any" class="form-control" data-testid="target-value-input" />
										</div>
										<div class="form-group">
											<label>${__("Target Unit")}</label>
											<input type="text" class="form-control" data-testid="target-unit-input" />
										</div>
									</div>
									<button type="button" class="btn btn-primary" data-testid="save-node-button">${__("Save")}</button>
									<button type="button" class="btn btn-default ml-2" data-testid="delete-node-button">${__("Delete")}</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			`);

			this.$treeList = this.$wrapper.find(".kt-sb-tree-list");
			this.$readiness = this.$wrapper.find("[data-testid='strategy-readiness']");
			this.$emptyHint = this.$wrapper.find("[data-testid='empty-editor-hint']");
			this.$editorForm = this.$wrapper.find(".kt-sb-editor-form");
			this.$targetFields = this.$wrapper.find(".kt-sb-target-fields");

			const me = this;
			this.$wrapper.find("[data-testid='add-program-button']").on("click", () => me.promptCreate("Program"));
			this.$wrapper.find("[data-testid='add-objective-button']").on("click", () => me.promptCreate("Objective"));
			this.$wrapper.find("[data-testid='add-target-button']").on("click", () => me.promptCreate("Target"));
			this.$wrapper.find("[data-testid='save-node-button']").on("click", () => me.saveSelected());
			this.$wrapper.find("[data-testid='delete-node-button']").on("click", () => me.deleteSelected());
		}

		loadTree() {
			const me = this;
			return frappe
				.call({
					method: "kentender_strategy.api.strategy_builder.get_strategy_tree",
					args: { plan_name: me.planName },
				})
				.then((r) => {
					me.flatNodes = (r.message && r.message.nodes) || [];
					me.nodeByName = {};
					me.flatNodes.forEach((n) => {
						me.nodeByName[n.name] = n;
					});
					const counts = (r.message && r.message.counts) || {};
					me.$readiness.text(
						`${__("Readiness")}: ${__("Programs")}: ${counts.programs || 0} · ${__("Objectives")}: ${counts.objectives || 0} · ${__("Targets")}: ${counts.targets || 0}`,
					);
					me.renderTree();
					me.updateAddButtons();
					if (me.selectedName && me.nodeByName[me.selectedName]) {
						me.fillEditor(me.nodeByName[me.selectedName]);
					} else if (me.selectedName) {
						me.selectedName = null;
						me.showEmptyEditor();
					} else {
						me.showEmptyEditor();
					}
				});
		}

		labelForNode(n) {
			const kind = n.node_type;
			const t = n.title || "";
			if (kind === "Target" && n.target_year) {
				return `${kind} — ${n.target_year}: ${t}`;
			}
			return `${kind} — ${t}`;
		}

		renderTree() {
			const me = this;
			const tree = nestNodes(me.flatNodes);
			if (!me.flatNodes.length) {
				this.$treeList.html(
					`<div class="text-muted small" data-testid="empty-tree-message">${__(
						"No programs yet. Use Add Program to begin.",
					)}</div>`,
				);
				return;
			}
			function renderLevel(nodes, depth) {
				const $ul = $(`<ul class="list-unstyled kt-sb-tree-level" style="padding-left:${depth ? 12 : 0}px"></ul>`);
				nodes.forEach((n) => {
					const $li = $("<li class='mb-1'></li>");
					const active = me.selectedName === n.name ? "font-weight-bold" : "";
					const label = me.labelForNode(n);
					$li.append(
						`<button type="button" class="btn btn-link btn-sm text-left p-0 ${active} kt-sb-node-btn" data-node="${frappe.utils.escape_html(
							n.name,
						)}">${frappe.utils.escape_html(label)}</button>`,
					);
					const childTree = renderLevel(n.children || [], depth + 1);
					$li.append(childTree);
					$ul.append($li);
				});
				return $ul;
			}
			const $root = renderLevel(tree, 0);
			me.$treeList.empty().append($root);
			me.$treeList.find(".kt-sb-node-btn").each(function () {
				const name = $(this).attr("data-node");
				$(this)
					.closest("li")
					.attr("data-testid", "tree-node-" + name);
			});
			me.$treeList.find(".kt-sb-node-btn").on("click", function () {
				const name = $(this).attr("data-node");
				me.selectNode(name);
			});
		}

		selectNode(name) {
			this.selectedName = name;
			this.creatingMode = null;
			this.renderTree();
			const n = this.nodeByName[name];
			if (n) {
				this.fillEditor(n);
			}
			this.updateAddButtons();
		}

		selectedNodeType() {
			if (!this.selectedName) {
				return null;
			}
			const n = this.nodeByName[this.selectedName];
			return n ? n.node_type : null;
		}

		updateAddButtons() {
			const $obj = this.$wrapper.find("[data-testid='add-objective-button']");
			const $tar = this.$wrapper.find("[data-testid='add-target-button']");
			const t = this.selectedNodeType();
			$obj.prop("disabled", t !== "Program");
			$tar.prop("disabled", t !== "Objective");
		}

		showEmptyEditor() {
			this.$emptyHint.show();
			this.$editorForm.hide();
		}

		fillEditor(n) {
			this.$emptyHint.hide();
			this.$editorForm.show();
			this.$wrapper.find("[data-testid='selected-node-type']").text(n.node_type);
			this.$wrapper.find("[data-testid='node-title-input']").val(n.title || "");
			this.$wrapper.find("[data-testid='node-description-input']").val(n.description || "");
			if (n.node_type === "Target") {
				this.$targetFields.show();
				this.$wrapper.find("[data-testid='target-year-input']").val(n.target_year || "");
				this.$wrapper.find("[data-testid='target-value-input']").val(
					n.target_value !== null && n.target_value !== undefined ? n.target_value : "",
				);
				this.$wrapper.find("[data-testid='target-unit-input']").val(n.target_unit || "");
			} else {
				this.$targetFields.hide();
			}
		}

		promptCreate(nodeType) {
			const me = this;
			let parent = null;
			if (nodeType === "Objective") {
				if (me.selectedNodeType() !== "Program") {
					return;
				}
				parent = me.selectedName;
			} else if (nodeType === "Target") {
				if (me.selectedNodeType() !== "Objective") {
					return;
				}
				parent = me.selectedName;
			}

			const fields = [
				{ fieldname: "node_title", fieldtype: "Data", label: __("Title"), reqd: 1 },
				{ fieldname: "node_description", fieldtype: "Small Text", label: __("Description") },
			];
			if (nodeType === "Target") {
				fields.push(
					{ fieldname: "target_year", fieldtype: "Int", label: __("Target Year") },
					{ fieldname: "target_value", fieldtype: "Float", label: __("Target Value") },
					{ fieldname: "target_unit", fieldtype: "Data", label: __("Target Unit") },
				);
			}

			const d = new frappe.ui.Dialog({
				title:
					nodeType === "Program"
						? __("New Program")
						: nodeType === "Objective"
							? __("New Objective")
							: __("New Target"),
				fields,
				primary_action_label: __("Create"),
				primary_action(values) {
					const data = {
						node_title: values.node_title,
						node_description: values.node_description || "",
					};
					if (nodeType === "Target") {
						data.target_year = values.target_year;
						data.target_value = values.target_value;
						data.target_unit = values.target_unit || "";
					}
					frappe.call({
						method: "kentender_strategy.api.strategy_builder.create_strategy_node",
						args: {
							plan_name: me.planName,
							parent_name: parent,
							node_type: nodeType,
							initial_data: data,
						},
						callback(r) {
							d.hide();
							const newName = r.message && r.message.name;
							me.loadTree().then(() => {
								if (newName) {
									me.selectNode(newName);
								}
							});
							frappe.show_alert({
								message:
									nodeType === "Program"
										? __("Program saved")
										: nodeType === "Objective"
											? __("Objective saved")
											: __("Target saved"),
								indicator: "green",
							});
						},
					});
				},
			});
			d.show();
		}

		saveSelected() {
			const me = this;
			if (!me.selectedName) {
				return;
			}
			const n = me.nodeByName[me.selectedName];
			if (!n) {
				return;
			}
			const data = {
				node_title: me.$wrapper.find("[data-testid='node-title-input']").val(),
				node_description: me.$wrapper.find("[data-testid='node-description-input']").val(),
			};
			if (n.node_type === "Target") {
				data.target_year = me.$wrapper.find("[data-testid='target-year-input']").val();
				data.target_value = me.$wrapper.find("[data-testid='target-value-input']").val();
				data.target_unit = me.$wrapper.find("[data-testid='target-unit-input']").val();
			}
			frappe.call({
				method: "kentender_strategy.api.strategy_builder.update_strategy_node",
				args: { node_name: me.selectedName, data },
				callback() {
					me.loadTree();
					const label =
						n.node_type === "Program"
							? __("Program saved")
							: n.node_type === "Objective"
								? __("Objective saved")
								: __("Target saved");
					frappe.show_alert({ message: label, indicator: "green" });
				},
			});
		}

		deleteSelected() {
			const me = this;
			if (!me.selectedName) {
				return;
			}
			frappe.confirm(__("Delete this node?"), () => {
				frappe.call({
					method: "kentender_strategy.api.strategy_builder.delete_strategy_node",
					args: { node_name: me.selectedName },
					callback() {
						me.selectedName = null;
						me.loadTree();
						frappe.show_alert({ message: __("Deleted"), indicator: "green" });
					},
				});
			});
		}
	}

	function bootStrategyBuilderPage() {
		const el = frappe.pages["strategy-builder"];
		if (!el) {
			return;
		}
		const $w = $(el);
		if ($w.data("kt_sb")) {
			return;
		}
		const sb = new StrategyBuilder($w);
		$w.data("kt_sb", sb);
		sb.init();
		$w.on("show", function () {
			const s = $w.data("kt_sb");
			if (s && s.planName) {
				s.loadTree();
			}
		});
	}

	bootStrategyBuilderPage();
})();
