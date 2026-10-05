<!-- REQ-DES-01 — Requisitions workspace (board v2, base + DRAFT / ACTION /
     NONE / TECHNICAL). Level 1 is this actor's exact work, Level 2 the
     purchases ready to start, Level 3 the searchable register (§13.2). Every
     row, label and route comes from the server; this screen only lays it out
     and keeps the caller's own filter selection. -->
<template>
	<div class="kt-panel-lg req-page" data-testid="req-workspace" :data-mode="workspace.mode">
		<h3 style="margin: 0">Procurement Requisitions</h3>
		<p class="kt-muted req-lede" :style="technical ? 'margin-bottom: var(--kt-space-6)' : ''">Prepare and follow requests for purchases already approved in the annual plan.</p>

		<template v-if="!technical">
			<section v-if="work.length" data-testid="req-your-work">
				<CardTitle title="Your work" icon="inbox" />
				<div v-for="row in work" :key="row.task_id || row.requisition" class="req-work-row" data-testid="req-work-row">
					<div>
						<div class="kt-label">{{ row.meta }}</div>
						<div class="req-work-task">{{ row.task }}</div>
						<div class="req-work-title">{{ row.title }}</div>
						<div v-if="row.detail" class="kt-muted req-work-detail">{{ row.detail }}</div>
					</div>
					<button type="button" class="btn btn-primary" @click="ctx.goPath(row.route)">{{ row.action }}</button>
				</div>
			</section>

			<section v-if="showReady" data-testid="req-ready">
				<CardTitle title="Ready to start" icon="inbox" />
				<template v-if="readyRows.length">
					<div class="req-has-cards" style="margin-bottom: var(--kt-space-8)">
						<table class="table">
							<thead>
								<tr><th>Approved purchase</th><th>Departments</th><th>Still available</th><th>Needed by</th><th style="white-space: nowrap">Action</th></tr>
							</thead>
							<tbody>
								<tr v-for="row in readyRows" :key="row.plan_item_id" data-testid="req-ready-row">
									<td><div style="font-weight: 600">{{ row.title }}</div><div class="kt-label" style="margin-top: 4px">{{ row.plan_item_reference }}</div></td>
									<td>{{ row.departments }}</td>
									<td>{{ row.available_quantity }}<div class="kt-label">{{ row.available_value }}</div></td>
									<td>{{ row.needed_by }}</td>
									<td><button type="button" class="btn btn-primary" data-testid="req-start" @click="ctx.goPath(row.route)">Start requisition</button></td>
								</tr>
							</tbody>
						</table>
						<div class="req-row-cards">
							<div v-for="row in readyRows" :key="row.plan_item_id" class="req-row-card">
								<div style="font-size: 15px; font-weight: 600">{{ row.title }}</div>
								<div class="kt-label" style="margin-top: 2px">{{ row.plan_item_reference }}</div>
								<dl>
									<dt class="kt-label">Departments</dt><dd>{{ row.departments }}</dd>
									<dt class="kt-label">Still available</dt><dd>{{ row.available_quantity }} · {{ row.available_value }}</dd>
									<dt class="kt-label">Needed by</dt><dd>{{ row.needed_by }}</dd>
								</dl>
								<div style="margin-top: 12px"><button type="button" class="btn btn-primary req-btn-block" @click="ctx.goPath(row.route)">Start requisition</button></div>
							</div>
						</div>
					</div>
				</template>
				<!-- An open requisition replaces Start requisition; it is never shown beside it (REQ-DES-12). -->
				<div v-for="row in existingRows" :key="row.plan_item_id" style="margin-bottom: var(--kt-space-8)" data-testid="req-ready-existing">
					<div class="req-rule is-accent">
						<div style="font-size: 14px; font-weight: 600">{{ row.title }}</div>
						<p style="font-size: 14px; margin: 6px 0 0">{{ row.existing.summary }}</p>
					</div>
					<div class="req-actions" style="margin-top: var(--kt-space-4)">
						<button type="button" class="btn btn-primary" @click="ctx.goPath(row.existing.route)">Open existing requisition</button>
					</div>
				</div>
				<div v-if="!readyRows.length && !existingRows.length" class="req-empty" data-testid="req-ready-none">
					<div class="req-empty-title">No approved purchases are ready for a requisition.</div>
					<p class="kt-muted" style="font-size: 13px; margin: 6px 0 0">New requisitions appear here once Planning approves a purchase.</p>
				</div>
			</section>
		</template>

		<section data-testid="req-register" :style="!technical && !readyRows.length && !existingRows.length && showReady ? 'margin-top: var(--kt-space-8)' : ''">
			<div v-if="technical">
				<CardTitle title="Requisitions" class="req-register-title" />
			</div>
			<div v-else class="req-register-head">
				<CardTitle title="Your requisitions" icon="clipboard" class="req-register-title" style="margin: 0" />
				<span v-if="approvals" class="kt-label" data-testid="req-count-approvals">Approvals {{ approvals }}</span>
			</div>
			<div class="req-filters" :class="{ 'is-technical': technical }">
				<input
					class="input"
					type="search"
					aria-label="Search by requisition or purchase"
					placeholder="Search by requisition or purchase"
					:value="search"
					data-testid="req-filter-search"
					@input="onSearch($event.target.value)"
				/>
				<select class="input" aria-label="Status" :value="filters.status" data-testid="req-filter-status" @change="$emit('filters', { status: $event.target.value })">
					<option value="">All statuses</option>
					<option v-for="o in options.statuses || []" :key="o.value" :value="o.value">{{ o.label }}</option>
				</select>
				<select class="input" aria-label="Department" :value="filters.department" data-testid="req-filter-department" @change="$emit('filters', { department: $event.target.value })">
					<option value="">{{ workspace.department_filter_label || "All my departments" }}</option>
					<option v-for="o in options.departments || []" :key="o.value" :value="o.value">{{ o.label }}</option>
				</select>
				<select v-if="technical" class="input" aria-label="Financial year" :value="filters.fiscal_year" data-testid="req-filter-fiscal-year" @change="$emit('filters', { fiscal_year: $event.target.value })">
					<option value="">All financial years</option>
					<option v-for="o in options.fiscal_years || []" :key="o.value" :value="o.value">{{ o.label }}</option>
				</select>
				<button v-else type="button" class="btn btn-ghost" data-testid="req-clear-filters" @click="clearFilters">Clear filters</button>
			</div>
			<div v-if="register.length" class="req-has-cards">
				<table class="table" data-testid="req-register-table">
					<thead>
						<tr>
							<th>Requisition</th><th>Approved purchase</th><th>Departments</th><th>Status</th><th>Updated</th>
						</tr>
					</thead>
					<tbody>
						<tr v-for="row in register" :key="row.requisition" class="req-row-link" data-testid="req-register-row" @click="ctx.goPath(row.route)">
							<td style="white-space: nowrap"><a :href="row.route" @click.stop.prevent="ctx.goPath(row.route)">{{ row.reference }}</a></td>
							<td>{{ row.title }}<div v-if="technical" class="kt-label">{{ row.plan_item_reference }}</div></td>
							<td>{{ row.departments }}</td>
							<td>{{ row.status }}</td>
							<td>{{ row.updated }}</td>
						</tr>
					</tbody>
				</table>
				<div class="req-row-cards">
					<div v-for="row in register" :key="row.requisition" class="req-row-card">
						<a :href="row.route" style="font-weight: 600" @click.stop.prevent="ctx.goPath(row.route)">{{ row.reference }}</a>
						<dl>
							<dt class="kt-label">Approved purchase</dt><dd>{{ row.title }}</dd>
							<dt class="kt-label">Departments</dt><dd>{{ row.departments }}</dd>
							<dt class="kt-label">Status</dt><dd>{{ row.status }}</dd>
							<dt class="kt-label">Updated</dt><dd>{{ row.updated }}</dd>
						</dl>
					</div>
				</div>
			</div>
			<p v-else-if="filtered" style="font-size: 14px; margin: 0" data-testid="req-register-no-match">No requisitions match these filters.</p>
			<p v-else style="font-size: 14px; margin: 0" data-testid="req-register-empty">You have no requisitions yet.</p>
		</section>
	</div>
</template>

<script setup>
import { computed, onBeforeUnmount, ref } from "vue";
import { useReq } from "../data/context.js";
import CardTitle from "./shared/CardTitle.vue";

const props = defineProps({
	workspace: { type: Object, required: true },
	filters: { type: Object, required: true },
});
const emit = defineEmits(["filters"]);
const ctx = useReq();

const technical = computed(() => props.workspace.mode === "technical");
const work = computed(() => props.workspace.your_work || []);
const ready = computed(() => props.workspace.ready_to_start || []);
const readyRows = computed(() => ready.value.filter((r) => !r.existing));
const existingRows = computed(() => ready.value.filter((r) => r.existing));
// DRAFT variant: with a Draft already leading Your work and nothing else to
// start, the Ready section is absent rather than an empty state (§13.2).
const showReady = computed(() => ready.value.length > 0 || work.value.length === 0);
const register = computed(() => props.workspace.register || []);
const options = computed(() => props.workspace.filters || {});
const approvals = computed(() => (props.workspace.counts || {}).Approvals || 0);
const filtered = computed(() => !!search.value || ["search", "status", "department", "fiscal_year"].some((k) => props.filters[k]));

// The text being typed is this input's own state; the root hears it once the
// typing pauses (a re-render must never reset what is being typed).
const search = ref(props.filters.search || "");
let searchTimer = null;
function onSearch(value) {
	search.value = value;
	clearTimeout(searchTimer);
	searchTimer = setTimeout(() => emit("filters", { search: value }), 250);
}
onBeforeUnmount(() => clearTimeout(searchTimer));

function clearFilters() {
	clearTimeout(searchTimer);
	search.value = "";
	emit("filters", { search: "", status: "", department: "", fiscal_year: "" });
}
</script>
