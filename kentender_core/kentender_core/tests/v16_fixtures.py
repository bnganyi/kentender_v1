"""Shared fixtures for the AUTH-ADR-001 v1.6 / CFG-CHG-002 v0.6 suites.

One site is one Procuring Entity, and exactly one root Organisation Unit
exists, so fixtures can no longer build private roots per test module. Every
suite instead:

- ensures the canonical KT-STD-001 §8 site identity exists (Site Procuring
  Entity Single configured as PE-MOH, root unit present) — governed
  configuration, deliberately NOT purged; and
- builds its own subtree of `KT Test …` units *beneath* the real root, plus
  `kt.test.%` users — all purged by
  :mod:`kentender_core.tests.responsibility_test_cleanup`.
"""

from __future__ import annotations

import frappe

from kentender_core.services import organisation_structure as structure
from kentender_core.services import site_configuration as configuration

SITE_PE_NAME = "Ministry of Health"
SITE_PE_CODE = "PE-MOH"


def ensure_site_configured() -> str:
	"""Configure the canonical §8 site identity if this site has none yet.

	Returns the root Organisation Unit name. Committed by the caller's
	setUpClass; never purged — it is the governed site configuration, not a
	fixture.
	"""
	if not configuration.is_configured():
		single = frappe.get_doc(configuration.SITE_PE_DOCTYPE)
		single.pe_name = SITE_PE_NAME
		single.pe_code = SITE_PE_CODE
		single.pe_type = "National Government Ministry"
		single.timezone = "Africa/Nairobi"
		single.configured_by = "Administrator"
		single.configured_at = frappe.utils.now_datetime()
		single.save(ignore_permissions=True)
	root = configuration._root_unit()
	if not root:
		created = configuration._ensure_root_unit(SITE_PE_NAME, SITE_PE_CODE)
		return created["id"]
	return root["id"]


def unit(name: str, parent: str = "", namespace: str = "KT_TEST") -> str:
	"""One `KT Test …` unit beneath the given parent (default: the root).

	Created through the governed service so codes are generated, then stamped
	with the fixture namespace so the purge can find it.
	"""
	result = structure.add_organisation_unit(parent_id=parent, name=name)
	frappe.db.set_value(
		"Organisation Unit", result["unit"], "fixture_namespace", namespace, update_modified=False
	)
	return result["unit"]


def user(local_part: str, full_name: str = "", roles: tuple[str, ...] = ()) -> str:
	"""One enabled `kt.test.%` System User with Desk access.

	Frappe flips a role-less user to Website User on save, so Desk User is
	always added; extra roles are for negative-path fixtures only — a Frappe
	Role never grants business authority by itself (AUTH-AC-007).
	"""
	email = f"kt.test.{local_part}@example.test"
	if not frappe.db.exists("User", email):
		doc = frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": full_name or local_part.replace(".", " ").title(),
				"send_welcome_email": 0,
				"user_type": "System User",
				"enabled": 1,
			}
		)
		doc.insert(ignore_permissions=True)
		doc.add_roles("Desk User")
	if roles:
		frappe.get_doc("User", email).add_roles(*roles)
	return email
