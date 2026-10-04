<script setup>
// BOP-CHG-001 v0.10 §10.5 — the public opening page (boards p0–p6), ported
// class-for-class and served at /tenders/{ref}/opening inside Bid Submission's
// portal app (plan D10: this file is Bid Opening's; the portal renders it for
// its `public-opening` screen). The server decides the phase, what a visitor
// may do and every sentence about the register; bids appear only after the
// recorder has confirmed what was read aloud. While the opening is live the
// page re-reads every few seconds (plan D7: no socket.io on this bench).
import { computed, inject, onMounted, onUnmounted, ref, watch } from "vue";

const BASE = "kentender_procurement.bid_opening.api";
const POLL_MS = 5000;
const props = defineProps({ initial: { type: Object, default: null }, reference: { type: String, required: true } });
const emit = defineEmits(["not-found"]);
const portal = inject("portal");
const { epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const data = ref(props.initial);
const failure = ref("");
const error = ref("");
const guard = portal.createSequenceGuard();
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (error.value = e.message), mintKey: (label) => `bop-public-${label}-${Date.now()}-${Math.random().toString(16).slice(2)}` });
const pending = runner.pending;

const tender = computed(() => (data.value && data.value.tender) || {});
const phase = computed(() => (data.value && data.value.phase) || "");
const arrangements = computed(() => (data.value && data.value.arrangements) || {});
const register = computed(() => (data.value && data.value.register) || {});
const readout = computed(() => (data.value && data.value.readout) || []);
const beforeStart = computed(() => ["details-coming", "before-join", "join"].includes(phase.value));
const desc = computed(() => [tender.value.reference, tender.value.entity, beforeStart.value ? `Opening ${tender.value.opening_label}` : ""].filter(Boolean).join(" · "));
const downloadUrl = computed(() => `/api/method/${BASE}.download_opening_register?tender_reference=${encodeURIComponent(props.reference)}`);

async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(`${BASE}.get_public_opening`, { tender_reference: props.reference });
		if (!guard.isCurrent(token)) return;
		data.value = result;
		failure.value = "";
	} catch (e) {
		if (!guard.isCurrent(token)) return;
		if (e.status === 404 || e.httpStatus === 404) emit("not-found");
		else failure.value = e.message;
	}
}
function command(method, label) {
	error.value = "";
	return runner.run(async (key) => {
		const result = await portal.call(`${BASE}.${method}`, { tender_reference: props.reference, idempotency_key: key }, { type: "POST" });
		if (result && result.ok === false) error.value = result.message || "The action could not be completed.";
		await load();
	}, label);
}
const join = () => command("join_public_opening", "join");
const requestRegister = () => command("request_opening_register", "request");

watch(epoch, () => load());
watch(() => tender.value.title, (title) => title && portal.setTitle(`Bid opening · ${title}`), { immediate: true });
let poll = null;
onMounted(() => {
	if (!data.value) load();
	poll = setInterval(() => {
		if (!document.hidden && ["join", "in-session", "ended"].includes(phase.value)) load();
	}, POLL_MS);
});
onUnmounted(() => clearInterval(poll));
</script>

<template>
	<div v-if="data" class="kt-page" data-testid="bop-public" :data-phase="phase">
		<div class="kt-page-head"><div><h1 class="kt-page-title">Bid opening · {{ tender.title }}</h1><p class="kt-page-desc">{{ desc }}<template v-if="data.status"> · <span class="kt-status" :class="['not-held', 'cancelled'].includes(phase) ? 'is-critical' : 'is-live'">{{ data.status }}</span></template></p></div></div>

		<!-- p0, p1a, p1: before the opening -->
		<template v-if="beforeStart">
			<div class="kt-region"><h2>Attending the opening</h2>
				<p style="margin:0 0 16px;font-size:16px;max-width:70ch">You can attend the opening. Attending does not submit or change a bid. After the opening record is complete, a supplier who submitted a bid can request the opening register.</p>
				<div v-if="!arrangements.published" class="kt-meta-row" data-testid="bop-public-arrangements"><div><span class="kt-label">Opening time</span><span class="kt-meta-value">{{ tender.opening_label }}</span></div><div><span class="kt-label">How to attend</span><span class="kt-meta-value">{{ arrangements.message }}</span></div></div>
				<div v-else class="kt-meta-row" data-testid="bop-public-arrangements"><div><span class="kt-label">How to attend</span><span class="kt-meta-value">{{ arrangements.attendance_method }}</span></div><div><span class="kt-label">Join opens</span><span class="kt-meta-value">{{ arrangements.join_opens_label }}</span></div><div><span class="kt-label">Opening time</span><span class="kt-meta-value">{{ arrangements.scheduled_label }}</span></div><div><span class="kt-label">Published</span><span class="kt-meta-value">{{ arrangements.published_label }}</span></div></div>
				<p v-if="arrangements.published && arrangements.access_instructions" style="margin:16px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty" data-testid="bop-public-instructions">{{ arrangements.access_instructions }}</p>
				<div v-if="phase === 'join'" style="display:flex;gap:12px;flex-wrap:wrap;align-items:center;margin-top:16px">
					<button v-if="data.can_join" type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bop-public-join" @click="join">Join public opening</button>
					<span v-else-if="data.joined_label" class="kt-status is-live" data-testid="bop-public-joined">Joined {{ data.joined_label }}</span>
					<a v-else-if="!data.signed_in" class="kt-btn kt-btn-secondary" :href="`/login?redirect-to=${encodeURIComponent(`/tenders/${reference}/opening`)}`" data-testid="bop-public-sign-in">Sign in to join</a>
				</div>
				<p v-if="error" class="kt-field-error" role="alert">{{ error }}</p>
			</div>
			<div class="kt-region is-secondary"><h2>What the opening register is</h2>
				<div class="kt-group"><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty">The opening register lists each bid opened, with the tenderer’s name, the total they submitted and the tender security they gave, exactly as read aloud.</p></div>
			</div>
		</template>

		<!-- p2–p6: during and after the readout -->
		<template v-else-if="['in-session', 'ended', 'complete'].includes(phase)">
			<div class="kt-region"><h2>Read aloud at the opening</h2>
				<p v-if="phase === 'in-session'" style="margin:0 0 16px;font-size:16px;max-width:70ch"><template v-if="data.joined_label">You joined at {{ data.joined_label }}. </template>Each bid appears here once the committee has recorded what was read aloud.</p>
				<table class="kt-table" data-testid="bop-public-readout"><thead><tr><th>No.</th><th>Tenderer</th><th class="is-num">Submitted total</th><th>Tender security given</th><th>Recorded at</th></tr></thead><tbody>
					<tr v-for="r in readout" :key="r.number"><td>{{ r.number }}</td><td>{{ r.tenderer }}</td><td class="is-num">{{ r.submitted_total }}</td><td>{{ r.security_given }}</td><td>{{ r.recorded_label }}</td></tr>
				</tbody></table>
				<p v-if="!readout.length" style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty" data-testid="bop-public-readout-none">{{ phase === "in-session" ? "No bid has been read aloud yet." : "There were no bids to open." }}</p>
				<p v-for="(line, i) in phase === 'in-session' ? data.repeats : []" :key="i" style="margin:12px 0 0;font-size:14px;max-width:75ch;text-wrap:pretty">{{ line }}</p>
			</div>
			<div class="kt-region" :class="{ 'is-secondary': !['can-request', 'preparing', 'ready'].includes(register.state) }" data-testid="bop-public-register" :data-state="register.state"><h2>Opening register</h2>
				<template v-if="register.state === 'can-request'"><p style="margin:0 0 12px;font-size:14px;max-width:75ch;text-wrap:pretty">{{ register.message }}</p><button type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bop-public-request" @click="requestRegister">Request opening register</button></template>
				<div v-else-if="register.state === 'preparing'" class="kt-group"><p style="margin:0 0 4px;font-size:16px;font-weight:600">The opening register is being prepared</p><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty">{{ register.message }}</p></div>
				<template v-else-if="register.state === 'ready'"><p style="margin:0 0 12px;font-size:14px;max-width:75ch;text-wrap:pretty">{{ register.message }}</p><a class="kt-btn kt-btn-primary" :href="downloadUrl" data-testid="bop-public-download">Download opening register</a></template>
				<div v-else class="kt-group"><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty">{{ register.message }}</p></div>
				<p v-if="error" class="kt-field-error" role="alert">{{ error }}</p>
			</div>
		</template>

		<!-- the opening did not take place, or ended by cancellation -->
		<template v-else>
			<div class="kt-region" data-testid="bop-public-ended"><h2>{{ phase === "not-held" ? "The opening did not take place" : "The opening ended when the Tender was cancelled" }}</h2>
				<div class="kt-group"><p style="margin:0;font-size:14px;max-width:75ch;text-wrap:pretty">{{ phase === "not-held" ? "No bids were opened. Any next step for the Tender will be published on its page." : "What was read aloud before the cancellation is shown here. Cancellation notices are published with the Tender." }}</p></div>
			</div>
			<div v-if="readout.length" class="kt-region is-secondary"><h2>Read aloud at the opening</h2>
				<table class="kt-table"><thead><tr><th>No.</th><th>Tenderer</th><th class="is-num">Submitted total</th><th>Tender security given</th><th>Recorded at</th></tr></thead><tbody>
					<tr v-for="r in readout" :key="r.number"><td>{{ r.number }}</td><td>{{ r.tenderer }}</td><td class="is-num">{{ r.submitted_total }}</td><td>{{ r.security_given }}</td><td>{{ r.recorded_label }}</td></tr>
				</tbody></table>
			</div>
		</template>
	</div>
	<div v-else-if="failure" class="kt-page" data-testid="bop-public-failure"><div class="kt-region"><h2>The bid opening could not be loaded</h2><p style="margin:0;font-size:14px">{{ failure }}</p></div></div>
</template>
