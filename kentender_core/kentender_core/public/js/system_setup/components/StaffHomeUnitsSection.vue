<script setup>
// AUTH-ADR-001 v1.12 AUTH-DES-10 — the Staff home units tab of Users and
// responsibilities: where each staff member works, and who has no home unit
// recorded. Read-mostly; each row has one action that opens AUTH-DES-11. A home
// unit grants nothing, so there is no responsibility, scope or role column.
//
// One server predicate behind rows and count; the filters are visible,
// optional and non-authoritative; "Not recorded" is derived on the server. The
// table is paged in the browser with the shared pager (AGENTS.md §6.11).
import { computed, onMounted, reactive, ref, watch, nextTick } from "vue";
import { onSetupRevalidate } from "../composables/useRouteState.js";
import TablePagerHost from "../../pager_shared/TablePagerHost.vue";
import { usePagedRows } from "../../pager_shared/usePagedRows.js";
import SetHomeUnitDialog from "./SetHomeUnitDialog.vue";
import { newIdempotencyKey, staffHomeUnitApi } from "../data/staffHomeUnitApi.js";
import AccessDenied from "../../access_shared/AccessDenied.vue";

const loading = ref(true);
const loadError = ref("");
const forbidden = ref(false);
const rows = ref([]);
const units = ref([]);
const busy = ref(false);
const { pagedRows, page, pageSize, setPage, setPageSize, reset } = usePagedRows(rows, "system-setup-staff-home-units");
const filters = reactive({ search: "", home: "" });
const dialog = reactive({ row: null, error: "" });
let trigger = null;
let attemptKey = "";

const hasFilters = computed(() => !!filters.search || !!filters.home);
const sequence = kentender_core.desk_page.createSequenceGuard();

async function load({ quiet = false } = {}) {
	const ticket = sequence.next();
	// The skeleton is for a tab with nothing to show yet; a refresh happens in place.
	if (!quiet || !rows.value.length) loading.value = true;
	try {
		const result = await staffHomeUnitApi.list({ search: filters.search, notRecorded: filters.home === "not-recorded" });
		if (!sequence.isCurrent(ticket)) return;
		if (result && result.outcome === "FORBIDDEN") {
			forbidden.value = true;
			rows.value = [];
			return;
		}
		forbidden.value = false;
		loadError.value = "";
		rows.value = result.rows || [];
		units.value = result.units || [];
	} catch (error) {
		if (!sequence.isCurrent(ticket)) return;
		loadError.value = error.message || __("Staff members could not be loaded");
		rows.value = [];
	} finally {
		if (sequence.isCurrent(ticket)) loading.value = false;
	}
}

let searchTimer = null;
watch(() => filters.search, () => {
	reset();
	if (searchTimer) clearTimeout(searchTimer);
	searchTimer = setTimeout(() => load({ quiet: true }), 250);
});
watch(() => filters.home, () => {
	reset();
	load({ quiet: true });
});
onMounted(() => load());
onSetupRevalidate(() => load({ quiet: true }));

function clearFilters() {
	filters.search = "";
	filters.home = "";
}

function openDialog(row) {
	trigger = document.activeElement;
	dialog.row = row;
	dialog.error = "";
	attemptKey = newIdempotencyKey();
}
async function closeDialog({ restoreFocus = true } = {}) {
	dialog.row = null;
	dialog.error = "";
	await nextTick();
	if (restoreFocus && trigger && trigger.isConnected) trigger.focus();
	trigger = null;
}

// One command, awaited with its reload inside the pending guard (AGENTS.md §6.4).
async function submit(unit) {
	if (!dialog.row) return;
	busy.value = true;
	dialog.error = "";
	try {
		await staffHomeUnitApi.set(dialog.row.user, unit, dialog.row.token, attemptKey);
		await closeDialog({ restoreFocus: false });
		await load({ quiet: true });
	} catch (error) {
		dialog.error = error.message;
		// A stale token reloads the current row rather than overwriting it.
		if (/changed since you opened it/i.test(error.message || "")) await load({ quiet: true });
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<div class="kt-staff-home-units" data-testid="kt-staff-home-units">
		<template v-if="forbidden">
			<AccessDenied :heading="__('You do not have access to System setup')" :text="__('This area needs Administrator or System Manager access. Ask your KenTender administrator to grant it.')" testid="kt-home-forbidden" />
		</template>
		<template v-else-if="loading && !rows.length">
			<div role="status" aria-live="polite" data-testid="kt-home-loading">
				<p class="text-muted" style="margin:0 0 10px">{{ __("Loading staff members…") }}</p>
				<div class="kt-table-scroll">
					<table class="table">
						<thead><tr><th>{{ __("Staff member") }}</th><th>{{ __("Home organisation unit") }}</th><th>{{ __("Action") }}</th></tr></thead>
						<tbody>
							<tr v-for="n in 3" :key="n">
								<td><div class="kt-skel" style="width:70%" /></td>
								<td><div class="kt-skel" style="width:60%" /></td>
								<td><div class="kt-skel" style="width:30%" /></td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
		</template>
		<template v-else-if="loadError">
			<div class="kt-ura-state" role="alert" data-testid="kt-home-error">
				<p style="font-weight:600;margin:0 0 4px">{{ __("Staff members could not be loaded") }}</p>
				<p class="card-body" style="margin:0 0 16px">{{ __("Try again. If the problem continues, contact support.") }}</p>
				<button type="button" class="btn btn-secondary" data-testid="kt-home-retry" @click="load()">{{ __("Try again") }}</button>
			</div>
		</template>
		<template v-else>
			<p class="card-body" style="margin:0 0 14px" data-testid="kt-home-line">{{ __("Record where each staff member works. This does not grant any responsibility or access.") }}</p>
			<div class="kt-filter-bar kt-ura-filters">
				<div class="field is-wide">
					<label for="kt-home-search">{{ __("Search") }}</label>
					<div class="kt-input-icon">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
						<input id="kt-home-search" v-model="filters.search" class="input" type="search" :placeholder="__('Search staff member')" data-testid="kt-home-search">
					</div>
				</div>
				<div class="field">
					<label for="kt-home-filter">{{ __("Home unit") }}</label>
					<select id="kt-home-filter" v-model="filters.home" class="input" data-testid="kt-home-filter">
						<option value="">{{ __("All staff") }}</option>
						<option value="not-recorded">{{ __("Not recorded") }}</option>
					</select>
				</div>
				<button type="button" class="btn btn-secondary" :disabled="!hasFilters" data-testid="kt-home-clear" @click="clearFilters">{{ __("Clear filters") }}</button>
			</div>

			<div v-if="!rows.length" class="kt-ura-state" data-testid="kt-home-empty">
				<p style="font-weight:600;margin:0 0 4px">
					{{ filters.home === "not-recorded" && !filters.search ? __("Every staff member has a home unit recorded.") : __("No staff members match these filters") }}
				</p>
				<p v-if="filters.search || filters.home !== 'not-recorded'" class="card-body" style="margin:0">{{ __("Clear the filters to see every staff member.") }}</p>
			</div>
			<template v-else>
				<div class="kt-table-scroll" data-testid="kt-home-table">
					<table class="table">
						<thead>
							<tr>
								<th>{{ __("Staff member") }}</th>
								<th>{{ __("Home organisation unit") }}</th>
								<th>{{ __("Action") }}</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="row in pagedRows" :key="row.user" :data-testid="'kt-home-row-' + row.user">
								<td>
									<div style="font-weight:600">{{ row.full_name }}</div>
									<div class="text-muted" style="font-size:13px">{{ row.user }}</div>
								</td>
								<td :data-testid="'kt-home-unit-' + row.user">
									<span v-if="row.state === 'Not recorded'" class="text-muted">{{ __("Not recorded") }}</span>
									<template v-else>{{ row.unit_name }} <span v-if="row.unit_status === 'Inactive'" class="text-muted">{{ __("Inactive") }}</span></template>
								</td>
								<td>
									<a href="#" :data-testid="'kt-home-edit-' + row.user" @click.stop.prevent="openDialog(row)">{{ row.state === "Not recorded" ? __("Set home unit") : __("Change") }}</a>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
				<TablePagerHost :total="rows.length" :page="page" :page-size="pageSize" noun="staff member" noun-plural="staff members" @update:page="setPage" @update:page-size="setPageSize" />
			</template>
		</template>

		<SetHomeUnitDialog
			v-if="dialog.row"
			:row="dialog.row"
			:units="units"
			:busy="busy"
			:error="dialog.error"
			@save="submit"
			@clear="submit('')"
			@cancel="closeDialog"
		/>
	</div>
</template>
