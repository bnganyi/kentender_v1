(window.CMP = window.CMP || []).push({ o: 3, f: function (h) {
const { f, r, t, fl, x, xs, xh, lk, bt, pv, R, tx, dt, ta, file, ro, sel, rad, wide, turn, wait, done, blk, dlg, S, V, D } = h;
const G5 = '5 · Obligations, reporting and warranty', G6 = '6 · Changes and adjustments';
const out = [];
const owCols = ['Task', 'State', 'Due', 'Responsible person', 'Action'];
const owRows = [['Payment confirmation', 'Waiting', '23 Jul 2027', 'Beatrice Kamau', '@Open'], ['Warranty for eight accepted units', 'Scheduled', '20 Jul 2028', 'Julia Njeri', '@Open']];
const lead10 = R('Replacement delivery', r(['Units', 'CM-DEMO-009/010'], ['Due', '27 Jul 2027'], ['State', 'Awaiting supplier']));

// D10
const d10 = S({ id: 'D10', d: 'D10', g: G5, name: 'Contract obligations', vl: 'Base', arch: 'Record detail', who: 'Julia Njeri · contract owner', at: '23 Jul 2027, 09:15 EAT', subj: 'Agreement 1',
  title: 'Remaining obligations', st: 'Active', tab: 'Obligations', next: turn('Follow up the replacement delivery.', 'Julia Njeri'),
  regions: [lead10, R('Other work', t(owCols, owRows))], p: 'Open replacement issue', s2: ['View agreement'], ev: ['Issue 1', 'Agreement 1'],
  note: 'One shared Other work table (§6.3, D40 reference). The leading task is excluded from it. The warranty is Active; Scheduled is the follow-up task state.' });
out.push(d10);

// D40 reader variants
const reg40 = R('Work register', t(owCols, [['Replacement follow-up', 'Awaiting supplier', '27 Jul 2027', 'Julia Njeri', '@Open']].concat(owRows)));
const pay40 = R('Payment follow-up', r(['Payment', 'KES 800,000 recorded'], ['Settlement', 'Not confirmed']));
const d40 = V(d10, { id: 'D40', d: 'D40', g: G5, dn: 'Other work & reader variants', vl: 'Base — identical to D10', note: 'D40 is the reference presentation of D10’s shared Other work region, not a second panel.' });
const reader = (id, vl, who, extra, note) => V(d10, { id, d: 'D40', g: G5, vl, who, next: null, regions: [reg40, pay40].concat(extra || []), p: '', s2: ['View agreement'], note });
out.push(d40,
  reader('D40-AO', 'Accounting Officer read', 'Amina Hassan · Accounting Officer', [], 'No personal task block. Protected account and bank detail absent.'),
  reader('D40-HOD', 'Head of User Department read', 'Julia Njeri · Head of User Department (Digital Health only)', [R('Source allocation', r(['Digital Health', 'Own source allocation detail only']))], 'Allocation amount not supplied; only the unit is shown.'),
  S({ id: 'D40-D', d: 'D40', g: G5, vl: 'Departmental Author — denied', page: 'state', icon: 'lock', who: 'Grace Wanjiku · Departmental Author only', at: '23 Jul 2027, 09:15 EAT', msg: 'You do not have access to this contract.', s2: ['Back to contracts'] }),
  reader('D40-F', 'Finance maker read', 'Josphat Mwangi · Finance maker', [], 'No preparation task for Josphat exists at this instant in the brief, so none is shown. No approver action.'),
  reader('D40-T', 'Technical reader', 'Daniel Otieno · Technical operator (site-wide read)'),
  reader('D40-AUD', 'Auditor', 'Naomi · Site-wide auditor'),
  V(d10, { id: 'D40-S', d: 'D40', g: G5, vl: 'Supplier representative', who: 'David Ouma · Afya supplier representative', back: 'Back to my contracts', next: null,
    regions: [R('Other work', t(owCols, [['Replacement remedy', 'Open', '27 Jul 2027', 'David Ouma', '@View issue']]))], p: '', s2: [], ev: ['Issue 1'], note: 'Supplier sees only their own remedy; never internal Finance tasks.' })
);

// D15
const d15 = S({ id: 'D15', d: 'D15', g: G5, name: 'Contract reporting', vl: 'Base — July report', arch: 'Record detail', who: 'Charles Mutiso · HOP', at: '1 Aug 2027, 09:00 EAT', subj: 'July progress report draft 1',
  title: 'Monthly contract progress', st: 'Active', tab: 'Obligations', next: turn('Review and submit the July report.', 'Charles Mutiso'),
  regions: [R('Coverage', r(['Report month', 'July 2027'], ['Contracts covered', '1 in Contract Management'], ['Contracts outside Contract Management', 'Not included — reconcile before claiming full coverage'])), R('Report', t(['Contract', 'Title', 'Contract value', 'Commenced', 'Status', 'Cash confirmed', 'Expected completion'], [['CM-MOH-2027-001', 'IT equipment delivery', 'KES 1,000,000', '2 July 2027', 'Active', 'KES 800,000', '27 July 2028']], [2, 5]),
    x('10 laptops accepted; 2 were replacement units. Unpaid KES 200,000; no noncash adjustment. No open delivery issue.')), R('Submission', r(['Author', 'Charles Mutiso, HOP'], ['Recipient', 'Amina Hassan, Accounting Officer'], ['AO receipt', 'Recorded after submission']))],
  p: 'Submit report', s2: ['View contract'], ev: ['Agreement 1', 'Finance reconciliation 2'], note: 'The single report row is a management output, not the operational record layout.' });
const d15l = S({ id: 'D15-L', d: 'D15', g: G5, vl: 'Publication requirement — blocked', arch: 'Record detail', who: 'Charles Mutiso · HOP', at: '2 Jul 2027, 11:00 EAT', subj: 'Publication obligation',
  title: 'Publication requirement needs review', st: 'Needs review', tab: 'Obligations', next: blk('The applicable publication deadline needs confirmation.', 'Charles Mutiso', ['Record source evidence', 'View source event', 'View signing record']),
  regions: [R('Obligation', r(['Trigger', 'Award decision recorded 17 Jun 2027, 10:00 EAT'], ['Separate fact', 'Contract signed 2 Jul 2027, 10:30 EAT'], ['Destinations', 'Notice boards; website if available; report to PPRA'], ['Deadline', 'Not confirmed — set by current directions'], ['Responsible review', 'Procurement/reporting owner']))],
  ev: ['Award decision event', 'Signing record'], note: 'CM-R-13: §138 leaves period and manner to directions, so no fourteen-day countdown. Pending LQ-06; evidence recorded here is a proposal, not a rule.' });
out.push(d15, d15l, D(d15l, 'D15-L · Evidence', 'Record source evidence dialog', dlg('Record source evidence', [fl(tx('Source reference', ''), dt('Dated', ''), file('Copy', ''), ta('Notes', ''))], 'Save evidence')));

// D16
const d16 = S({ id: 'D16', d: 'D16', g: G5, name: 'Security follow-up', vl: 'Base — record return', arch: 'Record detail', who: 'Charles Mutiso · HOP', at: '1 Aug 2027, 09:30 EAT', subj: 'Agreement 1',
  ref: 'CM-MOH-2027-SEC-RETURN-001', title: 'Performance security', st: 'Active', tab: 'Obligations', next: turn('Record the security return.', 'Charles Mutiso'),
  regions: [R('Instrument', r(['Instrument', 'TEST-G-RETURN-001'], ['Guaranteed amount', 'KES 100,000'], ['AO final acceptance', '27 July 2027'], ['Return due', '26 August 2027 — 30 days from AO final acceptance'], ['Status', 'Return due'])),
    R('Return', fl(dt('Return date', '1 August 2027'), file('Evidence', 'Bank discharge TEST-G-RETURN-001')))],
  p: 'Record return', s2: ['View guarantee'], ev: ['Guarantee TEST-G-RETURN-001', 'Source clause TEST-SEC-RETURN-01'], note: 'CM-R-09: the 30-day clock starts at the AO final-acceptance record, not committee acceptance, payment or warranty expiry. Dates are synthetic.' });
const claim16 = (ended) => R('Claim', r(['Unit', 'CM-WAR-OPEN-004'], ['Accepted', '20 Jul 2027'], ['Source terms', 'WAR-OPEN-TERMS-01'], ['Fault', 'Battery does not charge'], ['Warranty', ended ? 'Expired 20 July 2028; timely claim remains open' : 'Ends 20 July 2028'], ['Evidence', 'Diagnostic 1']));
const d16w = S({ id: 'D16-W', d: 'D16', g: G5, vl: 'Warranty claim — send notice', arch: 'Record detail', who: 'Julia Njeri · contract owner', at: '10 Jul 2028, 09:00 EAT', subj: 'Agreement 1 · warranty claim 1',
  ref: 'CM-MOH-2027-WAR-OPEN-001', title: 'Warranty claim', st: 'Active', tab: 'Obligations', next: turn('Send the defect notice.', 'Julia Njeri'),
  regions: [claim16(false), R('Defect notice', fl(ta('Notice', 'Battery does not charge')))], p: 'Send notice', s2: ['View warranty'], ev: ['Diagnostic 1'] });
out.push(d16, d16w,
  V(d16w, { id: 'D16-P', vl: 'Remedy pending after expiry', at: '21 Jul 2028, 09:00 EAT', next: wait('Supplier representative David Ouma must respond to the warranty remedy; requested 10 Jul 2028, 09:10 EAT.'),
    regions: [claim16(true), R('Notice', r(['Defect notice', 'Sent 10 Jul 2028']))], p: '', s2: ['View notice', 'View claim history'], ev: ['Diagnostic 1', 'Defect notice 1'] }));

// D35
const claim35 = R('Claim', r(['Unit', 'CM-WAR-004'], ['Warranty ends', '20 Jul 2028'], ['Fault', 'Battery does not charge'], ['Notice sent', '10 Jul 2028, 09:00'], ['Remedy', 'Like-for-like replacement under issued terms']));
const d35 = S({ id: 'D35', d: 'D35', g: G5, name: 'Paid-unit warranty replacement', vl: 'Base — arrange return', arch: 'Record detail', who: 'Julia Njeri · contract owner', at: '10 Jul 2028, 09:00 EAT', subj: 'All ten units accepted, invoiced and paid',
  ref: 'CM-MOH-2027-WAR-001', title: 'Follow up warranty replacement', st: 'Active', tab: 'Obligations', next: turn('Arrange return of the faulty laptop.', 'Julia Njeri'),
  regions: [claim35, R('Progress', f(['Returned', 'No'], ['Replacement', 'Not received'], ['Finance correction', 'Pending — Josphat Mwangi']))], p: 'Record return', s2: [], ev: ['Defect notice 1'] });
const rem35 = (rec) => R('Remedy', r(['Returned unit', 'CM-WAR-004'], ['Replacement', 'CM-WAR-011'], ['Return/credit and replacement receipt', rec], ['Acquisition entitlement', '10 units / KES 1,000,000, unchanged'], ['Additional cash or payable', 'KES 0']));
const find35 = R('Findings', t(['Check', 'Observed', 'Result'], [['RAM', '16 GB', '!Meets'], ['Storage', '512 GB', '!Meets'], ['Starts', 'Yes', '!Meets']]), r(['Evidence', 'Test WAR log 1'], ['Verification source', 'Current technical certificate and fully signed replacement report']));
const d35v = V(d35, { id: 'D35-V', vl: 'Verify remedy', who: 'Peter Mugo · current technical capacity', at: '15 Jul 2028, 10:00 EAT', title: 'Verify warranty remedy', next: turn('Confirm the remedy evidence.', 'Peter Mugo'),
  regions: [rem35('Reconciled'), find35], p: 'Verify remedy', s2: ['Request correction'], ev: ['Test WAR log 1', 'Replacement report'] });
out.push(d35,
  D(d35, 'D35 · Return', 'Record return dialog', dlg('Record return', [fl(ro('Unit', 'CM-WAR-004'), dt('Actual collection date', '12 Jul 2028'), file('Evidence', 'Test collection WAR-01'))], 'Record return'), { note: 'Records collection evidence and requests the authorised acceptance/native correction; not a custody-only removal.' }),
  d35v,
  V(d35, { id: 'D35-C', vl: 'Claim closed', at: '15 Jul 2028, 11:00 EAT', next: done('The remedy was verified and the claim closed on 15 Jul 2028.'),
    regions: [R('Outcome', r(['Original cash', 'KES 1,000,000'], ['Additional invoice entitlement', 'None'], ['Original unit', 'CM-WAR-004'], ['Replacement', 'CM-WAR-011']))], p: '', s2: ['View remedy', 'View history'], note: 'Done headline wording assumed; the brief states "remedy verified, claim closed".' }),
  V(d35v, { id: 'D35-H', vl: 'Reconciliation incomplete', regions: [rem35('Incomplete'), find35], next: blk('Finance must reconcile the replacement.', 'Josphat Mwangi', ['View affected records', 'View claim']), p: '', s2: [] })
);

// ── Changes ──
const EXT = 'CM-MOH-2027-EXTENSION-001';
const extCmp = (h3) => t(['Term', 'Current', h3], [['Delivery date', '20 July 2027', '27 July 2027'], ['Contract value', 'KES 1,000,000', 'KES 1,000,000'], ['Quantity', '10', '10']], [1, 2]);
const d27 = S({ id: 'D27', d: 'D27', g: G6, name: 'Request delivery extension', vl: 'Base — request', arch: 'Form or editor', who: 'Julia Njeri · contract coordination', at: '18 Jul 2027, 10:00 EAT', subj: 'Agreement 1 · change 1 draft 1',
  ref: EXT, title: 'Request delivery extension', st: 'Active', tab: 'Obligations', next: turn('Explain the requested delivery date.', 'Julia Njeri'),
  regions: [R('Request', fl(ro('Current delivery', '20 Jul 2027'), dt('Proposed date', '27 Jul 2027'), ta('Reason', 'Supplier reports a seven-day shipment delay.'), file('Supplier request', 'Supplier request 1'), ro('Amount and quantity', 'KES 1,000,000; 10 laptops; no price change')))],
  p: 'Request extension', s2: ['Cancel'], ev: ['Agreement 1'] });
out.push(d27,
  V(d27, { id: 'D27-R', vl: 'HOP — submit for decision', who: 'Charles Mutiso · HOP', at: '18 Jul 2027, 11:00 EAT', title: 'Review delivery extension request', next: turn('Submit the supported request for decision.', 'Charles Mutiso'),
    regions: [R('Request', extCmp('Proposed'), r(['Reason', 'Supplier reports a seven-day shipment delay.'])),
      R('Appointed reviewers', t(['Reviewer', 'Declaration', 'Recommendation signed'], [['Grace Wambui', 'No conflict', '18 Jul 2027, 10:40'], ['Peter Mugo', 'No conflict', '18 Jul 2027, 10:45'], ['Ruth Achieng', 'No conflict', '18 Jul 2027, 10:50']]),
        r(['Recommendation', 'Approve date extension without price change'], ['Appointment', 'AO/VAR/2027/001']))],
    p: 'Submit change for decision', s2: ['Return for correction'], ev: ['Technical review 1', 'Recommendation 1', 'Legal review 1'], note: 'Title assumed. Reviewers are expressly appointed, not reused Evaluation appointments.' }),
  V(d27, { id: 'D27-A', vl: 'Supplier signs amendment', who: 'Mary Wanjiku · Afya supplier signatory', at: '19 Jul 2027, 11:00 EAT', subj: 'Amendment 1', back: 'Back to my contracts', title: 'Sign amendment',
    next: turn('Review and sign amendment 1.', 'Mary Wanjiku'), regions: [R('Amendment 1', extCmp('Amended'), lk('View amendment 1'), xh('The amendment takes effect only after both required signatures. Amina Hassan signs the same version next.'))],
    p: 'Sign amendment', s2: ['Report a problem'], ev: ['Amendment 1', 'Decision 1'], note: 'Title assumed.' }),
  V(d27, { id: 'D27 · Blocked', vl: 'Review authority missing', who: 'Charles Mutiso · HOP', at: '18 Jul 2027, 11:00 EAT', next: blk('Review authority needs confirmation', 'Charles Mutiso', ['View appointment']),
    regions: [R('Request', extCmp('Proposed'))], p: '', s2: [] })
);
const d14 = S({ id: 'D14', d: 'D14', g: G6, name: 'Extension review', vl: 'Base — AO decision', arch: 'Review or decision', who: 'Amina Hassan · Accounting Officer', at: '19 Jul 2027, 10:00 EAT', subj: 'Agreement 1 · change 1 draft 1',
  ref: EXT, title: 'Review delivery extension', st: 'Active', tab: 'Obligations', next: turn('Decide the requested delivery date.', 'Amina Hassan'),
  regions: [R('Requested change', extCmp('Requested'), r(['Reason', 'Supplier requests seven additional days because the shipment was delayed.'], ['Recommendation', 'Approve the revised date; no price change.'])),
    R('Supporting evidence', lk('Supplier request 1', 'Technical review 1', 'Current committee recommendation 1', 'Legal review 1'))],
  p: 'Approve extension', s2: ['Decline', 'Return for correction'], ev: ['Supplier request 1', 'Technical review 1', 'Current committee recommendation 1', 'Legal review 1'] });
out.push(d14,
  D(d14, 'D14 · Approve', 'Decision dialog', dlg('Approve extension', [fl(ta('Reason', 'The documented grounds support the revised date without changing price or quantity.'))], 'Confirm decision')),
  D(d14, 'D14 · Decline', 'Decline dialog (required reason)', dlg('Decline extension', [fl(ta('Reason', ''))], 'Confirm decision')),
  V(d14, { id: 'D14-P', vl: 'Approved — amendment pending', at: '19 Jul 2027, 10:15 EAT', next: wait('Supplier signatory Mary Wanjiku must sign amendment 1; assigned 19 Jul 2027, 10:15 EAT.'),
    regions: [R('Decision', r(['Decision', 'Approved 19 Jul 2027, 10:15 EAT'], ['Operative delivery date', '20 July 2027 — amendment not yet effective']))], p: '', s2: ['View amendment', 'View decision'] })
);

// D34
const QTY = 'CM-MOH-2027-QTY-001';
const qCmp = (q, tot, pct) => t(['', 'Current', 'Proposed'], [['Quantity', '10', q], ['Total', 'KES 1,000,000', tot], ['Cumulative change', '—', pct]], [1, 2]);
const d34 = S({ id: 'D34', d: 'D34', g: G6, name: 'Quantity variation', vl: 'Base — request', arch: 'Form or editor', who: 'Julia Njeri · contract coordination', at: '18 Jul 2027, 09:00 EAT', subj: 'Agreement 1',
  ref: QTY, title: 'Request quantity change', st: 'Active', tab: 'Obligations', next: turn('Explain the additional quantity.', 'Julia Njeri'),
  regions: [R('Quantity', t(['Item', 'Original', 'Rate', 'Proposed'], [['Laptop', '10', 'KES 100,000', '#11']], [1, 2, 3]), f(['Proposed total', 'KES 1,100,000'], ['Cumulative quantity change', '10%'], ['Cumulative value change', '10%'])),
    R('Request', fl(ta('Reason', 'One additional user needs the same specified laptop'), file('Source request', 'Test quantity request 1')))],
  p: 'Request change', s2: ['Cancel'], ev: ['Agreement 1', 'Test quantity request 1'], note: 'Synthetic ceilings: 15% goods quantity, 25% cumulative value. Rate and percentages are not editable.' });
const rev34 = R('Review', r(['Technical recommendation', 'Test QTY review 1'], ['Legal/source evidence', 'Test QTY basis 1'], ['Funding', 'Digital Health KES 100,000 additional'], ['Funding confirmation', 'QTY-01']));
const d34a = V(d34, { id: 'D34-A', vl: 'AO decision', who: 'Amina Hassan · Accounting Officer', at: '18 Jul 2027, 11:00 EAT', title: 'Review quantity change', next: turn('Decide the quantity change.', 'Amina Hassan'),
  regions: [R('Comparison', qCmp('11', 'KES 1,100,000', '10%'), xh('Synthetic mechanism test — not a legally cleared production example.')), rev34], p: 'Approve change', s2: ['Decline', 'Return for correction'], note: 'Title and headline assumed.' });
out.push(d34,
  V(d34, { id: 'D34-R', vl: 'HOP — submit for decision', who: 'Charles Mutiso · HOP', at: '18 Jul 2027, 10:00 EAT', next: turn('Submit the change for decision.', 'Charles Mutiso'),
    regions: [R('Comparison', qCmp('11', 'KES 1,100,000', '10%'), xh('Synthetic mechanism test — not a legally cleared production example.')), rev34], p: 'Submit change for decision', s2: ['Return for correction'], note: 'Headline assumed.' }),
  d34a,
  D(d34a, 'D34-A · Decide', 'Decision dialog', dlg('Approve change', [fl(ta('Reason', 'Additional quantity is supported at the unchanged issued rate'))], 'Confirm decision')),
  V(d34, { id: 'D34-P', vl: 'Supplier signs amendment', who: 'Mary Wanjiku · Afya supplier signatory', at: '19 Jul 2027, 09:00 EAT', subj: 'Amendment 1', back: 'Back to my contracts', title: 'Sign amendment',
    next: turn('Review and sign amendment 1.', 'Mary Wanjiku'), regions: [R('Amendment 1', qCmp('11', 'KES 1,100,000', '10%'), xh('Synthetic mechanism test — not a legally cleared production example.'))], p: 'Sign amendment', s2: ['Report a problem'], note: 'Title and headline assumed; Amina signs the same version next.' }),
  V(d34, { id: 'D34-H', vl: 'Effective — order update failed', at: '19 Jul 2027, 10:00 EAT', title: 'Contract change recorded', next: wait('Technical operator Daniel Otieno is restoring the order update; assigned 19 Jul 2027, 10:00 EAT.'),
    regions: [R('Change', r(['Operative quantity', '11'], ['Budget adjustment', 'Acknowledged'], ['Order update', 'Pending'], ['New spending', 'Held for the changed quantity']), xh('Synthetic mechanism test — not a legally cleared production example.'))], p: '', s2: ['View update status', 'View amendment'] }),
  V(d34, { id: 'D34-L', vl: 'Change requires legal review', who: 'Charles Mutiso · HOP', at: '18 Jul 2027, 10:00 EAT',
    next: blk('Change requires legal review', 'Charles Mutiso', ['View rule', 'View request', 'Return for correction'], 'The proposed increase is within twelve months of signing. Its legal basis has not been established.'),
    regions: [R('Comparison', qCmp('11', 'KES 1,100,000', '10%')), rev34], p: '', s2: [],
    note: '§19.6 / CM-R-11: early upward-total change held pending LQ-02. Approval and signing are held; no Approve anyway and no new page.' }),
  V(d34, { id: 'D34-X', vl: 'Exceeds limit — blocked', regions: [R('Comparison', qCmp('12', 'KES 1,200,000', '20%'), r(['Applicable limit', '15% goods quantity (synthetic test rule)']))],
    next: blk('Proposed quantity exceeds the applicable limit', 'Julia Njeri', ['View rule', 'View issue']), p: '', s2: [] })
);

// D36
const DLY = 'CM-MOH-2027-DELAY-001';
const calc36 = (due, late, days, amt, extra) => R('Calculation', r(...[['Due date', due], ['Delivered', '25 Jul 2027'], ['Days late', late], ['Eligible principal', 'KES 1,000,000'], ['Rate', '0.1% per day (synthetic test rate)'], ['Cap', '10% (KES 100,000)']].concat(extra || [])), f(['Calculation', 'KES 1,000 per day × ' + days], ['Proposed adjustment', amt]));
const cause36 = R('Causation and response', r(['Causation', 'Supplier shipment delay'], ['Supplier challenge', 'Requests exclusion of two days']));
const d36 = S({ id: 'D36', d: 'D36', g: G6, name: 'Contractual delay adjustment', vl: 'Base — HOP review', arch: 'Review or decision', who: 'Charles Mutiso · HOP', at: '29 Jul 2027, 09:00 EAT', subj: 'All 10 accepted 25 Jul 2027',
  ref: DLY, title: 'Review delivery delay', st: 'Active', tab: 'Obligations', next: turn('Review the proposed adjustment.', 'Charles Mutiso'),
  regions: [calc36('20 Jul 2027', '5 calendar days (21–25 Jul inclusive)', '5', 'KES 5,000', [['Effective extension', 'None']]), cause36],
  p: 'Submit adjustment for decision', s2: ['Return for correction', 'View clause'], ev: ['Delivery 25 Jul 2027', 'Clause TEST-DELAY-01', 'Supplier response 1'], note: 'Isolated mechanism test: the daily rate is synthetic, not a verified §140 rate, until LQ-04 is resolved.' });
const d36a = V(d36, { id: 'D36-A', vl: 'AO decision', who: 'Amina Hassan · decision authority (synthetic)', at: '30 Jul 2027, 09:00 EAT', next: turn('Decide the proposed adjustment.', 'Amina Hassan'),
  regions: [calc36('20 Jul 2027', '5 calendar days (21–25 Jul inclusive)', '5', 'KES 5,000'), cause36, R('Recommendation', r(['Technical/legal recommendation', 'No supported exclusion']))], p: 'Approve adjustment', s2: ['Decline', 'Return for correction'], note: 'Headline assumed.' });
out.push(d36, d36a,
  D(d36a, 'D36-A · Decide', 'Decision dialog', dlg('Approve adjustment', [fl(ta('Reason', 'Supplier-responsible five-day delay established'))], 'Confirm decision')),
  V(d36, { id: 'D36-S', vl: 'Certification with adjustment', at: 'Not stated', title: 'Review invoice', next: turn('Review and sign the certification.', 'Charles Mutiso'), tab: 'Invoices',
    regions: [R('Certification', t(['Supported gross', 'Authorised adjustment', 'Proposed cash'], [['KES 1,000,000', 'KES 5,000', 'KES 995,000']], [0, 1, 2]), xh('Finance applies the adjustment through the reviewed native mapping; the invoice rate is not edited. The KES 5,000 is a noncash adjustment, never cash.'))],
    p: 'Sign certification', s2: ['View calculation'], note: 'Instant, title and headline not supplied; assumed.' }),
  V(d36, { id: 'D36-H', vl: 'Deduction mapping unverified', next: blk('This action is on hold.', 'Josphat Mwangi', ['View calculation', 'View issue'], 'The native deduction mapping is not verified; payment is held.'), p: '', s2: [] }),
  V(d36, { id: 'D36-E', vl: 'Effective-extension branch', regions: [calc36('22 Jul 2027 (effective extension)', '3 calendar days (23–25 Jul inclusive)', '3', 'KES 3,000', [['Previous computation', 'KES 5,000 — retained']]), cause36],
    note: 'Separate branch: an unsigned extension request cannot select this variant.' })
);
return out;
} });
