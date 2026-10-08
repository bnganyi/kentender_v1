// The Bid Evaluation board vocabulary (EVL-CHG-001 v0.4 §9; plan D13).
//
// A runtime port of the artboards' own kit (`15_bid_evaluation/design/evl/
// evl-kit.js`: the block builders, the status-chip classifier, the table-cell
// markers and `normBlock`/`norm`), so a live screen describes itself in exactly
// the vocabulary its boards were drawn in and `EvlBoard.vue` renders it with the
// boards' classes, container for container. The only additions are live ones:
// a field or choice names the form value it edits (`name`), and a button or a
// table-cell button names the action it runs (`action`). People are recognised
// from the names the server supplied, not from a fixture table.

export const p = (t, o) => ({ k: "p", t, ...(o || {}) });
export const f = (...items) => ({ k: "facts", items });
export const kv = (rows, o) => ({ k: "kv", rows, ...(o || {}) });
export const tb = (cols, rows, o) => ({ k: "table", cols, rows, ...(o || {}) });
export const n = (tone, t, d, o) => ({ k: "notice", tone, t, d, ...(o || {}) });
export const fi = (label, value, o) => ({ k: "field", label, value, ...(o || {}) });
export const ra = (label, opts, sel, o) => ({ k: "radios", label, opts, sel, ...(o || {}) });
export const sg = (label, opts, sel, o) => ({ k: "seg", label, opts, sel, ...(o || {}) });
export const cb = (t, on, o) => ({ k: "check", t, on, ...(o || {}) });
export const ds = (t, lines, o) => ({ k: "disc", t, lines: [].concat(lines || []), ...(o || {}) });
export const at = (t, meta, o) => ({ k: "attn", t, meta, ...(o || {}) });
export const lk = (links, o) => ({ k: "links", links, ...(o || {}) });
export const ev = (items, o) => ({ k: "evid", items, ...(o || {}) });
export const task = (tt, ref, state, btn, o) => ({ k: "task", tt, ref, state, btn, ...(o || {}) });
export const fb = (cells, o) => ({ k: "filter", cells, ...(o || {}) });
export const em = (t, btn, icon, sub, o) => ({ k: "empty", t, btn, eic: icon, sub, ...(o || {}) });

// A cell or button marker: "@" a button, "#" an input look, "*" strong, "~" disabled.
export const button = (label, action, o) => ({ label, action, ...(o || {}) });

const CHIP = {
	"is-live": ["Meets", "Responsive", "Report sent", "Resolved", "No conflict", "Received"],
	"is-critical": ["Does not meet", "Not responsive", "Cancelled", "Excluded change", "Returned", "Conflict declared"],
	"is-attention": ["Needs review", "Your signature needed", "Received late", "Reply overdue", "Delivery problem"],
	"is-pending": ["Not applicable", "Not ranked", "Not joined", "Awaiting signature", "Not assessed — mandatory requirement not met", "Not considered", "Declaration pending", "Declaration owed"],
};
export function chipOf(t) {
	for (const k in CHIP) if (CHIP[k].indexOf(t) >= 0) return k;
	if (/^(Signed|Joined|Present) /.test(t)) return "is-live";
	if (/^Left /.test(t)) return "is-attention";
	return null;
}

export const initials = (name) => String(name || "").split(" ").filter(Boolean).map((x) => x[0]).slice(0, 2).join("");

const ICONS = {
	users: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 3a4 4 0 1 0 0 8a4 4 0 1 0 0-8 M22 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75",
	userCheck: "M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 3a4 4 0 1 0 0 8a4 4 0 1 0 0-8 M16 11l2 2 4-4",
	clipboard: "M9 2h6v4H9z M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2 M9 14l2 2 4-4",
	search: "M11 3a8 8 0 1 0 0 16a8 8 0 1 0 0-16 M21 21l-4.3-4.3",
	messages: "M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z M8 9h8 M8 13h5",
	mail: "M2 5h20v14H2z M22 6l-10 7L2 6",
	reply: "M9 17l-5-5 5-5 M20 18v-2a4 4 0 0 0-4-4H4",
	pen: "M12 20h9 M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z",
	file: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8",
	alert: "M12 3l9 16H3z M12 10v4 M12 17h.01",
	shield: "M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10 M9 12l2 2 4-4",
	pause: "M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20 M10 15V9 M14 15V9",
	layout: "M3 3h18v18H3z M3 9h18 M9 21V9",
	calendar: "M3 4h18v18H3z M16 2v4 M8 2v4 M3 10h18",
	banknote: "M2 6h20v12H2z M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6 M6 12h.01 M18 12h.01",
	listChecks: "M3 17l2 2 4-4 M3 7l2 2 4-4 M13 6h8 M13 12h8 M13 18h8",
	clip: "M21.4 11l-9.2 9.2a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5",
	history: "M3 12a9 9 0 1 0 3-6.7L3 8 M3 3v5h5 M12 7v5l4 2",
	buoy: "M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20 M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8 M4.9 4.9l4.3 4.3 M14.8 14.8l4.3 4.3 M14.8 9.2l4.3-4.3 M4.9 19.1l4.3-4.3",
	send: "M22 2L11 13 M22 2l-7 20-4-9-9-4z",
	check: "M20 6L9 17l-5-5",
	refresh: "M3 12a9 9 0 0 1 15-6.7L21 8 M21 3v5h-5 M21 12a9 9 0 0 1-15 6.7L3 16 M3 21v-5h5",
	login: "M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4 M10 17l5-5-5-5 M15 12H3",
	flag: "M4 22V4 M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1",
	undo: "M9 14L4 9l5-5 M4 9h10.5a5.5 5.5 0 0 1 0 11H11",
	download: "M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M7 10l5 5 5-5 M12 15V3",
	eye: "M2 12s3-7 10-7 10 7 10 7-3 7-10 7S2 12 2 12 M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6",
	building: "M3 21h18 M5 21V7l7-4 7 4v14 M9 21v-6h6v6",
	ban: "M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20 M4.9 4.9l14.2 14.2",
	loader: "M12 2v4 M12 18v4 M4.9 4.9l2.9 2.9 M16.2 16.2l2.9 2.9 M2 12h4 M18 12h4 M4.9 19.1l2.9-2.9 M16.2 7.8l2.9-2.9",
};
export const IC = ICONS;
const TITLE_IC = [[/signature/, ICONS.pen], [/attendance|committee members|current committee|appointed committee|^committee$|positions/, ICONS.users], [/session/, ICONS.calendar],
	[/verification/, ICONS.shield], [/clarification|question|reply|request/, ICONS.messages], [/financial|funding/, ICONS.banknote],
	[/comparison|results|findings|unresolved|evaluations/, ICONS.listChecks], [/evidence|supporting|documents/, ICONS.clip], [/history/, ICONS.history],
	[/support issue/, ICONS.buoy], [/source/, ICONS.building], [/summary|report|recommendation|tender and committee|conclusion/, ICONS.file]];
const titleIcon = (t) => { if (!t) return ""; const s = t.toLowerCase(); for (const [re, ic] of TITLE_IC) if (re.test(s)) return ic; return ""; };
const BTN_IC = [[/^sign/i, ICONS.pen], [/^(send|retry notice|retry delivery)/i, ICONS.send], [/^(appoint|assign|complete declaration)/i, ICONS.userCheck], [/^replace/i, ICONS.users],
	[/^start discussion/i, ICONS.messages], [/^join/i, ICONS.login], [/^(raise|record concern|send concern)/i, ICONS.flag], [/report issue|view issue|submit issue/i, ICONS.buoy],
	[/^(refresh|try again|check signature)/i, ICONS.refresh], [/^(return|withdraw)/i, ICONS.undo], [/^download/i, ICONS.download], [/^(view|open|preview|review latest)/i, ICONS.eye],
	[/^revise/i, ICONS.pen], [/^(record|save|authorise)/i, ICONS.check]];
const btnIcon = (t) => { for (const [re, ic] of BTN_IC) if (re.test(t)) return ic; return ""; };

function normButton(b) {
	if (!b) return null;
	const o = typeof b === "string" ? { label: b } : b;
	let label = String(o.label || "");
	const dis = label[0] === "~" || !!o.disabled;
	if (label[0] === "~") label = label.slice(1);
	const icon = btnIcon(label);
	return { t: label, dis, icon, hasIcon: !!icon, action: o.action || "", args: o.args || null, testid: o.testid || "" };
}

export function normBlock(b, { mobile = false, people = {} } = {}) {
	const o = { ...b };
	o["is_" + b.k] = true;
	o.icon = b.title ? b.icon || titleIcon(b.title) : "";
	o.hasIcon = !!o.icon;
	o.titleMain = !!b.title && !b.sec;
	o.titleSec = !!b.title && !!b.sec;
	const vx = (v) => { const c = chipOf(String(v)); const pn = people[v]; return { chip: !!c, cls: c || "", person: !c && !!pn, ini: pn || "", plain: !c && !pn }; };
	if (b.k === "p") { o.plain = !b.muted && !b.strong; o.isMuted = !!b.muted; o.isStrong = !!b.strong; }
	if (b.k === "facts") o.itemList = b.items.map(([l, v]) => ({ l, v, ...vx(v) }));
	if (b.k === "kv") { o.rowList = b.rows.map(([l, v]) => ({ l, v, ...vx(v) })); o.cols = mobile ? "minmax(0,1fr)" : "220px minmax(0,1fr)"; }
	if (b.k === "table") {
		const numIdx = b.cols.map((_c, i) => i).filter((i) => b.rows.some((r) => typeof r[i] !== "object" && /^\*?KES /.test(String(r[i]))) || (b.num || []).indexOf(i) >= 0);
		o.ths = b.cols.map((t, i) => ({ t, td: numIdx.indexOf(i) >= 0 ? "is-num" : "" }));
		o.trs = b.rows.map((r) => ({ cells: r.map((c, i) => cellOf(c, numIdx.indexOf(i) >= 0, people)) }));
		o.hasCaption = !!b.caption;
		o.paged = b.paged || "";
	}
	if (b.k === "notice") { o.cls = "is-" + b.tone; o.iWarn = b.tone === "warning"; o.iCrit = b.tone === "critical"; o.iInfo = b.tone === "info" || b.tone === "live"; o.hasD = !!b.d; }
	if (b.k === "field") {
		o.isArea = !!b.area; o.isSelect = !!b.select; o.isFile = !!b.file; o.isInput = !b.area && !b.select && !b.file;
		o.rowsN = b.rows || 3; o.hasHelp = !!b.help; o.hasErr = !!b.err; o.hasErrd = !!b.errd;
	}
	if (b.k === "radios" || b.k === "seg") o.options = b.opts.map((t, i) => ({ t, value: (b.values || b.opts)[i], on: i === b.sel }));
	if (b.k === "attn") { o.hasMeta = !!b.meta; const nm = Object.keys(people).find((x) => String(b.meta || "").indexOf(x) >= 0); o.hasWho = !!nm; o.ini = nm ? people[nm] : ""; }
	if (b.k === "disc") { o.linkList = (b.links || []).map((l) => (typeof l === "string" ? { t: l } : { t: l.label, action: l.action, args: l.args })); o.hasLinks = o.linkList.length > 0; o.lineList = o.lines.map((t) => ({ t })); }
	if (b.k === "links") o.linkList = b.links.map((l) => (typeof l === "string" ? { t: l } : { t: l.label, action: l.action, args: l.args }));
	if (b.k === "evid") o.itemList = b.items.map((it) => (Array.isArray(it) ? { t: it[0], b: it[1] || "View evidence" } : { t: it.label, b: it.button || "View evidence", action: it.action, args: it.args }));
	if (b.k === "filter") o.cellList = b.cells.map(([l, v, opt]) => ({ l, v: v || "", cls: opt && opt.wide ? "is-wide" : "", sel: !!(opt && opt.select), inp: !(opt && opt.select), ph: (opt && opt.ph) || "", name: (opt && opt.name) || "", options: (opt && opt.options) || [] }));
	if (b.k === "empty") { o.hasBtn = !!b.btn; o.hasSub = !!b.sub; o.eicon = ICONS[b.eic] || ICONS.layout; }
	if (b.k === "task") o.button = normButton(b.btn);
	return o;
}

function cellOf(raw, num, people) {
	const td = num ? "is-num" : "";
	if (raw && typeof raw === "object") {
		if (raw.select) return { sel: true, name: raw.select, options: raw.options || [], td, testid: raw.testid || "", err: raw.error || "" };
		if (raw.input) return { field: true, name: raw.input, td, testid: raw.testid || "", err: raw.error || "" };
		if (raw.text !== undefined) return { t: raw.text, txt: true, note: raw.note || "", td };
		return { t: raw.label, btn: true, td, action: raw.action, args: raw.args || null, testid: raw.testid || "" };
	}
	const s = String(raw == null ? "" : raw);
	if (s[0] === "@") return { t: s.slice(1), btn: true, td };
	if (s[0] === "#") return { t: s.slice(1), inp: true, td };
	if (s[0] === "*") return { t: s.slice(1), strong: true, td };
	const c = chipOf(s);
	if (c) return { t: s, chip: true, cls: c, td };
	if (people[s]) return { t: s, person: true, ini: people[s], td };
	return { t: s, txt: true, td };
}

const TNAMES = ["Prepare", "Review", "Report"];

// The server's journey (next_step.journey) in the boards' tracker words.
export function trackerOf(journey) {
	if (!journey || !journey.stages) return [];
	return journey.stages.map((s, i) => ({
		name: TNAMES[i] || s.label, num: String(i + 1),
		cls: s.marker === "done" ? "is-done" : s.marker === "current" ? "is-current" : s.marker === "blocked" ? "is-blocked" : "",
		st: s.marker === "done" ? "✓ Done" : s.marker === "current" ? "Current · " + (s.holder || "") : s.marker === "blocked" ? "Blocked" : "Not started",
	}));
}

// The server's next-step answer in the boards' guidance words.
export function nextOf(answer) {
	if (!answer || answer.kind === "not_involved") return null;
	const k = answer.kind === "your_turn" || answer.kind === "your_turn_blocked" ? "turn" : answer.kind === "done" ? "done" : "wait";
	return { k, label: answer.kind === "timed" ? "Scheduled" : answer.label, h: answer.headline, s: answer.sentence };
}

export function norm(board, { people = {} } = {}) {
	const mobile = board.size === "m";
	const nx = board.nx || null;
	const tr = board.tr || [];
	const pri = normButton(board.pri);
	const sec = (board.sec || []).map(normButton);
	const dlg = board.dlg
		? { ...board.dlg, blocks: (board.dlg.blocks || []).map((x) => normBlock(x, { mobile, people })), pri: normButton(board.dlg.pri) || { t: "", dis: true },
			sec: (board.dlg.sec || [{ label: "Cancel", action: "close-dialog" }]).map(normButton), hasCons: !!board.dlg.cons }
		: null;
	return {
		icon: board.icon || ICONS.file, isMobile: mobile,
		back: board.back || "", hasBack: !!board.back, backAction: board.backAction || "",
		title: board.title || "", desc: board.desc || "", hasHead: !!board.title, hasDesc: !!board.desc,
		tabs: (board.tabs || []).map((t, i) => ({ t: t.label || t, action: t.action || "", args: t.args || null, on: i === (board.tab || 0) })), hasTabs: !!(board.tabs && board.tabs.length),
		tr, hasTr: tr.length > 0,
		nx: nx || {}, nxTurn: !!nx && nx.k === "turn", nxWait: !!nx && nx.k === "wait", nxDone: !!nx && nx.k === "done",
		nxLabel: nx ? nx.label || (nx.k === "turn" ? "Your turn" : nx.k === "wait" ? "Waiting on someone" : "Done") : "", hasNxS: !!(nx && nx.s),
		notInvolved: board.notInvolved || "", hasNotInvolved: !!board.notInvolved,
		hasGuide: tr.length > 0 || !!nx || !!board.notInvolved,
		blocks: (board.blocks || []).map((x) => normBlock(x, { mobile, people })),
		pri: pri || { t: "", dis: true }, hasPri: !!pri, sec, onlySec: !pri && sec.length > 0,
		cons: board.cons || "", hasCons: !!board.cons,
		dlg: dlg || {}, hasDlg: !!dlg,
	};
}
