<!-- The supplier's reply to the evaluation committee — EVL-CHG-001 v0.4 §9.7,
     served at /tenders/{ref}/bid/evaluation-clarifications/{request} inside
     Bid Submission's portal (plan D14: this file is Bid Evaluation's; the
     portal renders it for its `evaluation-clarification` screen). The server
     decides everything the supplier may read and do; a draft is private until
     sent, and a closed request accepts nothing. -->
<template>
	<div class="kt-evl-portal" data-testid="evl-supplier" :data-state="data ? data.status : 'loading'" :data-pending="pending ? 'true' : 'false'">
		<EvlBoard v-if="board" :board="board" :form="form" :pending="pending" :error="error" :fields="fields" @action="onAction" @update="onUpdate" />
		<input ref="picker" type="file" accept="application/pdf,image/png,image/jpeg" multiple style="display:none" data-testid="evl-supplier-file" @change="onFiles">
	</div>
</template>

<script setup>
import { computed, inject, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import EvlBoard from "../board/EvlBoard.vue";
import { supplierBoard } from "./supplier.js";

const BASE = "kentender_procurement.bid_evaluation.api";
const props = defineProps({ initial: { type: Object, default: null }, reference: { type: String, required: true }, clarification: { type: String, required: true } });
const emit = defineEmits(["not-found"]);
const portal = inject("portal");
const { route, go, epoch } = portal.useRoute({ ref, onMounted, onUnmounted });
const data = ref(props.initial);
const form = reactive({ body: "", attachments: [] });
const error = ref("");
const fields = ref({});
const picker = ref(null);
const guard = portal.createSequenceGuard();
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (error.value = e.message), mintKey: (label) => `evl-supplier-${label}-${Date.now()}-${Math.random().toString(16).slice(2)}` });
const pending = runner.pending;
const organisation = computed(() => (route.value && route.value.query && route.value.query.organisation) || "");
const board = computed(() => (data.value ? supplierBoard(data.value, form) : null));

function prefill() {
	const reply = (data.value && data.value.reply) || {};
	if (!form.body && reply.state === "Draft") form.body = reply.body || "";
}
prefill();

async function load() {
	const token = guard.next();
	try {
		const result = await portal.call(`${BASE}.get_own_clarification`, { tender_reference: props.reference, clarification: props.clarification, organisation: organisation.value });
		if (!guard.isCurrent(token)) return;
		data.value = result;
		prefill();
	} catch (e) {
		if (!guard.isCurrent(token)) return;
		if (e.status === 404 || e.httpStatus === 404) emit("not-found");
		else error.value = e.message;
	}
}
if (!data.value) load();
watch(epoch, () => load());

function send(method, label) {
	error.value = "";
	fields.value = {};
	return runner.run(async (key) => {
		const result = await portal.call(`${BASE}.${method}`, { tender_reference: props.reference, clarification: props.clarification, body: form.body,
			attachments: JSON.stringify(form.attachments), organisation: organisation.value, idempotency_key: key }, { type: "POST" });
		if (result && result.ok === false) {
			error.value = result.message || "The action could not be completed.";
			fields.value = result.fields || {};
		}
		await load();
	}, label);
}

function onUpdate({ name, value }) {
	form[name] = value;
}

async function onFiles(event) {
	const chosen = Array.from(event.target.files || []);
	form.attachments = await Promise.all(chosen.map((file) => new Promise((resolve) => {
		const reader = new FileReader();
		reader.onload = () => resolve({ filename: file.name, media_type: file.type, content_base64: String(reader.result).split(",")[1] || "" });
		reader.readAsDataURL(file);
	})));
	event.target.value = "";
}

function onAction({ action, args }) {
	if (action === "send-reply") return send("submit_clarification_reply", "reply");
	if (action === "save-draft") return send("save_clarification_draft", "draft");
	if (action === "choose-file") return picker.value && picker.value.click();
	const query = organisation.value ? { organisation: organisation.value } : {};
	if (action === "back-to-bid") return go(`/tenders/${props.reference}/bid`, { query });
	if (action === "open-request" && args) return go(`/tenders/${props.reference}/bid/evaluation-clarifications/${args.clarification}`, { query });
	return null;
}
</script>
