// CFG-CHG-002 v0.14 §9 — System setup's link grammar, in one place.
//
//   #<tab>
//   #fiscal-years/{fy}
//   #procurement-settings/{section}
//   #procurement-settings/{section}/new
//   #procurement-settings/{section}/{id}[/versions/{version_id}][/{action}]
//
// Sections are the spec's stable keys (funding-sources, procurement-rules,
// schedule-profiles, reminders, supplier-portal) plus `calendars`, which the spec opens inside
// this tab from a working-days schedule. Each segment is encoded on its own,
// so an id with a space or a slash stays one id.
//
// The current tabs still switch on their older internal view names
// (`rule/X`, `new-method-version/X`, …). `legacyToRoute`/`routeToLegacy`
// translate those to and from these links until each screen is re-ported
// (plan Phase 5), so the URL is already the spec's while the screens change.
export const TABS = ["procuring-entity", "fiscal-years", "organisation-structure", "users-and-responsibilities", "procurement-settings"];
export const SECTIONS = ["funding-sources", "procurement-rules", "schedule-profiles", "reminders", "supplier-portal", "calendars"];
const ACTIONS = ["new-version", "edit", "check-sources", "history"];
const ID_TABS = ["fiscal-years", "organisation-structure", "users-and-responsibilities"];
export const STAFF_HOME_UNITS = "staff-home-units";

function decode(segment) {
	try {
		return decodeURIComponent(segment);
	} catch (e) {
		return segment;
	}
}

export function parseSetupHash(hash) {
	const route = { tab: "", section: "", id: "", versionId: "", action: "" };
	const parts = String(hash || "")
		.replace(/^#/, "")
		.split("/")
		.filter((part) => part !== "")
		.map(decode);
	if (!TABS.includes(parts[0])) return route;
	route.tab = parts[0];
	// The Staff home units tab of Users and responsibilities (AUTH-ADR-001 v1.12 §12) is a local section, not a responsibility id.
	if (route.tab === "users-and-responsibilities" && parts[1] === STAFF_HOME_UNITS) {
		route.section = STAFF_HOME_UNITS;
		return route;
	}
	// A year, an organisation unit and a responsibility each open by id.
	if (ID_TABS.includes(route.tab)) {
		route.id = parts[1] || "";
		return route;
	}
	if (route.tab !== "procurement-settings" || !SECTIONS.includes(parts[1])) return route;
	route.section = parts[1];
	let rest = parts.slice(2);
	if (rest[0] === "new") {
		route.action = "new";
		return route;
	}
	route.id = rest[0] || "";
	rest = rest.slice(1);
	if (rest[0] === "versions" && rest[1]) {
		route.versionId = rest[1];
		rest = rest.slice(2);
	}
	if (ACTIONS.includes(rest[0])) route.action = rest[0];
	return route;
}

export function buildSetupHash({ tab = "", section = "", id = "", versionId = "", action = "" } = {}) {
	if (!tab) return "";
	const parts = [tab];
	if (tab === "users-and-responsibilities" && section === STAFF_HOME_UNITS) return `${tab}/${STAFF_HOME_UNITS}`;
	if (ID_TABS.includes(tab)) {
		if (id) parts.push(id);
		return parts.map((p, i) => (i ? encodeURIComponent(p) : p)).join("/");
	}
	if (section) parts.push(section);
	if (section && action === "new") parts.push("new");
	else if (section && id) {
		parts.push(encodeURIComponent(id));
		if (versionId) parts.push("versions", encodeURIComponent(versionId));
		if (action) parts.push(action);
	}
	return parts.join("/");
}

// Older view name → [section, action]; the id is the view's name.
const LEGACY = {
	source: ["funding-sources", ""],
	"new-source": ["funding-sources", "new"],
	rule: ["procurement-rules", ""],
	"new-rule": ["procurement-rules", "new"],
	"new-rule-version": ["procurement-rules", "new-version"],
	"edit-rule-version": ["procurement-rules", "edit"],
	"new-method-version": ["procurement-rules", "new-version"],
	"edit-method-rule": ["procurement-rules", "edit"],
	"check-sources": ["procurement-rules", "check-sources"],
	profile: ["schedule-profiles", ""],
	"new-schedule": ["schedule-profiles", "new"],
	"new-schedule-version": ["schedule-profiles", "new-version"],
	"edit-schedule": ["schedule-profiles", "edit"],
	calendar: ["calendars", ""],
	"new-calendar": ["calendars", "new"],
	"calendar-new-version": ["calendars", "new-version"],
	"calendar-edit": ["calendars", "edit"],
	"calendar-check-sources": ["calendars", "check-sources"],
	"calendar-history": ["calendars", "history"],
};

export function legacyToRoute(tab, legacy) {
	const [kind, ...rest] = String(legacy || "").split("/");
	const name = rest.join("/");
	if (tab === "fiscal-years") return { tab, section: "", id: kind === "year" ? name : "", versionId: "", action: "" };
	if (SECTIONS.includes(kind) && !name) return { tab, section: kind, id: "", versionId: "", action: "" };
	const mapped = LEGACY[kind];
	if (!mapped) return { tab, section: "", id: "", versionId: "", action: "" };
	const [section, action] = mapped;
	return { tab, section, id: action === "new" ? "" : name, versionId: "", action };
}

export function routeToLegacy(route, { isMethodRule = () => false } = {}) {
	const { tab, section, id, versionId, action } = route || {};
	if (tab === "fiscal-years") return id ? `year/${id}` : "";
	if (tab !== "procurement-settings") return "";
	if (action === "new") {
		return { "funding-sources": "new-source", "procurement-rules": "new-rule", "schedule-profiles": "new-schedule", calendars: "new-calendar" }[section] || "";
	}
	if (!id) return "";
	if (section === "funding-sources") return `source/${id}`;
	if (section === "calendars") {
		const kind = { "new-version": "calendar-new-version", edit: "calendar-edit", "check-sources": "calendar-check-sources", history: "calendar-history" }[action];
		return `${kind || "calendar"}/${id}`;
	}
	if (section === "schedule-profiles") {
		if (action === "new-version") return `new-schedule-version/${id}`;
		if (action === "edit") return `edit-schedule/${id}`;
		return `profile/${versionId || id}`;
	}
	if (section === "procurement-rules") {
		const method = isMethodRule(id);
		if (action === "new-version") return `${method ? "new-method-version" : "new-rule-version"}/${id}`;
		if (action === "edit") return `${method ? "edit-method-rule" : "edit-rule-version"}/${id}`;
		if (action === "check-sources") return `check-sources/${versionId || id}`;
		return `rule/${versionId || id}`;
	}
	return "";
}
