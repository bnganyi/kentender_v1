<script setup>
// BDS-CHG-001 v0.8 §10.10 "response drawer" (board C), used for one form of
// a task: its published facts and locked statement, then its fields; Save
// response sends only this form's changed answers through `SaveBidTask`
// against the bid's version. 480 px from the right; the full width at 390.
// A refusal names each field in place and keeps what was entered.
import { computed, inject, nextTick, onMounted, reactive, ref } from "vue";
import FieldControl from "./FieldControl.vue";

const SAVE = "kentender_procurement.bid_submission.api.save_bid_task";
const props = defineProps({
	group: { type: Object, required: true }, // { key, label, facts, statement, fields }
	task: { type: String, required: true },
	bid: { type: Object, required: true }, // { reference, record_version }
});
const emit = defineEmits(["close", "saved", "changed"]);
const portal = inject("portal");
const values = reactive(Object.fromEntries(props.group.fields.map((f) => [f.handle, f.value])));
const errors = ref({});
const failure = ref("");
const panel = ref(null);
const runner = portal.createCommandRunner({ ref }, { onError: (e) => (failure.value = e.message) });
const pending = computed(() => runner.pending.value);
const editable = computed(() => props.group.fields.some((f) => f.editable && f.kind !== "evidence"));

function visible(field) {
	const rule = field.shown_when;
	if (!rule) return field.visible !== false;
	return rule.handles.some((handle) => rule.values.includes(values[handle]));
}
function changed() {
	return Object.fromEntries(props.group.fields.filter((f) => f.editable && f.kind !== "evidence" && JSON.stringify(values[f.handle]) !== JSON.stringify(f.value)).map((f) => [f.handle, values[f.handle]]));
}
function save() {
	errors.value = {};
	failure.value = "";
	const answers = changed();
	if (!Object.keys(answers).length) return emit("close");
	return runner.run(async () => {
		const result = await portal.call(SAVE, { bid_reference: props.bid.reference, task: props.task, values: JSON.stringify(answers), expected_record_version: props.bid.record_version, idempotency_key: `bds-${props.task}-${Date.now().toString(36)}` }, { type: "POST" });
		if (result && result.ok) emit("saved", result);
		else if (result && result.errors) errors.value = result.errors;
		else if (result) failure.value = result.message || "";
	}, "Save response");
}
onMounted(() => nextTick(() => panel.value && panel.value.focus()));
</script>

<template>
	<div class="bds-drawer-backdrop" data-testid="bds-response-drawer" @keydown.esc.stop="emit('close')" @click.self="emit('close')">
		<aside ref="panel" class="bds-drawer" role="dialog" aria-modal="true" :aria-label="group.label" tabindex="-1">
			<div class="bds-drawer-head">{{ group.label }}</div>
			<div class="bds-drawer-body">
				<div v-for="fact in group.facts || []" :key="fact.label" class="bds-drawer-fact"><span class="kt-label">{{ fact.label }}</span><span>{{ fact.value }}</span></div>
				<div v-if="group.statement" class="bds-statement" data-testid="bds-drawer-statement">{{ group.statement }}</div>
				<template v-for="field in group.fields" :key="field.handle">
					<FieldControl v-if="visible(field)" v-model="values[field.handle]" :field="field" :error="errors[field.handle] || ''" :bid="bid" id-prefix="bds-drawer" @changed="emit('changed', $event)" />
				</template>
				<div v-if="failure" class="kt-notice is-critical" role="alert"><div class="kt-notice-body">{{ failure }}</div></div>
			</div>
			<div class="bds-drawer-foot">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="emit('close')">{{ editable ? __("Cancel") : __("Close") }}</button>
				<button v-if="editable" type="button" class="kt-btn kt-btn-primary" :disabled="pending" data-testid="bds-drawer-save" @click="save">{{ pending ? __("Saving…") : __("Save response") }}</button>
			</div>
		</aside>
	</div>
</template>
