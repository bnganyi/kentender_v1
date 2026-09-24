<script setup>
// The Users and responsibilities tab, ported from
// C06-Users-Responsibilities.dc.html: the register (AUTH-DES-03), the assign
// and edit dialogs (AUTH-DES-04/05), the detail (AUTH-DES-06), the revoke
// dialog (AUTH-DES-07) and the common states (AUTH-DES-08). There is no
// Procuring Entity filter, column or control anywhere: one site is one PE.
// Filters are visible, optional and non-authoritative; the server applies
// the one predicate behind them.
//
// A responsibility opens by its own link (`#users-and-responsibilities/{id}`),
// so reload and Back return to it.
import { computed, nextTick, onMounted, reactive, ref, watch } from "vue";
import { onSetupRevalidate } from "../composables/useRouteState.js";
import AssignDialog from "../components/AssignDialog.vue";
import ResponsibilityDetail from "../components/ResponsibilityDetail.vue";
import RevokeDialog from "../components/RevokeDialog.vue";
import { responsibilityApi } from "../data/responsibilityApi.js";

const props = defineProps({
	// Preset unit filter when arriving from "View affected responsibilities".
	initialUnit: { type: String, default: "" },
	// The responsibility named by the link; empty shows the register.
	assignmentId: { type: String, default: "" },
});
const emit = defineEmits(["open"]);

const loading = ref(true);
const busy = ref(false);
const loadError = ref("");
const forbidden = ref(false);
const rows = ref([]);
const total = ref(0);
const options = ref({ responsibilities: [], organisation_units: [], statuses: [] });
const detail = ref(null);
const detailLoading = ref(false);
const detailError = ref("");
const dialog = reactive({ kind: "", error: "" });
// The control that opened a dialog, so closing it returns focus there.
let trigger = null;

const filters = reactive({
	search: "",
	organisation_unit: props.initialUnit || "",
	business_role: "",
	status: "",
});

const STATUS_KIND = {
	Active: "is-live",
	Scheduled: "is-draft",
	Expired: "is-pending",
	Revoked: "is-critical",
};

const hasFilters = computed(() => Object.values(filters).some((v) => v));
// The board's state variants replace the register's header and filters;
// an empty result under filters keeps them, so the filters can be cleared.
const registerState = computed(() => {
	if (loading.value) return "loading";
	if (forbidden.value) return "forbidden";
	if (loadError.value) return "error";
	if (!rows.value.length && !hasFilters.value) return "empty";
	return "";
});

const rowSequence = kentender_core.desk_page.createSequenceGuard();
const detailSequence = kentender_core.desk_page.createSequenceGuard();

async function loadOptions() {
	try {
		options.value = await responsibilityApi.formOptions();
	} catch (error) {
		if (error.httpStatus === 403) forbidden.value = true;
	}
}

async function loadRows({ quiet = false } = {}) {
	const ticket = rowSequence.next();
	if (!quiet) loading.value = true;
	try {
		const result = await responsibilityApi.listRows({ ...filters });
		if (!rowSequence.isCurrent(ticket)) return;
		rows.value = result.rows;
		total.value = result.total;
		loadError.value = "";
		forbidden.value = false;
	} catch (error) {
		if (!rowSequence.isCurrent(ticket)) return;
		if (error.httpStatus === 403) forbidden.value = true;
		else loadError.value = error.message;
		rows.value = [];
	} finally {
		if (rowSequence.isCurrent(ticket)) loading.value = false;
	}
}

let searchTimer = null;
function loadRowsDebounced() {
	if (searchTimer) clearTimeout(searchTimer);
	searchTimer = setTimeout(() => loadRows({ quiet: true }), 250);
}

async function loadDetail({ quiet = false } = {}) {
	const id = props.assignmentId;
	if (!id) {
		detail.value = null;
		return;
	}
	const ticket = detailSequence.next();
	// Nothing to show yet is the only reason for the loading line; a
	// re-read of the one on screen happens in place.
	if (!quiet || detail.value?.assignment !== id) detailLoading.value = true;
	try {
		const result = await responsibilityApi.detail(id);
		if (!detailSequence.isCurrent(ticket)) return;
		detail.value = result;
		detailError.value = "";
	} catch (error) {
		if (!detailSequence.isCurrent(ticket)) return;
		if (error.httpStatus === 403) forbidden.value = true;
		else detailError.value = error.message;
		detail.value = null;
	} finally {
		if (detailSequence.isCurrent(ticket)) detailLoading.value = false;
	}
}

function openDetail(id) {
	emit("open", id);
}

// Kept alive by the root: a return re-reads what is on screen, in place.
onSetupRevalidate(() => {
	loadRows({ quiet: true });
	if (props.assignmentId) loadDetail({ quiet: true });
});
onMounted(() => {
	loadOptions();
	loadRows();
	loadDetail();
});
watch(() => props.assignmentId, () => loadDetail());
watch(() => props.initialUnit, (unit) => {
	filters.organisation_unit = unit || "";
	loadRows({ quiet: true });
});
watch(() => filters.search, loadRowsDebounced);
watch(
	() => [filters.organisation_unit, filters.business_role, filters.status],
	() => loadRows({ quiet: true })
);

function clearFilters() {
	Object.keys(filters).forEach((key) => (filters[key] = ""));
	loadRows({ quiet: true });
}

function openDialog(kind) {
	trigger = document.activeElement;
	dialog.kind = kind;
	dialog.error = "";
}
async function closeDialog({ restoreFocus = true } = {}) {
	dialog.kind = "";
	dialog.error = "";
	await nextTick();
	if (restoreFocus && trigger && trigger.isConnected) trigger.focus();
	trigger = null;
}

async function submitAssignment(payload) {
	busy.value = true;
	dialog.error = "";
	try {
		const result = await responsibilityApi.assign(payload);
		await closeDialog({ restoreFocus: false });
		await loadRows({ quiet: true });
		openDetail(result.assignment);
	} catch (error) {
		dialog.error = error.message;
	} finally {
		busy.value = false;
	}
}

async function submitEdit(payload) {
	busy.value = true;
	dialog.error = "";
	try {
		await responsibilityApi.updateScheduled(detail.value.assignment, payload, detail.value.expected_version);
		await closeDialog();
		await loadDetail({ quiet: true });
		loadRows({ quiet: true });
	} catch (error) {
		dialog.error = error.message;
	} finally {
		busy.value = false;
	}
}

async function submitRevocation(reason) {
	busy.value = true;
	dialog.error = "";
	try {
		await responsibilityApi.revoke(detail.value.assignment, reason, detail.value.expected_version);
		await closeDialog({ restoreFocus: false });
		await loadDetail({ quiet: true });
		loadRows({ quiet: true });
	} catch (error) {
		dialog.error = error.message;
	} finally {
		busy.value = false;
	}
}
</script>

<template>
	<section class="kt-setup-section is-flow" data-testid="kt-setup-ura">
		<!-- AUTH-DES-06 -->
		<template v-if="assignmentId">
			<div v-if="detailLoading && !detail" role="status" aria-live="polite" data-testid="kt-ura-loading">
				<p class="text-muted" style="margin:0 0 10px">{{ __("Loading responsibility…") }}</p>
				<div class="kt-skel" style="width:90%" />
				<div class="kt-skel" style="width:70%" />
			</div>
			<div v-else-if="forbidden" class="kt-ura-state" data-testid="kt-ura-forbidden">
				<p style="font-weight:600;margin:0 0 4px">{{ __("You do not have access to System setup") }}</p>
				<p class="card-body" style="margin:0">{{ __("This area needs Administrator or System Manager access. Ask your KenTender administrator to grant it.") }}</p>
			</div>
			<div v-else-if="detailError" class="kt-ura-state" role="alert" data-testid="kt-ura-detail-error">
				<p style="font-weight:600;margin:0 0 4px">{{ __("Responsibilities could not be loaded") }}</p>
				<p class="card-body" style="margin:0 0 16px">{{ __("Try again. If the problem continues, contact support.") }}</p>
				<button type="button" class="kt-btn kt-btn-secondary" @click="loadDetail()">{{ __("Try again") }}</button>
			</div>
			<ResponsibilityDetail
				v-else-if="detail"
				:assignment="detail"
				@revoke="openDialog('revoke')"
				@edit="openDialog('edit')"
			/>
		</template>

		<!-- AUTH-DES-08 states: the heading and the state, nothing else -->
		<template v-else-if="registerState">
			<!-- The Forbidden variant is drawn without the heading. -->
			<h2 v-if="registerState !== 'forbidden'" style="margin:0 0 16px;font-size:22px">{{ __("Users and responsibilities") }}</h2>
			<div v-if="registerState === 'loading'" role="status" aria-live="polite" data-testid="kt-ura-loading">
				<p class="text-muted" style="margin:0 0 10px">{{ __("Loading responsibilities…") }}</p>
				<div class="kt-table-scroll">
					<table class="kt-table">
						<thead><tr><th>{{ __("User") }}</th><th>{{ __("Responsibility") }}</th><th>{{ __("Scope") }}</th><th>{{ __("Status") }}</th></tr></thead>
						<tbody>
							<tr v-for="n in 3" :key="n">
								<td><div class="kt-skel" style="width:70%" /></td>
								<td><div class="kt-skel" style="width:80%" /></td>
								<td><div class="kt-skel" style="width:60%" /></td>
								<td><div class="kt-skel" style="width:50%" /></td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
			<div v-else-if="registerState === 'forbidden'" class="kt-ura-state" data-testid="kt-ura-forbidden">
				<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="var(--kt-color-neutral-400)" stroke-width="1.5" aria-hidden="true" style="margin:0 auto 12px"><rect x="5" y="11" width="14" height="10" /><path d="M8 11V7a4 4 0 0 1 8 0v4" /></svg>
				<p style="font-weight:600;margin:0 0 4px">{{ __("You do not have access to System setup") }}</p>
				<p class="card-body" style="margin:0 auto;max-width:52ch">{{ __("This area needs Administrator or System Manager access. Ask your KenTender administrator to grant it.") }}</p>
			</div>
			<div v-else-if="registerState === 'error'" class="kt-ura-state" role="alert" data-testid="kt-ura-error">
				<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="var(--kt-color-neutral-400)" stroke-width="1.5" aria-hidden="true" style="margin:0 auto 12px"><circle cx="12" cy="12" r="9" /><path d="M12 8v5" /><path d="M12 16h.01" /></svg>
				<p style="font-weight:600;margin:0 0 4px">{{ __("Responsibilities could not be loaded") }}</p>
				<p class="card-body" style="margin:0 0 16px">{{ __("Try again. If the problem continues, contact support.") }}</p>
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-ura-retry" @click="loadRows()">{{ __("Try again") }}</button>
			</div>
			<div v-else class="kt-ura-state" data-testid="kt-ura-empty">
				<svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="var(--kt-color-neutral-400)" stroke-width="1.5" aria-hidden="true" style="margin:0 auto 12px"><circle cx="9" cy="8" r="4" /><path d="M2 21a7 7 0 0 1 14 0" /><path d="M19 8v6M16 11h6" /></svg>
				<p style="font-weight:600;margin:0 0 4px">{{ __("No responsibilities assigned yet") }}</p>
				<p class="card-body" style="margin:0 0 16px">{{ __("Assign the first business responsibility for this entity.") }}</p>
				<button type="button" class="kt-btn kt-btn-primary" data-testid="kt-ura-empty-assign" @click="openDialog('assign')">{{ __("Assign responsibility") }}</button>
			</div>
		</template>

		<!-- AUTH-DES-03 -->
		<template v-else>
			<div class="kt-ura-head">
				<div>
					<div class="kt-eyebrow">{{ __("System setup") }}</div>
					<h2 style="margin:4px 0 6px">{{ __("Users and responsibilities") }}</h2>
					<p class="card-body" style="margin:0">{{ __("Assign each user a business responsibility in its exact organisational scope.") }}</p>
				</div>
				<button type="button" class="kt-btn kt-btn-primary" data-testid="kt-ura-assign-open" @click="openDialog('assign')">
					<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><path d="M12 5v14M5 12h14" /></svg>{{ __("Assign responsibility") }}
				</button>
			</div>

			<div class="kt-filter-bar kt-ura-filters">
				<div class="kt-field is-wide">
					<label for="kt-ura-search">{{ __("Search") }}</label>
					<div class="kt-input-icon">
						<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true"><circle cx="11" cy="11" r="7" /><path d="m20 20-3.5-3.5" /></svg>
						<input
							id="kt-ura-search"
							v-model="filters.search"
							class="kt-input"
							type="search"
							:placeholder="__('Search user or responsibility')"
							data-testid="kt-ura-search"
						>
					</div>
				</div>
				<div class="kt-field">
					<label for="kt-ura-filter-ou">{{ __("Organisation unit") }}</label>
					<select id="kt-ura-filter-ou" v-model="filters.organisation_unit" class="kt-input" data-testid="kt-ura-filter-ou">
						<option value="">{{ __("All organisation units") }}</option>
						<option v-for="unit in options.organisation_units" :key="unit.id" :value="unit.id">{{ unit.label }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="kt-ura-filter-role">{{ __("Responsibility") }}</label>
					<select id="kt-ura-filter-role" v-model="filters.business_role" class="kt-input" data-testid="kt-ura-filter-role">
						<option value="">{{ __("All responsibilities") }}</option>
						<option v-for="role in options.responsibilities" :key="role.business_role" :value="role.business_role">{{ role.business_role }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="kt-ura-filter-status">{{ __("Status") }}</label>
					<select id="kt-ura-filter-status" v-model="filters.status" class="kt-input" data-testid="kt-ura-filter-status">
						<option value="">{{ __("All statuses") }}</option>
						<option v-for="status in options.statuses" :key="status" :value="status">{{ status }}</option>
					</select>
				</div>
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="!hasFilters" data-testid="kt-ura-clear" @click="clearFilters">{{ __("Clear filters") }}</button>
			</div>

			<div v-if="!rows.length" class="kt-ura-state" data-testid="kt-ura-no-match">
				<p style="font-weight:600;margin:0 0 4px">{{ __("No responsibilities match these filters") }}</p>
				<p class="card-body" style="margin:0">{{ __("Clear the filters to see every assignment.") }}</p>
			</div>
			<template v-else>
				<div class="kt-table-scroll" data-testid="kt-ura-table">
					<table class="kt-table">
						<thead>
							<tr>
								<th>{{ __("User") }}</th>
								<th>{{ __("Responsibility") }}</th>
								<th>{{ __("Scope") }}</th>
								<th>{{ __("Coverage") }}</th>
								<th>{{ __("Appointment") }}</th>
								<th>{{ __("Effective period") }}</th>
								<th>{{ __("Status") }}</th>
								<th>{{ __("Action") }}</th>
							</tr>
						</thead>
						<tbody>
							<tr v-for="row in rows" :key="row.assignment" :data-testid="'kt-ura-row-' + row.assignment">
								<td>
									<div style="font-weight:600">{{ row.user_full_name }}</div>
									<div class="text-muted" style="font-size:13px">{{ row.user }}</div>
								</td>
								<td>{{ row.business_role }}</td>
								<td>{{ row.scope_label }}</td>
								<td>{{ row.coverage }}</td>
								<td>{{ row.appointment_type }}</td>
								<td>{{ row.period_label }}</td>
								<td><span class="kt-status" :class="STATUS_KIND[row.status]">{{ row.status }}</span></td>
								<td>
									<a
										:href="'#users-and-responsibilities/' + encodeURIComponent(row.assignment)"
										:data-testid="'kt-ura-view-' + row.assignment"
										@click.stop.prevent="openDetail(row.assignment)"
									>{{ __("View") }}</a>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
				<p class="text-muted" style="font-size:13px;margin:12px 0 0" data-testid="kt-ura-count">
					{{ total === 1 ? __("1 responsibility") : __("{0} responsibilities", [total]) }}
				</p>
			</template>
		</template>

		<AssignDialog
			v-if="dialog.kind === 'assign'"
			:responsibilities="options.responsibilities"
			:organisation-units="options.organisation_units"
			:busy="busy"
			:error="dialog.error"
			@submit="submitAssignment"
			@cancel="closeDialog"
		/>
		<AssignDialog
			v-if="dialog.kind === 'edit' && detail"
			:editing="detail"
			:responsibilities="options.responsibilities"
			:organisation-units="options.organisation_units"
			:busy="busy"
			:error="dialog.error"
			@submit="submitEdit"
			@cancel="closeDialog"
		/>
		<RevokeDialog
			v-if="dialog.kind === 'revoke' && detail"
			:assignment="detail"
			:busy="busy"
			:error="dialog.error"
			@confirm="submitRevocation"
			@cancel="closeDialog"
		/>
	</section>
</template>
