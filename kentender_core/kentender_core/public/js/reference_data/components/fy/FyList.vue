<script setup>
import { reactive, computed } from "vue";
import RegisterStates from "../RegisterStates.vue";
import StatusPill from "../StatusPill.vue";

const props = defineProps({
	rows: { type: Array, default: () => [] },
	loading: { type: Boolean, default: false },
	error: { type: Object, default: null },
});
const emit = defineEmits(["open", "retry"]);

const filters = reactive({ q: "", phase: "", status: "" });

function clearFilters() {
	filters.q = "";
	filters.phase = "";
	filters.status = "";
}

const phaseOptions = computed(() => [...new Set(props.rows.map((r) => r.calendar_phase))].sort());
const statusOptions = computed(() => [...new Set(props.rows.map((r) => r.record_status))].sort());

const filteredRows = computed(() => {
	const needle = filters.q.trim().toLowerCase();
	return props.rows.filter((r) => {
		if (needle && !r.label.toLowerCase().includes(needle)) return false;
		if (filters.phase && r.calendar_phase !== filters.phase) return false;
		if (filters.status && r.record_status !== filters.status) return false;
		return true;
	});
});

const isEmpty = computed(() => !props.loading && !props.error && props.rows.length > 0 && filteredRows.value.length === 0);
</script>

<template>
	<div style="margin:28px 48px 0;display:grid;grid-template-columns:minmax(0,1fr) 260px 260px;gap:16px">
		<input class="kt-input" type="text" v-model="filters.q" :placeholder="__('Search financial year')" />
		<select class="kt-input" v-model="filters.phase">
			<option value="">{{ __("All calendar phases") }}</option>
			<option v-for="p in phaseOptions" :key="p" :value="p">{{ p }}</option>
		</select>
		<select class="kt-input" v-model="filters.status">
			<option value="">{{ __("All reference statuses") }}</option>
			<option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
		</select>
	</div>

	<div style="margin:28px 48px 0">
		<RegisterStates :loading="loading" :error="error" :is-empty="isEmpty" @clear-filters="clearFilters" @retry="emit('retry')">
			<table class="kt-table">
				<thead>
					<tr>
						<th style="width:150px">{{ __("Financial year") }}</th>
						<th>{{ __("Period") }}</th>
						<th style="width:200px">{{ __("Calendar phase") }}</th>
						<th style="width:180px">{{ __("Reference status") }}</th>
						<th style="width:150px;text-align:right">{{ __("PE/FY contexts") }}</th>
						<th style="width:100px;text-align:right">{{ __("Action") }}</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in filteredRows" :key="row.financial_year_id">
						<td class="kt-tabular">{{ row.label }}</td>
						<td class="kt-muted">{{ frappe.datetime.str_to_user(row.start_date) }}–{{ frappe.datetime.str_to_user(row.end_date) }}</td>
						<td class="kt-muted">{{ row.calendar_phase }}</td>
						<td><StatusPill :status="row.record_status" /></td>
						<td style="text-align:right" class="kt-tabular">{{ row.context_count }}</td>
						<td style="text-align:right">
							<button type="button" class="kt-btn kt-btn-ghost" @click="emit('open', row.financial_year_id)">{{ __("View") }}</button>
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
