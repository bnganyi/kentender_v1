<!-- The supplier's award notice — AWD-CHG-001 v0.4 §9 "/supplier/awards/{notice_id}"
     (plan D14). Mounted once by the portal runtime; the first paint is the
     server's own answer, later ones reload in place after each command. -->
<template>
	<div class="kt-industry kt-awd" data-testid="awd-portal" :data-screen="board ? board.screen : ''" :data-pending="pending ? 'true' : 'false'">
		<div v-if="data && data.test_environment" class="kt-notice is-info awd-test-environment" data-testid="awd-test-environment"><div class="kt-notice-body">{{ data.test_environment }}</div></div>
		<AwdBoard v-if="board" :board="board" :form="form" :pending="pending" :error="error" :reasons="reasons" :fields="fields" @action="onAction" @update="onUpdate" />
		<div v-if="viewing && data" class="awd-letter" data-testid="awd-letter" v-html="data.letter_html"></div>
	</div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import AwdBoard from "../board/AwdBoard.vue";
import { dialogFor } from "../screens/dialogs.js";
import { noticesBoard, supplierBoard } from "./supplier.js";

const props = defineProps({ initial: { type: Object, default: () => ({}) }, portal: { type: Object, required: true } });
const { route, epoch } = props.portal.useRoute({ ref, onMounted, onUnmounted });

const payload = (props.initial && props.initial.payload) || {};
const data = ref(payload.screen === "award-notice" ? payload.data : null);
const list = ref(payload.screen === "award-notices" ? payload.data.notices : null);
const form = reactive({});
const dialog = ref(null);
const pending = ref(false);
const error = ref("");
const reasons = ref([]);
const fields = ref({});
const viewing = ref(false);
const keys = {};

const noticeId = computed(() => ((route.value && route.value.segments) || [])[2] || "");

const board = computed(() => {
	if (!noticeId.value) return list.value ? noticesBoard(list.value) : null;
	if (!data.value) return { hdr: { title: "Not found" }, screen: "not-found", sec: [{ t: "Award notice", empty: "This notice does not exist or you do not have access to it." }] };
	let b = supplierBoard(data.value, { viewing: viewing.value });
	if (dialog.value) {
		const d = dialogFor(dialog.value.name, dialog.value.args, data.value);
		if (d) b = { ...b, dlg: d };
	}
	return b;
});

async function load() {
	if (!noticeId.value) {
		const out = await props.portal.call("kentender_procurement.award.api.list_supplier_notices", {}).catch(() => null);
		list.value = out ? out.notices : [];
		return;
	}
	try {
		data.value = await props.portal.call("kentender_procurement.award.api.get_supplier_notice", { notice: noticeId.value });
	} catch (e) {
		data.value = null;
	}
}

function clearErrors() {
	error.value = "";
	reasons.value = [];
	fields.value = {};
}

async function run(method, args, slot) {
	if (pending.value) return;
	pending.value = true;
	clearErrors();
	const key = keys[slot] || (keys[slot] = `awd-${method}-${Date.now()}-${Math.random().toString(16).slice(2)}`);
	try {
		const out = await props.portal.call(`kentender_procurement.award.api.${method}`, { ...args, idempotency_key: key }, { type: "POST" });
		if (out && out.ok === false) {
			error.value = out.message || "The action could not be completed.";
			fields.value = Object.fromEntries(Object.entries(out.fields || {}).map(([k, v]) => [`dlg_${k}`, v]));
		} else {
			delete keys[slot];
			dialog.value = null;
			if (out && out.message) error.value = "";
		}
	} catch (e) {
		error.value = e.message || "The action could not be completed.";
	} finally {
		pending.value = false;
		await load();
	}
}

function onUpdate({ name, value }) {
	form[name] = value;
}

function onAction(a) {
	const { action, args = {} } = a || {};
	if (action === "dialog") {
		clearErrors();
		dialog.value = { name: args.name, args };
		return;
	}
	if (action === "close-dialog") { dialog.value = null; clearErrors(); return; }
	if (action === "view-notice") { viewing.value = true; return; }
	if (action === "back-to-notice") { viewing.value = false; return; }
	if (action === "open-notice") { props.portal.go(`/supplier/awards/${args.notice}`); return; }
	if (action === "respond") return run("respond", { notice: data.value.notice, response: args.response, reason: form.dlg_reason || "", notice_version: data.value.notice_version },
		`respond:${args.response}`);
	if (action === "request-explanation") return run("request_explanation", { notice: data.value.notice, request: form.dlg_request || "" }, "request");
}

watch(noticeId, () => { viewing.value = false; dialog.value = null; load(); });
watch(epoch, () => load());
</script>
