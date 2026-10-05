<script setup>
// ANL §10A.4, §10A.1 rule 11 — Outstanding work: each row is the record title in bold, the matter sentence
// (never repeating the instant), a small tinted badge "Waiting n days" and the quiet "since 16 June, 09:00".
// A row whose Award position could not be read has no waiting time and so no badge (31F).
import RegionHeading from "./RegionHeading.vue";

defineProps({ outstanding: { type: Object, required: true } });
</script>

<template>
	<section class="kt-ap-section is-ruled" data-testid="kt-anl-outstanding">
		<RegionHeading icon="hourglass" :title="outstanding.title" :chip="false" />
		<div class="kt-ap-orows">
			<div v-for="row in outstanding.rows" :key="row.key" class="kt-ap-orow" data-testid="kt-anl-orow">
				<p>
					<strong>{{ row.title }}</strong>{{ " " }}<span class="kt-ap-orow-text">{{ row.text }}</span>
				</p>
				<span v-if="row.waiting || row.since" class="kt-ap-orow-wait">
					<span v-if="row.waiting" class="kt-ap-badge">{{ row.waiting }}</span>
					<span v-if="row.since" class="kt-ap-since">{{ row.since }}</span>
				</span>
			</div>
		</div>
	</section>
</template>
