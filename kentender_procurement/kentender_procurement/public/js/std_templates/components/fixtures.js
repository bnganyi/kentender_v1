// Component-test fixtures in the exact InstalledSTDReleaseProjection v1 shape
// the read services return (kentender_procurement.std_templates.services.read).
// Values follow the installed release 1.1 on the dev site.

export function listPayload(kind = "rows") {
	const release = {
		release_id: "stdr-0e81b40c-d548-498c-855a-d4f80764af40",
		display_name: "IT Equipment Open Tender",
		template_key: "IT-EQUIPMENT-OPEN-V1",
		template_release: "1.1",
		supported_use: { line: "Goods · Open Tender · single lot", detail: "None/Youth/Women/Persons with disabilities; County restriction conditional", label: "Goods · Open Tender · single lot · None/Youth/Women/Persons with disabilities; County restriction conditional" },
		status: "Unavailable",
		status_class: "is-attention",
		consequence: "This release cannot be used to publish a Tender. Open it to see why.",
		official_source: "PPRA Standard Tender Document for Procurement of Goods",
		last_verified: "26 September 2026, 00:09 EAT",
	};
	const base = { outcome: "OK", installed_count: 1, filters: { search: "", status: "", statuses: ["All statuses", "Available", "Unavailable", "Superseded", "Withdrawn"] } };
	if (kind === "filtered") return { ...base, releases: [], empty: "No STD Templates match these filters.", empty_kind: "filtered" };
	if (kind === "installed") return { ...base, installed_count: 0, releases: [], empty: "No STD Templates are installed. Ask whoever manages this site to install a release.", empty_kind: "installed" };
	return { ...base, releases: [release], empty: "", empty_kind: "" };
}

export function detailPayload(state = "Unavailable") {
	const statusClass = { Available: "is-live", Unavailable: "is-attention", Superseded: "is-pending", Withdrawn: "is-critical" }[state];
	const verificationRows = ["Official source", "Tender documents", "Supplier responses", "Evaluation and contract mappings", "Reservation variants", "Addendum identity rules", "MoH fixture"].map((check) => ({
		check,
		result: "Incomplete",
		result_class: "is-attention",
		note: "Automated checks passed; awaiting the named review.",
	}));
	const on = state !== "Unavailable";
	verificationRows.push({ check: "Site switch", result: on ? "On" : "Off", result_class: on ? "is-live" : "is-attention", note: `Switched ${on ? "on" : "off"} by bnganyi on 26 September 2026, 10:00 EAT.` });
	const variant = {};
	if (state === "Superseded") variant.successor = "IT Equipment Open Tender · Release 1.2";
	if (state === "Withdrawn") variant.withdrawal = [{ label: "Reason", value: "Legal defect in the reservation clause." }, { label: "Recorded", value: "30 September 2026, 10:00 EAT" }, { label: "Actor", value: "bnganyi" }, { label: "Successor", value: "" }];
	return {
		outcome: "OK",
		release: {
			release_id: "stdr-0e81b40c-d548-498c-855a-d4f80764af40",
			display_name: "IT Equipment Open Tender",
			template_key: "IT-EQUIPMENT-OPEN-V1",
			template_release: "1.1",
			status: state,
			status_class: statusClass,
			lifecycle_status: state === "Unavailable" ? "Available" : state,
			failed_verification: false,
			consequence: state === "Available" ? "This release may be used only for the supported procurements below." : "This release cannot be used to publish a Tender.",
			next_step: state === "Unavailable" ? { head: "Switched off on this site.", holder: "Whoever manages this site can switch it on." } : { head: "Ready for supported Tenders.", holder: "Next: Procurement Officer." },
		},
		blockers: state === "Unavailable" ? [{ n: 1, text: "This release is switched off on this site.", owner: "Site administrator", failed: false, gate_id: "" }] : [],
		overview: {
			supported: [
				{ label: "Procurement category", value: "Goods — IT Equipment" },
				{ label: "Procurement method", value: "Open Tender" },
				{ label: "Lots", value: "One lot" },
			],
			not_supported: ["Works", "Weighted technical scoring"],
			release: { template_release: "1.1", status: state, status_class: statusClass },
			official_source: { title: "PPRA Standard Tender Document for Procurement of Goods", source_owner: "Public Procurement Regulatory Authority (PPRA)", retrieval_date: "28 August 2026" },
		},
		tender_content: {
			outputs: [
				{ output_id: "invitation", title: "Invitation to Tender", summary: "Separate public notice; never embedded in the issued Tender." },
				{ output_id: "issued_tender", title: "Complete issued Tender", summary: "Cover, contents and Sections I–VIII; 23 of 28 official forms published." },
			],
			coverage_line: "290 of 296 rows reviewed; 28 forms accounted for",
			inherited: "Goods and delivery and technical requirements",
			entered: "Tender details and dates and contract terms",
			generated: "Tender reference and schedules",
		},
		bid_response: {
			tasks: [{ n: 1, name: "Tender documents and addenda", purpose: "View and acknowledge the current published package." }],
			controls: ["Confirmation", "Yes/No"],
			response_families: "13 response families from 24 released response rules",
			fixture_content: "One grouped Goods line from 2 Requisition items",
			reservation_evidence: "Evaluated as eligibility pass/fail.",
			evaluation_groups: [{ n: 1, name: "Eligibility", note: "", rule_count: 13 }, { n: 2, name: "Technical compliance", note: "One shared pass/fail gate", rule_count: 7 }],
			carried: ["Goods and delivery schedule"],
			not_carried: ["Eligibility-only evidence"],
		},
		coverage: {
			treatments: [{ label: "Rendered", n: 188 }, { label: "Structured input", n: 30 }, { label: "Conditional", n: 11 }, { label: "Excluded with reason", n: 60 }, { label: "Not applicable", n: 7 }],
			total: 296,
			forms_total: 28,
			mapping_rule: "",
			changes: { heading: "Changes from release 1.0", result: "Breaking — not interchangeable with the preceding release", summary: "Compared with release 1.0: 155 changes.", chips: ["Response rules: 24 added"], preceding_release: "1.0" },
		},
		verification: { caption: "These checks were recorded when this release was built. They are for information only; whether this site can use the release depends on its switch, its integrity and its renderer.", rows: verificationRows, source: { last_checked: "28 August 2026", checked_by: "bnganyi (product owner)", outcome: "Passed" } },
		variant,
		technical: [{ label: "Release ID", value: "stdr-0e81b40c-d548-498c-855a-d4f80764af40" }, { label: "Product profile", value: "GOODS-IT-SIMPLE-V1" }],
		last_verified: "26 September 2026, 00:09 EAT",
		concerns: { counts: { Open: 0 }, total: 0, own: [], categories: ["Source treatment", "Tender document", "Supplier response", "Evaluation mapping", "Contract mapping", "Renderer", "Other"] },
		allowed_actions: ["preview", "download_review_pack", "view_coverage", "view_changes", "report_concern"],
		viewer: { technical: false },
	};
}
