<!-- Contracts — CM-CHG-001 v0.8 §9.0, §10.3. One Desk Page ("contracts") for the workspace (/app/contracts); the contract and its five tabs arrive with the formation
     package. The app stays mounted across navigations (AGENTS.md §6.1). One loader with a sequence guard; the page revalidates in place when it comes back into view.
     The server decides what a viewer may read; this screen only draws its answer: the workspace, the stable denial (D-DENIED) or the load failure (D-ERR). -->
<template>
	<div class="kt-industry kt-cm">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" data-testid="cm-root" :data-screen="screen" :data-loading="loading ? 'true' : 'false'" :data-refreshing="refreshing ? 'true' : 'false'">
			<div class="kt-page">
				<AccessDenied
					v-if="screen === 'workspace-forbidden'"
					heading="You do not have access to Contracts"
					:text="['This area needs a contract responsibility, a supplier account or a technical reader role.', 'Ask your KenTender administrator to check your assignment in System setup.']"
				/>
				<StatePage
					v-else-if="screen === 'error'"
					tone="error"
					message="This record could not be loaded."
					primary="Retry"
					:secondary="['Back to contracts']"
					:busy="loading"
					testid="cm-load-error"
					@primary="load()"
					@secondary="backToContracts"
				/>
				<div v-else-if="screen === 'workspace' && !total" class="kt-empty" data-testid="cm-empty">
					<span class="kt-spot is-neutral" aria-hidden="true">
						<svg class="kt-icon" viewBox="0 0 24 24"><path d="M6 3h9l4 4v14H6z" /><path d="M14 3v5h5" /></svg>
					</span>
					<h2>{{ __("Contracts") }}</h2>
					<p>{{ __("There are no contracts to show yet.") }}</p>
				</div>
				<ul v-else-if="screen === 'workspace'" data-testid="cm-list">
					<li v-for="row in rows" :key="row.case">{{ row.case }}</li>
				</ul>
				<div v-else class="kt-skel" data-testid="cm-skeleton" style="width: 100%" aria-busy="true"></div>
			</div>
		</div>
	</div>
</template>

<script setup>
import { computed, ref, watch } from "vue";
import * as api from "./data/api.js";
import { useRouteState } from "./composables/useRouteState.js";
import { usePageRail } from "./composables/usePageRail.js";
import AccessDenied from "../access_shared/AccessDenied.vue";
import StatePage from "./components/StatePage.vue";

const PAGE = "contracts";
const { epoch } = useRouteState(PAGE);

const railEl = ref(null);
const payload = ref(null);
const loading = ref(false);
const failed = ref(false);
let seq = 0; // a slower, older response must never overwrite a newer one (AGENTS.md §6.4)

// The skeleton is only for a screen with nothing to show yet; a screen already loaded refreshes in place.
const screen = computed(() => (failed.value && !payload.value ? "error" : payload.value ? payload.value.screen : "loading"));
const refreshing = computed(() => loading.value && !!payload.value);
const total = computed(() => (payload.value && payload.value.total) || 0);
const rows = computed(() => (payload.value && payload.value.rows) || []);

async function load() {
	const token = ++seq;
	loading.value = true;
	try {
		const answer = await api.getWorkspace();
		if (token !== seq) return;
		payload.value = answer;
		failed.value = false;
	} catch (error) {
		if (token !== seq) return;
		failed.value = true;
	} finally {
		if (token === seq) loading.value = false;
	}
}

function backToContracts() {
	frappe.set_route("contracts");
	load();
}

load();
// The page coming back into view on the same route revalidates what it already shows, quietly.
watch(epoch, () => load());

const railTrail = computed(() => [{ label: __("Home"), route: ["home"] }, { label: __("Contracts") }]);
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
