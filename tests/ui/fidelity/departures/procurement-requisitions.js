// Structural departures for the Procurement Requisitions screens (REQ-CHG-001
// v1.11, board `design/Requisitions - Design Board v2.dc.html`).
//
// Keyed `Component#variant`. Every entry names what the build adds or omits
// that the board does not draw, why, and the authority for it. Unregistered
// additions fail; stale entries fail too. Never resolve a departure by
// deleting an enhancement the spec requires.
// The board's variant sets "show only the facts that differ from their named
// parent" (board intro): the page header a variant inherits is not redrawn.
const INHERITED_HEADER = {
	path: "h3",
	because: "The page header belongs to the parent REQ-DES-01 frame; the variant set draws only what differs from it.",
	authority: "Requisitions board v2 intro — variant sets show only the facts that differ from their named parent",
};

// REQ-DES-07 and REQ-DES-08 state in a note that REQ-DES-06's result-first
// review follows; they do not redraw it. Its section headings and the
// delivery-date warning inside the open Purpose section are that composition.
const REVIEW_BY_REFERENCE = (frame) => [
	...Array.from({ length: 5 }, () => ({
		path: "card-title",
		because: "A section heading of the REQ-DES-06 result-first review that this frame includes by reference.",
		authority: `Requisitions board v2 ${frame} note — the complete review from REQ-DES-06 follows`,
	})),
	{
		path: "notice.is-warning",
		because: "The delivery-date warning inside REQ-DES-06's open Purpose section, included by reference.",
		authority: `Requisitions board v2 ${frame} note — Purpose starts open because of the date warning`,
	},
];

export const DEPARTURES = {
	"WorkspaceScreen#REQ-DES-01-DRAFT": [INHERITED_HEADER],
	"WorkspaceScreen#REQ-DES-01-ACTION": [INHERITED_HEADER],
	"WorkspaceScreen#REQ-DES-01-NONE": [INHERITED_HEADER],
	// The contributor frame draws only its Access table, footer and saved
	// notice; the section headings above them are the parent REQ-DES-03's.
	"RequestDetailsTask#REQ-DES-03-CONTRIBUTOR": [
		{ path: "card-title", because: "Amounts requested and Equipment headings belong to the parent REQ-DES-03 frame.", authority: INHERITED_HEADER.authority },
		{ path: "card-title", because: "Amounts requested and Equipment headings belong to the parent REQ-DES-03 frame.", authority: INHERITED_HEADER.authority },
	],
	// The one-source frame redraws only the department table; the four shared
	// details fields are unchanged from the parent REQ-DES-04 dialog.
	"AddLaptopDialog#REQ-DES-04-ONE-SOURCE": Array.from({ length: 4 }, () => ({
		path: "dialog > field",
		because: "Shared details (category, item name, delivery location, latest date) are the parent REQ-DES-04 dialog's; the variant draws only what differs.",
		authority: INHERITED_HEADER.authority,
	})),
	// REQ-DES-05-COMPLETE draws the Reviewed head and the first group, then
	// states in words that "the same eleven technical rows, six warranty/support
	// values and five acceptance checks are shown as confirmed content".
	"DepartmentTaskScreen#REQ-DES-07": [
		...REVIEW_BY_REFERENCE("REQ-DES-07"),
		{
			testid: "req-record-details",
			because: "The frame reuses REQ-DES-06's result-first review and disclosure states by reference; Record details is part of that composition.",
			authority: "Requisitions board v2 REQ-DES-07 note — uses the review and disclosure states from REQ-DES-06",
		},
	],
	"ProcurementTaskScreen#REQ-DES-08": [
		...REVIEW_BY_REFERENCE("REQ-DES-08"),
		{
			testid: "req-record-details",
			because: "The frame states that REQ-DES-06's complete review summaries and expandable detail follow; Record details is part of that composition.",
			authority: "Requisitions board v2 REQ-DES-08 note — the complete review from REQ-DES-06 follows here",
		},
	],
	"StoppedScreen#Planning correction requested": [
		{
			testid: "req-record-details",
			because: "The frame states that the complete request follows in read-only form; Record details is part of that complete read-only request.",
			authority: "Requisitions board v2 REQ-DES-11 note — the complete request follows in read-only form",
		},
	],
	"VersionScreen#Returned reviewed Version": [
		{ path: "h3", because: "The requisition title heads the record page; the frame draws only the Version's status, decision facts and link.", authority: INHERITED_HEADER.authority },
		{
			testid: "req-record-details",
			because: "The frame is 'the exact earlier Version as a complete read-only review'; Record details is part of that complete review (REQ-DES-06 composition).",
			authority: "Requisitions board v2 REQ-DES-11 Returned reviewed Version caption",
		},
	],
	"RequirementsTask#REQ-DES-05-COMPLETE": [
		...Array.from({ length: 3 }, () => ({
			path: "card-title",
			because: "Technical requirements, Warranty and support and Acceptance checks headings of the parent REQ-DES-05 workbench, which the COMPLETE frame summarises in its note rather than redraws.",
			authority: "Requisitions board v2 REQ-DES-05-COMPLETE note",
		})),
		...Array.from({ length: 6 }, () => ({
			path: "field",
			because: "The six warranty and support values, kept as confirmed content per the COMPLETE frame's note.",
			authority: "Requisitions board v2 REQ-DES-05-COMPLETE note",
		})),
	],
};

// Screens compared structurally against their boards (grown slice by slice).
export const COVERED = [
	"WorkspaceScreen#REQ-DES-01",
	"WorkspaceScreen#REQ-DES-01-DRAFT",
	"WorkspaceScreen#REQ-DES-01-ACTION",
	"WorkspaceScreen#REQ-DES-01-NONE",
	"WorkspaceScreen#REQ-DES-01-TECHNICAL",
	"StartDialog#REQ-DES-02",
	"StartDialog#REQ-DES-02-UNSUPPORTED",
	"StartDialog#REQ-DES-02-RULE-UNAVAILABLE",
	"StartDialog#REQ-DES-02-RESERVATION-UNSUPPORTED",
	"EditorScreen#REQ-DES-03",
	"RequestDetailsTask#Purchase and source details",
	"RequestDetailsTask#REQ-DES-03-COMPLETE",
	"EditorScreen#REQ-DES-03-RETURNED",
	"RequestDetailsTask#REQ-DES-03-CONTRIBUTOR",
	"AddLaptopDialog#REQ-DES-04",
	"AddLaptopDialog#REQ-DES-04-ONE-SOURCE",
	"AddLaptopDialog#REQ-DES-04-VALIDATION",
	"EditorScreen#REQ-DES-05",
	"RequirementsTask#REQ-DES-05-COMPLETE",
	"ReviewTask#REQ-DES-06",
	"ReviewTask#REQ-DES-06-DIRECT-HOD",
	"ReasonDialog#Withdraw requisition dialog",
	"DepartmentTaskScreen#REQ-DES-07",
	"ReasonDialog#Return dialog",
	"ProcurementTaskScreen#REQ-DES-08",
	"ProcurementTaskScreen#Procurement checks",
	"ProcurementTaskScreen#REQ-DES-08-BLOCKING-FUNDING",
	"ProcurementTaskScreen#REQ-DES-08-HOLD",
	"ProcurementTaskScreen#REQ-DES-08-TECHNICAL",
	"ReasonDialog#Return-to-department dialog",
	"ReasonDialog#Change-submitting-department dialog",
	"ReasonDialog#REQ-DES-08-CORRECTION",
	"AuthoriseDialog#REQ-DES-09",
	"AuthorisedScreen#REQ-DES-10",
	"AuthorisedScreen#HOPF before consumption",
	"AuthorisedScreen#Consumed",
	"AuthorisedScreen#Revoked",
	"ReasonDialog#Revocation dialog",
	"StoppedScreen#Planning correction requested",
	"StoppedScreen#Outcome unavailable",
	"StoppedScreen#Another request unresolved",
	"StoppedScreen#Fresh-start confirmation · Resolved",
	"VersionScreen#Returned reviewed Version",
];
