<script setup>
import { ref, nextTick, watch } from "vue";

const props = defineProps({
	open: { type: Boolean, default: false },
	action: { type: String, default: "" },
	needsReason: { type: Boolean, default: false },
});
const emit = defineEmits(["confirm", "cancel"]);

const reason = ref("");
const reasonRef = ref(null);
const confirmRef = ref(null);
const touched = ref(false);

const reasonInvalid = () => props.needsReason && !reason.value.trim();

watch(
	() => props.open,
	async (isOpen) => {
		if (!isOpen) return;
		reason.value = "";
		touched.value = false;
		await nextTick();
		(props.needsReason ? reasonRef.value : confirmRef.value)?.focus();
	}
);

function onConfirm() {
	touched.value = true;
	if (reasonInvalid()) return;
	emit("confirm", reason.value.trim() || null);
}

function onKeydown(e) {
	if (e.key === "Escape") emit("cancel");
}
</script>

<template>
	<div v-if="open" class="kt-pp-dialog-backdrop" @click.self="$emit('cancel')" @keydown="onKeydown">
		<div class="kt-pp-dialog" role="dialog" aria-modal="true">
			<div class="kt-pp-dialog__header">
				<h3>{{ action }}</h3>
				<button type="button" class="kt-pp-dialog__close" aria-label="Cancel" @click="$emit('cancel')">
					×
				</button>
			</div>
			<div class="kt-pp-dialog__body">
				<p>Confirm: {{ action }}?</p>
				<div v-if="needsReason" class="kt-pp-field">
					<label for="kt-pp-dialog-reason">Reason</label>
					<textarea
						id="kt-pp-dialog-reason"
						ref="reasonRef"
						v-model="reason"
						class="kt-pp-input"
						rows="3"
					></textarea>
					<p v-if="touched && reasonInvalid()" class="kt-pp-dialog__error">Reason is required.</p>
				</div>
			</div>
			<div class="kt-pp-dialog__footer">
				<button type="button" class="kt-pp-btn kt-pp-btn--secondary" @click="$emit('cancel')">
					Cancel
				</button>
				<button
					ref="confirmRef"
					type="button"
					class="kt-pp-btn kt-pp-btn--primary"
					@click="onConfirm"
				>
					Confirm
				</button>
			</div>
		</div>
	</div>
</template>

<style scoped>
.kt-pp-dialog-backdrop {
	position: fixed;
	inset: 0;
	z-index: 1100;
	display: flex;
	align-items: center;
	justify-content: center;
	background: color-mix(in srgb, #2b2b2d 50%, transparent);
}
.kt-pp-dialog {
	width: min(440px, calc(100vw - 32px));
	display: flex;
	flex-direction: column;
	gap: var(--ktpp-space-3);
	padding: var(--ktpp-space-4);
	background: var(--ktpp-color-bg);
	border: 1px solid var(--ktpp-color-divider);
	box-shadow: var(--ktpp-shadow-sm);
}
.kt-pp-dialog__header {
	display: flex;
	align-items: center;
	justify-content: space-between;
}
.kt-pp-dialog__header h3 {
	font-size: 18px;
}
.kt-pp-dialog__close {
	background: none;
	border: 0;
	font-size: 20px;
	line-height: 1;
	cursor: pointer;
	color: var(--ktpp-color-text);
}
.kt-pp-dialog__body p {
	margin: 0 0 10px;
	font-size: 14px;
}
.kt-pp-field > label {
	display: block;
	font-size: 12px;
	margin-bottom: 5px;
	color: color-mix(in srgb, var(--ktpp-color-text) 70%, transparent);
}
.kt-pp-input {
	width: 100%;
	padding: 6px 10px;
	font: inherit;
	font-size: 14px;
	color: var(--ktpp-color-text);
	background: var(--ktpp-color-surface);
	border: 1px solid var(--ktpp-color-divider);
	border-radius: var(--ktpp-radius-md);
}
.kt-pp-dialog__error {
	color: #b3261e;
	font-size: 12px;
	margin: 6px 0 0;
}
.kt-pp-dialog__footer {
	display: flex;
	justify-content: flex-end;
	gap: var(--ktpp-space-2);
}
.kt-pp-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	font-family: var(--ktpp-font-heading);
	font-weight: var(--ktpp-font-heading-weight);
	font-size: 14px;
	padding: 7px 14px;
	border-radius: var(--ktpp-radius-md);
	border: 1px solid transparent;
}
.kt-pp-btn--secondary {
	border-color: var(--ktpp-color-divider);
	background: transparent;
	color: var(--ktpp-color-text);
}
.kt-pp-btn--secondary:hover {
	background: color-mix(in srgb, var(--ktpp-color-text) 7%, transparent);
}
.kt-pp-btn--primary {
	background: var(--ktpp-color-accent);
	color: var(--ktpp-color-bg);
	border-color: var(--ktpp-color-accent);
}
.kt-pp-btn--primary:hover {
	background: var(--ktpp-color-accent-600);
}
</style>
