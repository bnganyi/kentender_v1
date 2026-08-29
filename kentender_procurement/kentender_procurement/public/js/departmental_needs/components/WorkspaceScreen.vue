<!-- NDS-UI-01 requester workspace (§12.1), rendering NDS-DES-01 and all five
     NDS-DES-14 states with their exact copy. -->
<template>
	<div>
		<!-- Masthead: present in every state, so the page never blanks. -->
		<div
			style="display: flex; align-items: flex-start; justify-content: space-between; margin-bottom: 24px"
		>
			<div>
				<div class="kt-page-kicker">DEPARTMENTAL NEEDS</div>
				<h1 class="kt-page-title">My needs</h1>
				<p class="kt-page-lede">
					Capture and track the requirements your department expects to include in
					procurement planning.
				</p>
			</div>
			<!-- §12.1 — Create need exists only while intake is Open. -->
			<button
				v-if="canCreate"
				class="kt-btn kt-btn-primary"
				@click="$emit('create')"
			>
				Create need
			</button>
		</div>

		<!-- NDS-DES-14a loading -->
		<div v-if="loading" class="kt-card kt-blueprint" style="padding: 0; overflow: hidden">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div v-for="row in 3" :key="row" class="kt-skel-row">
				<div class="kt-skel" style="width: 78%"></div>
				<div class="kt-skel" style="width: 56%"></div>
				<div class="kt-skel" style="width: 56%"></div>
				<div class="kt-skel" style="width: 56%"></div>
				<div class="kt-skel" style="width: 56%"></div>
				<div class="kt-skel" style="width: 46%"></div>
			</div>
		</div>

		<!-- NDS-DES-14e error -->
		<div
			v-else-if="error"
			class="kt-card kt-blueprint"
			style="padding: 64px 24px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div style="font-family: var(--font-heading); font-size: 22px; font-weight: 600">
				Departmental Needs could not be loaded
			</div>
			<p
				style="margin: 0 0 8px; font-size: 14.5px; color: var(--color-neutral-700); max-width: 420px"
			>
				Try again. If the problem continues, contact support.
			</p>
			<button class="kt-btn kt-btn-secondary" @click="$emit('reload')">Try again</button>
		</div>

		<!-- NDS-DES-14d no authorised context -->
		<div
			v-else-if="outcome === 'NO_AUTHORISED_CONTEXT'"
			class="kt-card kt-blueprint"
			style="padding: 64px 24px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div style="font-family: var(--font-heading); font-size: 22px; font-weight: 600">
				Departmental Needs is not available
			</div>
			<p
				style="margin: 0; font-size: 14.5px; color: var(--color-neutral-700); max-width: 460px"
			>
				You do not have an active Departmental Needs assignment for a configured Procuring
				Entity, department and Financial Year.
			</p>
		</div>

		<template v-else>
			<ContextCard :items="contextItems" />

			<!-- §12.1 — search matches title or reference; status is the only filter. -->
			<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px">
				<div class="kt-field" style="flex: 1; max-width: 360px; margin: 0">
					<label class="sr-only" for="nds-search">Search title or reference</label>
					<input
						id="nds-search"
						class="kt-input"
						type="text"
						placeholder="Search title or reference"
						:value="search"
						@input="$emit('update:search', $event.target.value)"
					/>
				</div>
				<div class="kt-field" style="width: 200px; margin: 0">
					<label class="sr-only" for="nds-status">Status</label>
					<select
						id="nds-status"
						class="kt-input"
						:value="status"
						@change="$emit('update:status', $event.target.value)"
					>
						<option value="">All statuses</option>
						<option v-for="option in STATUSES" :key="option" :value="option">
							{{ option }}
						</option>
					</select>
				</div>
				<button class="kt-btn kt-btn-secondary" @click="$emit('clear-filters')">
					Clear filters
				</button>
			</div>

			<!-- NDS-DES-14b empty -->
			<div
				v-if="!needs.length"
				class="kt-card kt-blueprint"
				style="padding: 64px 24px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px"
			>
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div style="font-family: var(--font-heading); font-size: 22px; font-weight: 600">
					No departmental needs yet
				</div>
				<p
					style="margin: 0 0 8px; font-size: 14.5px; color: var(--color-neutral-700); max-width: 420px"
				>
					Create the first need for this department and Financial Year.
				</p>
				<button
					v-if="canCreate"
					class="kt-btn kt-btn-primary"
					@click="$emit('create')"
				>
					Create need
				</button>
			</div>

			<NeedsTable
				v-else
				:needs="needs"
				:columns="columns"
				@action="(row, action) => $emit('action', row, action)"
			/>

			<div v-if="needs.length" style="margin-top: 12px; font-size: 13px; color: var(--color-neutral-600)">
				{{ countLabel }}
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";
import ContextCard from "./ContextCard.vue";
import NeedsTable from "./NeedsTable.vue";
import { formatInstant } from "../data/format.js";

const props = defineProps({
	loading: Boolean,
	error: { type: String, default: "" },
	outcome: { type: String, default: "" },
	context: { type: Object, default: () => ({}) },
	intake: { type: Object, default: () => ({}) },
	needs: { type: Array, default: () => [] },
	countLabel: { type: String, default: "" },
	search: { type: String, default: "" },
	status: { type: String, default: "" },
});

defineEmits(["create", "reload", "action", "update:search", "update:status", "clear-filters"]);

const STATUSES = [
	"Draft",
	"Submitted",
	"Returned",
	"Accepted for planning",
	"Not taken forward",
];

const columns = [
	{ key: "need", label: "Need" },
	{ key: "quantity_label", label: "Quantity", align: "right" },
	{ key: "required_by_label", label: "Required by" },
	{ key: "status", label: "Status", status: true },
	{ key: "planning_usage", label: "Planning usage", status: true },
	{ key: "action", label: "Action", align: "right" },
];

const canCreate = computed(() => props.intake && props.intake.state === "Open");

const contextItems = computed(() => [
	{ label: "Procuring Entity", value: props.context.procuring_entity_label || props.context.procuring_entity || "" },
	{ label: "Department", value: props.context.organisation_unit_label || props.context.organisation_unit || "" },
	{ label: "Financial Year", value: props.context.financial_year_label || props.context.financial_year || "" },
	{ label: "Intake window", value: intakeLabel.value },
]);

// NDS-DES-14c — intake closed still shows existing records; only the label and
// the missing Create button say so (§12.1).
const intakeLabel = computed(() => {
	const window = props.intake || {};
	if (window.state === "Open") return `Open until ${formatInstant(window.closes_at)}`;
	if (window.state === "Scheduled") return `Opens ${formatInstant(window.opens_at)}`;
	if (window.state === "Closed") return `Closed ${formatInstant(window.closes_at)}`;
	return "Not configured";
});
</script>
