import frappe
from frappe import _
from frappe.utils import cint, getdate

NODE_TYPE_ALIASES = {
	"Objective": "Indicator",
	"Output Indicator": "Indicator",
	"Sub-program": "SubProgram",
	"Sub Program": "SubProgram",
}


def normalize_node_type(node_type: str) -> str:
	nt = (node_type or "").strip()
	return NODE_TYPE_ALIASES.get(nt, nt)


def get_plan_or_throw(plan_name: str):
	if not plan_name or not frappe.db.exists("Strategic Plan", plan_name):
		frappe.throw(_("Strategic Plan not found."), frappe.DoesNotExistError)
	return frappe.get_doc("Strategic Plan", plan_name)


def build_tree(plan_name: str) -> dict:
	plan = get_plan_or_throw(plan_name)
	rows = []
	programs = frappe.db.get_all(
		"Strategy Program",
		filters={"strategic_plan": plan_name},
		fields=["name", "program_title", "description", "order_index", "program_code"],
		order_by="order_index asc, name asc",
	)
	for p in programs:
		rows.append(
			{
				"name": p.name,
				"parent": "",
				"node_type": "Program",
				"title": p.program_title,
				"description": p.description or "",
				"order_index": p.order_index or 0,
				"doctype_ref": "Strategy Program",
				"code": p.program_code or "",
			}
		)
		sub_programs = frappe.db.get_all(
			"Sub Program",
			filters={"strategic_plan": plan_name, "program": p.name},
			fields=["name", "title", "sub_program_code"],
			order_by="modified asc, name asc",
		)
		for sp in sub_programs:
			rows.append(
				{
					"name": sp.name,
					"parent": p.name,
					"node_type": "SubProgram",
					"title": sp.title,
					"description": "",
					"order_index": 0,
					"doctype_ref": "Sub Program",
					"code": sp.sub_program_code or "",
				}
			)
			objectives = frappe.db.get_all(
				"Strategy Objective",
				filters={"strategic_plan": plan_name, "sub_program": sp.name},
				fields=["name", "objective_title", "description", "order_index", "objective_code"],
				order_by="order_index asc, name asc",
			)
			for o in objectives:
				rows.append(
					{
						"name": o.name,
						"parent": sp.name,
						"node_type": "Indicator",
						"title": o.objective_title,
						"description": o.description or "",
						"order_index": o.order_index or 0,
						"doctype_ref": "Strategy Objective",
						"code": o.objective_code or "",
					}
				)
				targets = frappe.db.get_all(
					"Strategy Target",
					filters={"strategic_plan": plan_name, "objective": o.name},
					fields=[
						"name",
						"target_title",
						"description",
						"order_index",
						"target_code",
						"measurement_type",
						"target_period_type",
						"target_year",
						"target_due_date",
						"target_value_numeric",
						"target_value_text",
						"target_unit",
						"baseline_value_numeric",
						"baseline_value_text",
						"baseline_year",
					],
					order_by="order_index asc, name asc",
				)
				for t in targets:
					rows.append(
						{
							"name": t.name,
							"parent": o.name,
							"node_type": "Target",
							"title": t.target_title,
							"description": t.description or "",
							"order_index": t.order_index or 0,
							"doctype_ref": "Strategy Target",
							"code": t.target_code or "",
							"measurement_type": t.measurement_type,
							"target_period_type": t.target_period_type,
							"target_year": t.target_year,
							"target_due_date": t.target_due_date,
							"target_value_numeric": t.target_value_numeric,
							"target_value_text": t.target_value_text,
							"target_unit": t.target_unit or "",
							"baseline_value_numeric": t.baseline_value_numeric,
							"baseline_value_text": t.baseline_value_text,
							"baseline_year": t.baseline_year,
						}
					)

	counts = {"programs": 0, "sub_programs": 0, "indicators": 0, "targets": 0}
	for r in rows:
		nt = r["node_type"]
		if nt == "Program":
			counts["programs"] += 1
		elif nt == "SubProgram":
			counts["sub_programs"] += 1
		elif nt == "Indicator":
			counts["indicators"] += 1
		elif nt == "Target":
			counts["targets"] += 1
	counts["objectives"] = counts["indicators"]

	return {
		"plan": {
			"name": plan.name,
			"title": plan.strategic_plan_name,
			"description": plan.description or "",
			"start_year": plan.start_year,
			"end_year": plan.end_year,
			"status": plan.status,
		},
		"nodes": rows,
		"counts": counts,
	}


def validate_new_node(plan_name: str, parent_name: str | None, node_type: str) -> None:
	node_type = normalize_node_type(node_type)
	get_plan_or_throw(plan_name)
	if node_type == "Program":
		if parent_name:
			frappe.throw(_("Program cannot have a parent."))
		return
	if not parent_name:
		frappe.throw(_("Parent node is required."))
	if node_type == "SubProgram":
		if not frappe.db.exists("Strategy Program", parent_name):
			frappe.throw(_("Sub-program must be created under a Program."))
		p = frappe.get_doc("Strategy Program", parent_name)
		if p.strategic_plan != plan_name:
			frappe.throw(_("Parent belongs to a different Strategic Plan."))
	elif node_type == "Indicator":
		if frappe.db.exists("Sub Program", parent_name):
			sp = frappe.get_doc("Sub Program", parent_name)
			if sp.strategic_plan != plan_name:
				frappe.throw(_("Parent belongs to a different Strategic Plan."))
			return
		if frappe.db.exists("Strategy Program", parent_name):
			frappe.throw(
				_("Indicator must be created under a Sub-program, not directly under a Program."),
				title=_("Invalid hierarchy"),
			)
		frappe.throw(_("Indicator must be created under a Sub-program."))
	elif node_type == "Target":
		if not frappe.db.exists("Strategy Objective", parent_name):
			frappe.throw(_("Target must be created under an Indicator."))
		o = frappe.get_doc("Strategy Objective", parent_name)
		if o.strategic_plan != plan_name:
			frappe.throw(_("Parent belongs to a different Strategic Plan."))
	else:
		frappe.throw(_("Invalid node type."))


def _next_order_index_program(plan_name: str) -> int:
	rows = frappe.db.get_all(
		"Strategy Program",
		filters={"strategic_plan": plan_name},
		fields=["order_index"],
		order_by="order_index desc",
		limit=1,
	)
	if not rows:
		return 0
	return (rows[0].order_index or 0) + 1


def _next_order_index_objective(plan_name: str, sub_program_name: str) -> int:
	rows = frappe.db.get_all(
		"Strategy Objective",
		filters={"strategic_plan": plan_name, "sub_program": sub_program_name},
		fields=["order_index"],
		order_by="order_index desc",
		limit=1,
	)
	if not rows:
		return 0
	return (rows[0].order_index or 0) + 1


def _next_order_index_target(plan_name: str, objective_name: str) -> int:
	rows = frappe.db.get_all(
		"Strategy Target",
		filters={"strategic_plan": plan_name, "objective": objective_name},
		fields=["order_index"],
		order_by="order_index desc",
		limit=1,
	)
	if not rows:
		return 0
	return (rows[0].order_index or 0) + 1


def create_node(
	plan_name: str,
	parent_name: str | None,
	node_type: str,
	initial_data: dict | None = None,
) -> str:
	node_type = normalize_node_type(node_type)
	validate_new_node(plan_name, parent_name, node_type)
	data = initial_data or {}
	if node_type == "Program":
		doc = frappe.get_doc(
			{
				"doctype": "Strategy Program",
				"strategic_plan": plan_name,
				"program_title": data.get("node_title") or data.get("program_title") or _("Untitled"),
				"description": data.get("node_description") or data.get("description"),
				"order_index": _next_order_index_program(plan_name),
			}
		)
		doc.insert()
		return doc.name

	if node_type == "SubProgram":
		prog = frappe.get_doc("Strategy Program", parent_name)
		doc = frappe.get_doc(
			{
				"doctype": "Sub Program",
				"strategic_plan": plan_name,
				"program": parent_name,
				"title": data.get("node_title") or data.get("title") or _("Untitled"),
			}
		)
		doc.insert()
		return doc.name

	if node_type == "Indicator":
		sp = frappe.get_doc("Sub Program", parent_name)
		doc = frappe.get_doc(
			{
				"doctype": "Strategy Objective",
				"strategic_plan": plan_name,
				"program": sp.program,
				"sub_program": parent_name,
				"objective_title": data.get("node_title") or data.get("objective_title") or _("Untitled"),
				"description": data.get("node_description") or data.get("description"),
				"order_index": _next_order_index_objective(plan_name, parent_name),
			}
		)
		doc.insert()
		return doc.name

	obj = frappe.get_doc("Strategy Objective", parent_name)
	mt = data.get("measurement_type") or "Numeric"
	ptype = data.get("target_period_type") or "Annual"
	start_y = frappe.db.get_value("Strategic Plan", plan_name, "start_year")
	default_year = cint(start_y) if start_y is not None else cint(frappe.utils.today()[:4])

	row = {
		"doctype": "Strategy Target",
		"strategic_plan": plan_name,
		"program": obj.program,
		"objective": parent_name,
		"target_title": data.get("node_title") or data.get("target_title") or _("Untitled"),
		"description": data.get("node_description") or data.get("description"),
		"order_index": _next_order_index_target(plan_name, parent_name),
		"measurement_type": mt,
		"target_period_type": ptype,
		"baseline_value_numeric": data.get("baseline_value_numeric"),
		"baseline_value_text": data.get("baseline_value_text"),
		"baseline_year": data.get("baseline_year"),
	}
	if ptype == "Annual":
		ty = data.get("target_year")
		if ty is None or ty == "":
			ty = default_year
		row["target_year"] = cint(ty)
		row["target_due_date"] = None
	elif ptype == "End of Plan":
		row["target_year"] = None
		row["target_due_date"] = None
	else:
		row["target_year"] = None
		dd = data.get("target_due_date")
		row["target_due_date"] = getdate(dd) if dd else getdate(frappe.utils.today())

	if mt in ("Numeric", "Percentage", "Currency"):
		nv = data.get("target_value_numeric")
		if nv is None and data.get("target_value") is not None:
			nv = data.get("target_value")
		row["target_value_numeric"] = nv if nv is not None else 0
		if mt == "Percentage":
			row["target_unit"] = "Percent"
		else:
			row["target_unit"] = (data.get("target_unit") or "").strip() or ("KES" if mt == "Currency" else _("Unit"))
		row["target_value_text"] = ""
	else:
		row["target_value_text"] = (data.get("target_value_text") or "").strip() or _("Description")
		row["target_value_numeric"] = None
	doc = frappe.get_doc(row)
	doc.insert()
	return doc.name


def update_node(node_name: str, data: dict) -> None:
	if frappe.db.exists("Strategy Program", node_name):
		doc = frappe.get_doc("Strategy Program", node_name)
		if "node_title" in data and data["node_title"] is not None:
			doc.program_title = data["node_title"]
		if "node_description" in data and data["node_description"] is not None:
			doc.description = data["node_description"]
		doc.save()
		return
	if frappe.db.exists("Sub Program", node_name):
		doc = frappe.get_doc("Sub Program", node_name)
		if data.get("parent_name"):
			pname = data["parent_name"]
			if not frappe.db.exists("Strategy Program", pname):
				frappe.throw(_("Parent program not found."))
			parent_prog = frappe.get_doc("Strategy Program", pname)
			doc.program = parent_prog.name
			doc.strategic_plan = parent_prog.strategic_plan
		if "node_title" in data and data["node_title"] is not None:
			doc.title = data["node_title"]
		if "title" in data and data["title"] is not None:
			doc.title = data["title"]
		doc.save()
		return
	if frappe.db.exists("Strategy Objective", node_name):
		doc = frappe.get_doc("Strategy Objective", node_name)
		if data.get("parent_name"):
			spname = data["parent_name"]
			if not frappe.db.exists("Sub Program", spname):
				frappe.throw(_("Parent sub-program not found."))
			sub_program = frappe.get_doc("Sub Program", spname)
			doc.sub_program = sub_program.name
			doc.program = sub_program.program
			doc.strategic_plan = sub_program.strategic_plan
		if "node_title" in data and data["node_title"] is not None:
			doc.objective_title = data["node_title"]
		if "node_description" in data and data["node_description"] is not None:
			doc.description = data["node_description"]
		doc.save()
		return
	if frappe.db.exists("Strategy Target", node_name):
		doc = frappe.get_doc("Strategy Target", node_name)
		if data.get("parent_name"):
			oname = data["parent_name"]
			if not frappe.db.exists("Strategy Objective", oname):
				frappe.throw(_("Parent indicator not found."))
			objective = frappe.get_doc("Strategy Objective", oname)
			doc.objective = objective.name
			doc.program = objective.program
			doc.strategic_plan = objective.strategic_plan
		for src, dest in (
			("node_title", "target_title"),
			("node_description", "description"),
			("target_title", "target_title"),
			("description", "description"),
		):
			if src in data and data[src] is not None:
				doc.set(dest, data[src])
		for f in (
			"measurement_type",
			"target_period_type",
			"target_value_numeric",
			"target_value_text",
			"target_unit",
			"baseline_value_numeric",
			"baseline_value_text",
			"baseline_year",
		):
			if f in data and data[f] is not None:
				doc.set(f, data[f])
		if "target_year" in data:
			vy = data["target_year"]
			doc.target_year = cint(vy) if vy not in (None, "") else None
		if "target_due_date" in data:
			vd = data["target_due_date"]
			doc.target_due_date = getdate(vd) if vd not in (None, "") else None
		if data.get("target_value") is not None and data.get("target_value") != "":
			doc.target_value_numeric = data.get("target_value")
		doc.save()
		return
	frappe.throw(_("Strategy node not found."), frappe.DoesNotExistError)


def delete_node(node_name: str) -> None:
	if frappe.db.exists("Strategy Program", node_name):
		if frappe.db.count("Sub Program", {"program": node_name}):
			frappe.throw(_("Delete sub-programs under this program first."))
		if frappe.db.count("Strategy Target", {"program": node_name}):
			frappe.throw(_("Delete targets under this program first."))
		frappe.delete_doc("Strategy Program", node_name)
		return
	if frappe.db.exists("Sub Program", node_name):
		if frappe.db.count("Strategy Objective", {"sub_program": node_name}):
			frappe.throw(_("Delete indicators under this sub-program first."))
		frappe.delete_doc("Sub Program", node_name)
		return
	if frappe.db.exists("Strategy Objective", node_name):
		if frappe.db.count("Strategy Target", {"objective": node_name}):
			frappe.throw(_("Delete targets under this indicator first."))
		frappe.delete_doc("Strategy Objective", node_name)
		return
	if frappe.db.exists("Strategy Target", node_name):
		frappe.delete_doc("Strategy Target", node_name)
		return
	frappe.throw(_("Strategy node not found."), frappe.DoesNotExistError)
