<!-- Award — AWD-CHG-001 v0.4 §9, §10. One Desk Page ("award") for the workspace
     (/app/award) and every award record (/app/award/{award_id}, with its
     request and read-only view sub-routes); the app stays mounted across them
     (AGENTS.md §6.1). One loader with a sequence guard; one pending gate for
     every command; the page reloads after each command and revalidates in
     place. The server decides what a viewer may read and do; the screens only
     draw its answer in the boards' vocabulary. -->
<template>
	<div class="kt-industry kt-awd">
		<div ref="railEl" class="kt-rail-mount"></div>
		<div class="kt-shell" data-testid="awd-root" :data-screen="board ? board.screen || '' : 'loading'" :data-loading="loading ? 'true' : 'false'" :data-pending="pending ? 'true' : 'false'">
			<div v-if="testLabel" class="kt-notice is-info awd-test-environment" data-testid="awd-test-environment"><div class="kt-notice-body">{{ testLabel }}</div></div>
			<AwdBoard v-if="board" :key="screenKey" :board="board" :form="form" :pending="pending" :error="error" :reasons="reasons" :fields="fields"
				@action="onAction" @update="onUpdate" />
		</div>
	</div>
</template>

<script setup>
import { computed, reactive, ref, watch } from "vue";
import * as api from "./data/api.js";
import { useRouteState } from "./composables/useRouteState.js";
import AwdBoard from "./board/AwdBoard.vue";
import { recordBoard } from "./screens/record.js";
import { workspaceBoard } from "./screens/workspace.js";
import { viewBoard } from "./screens/views.js";
import { dialogFor } from "./screens/dialogs.js";
import { usePageRail } from "../tnd_shared/composables/usePageRail.js";

const PAGE = "award";
const { route, epoch } = useRouteState(PAGE);
const segments = computed(() => route.value.slice(1).filter(Boolean));
const awardId = computed(() => segments.value[0] || "");
const sub = computed(() => segments.value[1] || "");
const subId = computed(() => segments.value.slice(2).join("/"));
const screenKey = computed(() => `${awardId.value}:${sub.value}:${subId.value}`);

const railEl = ref(null);
const data = ref(null);
const work = ref(null);
const loading = ref(false);
const failure = ref("");
const pending = ref(false);
const error = ref("");
const reasons = ref([]);
const fields = ref({});
const form = reactive({});
const dialog = ref(null);
const signKeys = {};
let seq = 0;

const testLabel = computed(() => (data.value && data.value.test_environment) || (work.value && work.value.test_environment) || "");

const board = computed(() => {
	if (failure.value) return { hdr: { title: failure.value === "not-found" ? "Not found" : "Award" }, screen: failure.value,
		sec: [{ t: "Award", empty: failure.value === "not-found" ? "This award record does not exist or you do not have access to it." : "We could not load this award. Try again." }] };
	if (!awardId.value) return work.value ? workspaceBoard(work.value) : { hdr: { title: "Award" }, screen: "loading", sec: [{ t: "Your award tasks", empty: "Loading…" }] };
	if (!data.value) return { hdr: { title: "Award" }, screen: "loading", sec: [{ t: "Award", empty: "Loading…" }] };
	let b = sub.value === "view" ? viewBoard(data.value, subId.value) : recordBoard(data.value, { sub: sub.value, id: subId.value });
	if (dialog.value) {
		const dlg = dialogFor(dialog.value.name, dialog.value.args, data.value);
		if (dlg) b = { ...b, dlg };
	}
	return b;
});

// ------------------------------------------------------------------ loading
async function load({ quiet = false } = {}) {
	const token = ++seq;
	if (!quiet) loading.value = true;
	try {
		if (!awardId.value) {
			const out = await api.getWorkspace();
			if (token !== seq) return;
			work.value = out;
		} else {
			const out = await api.getAward(awardId.value);
			if (token !== seq) return;
			if (out && out.ok === false) throw Object.assign(new Error(out.message || ""), { httpStatus: 500 });
			data.value = out;
			prefill();
		}
		failure.value = "";
	} catch (e) {
		if (token !== seq) return;
		if (!quiet || !data.value) failure.value = e.httpStatus === 404 || /not found/i.test(e.message || "") ? "not-found" : "failure";
	} finally {
		if (token === seq) loading.value = false;
	}
}

// A value the viewer has typed is never overwritten by a reload (AGENTS.md §6.4).
function prefill() {
	const d = data.value;
	const set = (name, value) => { if (form[name] === undefined && value !== undefined && value !== null) form[name] = value; };
	const w = d.opinion && d.opinion.working;
	if (w && w.state !== "Out of date") {
		set("conclusion", w.conclusion || "");
		set("reason", w.reason || "");
	}
	const open = (d.correspondence || []).find((c) => c.state === "Open");
	if (open) set("reply", open.draft || "");
}

function resetScreen() {
	Object.keys(form).forEach((k) => delete form[k]);
	dialog.value = null;
	clearErrors();
}

function clearErrors() {
	error.value = "";
	reasons.value = [];
	fields.value = {};
}

// ------------------------------------------------------------------ commands
function refuse(result) {
	if (result.code === "AWD_RECORD_CHANGED" && result.detail && result.detail.record_version !== undefined) {
		error.value = result.message;
		load({ quiet: true });
		return;
	}
	error.value = result.message || "The action could not be completed.";
	const f = { ...(result.fields || {}) };
	if (dialog.value && result.fields) Object.entries(result.fields).forEach(([k, v]) => { f[`dlg_${k}`] = v; });
	fields.value = f;
	const list = (result.reasons || []).map((r) => (r.detail && (r.detail.reason || r.detail.title)) || (r.message !== result.message ? r.message : "")).filter(Boolean);
	reasons.value = [...new Set(list)];
}

async function run(method, args, { key, close = true, after } = {}) {
	if (pending.value) return null;
	pending.value = true;
	clearErrors();
	try {
		const result = await api.command(method, args, key);
		if (result && result.ok === false) refuse(result);
		else {
			if (close) dialog.value = null;
			if (after) after(result);
		}
		await load({ quiet: true });
		return result;
	} catch (e) {
		error.value = e.message || "The action could not be completed.";
		await load({ quiet: true });
		return null;
	} finally {
		pending.value = false;
	}
}

const version = () => (data.value ? data.value.record_version : 0);
const award = () => awardId.value;

async function saveOpinion() {
	return run("save_opinion", { award: award(), conclusion: form.conclusion || "", reason: form.reason || "", expected_version: version() }, { close: false });
}

async function signOpinion() {
	const w = data.value.opinion.working;
	const dirty = !w || (form.conclusion || "") !== (w.conclusion || "") || (form.reason || "") !== (w.reason || "") || w.state === "Out of date";
	if (dirty) {
		const saved = await saveOpinion();
		if (!saved || saved.ok === false) return;
	}
	const slot = `sign:${award()}:${(data.value.opinion.working || {}).id || ""}:${version()}`;
	const key = signKeys[slot] || (signKeys[slot] = api.newKey("sign_opinion"));
	return run("sign_opinion", { award: award(), expected_version: version() }, { key });
}

function go(...path) {
	frappe.set_route(PAGE, ...path);
}

function onUpdate({ name, value }) {
	form[name] = value;
	if (fields.value[name]) fields.value = { ...fields.value, [name]: "" };
}

async function onFix(fix) {
	const id = (fix && fix.fix_id) || "";
	const [kind, arg] = id.split(":");
	if (kind === "return_report") return openDialog("return-report", {});
	if (kind === "record_outcome") return openDialog("record-outcome", { issue: arg });
	if (kind === "view_issue") return go(award(), "view", "issues");
	if (kind === "correct_contact") return run("correct_contact", { award: award(), notice: arg }, { close: false });
	return null;
}

function openDialog(name, args) {
	clearErrors();
	dialog.value = { name, args: args || {} };
	if (name === "accept") return;
	["dlg_reason", "dlg_next_action", "dlg_evidence", "dlg_outcome", "dlg_basis", "dlg_source", "dlg_received_at", "dlg_effective_from", "dlg_scope"].forEach((k) => {
		if (form[k] === undefined) form[k] = "";
	});
}

async function onAction(a) {
	const { action, args = {} } = a || {};
	switch (action) {
		case "open": return go(args.award);
		case "back": return go(award());
		case "view": return go(award(), "view", args.what);
		case "dialog": return openDialog(args.name, args);
		case "close-dialog": dialog.value = null; clearErrors(); return null;
		case "fix": return onFix(args);
		case "save-opinion": return saveOpinion();
		case "sign-opinion": return signOpinion();
		case "return-report": return run("return_report", { award: award(), reason: form.dlg_reason || "", expected_version: version() });
		case "award": return run("record_decision", { award: award(), outcome: "Award", reason: form.decision_reason || "", expected_version: version() });
		case "decide": return run("record_decision", { award: award(), outcome: args.outcome, reason: form.dlg_reason || "", next_action: form.dlg_next_action || "",
			expected_version: version() });
		case "correction": return run("record_correction_decision", { award: award(), outcome: args.outcome, reason: args.reason || form.dlg_reason || "",
			next_action: form.dlg_next_action || "", expected_version: version() });
		case "corrected-award": return run("record_correction_decision", { award: award(), outcome: "Record corrected award", reason: form.decision_reason || "",
			expected_version: version() });
		case "authorise-revised": return run("record_correction_decision", { award: award(), outcome: "Authorise revised notices", expected_version: version() });
		case "disposition": return run("record_disposition", { award: award(), issue: args.issue, outcome: form.dlg_outcome || "", reason: form.dlg_reason || "",
			evidence: form.dlg_evidence || "", next_action: form.dlg_next_action || "" });
		case "record-restriction": return run("record_restriction", { award: award(), basis: form.dlg_basis || "", source: form.dlg_source || "",
			received_at: form.dlg_received_at || "", effective_from: form.dlg_effective_from || "", scope: form.dlg_scope || "", evidence: form.dlg_evidence || "",
			reason: form.dlg_reason || "" });
		case "save-reply": return run("save_explanation", { award: award(), request: args.request, reply: form.reply || "" }, { close: false });
		case "send-reply": return run("send_explanation", { award: award(), request: args.request, reply: form.reply || "" }, { close: false });
		case "retry-operation": return run("retry_operation", { award: award() }, { close: false });
		default: return null;
	}
}

// ------------------------------------------------------------------ lifecycle
watch(screenKey, (now, before) => {
	const [idNow] = now.split(":");
	const [idBefore] = (before || "").split(":");
	if (idNow !== idBefore) {
		data.value = null;
		failure.value = "";
		resetScreen();
	} else {
		dialog.value = null;
		clearErrors();
	}
	load({ quiet: idNow === idBefore && !!data.value });
}, { immediate: true });
watch(epoch, () => load({ quiet: true }));

const railTrail = computed(() => {
	const trail = [{ label: __("Home"), route: ["Workspaces", "Procurement Home"] }, { label: "Award", route: awardId.value ? ["award"] : null }];
	if (awardId.value) trail.push({ label: awardId.value });
	return trail;
});
usePageRail(railEl, railTrail, { showPeSwitcher: false });
</script>
