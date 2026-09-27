// KenTender public portal runtime — the portal counterpart of kt_desk_page.js
// (BDS-CHG-001 v0.8 plan OD-B, AGENTS.md §6.1/§6.4). One Website page
// (kentender_core/www/kt_portal) serves every supplier route; the owning
// surface's bundle registers here and keeps one Vue app mounted while the
// user moves between its routes with the History API.
//
// Contract (same shape as kentender_core.desk_page where the idea is shared):
//   register(surfaceKey, opts) — opts.prefixes: the paths this surface owns;
//                                opts.mount(el, { initial, portal }) mounts the
//                                app once, on the server-rendered page whose
//                                surface is `surfaceKey`.
//   useRoute(vue)              — { route, go, epoch }: `route` is the current
//                                { path, segments, query }; `go(path, {replace,
//                                query})` stays in-app for an owned path and
//                                loads any other page; `epoch` ticks when the
//                                page is restored from the back/forward cache
//                                so screens revalidate in place.
//   call(method, args, opts)   — fetch against /api/method with the CSRF
//                                header; returns `message`; a failure is an
//                                Error with `status`, `code` (kt_error_code or
//                                exc_type) and `detail`. Never opens a Frappe
//                                message dialog (Website frappe.call does).
//   createCommandRunner / createSequenceGuard / createScreenCache — identical
//                                behaviour to desk_page (shared spec).
//   setTitle(text)             — "<text> · KenTender".

export function createCommandRunner(vue, opts) {
	opts = opts || {};
	const pending = vue.ref(false);
	function run(fn, actionLabel) {
		if (pending.value) return Promise.resolve(null);
		pending.value = true;
		if (opts.onStart) opts.onStart(actionLabel);
		const key = opts.mintKey ? opts.mintKey(actionLabel) : undefined;
		return Promise.resolve()
			.then(() => fn(key))
			.catch((e) => {
				if (opts.onError) opts.onError(e, actionLabel);
				return null;
			})
			.finally(() => {
				pending.value = false;
			});
	}
	return { pending, run };
}

export function createSequenceGuard() {
	let token = 0;
	return {
		next: () => ++token,
		isCurrent: (candidate) => candidate === token,
	};
}

export function createScreenCache() {
	const store = new Map();
	return {
		get: (key) => store.get(key),
		has: (key) => store.has(key),
		set: (key, value) => store.set(key, value),
		remove: (key) => store.delete(key),
		clear: () => store.clear(),
	};
}

const NAV_PREFIXES = { tenders: ["/tenders"], "my-bids": ["/my-bids"], account: ["/account"] };
const STATUS_TEXT = {
	403: "You do not have permission to do this.",
	404: "This item is unavailable or you do not have permission to view it.",
	409: "This record changed since you opened it. Reload to see the current version.",
	429: "Too many requests. Wait a moment and try again.",
};
const FALLBACK_TEXT = "The service could not complete this request. Your saved work is unchanged. Try again.";

function normalise(path) {
	const text = "/" + String(path || "").trim().replace(/^\/+|\/+$/g, "");
	return text === "/" ? "/" : text;
}

function owns(prefix, path) {
	const p = normalise(prefix);
	return path === p || path.startsWith(p + "/");
}

function plain(html) {
	return String(html || "").replace(/<[^>]*>/g, "").trim();
}

function serverMessage(body) {
	try {
		const list = JSON.parse(body._server_messages || "[]");
		const texts = list.map((item) => {
			try {
				return plain(JSON.parse(item).message);
			} catch (e) {
				return plain(item);
			}
		});
		return texts.filter(Boolean).join(" ");
	} catch (e) {
		return "";
	}
}

export function toError(status, body) {
	body = body || {};
	const err = new Error(body.kt_error_message || serverMessage(body) || STATUS_TEXT[status] || FALLBACK_TEXT);
	err.status = status;
	err.code = body.kt_error_code || body.exc_type || "";
	err.detail = body.kt_error_detail || {};
	return err;
}

export function createPortalRuntime(win) {
	win = win || window;
	const doc = win.document;
	const surfaces = {};
	const listeners = new Set();
	let mounted = false;

	function location() {
		const url = new URL(win.location.href);
		const path = normalise(url.pathname);
		return { path, segments: path.split("/").filter(Boolean), query: Object.fromEntries(url.searchParams.entries()) };
	}

	function initial() {
		const el = doc.getElementById("kt-portal-initial");
		if (!el) return {};
		try {
			return JSON.parse(el.textContent || "{}");
		} catch (e) {
			return {};
		}
	}

	function currentSurface() {
		return (doc.body && doc.body.dataset.ktPortalSurface) || "";
	}

	function ownedHere(path) {
		const entry = surfaces[currentSurface()];
		return !!(entry && entry.prefixes.some((prefix) => owns(prefix, path)));
	}

	function syncNav(path) {
		doc.querySelectorAll("[data-kt-portal-nav]").forEach((a) => {
			const prefixes = NAV_PREFIXES[a.getAttribute("data-kt-portal-nav")] || [];
			if (prefixes.some((prefix) => owns(prefix, path))) a.setAttribute("aria-current", "page");
			else a.removeAttribute("aria-current");
		});
	}

	function notify(reason) {
		const loc = location();
		syncNav(loc.path);
		listeners.forEach((fn) => fn(loc, reason));
	}

	function href(path, query) {
		const target = normalise(path);
		const params = new URLSearchParams();
		Object.entries(query || {}).forEach(([k, v]) => {
			if (v !== undefined && v !== null && v !== "") params.append(k, String(v));
		});
		const qs = params.toString();
		return qs ? `${target}?${qs}` : target;
	}

	function go(path, opts) {
		opts = opts || {};
		const target = href(path, opts.query);
		const loc = location();
		if (!ownedHere(normalise(path))) {
			win.location.assign(target);
			return;
		}
		if (target === href(loc.path, loc.query)) {
			if (!opts.replace) notify("same");
			return;
		}
		if (opts.replace) win.history.replaceState({ kt: true }, "", target);
		else win.history.pushState({ kt: true }, "", target);
		notify(opts.replace ? "replace" : "push");
		if (!opts.replace && !opts.keepFocus) {
			const main = doc.getElementById("kt-portal-main");
			if (main) main.focus({ preventScroll: true });
			if (win.scrollTo) win.scrollTo(0, 0);
		}
	}

	function onClick(event) {
		if (event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
		const a = event.target && event.target.closest ? event.target.closest("a[href]") : null;
		if (!a || a.target === "_blank" || a.hasAttribute("download") || a.getAttribute("rel") === "external") return;
		let url;
		try {
			url = new URL(a.href, win.location.href);
		} catch (e) {
			return;
		}
		if (url.origin !== win.location.origin || !ownedHere(normalise(url.pathname))) return;
		event.preventDefault();
		go(url.pathname, { query: Object.fromEntries(url.searchParams.entries()) });
	}

	function onPop() {
		notify("pop");
	}

	function onPageShow(event) {
		if (event.persisted) notify("restore");
	}

	function start() {
		win.addEventListener("popstate", onPop);
		win.addEventListener("pageshow", onPageShow);
		doc.addEventListener("click", onClick);
	}

	// Tests only: a page has exactly one runtime for its whole life.
	function dispose() {
		win.removeEventListener("popstate", onPop);
		win.removeEventListener("pageshow", onPageShow);
		doc.removeEventListener("click", onClick);
		listeners.clear();
		mounted = false;
	}

	function register(surfaceKey, opts) {
		opts = opts || {};
		if (typeof opts.mount !== "function") throw new Error(`kentender_core.portal_page.register(${surfaceKey}): opts.mount is required`);
		surfaces[surfaceKey] = { prefixes: [].concat(opts.prefixes || []).map(normalise), mount: opts.mount };
		if (mounted || currentSurface() !== surfaceKey) return null;
		const el = doc.getElementById("kt-portal-app");
		if (!el) return null;
		mounted = true;
		start();
		return opts.mount(el, { initial: initial(), portal: api });
	}

	function useRoute(vue) {
		const route = vue.ref(location());
		const epoch = vue.ref(0);
		function listener(loc, reason) {
			if (reason === "restore" || reason === "same") epoch.value += 1;
			if (href(loc.path, loc.query) !== href(route.value.path, route.value.query)) route.value = loc;
		}
		vue.onMounted(() => listeners.add(listener));
		vue.onUnmounted(() => listeners.delete(listener));
		return { route, go, epoch, href };
	}

	async function call(method, args, opts) {
		args = args || {};
		opts = opts || {};
		const type = (opts.type || "GET").toUpperCase();
		const csrf = (win.frappe && win.frappe.csrf_token) || "";
		const init = { method: type, credentials: "same-origin", headers: { Accept: "application/json", "X-Frappe-CSRF-Token": csrf } };
		let url = `/api/method/${method}`;
		if (type === "GET") {
			const params = new URLSearchParams();
			Object.entries(args).forEach(([k, v]) => {
				if (v !== undefined && v !== null) params.append(k, typeof v === "object" ? JSON.stringify(v) : String(v));
			});
			const qs = params.toString();
			if (qs) url += `?${qs}`;
		} else {
			init.headers["Content-Type"] = "application/json";
			init.body = JSON.stringify(args);
		}
		let res;
		try {
			res = await win.fetch(url, init);
		} catch (e) {
			throw toError(0, {});
		}
		let body = {};
		try {
			body = await res.json();
		} catch (e) {
			body = {};
		}
		if (!res.ok) throw toError(res.status, body);
		return body.message;
	}

	// A command with files (BDS-CHG-001 v0.8 plan OD-B `upload()`): multipart
	// POST; `fields` as form values, `files` as {field: File}. Same error
	// contract as call().
	async function upload(method, fields, files) {
		const csrf = (win.frappe && win.frappe.csrf_token) || "";
		const form = new win.FormData();
		Object.entries(fields || {}).forEach(([k, v]) => {
			if (v !== undefined && v !== null) form.append(k, typeof v === "object" ? JSON.stringify(v) : String(v));
		});
		Object.entries(files || {}).forEach(([k, file]) => {
			if (file) form.append(k, file, file.name);
		});
		let res;
		try {
			res = await win.fetch(`/api/method/${method}`, { method: "POST", credentials: "same-origin", headers: { Accept: "application/json", "X-Frappe-CSRF-Token": csrf }, body: form });
		} catch (e) {
			throw toError(0, {});
		}
		let body = {};
		try {
			body = await res.json();
		} catch (e) {
			body = {};
		}
		if (!res.ok) throw toError(res.status, body);
		return body.message;
	}

	function setTitle(text) {
		doc.title = text ? `${text} · KenTender` : "KenTender";
	}

	const api = { register, useRoute, go, call, upload, setTitle, initial, dispose, createCommandRunner, createSequenceGuard, createScreenCache };
	return api;
}
