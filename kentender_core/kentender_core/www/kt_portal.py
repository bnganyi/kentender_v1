# Copyright (c) 2026, KenTender and contributors
# For license information, please see license.txt

"""The one public supplier portal page (BDS-CHG-001 v0.8 plan OD-B). Every
portal route is a `website_route_rules` entry pointing here; the owning
app's surface resolver answers it through `portal_runtime.resolve`."""

from __future__ import annotations

import json
import os

import frappe

from kentender_core.services import portal_runtime

no_cache = 1
_CSS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "public", "css")


def _asset_version(name: str) -> str:
	try:
		return str(int(os.path.getmtime(os.path.join(_CSS_DIR, name))))
	except OSError:
		return "0"


def get_context(context):
	request = frappe.local.request
	answer = portal_runtime.resolve(
		request.path,
		query={key: request.args.get(key) for key in request.args} if request else {},
		query_string=request.query_string.decode("utf-8") if request and request.query_string else "",
	)
	if answer.get("redirect"):
		frappe.local.flags.redirect_location = answer["redirect"]
		raise frappe.Redirect
	if answer["verdict"] == "NOT_FOUND":
		context.http_status_code = 404
	context.no_cache = 1
	context.title = answer["title"] or "KenTender"
	context.kt_portal = answer
	context.kt_portal_asset_version = _asset_version
	context.kt_portal_initial = json.dumps(
		{"verdict": answer["verdict"], "path": answer["path"], "surface": answer["surface"]["key"], "payload": answer["payload"], "signed_in": answer["shell"]["signed_in"]},
		default=str, ensure_ascii=False,
	).replace("</", "<\\/")
	lang = frappe.local.lang or "en"
	if lang == "en":
		context.kt_portal_messages = ""
	else:
		from frappe.translate import get_all_translations

		context.kt_portal_messages = json.dumps(get_all_translations(lang) or {}, ensure_ascii=False).replace("</", "<\\/")
	return context
