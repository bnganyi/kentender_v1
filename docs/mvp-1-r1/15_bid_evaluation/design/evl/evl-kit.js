(function () {
  if (window.EVL && window.EVL.__ready) return;
  const E = window.EVL = window.EVL || {};
  E.__ready = true;
  E.boards = E.boards || [];
  E.GROUPS = ['D01 Work workspace', 'D02 Committee and declaration', 'D03 Evaluation record', 'D04 Requirement review', 'D05 Committee discussion', 'D06 Clarification', 'D07 Report and signing', 'D08 Issues, verification and correction', 'Pause and cancellation', 'Shared page states'];
  let seq = 0;
  E.add = (...bs) => bs.forEach(b => { const i = E.boards.findIndex(x => x.id === b.id); if (i >= 0) { b._s = E.boards[i]._s; E.boards[i] = b; } else { b._s = seq++; E.boards.push(b); } });
  const ord = (b) => { if (!b.after) return b._s; const base = E.boards.find(x => x.id === b.after); return base ? base._s + 0.5 + b._s / 1e6 : b._s; };
  E.sorted = () => E.boards.slice().sort((a, b) => (E.GROUPS.indexOf(a.g) - E.GROUPS.indexOf(b.g)) || (ord(a) - ord(b)));

  E.P = {
    amina: ['Amina Hassan', 'Accounting Officer'], charles: ['Charles Mutiso', 'Head of Procurement'],
    grace: ['Grace Wambui', 'Chair'], peter: ['Peter Mugo', 'Member'], ruth: ['Ruth Achieng', 'Member'],
    brian: ['Brian Wafula', 'Secretary'], david: ['David Ouma', 'Supplier Representative'],
    naomi: ['Naomi Chebet', 'Auditor'], esther: ['Esther Njeri', 'Technical support'], none: ['Signed-in user', '']
  };
  E.TN = 'TND-MOH-2027-033'; E.TT = 'Supply and delivery of business laptops'; E.AF = 'Afya Digital Supplies Limited';
  E.KES = 'KES 46,400,000.00';


  E.IC = {
    users: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 3a4 4 0 1 0 0 8a4 4 0 1 0 0-8 M22 21v-2a4 4 0 0 0-3-3.87 M16 3.13a4 4 0 0 1 0 7.75',
    userCheck: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 3a4 4 0 1 0 0 8a4 4 0 1 0 0-8 M16 11l2 2 4-4',
    clipboard: 'M9 2h6v4H9z M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2 M9 14l2 2 4-4',
    search: 'M11 3a8 8 0 1 0 0 16a8 8 0 1 0 0-16 M21 21l-4.3-4.3',
    messages: 'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z M8 9h8 M8 13h5',
    mail: 'M2 5h20v14H2z M22 6l-10 7L2 6',
    reply: 'M9 17l-5-5 5-5 M20 18v-2a4 4 0 0 0-4-4H4',
    pen: 'M12 20h9 M16.5 3.5a2.1 2.1 0 0 1 3 3L7 19l-4 1 1-4z',
    file: 'M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z M14 2v6h6 M16 13H8 M16 17H8 M10 9H8',
    alert: 'M12 3l9 16H3z M12 10v4 M12 17h.01',
    shield: 'M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10 M9 12l2 2 4-4',
    pause: 'M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20 M10 15V9 M14 15V9',
    layout: 'M3 3h18v18H3z M3 9h18 M9 21V9',
    calendar: 'M3 4h18v18H3z M16 2v4 M8 2v4 M3 10h18',
    banknote: 'M2 6h20v12H2z M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6 M6 12h.01 M18 12h.01',
    listChecks: 'M3 17l2 2 4-4 M3 7l2 2 4-4 M13 6h8 M13 12h8 M13 18h8',
    clip: 'M21.4 11l-9.2 9.2a6 6 0 0 1-8.5-8.5l9.2-9.2a4 4 0 0 1 5.7 5.7l-9.2 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5',
    history: 'M3 12a9 9 0 1 0 3-6.7L3 8 M3 3v5h5 M12 7v5l4 2',
    buoy: 'M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20 M12 8a4 4 0 1 0 0 8a4 4 0 1 0 0-8 M4.9 4.9l4.3 4.3 M14.8 14.8l4.3 4.3 M14.8 9.2l4.3-4.3 M4.9 19.1l4.3-4.3',
    send: 'M22 2L11 13 M22 2l-7 20-4-9-9-4z',
    check: 'M20 6L9 17l-5-5',
    refresh: 'M3 12a9 9 0 0 1 15-6.7L21 8 M21 3v5h-5 M21 12a9 9 0 0 1-15 6.7L3 16 M3 21v-5h5',
    login: 'M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4 M10 17l5-5-5-5 M15 12H3',
    flag: 'M4 22V4 M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1',
    undo: 'M9 14L4 9l5-5 M4 9h10.5a5.5 5.5 0 0 1 0 11H11',
    download: 'M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4 M7 10l5 5 5-5 M12 15V3',
    eye: 'M2 12s3-7 10-7 10 7 10 7-3 7-10 7S2 12 2 12 M12 9a3 3 0 1 0 0 6a3 3 0 1 0 0-6',
    building: 'M3 21h18 M5 21V7l7-4 7 4v14 M9 21v-6h6v6',
    ban: 'M12 2a10 10 0 1 0 0 20a10 10 0 1 0 0-20 M4.9 4.9l14.2 14.2',
    loader: 'M12 2v4 M12 18v4 M4.9 4.9l2.9 2.9 M16.2 16.2l2.9 2.9 M2 12h4 M18 12h4 M4.9 19.1l2.9-2.9 M16.2 7.8l2.9-2.9'
  };
  const I = E.IC;
  const TITLE_IC = [[/signature/, I.pen], [/attendance|committee members|current committee|appointed committee|^committee$|positions/, I.users], [/session/, I.calendar],
    [/verification/, I.shield], [/clarification|question|reply|request/, I.messages], [/financial|funding/, I.banknote],
    [/comparison|results|findings|unresolved|evaluations/, I.listChecks], [/evidence|supporting|documents/, I.clip], [/history/, I.history],
    [/support issue/, I.buoy], [/source/, I.building], [/summary|report|recommendation|tender and committee|conclusion/, I.file]];
  const titleIcon = (t) => { if (!t) return ''; const s = t.toLowerCase(); for (const [re, ic] of TITLE_IC) if (re.test(s)) return ic; return ''; };
  const BTN_IC = [[/^sign/i, I.pen], [/^(send|retry notice|retry delivery)/i, I.send], [/^(appoint|assign|complete declaration)/i, I.userCheck], [/^replace/i, I.users],
    [/^start discussion/i, I.messages], [/^join/i, I.login], [/^(raise|record concern|send concern)/i, I.flag], [/report issue|view issue|submit issue/i, I.buoy],
    [/^(refresh|try again|check signature)/i, I.refresh], [/^(return|withdraw)/i, I.undo], [/^download/i, I.download], [/^(view|open|preview|review latest)/i, I.eye],
    [/^revise/i, I.pen], [/^(record|save|authorise)/i, I.check]];
  const btnIcon = (t) => { for (const [re, ic] of BTN_IC) if (re.test(t)) return ic; return ''; };
  const GROUP_IC = { 'D01 Work workspace': I.layout, 'D02 Committee and declaration': I.userCheck, 'D03 Evaluation record': I.clipboard, 'D04 Requirement review': I.search,
    'D05 Committee discussion': I.messages, 'D06 Clarification': I.mail, 'D07 Report and signing': I.file, 'D08 Issues, verification and correction': I.shield,
    'Pause and cancellation': I.pause, 'Shared page states': I.layout };
  E.PEOPLE = {};
  ['Amina Hassan','Charles Mutiso','Grace Wambui','Peter Mugo','Ruth Achieng','Brian Wafula','David Ouma','Naomi Chebet','Esther Njeri','Samuel Otieno'].forEach(n => E.PEOPLE[n] = n.split(' ').map(x => x[0]).join(''));

  // blocks
  E.p = (t, o) => ({ k: 'p', t, ...(o || {}) });
  E.f = (...items) => ({ k: 'facts', items });
  E.kv = (rows, o) => ({ k: 'kv', rows, ...(o || {}) });
  E.tb = (cols, rows, o) => ({ k: 'table', cols, rows, ...(o || {}) });
  E.n = (tone, t, d, o) => ({ k: 'notice', tone, t, d, ...(o || {}) });
  E.fi = (label, value, o) => ({ k: 'field', label, value, ...(o || {}) });
  E.ra = (label, opts, sel, o) => ({ k: 'radios', label, opts, sel, ...(o || {}) });
  E.sg = (label, opts, sel, o) => ({ k: 'seg', label, opts, sel, ...(o || {}) });
  E.cb = (t, on) => ({ k: 'check', t, on });
  E.ds = (t, lines, o) => ({ k: 'disc', t, lines: [].concat(lines || []), ...(o || {}) });
  E.at = (t, meta, o) => ({ k: 'attn', t, meta, ...(o || {}) });
  E.lk = (links, o) => ({ k: 'links', links, ...(o || {}) });
  E.ev = (items, o) => ({ k: 'evid', items, ...(o || {}) });
  E.task = (tt, ref, state, btn) => ({ k: 'task', tt, ref, state, btn });
  E.fb = (cells, o) => ({ k: 'filter', cells, ...(o || {}) });
  E.em = (t, btn, icon, sub) => ({ k: 'empty', t, btn, eic: icon, sub });

  // shared compositions
  E.recHead = (o) => Object.assign({ title: E.TT, desc: E.TN, crumb: ['Bid evaluation', E.TN] }, o || {});
  E.summary = (o) => E.kv([
    ['Recommendation', (o && o.rec) || 'Afya Digital Supplies Limited'],
    ['Evaluated total', (o && o.total) || E.KES],
    ['Eligibility', 'Meets'],
    ['Technical compliance', 'Meets'],
    ['Clarification', 'Resolved — the address is present in the submitted evidence.'],
    ['Due diligence', 'No additional exercise undertaken; no separate exercise required by the published tender and no outstanding verification concern recorded by the committee.']
  ], Object.assign({ title: 'Summary' }, o || {}));
  E.sections = () => E.lk(['Tender and committee', 'Bid findings', 'Financial comparison', 'Clarifications and committee record', 'Recommendation and reasons'], { title: 'Report sections', sec: true });
  E.sigs = (g, p, r, o) => E.tb(['Member', 'Capacity', 'Signature'], [['Grace Wambui', 'Chair', g], ['Peter Mugo', 'Member', p], ['Ruth Achieng', 'Member', r]], Object.assign({ title: 'Signatures', sec: true }, o || {}));
  E.roster = (o) => E.tb(['Person', 'Department', 'Capacity'], [
    ['Grace Wambui', 'Human Resources Management and Development', 'Chair'],
    ['Peter Mugo', 'ICT', 'Member'], ['Ruth Achieng', 'Finance', 'Member'],
    ['Brian Wafula', 'Procurement', 'Secretary — not a voting or signing member']
  ], Object.assign({ title: 'Committee', sec: true }, o || {}));
  E.attend = (rows, o) => E.tb(['Person', 'Capacity', 'Attendance'], rows, Object.assign({ title: 'Attendance', sec: true }, o || {}));
  E.comp = (rows, o) => E.tb(['Bidder', 'Eligibility', 'Technical compliance', 'Submitted total', 'Evaluated total', 'Position', 'Action'], rows, Object.assign({ title: 'Bid comparison' }, o || {}));
  E.Q1 = 'Please identify the page and section of your submitted Kenya service-centre details that gives the Nairobi service address.';
  E.SCOPE = 'Explain the submitted evidence. Do not change your offer or add a new service arrangement.';
  E.REPLY = 'The service address is on page 2, section 3 of Kenya service-centre details: Westlands Business Park, Waiyaki Way, Nairobi.';

  // trackers: code chars d=done c=current b=blocked n=not started
  const TNAMES = ['Prepare', 'Review', 'Report'];
  E.T = (code, holder) => ({ code, holder });

  const CHIP = {
    'is-live': ['Meets', 'Responsive', 'Report sent', 'Resolved', 'No conflict', 'Received'],
    'is-critical': ['Does not meet', 'Not responsive', 'Cancelled', 'Excluded change', 'Returned', 'Conflict declared'],
    'is-attention': ['Needs review', 'Your signature needed', 'Received late', 'Reply overdue', 'Delivery problem'],
    'is-pending': ['Not applicable', 'Not ranked', 'Not joined', 'Awaiting signature', 'Not assessed — mandatory requirement not met', 'Not considered', 'Declaration pending']
  };
  const chipOf = (t) => {
    for (const k in CHIP) if (CHIP[k].indexOf(t) >= 0) return k;
    if (/^(Signed|Joined|Present) /.test(t)) return 'is-live';
    if (/^Left /.test(t)) return 'is-attention';
    return null;
  };
  const cell = (raw, num) => {
    const s = String(raw == null ? '' : raw);
    const td = num ? 'is-num' : '';
    if (s[0] === '@') return { t: s.slice(1), btn: true, td };
    if (s[0] === '#') return { t: s.slice(1), inp: true, td };
    if (s[0] === '*') return { t: s.slice(1), strong: true, td };
    if (s[0] === '!') { const [t, note] = s.slice(1).split('|'); return { t, txt: true, note: note || '', td }; }  // v0.7: read-only text with a note beneath it
    const c = chipOf(s);
    if (c) return { t: s, chip: true, cls: c, td };
    if (E.PEOPLE[s]) return { t: s, person: true, ini: E.PEOPLE[s], td };
    return { t: s, txt: true, td };
  };
  const btn = (s) => { s = String(s); const dis = s[0] === '~'; const t = dis ? s.slice(1) : s; const icon = btnIcon(t); return { t, dis, icon, hasIcon: !!icon }; };
  const initials = (n) => n.split(' ').map(x => x[0]).slice(0, 2).join('');
  let uid = 0;

  E.normBlock = (b, mobile) => {
    const o = Object.assign({}, b);
    o['is_' + b.k] = true;
    o.hasTitle = !!b.title; o.icon = b.title ? (b.icon || titleIcon(b.title)) : ''; o.hasIcon = !!o.icon; o.titleMain = !!b.title && !b.sec; o.titleSec = !!b.title && !!b.sec;
    o.name = 'r' + (uid++);
    if (b.k === 'p') { o.plain = !b.muted && !b.strong; o.isMuted = !!b.muted; o.isStrong = !!b.strong; }
    const vx = (v) => { const c = chipOf(String(v)); const pn = E.PEOPLE[v]; return { chip: !!c, cls: c || '', person: !c && !!pn, ini: pn || '', plain: !c && !pn }; };
    if (b.k === 'facts') o.items = b.items.map(([l, v]) => Object.assign({ l, v }, vx(v)));
    if (b.k === 'kv') { o.rows = b.rows.map(([l, v]) => Object.assign({ l, v }, vx(v))); o.cols = mobile ? 'minmax(0,1fr)' : '220px minmax(0,1fr)'; }
    if (b.k === 'table') {
      const numIdx = b.cols.map((c, i) => i).filter(i => b.rows.some(r => /^\*?KES /.test(String(r[i]))) || (b.num || []).indexOf(i) >= 0);
      o.ths = b.cols.map((t, i) => ({ t, td: numIdx.indexOf(i) >= 0 ? 'is-num' : '' }));
      o.trs = b.rows.map(r => ({ cells: r.map((c, i) => cell(c, numIdx.indexOf(i) >= 0)) }));
      o.hasCaption = !!b.caption;
    }
    if (b.k === 'notice') { o.cls = 'is-' + b.tone; o.iWarn = b.tone === 'warning'; o.iCrit = b.tone === 'critical'; o.iInfo = b.tone === 'info' || b.tone === 'live'; o.hasD = !!b.d; }
    if (b.k === 'field') {
      o.isArea = !!b.area; o.isSelect = !!b.select; o.isFile = !!b.file; o.isInput = !b.area && !b.select && !b.file;
      o.rows = b.rows || 3; o.value = b.value || ''; o.ph = b.ph || ''; o.hasHelp = !!b.help; o.hasErr = !!b.err; o.hasErrd = !!b.errd; o.req = !!b.req;
    }
    if (b.k === 'radios' || b.k === 'seg') o.options = b.opts.map((t, i) => ({ t, on: i === b.sel }));
    if (b.k === 'attn') { o.hasMeta = !!b.meta; const nm = Object.keys(E.PEOPLE).find(x => (b.meta || '').indexOf(x) >= 0); o.hasWho = !!nm; o.ini = nm ? E.PEOPLE[nm] : ''; }
    if (b.k === 'disc') { o.hasLinks = !!(b.links && b.links.length); o.linkList = b.links || []; o.lineList = o.lines.map(t => ({ t })); }
    if (b.k === 'links') o.linkList = b.links;
    if (b.k === 'evid') o.itemList = b.items.map(([t, bt]) => ({ t, b: bt || 'View evidence' }));
    if (b.k === 'filter') o.cellList = b.cells.map(([l, v, opt]) => ({ l, v: v || '', cls: opt && opt.wide ? 'is-wide' : '', sel: !!(opt && opt.select), inp: !(opt && opt.select), ph: (opt && opt.ph) || '' }));
    if (b.k === 'empty') { o.hasBtn = !!b.btn; o.hasSub = !!b.sub; o.eicon = I[b.eic] || I.layout; }
    return o;
  };

  E.norm = (b) => {
    const mobile = b.size === 'm';
    const W = mobile ? 390 : b.size === 'c' ? 1024 : 1440;
    const H = mobile ? 844 : b.size === 'c' ? 768 : 1024;
    const who = E.P[b.actor] || E.P.none;
    const nx = b.nx || null;
    const tr = b.tr ? b.tr.code.split('').map((c, i) => ({
      name: TNAMES[i], num: String(i + 1),
      cls: c === 'd' ? 'is-done' : c === 'c' ? 'is-current' : c === 'b' ? 'is-blocked' : '',
      st: c === 'd' ? '✓ Done' : c === 'c' ? ('Current · ' + (b.tr.holder || '')) : c === 'b' ? 'Blocked' : 'Not started'
    })) : [];
    const crumb = (b.crumb || []).map((t, i, a) => ({ t, last: i === a.length - 1, notLast: i < a.length - 1 }));
    const pri = b.pri ? btn(b.pri) : null;
    const sec = (b.sec || []).map(btn);
    const d = b.dlg ? Object.assign({}, b.dlg, {
      blocks: (b.dlg.blocks || []).map(x => E.normBlock(x, mobile)),
      pri: b.dlg.pri ? btn(b.dlg.pri) : { t: '', dis: true },
      sec: (b.dlg.sec || ['Cancel']).map(btn),
      hasCons: !!b.dlg.cons
    }) : null;
    return {
      id: b.id, name: b.name, g: b.g,
      icon: b.icon || (b.size === 'm' ? I.reply : GROUP_IC[b.g] || I.file),
      W, H, isMobile: mobile, isDesk: !mobile,
      pm: '0', pp: mobile ? '16px' : 'var(--space-6)',
      userName: who[0], userRole: who[1], userInit: initials(who[0]),
      org: b.org || 'Ministry of Health',
      crumb, hasCrumb: crumb.length > 0,
      back: b.back || '', hasBack: !!b.back,
      title: b.title || '', desc: b.desc || '', hasHead: !!b.title, hasDesc: !!b.desc,
      tabs: (b.tabs || []).map((t, i) => ({ t, on: i === (b.tab || 0) })), hasTabs: !!(b.tabs && b.tabs.length),
      tr, hasTr: tr.length > 0,
      nx: nx || {}, hasNx: !!nx,
      nxTurn: !!nx && nx.k === 'turn', nxWait: !!nx && nx.k === 'wait', nxDone: !!nx && nx.k === 'done',
      nxLabel: nx ? (nx.label || (nx.k === 'turn' ? 'Your turn' : nx.k === 'wait' ? 'Waiting on someone' : 'Done')) : '',
      hasNxS: !!(nx && nx.s),
      notInvolved: b.notInvolved || '', hasNotInvolved: !!b.notInvolved,
      hasGuide: tr.length > 0 || !!nx || !!b.notInvolved,
      blocks: (b.blocks || []).map(x => E.normBlock(x, mobile)),
      pri: pri || { t: '', dis: true }, hasPri: !!pri, sec, hasSec: sec.length > 0,
      onlySec: !pri && sec.length > 0,
      cons: b.cons || '', hasCons: !!b.cons,
      dlg: d || {}, hasDlg: !!d,
      meta: [who[0] + (who[1] ? ' (' + who[1] + ')' : ''), b.at, b.arch, b.state, W + ' × ' + H, b.spec].filter(Boolean).join(' · '),
      who: who[0] + (b.at ? ' · ' + b.at : ''),
      note: b.note || '', hasNote: !!b.note
    };
  };

  const q = Array.isArray(window.EVL_Q) ? window.EVL_Q : [];
  window.EVL_Q = { push: (fn) => fn(E) };
  q.forEach(fn => fn(E));
})();
