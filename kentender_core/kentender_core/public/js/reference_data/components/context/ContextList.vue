<script setup>
import { reactive, computed } from "vue";
import RegisterStates from "../RegisterStates.vue";
import StatusPill from "../StatusPill.vue";

const props = defineProps({
	rows: { type: Array, default: () => [] },
	loading: { type: Boolean, default: false },
	error: { type: Object, default: null },
	peOptions: { type: Array, default: () => [] }, // [{code, legal_name}]
	fyOptions: { type: Array, default: () => [] }, // [{label}]
});
const emit = defineEmits(["open", "retry"]);

const filters = reactive({ q: "", pe: "", fy: "", status: "" });

function clearFilters() {
	filters.q = "";
	filters.pe = "";
	filters.fy = "";
	filters.status = "";
}

const statusOptions = computed(() => [...new Set(props.rows.map((r) => r.status))].sort());

const filteredRows = computed(() => {
	const needle = filters.q.trim().toLowerCase();
	return props.rows.filter((r) => {
		if (needle && !(`${r.context_id} ${r.procuring_entity}`.toLowerCase().includes(needle))) return false;
		if (filters.pe && r.procuring_entity !== filters.pe) return false;
		if (filters.fy && r.financial_year !== filters.fy) return false;
		if (filters.status && r.status !== filters.status) return false;
		return true;
	});
});

const isEmpty = computed(() => !props.loading && !props.error && props.rows.length > 0 && filteredRows.value.length === 0);
</script>

<template>
	<div style="margin:28px 48px 0;display:grid;grid-template-columns:minmax(0,1fr) 220px 200px 200px;gap:16px">
		<input class="kt-input" type="text" v-model="filters.q" :placeholder="__('Search context or procuring entity')" />
		<select class="kt-input" v-model="filters.pe">
			<option value="">{{ __("All procuring entities") }}</option>
			<option v-for="p in peOptions" :key="p.code" :value="p.legal_name">{{ p.legal_name }}</option>
		</select>
		<select class="kt-input" v-model="filters.fy">
			<option value="">{{ __("All financial years") }}</option>
			<option v-for="f in fyOptions" :key="f.label" :value="f.label">{{ f.label }}</option>
		</select>
		<select class="kt-input" v-model="filters.status">
			<option value="">{{ __("All statuses") }}</option>
			<option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
		</select>
	</div>

	<div style="margin:28px 48px 0">
		<RegisterStates :loading="loading" :error="error" :is-empty="isEmpty" @clear-filters="clearFilters" @retry="emit('retry')">
			<table class="kt-table">
				<thead>
					<tr>
						<th style="width:210px">{{ __("Context") }}</th>
						<th>{{ __("Procuring entity") }}</th>
						<th style="width:120px">{{ __("Financial year") }}</th>
						<th style="width:300px">{{ __("Available from–to") }}</th>
						<th style="width:110px">{{ __("Status") }}</th>
						<th style="width:200px">{{ __("Readiness") }}</th>
						<th style="width:96px;text-align:right">{{ __("Action") }}</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in filteredRows" :key="row.context_id">
						<td class="kt-tabular">{{ row.context_id }}</td>
						<td>{{ row.procuring_entity }}</td>
						<td class="kt-muted kt-tabular">{{ row.financial_year }}</td>
						<td class="kt-muted">{{ frappe.datetime.str_to_user(row.active_from) }}–{{ frappe.datetime.str_to_user(row.active_to) }}</td>
						<td><StatusPill :status="row.status" /></td>
						<td><StatusPill :status="row.readiness" /></td>
						<td style="text-align:right">
							<button type="button" class="kt-btn kt-btn-ghost" @click="emit('open', row.context_id)">{{ __("View") }}</button>
						</td>
					</tr>
				</tbody>
			</table>
			<div style="padding:18px 16px 0;font-size:13px;color:color-mix(in srgb, var(--kt-color-text) 60%, transparent)">
				{{ __("Showing {0} of {1}", [filteredRows.length, rows.length]) }}
			</div>
		</RegisterStates>
	</div>
</template>
