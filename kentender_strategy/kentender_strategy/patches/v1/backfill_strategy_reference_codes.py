import frappe


def execute():
	_backfill_sub_program_codes()
	_backfill_strategy_target_codes()


def _backfill_sub_program_codes():
	if not frappe.db.exists("DocType", "Sub Program"):
		return
	if not frappe.get_meta("Sub Program").has_field("sub_program_code"):
		return

	rows = frappe.get_all(
		"Sub Program",
		fields=["name", "program", "sub_program_code"],
		order_by="program asc, modified asc, creation asc",
		limit=100000,
	)
	if not rows:
		return

	program_names = sorted({r.program for r in rows if r.program})
	program_codes = {}
	if program_names:
		for p in frappe.get_all(
			"Strategy Program",
			filters={"name": ["in", program_names]},
			fields=["name", "program_code"],
			limit=100000,
		):
			program_codes[p.name] = _clean_code(p.program_code)

	used_per_program = {}
	counter_per_program = {}
	for row in rows:
		program = row.program or ""
		used = used_per_program.setdefault(program, set())
		existing = _clean_code(row.sub_program_code)
		if existing:
			used.add(existing)

	for row in rows:
		if _clean_code(row.sub_program_code):
			continue
		program = row.program or ""
		used = used_per_program.setdefault(program, set())
		counter_per_program[program] = counter_per_program.get(program, 0) + 1
		base = program_codes.get(program) or _fallback_from_name(program, "PRG")
		candidate = f"SUB-{base}-{counter_per_program[program]:03d}"
		while candidate in used:
			counter_per_program[program] += 1
			candidate = f"SUB-{base}-{counter_per_program[program]:03d}"
		frappe.db.set_value("Sub Program", row.name, "sub_program_code", candidate, update_modified=False)
		used.add(candidate)


def _backfill_strategy_target_codes():
	if not frappe.db.exists("DocType", "Strategy Target"):
		return
	if not frappe.get_meta("Strategy Target").has_field("target_code"):
		return

	rows = frappe.get_all(
		"Strategy Target",
		fields=["name", "objective", "target_code"],
		order_by="objective asc, modified asc, creation asc",
		limit=100000,
	)
	if not rows:
		return

	objective_names = sorted({r.objective for r in rows if r.objective})
	objective_codes = {}
	if objective_names:
		for o in frappe.get_all(
			"Strategy Objective",
			filters={"name": ["in", objective_names]},
			fields=["name", "objective_code"],
			limit=100000,
		):
			objective_codes[o.name] = _clean_code(o.objective_code)

	used_per_objective = {}
	counter_per_objective = {}
	for row in rows:
		objective = row.objective or ""
		used = used_per_objective.setdefault(objective, set())
		existing = _clean_code(row.target_code)
		if existing:
			used.add(existing)

	for row in rows:
		if _clean_code(row.target_code):
			continue
		objective = row.objective or ""
		used = used_per_objective.setdefault(objective, set())
		counter_per_objective[objective] = counter_per_objective.get(objective, 0) + 1
		base = objective_codes.get(objective) or _fallback_from_name(objective, "OBJ")
		candidate = f"TGT-{base}-{counter_per_objective[objective]:03d}"
		while candidate in used:
			counter_per_objective[objective] += 1
			candidate = f"TGT-{base}-{counter_per_objective[objective]:03d}"
		frappe.db.set_value("Strategy Target", row.name, "target_code", candidate, update_modified=False)
		used.add(candidate)


def _clean_code(value: str | None) -> str:
	return (value or "").strip().upper()


def _fallback_from_name(name: str | None, prefix: str) -> str:
	token = (name or "").strip().upper().replace("-", "")
	token = "".join(ch for ch in token if ch.isalnum())
	if not token:
		token = prefix
	return token[-6:]
