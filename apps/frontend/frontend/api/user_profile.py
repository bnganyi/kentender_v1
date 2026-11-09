import frappe
from frappe.utils import strip_html


@frappe.whitelist()
def get_my_profile():
	user_id = frappe.session.user
	if not user_id or user_id == "Guest":
		frappe.throw("You must be signed in to view your profile.", frappe.PermissionError)

	user = frappe.get_doc("User", user_id)

	profile = {
		"full_name": user.full_name,
		"first_name": user.first_name,
		"middle_name": user.middle_name,
		"last_name": user.last_name,
		"email": user.email,
		"username": user.username,
		"phone": user.phone,
		"mobile_no": user.mobile_no,
		"location": user.location,
		"language": user.language,
		"time_zone": user.time_zone,
		"user_image": user.user_image,
		"last_login": user.last_login,
		"last_active": user.last_active,
	}

	activity = frappe.get_all(
		"Activity Log",
		filters={"user": user_id},
		fields=["subject", "operation", "status", "communication_date", "ip_address"],
		order_by="creation desc",
		limit_page_length=50,
	)
	for event in activity:
		event.subject = strip_html(event.subject or "")
	session_history = frappe.get_all(
		"Activity Log",
		filters={"user": user_id, "operation": ["in", ["Login", "Logout"]]},
		fields=["subject", "operation", "status", "communication_date", "ip_address"],
		order_by="creation desc",
		limit_page_length=50,
	)
	for event in session_history:
		event.subject = strip_html(event.subject or "")
	sessions = [
		{
			"id": session.id,
			"ip_address": session.ip_address,
			"last_updated": session.last_updated,
			"is_current": session.is_current,
			"session_created": session.session_created,
			"user_agent": session.user_agent,
		}
		for session in user.active_sessions
	]

	return {"profile": profile, "activity": activity, "session_history": session_history, "sessions": sessions}
