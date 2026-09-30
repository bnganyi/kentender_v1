<!-- Bid Evaluation — EVL-CHG-001 v0.4 §9, §10. Mounted by the Tenders page into
     its host for every route under /app/tenders/{ref}/evaluation (screens/index.js
     lists them). One loader with a sequence guard; one pending gate for every
     command; the page reloads after each command and revalidates in place; a
     quiet poll and a presence heartbeat while a committee discussion is live
     (plan D15: no socket.io on this bench). The server decides what a viewer
     may read and do; the screens only draw its answer in the boards' vocabulary. -->
<template>
	<div class="kt-evl" data-testid="evl-root" :data-screen="board ? board.screen || failure || 'loading' : ''" :data-loading="loading ? 'true' : 'false'" :data-pending="pending ? 'true' : 'false'">
		<EvlBoard v-if="board" :key="screenKey" :board="board" :form="form" :people="people" :pending="pending" :error="error" :reasons="reasons" :fields="fields"
			@action="onAction" @update="onUpdate" />
	</div>
</template>

<script setup>
import { computed, onUnmounted, reactive, ref, watch } from "vue";
import * as api from "./data/api.js";
import { useRouteState } from "./composables/useRouteState.js";
import EvlBoard from "./board/EvlBoard.vue";
import { build, dialogFor, needs, record } from "./screens/index.js";
import { peopleOf, staleBoard } from "./screens/common.js";
import { memberRows } from "./screens/committee.js";

const PAGE = "tenders";
const POLL_MS = 5000;
const HEARTBEAT_MS = 20000;

const { route, epoch } = useRouteState(PAGE);
const segments = computed(() => route.value.slice(1).filter(Boolean));
const ref_ = computed(() => (segments.value[1] === "evaluation" ? segments.value[0] : ""));
const sub = computed(() => (segments.value[1] === "evaluation" ? segments.value[2] || "" : ""));
const id = computed(() => (segments.value[1] === "evaluation" ? segments.value.slice(3).join("/") : ""));
const screenKey = computed(() => `${ref_.value}:${sub.value}:${id.value}`);

const data = ref(null);
const extra = reactive({ bid: null, report: null, record: null, candidates: null });
const loading = ref(false);
const failure = ref("");
const pending = ref(false);
const error = ref("");
const reasons = ref([]);
const fields = ref({});
const form = reactive({});
const dialog = ref(null);
const unconfirmed = ref(false);
const stale = ref(false);
const signKeys = {};
let seq = 0;

const people = computed(() => peopleOf(data.value));
const ctx = computed(() => ({
	data: data.value, sub: sub.value, id: id.value, user: frappe.session.user, form, errors: memberErrors.value,
	bid: extra.bid, report: extra.report, record: extra.record, candidates: extra.candidates, unconfirmed: unconfirmed.value,
	dialogArgs: dialog.value ? dialog.value.args : null,
}));

const board = computed(() => {
	if (failure.value) return { ...record.states(failure.value), screen: failure.value };
	if (!data.value) return { ...record.states("loading"), screen: "loading" };
	const b = build(ctx.value);
	if (!b) return { ...record.states("not-found"), screen: "not-found" };
	if (stale.value) return staleBoard(b);
	if (dialog.value) {
		const d = dialogFor(dialog.value.name, ctx.value);
		if (d) return { ...b, dlg: { ...d, pri: d.pri, sec: d.sec || [{ label: "Cancel", action: "close-dialog" }] } };
	}
	return b;
});

// ------------------------------------------------------------------ loading
async function load({ quiet = false } = {}) {
	const reference = ref_.value;
	if (!reference) return;
	const token = ++seq;
	if (!quiet) loading.value = true;
	try {
		const loaded = await api.getEvaluation(reference);
		if (token !== seq) return;
		if (loaded && loaded.ok === false) throw Object.assign(new Error(loaded.message || ""), { httpStatus: 500 });
		const want = needs(sub.value, id.value, loaded);
		const [bid, report, rec, candidates] = await Promise.all([
			want.bid ? api.getBid(reference, want.bid).catch(() => null) : null,
			want.report !== undefined ? api.getReport(reference, want.report).catch(() => null) : null,
			want.record ? api.getCommitteeRecord(reference).catch(() => null) : null,
			want.candidates ? api.getCandidates(reference, want.candidates).then((r) => r.candidates || r).catch(() => []) : null,
		]);
		if (token !== seq) return;
		data.value = loaded;
		Object.assign(extra, { bid: okOrNull(bid), report: okOrNull(report), record: okOrNull(rec), candidates });
		failure.value = "";
		prefill();
	} catch (e) {
		if (token !== seq) return;
		if (!quiet || !data.value) failure.value = e.httpStatus === 404 || /not found/i.test(e.message || "") ? "not-found" : "failure";
	} finally {
		if (token === seq) loading.value = false;
	}
}
const okOrNull = (x) => (x && x.ok === false ? null : x);

// Form defaults for the screen just entered; a value the viewer has typed is
// never overwritten by a reload (AGENTS.md §6.4).
function prefill() {
	const d = (name, value) => { if (form[name] === undefined && value !== undefined) form[name] = value; };
	if (sub.value === "appoint" || (!sub.value && (data.value.guidance || {}).primary_action === "appoint_committee")) {
		memberRows(form).forEach((i) => d(`m${i}_capacity`, i === 0 ? "Chair" : "Member"));
	}
	if (sub.value === "declaration") d("choice", "No conflict to declare");
	if (sub.value === "report" && extra.report && extra.report.live) d("narrative", extra.report.content && extra.report.content.narrative || "");
	if (sub.value === "update") d("impact", "No effect on findings");
	if (sub.value === "replace") {
		const blocked = ((data.value.committee || {}).members || []).find((m) => m.declaration === "Conflict declared" || m.unavailable);
		if (blocked) d("outgoing", blocked.user);
	}
	if (sub.value === "bid" && extra.bid && form.requirement_key === undefined) {
		const pendingReq = (extra.bid.requirements || []).find((r) => r.evidence_pending) || (extra.bid.requirements || []).find((r) => r.result === "Needs review");
		if (pendingReq) form.requirement_key = pendingReq.requirement_key;
	}
}

function resetScreen() {
	Object.keys(form).forEach((k) => delete form[k]);
	dialog.value = null;
	error.value = "";
	reasons.value = [];
	fields.value = {};
	unconfirmed.value = false;
	stale.value = false;
}

// ------------------------------------------------------------------ commands
function collect(spec) {
	const args = {};
	(spec.fields || []).forEach((f) => {
		const [arg, key] = Array.isArray(f) ? f : [f, f];
		const value = form[key];
		args[arg] = typeof value === "boolean" ? (value ? 1 : 0) : value ?? "";
	});
	const values = { ...(spec.values || {}) };
	const compose = values.compose;
	delete values.compose;
	Object.assign(args, values);
	if (compose === "members") {
		args.members = JSON.stringify(memberRows(form).map((i) => ({ user: form[`m${i}_user`] || "", department: form[`m${i}_department`] || "", capacity: form[`m${i}_capacity`] || "" }))
			.filter((m) => m.user || m.department));
	}
	if (compose === "incoming") {
		const pick = (extra.candidates || []).find((c) => c.user === form.incoming) || {};
		args.incoming = JSON.stringify({ user: form.incoming || "", department: pick.department || values.department || "", capacity: values.capacity || "Member" });
		delete args.department;
		delete args.capacity;
	}
	if (compose === "participants") {
		args.participants = JSON.stringify(((data.value.committee || {}).members || []).filter((m) => form[`p_${m.user}`]).map((m) => m.user));
	}
	if (compose === "qualified") args.qualified = form.result === "Needs review" ? 1 : 0;
	if (compose === "disposition-result" && !args.result) {
		const c = ((data.value.work || {}).clarifications || []).find((x) => x.name === args.clarification) || {};
		const r = ((extra.bid || {}).requirements || []).find((x) => x.requirement_key === c.requirement_key) || {};
		args.result = r.result || "Needs review";
	}
	if (compose === "impact") args.impact = form.impact === "Findings need review" ? "Findings need review" : "No effect on findings";
	if (spec.versioned) args.expected_version = data.value.record_version;
	if (spec.reportVersion) args.expected_version = (extra.report || {}).report_record_version || 0;
	return args;
}

function describe(result) {
	const list = (result.reasons || []).flatMap((r) => {
		const d = r.detail || {};
		if (d.issues) return d.issues.map((i) => `${i.item}${i.holder_name ? ` — ${i.holder_name}` : ""}`);
		if (d.explanation) return [d.explanation];
		if (d.absent_names) return [`${d.absent_names.join(" and ")} must be present.`];
		return r.message && r.message !== result.message ? [r.message] : [];
	});
	return [...new Set(list)];
}

const memberErrors = computed(() => {
	const out = { members: {} };
	(reasons.value.raw || []).forEach((r) => {
		const d = r.detail || {};
		if (r.code !== "EVL_MEMBER_INELIGIBLE") return;
		if (sub.value === "replace") {
			out.incoming = "This person cannot serve on this evaluation committee.";
			out.incoming_detail = d.explanation || "";
			return;
		}
		memberRows(form).forEach((i) => { if (form[`m${i}_user`] === d.person) out.members[i] = d.explanation || Object.values(d.fields || {})[0] || r.message; });
	});
	return out;
});

async function run(spec) {
	if (pending.value || !data.value) return null;
	pending.value = true;
	error.value = "";
	reasons.value = [];
	fields.value = {};
	try {
		if (spec.saveNarrative && extra.report && extra.report.live && (form.narrative || "") !== ((extra.report.content || {}).narrative || "")) {
			const saved = await api.command("save_report_narrative", ref_.value, { narrative: form.narrative || "", expected_version: extra.report.report_record_version || 0 });
			if (saved && saved.ok === false) return refuse(saved);
			await load({ quiet: true });
		}
		const args = collect(spec);
		let key;
		if (spec.reuseKey) {
			const slot = `${spec.method}:${args.report_version || ""}`;
			key = signKeys[slot] || (signKeys[slot] = api.newKey(spec.method));
		}
		const result = await api.command(spec.method, ref_.value, args, key);
		if (result && result.ok === false) {
			if (result.code === "EVL_SIGNATURE_UNCONFIRMED") unconfirmed.value = true;
			refuse(result);
		} else {
			if (spec.reuseKey) unconfirmed.value = false;
			if (spec.close) dialog.value = null;
			if (spec.after) go(spec.after);
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

function refuse(result) {
	if (result.code === "EVL_VERSION_CONFLICT" && result.detail && result.detail.record_version !== undefined) {
		// someone else changed the record: keep the page and the form, offer Refresh
		stale.value = true;
		dialog.value = null;
		return result;
	}
	error.value = result.message || "The action could not be completed.";
	fields.value = result.fields || {};
	if (result.fields && dialog.value) {
		// a dialog's field names are prefixed to keep them apart from the page's
		Object.entries(result.fields).forEach(([k, v]) => { fields.value[`${dialog.value.name}_${k}`] = v; });
	}
	const list = describe(result);
	reasons.value = Object.assign(list, { raw: result.reasons || [] });
	return result;
}

// ------------------------------------------------------------------ actions
function go(to) {
	const path = [].concat(to || []);
	if (path[0] === "tender") return frappe.set_route(PAGE, ref_.value);
	if (path[0] === "workspace") return frappe.set_route("bid-evaluation");
	frappe.set_route(PAGE, ref_.value, "evaluation", ...path);
}

function onUpdate({ name, value }) {
	form[name] = value;
	if (fields.value[name]) fields.value = { ...fields.value, [name]: "" };
}

async function onAction({ action, args }) {
	const a = args || {};
	switch (action) {
		case "nav":
			go(a.to);
			if (a.anchor) setTimeout(() => document.getElementById(`evl-${a.anchor.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`)?.scrollIntoView({ block: "start" }), 400);
			return;
		case "cmd": return run(a);
		case "dialog":
			error.value = "";
			reasons.value = [];
			// a dialog may open with the recorded words it confirms (the chair's reason)
			Object.entries(a.prefill || {}).forEach(([k, v]) => { if (form[k] === undefined) form[k] = v; });
			dialog.value = { name: a.name, args: a };
			return;
		case "close-dialog": dialog.value = null; error.value = ""; reasons.value = []; return;
		case "set": form[a.name] = a.value; return;
		case "add-member": form.member_count = memberRows(form).length + 1; memberRows(form).forEach((i) => { if (form[`m${i}_capacity`] === undefined) form[`m${i}_capacity`] = "Member"; }); return;
		case "reload": failure.value = ""; return load();
		case "refresh-stale": stale.value = false; return load({ quiet: true });
		case "back": case "back-to-record": return go([]);
		case "nav-opening": return frappe.set_route(PAGE, ref_.value, "opening");
		case "evidence": {
			const bid = a.bid || (extra.bid && extra.bid.bid);
			if (bid && a.digest) window.open(api.evidenceUrl(ref_.value, bid, a.digest), "_blank", "noopener");
			return;
		}
		case "download":
			go(["report", "preview"]);
			setTimeout(() => window.print(), 800);
			return;
		case "fix": return;
		default: return;
	}
}

// ------------------------------------------------------------------ lifecycle
watch(screenKey, (now, before) => {
	const [refNow] = now.split(":");
	const [refBefore] = (before || "").split(":");
	if (refNow !== refBefore) {
		data.value = null;
		Object.assign(extra, { bid: null, report: null, record: null, candidates: null });
	}
	resetScreen();
	load({ quiet: !!data.value });
}, { immediate: true });
watch(epoch, () => load({ quiet: true }));

const live = computed(() => !!(data.value && (data.value.work || {}).session));
const poll = setInterval(() => {
	if (document.hidden || pending.value || !live.value) return;
	load({ quiet: true });
}, POLL_MS);
const beat = setInterval(() => {
	const s = data.value && (data.value.work || {}).session;
	if (s && (s.present || []).includes(frappe.session.user) && !document.hidden) api.heartbeat(ref_.value).catch(() => {});
}, HEARTBEAT_MS);
onUnmounted(() => {
	clearInterval(poll);
	clearInterval(beat);
	seq++;
});
</script>
