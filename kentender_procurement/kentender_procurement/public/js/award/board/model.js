// The Award board vocabulary (AWD-CHG-001 v0.4 §10; plan D15).
//
// A runtime port of the artboards' own normaliser (`16_award/design/Award
// Artboards.dc.html`, `Component.norm`, the `btn`, `chipOf` and icon tables),
// so a live screen describes itself in the same data the boards were drawn
// from — header, next step, sections (facts, paragraphs, definitions, table,
// empty state, fields, note), actions placed in the decision bar or a row,
// disclosures and a dialog — and `AwdBoard.vue` draws it with the boards'
// markup, container for container. The only additions are live ones: a
// field names the form value it edits (`name`), a button names the action it
// runs (`action`, `args`). The journey and the internal next step are the
// server's own answers, drawn by kentender_core's shared guidance region.

const ICO = {
	file: ["M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z", "M14 2v4a2 2 0 0 0 2 2h4", "M10 9H8", "M16 13H8", "M16 17H8"],
	award: ["M18 8a6 6 0 1 1-12 0 6 6 0 0 1 12 0z", "M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"],
	pen: ["M12 20h9", "M16.5 3.5a2.12 2.12 0 0 1 3 3L7 19l-4 1 1-4Z"],
	scale: ["m16 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z", "m2 16 3-8 3 8c-.87.65-1.92 1-3 1s-2.13-.35-3-1Z", "M7 21h10", "M12 3v18", "M3 7h2c2 0 5-1 7-2 2 1 5 2 7 2h2"],
	mail: ["M4 4h16a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z", "m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"],
	clock: ["M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0z", "M12 6v6l4 2"],
	send: ["m22 2-7 20-4-9-9-4Z", "M22 2 11 13"],
	msg: ["M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"],
	reply: ["M9 17 4 12 9 7", "M20 18v-2a4 4 0 0 0-4-4H4"],
	lock: ["M5 11h14a2 2 0 0 1 2 2v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2z", "M7 11V7a5 5 0 0 1 10 0v4"],
	alert: ["M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0z", "M12 8v4", "M12 16h.01"],
	server: ["M4 2h16a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2z", "M4 14h16a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2v-4a2 2 0 0 1 2-2z", "M6 6h.01", "M6 18h.01"],
	list: ["M8 6h13", "M8 12h13", "M8 18h13", "M3 6h.01", "M3 12h.01", "M3 18h.01"],
	refresh: ["M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8", "M21 3v5h-5", "M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16", "M8 16H3v5"],
};
const SECICO = {
	"Your award tasks": "list", "Evaluation report": "file", "Corrected report": "file", Recommendation: "award", "Professional opinion": "pen", Decision: "scale",
	"Award notice": "mail", "Revised notice": "mail", Notices: "mail", "Acceptance and wait": "clock", Contracting: "send", Request: "msg",
	"Accounting Officer’s comments": "msg", "Supplier response": "reply", "Your response": "reply", Restriction: "lock", "Report correction": "refresh",
	"Reported correction": "refresh", "Correction instruction": "refresh", "Outstanding issue": "alert", Operation: "server", "Evaluation result": "scale",
	"Award result": "award", "Corrected award": "award",
};
const NL = { turn: "Your turn", waiting: "Waiting on someone", done: "Done" };

export const ico = (k) => (ICO[k] || ICO.file).map((d) => ({ d }));
export function sectionIcon(title) {
	if (SECICO[title]) return ico(SECICO[title]);
	if (/^Professional opinion/.test(title)) return ico("pen");
	if (/^Decision cycle/.test(title)) return ico("scale");
	return ico("file");
}

// "~is-critical:Delivery failed" draws a status chip, as on the boards.
export function chipOf(s) {
	const m = /^~([a-z-]+):(.*)$/.exec(String(s ?? ""));
	return m ? { t: m[2], chip: `kt-status ${m[1]}`, hasChip: true, noChip: false } : { t: String(s ?? ""), chip: "", hasChip: false, noChip: true };
}

// A button: "*Label" is primary, "!Label" danger, otherwise secondary; the
// live action it runs rides alongside.
export function btn(spec, action, args, extra) {
	const s = String(spec);
	const cls = s[0] === "*" ? "kt-btn kt-btn-primary" : s[0] === "!" ? "kt-btn kt-btn-danger" : "kt-btn kt-btn-secondary";
	const label = /^[*!]/.test(s) ? s.slice(1) : s;
	return { label, cls, action: action || "noop", args: args || {}, ...(extra || {}) };
}

export const slug = (t) => String(t || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");

function field(f, key, i, form) {
	const name = f.name || "";
	const value = name ? form[name] ?? f.value ?? "" : f.ro || f.value || "";
	const opts = (f.radio || []).map((o, k) => ({ label: o, value: o, name: name || `${key}-${i}`, checked: name ? form[name] === o : f.checked === k }));
	return { label: f.label, name, value, isRo: !!f.ro, isRadio: !!f.radio, isArea: !!f.area, isInput: !f.ro && !f.radio && !f.area, opts, err: f.err || "", req: !!f.req };
}

// b: { hdr: {title, desc}, kicker, chip: [cls, label], next: {k, h, s, l}, guidance: {answer, journey},
//      sec: [...], act: [...], place: "decision" | "row", disc: [...], dlg: {t, b, f, a} }
export function norm(b, form = {}) {
	const hdr = b.hdr || {};
	const n = b.next;
	const o = {
		title: hdr.title || "", desc: hdr.desc || "", hasDesc: !!hdr.desc, isDialog: !!b.dlg, hasChip: !!b.chip,
		chipCls: b.chip ? `kt-status ${b.chip[0]}` : "", chipLabel: b.chip ? b.chip[1] : "",
	};
	o.hasKicker = !!b.kicker;
	o.kicker = b.kicker || "";
	o.kIco = ico(b.kicker === "Award notice" ? "mail" : b.kicker === "Technical work" ? "server" : "award");
	o.guidance = b.guidance || null;
	o.hasLocalNext = !!n && !b.guidance;
	o.nextCls = n ? `kt-next-step is-${n.k}` : "";
	o.nl = n ? n.l || NL[n.k] || "" : "";
	o.nh = n ? n.h : "";
	o.ns = (n && n.s) || "";
	o.hasNs = !!(n && n.s);
	o.sections = (b.sec || []).map((s, si) => {
		const t = s.tbl;
		const nums = (t && t.n) || [];
		return {
			t: s.t, ico: sectionIcon(s.t), cls: s.sec ? "kt-region is-secondary" : "kt-region", anchor: s.anchor || slug(s.t), testid: s.testid || "",
			hasP: !!s.p, p: (s.p || []).map((x) => ({ t: /^[+!]/.test(x) ? x.slice(1) : x, ok: x[0] === "+", warn: x[0] === "!" })),
			hasF: !!s.f, f: (s.f || []).map((x) => { const c = chipOf(x[1]); return { l: x[0], v: c.t, chip: c.chip, hasChip: c.hasChip, noChip: c.noChip }; }),
			hasD: !!s.d, d: (s.d || []).map((x) => ({ l: x[0], v: x[1] })),
			hasTbl: !!t,
			th: t ? t.h.map((h, k) => ({ t: h, cls: nums.includes(k) ? "is-num" : "" })).concat(t.a ? [{ t: "Action", cls: "" }] : []) : [],
			rows: t ? t.r.map((r, ri) => ({ cells: r.map((c, k) => ({ ...chipOf(c), cls: nums.includes(k) ? "is-num" : "" })), hasA: !!t.a,
				a: t.a || "—", action: (t.actions && t.actions[ri]) || { action: "noop" } })) : [],
			hasEmpty: !!s.empty, empty: s.empty || "",
			hasFld: !!s.fld, fld: (s.fld || []).map((f, i) => field(f, `s${si}`, i, form)),
			hasNote: !!s.note, note: s.note || "",
		};
	});
	o.acts = (b.act || []).map((a) => (typeof a === "string" ? btn(a) : a));
	o.hasDecision = b.place === "decision" && o.acts.length > 0;
	o.hasRow = b.place === "row" && o.acts.length > 0;
	o.disc = (b.disc || []).map((d, i) => {
		const x = typeof d === "string" ? { t: d } : d;
		return { t: x.t, a: x.a || null, lines: x.lines || [], key: `${i}:${x.t}` };
	});
	o.hasDisc = o.disc.length > 0;
	if (b.dlg) {
		o.dt = b.dlg.t;
		o.db = b.dlg.b || "";
		o.hasDb = !!b.dlg.b;
		o.dfld = (b.dlg.f || []).map((f, i) => field(f, "dlg", i, form));
		o.dacts = b.dlg.a.map((a) => (typeof a === "string" ? btn(a) : a));
	}
	return o;
}
