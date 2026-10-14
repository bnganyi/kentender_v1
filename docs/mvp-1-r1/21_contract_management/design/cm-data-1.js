(window.CMP = window.CMP || []).push({ o: 1, f: function (h) {
const { f, r, t, fl, x, xs, xh, lk, bt, pv, R, tx, dt, ta, file, ro, sel, rad, wide, turn, wait, done, blk, dlg, S, V, D } = h;
const G1 = '1 · Contracts list', G2 = '2 · Formation and signing';
const out = [];
const people = ['All people', 'Brian Wafula', 'Charles Mutiso', 'Julia Njeri', 'Peter Mugo', 'Grace Wanjiku', 'Amina Hassan', 'Josphat Mwangi', 'Beatrice Kamau'];
const statuses = ['All statuses', 'Preparing', 'Awaiting signatures', 'Active', 'Closed', 'Did not proceed', 'Terminated'];
const filters = (q) => [tx('Search contracts', q || ''), sel('Status', 'All statuses', statuses), sel('Source', 'All sources', ['All sources', 'KenTender award', 'External records', 'eGP']), sel('Responsible person', 'All people', people), sel('Managing unit', 'All units', ['All units', 'Digital Health (OU-MOH-DHI)'])];
const cols = ['Contract', 'Supplier', 'Status', 'Next action', 'Responsible person', ''];

// D01
const d01 = S({ id: 'D01', d: 'D01', g: G1, name: 'Contract list', vl: 'Base — My work', page: 'list', who: 'Charles Mutiso · HOP', at: '2 Jul 2027, 09:01 EAT', subj: 'Contract register',
  title: 'Contracts', headP: 'Register existing contract', views: ['My work', 'All contracts'], view: 0, filters: filters(), cols,
  rows: [['CM-MOH-2027-001', 'Afya Digital Supplies Limited', '!Preparing', 'Prepare contract', 'Charles Mutiso', '@Open contract']] });
out.push(d01,
  V(d01, { id: 'D01-E', vl: 'Empty register', rows: [], empty: 'No contracts are available.' }),
  V(d01, { id: 'D01-F', vl: 'No search results', filters: filters('unknown'), rows: [], empty: 'No contracts match your search.', emptyAct: 'Clear search' }),
  V(d01, { id: 'D01-T', vl: 'Technical reader — All contracts', who: 'Daniel Otieno · Technical operator (site-wide read)', at: '3 Aug 2027, 12:00 EAT', headP: '', view: 1,
    note: 'All contracts view; My work is empty for this reader. Normal authorised D01 facts are retained, as the v0.7 state card directs.' }),
  V(d01, { id: 'D01-AUD', vl: 'Auditor — All contracts', who: 'Naomi · Site-wide auditor', at: '3 Aug 2027, 12:00 EAT', headP: '', view: 1,
    note: 'All contracts view; My work is empty for this reader. Register existing contract is absent.' })
);

// D01-S
const d01s = S({ id: 'D01-S', d: 'D01-S', g: G1, name: 'My contracts (supplier)', vl: 'Base', page: 'list', who: 'Mary Wanjiku · Afya supplier signatory', at: '2 Jul 2027, 10:00 EAT', subj: 'Supplier contract list',
  title: 'My contracts', filters: [tx('Search contracts', '')], cols: ['Contract', 'Title', 'Status', 'Next action', ''],
  rows: [['CM-MOH-2027-001', 'IT equipment delivery', '!Awaiting signatures', 'Sign contract', '@Open contract']] });
out.push(d01s, V(d01s, { id: 'D01-S-E', vl: 'Empty', rows: [], empty: 'No contracts are available.' }));

// D02
const agreementFacts = r(['Supplier', 'Afya Digital Supplies Limited'], ['Items', '10 laptops at KES 100,000 each'], ['Contract value', 'KES 1,000,000, tax included'], ['Delivery due', '20 July 2027'], ['Warranty', '12 months from each unit’s acceptance'], ['Performance security', 'Not required under these test terms']);
const summary = R('Summary', f(['Contract value', 'KES 1,000,000'], ['Delivery', '20 July 2027'], ['Warranty', '12 months'], ['Security', 'Not required under these test terms']));
const d02 = S({ id: 'D02', d: 'D02', g: G2, name: 'Prepare agreement', vl: 'Base — Preparing', arch: 'Record detail', who: 'Brian Wafula · authorised preparer', at: '2 Jul 2027, 09:15 EAT', subj: 'Agreement draft 1',
  title: 'Prepare contract', st: 'Preparing', tab: 'Agreement', next: turn('Review the contract and send it for signature.', 'Brian Wafula'),
  regions: [summary, R('Agreement summary', agreementFacts, lk('View agreement 1'))],
  p: 'Send for signature', s2: ['View award'], ev: ['Award package 1', 'Issued terms 1'],
  note: 'View agreement 1 opens the source-based Form No. 4 preview (D02-V, §19.4). The summary remains the entry view.' });
const pkg = R('Incorporated documents', t(['Category', 'Document', 'Source'], [['Agreement', 'Form No. 4, Contract Agreement', 'Issued terms 1'], ['Tender form', 'Form of tender', 'Award package 1'], ['Price schedule', 'Price schedule', 'Award package 1'], ['Requirements schedule', 'Schedule of requirements', 'Issued terms 1'], ['Technical specifications', 'Technical specifications', 'Issued terms 1'], ['General conditions', 'General Conditions of Contract', 'Issued terms 1'], ['Special conditions', 'Special Conditions of Contract', 'Issued terms 1'], ['Award notification', 'Notification of award', 'Award package 1']]));
const parties = R('Parties and execution', t(['Party', 'Signatory', 'Capacity', 'Witness'], [['Procuring entity', 'Amina Hassan', 'Accounting Officer', 'Captured at signing'], ['Supplier', 'Mary Wanjiku', 'Authorised signatory', 'Captured at signing']]));
out.push(d02,
  V(d02, { id: 'D02-H', vl: 'Signing on hold', who: 'Charles Mutiso · HOP', next: blk('Contract signing is on hold.', 'Charles Mutiso', ['View issue', 'View award'], 'An award restriction requires review.'), p: '', s2: [] }),
  V(d02, { id: 'D02-S', vl: 'Signing unavailable', at: '2 Jul 2027, 09:20 EAT', next: wait('Technical operator Daniel Otieno is restoring signing; incident assigned 2 Jul 2027, 09:20 EAT.', 'Signing is unavailable. Your work has been saved.'), p: '', s2: ['View update status'],
    regions: [summary, pkg, parties], note: 'Back to contracts sits beside the heading; no new signature attempt. Package and party/capacity/witness particulars per §19.4; witness method pending LQ-05.' }),
  V(d02, { id: 'D02-V', vl: 'View agreement 1 — source-layout prototype', title: 'Agreement 1', subj: 'Agreement draft 1 · Form No. 4', back: 'Back to contract', next: null,
    regions: [R('Form No. 4 particulars', t(['Insertion', 'Bound value', 'Source'], [['Agreement date', '2 July 2027 — proposed execution date, confirm before sending', 'Prepared particulars'], ['Procuring entity', 'Ministry of Health', 'Award entity particulars'], ['Supplier', 'Afya Digital Supplies Limited', 'Accepted supplier identity'], ['Goods', '10 laptops', 'Issued requirements, awarded lot'], ['Amount', 'KES 1,000,000, tax included', 'Accepted price schedule'], ['Delivery, warranty, security', '20 July 2027; 12 months; not required under these test terms', 'Issued GCC/SCC'], ['Entity signatory', 'Amina Hassan, Accounting Officer', 'Authority record'], ['Supplier representative', 'Mary Wanjiku, authorised signatory', 'Supplier authority evidence'], ['Witnesses', 'One for each party, captured at signing', 'Signing session']])),
      pkg, R('Agreement text', xh('The covenant and precedence text is copied verbatim from the issued Form No. 4. Only its declared insertions are filled.'))],
    p: '', s2: ['Download agreement 1'], ev: ['Award package 1', 'Issued terms 1'],
    note: 'Clearly labelled source-layout prototype (§19.4): not an installed, signed or conformance-tested output. Form No. 4 body text is not drawn; no legal prose drafted. Entity address and supplier incorporation particulars are not supplied in the fixture.' })
);

// D03
const d03 = S({ id: 'D03', d: 'D03', g: G2, name: 'Supplier signature', vl: 'Base — Mary signs', arch: 'Review or decision', who: 'Mary Wanjiku · Afya authorised signatory', at: '2 Jul 2027, 10:00 EAT', subj: 'Frozen agreement 1',
  title: 'Sign contract', st: 'Awaiting signatures', tab: 'Agreement', back: 'Back to my contracts', next: turn('Review the agreement before signing.', 'Mary Wanjiku'),
  regions: [summary, R('Agreement summary', agreementFacts, lk('View agreement 1'))], p: 'Sign contract', s2: ['Report a problem'], ev: ['Agreement 1'] });
out.push(d03,
  V(d03, { id: 'D03-W', vl: 'Supplier signed — entity pending', at: '2 Jul 2027, 10:05 EAT', next: wait('Accounting Officer Amina Hassan must sign agreement 1; assigned 2 Jul 2027, 10:05 EAT.'), p: '', s2: ['View agreement'] }),
  V(d03, { id: 'D03-A', vl: 'Entity signatory view', who: 'Amina Hassan · Accounting Officer, entity signatory', at: '2 Jul 2027, before 10:30 EAT', back: 'Back to contracts',
    next: turn('Review agreement 1 and sign for the entity.', 'Amina Hassan'),
    regions: [summary, R('Agreement summary', agreementFacts, lk('View agreement 1')), R('Signatures', t(['Signatory', 'Capacity', 'Status'], [['Mary Wanjiku', 'Supplier authorised signatory', '!Signed'], ['Amina Hassan', 'Entity signatory', '!Awaiting signature']]))],
    p: 'Sign contract', s2: ['Report a problem'], note: 'Exact view instant not supplied; it falls between Mary’s 10:05 and Amina’s 10:30 signatures.' })
);

// D25
const secReq = R('Security requirement', f(['Contract sum', 'KES 1,000,000'], ['Required under test terms', 'KES 100,000'], ['Amount supplied', 'KES 100,000']));
const d25 = S({ id: 'D25', d: 'D25', g: G2, name: 'Verify security', vl: 'Base — confirmation received', arch: 'Review or decision', who: 'Charles Mutiso · HOP', at: '2 Jul 2027, 09:10 EAT', subj: 'Isolated pre-signing security branch',
  ref: 'CM-MOH-2027-SEC-VERIFY-001', title: 'Verify performance security', st: 'Preparing', tab: 'Agreement', next: turn('Check the issuer’s confirmation.', 'Charles Mutiso'),
  regions: [secReq, R('Instrument', r(['Issuer', 'Test Bank'], ['Beneficiary', 'Ministry of Health'], ['Reference', 'TEST-G-001'], ['Issued', '1 Jul 2027'], ['Expires', '31 Aug 2028'])),
    R('Issuer confirmation', r(['Source verification status', 'Confirmation received'], ['Confirmation', 'TEST-CONF-01'], ['Received', '2 Jul 2027']))],
  p: 'Verify security', s2: ['Reject security', 'View guarantee'], ev: ['Guarantee TEST-G-001', 'Issuer confirmation TEST-CONF-01'],
  note: 'Amount and expiry are synthetic issued terms, not a universal threshold or validity rule.' });
out.push(d25,
  D(d25, 'D25 · Verify', 'Verify dialog', dlg('Verify security', [r(['Instrument', 'TEST-G-001'], ['Issuer', 'Test Bank'], ['Amount', 'KES 100,000'], ['Confirmation', 'TEST-CONF-01'], ['Received', '2 Jul 2027'])], 'Verify')),
  D(d25, 'D25 · Reject', 'Reject dialog', dlg('Reject security', [fl(ta('Reason', ''))], 'Reject')),
  V(d25, { id: 'D25-R', vl: 'Record security', at: '2 Jul 2027, 09:05 EAT', title: 'Record performance security', next: turn('Record the performance security.', 'Charles Mutiso'),
    regions: [secReq, R('Instrument', fl(tx('Issuer', 'Test Bank'), tx('Beneficiary', 'Ministry of Health'), tx('Reference', 'TEST-G-001'), tx('Amount', 'KES 100,000'), dt('Issued', '1 Jul 2027'), dt('Expires', '31 Aug 2028'), file('Attachment', 'Guarantee TEST-G-001')))],
    p: 'Save security', s2: ['Cancel'], ev: ['Guarantee TEST-G-001'], note: 'The brief gives no headline for D25-R; "Record the performance security." is assumed.' }),
  V(d25, { id: 'D25-J', vl: 'Rejected — supplier view', who: 'David Ouma · Afya supplier representative', at: '2 Jul 2027, 09:15 EAT', back: 'Back to my contracts', title: 'Performance security',
    next: wait('Afya Digital Supplies Limited must supply a replacement security; requested 2 Jul 2027, 09:15 EAT.'),
    regions: [R('Rejected instrument', r(['Reference', 'TEST-G-001'], ['Reason', 'The issuer could not confirm this instrument.'], ['History', 'Rejected instrument retained']))],
    p: '', s2: ['View rejection', 'View contract'], ev: ['Guarantee TEST-G-001'], note: 'Title assumed; the brief gives none for the supplier view.' })
);

// D26
const sigBasis = R('Signing basis', r(['Whole-document version', 'Agreement 1'], ['Authority source', 'Afya assignment 1'], ['Reviewed method', 'Outside signing permitted in these test terms']));
const d26 = S({ id: 'D26', d: 'D26', g: G2, name: 'Record outside signature', vl: 'Base', arch: 'Form or editor', who: 'Charles Mutiso · HOP', at: '2 Jul 2027, 10:10 EAT', subj: 'Isolated permitted outside-signing branch',
  title: 'Record an outside signature', st: 'Awaiting signatures', tab: 'Agreement', next: turn('Record the supplier’s signed agreement.', 'Charles Mutiso'),
  regions: [R('Signature evidence', fl(sel('Party', 'Supplier', ['Supplier', 'Procuring entity']), tx('Signed by', 'Mary Wanjiku'), tx('Capacity', 'Authorised signatory'), dt('Signed on', '2 Jul 2027'), file('Signed copy', 'Signed agreement 1 — supplier'), ta('Notes', ''))), sigBasis],
  p: 'Save signature evidence', s2: ['View agreement 1'], ev: ['Agreement 1', 'Signed agreement 1 — supplier'],
  note: 'The brief gives no separate contract identity for this branch, so the base reference is shown.' });
out.push(d26,
  V(d26, { id: 'D26-H', vl: 'Copies do not match', next: blk('The signed copies do not match agreement 1.', 'Charles Mutiso', ['Record source evidence', 'View differences']), p: '', s2: [] }),
  V(d26, { id: 'D26-E', vl: 'Check signed agreement', at: '2 Jul 2027, 10:35 EAT', title: 'Check signed agreement', next: turn('Confirm the parties and signed version.', 'Charles Mutiso'),
    regions: [R('Signed copies', t(['Party', 'Signed by', 'Capacity', 'Signed on', 'Copy'], [['Supplier', 'Mary Wanjiku', 'Authorised signatory', '2 Jul 2027', '@Signed agreement 1 — supplier'], ['Procuring entity', 'Amina Hassan', 'Entity signatory', '2 Jul 2027', '@Signed agreement 1 — entity']])), sigBasis],
    p: 'Confirm signature evidence', s2: ['Report a problem'], ev: ['Agreement 1', 'Signed agreement 1 — supplier', 'Signed agreement 1 — entity'],
    note: 'Entity copy label and Amina’s capacity text are assumed. Each copy must bind the full agreement 1 manifest (§19.4).' })
);

// D23
const members = t(['Member', 'Role', 'Capacity'], [['Julia Njeri', 'Chair', 'User department'], ['Peter Mugo', 'Member', 'Technical'], ['Brian Wafula', 'Member', 'Procurement']]);
const d23 = S({ id: 'D23', d: 'D23', g: G2, name: 'Appoint inspectors', vl: 'Base — AO review', arch: 'Review or decision', who: 'Amina Hassan · Accounting Officer', at: '3 Jul 2027, 10:00 EAT', subj: 'Appointment proposal 1',
  title: 'Appoint inspectors', st: 'Active', tab: 'Agreement', next: turn('Review the proposed inspectors.', 'Amina Hassan'),
  regions: [R('Proposed members', members), R('Proposal', f(['Proposed period', '3 Jul 2027–31 Jul 2028'], ['Recommended by', 'Charles Mutiso, 3 Jul 2027, 09:00'], ['Recommendation reference', 'CM-APPT-01']))],
  p: 'Appoint inspectors', s2: ['Return for correction', 'View recommendation'], ev: ['Recommendation CM-01'] });
out.push(d23,
  D(d23, 'D23 · Appoint', 'Appointment dialog', dlg('Appoint inspectors', [fl(dt('From date', '3 Jul 2027'), dt('Until date', '31 Jul 2028')), r(['Julia Njeri', 'Chair · User department'], ['Peter Mugo', 'Member · Technical'], ['Brian Wafula', 'Member · Procurement'], ['Period', '3 Jul 2027–31 Jul 2028'])], 'Appoint')),
  D(d23, 'D23 · Return', 'Return dialog', dlg('Return for correction', [fl(ta('Reason', ''))], 'Return')),
  V(d23, { id: 'D23-R', vl: 'Recommend (HOP draft)', who: 'Charles Mutiso · HOP', at: '3 Jul 2027, 09:00 EAT', subj: 'Draft recommendation', title: 'Recommend inspectors', next: turn('Recommend the inspectors for appointment.', 'Charles Mutiso'),
    regions: [R('Proposed members', fl(sel('Chair', 'Julia Njeri'), sel('Chair capacity', 'User department'), sel('Member', 'Peter Mugo'), sel('Member capacity', 'Technical'), sel('Member', 'Brian Wafula'), sel('Member capacity', 'Procurement'), dt('From date', '3 Jul 2027'), dt('Until date', '31 Jul 2028')))],
    p: 'Recommend inspectors', s2: ['Cancel'], ev: [], note: 'Title and headline are assumed; the brief only specifies the editable fields and the primary action.' }),
  V(d23, { id: 'D23-P', vl: 'Declaration pending', who: 'Charles Mutiso · HOP', at: '3 Jul 2027, 10:05 EAT', subj: 'Appointment 1',
    next: wait('Peter Mugo must declare his interest; assigned 3 Jul 2027, 10:05 EAT.'),
    regions: [R('Declarations', t(['Member', 'Role', 'Declaration'], [['Julia Njeri', 'Chair', 'No conflict declared'], ['Peter Mugo', 'Member', 'Declaration pending'], ['Brian Wafula', 'Member', 'No conflict declared']])),
      R('Appointment', f(['Reference', 'AO/CM/2027/001'], ['Written record', 'Appointment CM-01'], ['Period', '3 Jul 2027–31 Jul 2028']))],
    p: '', s2: ['View appointment'], ev: ['Appointment CM-01', 'Recommendation CM-01'] })
);

// D24
const ctxR = R('Contract', f(['Contract', 'CM-MOH-2027-001'], ['Title', 'IT equipment delivery'], ['Supplier', 'Afya Digital Supplies Limited']));
const decl = ['I have no conflict of interest', 'I have a conflict of interest'];
const d24 = S({ id: 'D24', d: 'D24', g: G2, name: 'Declare interest', vl: 'Base — not yet declared', arch: 'Form or editor', who: 'Peter Mugo · appointed member', at: '3 Jul 2027, 10:10 EAT', subj: 'Appointment 1',
  title: 'Declare interest', st: 'Active', tab: 'Agreement', next: turn('Declare any conflict for this contract.', 'Peter Mugo'),
  regions: [ctxR, R('Declaration', fl(rad('Your declaration', decl, -1)))], p: 'Save declaration', s2: ['View appointment'], ev: ['Appointment CM-01', 'Personal declaration 1'] });
out.push(d24,
  V(d24, { id: 'D24-C', vl: 'Conflict selected', regions: [ctxR, R('Declaration', fl(rad('Your declaration', decl, 1), ta('Description', 'A close family member works for the supplier.')), xs('You will not be able to inspect or sign this contract while this conflict remains unresolved.'))] }),
  V(d24, { id: 'D24-S', vl: 'Saved — no conflict', at: '3 Jul 2027, 10:11 EAT', next: done('Peter Mugo recorded his declaration on 3 Jul 2027, 10:11 EAT.'),
    regions: [ctxR, R('Declaration', r(['Declaration', 'I have no conflict of interest'], ['Recorded', '3 Jul 2027, 10:11 EAT']))], p: '', s2: ['View appointment'] }),
  V(d24, { id: 'D24-X', vl: 'Conflict — replacement needed', who: 'Charles Mutiso · HOP', at: '3 Jul 2027, 10:12 EAT', subj: 'Isolated declared-conflict branch',
    next: blk('Peter Mugo must be replaced before the affected inspection can proceed.', 'Charles Mutiso', ['Revise appointment recommendation', 'View declaration']),
    regions: [ctxR, R('Declaration', r(['Member', 'Peter Mugo'], ['Declaration', 'I have a conflict of interest'], ['Description', 'A close family member works for the supplier.']))], p: '', s2: [] })
);
return out;
} });
