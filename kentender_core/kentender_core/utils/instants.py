# Instants: where site time ends and UTC begins.
#
# Owner decision 26 Sep 2026 (FU-V127-01): every module stores and passes
# instants within the site as naive datetimes in the site timezone — Frappe's
# own rule (`now_datetime()`, `creation`, `modified`) — and shows them as
# stored (`kentender_core.utils.display.display_datetime`). A serialized
# message between modules (an event or outbox payload, anything that leaves
# the site) carries ISO-8601 UTC with a trailing "Z", and its receiver turns
# it back into site time before storing it. These two functions are the only
# conversion between the two.

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from frappe.utils import cstr, get_datetime, get_system_timezone


def to_utc_iso(value) -> str:
	"""A stored (site-timezone) instant as ``2026-11-25T07:00:00Z``."""
	if not value:
		return ""
	local = get_datetime(value).replace(tzinfo=ZoneInfo(get_system_timezone()))
	return local.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def from_utc_iso(value) -> datetime | None:
	"""An ISO-8601 UTC instant from a message as the naive site-timezone
	datetime every module stores."""
	if not value:
		return None
	instant = get_datetime(cstr(value).replace("Z", "+00:00"))
	if instant.tzinfo is None:
		instant = instant.replace(tzinfo=timezone.utc)
	return instant.astimezone(ZoneInfo(get_system_timezone())).replace(tzinfo=None)
