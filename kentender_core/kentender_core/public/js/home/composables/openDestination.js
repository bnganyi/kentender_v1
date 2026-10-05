// Navigation only (HOME §11): Home creates, clears and marks nothing. A destination is the
// owner's own route (and options), already checked by the server for owner and viewer; the
// owner's record read rechecks authority and current state when it opens (HOME §5, §7).
export function hrefOf(destination) {
	return "/app/" + destination.route.map((part) => encodeURIComponent(part)).join("/");
}

export function openDestination(destination) {
	const options = destination.route_options || {};
	if (Object.keys(options).length) frappe.route_options = { ...options };
	return frappe.set_route(...destination.route);
}

// A plain click follows the Desk route; a modified click (new tab, new window) keeps the
// browser's own behaviour on the real href.
export function followLink(event, destination) {
	if (event.defaultPrevented || event.button > 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
	event.preventDefault();
	openDestination(destination);
}
