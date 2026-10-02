<script setup>
// Where this task sits in the bid (owner request, 2 Oct 2026): the five tasks in
// their fixed order, numbered, each with its state; the current one marked; and
// Previous / Next links to its neighbours. The server sends the whole row (the
// "step" of a task read); nothing here decides an order or a state. A bidder may
// still work out of order: this only makes the order, and the progress, visible.
defineProps({
	step: { type: Object, required: true },
});
</script>

<template>
	<nav class="bds-stepper" :aria-label="__('Bid tasks')" data-testid="bds-stepper">
		<ol class="bds-stepper-list">
			<li v-for="t in step.tasks" :key="t.key">
				<a :href="t.href" class="bds-stepper-item" :class="['is-' + t.tone, { 'is-current': t.current }]" :aria-current="t.current ? 'step' : null" :aria-label="__('Step {0}: {1}, {2}', [t.number, t.short, t.hint || t.status])" :title="t.hint || t.status">
					<span class="bds-stepper-number" aria-hidden="true">{{ t.number }}</span>
					<span class="bds-stepper-name">{{ t.short }}</span>
				</a>
			</li>
		</ol>
		<div class="bds-stepper-line">
			<a v-if="step.previous" :href="step.previous.href" class="bds-stepper-previous" data-testid="bds-stepper-previous">← {{ step.previous.label }}</a>
			<span v-else></span>
			<span class="bds-stepper-where" data-testid="bds-stepper-where">{{ __("Step {0} of {1}", [step.number, step.of]) }}</span>
			<a v-if="step.next" :href="step.next.href" class="bds-stepper-next" data-testid="bds-stepper-next">{{ step.next.label }} →</a>
			<span v-else></span>
		</div>
	</nav>
</template>
