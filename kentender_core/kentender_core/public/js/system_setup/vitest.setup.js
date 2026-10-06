// The bench runtime supplies window.__ (translation) and window.frappe; the
// SFCs use both from template scope AND from <script setup> computeds, so the
// test environment defines the same globals.
globalThis.__ = (text, args) =>
	String(text).replace(/\{(\d+)\}/g, (_, index) => (args ? String(args[Number(index)]) : ""));
globalThis.frappe = globalThis.frappe || { set_route: () => {} };

// `kentender_core.desk_page.createCommandRunner` (AGENTS.md §6.4) is a bench
// global; the specs get the same contract: a pending ref held across the
// awaited action, onStart/onError callbacks, errors swallowed and surfaced.
globalThis.kentender_core = globalThis.kentender_core || {};
globalThis.kentender_core.desk_page = globalThis.kentender_core.desk_page || {
	createCommandRunner(vue, opts = {}) {
		const pending = vue.ref(false);
		return {
			pending,
			async run(action) {
				pending.value = true;
				try {
					if (opts.onStart) opts.onStart();
					return await action();
				} catch (error) {
					if (opts.onError) opts.onError(error);
					return null;
				} finally {
					pending.value = false;
				}
			},
		};
	},
	// Same contract as kt_desk_page.js: only the newest ticket is current.
	createSequenceGuard() {
		let token = 0;
		return { next: () => ++token, isCurrent: (candidate) => candidate === token };
	},
};

// The register tabs host kentender_core's shared table pager through
// pager_shared/TablePagerHost.vue; in the browser the helper comes from
// kt_industry_pager.bundle.js, so the same bundle module is loaded here.
globalThis.frappe.provide =
	globalThis.frappe.provide ||
	((path) => {
		let node = globalThis;
		for (const part of path.split(".")) {
			node[part] = node[part] || {};
			node = node[part];
		}
		return node;
	});
globalThis.window.kentender_core = globalThis.kentender_core;
await import("./../kt_industry/kt_industry_pager.bundle.js");
