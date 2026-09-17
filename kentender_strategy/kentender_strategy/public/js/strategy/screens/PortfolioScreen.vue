<script setup>
// STR-UI-01 Strategic plans (STR-DES-01 / STR-DES-02 / STR-DES-10). Routes:
//   /app/strategy            Plans tab
//   /app/strategy/my-work    Actions tab (route slug kept as "my-work" — the
//                            shared My Work aggregator's own name; the
//                            displayed label is the neutral "Actions", FU-07)
//   /app/strategy/new        Create strategic plan
import { ref, reactive, computed, onMounted, onActivated, watch } from "vue";
import { useRouteState } from "../../strategy_shared/composables/useRouteState.js";
import { usePageRail } from "../../strategy_shared/composables/usePageRail.js";
import { runAttempt } from "../../strategy_shared/data/attempts.js";
import { fetchPortfolio, savePlanDraft } from "../data/strategyApi.js";

const { route, go, epoch } = useRouteState("strategy");
const mode = computed(() => (route.value[1] === "new" ? "create" : "list"));
const activeTab = computed(() => (route.value[1] === "my-work" ? "my-work" : "plans"));

const railTrail = computed(() => {
	const items = [{ label: __("Home"), route: ["Workspaces", "Procurement Home"] }];
	if (mode.value === "create") {
		items.push({ label: __("Strategy Alignment"), route: ["strategy"] });
		items.push({ label: __("Create strategic plan") });
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
const statusOptions = ref([]);
const planTypeOptions = ref([]);
const loadedOnce = ref(false);

// §12.1 — search matches reference and title; plan type and status are
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
			statusOptions.value = data.status_options || [];
			planTypeOptions.value = data.plan_type_options || [];
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

function openRoute(routeArray) {
	if (Array.isArray(routeArray) && routeArray.length) frappe.set_route(...routeArray);
}

// --- Create strategic plan (STR-DES-02) ------------------------------------
const draft = reactive({ title: "", plan_role: "Primary", parent_primary_plan_id: "", period_start: "", period_end: "" });
const saving = ref(false);
const saveError = ref(null);
const savedDraftRoute = ref(null);
const unknownOutcome = ref(false);
const fieldErrors = reactive({ title: "", parent_primary_plan_id: "", period_start: "", period_end: "" });
function validateDraft() {
	fieldErrors.title = draft.title.trim() ? "" : __("Enter a plan title.");
	fieldErrors.parent_primary_plan_id =
		draft.plan_role === "Supporting Framework" && !draft.parent_primary_plan_id ? __("Select the main plan this framework sits under.") : "";
	fieldErrors.period_start = draft.period_start ? "" : __("Enter the start date.");
	fieldErrors.period_end = !draft.period_end
		? __("Enter the end date.")
		: draft.period_start && draft.period_end <= draft.period_start
		? __("The end date must be later than the start date.")
		: "";
	return !Object.values(fieldErrors).some(Boolean);
}
const primaryPlans = computed(() => plans.value.filter((p) => p.plan_role === "Primary"));

function openCreateForm() {
	Object.assign(draft, { title: "", plan_role: "Primary", parent_primary_plan_id: "", period_start: "", period_end: "" });
	Object.assign(fieldErrors, { title: "", parent_primary_plan_id: "", period_start: "", period_end: "" });
	saveError.value = null;
	savedDraftRoute.value = null;
	go("new");
}

const canCreatePlan = computed(() => !forbidden.value && canCreate.value);

// §8.2/§12.2 — one attempt identity; a confirmed save followed by a failed
// navigation offers "Open saved draft" for that exact identity; an unknown
// outcome replays the same request instead of creating again.
async function submitDraft() {
	if (!validateDraft()) return;
	saving.value = true;
	saveError.value = null;
	unknownOutcome.value = false;
	try {
		const result = await runAttempt(
			"create-plan",
			(key) =>
				savePlanDraft(
					{
						plan_role: draft.plan_role,
						parent_primary_plan_id: draft.plan_role === "Supporting Framework" ? draft.parent_primary_plan_id || null : null,
						title: draft.title,
						period_start: draft.period_start,
						period_end: draft.period_end,
						// §12.2 — the first version inherits the plan period.
						effective_from: draft.period_start,
						effective_to: draft.period_end,
					},
					null,
					key
				),
			{ onUnknown: () => (unknownOutcome.value = true) }
		);
		unknownOutcome.value = false;
		const target = ["strategy", "plan", result.plan.plan_reference, "version", String(result.version.version_number || 1), "structure"];
		savedDraftRoute.value = target;
		frappe.show_alert({ message: __("Plan created"), indicator: "green" });
		frappe.set_route(...target);
	} catch (e) {
		saveError.value = e.unknownOutcome
			? __("We could not confirm the result. Checking the existing request…")
			: e.message || __("Your changes were not saved.");
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
			<!-- KT-STD-001 §3A.1: nothing but the verdict's own state paints. -->
			<div v-if="loading" class="kt-card kt-blueprint" style="padding: 0" data-testid="str-loading">
				<div style="padding: 13.6px 13.6px 0">
					<h2 style="font-size: 19px; margin: 0">{{ __("Strategic plans") }}</h2>
					<p class="kt-muted" style="font-size: 12px; margin: 4px 0 0">{{ __("Loading strategic plans…") }}</p>
				</div>
				<div style="display: flex; flex-direction: column; gap: 6px; padding: 13.6px">
					<div v-for="i in 3" :key="i" class="kt-skel" style="height: 32px"></div>
				</div>
			</div>

			<div v-else-if="forbidden" class="kt-notice is-critical" data-testid="str-forbidden">
				<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>
				<div class="kt-notice-body">
					<strong>{{ __("You do not have access to Strategy Alignment.") }}</strong>
					{{ __("This area needs Strategy Author, Strategy Approver or Auditor responsibility, or Administrator/System Manager technical access. Ask your KenTender administrator to check your access in System setup.") }}
				</div>
			</div>

			<div v-else-if="error && !loadedOnce" data-testid="str-error">
				<div class="kt-notice is-warning">
					<svg class="kt-notice-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
					<div class="kt-notice-body"><strong>{{ __("Strategy information could not be loaded.") }}</strong> {{ __("Try again. If the problem continues, contact KenTender support.") }}</div>
				</div>
				<div style="margin-top: 10px"><button type="button" class="kt-btn kt-btn-secondary" @click="refresh">{{ __("Try again") }}</button></div>
			</div>

			<template v-else>
				<!-- The title, the tabs and the table below now sit inside one
				     bordered panel instead of floating as separate boxes, matching
				     the current design. -->
				<div class="kt-card kt-blueprint" style="padding: 0">
					<header style="display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; padding: 20.4px 20.4px 0">
						<div>
							<div class="kt-eyebrow" style="text-transform: uppercase; font-size: 11px; letter-spacing: 0.1em; color: var(--kt-color-accent); margin-bottom: 6px">
								{{ __("Strategy Alignment") }}
							</div>
							<h1 style="font-size: 30px; margin: 0">{{ __("Strategic plans") }}</h1>
							<p style="color: var(--kt-color-neutral-800); font-size: 14px; margin: 6.8px 0 20.4px; max-width: 640px">
								{{ __("Create and maintain the strategy used for budget and procurement planning.") }}
							</p>
						</div>
						<button v-if="canCreatePlan" type="button" class="kt-btn kt-btn-primary" style="margin-top: 2px" data-testid="str-new-plan" @click="openCreateForm">
							{{ __("Create strategic plan") }}
						</button>
					</header>

					<div class="kt-tabs" role="tablist" style="padding: 0 20.4px">
						<button type="button" role="tab" class="kt-tab" data-testid="str-tab-plans" :aria-selected="activeTab === 'plans'" @click="go()">
							{{ __("Plans") }} <span class="kt-count">{{ plans.length }}</span>
						</button>
						<button type="button" role="tab" class="kt-tab" data-testid="str-tab-my-work" :aria-selected="activeTab === 'my-work'" @click="go('my-work')">
							{{ __("Actions") }} <span class="kt-count">{{ myWork.length }}</span>
						</button>
					</div>

					<p v-if="error" class="kt-muted" data-testid="str-refresh-error" style="margin: 13.6px 20.4px 0">{{ __("The list could not be refreshed. Showing the last loaded plans.") }}</p>

					<template v-if="activeTab === 'plans'">
						<div v-if="plans.length === 0 && !filtersActive" style="padding: 20.4px 20.4px 27.2px; text-align: center; font-size: 13px; color: var(--kt-color-neutral-700)" data-testid="str-empty">
							{{ canCreatePlan ? __("No strategic plans exist yet.") : __("No strategic plans to display.") }}
						</div>
						<template v-else>
							<div style="display: flex; gap: 10.2px; padding: 13.6px 20.4px">
								<input v-model="filters.q" class="kt-input" style="flex: 1" data-testid="str-search" :placeholder="__('Search plan or reference')" :aria-label="__('Search plan or reference')" />
								<select v-model="filters.role" class="kt-input" style="width: 200px" data-testid="str-role-filter" :aria-label="__('Plan type')">
									<option value="">{{ __("All plan types") }}</option>
									<option v-for="o in planTypeOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
								</select>
								<select v-model="filters.status" class="kt-input" style="width: 180px" data-testid="str-status-filter" :aria-label="__('Status')">
									<option value="">{{ __("All statuses") }}</option>
									<option v-for="o in statusOptions" :key="o.value" :value="o.value">{{ o.label }}</option>
								</select>
							</div>
							<div v-if="plans.length === 0" style="padding: 20.4px 13.6px; text-align: center" data-testid="str-no-match">
								<div style="font-family: var(--kt-font-heading); font-weight: 600; font-size: 15px; margin-bottom: 4px">{{ __("No plans match these filters.") }}</div>
								<div style="font-size: 13px; color: var(--kt-color-neutral-700); margin-bottom: 10px">{{ __("Change or clear the filters to see other strategic plans.") }}</div>
								<button type="button" class="kt-btn kt-btn-secondary" data-testid="str-clear-filters" @click="clearFilters">{{ __("Clear filters") }}</button>
							</div>
							<template v-else>
								<table class="kt-table" data-testid="str-plans-table">
									<thead>
										<tr>
											<th>{{ __("Strategic plan") }}</th>
											<th>{{ __("Plan type") }}</th>
											<th>{{ __("Period") }}</th>
											<th>{{ __("Version") }}</th>
											<th>{{ __("Status") }}</th>
											<th>{{ __("Action") }}</th>
										</tr>
									</thead>
									<tbody>
										<tr v-for="p in plans" :key="p.id" data-testid="str-plan-row" :data-plan-reference="p.reference">
											<td>{{ p.title }} <span class="kt-muted">&middot; {{ p.reference }}</span></td>
											<td>{{ p.plan_type_label }}</td>
											<td>{{ p.period_fy_label || p.period_label || "—" }}</td>
											<td>{{ p.current_version ? p.current_version.version_number : "—" }}</td>
											<td><span class="kt-status" :class="p.status_tone" data-testid="str-row-status">{{ p.status_label }}</span></td>
											<td><a href="#" class="kt-btn kt-btn-ghost" style="padding: 4px 10px; height: auto" data-testid="str-row-action" @click.prevent="openRoute(p.action_route)">{{ p.available_action || __("View") }}</a></td>
										</tr>
									</tbody>
								</table>
								<div style="padding: 10.2px 20.4px" data-testid="str-count-label">
									<span style="font-size: 12px; color: var(--kt-color-neutral-700)">{{ plans.length === 1 ? __("Showing 1 of 1 plan") : __("Showing {0} of {1} plans", [plans.length, plans.length]) }}</span>
								</div>
							</template>
						</template>
					</template>

					<template v-else>
						<div v-if="myWork.length === 0" style="padding: 20.4px 20.4px 27.2px; text-align: center; font-size: 13px; color: var(--kt-color-neutral-700)" data-testid="str-my-work-empty">
							{{ __("Nothing needs your action right now.") }}
						</div>
						<template v-else>
							<table class="kt-table" data-testid="str-my-work-table">
								<thead>
									<tr>
										<th>{{ __("Plan") }}</th>
										<th>{{ __("Review") }}</th>
										<th>{{ __("Submitted by") }}</th>
										<th>{{ __("Submitted") }}</th>
										<th>{{ __("Status") }}</th>
										<th>{{ __("Action") }}</th>
									</tr>
								</thead>
								<tbody>
									<tr v-for="w in myWork" :key="w.version_id" data-testid="str-my-work-row" :data-version-reference="w.version_reference">
										<td>{{ w.plan_title }} <span class="kt-muted">&middot; {{ w.plan_reference }} &middot; {{ __("Version") }} {{ w.version_number }}</span></td>
										<td>{{ w.review_type }}</td>
										<td>{{ w.submitted_by || "—" }}</td>
										<td>{{ w.submitted_at_label || "—" }}</td>
										<td><span class="kt-status" :class="w.status_tone">{{ w.status_label }}</span></td>
										<td><a href="#" class="kt-btn kt-btn-ghost" style="padding: 4px 10px; height: auto" data-testid="str-my-work-action" @click.prevent="openRoute(w.action_route)">{{ w.action_label }}</a></td>
									</tr>
								</tbody>
							</table>
							<div style="padding: 10.2px 20.4px; font-size: 12px; color: var(--kt-color-neutral-700)">{{ __("Showing {0} item(s)", [myWork.length]) }}</div>
						</template>
					</template>
				</div>
			</template>
		</template>

		<template v-else>
			<div style="padding-bottom: 90px; max-width: 820px">
				<h1 style="font-size: 30px; margin: 0 0 8px">{{ __("Create strategic plan") }}</h1>
				<p style="color: var(--kt-color-neutral-800); font-size: 14px; margin: 0 0 20.4px; max-width: 560px">{{ __("Enter the plan details, then add its objectives and targets.") }}</p>
				<div class="kt-card kt-blueprint" style="max-width: 640px" data-testid="str-new-plan-form">
					<div class="kt-card-title">{{ __("Plan identity") }}</div>
					<div style="display: grid; gap: 13.6px">
						<div class="kt-field">
							<label for="str-plan-title">{{ __("Plan title") }}</label>
							<input id="str-plan-title" v-model="draft.title" class="kt-input" type="text" data-testid="str-plan-title" :aria-invalid="fieldErrors.title ? 'true' : 'false'" />
							<p v-if="fieldErrors.title" class="kt-field-error" data-testid="str-field-error-title">{{ fieldErrors.title }}</p>
						</div>
						<div class="kt-field">
							<label for="str-plan-role">{{ __("Plan type") }}</label>
							<select id="str-plan-role" v-model="draft.plan_role" class="kt-input" style="max-width: 260px" data-testid="str-plan-role">
								<option value="Primary">{{ __("Main strategic plan") }}</option>
								<option value="Supporting Framework">{{ __("Supporting framework") }}</option>
							</select>
						</div>
						<div v-if="draft.plan_role === 'Supporting Framework'" class="kt-field">
							<label for="str-plan-parent">{{ __("Main plan") }}</label>
							<select id="str-plan-parent" v-model="draft.parent_primary_plan_id" class="kt-input" data-testid="str-plan-parent">
								<option value="">{{ __("Select a main strategic plan") }}</option>
								<option v-for="p in primaryPlans" :key="p.id" :value="p.id">{{ p.title }} · {{ p.reference }}</option>
							</select>
							<div class="kt-field-hint">{{ __("A supporting framework sits under a main strategic plan.") }}</div>
							<p v-if="fieldErrors.parent_primary_plan_id" class="kt-field-error" data-testid="str-field-error-parent">{{ fieldErrors.parent_primary_plan_id }}</p>
						</div>
						<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 13.6px">
							<div class="kt-field">
								<label for="str-period-start">{{ __("Start date") }}</label>
								<input id="str-period-start" v-model="draft.period_start" class="kt-input" type="date" data-testid="str-period-start" />
								<p v-if="fieldErrors.period_start" class="kt-field-error" data-testid="str-field-error-period-start">{{ fieldErrors.period_start }}</p>
							</div>
							<div class="kt-field">
								<label for="str-period-end">{{ __("End date") }}</label>
								<input id="str-period-end" v-model="draft.period_end" class="kt-input" type="date" data-testid="str-period-end" />
								<p v-if="fieldErrors.period_end" class="kt-field-error" data-testid="str-field-error-period-end">{{ fieldErrors.period_end }}</p>
							</div>
						</div>
					</div>
					<p v-if="saveError" class="kt-field-error" data-testid="str-save-error" style="font-size: 14px">{{ saveError }}</p>
					<p v-if="savedDraftRoute" data-testid="str-open-saved-draft" style="font-size: 14px; margin: 0">
						{{ __("The plan was created.") }}
						<a href="#" @click.prevent="openRoute(savedDraftRoute)">{{ __("Open saved draft") }}</a>
					</p>
				</div>
			</div>
			<div class="kt-sticky-footer">
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="str-cancel-draft" @click="go()">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="saving" data-testid="str-save-draft" @click="submitDraft">
					{{ __("Create plan and add objectives") }}
				</button>
			</div>
		</template>
	</div>
</template>
