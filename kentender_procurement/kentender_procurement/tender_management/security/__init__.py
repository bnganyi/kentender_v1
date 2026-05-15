# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Security, permissions, and audit hardening package (SEC-0001).

Cross-cutting authorization, action availability, audit, and evidence export
services. Structure scaffold; implementation tickets SEC-0100+.

This package is distinct from ``tender_publication.authorization`` /
``tender_publication.audit`` (publication-specific gates).

Tracker:
``apps/kentender_v1/docs/prompts/std-production-readiness/workstream-7/IMPLEMENTATION_TRACKER.md``
"""

from __future__ import annotations
