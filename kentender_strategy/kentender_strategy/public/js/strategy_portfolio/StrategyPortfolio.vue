<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { useRouteState } from "../strategy_shared/composables/useRouteState.js";
import { usePageRail } from "../strategy_shared/composables/usePageRail.js";
import { fetchPortfolio, saveNewPlanDraft } from "./data/strategyPortfolioApi.js";

const { route, go } = useRouteState("strategy-portfolio");
const mode = computed(() => (route.value[1] === "new" ? "create" : "list"));

const railTrail = computed(() => {
	const items = [{ label: __("Home"), route: ["Workspaces", "Procurement Home"] }];
	if (mode.value === "create") {
		items.push({ label: __("Strategy Alignment"), route: ["strategy-portfolio"] });
		items.push({ label: __("New strategic plan") });
	} else {
		items.push({ label: __("Strategy Alignment") });
	}
	return items;
});
const railEl = ref(null);
usePageRail(railEl, railTrail);

const loading = ref(true);
const error = ref(null);
const forbidden = ref(false);
const plans = ref([]);
const myWork = ref([]);
const procuringEntity = ref(null);
const activeTab = ref("plans");

const filters = reactive({ q: "", role: "", status: "" });

async function refresh() {
	loading.value = true;
	error.value = null;
	forbidden.value = false;
	try {
		const data = await fetchPortfolio();
		if (data.forbidden) {
			forbidden.value = true;
		} else {
			plans.value = data.plans;
			myWork.value = data.my_work;
			procuringEntity.value = data.procuring_entity;
		}
	} catch (e) {
		error.value = e;
	} finally {
		loading.value = false;
	}
}
onMounted(refresh);
watch(mode, (m) => {
	if (m === "list") refresh();
});

const roleOptions = computed(() => [...new Set(plans.value.map((p) => p.plan_role))].sort());
const statusOptions = computed(() =>
	[...new Set(plans.value.map((p) => p.status))].sort()
);

const filteredPlans = computed(() => {
	const needle = filters.q.trim().toLowerCase();
	return plans.value.filter((p) => {
		if (
			needle &&
			!(p.title.toLowerCase().includes(needle) || (p.reference || "").toLowerCase().includes(needle))
		)
			return false;
		if (filters.role && p.plan_role !== filters.role) return false;
		if (filters.status && p.status !== filters.status) return false;
		return true;
	});
});

function clearFilters() {
	filters.q = "";
	filters.role = "";
	filters.status = "";
}

function statusClass(status) {
	if (status === "Active") return "is-live";
	if (["In Review", "Awaiting Approval", "Approved"].includes(status)) return "is-pending";
	return "is-draft";
}

function openPlan(plan) {
	frappe.set_route(plan.action_route || "strategy-plan-workspace", plan.action_target_id || plan.id);
}

function openMyWorkItem(item) {
	frappe.set_route("strategy-review-task", item.version_id);
}

// --- New strategic plan draft form (STR-DES-02) ---
const draft = reactive({
	title: "",
	plan_role: "Primary",
	period_start: "",
	period_end: "",
});
const saving = ref(false);
const saveError = ref(null);

function openCreateForm() {
	draft.title = "";
	draft.plan_role = "Primary";
	draft.period_start = "";
	draft.period_end = "";
	saveError.value = null;
	go("new");
}

async function submitDraft() {
	if (!procuringEntity.value) {
		saveError.value = "No Procuring Entity is available for your account to create a plan under.";
		return;
	}
	saving.value = true;
	saveError.value = null;
	try {
		const result = await saveNewPlanDraft({
			procuring_entity_id: procuringEntity.value.id,
			plan_role: draft.plan_role,
			title: draft.title,
			period_start: draft.period_start,
			period_end: draft.period_end,
		});
		frappe.show_alert({ message: __("Plan draft saved"), indicator: "green" });
		frappe.set_route("strategy-plan-workspace", result.plan.plan_id);
	} catch (e) {
		saveError.value = e.message || "Could not save the draft.";
	} finally {
		saving.value = false;
	}
}
</script>

<template>
	<div class="kt-industry">
		<div ref="railEl" class="kt-rail-mount"></div>
		<template v-if="mode === 'list'">
			<div class="kt-shell">
				<header style="display: flex; justify-content: space-between; align-items: flex-end; gap: 16px">
					<div>
						<div
							style="
								text-transform: uppercase;
								font-size: 11px;
								letter-spacing: 0.08em;
								color: var(--kt-color-accent);
								margin-bottom: 6px;
							"
						>
							{{ __("Strategy Alignment") }}
						</div>
						<h1 style="font-size: 32px">{{ __("Strategy Portfolio") }}</h1>
						<p class="kt-muted" style="margin-top: 6px">
							{{ __("Maintain the approved strategy structure used by Budget and Procurement Planning.") }}
						</p>
					</div>
					<button type="button" class="kt-btn kt-btn-primary" @click="openCreateForm" v-if="!forbidden">
						{{ __("New strategic plan") }}
					</button>
				</header>

				<div v-if="procuringEntity" class="kt-card" style="padding: 10px 16px">
					<span class="kt-muted">{{ __("Procuring Entity") }}: </span>
					<strong>{{ procuringEntity.name }}</strong>
				</div>

				<div class="kt-tabs">
					<div class="kt-tab" :aria-selected="activeTab === 'plans'" @click="activeTab = 'plans'">{{ __("Plans") }} <span class="kt-count">{{ plans.length }}</span></div>
					<div class="kt-tab" :aria-selected="activeTab === 'my-work'" @click="activeTab = 'my-work'">{{ __("My work") }} <span class="kt-count">{{ myWork.length }}</span></div>
				</div>

				<div v-if="forbidden" class="kt-card kt-empty">
					<h2>{{ __("You do not have access to Strategy Alignment.") }}</h2>
					<p>{{ __("Ask your KenTender administrator to review your Strategy assignment.") }}</p>
				</div>

				<div v-else-if="error" class="kt-card kt-empty">
					<h2>{{ __("Strategy plans could not be loaded.") }}</h2>
					<p>{{ __("Try again. If the problem continues, contact KenTender support.") }}</p>
					<button type="button" class="kt-btn kt-btn-secondary" @click="refresh">{{ __("Try again") }}</button>
				</div>

				<div v-else-if="!loading && activeTab === 'plans' && plans.length === 0" class="kt-card kt-empty">
					<h2>{{ __("No strategic plans exist for this scope.") }}</h2>
					<button type="button" class="kt-btn kt-btn-secondary" @click="openCreateForm" v-if="!forbidden">
						{{ __("New strategic plan") }}
					</button>
				</div>

				<template v-else-if="activeTab === 'plans'">
					<div style="display: flex; gap: 12px">
						<input
							v-model="filters.q"
							class="kt-input"
							style="flex: 1"
							:placeholder="__('Search plan or reference')"
							:disabled="loading"
						/>
						<select v-model="filters.role" class="kt-input" style="width: 190px" :disabled="loading">
							<option value="">{{ __("All plan roles") }}</option>
							<option v-for="r in roleOptions" :key="r" :value="r">{{ r }}</option>
						</select>
						<select v-model="filters.status" class="kt-input" style="width: 170px" :disabled="loading">
							<option value="">{{ __("All statuses") }}</option>
							<option v-for="s in statusOptions" :key="s" :value="s">{{ s }}</option>
						</select>
					</div>

					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div v-if="loading">
							<div
								v-for="i in 5"
								:key="i"
								class="kt-skel" style="height: 16px; margin-bottom: 10px"
							></div>
						</div>
						<div v-else-if="filteredPlans.length === 0 && plans.length > 0" class="kt-empty">
							<h2>{{ __("No plans match these filters.") }}</h2>
							<p>{{ __("Change or clear the filters to see other strategic plans.") }}</p>
							<button type="button" class="kt-btn kt-btn-secondary" @click="clearFilters">
								{{ __("Clear filters") }}
							</button>
						</div>
						<table v-else class="kt-table">
							<thead>
								<tr>
									<th>{{ __("Strategic plan") }}</th>
									<th>{{ __("Role") }}</th>
									<th>{{ __("Period") }}</th>
									<th>{{ __("Current version") }}</th>
									<th>{{ __("Status") }}</th>
									<th></th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="p in filteredPlans" :key="p.id">
									<td>
										<div>{{ p.title }}</div>
										<div class="kt-muted">{{ p.reference }}</div>
									</td>
									<td>{{ p.plan_role }}</td>
									<td>{{ p.period_label || "—" }}</td>
									<td>{{ p.current_version ? `Version ${p.current_version.version_number}` : "—" }}</td>
									<td><span class="kt-status" :class="statusClass(p.status)">{{ p.status }}</span></td>
									<td><a href="#" @click.prevent="openPlan(p)">{{ p.available_action || __("View") }}</a></td>
								</tr>
							</tbody>
						</table>
					</div>
					<div class="kt-muted">
						{{ __("Showing {0} of {1} plan(s)", [filteredPlans.length, plans.length]) }}
					</div>
				</template>

				<template v-else>
					<div class="kt-card kt-blueprint">
						<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
						<div v-if="loading">
							<div
								v-for="i in 5"
								:key="i"
								class="kt-skel" style="height: 16px; margin-bottom: 10px"
							></div>
						</div>
						<div v-else-if="myWork.length === 0" class="kt-empty">
							<h2>{{ __("Nothing needs your action right now.") }}</h2>
						</div>
						<table v-else class="kt-table">
							<thead>
								<tr>
									<th>{{ __("Strategic plan") }}</th>
									<th>{{ __("Version") }}</th>
									<th>{{ __("Status") }}</th>
									<th></th>
								</tr>
							</thead>
							<tbody>
								<tr v-for="w in myWork" :key="w.version_id">
									<td>
										<div>{{ w.plan_title }}</div>
										<div class="kt-muted">{{ w.plan_reference }}</div>
									</td>
									<td>{{ __("Version") }} {{ w.version_number }}</td>
									<td><span class="kt-status" :class="statusClass(w.status)">{{ w.status }}</span></td>
									<td><a href="#" @click.prevent="openMyWorkItem(w)">{{ __("Review") }}</a></td>
								</tr>
							</tbody>
						</table>
					</div>
					<div class="kt-muted">{{ __("Showing {0} item(s)", [myWork.length]) }}</div>
				</template>
			</div>
		</template>

		<template v-else>
			<div class="kt-shell" style="padding-bottom: 90px">
				<header>
					<h1 style="font-size: 28px">{{ __("New strategic plan") }} <span class="kt-status is-draft">{{ __("Draft") }}</span></h1>
				</header>
				<div class="kt-card kt-blueprint" style="max-width: 720px">
					<i class="kt-corner tl"></i><i class="kt-corner tr"></i><i class="kt-corner bl"></i><i class="kt-corner br"></i>
					<div class="kt-card-title">{{ __("Plan identity") }}</div>
					<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px">
						<div class="kt-field">
							<label>{{ __("Plan reference") }}</label>
							<div class="kt-input" style="background: color-mix(in srgb, var(--kt-color-text) 6%, transparent)">{{ __("Not assigned") }}</div>
						</div>
						<div class="kt-field">
							<label>{{ __("Procuring Entity") }}</label>
							<div class="kt-input" style="background: color-mix(in srgb, var(--kt-color-text) 6%, transparent)">
								{{ procuringEntity ? procuringEntity.name : __("Unavailable") }}
							</div>
						</div>
						<div class="kt-field">
							<label>{{ __("Organisation scope") }}</label>
							<select class="kt-input" disabled><option>{{ __("PE-wide") }}</option></select>
						</div>
						<div class="kt-field">
							<label>{{ __("Plan role") }}</label>
							<select v-model="draft.plan_role" class="kt-input">
								<option value="Primary">{{ __("Primary") }}</option>
								<option value="Supporting Framework">{{ __("Supporting Framework") }}</option>
							</select>
						</div>
						<div class="kt-field" style="grid-column: 1 / -1">
							<label>{{ __("Plan title") }}</label>
							<input v-model="draft.title" class="kt-input" type="text" />
						</div>
						<div class="kt-field">
							<label>{{ __("Plan period start") }}</label>
							<input v-model="draft.period_start" class="kt-input" type="date" />
						</div>
						<div class="kt-field">
							<label>{{ __("Plan period end") }}</label>
							<input v-model="draft.period_end" class="kt-input" type="date" />
						</div>
					</div>
					<p v-if="saveError" style="color: oklch(0.45 0.13 28)">{{ saveError }}</p>
				</div>
			</div>
			<div class="kt-sticky-footer">
				<button type="button" class="kt-btn kt-btn-ghost" @click="go()">{{ __("Cancel") }}</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="saving" @click="submitDraft">
					{{ __("Save draft") }}
				</button>
			</div>
		</template>
	</div>
</template>
