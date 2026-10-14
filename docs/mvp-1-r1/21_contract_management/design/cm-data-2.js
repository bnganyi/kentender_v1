(window.CMP = window.CMP || []).push({ o: 2, f: function (h) {
const { f, r, t, fl, x, xs, xh, lk, bt, pv, R, tx, dt, ta, file, ro, sel, rad, wide, turn, wait, done, blk, dlg, S, V, D } = h;
const G3 = '3 · Delivery and acceptance', G4 = '4 · Invoices and Finance';
const out = [];
const units = Array.from({ length: 10 }, (_, i) => 'CM-DEMO-0' + String(i + 1).padStart(2, '0'));

// D04
const d04 = S({ id: 'D04', d: 'D04', g: G3, name: 'Receive goods', vl: 'Base', arch: 'Form or editor', who: 'Grace Wanjiku · authorised receiver', at: '20 Jul 2027, 09:00 EAT', subj: 'Arrival draft 1',
  title: 'Record delivery', st: 'Active', tab: 'Deliveries', next: turn('Record the goods that arrived.', 'Grace Wanjiku'),
  regions: [R('Delivery', f(['Delivery due', '20 July 2027'], ['Destination', 'ICT receiving area'])),
    R('Arrival details', fl(tx('Supplier delivery reference', 'AFYA-DN-01'), dt('Received at', '20 Jul 2027, 09:00 EAT'), sel('Destination', 'ICT receiving area'))),
    R('Items', t(['Item', 'Expected', 'Arrived', 'Unit references'], [['Laptop', '10', '#10', 'CM-DEMO-001–CM-DEMO-010']], [1, 2]), bt('Enter unit references'), xh('Recording delivery does not accept the goods.'))],
  p: 'Record delivery', s2: ['Cancel'], ev: ['Delivery schedule 1'] });
out.push(d04, D(d04, 'D04 · Units', 'Unit references dialog', dlg('Unit references', [fl({ t: 'ta', l: 'Unit references', v: units.join('\n'), o: { rows: 11 } })], 'Use references')));

// D05
const findings5 = t(['Check', 'Required', 'Observed', 'Result'], [['RAM', 'At least 16 GB', '16 GB on all 10', '!Meets'], ['Storage', 'At least 512 GB', '512 GB on all 10', '!Meets'], ['Starts successfully', 'Yes', '8 Yes; 2 not recorded', '!Needs review']]);
const d05 = S({ id: 'D05', d: 'D05', g: G3, name: 'Inspect delivery', vl: 'Base — Your turn', arch: 'Review or decision', who: 'Peter Mugo · appointed inspector', at: '20 Jul 2027, 11:00 EAT', subj: 'Arrival 1 · observations 1',
  title: 'Inspect delivery', st: 'Active', tab: 'Deliveries', next: turn('Complete the missing observations.', 'Peter Mugo'),
  regions: [R('Coverage', f(['Coverage', '10 laptops; each unit inspected'])), R('Findings', findings5)],
  p: 'Record observations', s2: ['View all observations'], ev: ['Arrival 1', 'Contract requirements 1'] });
const obsRows = units.map((u, i) => [u, '16', '512', i < 8 ? 'Yes' : 'Not recorded', 'Test log 20-Jul-' + (i < 8 ? '01' : String(i + 1).padStart(2, '0'))]);
out.push(d05,
  D(d05, 'D05 · Record', 'Record observations dialog', dlg('Record observations', [t(['Unit', 'Starts', 'Evidence'], [['CM-DEMO-009', '^Not recorded|Not recorded,Yes,No', '~Test log 20-Jul-09'], ['CM-DEMO-010', '^Not recorded|Not recorded,Yes,No', '~Test log 20-Jul-10']])], 'Save observations')),
  D(d05, 'D05 · All', 'All observations detail', dlg('All observations', [t(['Unit', 'RAM (GB)', 'Storage (GB)', 'Starts', 'Evidence'], obsRows, [1, 2])], '', ['Close']), { note: 'The brief specifies no actions for the ten-unit detail; Close is assumed.' }),
  V(d05, { id: 'D05-M', vl: 'Evidence unreadable — blocked', next: blk('The inspection evidence needs review.', 'Peter Mugo', ['Record observations', 'View all observations']), p: '', s2: [] })
);

// D19
out.push(S({ id: 'D19', d: 'D19', g: G3, name: 'Technical certificate', vl: 'Base', arch: 'Review or decision', who: 'Peter Mugo · appointed technical member/certifier', at: '20 Jul 2027, 13:30 EAT', subj: 'Certificate 1 draft 1',
  title: 'Confirm technical inspection', st: 'Active', tab: 'Deliveries', next: turn('Review and sign the technical certificate.', 'Peter Mugo'),
  regions: [R('Technical certificate 1', r(['Contract', 'CM-MOH-2027-001'], ['Inspected', '10'], ['Conforms', '8'], ['Fails', '2'], ['Missing evidence', '0'], ['Tests', 'RAM ≥16 GB, storage ≥512 GB, successful start'], ['Conforming units', 'CM-DEMO-001–CM-DEMO-008'], ['Failed units', 'CM-DEMO-009 and CM-DEMO-010 failed start'], ['Recipient', 'Amina Hassan, Accounting Officer']), x('I confirm the quality and quantity of the goods or services identified in the attached coverage schedule against the cited contract requirements, subject to the recorded exceptions.'))],
  p: 'Sign technical certificate', s2: ['Request correction'], ev: ['Inspection 1'] }));

// D06 / D07
const sum6 = R('Findings', f(['Delivered', '10'], ['Meets', '8'], ['Does not meet', '2'], ['Needs review', '0']));
const fail6 = R('Units that do not meet', t(['Unit', 'Check', 'Required', 'Observed', 'Result'], [['CM-DEMO-009', 'Starts successfully', 'Yes', 'No', '!Does not meet'], ['CM-DEMO-010', 'Starts successfully', 'Yes', 'No', '!Does not meet']]));
const reason = 'Two laptops did not start during inspection. Replacement is required.';
const disp6 = R('Quantity disposition', f(['Accepted', '8'], ['Rejected', '2'], ['Deferred', '0']), r(['Reason', reason]));
const prev6 = R('', pv('Report preview', [['Statement', 'We record the inspection findings and the accept/reject disposition for the goods or services identified in the coverage schedule, with the stated exceptions and evidence.'], ['Findings', '8 meet; 2 do not meet; 0 need review'], ['Accepted', '8'], ['Rejected', '2'], ['Deferred', '0'], ['Reason', reason], ['Signers', 'Julia Njeri, Peter Mugo, Brian Wafula']]));
const tech6 = R('Technical evidence', x('Technical certificate 1 — signed by Peter Mugo, 20 Jul 2027, 13:35 EAT'));
const d06 = S({ id: 'D06', d: 'D06', g: G3, name: 'Acceptance review', vl: 'Base', arch: 'Review or decision', who: 'Julia Njeri · appointed chair', at: '20 Jul 2027, 14:00 EAT', subj: 'Report draft 1',
  title: 'Review inspection', st: 'Active', tab: 'Deliveries', next: turn('Prepare the acceptance report.', 'Julia Njeri'),
  regions: [sum6, fail6, disp6, prev6, tech6], p: 'Prepare report for signing', s2: ['View observations'], ev: ['Inspection 1'] });
out.push(d06);
const sigs = (b) => R('Signatures', t(['Signer', 'Role', 'Status', 'Signed'], [['Julia Njeri', 'Chair', '!Signed', '20 Jul 2027, 14:10 EAT'], ['Peter Mugo', 'Technical member', '!Signed', '20 Jul 2027, 14:15 EAT'], ['Brian Wafula', 'Procurement member', b ? '!Signed' : '!Awaiting signature', b ? '20 Jul 2027, 14:30 EAT' : '—']]));
const d07 = S({ id: 'D07', d: 'D07', g: G3, name: 'Acceptance signature', vl: 'Base — Brian signs', arch: 'Review or decision', who: 'Brian Wafula · appointed procurement member', at: '20 Jul 2027, 14:30 EAT', subj: 'Frozen report 1',
  title: 'Sign acceptance report', st: 'Active', tab: 'Deliveries', next: turn('Review and sign report 1.', 'Brian Wafula'),
  regions: [sum6, fail6, disp6, sigs(false), prev6, tech6], p: 'Sign report', s2: ['Request correction'], ev: ['Inspection 1', 'Technical certificate 1'] });
out.push(d07,
  D(d07, 'D07 · Correction', 'Request correction dialog', dlg('Request correction', [fl(ta('Reason', ''))], 'Send request')),
  V(d07, { id: 'D07-P', vl: 'Signed — stock update pending', at: '20 Jul 2027, 14:31 EAT', next: wait('Technical operator Daniel Otieno is restoring the stock update; incident assigned 20 Jul 2027, 14:31 EAT.', 'The record is signed. The stock update is still pending.'),
    regions: [sum6, disp6, sigs(true), prev6], p: '', s2: ['View update status', 'View report'] })
);

// D13
const issue13 = R('Issue', r(['Units', 'CM-DEMO-009 and CM-DEMO-010'], ['Result', 'Does not meet'], ['Observed', 'Both units failed to start'], ['Requested remedy', 'Replacement'], ['Requested reply date', '22 July 2027']));
const msg13 = 'Two laptops did not start during inspection. Please arrange replacement and confirm the delivery date.';
const d13 = S({ id: 'D13', d: 'D13', g: G3, name: 'Delivery issue', vl: 'Base — send findings', arch: 'Record detail', who: 'Julia Njeri · contract owner', at: '20 Jul 2027, 15:00 EAT', subj: 'Issue 1 version 1',
  title: 'Two laptops need replacement', st: 'Active', tab: 'Obligations', next: turn('Send the inspection findings to the supplier.', 'Julia Njeri'),
  regions: [issue13, R('Message to supplier', fl(ta('Message', msg13)))], p: 'Send message', s2: ['View acceptance report'], ev: ['Acceptance report 1', 'Inspection 1'] });
out.push(d13,
  V(d13, { id: 'D13-S', vl: 'Supplier reply', who: 'David Ouma · Afya supplier representative', at: '21 Jul 2027, 09:00 EAT', back: 'Back to my contracts', next: turn('Reply to the replacement request.', 'David Ouma'),
    regions: [issue13, R('Message from Ministry of Health', x(msg13)), R('Your reply', fl(ta('Reply', 'We will deliver two replacement laptops on 27 July 2027.')))], p: 'Send reply', s2: ['View acceptance report'] }),
  V(d13, { id: 'D13-C', vl: 'Issue closed', at: '27 Jul 2027, 16:00 EAT', next: done('This issue is closed.'),
    regions: [issue13, R('Resolution', x('Replacement units 011 and 012 were accepted on 27 July 2027.'))], p: '', s2: ['Report a new issue', 'View replacement acceptance'] })
);

// D31
const d31 = S({ id: 'D31', d: 'D31', g: G3, name: 'Required services', vl: 'Base — training evidence', arch: 'Review or decision', who: 'Peter Mugo · appointed technical certifier', at: '27 Jul 2027, 12:00 EAT', subj: 'Goods-plus-service package',
  ref: 'CM-MOH-2027-SVC-001', title: 'Review training completion', st: 'Active', tab: 'Deliveries', next: turn('Record the training evidence.', 'Peter Mugo'),
  regions: [R('Agreement', f(['Goods', '10 laptops · KES 1,000,000'], ['Service', '1 training session · KES 50,000'], ['Total', 'KES 1,050,000'])),
    R('Required service', r(['Requirement', 'Train ten named users to start and operate the supplied laptops'], ['Deadline', '27 Jul 2027'], ['Evidence required', 'Attendance and completed practical checklist'])),
    R('Observations', fl(tx('Observed attendance', '10 of 10'), tx('Practical checklist', '10 complete'), tx('Reference', 'TRAIN-01')), t(['Requirement', 'Result'], [['Training', '!Meets']]))],
  p: 'Save observations', s2: ['View service requirement'], ev: ['Agreement 1', 'TRAIN-01'] });
out.push(d31, V(d31, { id: 'D31-A', vl: 'Service acceptance report', who: 'Julia Njeri · appointed chair', at: '27 Jul 2027, 13:00 EAT', subj: 'Frozen service acceptance report', title: 'Sign acceptance report',
  next: turn('Review and sign the acceptance report.', 'Julia Njeri'),
  regions: [R('Report lines', t(['Line', 'Quantity', 'Accepted', 'Deferred'], [['Training', '1 session', '1', '0']], [2, 3])), R('Technical evidence', x('Technical certificate signed by Peter Mugo, 27 Jul 2027, 12:30 EAT')),
    R('Signatures', t(['Signer', 'Role', 'Status'], [['Julia Njeri', 'Chair', '!Awaiting signature'], ['Peter Mugo', 'Technical member', '!Awaiting signature'], ['Brian Wafula', 'Procurement member', '!Awaiting signature']])),
    R('', xh('Invoice entitlement for the service is KES 50,000, once. No stock or asset unit is created for a training service.'))],
  p: 'Sign report', s2: [], note: 'Title and headline are assumed; the brief names only the report contents and Sign report.' }));

// ── Invoices and Finance ──
const d18 = S({ id: 'D18', d: 'D18', g: G4, name: 'Supplier invoice', vl: 'Base — submit', arch: 'Form or editor', who: 'David Ouma · Afya supplier representative', at: '21 Jul 2027, 08:00 EAT', subj: 'Invoice draft 1', back: 'Back to my contracts',
  title: 'Submit invoice', st: 'Active', tab: 'Invoices', next: turn('Enter the invoice details.', 'David Ouma'),
  regions: [R('Invoice', fl(tx('Invoice number', 'INV-01'), dt('Invoice date', '21 July 2027'), file('Invoice file', 'Supplier invoice INV-01'))),
    R('Items', t(['Item', 'Quantity', 'Rate', 'Tax', 'Total'], [['Laptop', '#10', 'KES 100,000', 'Included', 'KES 1,000,000']], [1, 2, 4]))],
  p: 'Submit invoice', s2: ['Cancel'], ev: ['Agreement 1'] });
out.push(d18,
  V(d18, { id: 'D18-R', vl: 'Needs review — waiting', at: '21 Jul 2027, 08:05 EAT', next: wait('Procurement head Charles Mutiso must review the invoice; assigned 21 Jul 2027, 08:05 EAT.'),
    regions: [R('Invoice INV-01', r(['Status', 'Needs review'], ['Received', '21 Jul 2027, 08:05 EAT'], ['Claimed', '10 laptops · KES 1,000,000']), xs('Two laptops have not been accepted.'))], p: '', s2: ['View invoice', 'View acceptance'] }),
  V(d18, { id: 'D18-C', vl: 'Supplier correction', at: '21 Jul 2027, before 10:00 EAT', title: 'Correct invoice', next: turn('Correct the invoice quantity.', 'David Ouma'),
    regions: [R('Version 1 (retained)', r(['Invoice', 'INV-01 version 1'], ['Claimed', '10 laptops · KES 1,000,000'], ['Received', '21 Jul 2027, 08:05 EAT'])),
      R('Correction', t(['Item', 'Quantity', 'Rate', 'Tax', 'Total'], [['Laptop', '#8', 'KES 100,000', 'Included', 'KES 800,000']], [1, 2, 4]), fl(ta('Reason', 'Corrected to the eight accepted laptops.')))],
    p: 'Submit correction', s2: ['Cancel'], note: 'View instant assumed: before version 2 was received at 10:00.' })
);

const cmp8 = (q, c, warn) => R('Comparison', t(['Item', 'Invoiced', 'Eligible', 'Rate', 'Claimed', 'Supported'], [['Laptop', q, '8', 'KES 100,000', c, 'KES 800,000']], [1, 2, 3, 4, 5]), ...(warn ? [xs('Two laptops have not been accepted.')] : []));
const d08 = S({ id: 'D08', d: 'D08', g: G4, name: 'Invoice review', vl: 'Base — quantity difference', arch: 'Review or decision', who: 'Charles Mutiso · authorised certifier', at: '21 Jul 2027, 09:00 EAT', subj: 'Claim INV-01 version 1',
  title: 'Review invoice', st: 'Active', tab: 'Invoices', next: turn('Resolve the quantity difference.', 'Charles Mutiso'),
  regions: [cmp8('10', 'KES 1,000,000', true)], p: 'Request correction', s2: ['View acceptance report'], ev: ['Supplier invoice INV-01', 'Acceptance report 1', 'Receipt 1'],
  note: 'Correction-first policy (CM-OD-04): no partial certification of the disputed invoice.' });
out.push(d08,
  D(d08, 'D08 · Correction', 'Request correction dialog', dlg('Request correction', [r(['Recipient', 'Afya Digital Supplies Limited']), fl(ta('Message', 'Please correct the invoice to match the eight accepted laptops.'))], 'Send request')),
  V(d08, { id: 'D08-C', vl: 'Corrected claim — certify', at: '21 Jul 2027, before 10:15 EAT', subj: 'Claim INV-01 version 2', next: turn('Review and sign the certification.', 'Charles Mutiso'),
    regions: [R('Comparison', t(['Item', 'Invoiced', 'Eligible', 'Rate', 'Claimed', 'Supported'], [['Laptop', '8', '8', 'KES 100,000', 'KES 800,000', 'KES 800,000']], [1, 2, 3, 4, 5])),
      R('Certification', x('I certify that invoice INV-01 version 2, for KES 800,000, is supported by the cited effective contract and accepted goods or services, after the adjustments and recoveries shown in the certification schedule.'), r(['Accepted units', 'CM-DEMO-001–CM-DEMO-008'], ['Rejected units', 'CM-DEMO-009 and CM-DEMO-010 — not certified'], ['Recipient', 'Finance']))],
    note: 'Statement per §19.5; no adjustments or recoveries apply in this branch.',
    p: 'Sign certification', s2: ['View acceptance report'], ev: ['Supplier invoice INV-01 version 2', 'Acceptance report 1', 'Receipt 1'] }),
  V(d08, { id: 'D08-L', d: 'D08-L', name: 'Corrected claim after early liability', vl: 'Base — Finance must reconcile', p: '', s2: [], at: '21 Jul 2027, 10:15 EAT', subj: 'Isolated claim branch', ref: 'CM-MOH-2027-CLAIM-001', title: 'Review corrected invoice',
    next: blk('Finance must reconcile the original liability.', 'Josphat Mwangi', ['View correction', 'View accounting invoice']),
    regions: [R('Claims', t(['Claim', 'Received', 'Quantity', 'Amount'], [['Original claim', '21 Jul 2027, 08:05 EAT', '10', 'KES 1,000,000'], ['Corrected claim', '21 Jul 2027, 10:00 EAT', '8', 'KES 800,000']], [2, 3])),
      R('Accounting position', r(['Native liability posted', 'KES 1,000,000'], ['Required credit', 'KES 200,000'], ['Reconciled payable', 'Not established'], ['Supported amount', 'KES 800,000']))],
    ev: ['Supplier invoice INV-01', 'Supplier invoice INV-01 version 2', 'Accounting invoice'], note: 'No second liability draft and no KES 1,800,000 payable. After the native credit reconciles at 11:00, D08-C applies.' })
);

// D33
const src33 = R('Source', r(['Source claim', 'INV-01 version 2'], ['Certification', 'Certification 1'], ['Company', 'Ministry of Health'], ['Supplier', 'Afya Digital Supplies Limited'], ['Currency', 'KES'], ['Invoice date', '21 July 2027']));
const items33 = R('Accepted items', t(['Item', 'Quantity', 'Rate', 'Total'], [['Laptop', '8', 'KES 100,000', 'KES 800,000']], [1, 2, 3]));
const acct33 = R('Accounting details', fl(dt('Posting date', '21 July 2027'), sel('Payable account', 'Test supplier payable'), sel('Accounting treatment', 'Test IT equipment'), sel('Tax treatment', 'Test tax included'), sel('Cost centre', 'Test Ministry operations')), xh('Tax breakdown is generated from the configured test template and reconciles to the tax-inclusive KES 800,000.'));
const acct33ro = R('Accounting details', r(['Posting date', '21 July 2027'], ['Payable account', 'Test supplier payable'], ['Accounting treatment', 'Test IT equipment'], ['Tax treatment', 'Test tax included'], ['Cost centre', 'Test Ministry operations']));
const d33 = S({ id: 'D33', d: 'D33', g: G4, name: 'Finance invoice preparation', vl: 'Base — Finance maker', arch: 'Form or editor', who: 'Josphat Mwangi · Finance maker', at: '21 Jul 2027, 11:00 EAT', subj: 'Accounting invoice draft for INV-01 version 2',
  title: 'Prepare accounting invoice', st: 'Active', tab: 'Invoices', next: turn('Complete the accounting details for invoice INV-01.', 'Josphat Mwangi'),
  regions: [src33, items33, acct33], p: 'Submit invoice for approval', s2: ['Save draft', 'View certification', 'Cancel'], ev: ['Supplier invoice INV-01 version 2', 'Certification 1', 'Receipt 1'] });
out.push(d33,
  V(d33, { id: 'D33-U', vl: 'Accounting setup needs review', next: blk('The accounting setup needs review.', 'Finance configuration owner', ['View certification']), p: '', s2: [], note: 'State described inside the D33 brief (unresolved classification mapping); submission is unavailable.' }),
  V(d33, { id: 'D33-W', vl: 'Submitted — waiting', next: wait('Finance is reviewing the accounting invoice.', 'Finance approver Beatrice Kamau; assigned 21 Jul 2027, 11:00 EAT.'), regions: [src33, items33, acct33ro], p: '', s2: ['View certification'] }),
  V(d33, { id: 'D33-A', vl: 'Finance approver review', who: 'Beatrice Kamau · Finance approver', at: '21 Jul 2027, 11:30 EAT', next: turn('Review the accounting invoice.', 'Beatrice Kamau'),
    regions: [src33, items33, acct33ro, R('Prepared by', r(['Finance maker', 'Josphat Mwangi']))], p: 'Approve accounting invoice', s2: ['Return invoice for correction', 'View certification'] })
);
const d33a = out[out.length - 1];
out.push(D(d33a, 'D33-A · Return', 'Return dialog', dlg('Return invoice for correction', [fl(ta('Reason', 'Please review the accounting classification.'))], 'Return invoice')),
  V(d33a, { id: 'D33-A · Posted', vl: 'Posted', next: done('Accounting invoice posted.'), p: '', s2: ['View accounting invoice'], note: 'No claim that payment occurred.' }));

// D09
const d09 = S({ id: 'D09', d: 'D09', g: G4, name: 'Payment follow-up', vl: 'Base — contract owner', arch: 'Record detail (read-only)', who: 'Julia Njeri · contract owner', at: '23 Jul 2027, 09:00 EAT', subj: 'Claim INV-01 version 2 · KES 800,000',
  title: 'Invoice and payment', st: 'Active', tab: 'Invoices', next: wait('Finance approver Beatrice Kamau must confirm payment; assigned 22 Jul 2027, 14:15 EAT.'),
  regions: [R('', r(['Invoice', 'KES 800,000'], ['Certification', 'Signed'], ['Accounting entry', 'Posted'], ['Payment', 'KES 800,000 recorded'], ['Settlement', 'Not confirmed']))],
  s2: ['View payment record', 'View certification'], ev: ['Payment entry 1', 'Certification 1'] });
const payEditor = (amt, ref, date, extra) => [
  R('Source', r(['Company', 'Ministry of Health'], ['Supplier', 'Afya Digital Supplies Limited'], ['Currency', 'KES'], ['Source', 'INV-01 version 2'], ['Certification', 'Certification 1'], ['Accounting invoice', 'Posted'], ['Payable / certified outstanding', amt], ['Payment hold', 'None'], ['Beneficiary', 'Verified test account ending 1234'])),
  R('Payment details', fl(dt('Posting date', date), sel('Payment method', 'Bank transfer recorded'), sel('Bank account', 'Test operating bank'), sel('Payable account', 'Test supplier payable'), tx('Amount', amt), tx('Invoice allocation — INV-01', amt), tx('Reference', ref))),
  R('Calculated', f(['Supported deductions', 'KES 0'], ['Advance recovery', 'KES 0'], ['Unapplied amount', 'KES 0']))].concat(extra || []);
const d09f = V(d09, { id: 'D09-F', vl: 'Finance maker — payment editor', arch: 'Form or editor', who: 'Josphat Mwangi · Finance maker', at: '22 Jul 2027, 13:00 EAT', subj: 'Payment Entry TEST-PE-01 draft 1', title: 'Prepare payment',
  next: turn('Prepare the payment record.', 'Josphat Mwangi'), regions: payEditor('KES 800,000', 'TEST-PAY-01', '22 July 2027'),
  p: 'Submit payment for approval', s2: ['Save draft', 'View certification', 'Cancel'], ev: ['Certification 1', 'Accounting invoice', 'Verified beneficiary reference'] });
out.push(d09, d09f,
  V(d09f, { id: 'D09-F · Submitted', vl: 'Submitted — waiting', next: wait('Finance is reviewing the payment record.', 'Finance approver Beatrice Kamau; assigned 22 Jul 2027, 13:00 EAT.'), p: '', s2: ['View certification'] }),
  V(d09, { id: 'D09-T', vl: 'Technical reader', who: 'Daniel Otieno · Technical operator (site-wide read)', next: null, note: 'Not involved: no next-step block, no mutation. Credentials excluded.' }),
  V(d09, { id: 'D09-AUD', vl: 'Auditor', who: 'Naomi · Site-wide auditor', next: null, note: 'Not involved: no next-step block, no mutation.' })
);

// D17
const pay17 = R('Payment', r(['Supplier', 'Afya Digital Supplies Limited'], ['Invoice', 'INV-01 version 2'], ['Certified / payable', 'KES 800,000'], ['Proposed cash', 'KES 800,000'], ['Prepared by', 'Josphat Mwangi'], ['Payment hold', 'None'], ['Beneficiary reference', 'Verified test account ending 1234'], ['Settlement', 'Not confirmed']));
const det17 = R('Payment details', r(['Posting date', '22 July 2027'], ['Payment method', 'Bank transfer recorded'], ['Bank account', 'Test operating bank'], ['Payable account', 'Test supplier payable'], ['Amount', 'KES 800,000'], ['Allocation', 'INV-01 · KES 800,000'], ['Reference', 'TEST-PAY-01'], ['Supported deductions / advance recovery / unapplied', 'KES 0 / KES 0 / KES 0']));
const d17 = S({ id: 'D17', d: 'D17', g: G4, name: 'Finance payment approval', vl: 'Base — approver review', arch: 'Review or decision', who: 'Beatrice Kamau · Finance approver', at: '22 Jul 2027, 14:00 EAT', subj: 'Payment Entry TEST-PE-01 draft 1',
  title: 'Review payment', st: 'Active', tab: 'Invoices', next: turn('Review the payment record.', 'Beatrice Kamau'),
  regions: [pay17, det17], p: 'Approve payment', s2: ['Return payment for correction', 'View certification'], ev: ['Certification 1', 'Accounting invoice', 'Payment Entry TEST-PE-01'] });
out.push(d17,
  D(d17, 'D17 · Return', 'Return dialog', dlg('Return payment for correction', [fl(ta('Reason', 'Please review the payment allocation.'))], 'Return payment')),
  V(d17, { id: 'D17 · Posted', vl: 'Approved — posted', at: '22 Jul 2027, 14:15 EAT', next: done('Payment entry posted. Settlement is not confirmed.'), p: '', s2: ['View payment record'] }),
  V(d17, { id: 'D17 · Pending', vl: 'Approval pending', next: wait('The payment update is still pending.'), p: '', s2: ['View update status'] }),
  V(d09f, { id: 'D09-F · Stale', vl: 'Changed since review', next: blk('This payment has changed. Review the latest version.', 'Josphat Mwangi', ['Review latest version']), p: '', s2: [], note: 'Stale-review message from the D09-F card; the fix label is assumed.' }),
  V(d17, { id: 'D17-H', vl: 'Payment on hold', regions: [R('Payment', r(['Supplier', 'Afya Digital Supplies Limited'], ['Invoice', 'INV-01 version 2'], ['Prepared by', 'Josphat Mwangi'], ['Payment hold', 'Certification missing'], ['Settlement', 'Not confirmed']))],
    next: blk('This payment is on hold.', 'Charles Mutiso', ['View missing certification']), p: '', s2: [], note: 'Back to contracts is the header navigation.' }),
  V(d17, { id: 'D17-S', vl: 'Record settlement', at: '23 Jul 2027, 10:00 EAT', subj: 'Payment Entry TEST-PE-01 (posted)', next: turn('Record payment confirmation.', 'Beatrice Kamau'),
    regions: [R('Settlement', fl(tx('Amount', 'KES 800,000'), dt('Settlement date', '23 July 2027'), tx('Bank reference', 'TEST-BANK-01'), file('Evidence', 'Test bank confirmation 1')))], p: 'Confirm payment', s2: ['View payment record'],
    note: 'No bank transfer control: KenTender records settlement evidence only.' })
);

// D28
const set1 = ['TEST-PE-PART-01', 'KES 500,000', '!Confirmed', '23 Jul 2027, 10:00', 'TEST-BANK-PART-01'];
const setCols = ['Payment entry', 'Amount', 'Status', 'Date', 'Bank reference'];
const d28 = S({ id: 'D28', d: 'D28', g: G4, name: 'Partly paid invoice', vl: 'Base — partly paid', arch: 'Record detail', who: 'Julia Njeri · contract owner', at: '23 Jul 2027, 11:00 EAT', subj: 'Isolated partial-payment branch · INV-01 version 2',
  title: 'Invoice and payment', st: 'Active', tab: 'Invoices', next: wait('Finance approver Beatrice Kamau is following up the remaining KES 300,000; assigned 23 Jul 2027, 10:05 EAT.'),
  regions: [R('', r(['Certified', 'KES 800,000'], ['Cash confirmed', 'KES 500,000'], ['Noncash adjustment', 'KES 0'], ['Outstanding', 'KES 300,000'], ['Invoice', 'Partly paid'])), R('Settlements', t(setCols, [set1], [1]))],
  s2: ['View certification', 'View settlement'], ev: ['Certification 1', 'TEST-PE-PART-01'], note: 'No separate contract identity is given for this branch; the base reference is shown.' });
out.push(d28,
  V(d28, { id: 'D28-F', vl: 'Finance maker — remaining payment', who: 'Josphat Mwangi · Finance maker', at: '24 Jul 2027, 09:00 EAT', next: turn('Prepare payment for the remaining KES 300,000.', 'Josphat Mwangi'),
    regions: [R('Proposed payment', r(['Native entry', 'TEST-PE-PART-02'], ['Amount', 'KES 300,000'], ['Payment hold', 'None'], ['Certified outstanding', 'KES 300,000'])), R('Settlements', t(setCols, [set1], [1]))], p: 'Prepare payment', s2: [] }),
  V(d09f, { id: 'D28-F · Editor', d: 'D28', g: G4, vl: 'Payment editor — KES 300,000', at: '24 Jul 2027, 09:00 EAT', subj: 'Payment Entry TEST-PE-PART-02 draft', regions: payEditor('KES 300,000', 'TEST-PAY-PART-02', '24 July 2027'), ev: ['Certification 1', 'TEST-PE-PART-01'] }),
  V(d28, { id: 'D28-C', vl: 'Fully settled', at: '25 Jul 2027, 10:00 EAT', next: done('Finance confirmed the remaining KES 300,000 on 25 Jul 2027, 10:00 EAT.'),
    regions: [R('', r(['Certified', 'KES 800,000'], ['Cash confirmed', 'KES 800,000'], ['Noncash adjustment', 'KES 0'], ['Outstanding', 'KES 0'])), R('Settlements', t(setCols, [set1, ['TEST-PE-PART-02', 'KES 300,000', '!Confirmed', '25 Jul 2027, 10:00', '—']], [1]))] }),
  V(d28, { id: 'D28-V', vl: 'Second settlement reversed', at: '26 Jul 2027, 10:00 EAT', next: wait('Finance approver Beatrice Kamau is following up the remaining KES 300,000; assigned 26 Jul 2027, 10:00 EAT.'),
    regions: [R('', r(['Certified', 'KES 800,000'], ['Cash confirmed', 'KES 500,000'], ['Noncash adjustment', 'KES 0'], ['Outstanding', 'KES 300,000'], ['Invoice', 'Partly paid'])),
      R('Settlements', t(setCols, [set1, ['TEST-PE-PART-02', 'KES 300,000', '!Reversed', 'Reversed 26 Jul 2027, 10:00', '—']], [1]), lk('Original settlement', 'Reversal'))],
    note: 'Waiting headline wording is assumed from D28 with the reversal instant.' })
);

// D29
const clause29 = R('Advance clause', r(['Allowed', '10% of KES 1,000,000 = KES 100,000'], ['Payable', 'After effective signature'], ['Recovery', 'KES 10,000 per laptop accepted and invoiced']));
const guar29 = (st) => R('Advance guarantee', r(['Guarantee', 'TEST-AG-01'], ['Beneficiary', 'Ministry of Health'], ['Amount', 'KES 100,000'], ['Issuer', 'Test Bank'], ['Valid through', '31 Aug 2027'], ['Issuer confirmation', 'TEST-AG-CONF-01'], ['Status', st]));
const d29 = S({ id: 'D29', d: 'D29', g: G4, name: 'Advance support', vl: 'Base — advance claim', arch: 'Review or decision', who: 'Charles Mutiso · authorised certifier', at: '5 Jul 2027, 09:00 EAT', subj: 'Isolated advance branch',
  title: 'Review advance request', st: 'Active', tab: 'Invoices', next: turn('Review the advance and its guarantee.', 'Charles Mutiso'),
  regions: [clause29, guar29('Verified'), R('Claim', f(['Claim', 'ADV-01'], ['Amount', 'KES 100,000']))], p: 'Sign advance certification', s2: ['View advance clause', 'View guarantee'], ev: ['Advance clause', 'Guarantee TEST-AG-01'],
  note: 'Synthetic issued clause; not an advance option added to the base no-advance contract.' });
out.push(d29,
  V(d29, { id: 'D29-H', vl: 'Guarantee not verified', regions: [clause29, guar29('Not verified')], next: blk('The advance guarantee has not been verified.', 'Josphat Mwangi', ['View guarantee', 'View issue']), p: '', s2: [] }),
  V(d29, { id: 'D29-R', vl: 'Recovery on first invoice', at: 'Not stated', title: 'Review invoice', next: turn('Review and sign the certification.', 'Charles Mutiso'),
    regions: [R('Recovery', t(['Invoice', 'Gross', 'Advance recovery', 'Proposed cash', 'Advance remaining'], [['Accepted goods — 8 laptops', 'KES 800,000', 'KES 80,000', 'KES 720,000', 'KES 20,000']], [1, 2, 3, 4]),
      r(['Prior cash advance', 'KES 100,000'], ['Last two units', 'Invoice KES 200,000 would recover KES 20,000 and require KES 180,000 cash']))],
    p: 'Sign certification', s2: ['View advance clause'], note: 'Instant, title and headline are not supplied for D29-R; these are assumed.' })
);
return out;
} });
