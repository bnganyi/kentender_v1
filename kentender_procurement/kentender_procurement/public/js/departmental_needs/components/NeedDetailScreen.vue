<!-- NDS-UI-04 / NDS-UI-06 need detail (§12.4) — NDS-DES-05 submitted,
     NDS-DES-07 accepted. The screen shows the exact revision it was asked for
     and never rewrites the requested one. -->
<template>
	<div>
		<div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px">
			<div>
				<div class="kt-page-kicker" style="letter-spacing: 0.06em">{{ kicker }}</div>
				<div style="display: flex; align-items: center; gap: 12px; margin-top: 4px">
					<h1 class="kt-record-title">{{ shownRevision.title }}</h1>
					<StatusPill :label="need.current_state || ''" />
				</div>
			</div>
			<!-- §12.4 — both actions belong to the originator, on an accepted Need
			     with nothing already open. The server decides; the page only
			     renders what it was told. -->
			<div v-if="ownerActions.length" style="display: flex; gap: 12px; flex: none; margin-top: 6px">
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

		<!-- §12.4 — a superseded accepted revision stays readable and says so. -->
		<div
			v-if="isHistoricalRevision"
			class="kt-card kt-blueprint"
			style="margin-bottom: 16px; padding: 18px 24px"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title" style="margin-bottom: 8px">This revision has been superseded</div>
			<p style="margin: 0; font-size: 14.5px">
				Revision {{ currentAcceptedNumber }} is now the current accepted revision of this
				need.
			</p>
		</div>

		<!-- §12.1 — "Continue and Correct route to the actor's editable current
		     revision." The detail route is where the return notification and
		     the row's View land, so the author's own editable Draft/Returned
		     Need offers that route here too; the server decides (actions
		     carries `edit` only for the owner), the screen only renders it. -->
		<div
			v-if="editAction"
			class="kt-card kt-blueprint"
			style="margin-bottom: 16px; padding: 18px 24px"
			data-testid="nds-detail-editable"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px">
				<div>
					<div class="kt-card-title" style="margin-bottom: 8px">
						{{ isReturned ? "Returned for correction" : "Draft in progress" }}
					</div>
					<p v-if="isReturned && latestReturn" style="margin: 0 0 8px; font-size: 14.5px">
						{{ latestReturn.reason }}
					</p>
					<p v-else-if="!isReturned" style="margin: 0; font-size: 14.5px">
						This need has not been submitted for departmental review yet.
					</p>
					<div v-if="isReturned && latestReturn" style="font-size: 13px; color: var(--color-neutral-600)">
						Returned by {{ latestReturn.actor_label }} · {{ latestReturn.occurred_label }}
					</div>
				</div>
				<button
					class="kt-btn kt-btn-primary"
					style="flex: none"
					data-testid="nds-detail-edit"
					@click="$emit('edit')"
				>
					{{ editAction.label }}
				</button>
			</div>
		</div>

		<div
			v-if="need.current_state === 'Submitted'"
			class="kt-card kt-blueprint"
			style="margin-bottom: 16px; padding: 18px 24px"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div style="display: flex; align-items: center; justify-content: space-between; gap: 16px">
				<div>
					<div class="kt-card-title" style="margin-bottom: 8px">Awaiting departmental review</div>
					<p style="margin: 0 0 8px; font-size: 14.5px">
						This revision is read-only while it is in the department review queue.
					</p>
					<div style="font-size: 13px; color: var(--color-neutral-600)">
						Submitted by {{ authorLabel }}
					</div>
				</div>
				<!-- §12.2 — the reviewer's decision lives on the task screen (NDS-UI-05);
				     the server offers `review` only to the department reviewer who
				     is not the author, so the detail route is never a dead end for
				     the one person who has to act on it. -->
				<button
					v-if="reviewAction"
					class="kt-btn kt-btn-primary"
					style="flex: none"
					data-testid="nds-detail-review"
					@click="$emit('review', reviewAction)"
				>
					{{ reviewAction.label }}
				</button>
			</div>
		</div>

		<!-- §12.4 — an open successor is a status notice; the link is the
		     maker's only. -->
		<div
			v-if="openSuccessor"
			class="kt-card kt-blueprint"
			style="margin-bottom: 16px; padding: 18px 24px"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div style="display: flex; align-items: center; justify-content: space-between">
				<div>
					<div class="kt-card-title" style="margin-bottom: 8px">An update is open</div>
					<p style="margin: 0; font-size: 14.5px">
						The accepted revision below stays current until the update is accepted.
					</p>
				</div>
				<button
					v-if="canOpenSuccessor"
					class="kt-btn kt-btn-secondary"
					data-testid="nds-open-successor"
					@click="$emit('open-successor')"
				>
					Open update
				</button>
			</div>
		</div>

		<ContextCard :items="contextItems" />
		<RequirementCard :revision="shownRevision" />

		<!-- §12.4 — Planning usage, with View Plan Item absent when not included. -->
		<div v-if="showPlanning" class="kt-card kt-blueprint" style="padding: 20px 24px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px">
				<div class="kt-card-title" style="margin-bottom: 0">Procurement Planning</div>
				<StatusPill :label="usage.usage || 'Not included'" />
			</div>
			<p style="margin: 0 0 10px; font-size: 14.5px">{{ planningMessage }}</p>
			<div
				v-if="usage.active_plan_item"
				style="display: flex; align-items: center; justify-content: space-between"
			>
				<div style="font-size: 14px; color: var(--color-neutral-700)">
					{{ usage.active_plan_item }}
				</div>
				<button class="kt-btn kt-btn-secondary" data-testid="nds-view-plan-item" @click="$emit('view-plan-item')">
					View Plan Item
				</button>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import ContextCard from "./ContextCard.vue";
import RequirementCard from "./RequirementCard.vue";
import StatusPill from "./StatusPill.vue";
import { formatInstant, revisionKicker } from "../data/format.js";

const props = defineProps({
	need: { type: Object, default: () => ({}) },
	scopeLabels: { type: Object, default: () => ({}) },
	revision: { type: Object, default: () => ({}) },
	acceptedRevision: { type: Object, default: () => ({}) },
	usage: { type: Object, default: () => ({}) },
	authorLabel: { type: String, default: "" },
	accessProfile: { type: String, default: "" },
	// get_departmental_need().actions — the server's own list; `edit` is
	// present only for the owner of a Draft/Returned Need.
	actions: { type: Array, default: () => [] },
	latestReturn: { type: Object, default: null },
	acceptedByLabel: { type: String, default: "" },
	acceptedAt: { type: String, default: "" },
	// True while a withdrawal request is already open, which removes the
	// Request withdrawal action (§12.4).
	withdrawalOpen: Boolean,
	// NDS-UI-06 pins an exact revision in the route; NDS-UI-04 does not.
	pinnedRevision: { type: Object, default: null },
});
defineEmits(["create-update", "request-withdrawal", "view-plan-item", "open-successor", "edit", "review"]);

const isReturned = computed(() => props.need.current_state === "Returned");
const editAction = computed(() => (props.actions || []).find((a) => a.code === "edit") || null);
const reviewAction = computed(
	() => (props.actions || []).find((a) => a.code === "review" || a.code === "withdrawal") || null
);

const shownRevision = computed(
	() => props.pinnedRevision || props.acceptedRevision?.name && props.acceptedRevision || props.revision || {}
);

const isHistoricalRevision = computed(
	() =>
		!!props.pinnedRevision &&
		!!props.acceptedRevision?.name &&
		props.pinnedRevision.name !== props.acceptedRevision.name
);

const currentAcceptedNumber = computed(() => props.acceptedRevision?.revision_number || "");

const kicker = computed(() =>
	revisionKicker(props.need.need_reference, shownRevision.value, isAccepted.value ? "" : "")
		.replace("REVISION", isAccepted.value ? "ACCEPTED REVISION" : "REVISION")
);

const isAccepted = computed(() => props.need.current_state === "Accepted for planning");

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
	if (!props.withdrawalOpen)
		available.push({ code: "request-withdrawal", label: "Request withdrawal" });
	return available;
});

const showPlanning = computed(() => isAccepted.value);

const planningMessage = computed(() =>
	props.usage?.usage === "Fully included"
		? "This accepted revision is included in the Active Annual Procurement Plan."
		: "This accepted revision is not represented in an Active Plan."
);

function label(field) {
	return props.scopeLabels[field] || props.need[field] || "";
}

const contextItems = computed(() => {
	if (isAccepted.value) {
		return [
			{ label: "Requested by", value: props.authorLabel },
			{ label: "Accepted by", value: props.acceptedByLabel || props.authorLabel },
			{ label: "Accepted", value: formatInstant(props.acceptedAt) },
			{ label: "Department", value: label("organisation_unit") },
			{ label: "Financial Year", value: label("financial_year") },
		];
	}
	// "Requested by" keeps authorship visible to a reviewer opening a Draft or
	// Returned record from the departmental register (§6 view scope).
	return [
		{ label: "Requested by", value: props.authorLabel },
		{ label: "Department", value: label("organisation_unit") },
		{ label: "Financial Year", value: label("financial_year") },
	];
});
</script>
