<!-- NDS-UI-04 / NDS-UI-06 need detail (§12.4) — NDS-DES-05 submitted,
     NDS-DES-07 accepted. The screen shows the exact version it was asked for
     and never rewrites the requested one. -->
<template>
	<div>
		<div style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 20px">
			<div>
				<div class="kt-page-kicker" style="letter-spacing: 0.06em">{{ kicker }}</div>
				<div style="display: flex; align-items: center; gap: 12px; margin-top: 4px">
					<h1 class="kt-record-title">{{ shownVersion.title }}</h1>
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
					@click="$emit(action.code)"
				>
					{{ action.label }}
				</button>
			</div>
		</div>

		<!-- §12.4 — a superseded accepted version stays readable and says so. -->
		<div
			v-if="isHistoricalVersion"
			class="kt-card kt-blueprint"
			style="margin-bottom: 16px; padding: 18px 24px"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title" style="margin-bottom: 8px">This version has been superseded</div>
			<p style="margin: 0; font-size: 14.5px">
				Version {{ currentAcceptedNumber }} is now the current accepted version of this
				need.
			</p>
		</div>

		<div
			v-if="need.current_state === 'Submitted'"
			class="kt-card kt-blueprint"
			style="margin-bottom: 16px; padding: 18px 24px"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-card-title" style="margin-bottom: 8px">Awaiting departmental review</div>
			<p style="margin: 0 0 8px; font-size: 14.5px">
				This version is read-only while it is in the department review queue.
			</p>
			<div style="font-size: 13px; color: var(--color-neutral-600)">
				Submitted by {{ authorLabel }}
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
						The accepted version below stays current until the update is accepted.
					</p>
				</div>
				<button
					v-if="canOpenSuccessor"
					class="kt-btn kt-btn-secondary"
					@click="$emit('open-successor')"
				>
					Open update
				</button>
			</div>
		</div>

		<ContextCard :items="contextItems" />
		<RequirementCard :version="shownVersion" />

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
				<button class="kt-btn kt-btn-secondary" @click="$emit('view-plan-item')">
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
import { formatInstant, versionKicker } from "../data/format.js";

const props = defineProps({
	need: { type: Object, default: () => ({}) },
	scopeLabels: { type: Object, default: () => ({}) },
	version: { type: Object, default: () => ({}) },
	acceptedVersion: { type: Object, default: () => ({}) },
	usage: { type: Object, default: () => ({}) },
	authorLabel: { type: String, default: "" },
	accessProfile: { type: String, default: "" },
	acceptedByLabel: { type: String, default: "" },
	acceptedAt: { type: String, default: "" },
	// True while a withdrawal request is already open, which removes the
	// Request withdrawal action (§12.4).
	withdrawalOpen: Boolean,
	// NDS-UI-06 pins an exact version in the route; NDS-UI-04 does not.
	pinnedVersion: { type: Object, default: null },
});
defineEmits(["create-update", "request-withdrawal", "view-plan-item", "open-successor"]);

const shownVersion = computed(
	() => props.pinnedVersion || props.acceptedVersion?.name && props.acceptedVersion || props.version || {}
);

const isHistoricalVersion = computed(
	() =>
		!!props.pinnedVersion &&
		!!props.acceptedVersion?.name &&
		props.pinnedVersion.name !== props.acceptedVersion.name
);

const currentAcceptedNumber = computed(() => props.acceptedVersion?.version_number || "");

const kicker = computed(() =>
	versionKicker(props.need.need_reference, shownVersion.value, isAccepted.value ? "" : "")
		.replace("VERSION", isAccepted.value ? "ACCEPTED VERSION" : "VERSION")
);

const isAccepted = computed(() => props.need.current_state === "Accepted for planning");

const openSuccessor = computed(
	() =>
		isAccepted.value &&
		props.need.current_version &&
		props.need.current_accepted_version &&
		props.need.current_version !== props.need.current_accepted_version
);

const canOpenSuccessor = computed(() => props.accessProfile === "owner");

const ownerActions = computed(() => {
	if (props.accessProfile !== "owner" || !isAccepted.value || isHistoricalVersion.value) return [];
	const available = [];
	if (!openSuccessor.value) available.push({ code: "create-update", label: "Create update" });
	if (!props.withdrawalOpen)
		available.push({ code: "request-withdrawal", label: "Request withdrawal" });
	return available;
});

const showPlanning = computed(() => isAccepted.value);

const planningMessage = computed(() =>
	props.usage?.usage === "Fully included"
		? "This accepted version is included in the Active Annual Procurement Plan."
		: "This accepted version is not represented in an Active Plan."
);

function label(field) {
	return props.scopeLabels[field] || props.need[field] || "";
}

const contextItems = computed(() => {
	if (isAccepted.value) {
		return [
			{ label: "Accepted by", value: props.acceptedByLabel || props.authorLabel },
			{ label: "Accepted", value: formatInstant(props.acceptedAt) },
			{ label: "Department", value: label("organisation_unit") },
			{ label: "Financial Year", value: label("financial_year") },
		];
	}
	return [
		{ label: "Procuring Entity", value: label("procuring_entity") },
		{ label: "Department", value: label("organisation_unit") },
		{ label: "Financial Year", value: label("financial_year") },
	];
});
</script>
