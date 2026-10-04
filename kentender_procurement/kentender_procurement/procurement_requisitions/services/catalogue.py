# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""REQ-CHG-001 v1.11 §6.3/§6.4 — the code-owned IT Equipment characteristic
catalogue. Not edited in Desk (§6.2): a new characteristic requires a new
code release and document revision. Server-side control types, comparisons,
units and options are the single source of truth the client's dialog derives
its controls from (`GetRequisitionEditor`'s `catalogue` block) and the
server validates every posted value against, independently of what the
client rendered.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any

CATALOGUE_VERSION = "REQ-CAT-1.11"

# Control types.
YES_NO = "YES_NO"
INTEGER = "INTEGER"
DECIMAL = "DECIMAL"
SELECT = "SELECT"
MULTI_SELECT = "MULTI_SELECT"
TEXT = "TEXT"
PORT_LIST = "PORT_LIST"

# Comparisons (§6.3 column 3).
MINIMUM = "Minimum"
MAXIMUM = "Maximum"
EXACT = "Exact"
REQUIRED = "Required"
ONE_OF = "One of"

EQUIPMENT_CATEGORIES: tuple[str, ...] = (
	"Laptop", "Desktop computer", "Monitor", "Tablet", "Printer", "Scanner",
	"Network equipment", "Power-protection equipment", "Other IT equipment",
)

SERVICE_TYPES: tuple[str, ...] = (
	"Delivery", "Installation", "Configuration", "Data transfer", "User orientation",
	"Training", "Testing", "Other",
)

ACCEPTANCE_CHECK_TYPES: tuple[str, ...] = (
	"Quantity", "Physical condition", "Required specification", "Functional test",
	"Installation complete", "Documents received", "Other objective check",
)

ACCEPTANCE_EVIDENCE_TYPES: tuple[str, ...] = (
	"Inspection record", "Test result", "Delivery note", "Certificate", "Other stated record",
)

SERVICE_ACCEPTANCE_EVIDENCE: tuple[str, ...] = (
	"Delivery note", "Installation certificate", "Test result", "Attendance record",
	"Completion certificate", "Other stated record",
)

SUPPORTING_MATERIAL_TYPES: tuple[str, ...] = (
	"Drawing", "Photograph", "Room layout", "Network diagram", "Standards extract",
	"Site report", "Environment information", "Other supporting material",
)

_ALL_EQUIPMENT = frozenset(EQUIPMENT_CATEGORIES)
_PORTABLE_COMPUTE = frozenset({"Laptop", "Desktop computer", "Tablet"})


@dataclass(frozen=True)
class Characteristic:
	key: str
	label: str
	applies_to: frozenset[str] | None  # None = every equipment category
	control: str
	comparison: str
	unit: str = ""
	options: tuple[str, ...] = ()
	minimum: float | None = None
	maximum: float | None = None
	min_length: int = 0
	max_length: int = 0
	allows_other: bool = False
	repeatable: bool = False
	port_options: tuple[str, ...] = ()

	def applies(self, equipment_category: str) -> bool:
		return self.applies_to is None or equipment_category in self.applies_to

	def as_dict(self) -> dict[str, Any]:
		return {
			"key": self.key, "label": self.label,
			"applies_to": sorted(self.applies_to) if self.applies_to is not None else None,
			"control": self.control, "comparison": self.comparison, "unit": self.unit,
			"options": list(self.options), "minimum": self.minimum, "maximum": self.maximum,
			"min_length": self.min_length, "max_length": self.max_length,
			"allows_other": self.allows_other, "repeatable": self.repeatable,
			"port_options": list(self.port_options),
		}


CHARACTERISTICS: tuple[Characteristic, ...] = (
	Characteristic("electrical_compatibility", "Electrical compatibility", None, YES_NO, REQUIRED, options=("Yes",)),
	Characteristic("new_unused_equipment", "New and unused equipment", None, YES_NO, REQUIRED, options=("Yes",)),
	Characteristic("memory", "Memory", _PORTABLE_COMPUTE, INTEGER, MINIMUM, unit="GB", minimum=1, maximum=512),
	Characteristic("storage_capacity", "Storage capacity", _PORTABLE_COMPUTE, INTEGER, MINIMUM, unit="GB", minimum=16, maximum=8192),
	Characteristic("storage_type", "Storage type", _PORTABLE_COMPUTE, SELECT, ONE_OF, options=("NVMe SSD", "SSD", "eMMC")),
	Characteristic("display_size", "Display size", frozenset({"Laptop", "Desktop computer", "Monitor", "Tablet"}), DECIMAL, MINIMUM, unit="inches", minimum=5, maximum=60),
	Characteristic("battery_runtime", "Battery runtime", frozenset({"Laptop", "Tablet"}), DECIMAL, MINIMUM, unit="hours", minimum=1, maximum=30),
	Characteristic("processor_requirement", "Processor requirement", _PORTABLE_COMPUTE, TEXT, MINIMUM, min_length=3, max_length=200),
	Characteristic("operating_system_compatibility", "Operating-system compatibility", _PORTABLE_COMPUTE, TEXT, REQUIRED, min_length=3, max_length=160),
	Characteristic("network_connectivity", "Network connectivity", _PORTABLE_COMPUTE, MULTI_SELECT, REQUIRED, options=("Ethernet", "Wi-Fi 5", "Wi-Fi 6", "Wi-Fi 6E", "4G", "5G", "Bluetooth 5 or later")),
	Characteristic(
		"required_ports", "Required ports", _PORTABLE_COMPUTE, PORT_LIST, REQUIRED,
		port_options=("USB-A", "USB-C", "HDMI", "DisplayPort", "Ethernet", "Audio", "Other stated port"),
	),
	Characteristic("display_resolution", "Display resolution", frozenset({"Monitor"}), SELECT, MINIMUM, options=("Full HD", "QHD", "4K UHD")),
	Characteristic("panel_size", "Panel size", frozenset({"Monitor"}), DECIMAL, MINIMUM, unit="inches", minimum=15, maximum=60),
	Characteristic("print_technology", "Print technology", frozenset({"Printer"}), SELECT, EXACT, options=("Laser", "Ink tank", "Thermal")),
	Characteristic("colour_capability", "Colour capability", frozenset({"Printer"}), SELECT, EXACT, options=("Monochrome", "Colour")),
	Characteristic("print_speed", "Print speed", frozenset({"Printer"}), INTEGER, MINIMUM, unit="pages per minute", minimum=1, maximum=100),
	Characteristic("automatic_duplex", "Automatic duplex", frozenset({"Printer", "Scanner"}), YES_NO, REQUIRED, options=("Yes", "No")),
	Characteristic("scan_resolution", "Scan resolution", frozenset({"Scanner"}), INTEGER, MINIMUM, unit="dpi", minimum=75, maximum=2400),
	Characteristic("automatic_document_feeder_capacity", "Automatic document feeder capacity", frozenset({"Scanner"}), INTEGER, MINIMUM, unit="sheets", minimum=1, maximum=500),
	Characteristic("network_function", "Equipment function", frozenset({"Network equipment"}), SELECT, EXACT, options=("Switch", "Router", "Wireless access point", "Firewall appliance", "Other stated function")),
	Characteristic("network_port_count", "Port count", frozenset({"Network equipment"}), INTEGER, MINIMUM, unit="ports", minimum=1, maximum=128),
	Characteristic("network_throughput", "Throughput", frozenset({"Network equipment"}), DECIMAL, MINIMUM, unit="Gbps", minimum=0.1, maximum=1000),
	Characteristic("power_function", "Equipment function", frozenset({"Power-protection equipment"}), SELECT, EXACT, options=("UPS", "Surge protector", "Power distribution unit")),
	Characteristic("power_rated_capacity", "Rated capacity", frozenset({"Power-protection equipment"}), DECIMAL, MINIMUM, unit="kVA", minimum=0.1, maximum=1000),
	Characteristic("power_backup_runtime", "Backup runtime", frozenset({"Power-protection equipment"}), INTEGER, MINIMUM, unit="minutes", minimum=1, maximum=480),
	Characteristic("other_essential_characteristic", "Other essential characteristic", None, TEXT, REQUIRED, min_length=3, max_length=200, allows_other=True, repeatable=True),
)

CATALOGUE_BY_KEY: dict[str, Characteristic] = {c.key: c for c in CHARACTERISTICS}

BASELINE_RULES: dict[str, tuple[tuple[str, Any], ...]] = {
	"__all__": (("electrical_compatibility", "Yes"), ("new_unused_equipment", "Yes")),
	"Laptop": (("memory", None), ("storage_capacity", None), ("storage_type", "NVMe SSD")),
	"Desktop computer": (("memory", None), ("storage_capacity", None), ("storage_type", "NVMe SSD")),
	"Tablet": (("memory", None), ("storage_capacity", None), ("storage_type", "NVMe SSD")),
	"Monitor": (("display_resolution", None),),
	"Printer": (("print_technology", None),),
	"Scanner": (("scan_resolution", None),),
	"Network equipment": (("network_function", None),),
	"Power-protection equipment": (("power_function", None),),
}


def characteristics_for(equipment_category: str) -> list[Characteristic]:
	return [c for c in CHARACTERISTICS if c.applies(equipment_category)]


#: §6.4 — the catalogue-driven starting proposal for a supported category
#: other than Laptop (`proposal_for`). Only rows with a code-owned starting
#: value are proposed; a `None` entry is offered in the catalogue but never
#: pre-filled.
class CatalogueValueError(ValueError):
	def __init__(self, message: str, *, field: str = ""):
		self.field = field
		super().__init__(message)


#: §5.14 — the code-owned scale every DECIMAL characteristic uses.
DECIMAL_SCALE = 2


def _check_range(characteristic: Characteristic, number: Decimal) -> None:
	if characteristic.minimum is not None and number < Decimal(str(characteristic.minimum)):
		raise CatalogueValueError(f"{characteristic.label} must be at least {characteristic.minimum}.")
	if characteristic.maximum is not None and number > Decimal(str(characteristic.maximum)):
		raise CatalogueValueError(f"{characteristic.label} must be at most {characteristic.maximum}.")


def validate_value(characteristic: Characteristic, raw: Any, *, other_value: str = "") -> dict[str, Any]:
	"""Normalises a posted value into the canonical JSON shape this
	characteristic's control stores, raising `CatalogueValueError` (mapped
	by the caller onto `REQ_CONTROL_INVALID`) on anything out of range,
	off-list or the wrong shape."""
	control = characteristic.control
	if control == YES_NO:
		if raw not in characteristic.options:
			raise CatalogueValueError(f"{characteristic.label} must be one of {characteristic.options}.")
		return {"value": raw}
	if control == INTEGER:
		if isinstance(raw, (bool, float)):
			raise CatalogueValueError(f"{characteristic.label} must be a whole number.")
		try:
			number = int(str(raw).strip())
		except (TypeError, ValueError):
			raise CatalogueValueError(f"{characteristic.label} must be a whole number.")
		_check_range(characteristic, Decimal(number))
		return {"value": number}
	if control == DECIMAL:
		# §5.14 — exact decimal arithmetic at the declared scale; never a
		# binary float. The canonical value is the decimal string.
		if isinstance(raw, (bool, float)):
			raise CatalogueValueError(f"{characteristic.label} must be an exact decimal number.")
		try:
			number = Decimal(str(raw).strip())
		except (InvalidOperation, ValueError, TypeError):
			raise CatalogueValueError(f"{characteristic.label} must be a number.")
		if not number.is_finite() or -number.as_tuple().exponent > DECIMAL_SCALE:
			raise CatalogueValueError(f"{characteristic.label} supports at most {DECIMAL_SCALE} decimal places.")
		_check_range(characteristic, number)
		return {"value": f"{number:f}"}
	if control == SELECT:
		if raw == "Other" and characteristic.allows_other:
			if not other_value:
				raise CatalogueValueError(f"{characteristic.label}: a value for 'Other' is required.")
			return {"value": "Other", "other": other_value}
		if raw not in characteristic.options:
			raise CatalogueValueError(f"{characteristic.label} must be one of {characteristic.options}.")
		return {"value": raw}
	if control == MULTI_SELECT:
		values = raw if isinstance(raw, (list, tuple)) else [raw]
		if not values:
			raise CatalogueValueError(f"{characteristic.label}: at least one value is required.")
		for v in values:
			if v not in characteristic.options:
				raise CatalogueValueError(f"{characteristic.label}: {v!r} is not a recognised option.")
		return {"values": list(values)}
	if control == TEXT:
		text = str(raw or "").strip()
		if characteristic.allows_other and text.lower() == "other":
			if not other_value:
				raise CatalogueValueError(f"{characteristic.label}: a value for 'Other' is required.")
			return {"value": "Other", "other": other_value}
		if len(text) < characteristic.min_length or (characteristic.max_length and len(text) > characteristic.max_length):
			raise CatalogueValueError(f"{characteristic.label} must be {characteristic.min_length}-{characteristic.max_length or '∞'} characters.")
		return {"value": text}
	if control == PORT_LIST:
		rows = raw if isinstance(raw, (list, tuple)) else []
		if not rows:
			raise CatalogueValueError(f"{characteristic.label}: at least one port is required.")
		out = []
		for row in rows:
			port_type = (row or {}).get("port_type") if isinstance(row, dict) else None
			minimum_count = (row or {}).get("minimum_count") if isinstance(row, dict) else None
			if port_type not in characteristic.port_options:
				raise CatalogueValueError(f"{characteristic.label}: {port_type!r} is not a recognised port type.")
			try:
				count = int(minimum_count)
			except (TypeError, ValueError):
				raise CatalogueValueError(f"{characteristic.label}: each port needs a positive minimum count.")
			if count <= 0:
				raise CatalogueValueError(f"{characteristic.label}: each port needs a positive minimum count.")
			out.append({"port_type": port_type, "minimum_count": count})
		return {"ports": out}
	raise CatalogueValueError(f"Unknown control type {control!r}.")


def display_value(characteristic: Characteristic, value_json: dict[str, Any]) -> str:
	"""A human-readable projection of the canonical JSON, for
	`required_value_display` (§6.2's read-only source labelling)."""
	if "ports" in value_json:
		return "; ".join(f"{p['port_type']} ×{p['minimum_count']}" for p in value_json["ports"])
	if "values" in value_json:
		values = list(value_json["values"])
		return values[0] if len(values) == 1 else ", ".join(values[:-1]) + " and " + values[-1]
	value = value_json.get("value")
	if value == "Other" and value_json.get("other"):
		return value_json["other"]
	if characteristic.key == "electrical_compatibility" and value == "Yes":
		return "Yes — suitable for Kenyan mains supply"
	return f"{value}"


# --------------------------------------------------------------------------
# §6.4 / §13.1 — versioned code-owned requirement proposals
# --------------------------------------------------------------------------

STANDARD_PROFILE_KEY = "LAPTOP-REQUIREMENTS-V1"
STANDARD_PROFILE_VERSION = "1"
CATALOGUE_PROFILE_KEY = "IT-EQUIPMENT-CATALOGUE-V1"

#: The three headings the Requirements workbench groups technical rows under.
TECHNICAL_GROUPS: tuple[tuple[str, tuple[str, ...]], ...] = (
	("Basic equipment", ("electrical_compatibility", "new_unused_equipment", "other_essential_characteristic")),
	("Performance and storage", (
		"memory", "storage_capacity", "storage_type", "display_size", "battery_runtime", "processor_requirement",
		"operating_system_compatibility", "display_resolution", "panel_size", "print_technology", "colour_capability",
		"print_speed", "automatic_duplex", "scan_resolution", "automatic_document_feeder_capacity", "network_function",
		"network_port_count", "network_throughput", "power_function", "power_rated_capacity", "power_backup_runtime",
	)),
	("Connectivity", ("network_connectivity", "required_ports")),
)
GROUP_OF: dict[str, str] = {key: group for group, keys in TECHNICAL_GROUPS for key in keys}

#: §13.1 — the complete Laptop package: exactly eleven technical rows, six
#: warranty/support values and five acceptance checks.
LAPTOP_TECHNICAL: tuple[tuple[str, Any], ...] = (
	("electrical_compatibility", "Yes"),
	("new_unused_equipment", "Yes"),
	("memory", 16),
	("storage_capacity", 512),
	("storage_type", "NVMe SSD"),
	("display_size", "14.0"),
	("battery_runtime", "8"),
	("processor_requirement", "64-bit business-class processor, minimum 10 cores or equivalent benchmark"),
	("operating_system_compatibility", "Approved organisational Windows environment"),
	("network_connectivity", ["Wi-Fi 6", "Bluetooth 5 or later"]),
	("required_ports", [{"port_type": "USB-C", "minimum_count": 2}, {"port_type": "USB-A", "minimum_count": 2}, {"port_type": "HDMI", "minimum_count": 1}]),
)
STANDARD_SUPPORT: dict[str, Any] = {
	"minimum_warranty_months": 36,
	"onsite_support_required": True,
	"maximum_support_response_hours": 8,
	"manufacturer_support_required": True,
	"service_location_constraint": "Within Kenya",
	"support_description": "Supplier to provide escalation and warranty-contact details.",
}
STANDARD_ACCEPTANCE: tuple[dict[str, str], ...] = (
	{"check_type": "Quantity", "pass_condition": "Delivered quantities equal the authorised schedule", "evidence_type": "Inspection record"},
	{"check_type": "Physical condition", "pass_condition": "No visible damage and all listed accessories are present", "evidence_type": "Inspection record"},
	{"check_type": "Required specification", "pass_condition": "Every delivered unit complies with all mandatory technical rows", "evidence_type": "Inspection record"},
	{"check_type": "Functional test", "pass_condition": "Each device powers on and completes the agreed basic functional test", "evidence_type": "Test result"},
	{"check_type": "Documents received", "pass_condition": "Warranty and delivery documents are received and verified", "evidence_type": "Certificate"},
)


def _technical_row(key: str, raw: Any) -> dict[str, Any]:
	ch = CATALOGUE_BY_KEY[key]
	value = validate_value(ch, raw)
	return {
		"characteristic_key": key, "label": ch.label, "group": GROUP_OF.get(key, "Performance and storage"),
		"comparison": ch.comparison, "unit": ch.unit, "value": value, "display": display_value(ch, value),
		"applies_to_scope": "All items", "applies_to_id": "",
	}


def proposal_for(categories: list[str] | tuple[str, ...]) -> dict[str, Any]:
	"""§6.4 — the one complete editable proposal for the Draft's equipment.
	Laptop gets `LAPTOP-REQUIREMENTS-V1` exactly; any other supported
	category gets the catalogue-driven starting rows that carry a code-owned
	starting value. `proposal_digest` identifies exactly what was shown, so
	`ApplySelectedRequirementPackage` can refuse a stale one."""
	categories = [c for c in dict.fromkeys(categories or []) if c in EQUIPMENT_CATEGORIES]
	if not categories:
		return {"profile_key": "", "profile_version": "", "technical": [], "support": {}, "acceptance": [], "proposal_digest": ""}
	if categories == ["Laptop"]:
		technical = [_technical_row(k, v) for k, v in LAPTOP_TECHNICAL]
		profile_key, profile_version = STANDARD_PROFILE_KEY, STANDARD_PROFILE_VERSION
	else:
		technical = []
		seen: set[str] = set()
		for category in categories:
			rules = list(BASELINE_RULES.get("__all__", ())) + list(BASELINE_RULES.get(category, ()))
			for key, value in rules:
				if value is None or key in seen:
					continue
				seen.add(key)
				technical.append(_technical_row(key, value))
		profile_key, profile_version = CATALOGUE_PROFILE_KEY, STANDARD_PROFILE_VERSION
	payload = {
		"profile_key": profile_key, "profile_version": profile_version, "categories": categories,
		"technical": technical, "support": dict(STANDARD_SUPPORT),
		"acceptance": [{**row, "applies_to_scope": "All items", "applies_to_id": ""} for row in STANDARD_ACCEPTANCE],
	}
	payload["proposal_digest"] = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()
	return payload
