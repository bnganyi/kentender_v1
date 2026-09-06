<script setup>
// STR-UI-01 Strategy Portfolio (STR-DES-01/02/10). Routes:
//   /app/strategy            Plans tab
//   /app/strategy/my-work    My work tab
//   /app/strategy/new        New strategic plan draft form
import { ref, reactive, computed, onMounted, onActivated, watch } from "vue";
import { useRouteState } from "../../strategy_shared/composables/useRouteState.js";
import { usePageRail } from "../../strategy_shared/composables/usePageRail.js";
import { fetchPortfolio, saveNewPlanDraft } from "../data/strategyApi.js";

const { route, go, epoch } = useRouteState("strategy");
const mode = computed(() => (route.value[1] === "new" ? "create" : "list"));
const activeTab = computed(() => (route.value[1] === "my-work" ? "my-work" : "plans"));

const railTrail = computed(() => {
	const items = [{ label: __("Home"), route: ["Workspaces", "Procurement Home"] }];
	if (mode.value === "create") {
		items.push({ label: __("Strategy Alignment"), route: ["strategy"] });
		items.push({ label: __("New strategic plan") });
	} else {
		items.push({ label: __("Strategy Alignment") });
	}
	return items;
});
const railEl = ref(null);
usePageRail(railEl, railTrail);

const loading = ref(true);
const refreshing = ref(false);
const error = ref(null);
const forbidden = ref(false);
const plans = ref([]);
const myWork = ref([]);
const canCreate = ref(false);
const loadedOnce = ref(false);

// §12.1 — search matches reference and title; role and status are
// server-side; counts use the same predicate as rows.
const filters = reactive({ q: "", role: "", status: "" });

let refreshSeq = 0;
async function refresh(opts) {
	const quiet = !!(opts && opts.quiet === true) && loadedOnce.value;
	const seq = ++refreshSeq;
	if (quiet) refreshing.value = true;
	else loading.value = true;
	error.value = null;
	try {
		const data = await fetchPortfolio({ search: filters.q, plan_role: filters.role, status: filters.status });
		if (seq !== refreshSeq) return;
		forbidden.value = !!data.forbidden;
		if (!data.forbidden) {
			plans.value = data.plans;
			myWork.value = data.my_work;
			canCreate.value = !!data.can_create_plan;
		}
		loadedOnce.value = true;
	} catch (e) {
		if (seq === refreshSeq) error.value = e;
	} finally {
		if (seq === refreshSeq) {
			loading.value = false;
			refreshing.value = false;
		}
	}
}
onMounted(refresh);
let activations = 0;
onActivated(() => {
	// Back from a plan or an approval task: rows stay on screen and revalidate.
	if (activations++ > 0 && mode.value === "list") refresh({ quiet: true });
});
watch(mode, (m) => {
	if (m === "list") refresh({ quiet: true });
});
watch(epoch, () => {
	if (mode.value === "list") refresh({ quiet: true });
});
let filterTimer = null;
watch(
	() => [filters.q, filters.role, filters.status],
	() => {
		clearTimeout(filterTimer);
		filterTimer = setTimeout(() => refresh({ quiet: true }), 250);
	}
);

const filtersActive = computed(() => !!(filters.q || filters.role || filters.status));
function clearFilters() {
	filters.q = "";
	filters.role = "";
	filters.status = "";
}

const ROLE_OPTIONS = ["Primary", "Supporting Framework"];
const STATUS_OPTIONS = ["Draft", "Submitted for approval", "Active", "Superseded"];

function statusClass(status) {
	if (status === "Active") return "is-live";
	if (status === "Submitted for approval") return "is-pending";
	return "is-draft";
}

// §12.1 — View / Continue draft / Approve follow the server-returned route.
function openRoute(routeArray) {
	if (Array.isArray(routeArray) && routeArray.length) frappe.set_route(...routeArray);
}

// --- New strategic plan draft form (STR-DES-02) ---
const draft = reactive({ title: "", plan_role: "Primary", parent_primary_plan_id: "", period_start: "", period_end: "" });
const saving = ref(false);
const saveError = ref(null);
const fieldErrors = reactive({ title: "", parent_primary_plan_id: "", period_start: "", period_end: "" });
function validateDraft() {
	fieldErrors.title = draft.title.trim() ? "" : __("Enter a plan title.");
	fieldErrors.parent_primary_plan_id =
		draft.plan_role === "Supporting Framework" && !draft.parent_primary_plan_id ? __("Select the governing Primary plan.") : "";
	fieldErrors.period_start = draft.period_start ? "" : __("Enter the plan period start.");
	fieldErrors.period_end = !draft.period_end
		? __("Enter the plan period end.")
		: draft.period_start && draft.period_end <= draft.period_start
		? __("The plan period end must be later than its start.")
		: "";
	return !Object.values(fieldErrors).some(Boolean);
}
const primaryPlans = computed(() => plans.value.filter((p) => p.plan_role === "Primary"));

function openCreateForm() {
	Object.assign(draft, { title: "", plan_role: "Primary", parent_primary_plan_id: "", period_start: "", period_end: "" });
	Object.assign(fieldErrors, { title: "", parent_primary_plan_id: "", period_start: "", period_end: "" });
	saveError.value = null;
	go("new");
}

const canCreatePlan = computed(() => !forbidden.value && canCreate.value);

async function submitDraft() {
	if (!validateDraft()) return;
	saving.value = true;
	saveError.value = null;
	try {
		const result = await saveNewPlanDraft({
			plan_role: draft.plan_role,
			parent_primary_plan_id: draft.plan_role === "Supporting Framework" ? draft.parent_primary_plan_id || null : null,
			title: draft.title,
			period_start: draft.period_start,
			period_end: draft.period_end,
			// §12.2 — the first version effective period equals the plan period.
			effective_from: draft.period_start,
			effective_to: draft.period_end,
		});
		frappe.show_alert({ message: __("Plan draft saved"), indicator: "green" });
		frappe.set_route("strategy", "plan", result.plan.plan_reference);
	} catch (e) {
		saveError.value = e.message || __("Could not save the draft.");
	} finally {
		saving.value = false;
	}
}
</script>

<template>
	<div
		class="kt-shell"
		data-testid="str-portfolio"
		:data-mode="mode"
		:data-loading="loading ? 'true' : 'false'"
		:data-refreshing="refreshing ? 'true' : 'false'"
	>
		<template v-if="mode === 'list'">
			<header style="display: flex; justify-content: space-between; align-items: flex-end; gap: 16px">
				<div>
					<div class="kt-eyebrow" style="text-transform: uppercase; font-size: 11px; letter-spacing: 0.08em; color: var(--kt-color-accent); margin-bottom: 6px">
						{{ __("Strategy Alignment") }}
					</div>
					<h1 style="font-size: 32px">{{ __("Strategy Portfolio") }}</h1>
					<p class="kt-muted" style="margin-top: 6px">
						{{ __("Maintain the approved strategy structure used by Budget and Procurement Planning.") }}
					</p>
				</div>
				<button v-if="canCreatePlan" type="button" class="kt-btn kt-btn-primary" data-testid="str-new-plan" @click="openCreateForm">
					{{ __("New strategic plan") }}
				</button>
			</header>

			<!-- KT-STD-001 §3A.1: nothing but the verdict's own state paints. -->
			<div v-if="loading" class="kt-card kt-blueprint" data-testid="str-loading">
				<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
				<div v-for="i in 5" :key="i" class="kt-skel" style="height: 16px; margin-bottom: 10px"></div>
			</div>

			<div v-else-if="forbidden" class="kt-card kt-empty" data-testid="str-forbidden">
				<h2>{{ __("You do not have access to Strategy Alignment.") }}</h2>
				<p>{{ __("This area needs one of these responsibilities: Strategy Author, Strategy Approver or Auditor. Ask your KenTender administrator to assign one in System setup.") }}</p>
			</div>

			<div v-else-if="error && !loadedOnce" class="kt-card kt-empty" data-testid="str-error">
				<h2>{{ __("Strategy plans could not be loaded.") }}</h2>
				<p>{{ __("Try again. If the problem continues, contact KenTender support.") }}</p>
				<button type="button" class="kt-btn kt-btn-secondary" @click="refresh">{{ __("Try again") }}</button>
			</div>

			<template v-else>
				<div class="kt-tabs">
					<div class="kt-tab" data-testid="str-tab-plans" :aria-selected="activeTab === 'plans'" @click="go()">{{ __("Plans") }} <span class="kt-count">{{ plans.length }}</span></div>
					<div class="kt-tab" data-testid="str-tab-my-work" :aria-selected="activeTab === 'my-work'" @click="go('my-work')">{{ __("My work") }} <span class="kt-count">{{ myWork.length }}</span></div>
				</div>

				<p v-if="error" class="kt-muted" data-testid="str-refresh-error">{{ __("The list could not be refreshed. Showing the last loaded plans.") }}</p>

				<template v-if="activeTab === 'plans'">
					<div v-if="plans.length === 0 && !filtersActive" class="kt-card kt-empty" data-testid="str-empty">
						<h2>{{ __("No strategic plans exist yet.") }}</h2>
						<button v-if="canCreatePlan" type="button" class="kt-btn kt-btn-secondary" @click="openCreateForm">
							{{ __("New strategic plan") }}
						</button>
					</div>
					<template v-else>
						<div style="display: flex; gap: 12px">
							<input v-model="filters.q" class="kt-input" style="flex: 1" data-testid="str-search" :placeholder="__('Search plan or reference')" />
							<select v-model="filters.role" class="kt-input" style="width: 190px" data-testid="str-role-filter">
								<option value="">{{ __("All plan roles") }}</option>
								<option v-for="r in ROLE_OPTIONS" :key="r" :value="r">{{ r }}</option>
							</select>
							<select v-model="filters.status" class="kt-input" style="width: 190px" data-testid="str-status-filter">
								<option value="">{{ __("All statuses") }}</option>
								<option v-for="s in STATUS_OPTIONS" :key="s" :value="s">{{ s }}</option>
							</select>
						</div>

						<div class="kt-card kt-blueprint">
							<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
							<div v-if="plans.length === 0" class="kt-empty" data-testid="str-no-match">
								<h2>{{ __("No plans match these filters.") }}</h2>
								<p>{{ __("Change or clear the filters to see other strategic plans.") }}</p>
								<button type="button" class="kt-btn kt-btn-secondary" data-testid="str-clear-filters" @click="clearFilters">
									{{ __("Clear filters") }}
								</button>
							</div>
							<table v-else class="kt-table" data-testid="str-plans-table">
								<thead>
									<tr>
										<th>{{ __("Strategic plan") }}</th>
										<th>{{ __("Role") }}</th>
										<th>{{ __("Period") }}</th>
										<th>{{ __("Current version") }}</th>
										<th>{{ __("Status") }}</th>
										<th>{{ __("Action") }}</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="p in plans" :key="p.id" data-testid="str-plan-row" :data-plan-reference="p.reference">
										<td>
											<div>{{ p.title }}</div>
											<div class="kt-muted">{{ p.reference }}</div>
										</td>
										<td>{{ p.plan_role }}</td>
										<td>{{ p.period_label || "—" }}</td>
										<td>{{ p.current_version ? `Version ${p.current_version.version_number}` : "—" }}</td>
										<td><span class="kt-status" :class="statusClass(p.status)">{{ p.status }}</span></td>
										<td><a href="#" data-testid="str-row-action" @click.prevent="openRoute(p.action_route)">{{ p.available_action || __("View") }}</a></td>
									</tr>
								</tbody>
							</table>
						</div>
						<div class="kt-muted" data-testid="str-count-label">
							{{ plans.length === 1 ? __("Showing 1 of 1 plan") : __("Showing {0} of {1} plans", [plans.length, plans.length]) }}
						</div>
					</template>
				</template>

				<template v-else>
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div v-if="myWork.length === 0" class="kt-empty" data-testid="str-my-work-empty">
							<h2>{{ __("Nothing needs your action right now.") }}</h2>
						</div>
						<table v-else class="kt-table" data-testid="str-my-work-table">
							<thead>
								<tr>
									<th>{{ __("Strategic plan") }}</th>
									<th>{{ __("Version") }}</th>
									<th>{{ __("Status") }}</th>
									<th>{{ __("Action") }}</th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="w in myWork" :key="w.version_id" data-testid="str-my-work-row" :data-version-reference="w.version_reference">
									<td>
										<div>{{ w.plan_title }}</div>
										<div class="kt-muted">{{ w.plan_reference }}</div>
									</td>
									<td>{{ __("Version") }} {{ w.version_number }}</td>
									<td><span class="kt-status" :class="statusClass(w.status)">{{ w.status }}</span></td>
									<td><a href="#" data-testid="str-my-work-action" @click.prevent="openRoute(w.action_route)">{{ w.action_label }}</a></td>
								</tr>
							</tbody>
						</table>
					</div>
					<div class="kt-muted">{{ __("Showing {0} item(s)", [myWork.length]) }}</div>
				</template>
			</template>
		</template>

		<template v-else>
			<div style="padding-bottom: 90px">
				<header>
					<h1 style="font-size: 28px">{{ __("New strategic plan") }} <span class="kt-status is-draft">{{ __("Draft") }}</span></h1>
				</header>
				<div class="kt-card kt-blueprint" style="max-width: 720px" data-testid="str-new-plan-form">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">{{ __("Plan identity") }}</div>
					<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px">
						<div class="kt-field">
							<label>{{ __("Plan reference") }}</label>
							<div class="kt-input" style="background: color-mix(in srgb, var(--kt-color-text) 6%, transparent)">{{ __("Not assigned") }}</div>
						</div>
						<div class="kt-field">
							<label>{{ __("Plan role") }}</label>
							<select v-model="draft.plan_role" class="kt-input" data-testid="str-plan-role">
								<option value="Primary">{{ __("Primary") }}</option>
								<option value="Supporting Framework">{{ __("Supporting Framework") }}</option>
							</select>
						</div>
						<div class="kt-field" style="grid-column: 1 / -1">
							<label>{{ __("Plan title") }}</label>
							<input v-model="draft.title" class="kt-input" type="text" data-testid="str-plan-title" />
							<p v-if="fieldErrors.title" class="kt-field-error" data-testid="str-field-error-title">{{ fieldErrors.title }}</p>
						</div>
						<div v-if="draft.plan_role === 'Supporting Framework'" class="kt-field" style="grid-column: 1 / -1">
							<label>{{ __("Governing Primary plan") }}</label>
							<select v-model="draft.parent_primary_plan_id" class="kt-input" data-testid="str-plan-parent">
								<option value="">{{ __("Select a Primary plan") }}</option>
								<option v-for="p in primaryPlans" :key="p.id" :value="p.id">{{ p.title }} · {{ p.reference }}</option>
							</select>
							<p v-if="fieldErrors.parent_primary_plan_id" class="kt-field-error" data-testid="str-field-error-parent">{{ fieldErrors.parent_primary_plan_id }}</p>
						</div>
						<div class="kt-field">
							<label>{{ __("Plan period start") }}</label>
							<input v-model="draft.period_start" class="kt-input" type="date" data-testid="str-period-start" />
							<p v-if="fieldErrors.period_start" class="kt-field-error" data-testid="str-field-error-period-start">{{ fieldErrors.period_start }}</p>
						</div>
						<div class="kt-field">
							<label>{{ __("Plan period end") }}</label>
							<input v-model="draft.period_end" class="kt-input" type="date" data-testid="str-period-end" />
							<p v-if="fieldErrors.period_end" class="kt-field-error" data-testid="str-field-error-period-end">{{ fieldErrors.period_end }}</p>
						</div>
					</div>
					<p v-if="saveError" data-testid="str-save-error" style="color: oklch(0.45 0.13 28)">{{ saveError }}</p>
				</div>
			</div>
			<div class="kt-sticky-footer">
				<button type="button" class="kt-btn kt-btn-ghost" data-testid="str-cancel-draft" @click="go()">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="saving" data-testid="str-save-draft" @click="submitDraft">
					{{ __("Save draft") }}
				</button>
			</div>
		</template>
	</div>
</template>
