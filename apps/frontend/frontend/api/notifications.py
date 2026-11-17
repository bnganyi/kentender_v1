import frappe
from frappe.utils import cint
from frappe.utils.caching import http_cache


@frappe.whitelist()
@http_cache(max_age=60, stale_while_revalidate=60 * 60)
def get_notification_logs(limit: int = 20, start: int = 0, unread: bool = False):
	filters = {"for_user": frappe.session.user}
	if cint(unread):
		filters["read"] = 0

	notification_logs = frappe.db.get_list(
		"Notification Log",
		fields=[
			"name",
			"subject",
			"type",
			"read",
			"from_user",
			"creation",
			"link",
			"document_type",
			"document_name",
		],
		filters=filters,
		limit_start=max(cint(start), 0),
		limit=min(max(cint(limit), 1), 100),
		order_by="creation desc",
	)

	users = list({log.from_user for log in notification_logs if log.from_user})
	user_info = frappe._dict()
	for user in users:
		frappe.utils.add_user_info(user, user_info)

	return {"notification_logs": notification_logs, "user_info": user_info}