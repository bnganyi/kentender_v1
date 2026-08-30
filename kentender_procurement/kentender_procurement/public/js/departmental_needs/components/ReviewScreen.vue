<!-- NDS-UI-02 department review (§12.2) — NDS-DES-02 review queue and
     NDS-DES-02b department needs, two tabs over the same PE/OU/FY scope. -->
<template>
	<div>
		<div style="margin-bottom: 24px">
			<div class="kt-page-kicker">DEPARTMENTAL NEEDS</div>
			<h1 class="kt-page-title">Department review</h1>
			<p class="kt-page-lede">
				Review submitted needs and view the department's current needs.
			</p>
		</div>

		<div v-if="error" class="kt-error-summary" role="alert">{{ error }}</div>

		<!-- CTX-CHG-001 rule 4 — the reviewer's band also keeps the department
		     changeable and the Financial Year a live selector. -->
		<div class="kt-card kt-blueprint" style="margin-bottom: 16px; padding: 20px 24px">
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div class="kt-context-grid" style="grid-template-columns: repeat(3, 1fr)">
				<div class="kt-readonly-row">
					<div class="kt-readonly-label">Procuring Entity</div>
					<div class="kt-readonly-value is-strong">
						{{ context.procuring_entity_label || context.procuring_entity || "" }}
					</div>
				</div>
				<div class="kt-readonly-row">
					<div class="kt-readonly-label">
						Department
						<button
							type="button"
							class="kt-action-link"
							data-testid="nds-change-context"
							style="border: 0; background: none; padding: 0; margin-left: 8px; cursor: pointer; text-transform: none; letter-spacing: normal; font-size: 11.5px"
							@click="$emit('change-context')"
						>
							Change
						</button>
					</div>
					<div class="kt-readonly-value is-strong">
						{{ context.organisation_unit_label || context.organisation_unit || "" }}
					</div>
				</div>
				<div class="kt-readonly-row">
					<div class="kt-readonly-label">
						<label for="nds-review-fy-band">Financial Year</label>
					</div>
					<select
						id="nds-review-fy-band"
						class="kt-input"
						data-testid="nds-fy-band-select"
						style="max-width: 180px; padding: 6px 8px; font-size: 13.5px"
						:value="context.financial_year || ''"
						@change="$emit('select-financial-year', $event.target.value)"
					>
						<option v-if="!context.financial_year" value="" disabled>Select year…</option>
						<option v-for="year in financialYears" :key="year.id" :value="year.id">
							{{ year.label }}
						</option>
					</select>
				</div>
			</div>
		</div>

		<div class="kt-tabstrip" role="tablist">
			<button
				v-for="option in TABS"
				:key="option.key"
				class="kt-tab"
				data-testid="nds-review-tab"
				:data-tab="option.key"
				:class="{ 'is-selected': tab === option.key }"
				role="tab"
				:aria-selected="tab === option.key"
				@click="$emit('update:tab', option.key)"
			>
				{{ option.label }}
			</button>
		</div>

		<!-- The register tab carries the same filters as the workspace; the
		     queue is a task list and has none (§12.2). -->
		<div
			v-if="tab === 'register'"
			style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px"
		>
			<div class="kt-field" style="flex: 1; max-width: 360px; margin: 0">
				<label class="sr-only" for="nds-review-search">Search title or reference</label>
				<input
					id="nds-review-search"
					class="kt-input"
					type="text"
					placeholder="Search title or reference"
					:value="search"
					@input="$emit('update:search', $event.target.value)"
				/>
			</div>
			<div class="kt-field" style="width: 200px; margin: 0">
				<label class="sr-only" for="nds-review-status">Status</label>
				<select
					id="nds-review-status"
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

		<div
			v-if="loading"
			class="kt-card kt-blueprint"
			style="padding: 0; overflow: hidden"
		>
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

		<div
			v-else-if="!rows.length"
			class="kt-card kt-blueprint"
			style="padding: 64px 24px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 8px"
		>
			<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
			<i class="kt-corner bl"></i><i class="kt-corner br"></i>
			<div style="font-family: var(--font-heading); font-size: 22px; font-weight: 600">
				{{ tab === "queue" ? "Nothing awaiting review" : "No departmental needs yet" }}
			</div>
			<p style="margin: 0; font-size: 14.5px; color: var(--color-neutral-700); max-width: 420px">
				{{
					tab === "queue"
						? "Submitted needs for this department will appear here."
						: "Needs created for this department and Financial Year will appear here."
				}}
			</p>
		</div>

		<NeedsTable v-else :needs="rows" :columns="columns" @action="(row, a) => $emit('action', row, a)" />

		<div v-if="rows.length" style="margin-top: 12px; font-size: 13px; color: var(--color-neutral-600)">
			{{ countLabel }}
		</div>
	</div>
</template>

<script setup>
import { computed } from "vue";
import NeedsTable from "./NeedsTable.vue";

const props = defineProps({
	tab: { type: String, default: "queue" },
	loading: Boolean,
	error: { type: String, default: "" },
	context: { type: Object, default: () => ({}) },
	rows: { type: Array, default: () => [] },
	search: { type: String, default: "" },
	status: { type: String, default: "" },
	financialYears: { type: Array, default: () => [] },
});
defineEmits([
	"update:tab",
	"update:search",
	"update:status",
	"clear-filters",
	"action",
	"select-financial-year",
	"change-context",
]);

const TABS = [
	{ key: "queue", label: "Review queue" },
	{ key: "register", label: "Department needs" },
];

const STATUSES = [
	"Draft",
	"Submitted",
	"Returned",
	"Accepted for planning",
	"Not taken forward",
];

const QUEUE_COLUMNS = [
	{ key: "need", label: "Need" },
	{ key: "author_label", label: "Submitted by" },
	{ key: "quantity_label", label: "Quantity", align: "right" },
	{ key: "required_by_label", label: "Required by" },
	{ key: "status", label: "Status", status: true },
	{ key: "action", label: "Action", align: "right" },
];

const REGISTER_COLUMNS = [
	{ key: "need", label: "Need" },
	{ key: "author_label", label: "Requester" },
	{ key: "quantity_label", label: "Quantity", align: "right" },
	{ key: "required_by_label", label: "Required by" },
	{ key: "status", label: "Status", status: true },
	{ key: "planning_usage", label: "Planning usage", status: true },
	{ key: "action", label: "Action", align: "right" },
];

const columns = computed(() => (props.tab === "queue" ? QUEUE_COLUMNS : REGISTER_COLUMNS));

const countLabel = computed(() => {
	const count = props.rows.length;
	if (props.tab === "queue") {
		return count === 1 ? "1 need awaiting review" : `${count} needs awaiting review`;
	}
	return count === 1 ? "1 department need" : `${count} department needs`;
});

</script>
