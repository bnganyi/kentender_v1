<script setup>
// AUTH-ADR-001 v1.6 §13.4/§14.2 — the Users and responsibilities tab
// (AUTH-DES-03), with the §14.3 assign dialog, §13.7 detail and §13.8 revoke
// dialog. There is no Procuring Entity filter, column or control anywhere:
// one site is one PE (§1.1). Filters are visible, optional and
// non-authoritative; the server applies the one predicate behind them.
import { computed, onMounted, reactive, ref, watch } from "vue";
import AssignDialog from "../components/AssignDialog.vue";
import ResponsibilityDetail from "../components/ResponsibilityDetail.vue";
import RevokeDialog from "../components/RevokeDialog.vue";
import { responsibilityApi } from "../data/responsibilityApi.js";

const props = defineProps({
	// Preset OU filter when arriving from "View affected responsibilities".
	initialUnit: { type: String, default: "" },
});

const loading = ref(true);
const busy = ref(false);
const loadError = ref("");
const forbidden = ref(false);
const rows = ref([]);
const total = ref(0);
const options = ref({ responsibilities: [], organisation_units: [], statuses: [] });
const detail = ref(null);
const view = ref("register");
const dialog = reactive({ kind: "", error: "" });

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

async function loadOptions() {
	try {
		options.value = await responsibilityApi.formOptions();
	} catch (error) {
		if (error.httpStatus === 403) forbidden.value = true;
	}
}

async function loadRows({ quiet = false } = {}) {
	if (!quiet) loading.value = true;
	loadError.value = "";
	forbidden.value = false;
	try {
		const result = await responsibilityApi.listRows({ ...filters });
		rows.value = result.rows;
		total.value = result.total;
	} catch (error) {
		if (error.httpStatus === 403) forbidden.value = true;
		else loadError.value = error.message;
		rows.value = [];
	} finally {
		loading.value = false;
	}
}

let searchTimer = null;
function loadRowsDebounced() {
	if (searchTimer) clearTimeout(searchTimer);
	searchTimer = setTimeout(() => loadRows({ quiet: true }), 250);
}

async function openDetail(assignment) {
	view.value = "detail";
	loading.value = true;
	loadError.value = "";
	try {
		detail.value = await responsibilityApi.detail(assignment);
	} catch (error) {
		if (error.httpStatus === 403) forbidden.value = true;
		else loadError.value = error.message;
		detail.value = null;
	} finally {
		loading.value = false;
	}
}

function backToRegister() {
	view.value = "register";
	detail.value = null;
	loadRows({ quiet: true });
}

onMounted(() => {
	loadOptions();
	loadRows();
});
watch(() => props.initialUnit, (unit) => {
	filters.organisation_unit = unit || "";
	view.value = "register";
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
	dialog.kind = kind;
	dialog.error = "";
}
function closeDialog() {
	dialog.kind = "";
	dialog.error = "";
}

async function submitAssignment(payload) {
	busy.value = true;
	dialog.error = "";
	try {
		const result = await responsibilityApi.assign(payload);
		closeDialog();
		await loadRows();
		await openDetail(result.assignment);
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
		closeDialog();
		await openDetail(detail.value.assignment);
	} catch (error) {
		dialog.error = error.message;
	} finally {
		busy.value = false;
	}
}

</script>

<template>
	<section class="kt-setup-section" data-testid="kt-setup-ura">
		<!-- Detail — AUTH-DES-06 -->
		<template v-if="view === 'detail'">
			<div v-if="loading" class="kt-card kt-blueprint" data-testid="kt-ura-loading">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<span class="kt-eyebrow">{{ __("Loading") }}</span>
				<div class="kt-skel" style="width:90%" />
				<div class="kt-skel" style="width:70%" />
			</div>
			<div v-else-if="loadError" class="kt-card kt-blueprint kt-empty" data-testid="kt-ura-detail-error">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h2>{{ __("Responsibilities could not be loaded") }}</h2>
				<p>{{ __("Try again. If the problem continues, contact support.") }}</p>
				<button type="button" class="kt-btn kt-btn-secondary" @click="backToRegister">{{ __("Try again") }}</button>
			</div>
			<ResponsibilityDetail
				v-else-if="detail"
				:assignment="detail"
				@revoke="openDialog('revoke')"
				@back="backToRegister"
			/>
		</template>

		<!-- Register — AUTH-DES-03 -->
		<template v-else>
			<div class="kt-section-head">
				<div>
					<h2 class="kt-section-title">{{ __("Users and responsibilities") }}</h2>
					<p class="kt-muted">
						{{ __("Assign each user a business responsibility in its exact organisational scope.") }}
					</p>
				</div>
				<button
					type="button"
					class="kt-btn kt-btn-primary"
					data-testid="kt-ura-assign-open"
					@click="openDialog('assign')"
				>{{ __("Assign responsibility") }}</button>
			</div>

			<!-- AUTH-DES-03 — labelled filter panel -->
			<div class="kt-filters">
				<div class="kt-field">
					<label for="kt-ura-search">{{ __("Search user or responsibility") }}</label>
					<input
						id="kt-ura-search"
						v-model="filters.search"
						class="kt-input"
						type="search"
						:placeholder="__('Search user or responsibility')"
						data-testid="kt-ura-search"
					>
				</div>
				<div class="kt-field">
					<label for="kt-ura-filter-ou">{{ __("Organisation Unit") }}</label>
					<select id="kt-ura-filter-ou" v-model="filters.organisation_unit" class="kt-input" data-testid="kt-ura-filter-ou">
						<option value="">{{ __("All organisation units") }}</option>
						<option v-for="unit in options.organisation_units" :key="unit.id" :value="unit.id">{{ unit.label }}</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="kt-ura-filter-role">{{ __("Responsibility") }}</label>
					<select id="kt-ura-filter-role" v-model="filters.business_role" class="kt-input" data-testid="kt-ura-filter-role">
						<option value="">{{ __("All responsibilities") }}</option>
						<option v-for="role in options.responsibilities" :key="role.business_role" :value="role.business_role">
							{{ role.business_role }}
						</option>
					</select>
				</div>
				<div class="kt-field">
					<label for="kt-ura-filter-status">{{ __("Status") }}</label>
					<select id="kt-ura-filter-status" v-model="filters.status" class="kt-input" data-testid="kt-ura-filter-status">
						<option value="">{{ __("All statuses") }}</option>
						<option v-for="status in options.statuses" :key="status" :value="status">{{ status }}</option>
					</select>
				</div>
				<button
					type="button"
					class="kt-btn kt-btn-ghost"
					:disabled="!hasFilters"
					data-testid="kt-ura-clear"
					@click="clearFilters"
				>{{ __("Clear filters") }}</button>
			</div>

			<div v-if="loading" class="kt-card kt-blueprint" data-testid="kt-ura-loading">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<span class="kt-eyebrow">{{ __("Loading responsibilities…") }}</span>
				<div class="kt-skel" style="width:90%" />
				<div class="kt-skel" style="width:75%" />
				<div class="kt-skel" style="width:82%" />
			</div>

			<div v-else-if="forbidden" class="kt-card kt-blueprint kt-empty" data-testid="kt-ura-forbidden">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h2>{{ __("System setup is not available") }}</h2>
				<p>{{ __("You do not have the technical access required to maintain responsibilities.") }}</p>
			</div>

			<!-- AUTH-DES-08 — a failure is never drawn as an empty success -->
			<div v-else-if="loadError" class="kt-card kt-blueprint kt-empty" data-testid="kt-ura-error">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h2>{{ __("Responsibilities could not be loaded") }}</h2>
				<p>{{ __("Try again. If the problem continues, contact support.") }}</p>
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-ura-retry" @click="loadRows">
					{{ __("Try again") }}
				</button>
			</div>

			<div v-else-if="!rows.length" class="kt-card kt-blueprint kt-empty" data-testid="kt-ura-empty">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h2>{{ hasFilters ? __("No responsibilities match these filters") : __("No responsibilities assigned yet") }}</h2>
				<p>
					{{ hasFilters
						? __("Clear the filters to see every assignment.")
						: __("Assign the first business responsibility for this entity.") }}
				</p>
				<button
					v-if="!hasFilters"
					type="button"
					class="kt-btn kt-btn-primary"
					@click="openDialog('assign')"
				>{{ __("Assign responsibility") }}</button>
				<button v-else type="button" class="kt-btn kt-btn-secondary" @click="clearFilters">
					{{ __("Clear filters") }}
				</button>
			</div>

			<div v-else class="kt-card kt-blueprint kt-table-card" data-testid="kt-ura-table">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<div class="kt-table-scroll">
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
									<div class="kt-row-name">{{ row.user_full_name }}</div>
									<div class="kt-muted kt-row-login">{{ row.user }}</div>
								</td>
								<td>{{ row.business_role }}</td>
								<td>{{ row.scope_label }}</td>
								<td>{{ row.coverage }}</td>
								<td>{{ row.appointment_type }}</td>
								<td>{{ row.period_label }}</td>
								<td><span class="kt-status" :class="STATUS_KIND[row.status]">{{ row.status }}</span></td>
								<td>
									<a href="#" @click.prevent="openDetail(row.assignment)">{{ __("View") }}</a>
								</td>
							</tr>
						</tbody>
					</table>
				</div>
			</div>
			<p v-if="!loading && !forbidden && !loadError && rows.length" class="kt-count">
				{{ total === 1 ? __("1 responsibility") : __("{0} responsibilities", [total]) }}
			</p>
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
