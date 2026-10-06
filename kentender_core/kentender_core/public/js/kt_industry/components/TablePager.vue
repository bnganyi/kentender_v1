<!-- The one table pager (table-pagination standard): the total at the far left,
     "Rows per page" beside the numbered pages at the right. The pages' state
     lives with the caller — this draws what it is given and reports what the
     reader picks (onPage / onSize); it never pages anything itself.

     Below the smallest page size there is nothing to page, so only the total
     shows. The numbered buttons appear once there is more than one page. -->
<template>
	<div v-if="total > 0" class="kt-pager" data-testid="kt-pager">
		<p class="kt-pager-count" data-testid="kt-pager-count" aria-live="polite">{{ countText }}</p>
		<label v-if="showSize" class="kt-pager-size">
			<span>{{ t("Rows per page") }}</span>
			<select class="input" data-testid="kt-pager-size" :value="pageSize" @change="onSize(Number($event.target.value))">
				<option v-for="size in pageSizes" :key="size" :value="size">{{ size }}</option>
			</select>
		</label>
		<nav v-if="pages > 1" class="kt-pager-nav" :aria-label="t('Pagination')" data-testid="kt-pager-nav">
			<button type="button" class="btn btn-ghost kt-pager-step" data-testid="kt-pager-prev" :disabled="page <= 1" @click="onPage(page - 1)">
				<span aria-hidden="true">‹</span> {{ t("Prev") }}
			</button>
			<span class="kt-pager-status">{{ t("Page") }} {{ page }} {{ t("of") }} {{ pages }}</span>
			<template v-for="slot in slots" :key="slot">
				<span v-if="typeof slot === 'string'" class="kt-pager-gap" aria-hidden="true">…</span>
				<button
					v-else
					type="button"
					class="btn btn-ghost kt-pager-page"
					:class="{ 'is-current': slot === page }"
					:aria-label="`${t('Go to page')} ${slot}`"
					:aria-current="slot === page ? 'page' : null"
					:data-testid="`kt-pager-page-${slot}`"
					@click="slot !== page && onPage(slot)"
				>{{ slot }}</button>
			</template>
			<button type="button" class="btn btn-ghost kt-pager-step" data-testid="kt-pager-next" :disabled="page >= pages" @click="onPage(page + 1)">
				{{ t("Next") }} <span aria-hidden="true">›</span>
			</button>
		</nav>
	</div>
</template>

<script setup>
import { computed } from "vue";
import { pageWindow } from "../pagerWindow.js";

const props = defineProps({
	total: { type: Number, default: 0 },
	page: { type: Number, default: 1 },
	pageSize: { type: Number, default: 10 },
	pageSizes: { type: Array, default: () => [10, 25, 50, 100] },
	// Singular noun for the total: "need" -> "47 needs".
	noun: { type: String, default: "row" },
	// Irregular plurals: "responsibility" -> "responsibilities". Defaults to the noun with an "s".
	nounPlural: { type: String, default: "" },
	onPage: { type: Function, default: () => {} },
	onSize: { type: Function, default: () => {} },
});

const t = (text) => (typeof window !== "undefined" && typeof window.__ === "function" ? window.__(text) : text);

const pages = computed(() => Math.max(1, Math.ceil(props.total / props.pageSize)));
const slots = computed(() => pageWindow(props.page, pages.value));
// Nothing to choose until there is more than the smallest page.
const showSize = computed(() => props.total > Math.min(...props.pageSizes));

const countText = computed(() => {
	const noun = props.total === 1 ? props.noun : props.nounPlural || `${props.noun}s`;
	if (props.total <= props.pageSize) return `${props.total} ${noun}`;
	const from = (props.page - 1) * props.pageSize + 1;
	const to = Math.min(props.page * props.pageSize, props.total);
	return `${t("Showing")} ${from}–${to} ${t("of")} ${props.total} ${noun}`;
});
</script>
