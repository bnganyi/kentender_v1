<!-- REQ-CHG-001 v1.6 §13.1/§13.5-13.9 — the shared editor shell every one of
     the five steps sits inside: eyebrow + title + status badge + quiet
     reference line (§13.1's fixed header contract), the left step
     navigation with exact completion text, and the footer's Save draft +
     step-specific next action. Ported class-for-class from the REQ-DES-03/04
     artboards' shared chrome. -->
<template>
	<div class="req-editor">
		<header class="req-editor-header">
			<div class="req-eyebrow">PROCUREMENT REQUISITIONS</div>
			<div class="req-editor-titlebar">
				<h1 class="req-editor-title">{{ title }}</h1>
				<span class="kt-status" :class="statusClass">{{ status }}</span>
				<a v-if="showUpstreamCorrection" href="#" class="req-quiet-link req-upstream-trigger" data-testid="req-upstream-trigger" @click.prevent="$emit('request-upstream-correction')">Request upstream correction</a>
			</div>
			<div class="req-editor-reference">{{ reference }}</div>
		</header>
		<div class="req-editor-body">
			<nav class="req-step-nav">
				<button
					v-for="step in steps"
					:key="step.number"
					type="button"
					class="req-step"
					:class="{ 'is-active': step.number === activeStep, 'is-disabled': !step.enabled }"
					:disabled="!step.enabled"
					:data-testid="`req-step-${step.number}`"
					@click="step.enabled && $emit('go-to-step', step.number)"
				>
					<span class="req-step-index">{{ step.number }}</span>
					<span>
						<span class="req-step-label">{{ step.label }}</span>
						<span class="req-step-status" :class="`is-${step.kind}`">{{ step.statusText }}</span>
					</span>
				</button>
			</nav>
			<main class="req-step-main">
				<slot />
			</main>
		</div>
		<footer class="req-editor-footer">
			<slot name="footer">
				<button type="button" class="kt-btn kt-btn-secondary" :disabled="pending" @click="$emit('save-draft')">Save draft</button>
				<button type="button" class="kt-btn kt-btn-primary" :disabled="pending" @click="$emit('continue')">
					{{ continueLabel }}
				</button>
			</slot>
		</footer>
	</div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
	title: { type: String, required: true },
	status: { type: String, default: "Draft" },
	reference: { type: String, default: "" },
	steps: { type: Array, required: true }, // [{ number, label, statusText, kind, enabled }]
	activeStep: { type: Number, required: true },
	continueLabel: { type: String, default: "Continue" },
	pending: Boolean,
	showUpstreamCorrection: Boolean,
});

defineEmits(["go-to-step", "save-draft", "continue", "request-upstream-correction"]);

const STATUS_CLASS = { Draft: "is-draft", "Awaiting Department Approval": "is-attention", "Submitted to Procurement": "is-attention", Authorised: "is-live", Withdrawn: "is-draft", Revoked: "is-draft" };
const statusClass = computed(() => STATUS_CLASS[props.status] || "is-draft");
</script>
