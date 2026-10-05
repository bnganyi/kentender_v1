<!-- TPR-DES-01 Tenders workspace (§10.2), ported class-for-class: the masthead, the
     role-specific count cards (absent for readers, technical users and an
     empty result), the filter row, and the one connected queue table. Every
     row's status and action come from the server's own projection
     (read.py::tender_row / start_row) — the client never derives them. -->
<template>
	<div class="tnd-page tnd-page--wide" data-screen-label="TPR-DES-01 Tenders workspace">
		<BlueprintCard>
			<div class="tnd-ws-head">
				<div class="tnd-title-row">
					<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-accent-700)" stroke-width="1.5"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M10 9H8"/><path d="M16 13H8"/><path d="M16 17H8"/></svg>
					<h1 class="tnd-h1 tnd-h1--lg">Tenders</h1>
				</div>
				<p class="tnd-lede">Prepare approved requisitions, complete approvals and follow publication.</p>
			</div>

			<div v-if="loading" data-testid="tnd-loading">
				<div v-for="row in 3" :key="row" class="tnd-skel-row">
					<div class="kt-skel" style="width: 72%"></div>
					<div class="kt-skel" style="width: 52%"></div>
					<div class="kt-skel" style="width: 44%"></div>
				</div>
			</div>

			<template v-else>
				<div v-if="showCounts" class="tnd-ws-counts" data-testid="tnd-counts">
					<div class="kt-kpi-row tnd-kpi-row" :style="{ '--tnd-cards': counts.length }">
						<button v-for="c in counts" :key="c.key" type="button" class="kt-kpi-card tnd-kpi-btn" :class="[kpiClass(c), { 'is-selected': filters.status === c.key }]" :aria-pressed="filters.status === c.key ? 'true' : 'false'" :data-testid="`tnd-count-${c.key}`" @click="pickCount(c.key)">
							<svg class="kt-kpi-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path v-for="(d, i) in icon(c.key)" :key="i" :d="d"></path></svg>
							<div class="kt-kpi-value">{{ c.value }}</div>
							<div class="tnd-kpi-label">{{ c.label }}</div>
						</button>
					</div>
				</div>

				<div class="tnd-ws-filters">
					<div class="field tnd-search"><label for="tnd-search">Search</label><input id="tnd-search" class="input" placeholder="Tender, requisition or purchase" :value="filters.search" data-testid="tnd-filter-search" @input="update('search', $event.target.value)" /></div>
					<div class="field"><label for="tnd-status">Status</label><select id="tnd-status" class="input" :value="filters.status" data-testid="tnd-filter-status" @change="update('status', $event.target.value)">
						<option value="">All statuses</option>
						<option v-for="s in statusOptions" :key="s.key" :value="s.key">{{ s.label }}</option>
					</select></div>
					<div class="field"><label for="tnd-fy">Financial year</label><select id="tnd-fy" class="input" :value="filters.fiscal_year" data-testid="tnd-filter-fy" @change="update('fiscal_year', $event.target.value)">
						<option value="">All financial years</option>
						<option v-for="fy in fiscalYears" :key="fy" :value="fy">{{ fy }}</option>
					</select></div>
					<button type="button" class="btn btn-secondary" data-testid="tnd-clear-filters" @click="$emit('clear-filters')">Clear filters</button>
				</div>

				<div v-if="!rows.length" class="tnd-empty" data-testid="tnd-empty">
					<svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="var(--color-neutral-500)" stroke-width="1.5"><circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/></svg>
					<p>{{ workspace.empty_text || "No Tenders match these filters." }}</p>
					<button type="button" class="btn btn-secondary" @click="$emit('clear-filters')">Clear filters</button>
				</div>

				<div v-else class="tnd-table-wrap">
					<table class="table" data-testid="tnd-queue">
						<thead><tr><th style="width: 32%">Purchase</th><th style="width: 22%">Tender</th><th style="width: 22%">Status</th><th style="width: 14%">Required by</th><th style="width: 10%" class="tnd-cell-right">Action</th></tr></thead>
						<tbody>
							<tr v-for="row in rows" :key="row.kind + ':' + (row.tender || row.handoff)" :data-testid="`tnd-row-${row.status_key}`" :data-tender="row.tender_reference">
								<td><div class="tnd-row-purchase"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--color-neutral-600)" stroke-width="1.5"><path d="M16.5 9.4 7.55 4.24"/><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/><path d="M3.29 7 12 12l8.71-5"/><path d="M12 22V12"/></svg><div>{{ row.purchase }}<div class="tnd-sub">{{ row.plan_item_id }}</div></div></div></td>
								<td>{{ row.tender_reference }}<div class="tnd-sub">{{ row.requisition_reference }}</div></td>
								<td><span class="kt-status" :class="statusClass(row.status_key)">{{ row.status_label }}</span><div v-if="row.secondary" class="tnd-sub tnd-sub--4">{{ row.secondary }}</div></td>
								<td>{{ row.required_by }}</td>
								<td class="tnd-cell-right"><button type="button" class="btn" :class="row.action_key === 'view' ? 'btn-secondary' : 'btn-primary'" :disabled="pending" :data-testid="`tnd-action-${row.action_key}`" @click="$emit('navigate', row.route)">{{ row.action_label }}</button></td>
							</tr>
						</tbody>
					</table>
				</div>
			</template>
		</BlueprintCard>
	</div>
</template>

<script setup>
import { computed } from "vue";
import BlueprintCard from "./BlueprintCard.vue";

const props = defineProps({
	loading: Boolean,
	workspace: { type: Object, default: () => ({}) },
	filters: { type: Object, default: () => ({ search: "", status: "", fiscal_year: "" }) },
	pending: Boolean,
});
const emit = defineEmits(["navigate", "filter", "clear-filters"]);

const rows = computed(() => props.workspace.rows || []);
const counts = computed(() => props.workspace.counts || []);
const showCounts = computed(() => counts.value.length > 0);
const statusOptions = computed(() => (props.workspace.filters || {}).statuses || []);
const fiscalYears = computed(() => (props.workspace.filters || {}).fiscal_years || []);

// a count card is a shortcut to the Status filter; selecting the active card clears it
function pickCount(key) {
	update("status", props.filters.status === key ? "" : key);
}
function update(name, value) {
	emit("filter", { ...props.filters, [name]: value });
}

// TPR-DES-01 — the board's own status → pill and count → accent mapping.
const STATUS_CLASS = { ready: "is-pending", draft: "is-draft", returned: "is-attention", awaiting_approval: "is-attention", approved: "is-attention", publishing: "is-attention", published: "is-live", ended: "is-pending", cancelled: "is-critical", correction: "is-critical" };
function statusClass(key) {
	return STATUS_CLASS[key] || "is-draft";
}
const COUNT_STATE = { ready: "live", published: "live", returned: "attention", awaiting_approval: "attention", approved: "attention", publishing: "attention" };
function kpiClass(c) {
	const state = COUNT_STATE[c.key];
	return c.value > 0 && state ? `is-${state}` : "";
}
const ICON = {
	ready: ["M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20", "m10 8 6 4-6 4V8"],
	draft: ["M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z", "M14 2v5h5"],
	returned: ["M9 14 4 9l5-5", "M4 9h10.5A5.5 5.5 0 0 1 20 14.5v0A5.5 5.5 0 0 1 14.5 20H11"],
	in_progress: ["M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20", "M12 6v6l4 2"],
	published: ["M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20", "M2 12h20", "M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"],
	closed: ["M21 8v13H3V8", "M1 3h22v5H1z", "M10 12h4"],
	awaiting_approval: ["M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20", "M12 6v6l4 2"],
	approved: ["M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20", "M12 6v6l4 2"],
	publishing: ["M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z", "M14 2v5h5", "m9 15 2 2 4-4"],
};
function icon(key) {
	return ICON[key] || ICON.draft;
}
</script>
