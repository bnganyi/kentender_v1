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
import { em, fb, task, tb } from "../board/model.js";
import { usePageRail } from "../../tnd_shared/composables/usePageRail.js";

const STATES = ["All states", "Preparing", "Reviewing", "Signing", "Report sent", "No evaluation required", "Cancelled"];
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

const titleOf = (ref_) => (work.value.register.find((r) => r.tender === ref_) || {}).title || "";

const board = computed(() => {
	const head = { title: "Bid evaluation", desc: "Review automatic checks, resolve questions and prepare the committee report.", icon: undefined };
	if (forbidden.value) {
		return { ...head, blocks: [em("You do not have access to Bid evaluation.", null, "ban", "This area needs one of these responsibilities: Accounting Officer, Head of Procurement, appointed evaluation member, evaluation secretary or authorised auditor. Ask your KenTender administrator to assign the appropriate responsibility in System setup; committee membership also requires appointment.")] };
	}
	if (loading.value) return { ...head, blocks: [em("Loading evaluations…", null, "loader")] };
	const blocks = (work.value.tasks || []).map((t) => task(t.title, titleOf(t.reference) || t.reference, t.status === "Assigned" ? stateOf(t.reference) : t.status,
		{ label: t.action_label || "Open evaluation", action: "open", args: { route: t.route } }));
	blocks.push(fb([["Find a tender", form.query, { wide: true, ph: "Find a tender", name: "query" }], ["State", form.state, { select: true, name: "state", options: STATES.map((s) => ({ value: s === "All states" ? "" : s, label: s })) }]],
		{ title: "Evaluations", sec: true }));
	const rows = work.value.register || [];
	if (rows.length) blocks.push(tb(["Tender", "Title", "Work state", "Action"], rows.map((r) => [r.tender, r.title, r.state, { label: "View", action: "open", args: { route: ["tenders", r.tender, "evaluation"] }, testid: `evl-view-${r.tender}` }]), { testid: "evl-register" }));
	else if (form.query || form.state) blocks.push({ ...em("No evaluations match your search.", "Clear search", "search"), btnAction: "clear" });
	else blocks.push(em("No evaluations are assigned to you.", null, "clipboard"));
	return { ...head, blocks };
});

function stateOf(reference) {
	return (work.value.register.find((r) => r.tender === reference) || {}).state || "";
}

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
