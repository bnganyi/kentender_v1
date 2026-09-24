// The boards' canonical Reservation allocation fixture (PLN v1.25 §10.2):
// 30% of KES 130,000,000 eligible = KES 39,000,000; KES 50,000,000 Youth =
// 38.46%. Shared by the component and screen specs.
export const ITEMS = [
	{
		plan_item_id: "PPI-MOH-2027-021",
		title: "National digital health infrastructure upgrade",
		value_display: "KES 80,000,000",
		applicability: "Included",
		reason: "Counted: the reservation rule includes all planned procurement",
		designation: "None",
		qualifying_display: "KES 0",
		qualifying_is_zero: true,
	},
	{
		plan_item_id: "PPI-MOH-2027-033",
		title: "Clinical training and deployment laptops for digital health rollout",
		value_display: "KES 50,000,000",
		applicability: "Included",
		reason: "Counted: the reservation rule includes all planned procurement",
		designation: "Youth",
		qualifying_display: "KES 50,000,000",
		qualifying_is_zero: false,
	},
];

export const READY = {
	status_label: "Required allocation met",
	status_kind: "live",
	met: true,
	remaining_display: "KES 0",
	required_display: "KES 39,000,000",
	qualifying_display: "KES 50,000,000",
	share_display: "38.46%",
	eligible_display: "KES 130,000,000",
	target_display: "30%",
	plan_basis: "PLN-MOH-2027-001, Version 1",
	rule_version: "Reservation rules, Version 9",
	county_display: "Not applicable",
	restrictions_line: "No additional restriction applies",
	items: ITEMS,
};

export const BASE = {
	...READY,
	status_label: "Required allocation not met",
	status_kind: "attention",
	met: false,
	remaining_display: "KES 39,000,000",
	qualifying_display: "KES 0",
	share_display: "",
	items: [ITEMS[0], { ...ITEMS[1], designation: "None", qualifying_display: "KES 0", qualifying_is_zero: true }],
};
