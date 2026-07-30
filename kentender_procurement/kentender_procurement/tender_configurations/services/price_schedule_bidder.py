# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""Bidder-facing Price Schedule portal (pack 11 / Stitch 01–04)."""

from __future__ import annotations

import json
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation
from typing import Any
from urllib.parse import quote

import frappe
from frappe.utils import cstr, now_datetime

from kentender_procurement.tender_configurations.seed.lean_price_schedule import (
	FIXTURE_SINGLE_LOT,
	SCHEDULE_RECURRENT,
	SCHEDULE_SUPPLY,
	SECTION_KEY,
	materialize_lean_price_schedule,
)
from kentender_procurement.tender_configurations.services.electronic_bid import (
	STATUS_SEALED,
	create_or_get_draft,
	save_section_responses,
)
from kentender_procurement.tender_configurations.services.published_tender_overview import (
	ACTION_CLOSED,
	ACTION_UNAVAILABLE,
	ACTION_VIEW_SUBMITTED,
	get_published_tender_overview,
	resolve_published_tender_backend,
	start_or_get_bid_workspace,
)
from kentender_procurement.tender_configurations.services.schema_compiler import (
	persist_compiled_schema,
)
from kentender_procurement.tender_configurations.services.submission_checklist import (
	STATUS_COMPLETE,
	STATUS_IN_PROGRESS,
	STATUS_NEEDS_ATTENTION,
	STATUS_NOT_STARTED,
	portal_workspace_url,
)

MONEY_QUANT = Decimal("0.01")


def _parse_json(raw: Any, default: Any = None) -> Any:
	if raw is None or raw == "":
		return default if default is not None else {}
	if isinstance(raw, (dict, list)):
		return raw
	try:
		return json.loads(raw)
	except (TypeError, ValueError):
		return default if default is not None else {}


def _require_logged_in() -> None:
	if not frappe.session.user or frappe.session.user == "Guest":
		frappe.throw(frappe._("Please sign in to open this bid section."), frappe.PermissionError)


def _section_key(sec: dict[str, Any]) -> str:
	return cstr(sec.get("section_key") or sec.get("key") or "").strip()


def portal_price_schedule_url(publication_ref: str) -> str:
	ref = quote(cstr(publication_ref or "").strip(), safe="")
	return f"/tenders/{ref}/sections/{SECTION_KEY}"


def portal_price_schedule_schedule_url(publication_ref: str, schedule_key: str) -> str:
	sk = quote(cstr(schedule_key or "").strip(), safe="")
	return f"{portal_price_schedule_url(publication_ref)}/schedules/{sk}"


def portal_price_schedule_review_url(publication_ref: str) -> str:
	return f"{portal_price_schedule_url(publication_ref)}/review"


def _load_schema(cfg, bid_doc) -> dict[str, Any]:
	if bid_doc:
		schema = _parse_json(getattr(bid_doc, "schema_snapshot", None), {})
		if schema.get("sections"):
			return schema
	schema = _parse_json(getattr(cfg, "bidder_submission_schema", None), {})
	if not schema.get("sections"):
		schema = persist_compiled_schema(cfg.name)
	return schema


def _find_section(schema: dict[str, Any], section_key: str = SECTION_KEY) -> dict[str, Any] | None:
	want = cstr(section_key or "").strip()
	for sec in schema.get("sections") or []:
		if isinstance(sec, dict) and _section_key(sec) == want:
			return sec
	return None


def _ensure_bid(published_tender_ref: str):
	overview = get_published_tender_overview(published_tender_ref)
	backend = resolve_published_tender_backend(published_tender_ref)
	action = overview.get("primary_action")
	if action in (ACTION_CLOSED, ACTION_UNAVAILABLE):
		frappe.throw(
			frappe._("Bidding is not available ({0}).").format(action),
			title="BID_WORKSPACE_UNAVAILABLE",
		)
	pub_ref = cstr(overview.get("published_tender_ref") or published_tender_ref)
	cfg_id = cstr(backend.get("configuration_id") or "")
	if action == ACTION_VIEW_SUBMITTED or overview.get("bid_status") == STATUS_SEALED:
		started = start_or_get_bid_workspace(pub_ref)
		bid_id = started.get("bid_id") or backend.get("bid_id")
	else:
		draft = create_or_get_draft(cfg_id)
		bid_id = draft.get("bid_id")
	bid_doc = frappe.get_doc("Electronic Bid Submission", bid_id)
	if cstr(bid_doc.owner) not in ("", frappe.session.user) and frappe.session.user != "Administrator":
		# Owner check — Administrator allowed for domain/UI tests.
		if cstr(bid_doc.owner) != frappe.session.user:
			frappe.throw(frappe._("You cannot access another bidder's submission."), frappe.PermissionError)
	cfg = backend.get("configuration") or frappe.get_doc("Tender Configuration", cfg_id)
	schema = _load_schema(cfg, bid_doc)
	return overview, bid_doc, schema, {"pub_ref": pub_ref, "cfg_id": cfg_id, "cfg": cfg}


def _cfg_price_blob(cfg) -> dict[str, Any]:
	raw = _parse_json(getattr(cfg, "price_schedule", None), {})
	return raw if isinstance(raw, dict) else {}


def _enrich_line_from_cfg_item(item: dict[str, Any], order: int) -> dict[str, Any]:
	group = cstr(item.get("price_group") or "").strip().lower()
	if "recurrent" in group:
		schedule_key = SCHEDULE_RECURRENT
	else:
		schedule_key = SCHEDULE_SUPPLY
	currencies = item.get("permitted_currencies")
	if not isinstance(currencies, list) or not currencies:
		currencies = [cstr(item.get("currency") or "KES").strip() or "KES"]
	periods = item.get("periods") if isinstance(item.get("periods"), list) else []
	if schedule_key == SCHEDULE_RECURRENT and not periods:
		periods = ["year_1", "year_2", "year_3"]
	line_id = cstr(item.get("item_id") or item.get("line_id") or f"ps-line-{order}").strip()
	desc = cstr(
		item.get("bidder_facing_description") or item.get("item_name") or item.get("description") or ""
	).strip()
	return {
		"line_id": line_id,
		"display_reference": cstr(item.get("display_reference") or item.get("item_id") or line_id).strip(),
		"description": desc,
		"schedule_key": schedule_key,
		"lot_id": cstr(item.get("lot_id") or "").strip(),
		"quantity": cstr(item.get("quantity") or "1").strip() or "1",
		"unit": cstr(item.get("unit") or "Lot").strip() or "Lot",
		"required": 0 if item.get("required") in (0, "0", False, "false") else 1,
		"country_of_origin_required": 1
		if item.get("country_of_origin_required") in (1, "1", True, "true")
		else 0,
		"permitted_currencies": [cstr(c).strip() for c in currencies if cstr(c).strip()],
		"zero_allowed": 1 if item.get("zero_allowed") in (1, "1", True, "true") else 0,
		"periods": [cstr(p).strip() for p in periods if cstr(p).strip()],
		"display_order": int(item.get("display_order") or order),
	}


def hydrate_price_schedule_section(
	sec: dict[str, Any] | None,
	*,
	schema: dict[str, Any] | None = None,
	bid_doc: Any = None,
	cfg: Any = None,
) -> dict[str, Any] | None:
	"""Fill route-only / thin price_schedule stubs with lean or CFG-enriched lines."""
	if not isinstance(sec, dict):
		return sec
	if _section_key(sec) != SECTION_KEY:
		return sec
	lines = [r for r in (sec.get("price_lines") or []) if isinstance(r, dict) and r.get("line_id")]
	# Need schedule_key + description at minimum for bidder UI.
	needs = (not lines) or any(not cstr(r.get("schedule_key") or "").strip() for r in lines)
	if not needs and cstr(sec.get("slice_status") or "") not in (
		"",
		"route_only_not_editable_in_lean_slice",
	):
		sec.setdefault("section_type", "price_schedule")
		return sec

	blob = _cfg_price_blob(cfg) if cfg is not None else {}
	fixture = cstr(blob.get("lean_fixture") or FIXTURE_SINGLE_LOT).strip() or FIXTURE_SINGLE_LOT
	items = blob.get("items") if isinstance(blob.get("items"), list) else []
	if items:
		enriched = [_enrich_line_from_cfg_item(it, (i + 1) * 10) for i, it in enumerate(items) if isinstance(it, dict)]
		flags = blob.get("flags") if isinstance(blob.get("flags"), dict) else {}
		schedules = _schedules_from_lines(enriched)
		sec["price_lines"] = enriched
		sec["schedules"] = schedules
		sec["price_schedule_flags"] = flags or {
			"single_lot": 1,
			"lots": [],
			"alternatives_permitted": 0,
			"offers": [{"offer_id": "main", "label": "Main offer"}],
			"currency_precision": 2,
		}
	else:
		mat = materialize_lean_price_schedule(fixture)
		sec.update(mat)

	sec["section_type"] = "price_schedule"
	sec["slice_status"] = "price_schedule_implemented"
	if not cstr(sec.get("bidder_instructions") or "").strip():
		sec["bidder_instructions"] = (
			"Enter your prices for the goods and services specified in this tender."
		)
	if bid_doc is not None and isinstance(schema, dict) and schema.get("sections"):
		try:
			bid_doc.db_set(
				"schema_snapshot",
				json.dumps(schema, ensure_ascii=False),
				update_modified=False,
			)
		except Exception:
			pass
	return sec


def _schedules_from_lines(lines: list[dict[str, Any]]) -> list[dict[str, Any]]:
	labels = {
		SCHEDULE_SUPPLY: "Supply and Installation",
		SCHEDULE_RECURRENT: "Recurrent Costs",
	}
	order: list[str] = []
	for row in lines:
		sk = cstr(row.get("schedule_key") or "").strip()
		if sk and sk not in order:
			order.append(sk)
	out = []
	for i, sk in enumerate(order):
		periods: list[str] = []
		for row in lines:
			if cstr(row.get("schedule_key")) != sk:
				continue
			for p in row.get("periods") or []:
				ps = cstr(p).strip()
				if ps and ps not in periods:
					periods.append(ps)
		out.append(
			{
				"schedule_key": sk,
				"title": labels.get(sk, sk.replace("_", " ").title()),
				"display_order": (i + 1) * 10,
				"periods": periods,
				"period_labels": {"year_1": "Year 1", "year_2": "Year 2", "year_3": "Year 3"},
			}
		)
	return out


def _to_decimal(val: Any) -> Decimal | None:
	"""Return Decimal for an explicit value; None for blank/missing."""
	if val is None or val == "":
		return None
	if isinstance(val, bool):
		return None
	try:
		# Accept typed/display values with thousands separators (3,400,000.00).
		return Decimal(cstr(val).strip().replace(",", ""))
	except (InvalidOperation, ValueError, TypeError):
		raise frappe.ValidationError(frappe._("Enter a valid decimal price."))


def _money(val: Decimal, precision: int = 2) -> str:
	"""Canonical unformatted money string for storage / math (e.g. 3400000.00)."""
	q = Decimal("1").scaleb(-precision)
	return str(val.quantize(q, rounding=ROUND_HALF_UP))


def format_money_display(val: Any, precision: int = 2) -> str:
	"""Bidder-facing money with thousands separators (e.g. 3,400,000.00)."""
	if val is None or val == "":
		return ""
	try:
		if isinstance(val, Decimal):
			dec = val
		else:
			dec = Decimal(cstr(val).strip().replace(",", ""))
	except (InvalidOperation, ValueError, TypeError):
		return cstr(val)
	q = Decimal("1").scaleb(-precision)
	quantized = dec.quantize(q, rounding=ROUND_HALF_UP)
	return f"{quantized:,.{precision}f}"


def _qty(line: dict[str, Any]) -> Decimal:
	try:
		return Decimal(cstr(line.get("quantity") or "1").strip() or "1")
	except (InvalidOperation, ValueError):
		return Decimal("1")


def _response_map(raw: Any) -> dict[str, Any]:
	if not isinstance(raw, dict):
		return {}
	if "payload" in raw and ("section_key" in raw or "meta" in raw):
		inner = raw.get("payload")
		return inner if isinstance(inner, dict) else {}
	return raw


def _line_response_key(line_id: str, offer_id: str, lot_id: str = "") -> str:
	parts = [cstr(offer_id or "main").strip() or "main", cstr(line_id).strip()]
	lid = cstr(lot_id or "").strip()
	if lid:
		parts.insert(1, lid)
	return "::".join(parts)


def _get_line_resp(resp: dict[str, Any], line_id: str, offer_id: str, lot_id: str = "") -> dict[str, Any]:
	lines = resp.get("lines") if isinstance(resp.get("lines"), dict) else {}
	key = _line_response_key(line_id, offer_id, lot_id)
	row = lines.get(key)
	if isinstance(row, dict):
		return row
	# Fallback: bare line_id (single-lot main)
	row = lines.get(line_id)
	return row if isinstance(row, dict) else {}


def _set_line_resp(
	resp: dict[str, Any],
	line_id: str,
	offer_id: str,
	lot_id: str,
	payload: dict[str, Any],
) -> None:
	lines = resp.get("lines") if isinstance(resp.get("lines"), dict) else {}
	key = _line_response_key(line_id, offer_id, lot_id)
	existing = lines.get(key) if isinstance(lines.get(key), dict) else {}
	merged = dict(existing)
	merged.update(payload)
	lines[key] = merged
	resp["lines"] = lines


def _flags(sec: dict[str, Any]) -> dict[str, Any]:
	flags = sec.get("price_schedule_flags")
	return flags if isinstance(flags, dict) else {}


def _precision(sec: dict[str, Any]) -> int:
	try:
		return max(0, min(6, int(_flags(sec).get("currency_precision") or 2)))
	except (TypeError, ValueError):
		return 2


def _applicable_lines(
	sec: dict[str, Any],
	*,
	lot_id: str | None = None,
	schedule_key: str | None = None,
) -> list[dict[str, Any]]:
	want_lot = cstr(lot_id or "").strip()
	want_sk = cstr(schedule_key or "").strip()
	out = []
	for row in sec.get("price_lines") or []:
		if not isinstance(row, dict) or not cstr(row.get("line_id") or "").strip():
			continue
		row_lot = cstr(row.get("lot_id") or "").strip()
		if want_lot and row_lot and row_lot != want_lot:
			continue
		if want_sk and cstr(row.get("schedule_key") or "") != want_sk:
			continue
		out.append(row)
	out.sort(key=lambda r: (int(r.get("display_order") or 0), cstr(r.get("display_reference") or "")))
	return out


def validate_line_response(
	line: dict[str, Any],
	resp: dict[str, Any] | None,
	*,
	precision: int = 2,
) -> list[str]:
	"""Return human-readable field issues for one line (empty = ok / optional blank)."""
	issues: list[str] = []
	r = resp if isinstance(resp, dict) else {}
	required = line.get("required") not in (0, "0", False, "false")
	ref = cstr(line.get("display_reference") or line.get("line_id"))
	currencies = [cstr(c).strip() for c in (line.get("permitted_currencies") or []) if cstr(c).strip()]
	periods = [cstr(p).strip() for p in (line.get("periods") or []) if cstr(p).strip()]
	is_recurrent = cstr(line.get("schedule_key")) == SCHEDULE_RECURRENT or bool(periods)

	if is_recurrent:
		period_prices = r.get("period_prices") if isinstance(r.get("period_prices"), dict) else {}
		any_filled = False
		for p in periods:
			raw = period_prices.get(p)
			if raw is None or raw == "":
				if required:
					issues.append(f"Recurrent-cost period is incomplete for item {ref}.")
				continue
			any_filled = True
			try:
				dec = _to_decimal(raw)
			except frappe.ValidationError:
				issues.append(f"Enter a valid decimal price for item {ref}.")
				continue
			if dec is None:
				continue
			if dec < 0:
				issues.append(f"Negative prices are not allowed for item {ref}.")
			elif dec == 0 and line.get("zero_allowed") not in (1, "1", True, "true"):
				issues.append(f"Zero is not accepted for item {ref}.")
		if not required and not any_filled:
			return []
		currency = cstr(r.get("currency") or "").strip()
		if any_filled or required:
			if not currency:
				issues.append(f"Currency is required for item {ref}.")
			elif currencies and currency not in currencies:
				issues.append(f"Currency is not permitted for item {ref}.")
		return list(dict.fromkeys(issues))

	# Supply / unit price
	raw_price = r.get("unit_price")
	blank = raw_price is None or raw_price == ""
	if blank:
		if required:
			issues.append(f"Required item {ref} has no unit price.")
		return issues
	try:
		dec = _to_decimal(raw_price)
	except frappe.ValidationError:
		return [f"Enter a valid decimal price for item {ref}."]
	if dec is None:
		if required:
			issues.append(f"Required item {ref} has no unit price.")
		return issues
	if dec < 0:
		issues.append(f"Negative prices are not allowed for item {ref}.")
	elif dec == 0 and line.get("zero_allowed") not in (1, "1", True, "true"):
		issues.append(f"Zero is not accepted for item {ref}.")
	currency = cstr(r.get("currency") or "").strip()
	if not currency:
		issues.append(f"Currency is required for item {ref}.")
	elif currencies and currency not in currencies:
		issues.append(f"Currency is not permitted for item {ref}.")
	if line.get("country_of_origin_required") in (1, "1", True, "true"):
		if not cstr(r.get("country_of_origin") or "").strip():
			issues.append(f"Country of origin is missing for item {ref}.")
	return list(dict.fromkeys(issues))


def _line_total(line: dict[str, Any], resp: dict[str, Any], *, precision: int) -> Decimal | None:
	periods = [cstr(p).strip() for p in (line.get("periods") or []) if cstr(p).strip()]
	if cstr(line.get("schedule_key")) == SCHEDULE_RECURRENT or periods:
		period_prices = resp.get("period_prices") if isinstance(resp.get("period_prices"), dict) else {}
		total = Decimal("0")
		any_val = False
		for p in periods:
			dec = _to_decimal(period_prices.get(p)) if period_prices.get(p) not in (None, "") else None
			if dec is None:
				continue
			any_val = True
			total += dec
		if not any_val:
			return None
		return total.quantize(Decimal("1").scaleb(-precision), rounding=ROUND_HALF_UP)
	dec = _to_decimal(resp.get("unit_price")) if resp.get("unit_price") not in (None, "") else None
	if dec is None:
		return None
	lt = (_qty(line) * dec).quantize(Decimal("1").scaleb(-precision), rounding=ROUND_HALF_UP)
	return lt


def compute_totals(
	sec: dict[str, Any],
	resp: dict[str, Any],
	*,
	offer_id: str = "main",
	lot_id: str = "",
) -> dict[str, Any]:
	precision = _precision(sec)
	by_currency: dict[str, dict[str, Decimal]] = {}
	offer = cstr(offer_id or "main").strip() or "main"
	lot = cstr(lot_id or "").strip()

	for line in _applicable_lines(sec, lot_id=lot or None):
		lr = _get_line_resp(resp, cstr(line.get("line_id")), offer, cstr(line.get("lot_id") or lot))
		total = _line_total(line, lr, precision=precision)
		if total is None:
			continue
		currency = cstr(lr.get("currency") or (line.get("permitted_currencies") or ["KES"])[0]).strip() or "KES"
		bucket = by_currency.setdefault(
			currency,
			{
				"supply_subtotal": Decimal("0"),
				"recurrent_subtotal": Decimal("0"),
				"grand_total": Decimal("0"),
			},
		)
		sk = cstr(line.get("schedule_key"))
		if sk == SCHEDULE_RECURRENT or (line.get("periods") or []):
			bucket["recurrent_subtotal"] += total
		else:
			bucket["supply_subtotal"] += total

	out_by: dict[str, dict[str, str]] = {}
	primary_currency = ""
	primary_grand: str | None = None
	for currency, bucket in by_currency.items():
		grand = bucket["supply_subtotal"] + bucket["recurrent_subtotal"]
		out_by[currency] = {
			"supply_subtotal": _money(bucket["supply_subtotal"], precision),
			"recurrent_subtotal": _money(bucket["recurrent_subtotal"], precision),
			"grand_total": _money(grand, precision),
		}
		if not primary_currency:
			primary_currency = currency
			primary_grand = out_by[currency]["grand_total"]

	return {
		"by_currency": out_by,
		"totals": {
			"grand_total": primary_grand,
			"currency": primary_currency,
		},
	}


def collect_issues(
	sec: dict[str, Any],
	resp: dict[str, Any],
	*,
	offer_id: str = "main",
	lot_id: str = "",
) -> list[dict[str, Any]]:
	precision = _precision(sec)
	offer = cstr(offer_id or "main").strip() or "main"
	issues: list[dict[str, Any]] = []
	for line in _applicable_lines(sec, lot_id=cstr(lot_id or "").strip() or None):
		lid = cstr(line.get("line_id"))
		lr = _get_line_resp(resp, lid, offer, cstr(line.get("lot_id") or lot_id))
		for msg in validate_line_response(line, lr, precision=precision):
			issues.append(
				{
					"line_id": lid,
					"display_reference": cstr(line.get("display_reference") or lid),
					"schedule_key": cstr(line.get("schedule_key") or ""),
					"lot_id": cstr(line.get("lot_id") or ""),
					"issue": msg,
					"action_url": portal_price_schedule_schedule_url(
						"", cstr(line.get("schedule_key") or SCHEDULE_SUPPLY)
					),
				}
			)
	return issues


def derive_price_schedule_section_status(
	sec: dict[str, Any],
	section_responses: Any,
) -> tuple[str, int]:
	resp = _response_map(section_responses)
	issues = collect_issues(sec, resp, offer_id=cstr(resp.get("active_offer_id") or "main"))
	blocker_count = len(issues)
	confirmed = bool(resp.get("complete_confirmed") or resp.get("complete"))
	status_field = cstr(resp.get("section_status") or "").strip()
	lines_map = resp.get("lines") if isinstance(resp.get("lines"), dict) else {}
	has_any = bool(lines_map)

	if confirmed and blocker_count == 0:
		return STATUS_COMPLETE, 0
	if confirmed and blocker_count:
		return STATUS_NEEDS_ATTENTION, blocker_count
	if status_field == STATUS_COMPLETE and blocker_count == 0:
		return STATUS_COMPLETE, 0
	if blocker_count and has_any:
		return STATUS_NEEDS_ATTENTION if confirmed else STATUS_IN_PROGRESS, blocker_count
	if has_any:
		return STATUS_IN_PROGRESS, blocker_count
	return STATUS_NOT_STARTED, blocker_count


def _line_has_input(lr: dict[str, Any]) -> bool:
	if not isinstance(lr, dict) or not lr:
		return False
	if lr.get("unit_price") not in (None, ""):
		return True
	if cstr(lr.get("country_of_origin") or "").strip():
		return True
	pp = lr.get("period_prices") if isinstance(lr.get("period_prices"), dict) else {}
	return any(v not in (None, "") for v in pp.values())


def _schedule_progress(
	sec: dict[str, Any],
	resp: dict[str, Any],
	schedule_key: str,
	*,
	offer_id: str,
	lot_id: str = "",
) -> dict[str, Any]:
	lines = _applicable_lines(sec, lot_id=lot_id or None, schedule_key=schedule_key)
	required = [l for l in lines if l.get("required") not in (0, "0", False, "false")]
	complete = started = needs = 0
	for line in required:
		lr = _get_line_resp(resp, cstr(line.get("line_id")), offer_id, cstr(line.get("lot_id") or lot_id))
		errs = validate_line_response(line, lr, precision=_precision(sec))
		filled = _line_has_input(lr)
		if filled:
			started += 1
		if errs:
			if filled:
				needs += 1
		elif filled:
			complete += 1
	total = len(required)
	if total and complete >= total and needs == 0:
		status = STATUS_COMPLETE
	elif needs:
		status = STATUS_NEEDS_ATTENTION
	elif started:
		status = STATUS_IN_PROGRESS
	else:
		status = STATUS_NOT_STARTED
	action = "Review" if status == STATUS_COMPLETE else ("Continue" if started else "Start")
	# Stitch "N of M items" reflects priced/started rows, not only fully-valid complete.
	return {
		"schedule_key": schedule_key,
		"complete": complete,
		"started": started,
		"total": total,
		"progress_label": f"{started} of {total}",
		"progress_percent": int(round(100.0 * started / total)) if total else 0,
		"status": status,
		"action_label": action,
		"needs_attention": needs,
	}


def _empty_response(sec: dict[str, Any]) -> dict[str, Any]:
	flags = _flags(sec)
	offers = flags.get("offers") if isinstance(flags.get("offers"), list) else []
	if not offers:
		offers = [{"offer_id": "main", "label": "Main offer"}]
	return {
		"offers": offers,
		"active_offer_id": cstr(offers[0].get("offer_id") or "main"),
		"active_lot_id": "",
		"lines": {},
		"computed": {"by_currency": {}, "totals": {"grand_total": None, "currency": ""}},
		"section_status": STATUS_NOT_STARTED,
		"complete": False,
		"complete_confirmed": 0,
	}


def _prepare_section(published_tender_ref: str):
	_require_logged_in()
	overview, bid_doc, schema, ids = _ensure_bid(published_tender_ref)
	sec = _find_section(schema, SECTION_KEY)
	if not sec:
		# Ensure section exists for lean publishes
		sec = {"section_key": SECTION_KEY, "title": "Price Schedule", "price_lines": []}
		schema.setdefault("sections", []).append(sec)
	hydrate_price_schedule_section(sec, schema=schema, bid_doc=bid_doc, cfg=ids.get("cfg"))
	responses = _parse_json(getattr(bid_doc, "responses", None), {})
	resp = _response_map(responses.get(SECTION_KEY))
	if not resp:
		resp = _empty_response(sec)
	return overview, bid_doc, schema, ids, sec, resp, responses


def _persist(bid_doc, resp: dict[str, Any], sec: dict[str, Any]) -> None:
	# Strip client totals; recompute
	offer = cstr(resp.get("active_offer_id") or "main")
	lot = cstr(resp.get("active_lot_id") or "")
	computed = compute_totals(sec, resp, offer_id=offer, lot_id=lot)
	resp["computed"] = computed
	resp["totals"] = computed.get("totals") or {}
	# Reopen if previously complete
	issues = collect_issues(sec, resp, offer_id=offer, lot_id=lot)
	if resp.get("complete_confirmed") or resp.get("complete"):
		if issues:
			resp["complete"] = False
			resp["complete_confirmed"] = 0
			resp["section_status"] = STATUS_NEEDS_ATTENTION
		else:
			# editing after complete without issues → in progress until re-completed
			resp["complete"] = False
			resp["complete_confirmed"] = 0
			resp["section_status"] = STATUS_IN_PROGRESS
	else:
		status, _n = derive_price_schedule_section_status(sec, resp)
		resp["section_status"] = status
	save_section_responses(bid_doc.name, SECTION_KEY, resp)
	# Invalidate FoT when prices change
	try:
		from kentender_procurement.tender_configurations.services.form_of_tender import (
			invalidate_fot_certifications,
		)

		doc = frappe.get_doc("Electronic Bid Submission", bid_doc.name)
		invalidate_fot_certifications(doc, reason="price_schedule_changed")
		doc.save(ignore_permissions=True)
		frappe.db.commit()
	except Exception:
		frappe.db.commit()


def get_price_schedule_overview(
	published_tender_ref: str,
	*,
	offer_id: str | None = None,
	lot_id: str | None = None,
) -> dict[str, Any]:
	overview, bid_doc, _schema, ids, sec, resp, _responses = _prepare_section(published_tender_ref)
	flags = _flags(sec)
	offer = cstr(offer_id or resp.get("active_offer_id") or "main").strip() or "main"
	lot = cstr(lot_id if lot_id is not None else resp.get("active_lot_id") or "").strip()
	resp["active_offer_id"] = offer
	if lot:
		resp["active_lot_id"] = lot

	schedules_cfg = sec.get("schedules") or _schedules_from_lines(sec.get("price_lines") or [])
	schedule_rows = []
	complete_count = 0
	for s in schedules_cfg:
		sk = cstr(s.get("schedule_key"))
		prog = _schedule_progress(sec, resp, sk, offer_id=offer, lot_id=lot)
		if prog["status"] == STATUS_COMPLETE:
			complete_count += 1
		schedule_rows.append(
			{
				**s,
				**prog,
				"title": s.get("title") or sk,
				"href": portal_price_schedule_schedule_url(ids["pub_ref"], sk),
			}
		)
	status, blockers = derive_price_schedule_section_status(sec, resp)
	lots = flags.get("lots") if isinstance(flags.get("lots"), list) else []
	offers = flags.get("offers") if isinstance(flags.get("offers"), list) else resp.get("offers") or []
	show_lots = 0 if flags.get("single_lot", 1) or len(lots) <= 1 else 1
	show_alts = 1 if flags.get("alternatives_permitted") and len(offers) > 1 else 0

	return {
		"published_tender_ref": ids["pub_ref"],
		"section_key": SECTION_KEY,
		"section_title": cstr(sec.get("title") or "Price Schedule"),
		"section_instructions": cstr(
			sec.get("bidder_instructions")
			or "Enter your prices for the goods and services specified in this tender."
		),
		"progress_complete": complete_count,
		"progress_total": len(schedule_rows),
		"progress_label": f"{complete_count} of {len(schedule_rows)} schedules complete",
		"progress_percent": int(round(100.0 * complete_count / len(schedule_rows))) if schedule_rows else 0,
		"schedules": schedule_rows,
		"section_status": status,
		"blocker_count": blockers,
		"lots": lots,
		"offers": offers,
		"show_lot_selector": show_lots,
		"show_offer_tabs": show_alts,
		"active_offer_id": offer,
		"active_lot_id": lot,
		"workspace_url": portal_workspace_url(ids["pub_ref"]),
		"review_url": portal_price_schedule_review_url(ids["pub_ref"]),
		"section_url": portal_price_schedule_url(ids["pub_ref"]),
		"bid_id": bid_doc.name,
		"bid_sealed": 1 if cstr(bid_doc.status) == STATUS_SEALED else 0,
		"tender_title": overview.get("tender_title") or "",
		"procuring_entity": overview.get("procuring_entity") or "",
		"continue_url": (
			next((r["href"] for r in schedule_rows if r["status"] != STATUS_COMPLETE), None)
			or portal_price_schedule_review_url(ids["pub_ref"])
		),
	}


def get_price_schedule_editor(
	published_tender_ref: str,
	schedule_key: str,
	*,
	offer_id: str | None = None,
	lot_id: str | None = None,
) -> dict[str, Any]:
	overview, bid_doc, _schema, ids, sec, resp, _responses = _prepare_section(published_tender_ref)
	sk = cstr(schedule_key or "").strip()
	schedules = {cstr(s.get("schedule_key")): s for s in (sec.get("schedules") or _schedules_from_lines(sec.get("price_lines") or []))}
	if sk not in schedules and sk not in (SCHEDULE_SUPPLY, SCHEDULE_RECURRENT):
		frappe.throw(frappe._("Schedule not found."), frappe.DoesNotExistError)
	meta = schedules.get(sk) or {
		"schedule_key": sk,
		"title": "Supply and Installation" if sk == SCHEDULE_SUPPLY else "Recurrent Costs",
		"periods": [],
		"period_labels": {},
	}
	# Omit recurrent when not configured
	if sk == SCHEDULE_RECURRENT and not _applicable_lines(sec, schedule_key=SCHEDULE_RECURRENT):
		frappe.throw(frappe._("Recurrent Costs are not configured for this tender."), frappe.DoesNotExistError)

	offer = cstr(offer_id or resp.get("active_offer_id") or "main").strip() or "main"
	lot = cstr(lot_id if lot_id is not None else resp.get("active_lot_id") or "").strip()
	precision = _precision(sec)
	period_labels = meta.get("period_labels") if isinstance(meta.get("period_labels"), dict) else {}
	rows = []
	for line in _applicable_lines(sec, lot_id=lot or None, schedule_key=sk):
		lr = _get_line_resp(resp, cstr(line.get("line_id")), offer, cstr(line.get("lot_id") or lot))
		total = _line_total(line, lr, precision=precision)
		errs = validate_line_response(line, lr, precision=precision)
		raw_unit = lr.get("unit_price") if "unit_price" in lr else ""
		period_prices = lr.get("period_prices") if isinstance(lr.get("period_prices"), dict) else {}
		period_prices_display = {
			cstr(k): format_money_display(v, precision)
			for k, v in period_prices.items()
			if v not in (None, "")
		}
		row = {
			"line_id": cstr(line.get("line_id")),
			"display_reference": cstr(line.get("display_reference")),
			"description": cstr(line.get("description")),
			"quantity": cstr(line.get("quantity")),
			"unit": cstr(line.get("unit")),
			"required": 1 if line.get("required") not in (0, "0", False) else 0,
			"country_of_origin_required": 1 if line.get("country_of_origin_required") else 0,
			"permitted_currencies": list(line.get("permitted_currencies") or ["KES"]),
			"zero_allowed": 1 if line.get("zero_allowed") else 0,
			"periods": list(line.get("periods") or []),
			"currency": cstr(lr.get("currency") or ""),
			"unit_price": raw_unit,
			"unit_price_display": format_money_display(raw_unit, precision) if raw_unit not in (None, "") else "",
			"country_of_origin": cstr(lr.get("country_of_origin") or ""),
			"period_prices": period_prices,
			"period_prices_display": period_prices_display,
			"line_total": _money(total, precision) if total is not None else "",
			"line_total_display": format_money_display(total, precision) if total is not None else "",
			"errors": errs,
		}
		rows.append(row)

	prog = _schedule_progress(sec, resp, sk, offer_id=offer, lot_id=lot)
	countries = [
		"Kenya",
		"Germany",
		"USA",
		"United Kingdom",
		"India",
		"China",
		"South Africa",
		"Other",
	]
	schedules_ordered = [
		cstr(s.get("schedule_key"))
		for s in (sec.get("schedules") or _schedules_from_lines(sec.get("price_lines") or []))
		if cstr(s.get("schedule_key"))
	]
	try:
		idx = schedules_ordered.index(sk)
	except ValueError:
		idx = -1
	if idx >= 0 and idx + 1 < len(schedules_ordered):
		continue_url = portal_price_schedule_schedule_url(ids["pub_ref"], schedules_ordered[idx + 1])
	else:
		continue_url = portal_price_schedule_review_url(ids["pub_ref"])
	return {
		"published_tender_ref": ids["pub_ref"],
		"section_key": SECTION_KEY,
		"schedule_key": sk,
		"schedule_title": meta.get("title") or sk,
		"is_recurrent": 1 if sk == SCHEDULE_RECURRENT else 0,
		"periods": list(meta.get("periods") or []),
		"period_labels": period_labels,
		"rows": rows,
		"progress": prog,
		"countries": countries,
		"active_offer_id": offer,
		"active_lot_id": lot,
		"section_url": portal_price_schedule_url(ids["pub_ref"]),
		"review_url": portal_price_schedule_review_url(ids["pub_ref"]),
		"continue_url": continue_url,
		"workspace_url": portal_workspace_url(ids["pub_ref"]),
		"bid_sealed": 1 if cstr(bid_doc.status) == STATUS_SEALED else 0,
		"bid_id": bid_doc.name,
		"tender_title": overview.get("tender_title") or "",
		"show_country_column": 1
		if any(r.get("country_of_origin_required") for r in rows)
		else 0,
	}


def get_price_schedule_review(published_tender_ref: str) -> dict[str, Any]:
	overview, bid_doc, _schema, ids, sec, resp, _responses = _prepare_section(published_tender_ref)
	offer = cstr(resp.get("active_offer_id") or "main").strip() or "main"
	lot = cstr(resp.get("active_lot_id") or "").strip()
	computed = compute_totals(sec, resp, offer_id=offer, lot_id=lot)
	issues_raw = collect_issues(sec, resp, offer_id=offer, lot_id=lot)
	issues = []
	for iss in issues_raw:
		issues.append(
			{
				**iss,
				"action_url": portal_price_schedule_schedule_url(
					ids["pub_ref"], iss.get("schedule_key") or SCHEDULE_SUPPLY
				),
			}
		)
	status, blockers = derive_price_schedule_section_status(sec, resp)
	complete_enabled = (
		1
		if (not issues and cstr(bid_doc.status) != STATUS_SEALED and not resp.get("complete_confirmed"))
		else 0
	)

	summary_rows = []
	flags = _flags(sec)
	lots = flags.get("lots") if isinstance(flags.get("lots"), list) else []
	lot_label = next((cstr(l.get("label")) for l in lots if cstr(l.get("lot_id")) == lot), "") if lot else ""
	for s in sec.get("schedules") or _schedules_from_lines(sec.get("price_lines") or []):
		sk = cstr(s.get("schedule_key"))
		prog = _schedule_progress(sec, resp, sk, offer_id=offer, lot_id=lot)
		for currency, bucket in (computed.get("by_currency") or {}).items():
			sub = bucket.get("supply_subtotal") if sk == SCHEDULE_SUPPLY else bucket.get("recurrent_subtotal")
			if sk == SCHEDULE_RECURRENT and bucket.get("recurrent_subtotal") in ("0.00", "0", None):
				# still show if schedule exists
				pass
			summary_rows.append(
				{
					"lot_label": lot_label or "—",
					"schedule_key": sk,
					"schedule_title": s.get("title") or sk,
					"currency": currency,
					"subtotal": format_money_display(sub) if sub not in (None, "") else "0.00",
					"status": prog["status"],
					"edit_url": portal_price_schedule_schedule_url(ids["pub_ref"], sk),
				}
			)
	if not summary_rows:
		# one row per schedule even without prices
		for s in sec.get("schedules") or []:
			sk = cstr(s.get("schedule_key"))
			prog = _schedule_progress(sec, resp, sk, offer_id=offer, lot_id=lot)
			summary_rows.append(
				{
					"lot_label": lot_label or "—",
					"schedule_key": sk,
					"schedule_title": s.get("title") or sk,
					"currency": "—",
					"subtotal": "—",
					"status": prog["status"],
					"edit_url": portal_price_schedule_schedule_url(ids["pub_ref"], sk),
				}
			)

	# Display-formatted computed buckets for review footer totals
	computed_display = {"by_currency": {}, "totals": dict(computed.get("totals") or {})}
	for currency, bucket in (computed.get("by_currency") or {}).items():
		if not isinstance(bucket, dict):
			continue
		computed_display["by_currency"][currency] = {
			k: format_money_display(v) if v not in (None, "") else v for k, v in bucket.items()
		}
	if computed_display["totals"].get("grand_total") not in (None, ""):
		computed_display["totals"]["grand_total_display"] = format_money_display(
			computed_display["totals"].get("grand_total")
		)

	return {
		"published_tender_ref": ids["pub_ref"],
		"section_key": SECTION_KEY,
		"page_title": "Review Price Schedule",
		"section_status": status,
		"blocker_count": blockers,
		"complete_enabled": complete_enabled if not resp.get("complete_confirmed") else 0,
		"section_complete_confirmed": 1 if resp.get("complete_confirmed") else 0,
		"unresolved_issues": issues,
		"summary_rows": summary_rows,
		"computed": computed_display,
		"totals": computed_display.get("totals") or {},
		"section_url": portal_price_schedule_url(ids["pub_ref"]),
		"workspace_url": portal_workspace_url(ids["pub_ref"]),
		"review_url": portal_price_schedule_review_url(ids["pub_ref"]),
		"bid_id": bid_doc.name,
		"bid_sealed": 1 if cstr(bid_doc.status) == STATUS_SEALED else 0,
		"tender_title": overview.get("tender_title") or "",
		"read_only": 1 if cstr(bid_doc.status) == STATUS_SEALED else 0,
	}


def save_price_schedule_lines(
	published_tender_ref: str,
	payload: dict[str, Any] | str | None = None,
) -> dict[str, Any]:
	"""Save one or more line responses. Server recomputes totals."""
	overview, bid_doc, _schema, ids, sec, resp, _responses = _prepare_section(published_tender_ref)
	if cstr(bid_doc.status) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")
	if isinstance(payload, str):
		payload = _parse_json(payload, {})
	payload = dict(payload or {})
	# Never accept client totals
	payload.pop("computed", None)
	payload.pop("totals", None)
	payload.pop("grand_total", None)

	offer = cstr(payload.get("offer_id") or resp.get("active_offer_id") or "main").strip() or "main"
	lot = cstr(payload.get("lot_id") if payload.get("lot_id") is not None else resp.get("active_lot_id") or "").strip()
	resp["active_offer_id"] = offer
	resp["active_lot_id"] = lot

	raw_lines = payload.get("lines")
	if isinstance(raw_lines, dict):
		items = [{"line_id": k, **v} for k, v in raw_lines.items() if isinstance(v, dict)]
	elif isinstance(raw_lines, list):
		items = [x for x in raw_lines if isinstance(x, dict)]
	else:
		items = []

	line_index = {cstr(l.get("line_id")): l for l in (sec.get("price_lines") or []) if isinstance(l, dict)}
	field_errors: dict[str, list[str]] = {}
	for item in items:
		lid = cstr(item.get("line_id") or "").strip()
		if not lid or lid not in line_index:
			continue
		# Published fields cannot be modified via bidder payload
		clean = {
			"currency": cstr(item.get("currency") or "").strip(),
			"country_of_origin": cstr(item.get("country_of_origin") or "").strip(),
		}
		if "unit_price" in item:
			# Preserve explicit zero; omit blank; strip display commas
			if item.get("unit_price") is None or item.get("unit_price") == "":
				clean["unit_price"] = ""
			else:
				clean["unit_price"] = cstr(item.get("unit_price")).replace(",", "").strip()
		if isinstance(item.get("period_prices"), dict):
			clean["period_prices"] = {
				cstr(k): cstr(v).replace(",", "").strip()
				for k, v in item["period_prices"].items()
				if cstr(k).strip() and v not in (None, "")
			}
		_set_line_resp(resp, lid, offer, cstr(line_index[lid].get("lot_id") or lot), clean)
		errs = validate_line_response(line_index[lid], clean, precision=_precision(sec))
		if errs:
			field_errors[lid] = errs

	_persist(bid_doc, resp, sec)
	sk = cstr(payload.get("schedule_key") or "").strip()
	if sk:
		return get_price_schedule_editor(published_tender_ref, sk, offer_id=offer, lot_id=lot)
	return {
		"overview": get_price_schedule_overview(published_tender_ref, offer_id=offer, lot_id=lot),
		"field_errors": field_errors,
	}


def complete_price_schedule(published_tender_ref: str) -> dict[str, Any]:
	overview, bid_doc, _schema, ids, sec, resp, _responses = _prepare_section(published_tender_ref)
	if cstr(bid_doc.status) == STATUS_SEALED:
		frappe.throw(frappe._("Sealed electronic bids are immutable."), title="BID_IMMUTABLE")
	offer = cstr(resp.get("active_offer_id") or "main")
	lot = cstr(resp.get("active_lot_id") or "")
	issues = collect_issues(sec, resp, offer_id=offer, lot_id=lot)
	if issues:
		frappe.throw(
			frappe._("Resolve all pricing issues before completing the Price Schedule."),
			title="KT_PS_NOT_READY",
		)
	computed = compute_totals(sec, resp, offer_id=offer, lot_id=lot)
	resp["computed"] = computed
	resp["totals"] = computed.get("totals") or {}
	resp["complete"] = True
	resp["complete_confirmed"] = 1
	resp["section_status"] = STATUS_COMPLETE
	meta = resp.get("_meta") if isinstance(resp.get("_meta"), dict) else {}
	meta = dict(meta)
	meta["completed_by"] = frappe.session.user
	meta["completed_at"] = str(now_datetime())
	resp["_meta"] = meta
	save_section_responses(bid_doc.name, SECTION_KEY, resp)
	frappe.db.commit()
	return get_price_schedule_review(published_tender_ref)


def price_schedule_fot_projection(section_responses: Any) -> dict[str, Any]:
	"""FoT-facing projection from bidder PS payload."""
	resp = _response_map(section_responses)
	computed = resp.get("computed") if isinstance(resp.get("computed"), dict) else {}
	totals = resp.get("totals") if isinstance(resp.get("totals"), dict) else {}
	if not totals and isinstance(computed.get("totals"), dict):
		totals = computed["totals"]
	complete = bool(resp.get("complete_confirmed") or resp.get("complete")) or cstr(
		resp.get("section_status")
	) == STATUS_COMPLETE
	grand = totals.get("grand_total")
	currency = cstr(totals.get("currency") or resp.get("currency") or "").strip()
	grand_display = format_money_display(grand) if grand not in (None, "") else ""
	return {
		"complete": 1 if complete else 0,
		"grand_total": grand,
		"grand_total_display": grand_display,
		"currency": currency,
		"total_display": (
			f"{currency} {grand_display}".strip()
			if grand not in (None, "") and complete
			else ("Not completed" if not complete else "—")
		),
		"by_currency": computed.get("by_currency") or {},
	}
