<!-- Bid evaluation workspace — EVL-CHG-001 v0.4 §9.2, §10 (boards D01, D01-EMPTY,
     D01-FILTERED, D01-APPOINT, D01-APPOINT-HOP, S-FORBIDDEN):
       /app/bid-evaluation
     The viewer's own evaluation tasks, then the register of evaluations they
     may read, with a local search and state filter (ListEvaluationWork). No
     tracker or next step on the workspace; a task opens its evaluation. -->
<template>
	<div class="kt-industry kt-evl-ws">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" data-testid="evl-workspace" :data-loading="loading ? 'true' : 'false'">
			<EvlBoard :board="board" :form="form" :pending="false" :error="error" @action="onAction" @update="onUpdate" />
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import { frappeCall } from "../data/frappeCall.js";
import EvlBoard from "../board/EvlBoard.vue";
import { workspaceBoard } from "../screens/workspace.js";
import { usePageRail } from "../../tnd_shared/composables/usePageRail.js";

const railEl = ref(null);
const loading = ref(true);
const error = ref("");
const forbidden = ref(false);
const work = ref({ tasks: [], register: [], total: 0 });
const form = reactive({ query: "", state: "" });
let seq = 0;

async function load() {
	const token = ++seq;
	try {
		const out = await frappeCall("kentender_procurement.bid_evaluation.api.list_work", { query: form.query || "", state: form.state || "" }, "GET");
		if (token !== seq) return;
		work.value = out;
		forbidden.value = !!out.forbidden;
		error.value = "";
	} catch (e) {
		if (token !== seq) return;
		if (e.httpStatus === 403) forbidden.value = true;
		else error.value = "We could not load your evaluations.";
	} finally {
		if (token === seq) loading.value = false;
	}
}
load();
let timer = null;
watch(() => [form.query, form.state], () => {
	clearTimeout(timer);
	timer = setTimeout(load, 250);
});

const board = computed(() => workspaceBoard({ work: forbidden.value ? { forbidden: true } : work.value, form, loading: loading.value }));

function onUpdate({ name, value }) {
	form[name] = value;
}

function onAction({ action, args }) {
	if (action === "open" && args && args.route) frappe.set_route(...args.route);
	if (action === "clear") Object.assign(form, { query: "", state: "" });
	if (action === "reload") load();
}

const railTrail = computed(() => [{ label: __("Home"), route: ["Workspaces", "Procurement Home"] }, { label: "Bid evaluation" }]);
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
