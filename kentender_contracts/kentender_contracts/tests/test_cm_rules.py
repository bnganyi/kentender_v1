# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""CM-CHG-001 v0.8 §4.1, §19.3, §19.7 (tracker CM8-309; CM-AC-30, 36, 71 started): the 18 rules and 6 legal questions are in the code exactly as the
reconciled register has them; a rule that is not Verified refuses only the consequential actions it governs; an open legal question holds only the branch
it names; the synthetic profile exists only on a simulation site and keeps every statutory ceiling; and no deadline is a constant of the code."""

from __future__ import annotations

import dataclasses
import re
from pathlib import Path

import frappe
from frappe.tests import IntegrationTestCase

from kentender_contracts.rules import gate, profile, register
from kentender_contracts.services import errors, simulation

DOCS = Path(frappe.get_app_path("kentender_contracts")).resolve().parents[1] / "docs/mvp-1-r1/21_contract_management"
APP = Path(frappe.get_app_path("kentender_contracts")).resolve()


def md_rows(prefix):
	rows = []
	for line in (DOCS / "reconciliation/rule_register.md").read_text().splitlines():
		if line.startswith(prefix):
			rows.append([c.strip() for c in line.strip().strip("|").split(" | ")])
	return rows


def spec_command_names():
	lines = (DOCS / "KenTender_CM-CHG-001_Contract_Management_v0_8.md").read_text().splitlines()
	start = next(i for i, line in enumerate(lines) if line.startswith("## 7."))
	end = next(i for i, line in enumerate(lines) if line.startswith("## 8."))
	# §7 names a command in the first column of its table (with or without backticks) and in backticks in the paragraphs around it
	names = set(re.findall(r"`([A-Z][A-Za-z0-9]+)`", "\n".join(lines[start:end])))
	for line in lines[start:end]:
		if line.startswith("|") and not line.startswith("|---"):
			names |= set(re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z0-9]+)+\b", line.split("|")[1]))
	return names


class TestRuleRegister(IntegrationTestCase):
	def test_the_code_has_exactly_the_registers_eighteen_rules_in_order(self):
		rows = md_rows("| CM-R-")
		self.assertEqual([r.id for r in register.RULES], [f"CM-R-{n:02d}" for n in range(1, 19)])
		for rule, row in zip(register.RULES, rows):
			ident, name = row[0].split(" ", 1)
			self.assertEqual((rule.id, rule.name, rule.source, rule.input_event, rule.hold_key), (ident, name, row[1], row[3], row[4].strip("`")), rule.id)
			self.assertEqual(tuple(int(p) for p in re.findall(r"\d+", row[6])), rule.phases, rule.id)
			self.assertEqual(tuple(re.findall(r"LQ-\d+", row[7])), rule.questions, rule.id)
			spec_commands = [c.strip() for c in re.split(r"[;,]", re.sub(r"\(.*?\)", "", row[5])) if c.strip()]
			self.assertEqual([c for c in spec_commands if re.fullmatch(r"[A-Z][A-Za-z]+", c)], list(rule.commands), rule.id)

	def test_every_rule_is_classified_and_names_real_commands(self):
		names = spec_command_names()
		for rule in register.RULES:
			self.assertTrue(rule.classes, rule.id)
			self.assertFalse(set(rule.commands) - names, f"{rule.id} names a command that is not in section 7: {set(rule.commands) - names}")
		self.assertTrue(register.BY_ID["CM-R-18"].dependent_action)

	def test_the_code_has_exactly_the_six_legal_questions_and_they_agree_with_the_rules(self):
		rows = md_rows("| LQ-")
		self.assertEqual([q.id for q in register.QUESTIONS], [f"LQ-0{n}" for n in range(1, 7)])
		for question, row in zip(register.QUESTIONS, rows):
			self.assertEqual((question.id, question.hold_key), (row[0], row[3].strip("`")))
			self.assertTrue(row[1].startswith(question.reviewer + ":"), question.id)
		names = spec_command_names()
		for question in register.QUESTIONS:
			self.assertFalse({c for c, _ in question.holds} - names, question.id)
			if not question.release_gate_only:
				for rule_id in question.rules:
					self.assertIn(question.id, register.BY_ID[rule_id].questions, f"{question.id} is not on {rule_id}")
		for rule in register.RULES:
			for q in rule.questions:
				self.assertIn(rule.id, register.QUESTION_BY_ID[q].rules)

	def test_lq_01_is_a_release_gate_and_holds_no_runtime_action(self):
		self.assertEqual((register.QUESTION_BY_ID["LQ-01"].holds, register.QUESTION_BY_ID["LQ-01"].release_gate_only), ((), True))


class TestProfiles(IntegrationTestCase):
	def test_each_parameter_cites_a_rule_and_a_locator_and_the_statutory_values_are_the_specifications(self):
		for p in profile.SYNTHETIC.parameters:
			self.assertIn(p.rule, register.BY_ID)
			self.assertTrue(p.locator and p.unit, p.name)
		values = {p.name: p.value for p in profile.STATUTORY}
		self.assertEqual((values["goods_quantity_increase_ceiling_percent"], values["cumulative_goods_value_increase_ceiling_percent"]), (15, 25))
		self.assertEqual((values["advance_cap_percent"], values["performance_security_cap_percent"], values["security_return_days"]), (20, 10, 30))
		self.assertEqual(values["ag_clearance_threshold"], 5_000_000_000)

	def test_test_mode_keeps_every_statutory_ceiling_and_the_delay_percentage_is_never_production_law(self):
		self.assertEqual({p.name: p.value for p in profile.STATUTORY}, {p.name: p.value for p in profile.SYNTHETIC.parameters if p in profile.STATUTORY})
		self.assertEqual(profile.PRODUCTION.parameters, profile.STATUTORY)
		with self.assertRaises(KeyError):
			profile.PRODUCTION.parameter("delay_rate_per_day")
		self.assertEqual(profile.SYNTHETIC.parameter("delay_rate_per_day").value, 0.001)

	def test_the_production_profile_is_draft_and_the_synthetic_one_is_a_classification(self):
		self.assertEqual((profile.PRODUCTION.status, profile.PRODUCTION.synthetic, profile.PRODUCTION.resolved_questions), (profile.DRAFT, False, ()))
		self.assertEqual((profile.SYNTHETIC.status, profile.SYNTHETIC.synthetic), (profile.VERIFIED, True))

	def test_no_deadline_is_a_constant_of_the_code(self):
		"""CM-AC-30: an invalidated Regulations-only deadline cannot appear as a verified statutory one. The only day counts are parameters of a profile with a locator."""
		pattern = re.compile(r"(\b(14|30|60)\b\s*(\*\s*24\b|-?\s*days?\b|_days\b))|(days\s*=\s*(14|30|60)\b)|(timedelta\(days=(14|30|60)\b)", re.I)
		offenders = []
		for path in APP.rglob("*.py"):
			rel = path.relative_to(APP).as_posix()
			if rel.startswith("tests/") or rel in ("rules/profile.py", "hooks.py") or "/patches/" in rel or rel.startswith("contract_management/doctype/"):
				continue
			for n, line in enumerate(path.read_text().splitlines(), 1):
				if line.lstrip().startswith(("#", '"""')):
					continue
				if pattern.search(line):
					offenders.append(f"{rel}:{n}: {line.strip()[:100]}")
		self.assertEqual(offenders, [])


class TestRuleGate(IntegrationTestCase):
	def setUp(self):
		self.flags = {flag: frappe.conf.get(flag) for flag in simulation.FLAGS}
		frappe.conf.kt_cm_simulation_environment = 1  # the synthetic profile is available

	def tearDown(self):
		for flag, value in self.flags.items():
			frappe.conf[flag] = value

	def codes(self, guards):
		return [(r["code"], r["detail"].get("rule") or r["detail"].get("question")) for r in guards.reasons]

	def test_a_draft_production_profile_refuses_every_rule_that_governs_the_command_and_names_each(self):
		guards = gate.reasons("RequestContractSignatures", profile.PRODUCTION)
		self.assertEqual(self.codes(guards), [("CM_RULE", r) for r in ("CM-R-01", "CM-R-02", "CM-R-03", "CM-R-04", "CM-R-08", "CM-R-18")])
		first = guards.reasons[0]["detail"]
		self.assertEqual((first["profile"], first["profile_status"], first["hold_key"], first["holder"]), ("KE-PPADA-2015", "Draft", "FORMATION_AUTHORITY", "Legal/procurement owner"))
		with self.assertRaises(errors.ContractError) as caught:
			gate.require("RequestContractSignatures", profile.PRODUCTION)
		self.assertEqual(caught.exception.code, "CM_RULE")
		self.assertEqual(len(caught.exception.reasons), 6)

	def test_factual_and_protective_commands_are_not_governed_so_a_draft_profile_never_stops_them(self):
		for command in ("RecordContractIssue", "RecordInspectionObservationsDraft", "GetContractWorkspace", "ReceiveSupplierInvoice"):
			self.assertEqual(self.codes(gate.reasons(command, profile.PRODUCTION)), [], command)

	def test_a_suspended_rule_stops_only_what_it_governs(self):
		suspended = dataclasses.replace(profile.SYNTHETIC, suspended_rules=("CM-R-03",))
		self.assertEqual(self.codes(gate.reasons("RequestContractSignatures", suspended)), [("CM_RULE", "CM-R-03")])
		self.assertEqual(gate.reasons("RequestContractSignatures", suspended).reasons[0]["detail"]["profile_status"], "Suspended")
		self.assertEqual(self.codes(gate.reasons("SignContractVersion", suspended)), [])

	def test_a_legal_question_holds_only_the_branch_it_names(self):
		verified = dataclasses.replace(profile.SYNTHETIC, resolved_questions=())
		self.assertEqual(self.codes(gate.reasons("DecideContractChange", verified)), [])
		held = gate.reasons("DecideContractChange", verified, {"early_total_increase"})
		self.assertEqual(self.codes(held), [("CM_HOLD", "LQ-02")])
		detail = held.reasons[0]["detail"]
		self.assertEqual((detail["hold"], detail["holder"], detail["branch"]), ("CHANGE_EARLY_TOTAL_INCREASE", "procurement/legal partner", "early_total_increase"))
		self.assertEqual(self.codes(gate.reasons("DecideContractChange", verified, {"some_other_branch"})), [])
		self.assertEqual(self.codes(gate.reasons("SubmitContractChangeForDecision", verified, {"early_total_increase"})), [("CM_HOLD", "LQ-02")])

	def test_rules_and_questions_are_reported_together_so_neither_masks_the_other(self):
		held = gate.reasons("DecideContractChange", profile.PRODUCTION, {"early_total_increase"})
		self.assertEqual(self.codes(held), [("CM_RULE", "CM-R-10"), ("CM_RULE", "CM-R-11"), ("CM_HOLD", "LQ-02")])

	def test_the_synthetic_profile_answers_lq_02_to_04_illustratively_but_not_lq_05_or_06(self):
		synthetic = profile.SYNTHETIC
		self.assertEqual(self.codes(gate.reasons("DecideContractChange", synthetic, {"early_total_increase"})), [])
		self.assertEqual(self.codes(gate.reasons("DecideContractAdjustment", synthetic, {"automatic_deduction"})), [])
		self.assertEqual(self.codes(gate.reasons("RequestContractSignatures", synthetic, {"security_exemption"})), [])
		self.assertEqual(self.codes(gate.reasons("RequestContractSignatures", synthetic, {"production_execution_of_form_no_4"})), [("CM_HOLD", "LQ-05")])
		self.assertEqual(self.codes(gate.reasons("RecordContractAwardPublication", synthetic, {"publication_deadline_or_channel"})), [("CM_HOLD", "LQ-06")])

	def test_the_synthetic_profile_is_not_available_on_a_live_site(self):
		for flag in simulation.FLAGS:
			frappe.conf[flag] = 0
		with self.assertRaises(PermissionError):
			gate.reasons("DecideContractChange", profile.SYNTHETIC)
		self.assertEqual(self.codes(gate.reasons("DecideContractChange", profile.PRODUCTION)), [("CM_RULE", "CM-R-10"), ("CM_RULE", "CM-R-11")])
