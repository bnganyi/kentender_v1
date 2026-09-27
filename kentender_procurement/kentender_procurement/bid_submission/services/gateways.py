# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The approved external services Bid Submission depends on (BDS-CHG-001 v0.8
§5.7, §5.10, §7.4 and plan D6): the signing/trust service, the trusted-time
source and the electronic tender box (custody).

Each is found through a hook (`kt_bds_trust_services`, `kt_bds_time_services`,
`kt_bds_custody_services`); the last provider that answers wins. No
production provider is configured on this bench, so each reports unhealthy
there. The simulation doubles (Test Trust Service, trusted test clock, Test
Tender Box; owner decision OD-C) answer only on a test environment. Nothing
here is a certificate authority, a signature scheme or an encryption design
(§16)."""

from __future__ import annotations

from typing import Any

import frappe

TRUST, TIME, CUSTODY = "kt_bds_trust_services", "kt_bds_time_services", "kt_bds_custody_services"


def _service(hook: str) -> Any | None:
	for path in reversed(frappe.get_hooks(hook) or []):
		found = frappe.get_attr(path)()
		if found is not None:
			return found
	return None


def trust() -> Any | None:
	return _service(TRUST)


def trusted_time() -> Any | None:
	return _service(TIME)


def custody() -> Any | None:
	return _service(CUSTODY)


def _healthy(service) -> bool:
	try:
		return bool(service is not None and service.healthy())
	except Exception:
		return False


def trust_healthy() -> bool:
	return _healthy(trust())


def time_healthy() -> bool:
	return _healthy(trusted_time())


def custody_healthy() -> bool:
	return _healthy(custody())
