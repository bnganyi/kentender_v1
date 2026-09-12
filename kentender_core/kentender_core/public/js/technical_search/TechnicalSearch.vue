<script setup>
// AUTH-ADR-001 §10 / AUTH-DES-09 — Technical record search: find any
// KenTender record by reference or title, read-only. Only Administrator and
// System Manager ("technical" users) may use this page at all; everyone else
// gets a masked not-found from the server, rendered here as the Forbidden
// state (never a confirmation that this page exists).
//
// The verdict is resolved before anything else paints (§3A.1): the first
// call on mount is a search with an empty query. A 404 means "not
// technical" → Forbidden; any other response means the caller is technical
// and the screen is simply Empty (no query typed yet).
import { onMounted, ref } from "vue";
import { technicalSearchApi } from "./data/technicalSearchApi.js";

const phase = ref("loading"); // loading | forbidden | error | ready
const query = ref("");
const searchedQuery = ref("");
const rows = ref([]);
const searching = ref(false);
const searchError = ref("");

async function verify() {
	phase.value = "loading";
	try {
		await technicalSearchApi.search("", 25);
		phase.value = "ready";
	} catch (error) {
		if (error.httpStatus === 404) phase.value = "forbidden";
		else phase.value = "error";
	}
}

async function runSearch() {
	const q = query.value.trim();
	if (!q) {
		searchedQuery.value = "";
		rows.value = [];
		searchError.value = "";
		return;
	}
	searching.value = true;
	searchError.value = "";
	try {
		rows.value = await technicalSearchApi.search(q, 25);
		searchedQuery.value = q;
	} catch (error) {
		if (error.httpStatus === 404) {
			phase.value = "forbidden";
		} else {
			searchError.value = error.message;
			rows.value = [];
		}
	} finally {
		searching.value = false;
	}
}

function openRecord(row) {
	frappe.set_route(...row.route);
}

onMounted(verify);
</script>

<template>
	<div class="kt-industry kt-setup-root" data-testid="kt-ts-root">
		<div class="kt-setup-shell">
			<header class="kt-setup-header">
				<span class="kt-eyebrow">{{ __("Technical access") }}</span>
				<h1 class="kt-setup-title">{{ __("Technical record search") }}</h1>
				<p class="kt-setup-lede">
					{{ __("Find any KenTender record by reference or title. Read-only; technical access grants no business action.") }}
				</p>
			</header>

			<div v-if="phase === 'loading'" class="kt-card kt-blueprint" data-testid="kt-ts-loading">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<span class="kt-eyebrow">{{ __("Loading") }}</span>
				<div class="kt-skel" style="width:88%" />
				<div class="kt-skel" style="width:64%" />
				<div class="kt-skel" style="width:76%" />
			</div>

			<div v-else-if="phase === 'forbidden'" class="kt-card kt-blueprint kt-empty" data-testid="kt-ts-forbidden">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h2>{{ __("You do not have access to Technical record search") }}</h2>
				<p>{{ __("This area needs Administrator or System Manager access. Ask your KenTender administrator to grant it.") }}</p>
			</div>

			<div v-else-if="phase === 'error'" class="kt-card kt-blueprint kt-empty" data-testid="kt-ts-error">
				<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
				<h2>{{ __("Technical record search could not be loaded") }}</h2>
				<p>{{ __("Try again. If the problem continues, contact support.") }}</p>
				<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-ts-retry" @click="verify">
					{{ __("Try again") }}
				</button>
			</div>

			<template v-else>
				<div class="kt-search-row">
					<input
						v-model="query"
						class="kt-input"
						type="search"
						:placeholder="__('Search by reference or title')"
						data-testid="kt-ts-input"
						@keydown.enter="runSearch"
					>
					<button
						type="button"
						class="kt-btn kt-btn-primary"
						:disabled="searching"
						data-testid="kt-ts-search"
						@click="runSearch"
					>{{ __("Search") }}</button>
				</div>

				<div v-if="searchError" class="kt-card kt-blueprint kt-empty" data-testid="kt-ts-error">
					<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
					<h2>{{ __("Technical record search could not be loaded") }}</h2>
					<p>{{ __("Try again. If the problem continues, contact support.") }}</p>
					<button type="button" class="kt-btn kt-btn-secondary" data-testid="kt-ts-retry" @click="runSearch">
						{{ __("Try again") }}
					</button>
				</div>

				<div v-else-if="!searchedQuery" class="kt-card kt-blueprint kt-empty" data-testid="kt-ts-empty">
					<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
					<h2>{{ __("Enter a reference or title") }}</h2>
					<p>{{ __("Any KenTender record — need, plan, budget, requisition or tender — opens read-only from here.") }}</p>
				</div>

				<div v-else-if="!rows.length" class="kt-card kt-blueprint kt-empty" data-testid="kt-ts-nomatch">
					<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
					<h2>{{ __('No record matches "{0}"', [searchedQuery]) }}</h2>
					<p>{{ __("Check the reference and try again.") }}</p>
				</div>

				<div v-else class="kt-card kt-blueprint kt-table-card" data-testid="kt-ts-results">
					<i class="kt-corner tl" /><i class="kt-corner tr" /><i class="kt-corner bl" /><i class="kt-corner br" />
					<div class="kt-table-scroll">
						<table class="kt-table">
							<thead>
								<tr>
									<th>{{ __("Reference") }}</th>
									<th>{{ __("Record type") }}</th>
									<th>{{ __("Title") }}</th>
									<th>{{ __("Status") }}</th>
									<th>{{ __("Open") }}</th>
								</tr>
							</thead>
							<tbody>
								<tr
									v-for="row in rows"
									:key="row.doctype + ':' + row.name"
									data-testid="kt-ts-row"
								>
									<td>{{ row.reference }}</td>
									<td>{{ row.record_type }}</td>
									<td>{{ row.title || "—" }}</td>
									<td><span v-if="row.status" class="kt-status">{{ row.status }}</span><span v-else>—</span></td>
									<td>
										<a href="#" data-testid="kt-ts-open" @click.prevent="openRecord(row)">{{ __("Open") }}</a>
									</td>
								</tr>
							</tbody>
						</table>
					</div>
				</div>
			</template>
		</div>
	</div>
</template>

<style scoped>
.kt-search-row {
	display: flex;
	gap: 10px;
	align-items: stretch;
	margin-bottom: 20px;
}
.kt-search-row .kt-input {
	flex: 1 1 auto;
}
</style>
