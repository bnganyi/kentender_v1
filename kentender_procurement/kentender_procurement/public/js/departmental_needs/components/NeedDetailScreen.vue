<!-- NDS-UI-04 / NDS-UI-06 need detail (§12.4) — NDS-DES-05 submitted,
     NDS-DES-07 accepted + the Planning-status variants derivable from the
     existing usage/disposition projections (NONE/PROCEEDING/EXCLUDED/
     STILL-ACTIVE/RESTORED). The screen shows the exact revision it was asked
     for and never rewrites the requested one. -->
<template>
	<div class="kt-panel-lg" style="max-width: 700px">
		<div style="display: flex; justify-content: space-between; align-items: flex-start">
			<div>
				<h4 style="margin: 0">{{ shownRevision.title }}</h4>
				<div class="kt-label" style="margin: 4px 0 8px">{{ need.need_reference }}</div>
				<div style="display: flex; gap: var(--kt-space-3); align-items: center">
					<span class="kt-status" :class="statusClass">{{ statusLabel }}</span>
					<span class="text-muted" style="font-size: 12px">Revision {{ shownRevision.revision_number }}</span>
				</div>
			</div>
			<div v-if="ownerActions.length" style="display: flex; gap: var(--kt-space-2); flex: none">
				<button
					v-for="action in ownerActions"
					:key="action.code"
					class="kt-btn kt-btn-secondary"
					data-testid="nds-owner-action"
					:data-action="action.code"
					@click="$emit(action.code)"
				>
					{{ action.label }}
				</button>
			</div>
		</div>

		<!-- NDS-DES-14 MASKED-DETAIL is rendered by the parent (access denied
		     before this component mounts); a superseded pinned revision stays
		     readable and says so. -->
		<div v-if="isHistoricalRevision" class="kt-notice is-info" style="margin-top: var(--kt-space-4)">
			<div class="kt-notice-body">
				This revision has been superseded. Revision {{ currentAcceptedNumber }} is now the
				current accepted revision of this need.
			</div>
		</div>

		<div v-if="editAction" class="kt-notice is-warning" style="margin-top: var(--kt-space-4)" data-testid="nds-detail-editable">
			<div class="kt-notice-body">
				<template v-if="isReturned && latestReturn">
					<strong>What needs to change</strong><br />
					{{ latestReturn.reason }}
					<div style="display: flex; gap: var(--kt-space-6); margin-top: var(--kt-space-3); font-size: 12px">
						<div><strong style="color: var(--kt-color-text)">Returned by</strong> {{ latestReturn.actor_label }}</div>
						<div><strong style="color: var(--kt-color-text)">Returned at</strong> {{ latestReturn.occurred_label }}</div>
					</div>
				</template>
				<template v-else>This need has not been submitted for departmental review yet.</template>
			</div>
			<button class="kt-btn kt-btn-primary" style="margin-top: var(--kt-space-3)" data-testid="nds-detail-edit" @click="$emit('edit')">
				{{ editAction.label }}
			</button>
		</div>

		<div v-if="need.current_state === 'Submitted'" class="kt-notice is-info" style="margin-top: var(--kt-space-4)">
			<div class="kt-notice-body">
				Your requirement has been submitted. The details cannot be edited while it is
				under review.
			</div>
		</div>
		<div v-if="reviewAction" style="margin-top: var(--kt-space-3)">
			<button class="kt-btn kt-btn-primary" data-testid="nds-detail-review" @click="$emit('review', reviewAction)">
				{{ reviewAction.label }}
			</button>
		</div>

		<div v-if="openSuccessor" class="kt-notice is-info" style="margin-top: var(--kt-space-4)">
			<div class="kt-notice-body">
				The accepted revision below stays current until the update is accepted.
				<a v-if="canOpenSuccessor" href="#" style="margin-left: 8px" @click.prevent="$emit('open-successor')">Open update</a>
			</div>
		</div>

		<div class="kt-panel" style="margin: var(--kt-space-4) 0">
			<div class="kt-meta-row">
				<div v-for="fact in contextItems" :key="fact.label">
					<span class="kt-label">{{ fact.label }}</span>
					<span class="kt-meta-value" style="font-size: 14px">{{ fact.value }}</span>
				</div>
			</div>
		</div>

		<!-- §11.8 Planning status — two rows, Departmental plan (disposition) and
		     Current annual plan (usage); never merged into one status. -->
		<template v-if="showPlanning">
			<h6 class="kt-card-title">Planning status</h6>
			<div style="display: flex; flex-direction: column; gap: var(--kt-space-3); margin-top: var(--kt-space-4)">
				<div style="font-size: 13px">
					<span class="kt-label" style="display: block">Departmental plan</span>
					<span class="kt-status" :class="departmentalPlanStatus.cls">{{ departmentalPlanStatus.label }}</span>
				</div>
				<div style="font-size: 13px">
					<span class="kt-label" style="display: block">Current annual plan</span>
					<span class="kt-status" :class="annualPlanStatus.cls">{{ annualPlanStatus.label }}</span>
				</div>
			</div>
			<!-- NDS-DES-07A STILL-ACTIVE — a not-proceeding departmental
			     disposition with the requirement still Fully included blocks
			     withdrawal until Planning clears it. -->
			<div v-if="stillActive" class="kt-notice is-warning" style="margin-top: var(--kt-space-2)">
				<div class="kt-notice-body" style="font-size: 12px">
					The annual plan has not yet been updated. Withdrawal cannot be approved while
					this requirement remains included.
				</div>
			</div>
			<div class="text-muted" style="font-size: 12px; margin: var(--kt-space-3) 0 var(--kt-space-6)">
				These statuses do not confirm that the requirement has been purchased or delivered.
			</div>
		</template>

		<RequirementCard :revision="shownRevision" />

		<div
			v-if="showPlanning && planningHistory.length"
			class="kt-disclosure"
			style="margin-top: var(--kt-space-4)"
		>
			<div class="kt-disclosure-head" @click="planningHistoryOpen = !planningHistoryOpen">
				<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">Planning decisions and history</span></div>
				<svg
					class="kt-disclosure-chevron"
					:class="{ 'is-open': planningHistoryOpen }"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
				><path d="M6 9l6 6 6-6" /></svg>
			</div>
			<div v-if="planningHistoryOpen" class="kt-disclosure-body">
				<div class="kt-timeline">
					<div v-for="(item, index) in planningHistory" :key="index" class="kt-timeline-row">
						<div class="kt-timeline-dot-col">
							<i class="kt-timeline-dot" :class="item.dotClass"></i>
							<i v-if="index < planningHistory.length - 1" class="kt-timeline-line"></i>
						</div>
						<div class="kt-timeline-item">
							<div class="kt-timeline-item-title">{{ item.title }}</div>
							<div class="kt-timeline-item-meta">{{ item.meta }}</div>
							<div v-if="item.meta2" class="kt-timeline-item-meta">{{ item.meta2 }}</div>
							<button
								v-if="item.action"
								type="button"
								class="kt-action-link"
								style="font-size: 12px"
								@click="$emit(item.action)"
							>
								{{ item.actionLabel }}
							</button>
						</div>
					</div>
				</div>
			</div>
		</div>

		<div v-else-if="!showPlanning && history.length" class="kt-disclosure" style="margin-top: var(--kt-space-4)">
			<div class="kt-disclosure-head" @click="planningHistoryOpen = !planningHistoryOpen">
				<div class="kt-disclosure-title-row"><span class="kt-disclosure-title">History</span></div>
				<svg
					class="kt-disclosure-chevron"
					:class="{ 'is-open': planningHistoryOpen }"
					width="16"
					height="16"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
					stroke-width="1.5"
				><path d="M6 9l6 6 6-6" /></svg>
			</div>
			<div v-if="planningHistoryOpen" class="kt-disclosure-body">
				<div class="kt-timeline">
					<div v-for="(item, index) in history" :key="index" class="kt-timeline-row">
						<div class="kt-timeline-dot-col">
							<i class="kt-timeline-dot" :class="item.dot_class"></i>
							<i v-if="index < history.length - 1" class="kt-timeline-line"></i>
						</div>
						<div class="kt-timeline-item">
							<div class="kt-timeline-item-title">{{ item.title }}</div>
							<div class="kt-timeline-item-meta">{{ item.meta }}</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref } from "vue";
import RequirementCard from "./RequirementCard.vue";
import { formatInstant } from "../data/format.js";

const props = defineProps({
	need: { type: Object, default: () => ({}) },
	scopeLabels: { type: Object, default: () => ({}) },
	revision: { type: Object, default: () => ({}) },
	acceptedRevision: { type: Object, default: () => ({}) },
	usage: { type: Object, default: () => ({}) },
	// get_departmental_need().planning_disposition — Planning information only.
	disposition: { type: Object, default: null },
	authorLabel: { type: String, default: "" },
	accessProfile: { type: String, default: "" },
	actions: { type: Array, default: () => [] },
	latestReturn: { type: Object, default: null },
	acceptedByLabel: { type: String, default: "" },
	acceptedAt: { type: String, default: "" },
	acceptedCapacity: { type: String, default: "" },
	submittedAt: { type: String, default: "" },
	withdrawalOpen: Boolean,
	pinnedRevision: { type: Object, default: null },
	history: { type: Array, default: () => [] },
});
defineEmits(["create-update", "request-withdrawal", "view-plan-item", "open-successor", "edit", "review"]);

const planningHistoryOpen = ref(false);

const isReturned = computed(() => props.need.current_state === "Returned");
const isAccepted = computed(() => props.need.current_state === "Accepted for planning");
const editAction = computed(() => (props.actions || []).find((a) => a.code === "edit") || null);
const reviewAction = computed(
	() => (props.actions || []).find((a) => a.code === "review" || a.code === "withdrawal") || null
);

const shownRevision = computed(
	() => props.pinnedRevision || (props.acceptedRevision?.name && props.acceptedRevision) || props.revision || {}
);

const isHistoricalRevision = computed(
	() =>
		!!props.pinnedRevision &&
		!!props.acceptedRevision?.name &&
		props.pinnedRevision.name !== props.acceptedRevision.name
);

const currentAcceptedNumber = computed(() => props.acceptedRevision?.revision_number || "");

const STATUS_LABELS = {
	Draft: ["is-draft", "Draft"],
	Submitted: ["is-pending", "Awaiting Head of Department review"],
	Returned: ["is-attention", "Changes requested"],
	"Accepted for planning": ["is-live", "Accepted for planning"],
	"Not taken forward": ["is-critical", "Not taken forward"],
	Withdrawn: ["is-critical", "Withdrawn"],
};
const statusClass = computed(() => STATUS_LABELS[props.need.current_state]?.[0] || "is-draft");
const statusLabel = computed(() => STATUS_LABELS[props.need.current_state]?.[1] || props.need.current_state || "");

const openSuccessor = computed(
	() =>
		isAccepted.value &&
		props.need.current_revision &&
		props.need.current_accepted_revision &&
		props.need.current_revision !== props.need.current_accepted_revision
);

const canOpenSuccessor = computed(() => props.accessProfile === "owner");

const ownerActions = computed(() => {
	if (props.accessProfile !== "owner" || !isAccepted.value || isHistoricalRevision.value) return [];
	const available = [];
	if (!openSuccessor.value) available.push({ code: "create-update", label: "Create update" });
	// NDS-DES-11-OPEN-UPDATE — an open successor and an open withdrawal
	// request are mutually exclusive (§5.3); Request withdrawal is absent
	// while an update is already in progress, not just while one is open.
	if (!props.withdrawalOpen && !openSuccessor.value)
		available.push({ code: "request-withdrawal", label: "Request withdrawal" });
	return available;
});

const showPlanning = computed(() => isAccepted.value);

// §11.8/§11.8A — Departmental plan reads the accepted DPP disposition;
// Current annual plan reads Active usage. The two are independent facts,
// never merged into one status.
const departmentalPlanStatus = computed(() => {
	if (!props.disposition?.recorded) return { cls: "is-pending", label: "No accepted decision recorded" };
	return props.disposition.disposition === "Not proceeding"
		? { cls: "is-attention", label: "Not included this year" }
		: { cls: "is-live", label: "Included" };
});
const annualPlanStatus = computed(() => {
	if (props.usage?.usage !== "Fully included") return { cls: "is-pending", label: "Not included" };
	// STILL-ACTIVE — a not-proceeding departmental disposition, but the
	// requirement remains represented in the current annual plan.
	return stillActive.value ? { cls: "is-live", label: "Still included" } : { cls: "is-live", label: "Included" };
});
const stillActive = computed(
	() => props.disposition?.recorded && props.disposition.disposition === "Not proceeding" && props.usage?.usage === "Fully included"
);

const planningHistory = computed(() => {
	const items = [];
	for (const row of props.disposition?.history || []) {
		items.push({
			title: "Departmental decision",
			meta: `Requirement revision ${(row.need_revision || "").split("-V").pop()?.replace(/^0+/, "") || ""} · ${row.dpp_submission || ""}`,
			meta2: row.actor_label || row.decision_at ? `Accepted by Procurement${row.actor_label ? " " + row.actor_label : ""}${row.decision_at ? " · " + formatInstant(row.decision_at) : ""}` : "",
			dotClass: row.disposition === "Not proceeding" ? "is-attention" : "is-live",
		});
	}
	if (props.usage?.active_plan_item) {
		items.push({
			title: "Annual plan",
			meta: props.usage.active_plan || "",
			meta2: props.usage.active_plan_item || "",
			dotClass: "is-live",
			action: "view-plan-item",
			actionLabel: "View annual plan item",
		});
	}
	return items;
});

function label(field) {
	return props.scopeLabels[field] || props.need[field] || "";
}

const contextItems = computed(() => {
	if (isAccepted.value) {
		const facts = [
			{ label: "Department", value: label("organisation_unit") },
			{ label: "Financial year", value: label("financial_year") },
			{ label: "Accepted by", value: props.acceptedByLabel || props.authorLabel },
		];
		// §11.8 "Capacity" — omitted, not shown blank, when the accepting
		// assignment predates §15 snapshotting or has since been removed.
		if (props.acceptedCapacity) facts.push({ label: "Capacity", value: props.acceptedCapacity });
		facts.push({ label: "Accepted at", value: formatInstant(props.acceptedAt) });
		return facts;
	}
	const facts = [
		{ label: "Department", value: label("organisation_unit") },
		{ label: "Financial year", value: label("financial_year") },
		{ label: "Submitted by", value: props.authorLabel },
	];
	if (props.submittedAt) facts.push({ label: "Submitted at", value: formatInstant(props.submittedAt) });
	return facts;
});
</script>
