# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Shared STD readiness select values for TM2 Tender and TM2 Tender STD Binding."""

from __future__ import annotations

STD_READINESS_STATUSES: tuple[str, ...] = (
	"Not Assessed",
	"Not Ready",
	"Ready With Warnings",
	"Ready",
	"Blocked",
)
