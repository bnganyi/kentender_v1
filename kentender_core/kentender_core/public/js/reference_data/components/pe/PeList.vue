<script setup>
import { reactive, computed } from "vue";
import RegisterStates from "../RegisterStates.vue";
import StatusPill from "../StatusPill.vue";

const props = defineProps({
	rows: { type: Array, default: () => [] },
	loading: { type: Boolean, default: false },
	error: { type: Object, default: null },
	peTypes: { type: Array, default: () => [] },
});
const emit = defineEmits(["open", "retry"]);

const filters = reactive({ q: "", peType: "", status: "" });

function clearFilters() {
	filters.q = "";
	filters.peType = "";
	filters.status = "";
}

const statusOptions = computed(() => [...new Set(props.rows.map((r) => r.status))].sort());

const filteredRows = computed(() => {
	const needle = filters.q.trim().toLowerCase();
	return props.rows.filter((r) => {
		if (needle && !(`${r.code} ${r.legal_name}`.toLowerCase().includes(needle))) return false;
		if (filters.peType && r.pe_type !== filters.peType) return false;
		if (filters.status && r.status !== filters.status) return false;
		return true;
	});
});

const isEmpty = computed(() => !props.loading && !props.error && props.rows.length > 0 && filteredRows.value.length === 0);
</script>

<template>
	<div style="margin:28px 48px 0;display:grid;grid-template-columns:minmax(0,1fr) 260px 260px;gap:16px">
		<input class="kt-input" type="text" v-model="filters.q" :placeholder="__('Search code or name')" />
		<select class="kt-input" v-model="filters.peType">
			<option value="">{{ __("All PE types") }}</option>
			<option v-for="t in peTypes" :key="t.type_code" :value="t.type_code">{{ t.label }}</option>
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
						<th style="width:120px">{{ __("Code") }}</th>
						<th>{{ __("Procuring entity") }}</th>
						<th style="width:280px">{{ __("PE type") }}</th>
						<th style="width:130px">{{ __("Status") }}</th>
						<th style="width:170px">{{ __("Effective from") }}</th>
						<th style="width:100px;text-align:right">{{ __("Action") }}</th>
					</tr>
				</thead>
				<tbody>
					<tr v-for="row in filteredRows" :key="row.pe_id">
						<td class="kt-tabular">{{ row.code }}</td>
						<td>{{ row.legal_name }}</td>
						<td class="kt-muted">{{ row.pe_type || "—" }}</td>
						<td><StatusPill :status="row.status" /></td>
						<td class="kt-muted">{{ frappe.datetime.str_to_user(row.effective_from) || "—" }}</td>
						<td style="text-align:right">
							<button type="button" class="kt-btn kt-btn-ghost" @click="emit('open', row.pe_id)">{{ __("View") }}</button>
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
