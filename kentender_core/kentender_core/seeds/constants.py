# Copyright (c) 2025, Midas and contributors
# License: MIT. See LICENSE
"""Stable keys shared by seed and reset scripts (must not drift)."""

TEST_PASSWORD = "Test@123"

ENTITY_MOH = "MOH"
ENTITY_MOE = "MOE"

# Department display names encode spec codes (no department_code field on v1 Procuring Department).
DEPT_CLIN = "CLIN-SERV — Clinical Services"
DEPT_HR = "HR — Human Resources"
DEPT_FIN = "FIN — Finance"
DEPT_PROC = "PROC — Procurement"

BUSINESS_ROLES = (
	"Strategy Manager",
	"Planning Authority",
	"Requisitioner",
	"Procurement Planner",
	"Finance Reviewer",
)

# (email, full_name, business_role, department_label)
SEED_USERS = (
	("strategy.manager@moh.test", "Strategy Manager MOH", "Strategy Manager", DEPT_CLIN),
	("planning.authority@moh.test", "Planning Authority MOH", "Planning Authority", DEPT_FIN),
	("requisitioner@moh.test", "Requisitioner MOH", "Requisitioner", DEPT_CLIN),
	("planner@moh.test", "Procurement Planner MOH", "Procurement Planner", DEPT_PROC),
	("finance.reviewer@moh.test", "Finance Reviewer MOH", "Finance Reviewer", DEPT_FIN),
)

# Strategic plan titles (exact spec strings)
PLAN_BASIC_NAME = "MOH Strategic Plan 2026–2030"
PLAN_EXTENDED_NAME = "MOH Service Delivery Improvement Plan 2027–2031"
