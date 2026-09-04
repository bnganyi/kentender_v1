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
				data-testid="nds-create-need"
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
			<!-- §12.1 — the band shows the selected department (with Change
			     context), a CHANGEABLE Financial Year, and the Needs-submission
			     state with its exact close instant when set. There is no PE
			     dimension (AUTH-ADR-001 v1.6 §1.1 — the site is exactly one
			     implicit Procuring Entity). -->
			<div class="kt-card kt-blueprint" style="margin-bottom: 16px; padding: 20px 24px">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i>
				<i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div class="kt-context-grid" style="grid-template-columns: repeat(3, 1fr)">
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
							<label for="nds-fy-band">Financial Year</label>
						</div>
						<select
							id="nds-fy-band"
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
					<div class="kt-readonly-row">
						<div class="kt-readonly-label">Needs submission</div>
						<div class="kt-readonly-value is-strong" data-testid="nds-submission-state">
							{{ submission.open ? "Open" : "Closed" }}
						</div>
						<div
							v-if="submission.open && submission.closes_at"
							style="font-size: 12.5px; color: var(--color-neutral-600); margin-top: 4px"
							data-testid="nds-submission-closes-at"
						>
							Closes {{ formatInstant(submission.closes_at) }}
						</div>
					</div>
				</div>
			</div>

			<!-- §11.15 "No open Fiscal Year" — existing rows stay visible and
			     readable; only the notice and the missing Create button say so. -->
			<p
				v-if="!submission.open && needs.length"
				data-testid="nds-submission-closed-notice"
				style="margin: 0 0 16px; font-size: 13.5px; color: var(--color-neutral-700)"
			>
				Needs submission is currently closed. You can continue viewing existing needs.
			</p>

			<!-- §12.1 — search matches title or reference; status is the only filter. -->
			<div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px">
				<div class="kt-field" style="flex: 1; max-width: 360px; margin: 0">
					<label class="sr-only" for="nds-search">Search title or reference</label>
					<input
						id="nds-search"
						data-testid="nds-search"
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
						data-testid="nds-status-filter"
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
					{{ filtersActive ? "No needs match your filters" : "No departmental needs yet" }}
				</div>
				<p
					style="margin: 0 0 8px; font-size: 14.5px; color: var(--color-neutral-700); max-width: 420px"
				>
					{{
						filtersActive
							? "Adjust the search or status filter, or clear the filters."
							: "Create the first need for this department and Financial Year."
					}}
				</p>
				<button
					v-if="canCreate && !filtersActive"
					class="kt-btn kt-btn-primary"
					data-testid="nds-create-need-empty"
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

			<div v-if="needs.length" data-testid="nds-count" style="margin-top: 12px; font-size: 13px; color: var(--color-neutral-600)">
				{{ countLabel }}
			</div>
		</template>
	</div>
</template>

<script setup>
import { computed } from "vue";
import NeedsTable from "./NeedsTable.vue";
import { formatInstant } from "../data/format.js";

const props = defineProps({
	loading: Boolean,
	error: { type: String, default: "" },
	outcome: { type: String, default: "" },
	context: { type: Object, default: () => ({}) },
	// get_needs_submission_state() shape: { open, financial_year, label, closes_at }.
	submission: { type: Object, default: () => ({}) },
	needs: { type: Array, default: () => [] },
	actions: { type: Array, default: () => [] },
	countLabel: { type: String, default: "" },
	search: { type: String, default: "" },
	status: { type: String, default: "" },
	financialYears: { type: Array, default: () => [] },
});

defineEmits([
	"create",
	"reload",
	"action",
	"update:search",
	"update:status",
	"clear-filters",
	"select-financial-year",
	"change-context",
]);

const STATUSES = [
	"Draft",
	"Submitted",
	"Returned",
	"Accepted for planning",
	"Not taken forward",
];

const columns = [
	{ key: "need", label: "Need" },
	// The workspace also serves the Head of User Department through the main
	// rail entry, where rows are the whole department's, not the viewer's own —
	// authorship must be visible without opening each record.
	{ key: "author_label", label: "Requested by" },
	{ key: "quantity_label", label: "Quantity", align: "right" },
	{ key: "required_by_label", label: "Required by" },
	{ key: "status", label: "Status", status: true },
	{ key: "planning_usage", label: "Planning usage", status: true },
	{ key: "action", label: "Action", align: "right" },
];

// An empty list under active filters means "nothing matched", not "nothing
// exists" — the create-first copy would misstate the workspace.
const filtersActive = computed(() => !!(props.search || props.status));

// §12.1 — Create need needs both: the server must offer the action (only an
// author in this context does), and Needs submission must be Open. The flag
// check alone would show the button to a reviewer for as long as it is Open.
const canCreate = computed(
	() => props.actions.some((action) => action.code === "create") && !!props.submission.open
);
</script>
