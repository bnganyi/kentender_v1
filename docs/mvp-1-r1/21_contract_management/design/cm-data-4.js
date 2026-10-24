(window.CMP = window.CMP || []).push({ o: 4, f: function (h) {
const { f, r, t, fl, x, xs, xh, lk, bt, pv, R, tx, dt, ta, file, ro, sel, rad, wide, turn, wait, done, blk, dlg, S, V, D } = h;
const G7 = '7 · Termination and security claims', G8 = '8 · Close-out', G9 = '9 · Existing contract intake', G10 = '10 · System states';
const out = [];
const TERM = 'CM-MOH-2027-TERM-001';

// D20
const d20 = S({ id: 'D20', d: 'D20', g: G7, name: 'Termination review', vl: 'Base — AO decision', arch: 'Review or decision', who: 'Amina Hassan · Accounting Officer', at: '10 Aug 2027, 10:00 EAT', subj: 'Agreement 1 · termination 1 draft 1',
  ref: TERM, title: 'Review contract termination', st: 'Active', tab: 'Obligations', next: turn('Decide the termination request.', 'Amina Hassan'),
  regions: [R('Grounds', r(['Grounds', 'Material non-delivery'], ['Contractual notice', 'Completed in this synthetic branch'], ['HOP recommendation', 'Terminate unperformed balance'])),
    R('Financial position', f(['Accepted value', 'KES 800,000'], ['Cash paid', 'KES 600,000'], ['Supported unpaid', 'KES 200,000'], ['Advance balance', 'KES 0'], ['Disputed claim', 'KES 0'])),
    R('Supporting evidence', lk('Contract clause 8', 'Default notice and delivery proof', 'Cure-period record', 'Legal advice 1', 'Settlement calculation 1'))],
  p: 'Approve termination', s2: ['Decline', 'Return for correction'], ev: ['Contract clause 8', 'Default notice and delivery proof', 'Cure-period record', 'Legal advice 1', 'Settlement calculation 1'] });
out.push(d20,
  D(d20, 'D20 · Decline', 'Decline dialog (required reason)', dlg('Decline termination', [fl(ta('Reason', ''))], 'Confirm decision')),
  V(d20, { id: 'D20-P', vl: 'Approved — notice not delivered', at: '10 Aug 2027, 10:15 EAT', next: wait('Procurement head Charles Mutiso must deliver the termination notice; assigned 10 Aug 2027, 10:15 EAT.'), p: '', s2: ['View notice', 'View delivery status'] }),
  V(d20, { id: 'D20-T', vl: 'Termination effective', at: '10 Aug 2027, 11:00 EAT', st: 'Terminated', next: wait('Finance approver Beatrice Kamau is settling KES 200,000; assigned 10 Aug 2027, 11:00 EAT.'), p: '', s2: ['View termination record', 'View settlement'],
    note: 'No Complete contract action. Terminated is never shown as Completed.' })
);

// D39
const d39p = S({ id: 'D39-P', d: 'D39', g: G7, name: 'Termination settlement', vl: 'Prepare (HOP)', arch: 'Review or decision', who: 'Charles Mutiso · HOP', at: '20 Aug 2027, 09:00 EAT', subj: 'Finance reconciliation TERM-01',
  ref: TERM, title: 'Review termination settlement', st: 'Terminated', tab: 'Obligations', next: turn('Review the reconciled settlement.', 'Charles Mutiso'),
  regions: [R('Reconciliation', r(['Finance reconciliation', 'TERM-01'], ['Accepted', 'KES 800,000'], ['Cash', 'KES 800,000'], ['Advance, credits, costs, disputes', 'KES 0'], ['Final supported obligation', 'KES 800,000'], ['Budget decrease', 'Acknowledged'], ['Unclassified remaining items', 'None']))],
  p: 'Submit settlement for completion', s2: ['Return for correction', 'View reconciliation'], ev: ['Finance reconciliation TERM-01'] });
const set39 = (closure) => R('Settlement', r(['Accepted work', 'KES 800,000'], ['Cash confirmed', 'KES 600,000 + KES 200,000'], ['Advance', 'KES 0'], ['Credit', 'KES 0'], ['Authorised costs', 'KES 0'], ['Dispute', 'KES 0'], ['Unperformed balance', 'KES 200,000 extinguished by effective termination'], ['Final supported obligation', 'KES 800,000'], ['Budget decrease', 'Acknowledged'], ['Closure acknowledgement', closure]));
const d39 = S({ id: 'D39', d: 'D39', g: G7, vl: 'Complete (AO)', arch: 'Review or decision', who: 'Amina Hassan · Accounting Officer', at: '20 Aug 2027, 10:00 EAT', subj: 'HOP-reviewed reconciliation',
  ref: TERM, title: 'Complete termination settlement', st: 'Terminated', tab: 'Obligations', next: turn('Review the settlement record.', 'Amina Hassan'),
  regions: [set39('Pending')], p: 'Complete settlement', s2: ['Return for correction', 'View termination'], ev: ['Finance reconciliation TERM-01', 'HOP review'] });
out.push(d39p, d39,
  D(d39, 'D39 · Complete', 'Completion dialog', dlg('Complete settlement', [fl(ta('Reason', 'All required settlement facts reconciled'))], 'Confirm completion')),
  V(d39, { id: 'D39-C', vl: 'Settlement completed', next: done('Amina Hassan completed the termination settlement on 20 Aug 2027, 10:00 EAT.', 'Funding finalisation pending with the Budget owner.'), p: '', s2: ['View settlement', 'View funding update'],
    note: 'Lifecycle stays Terminated; never Completed.' }),
  V(d39, { id: 'D39-H', vl: 'Advance recovery unresolved', regions: [R('Settlement', r(['Accepted work', 'KES 800,000'], ['Outstanding advance', 'KES 20,000'], ['Survivor disposition', 'None valid']))],
    next: blk('The advance recovery needs resolution.', 'Finance owner', ['View recovery', 'View remaining obligations']), p: '', s2: [] })
);

// D37
const SEC = 'CM-MOH-2027-SEC-001';
const inst37 = R('Instrument', r(['Instrument', 'TEST-SG-01 (verified)'], ['Amount', 'KES 100,000'], ['Expiry', '31 Aug 2027'], ['Custodian', 'Charles Mutiso'], ['Claim basis', 'TEST-SG-CLAUSE-01']));
const claim37 = R('Proposed claim', r(['Amount', 'KES 40,000 — generated from test loss review'], ['Grounds', 'Failure to perform the unfulfilled obligation'], ['Recipient', 'Test issuer'], ['Claimant authority', 'Reviewed test mandate 1']));
const d37 = S({ id: 'D37', d: 'D37', g: G7, name: 'Security claim', vl: 'Base — prepare claim', arch: 'Review or decision', who: 'Charles Mutiso · HOP', at: '12 Aug 2027, 09:00 EAT', subj: 'Isolated termination/security contract',
  ref: SEC, title: 'Review security claim', st: 'Terminated', tab: 'Obligations', next: turn('Prepare the supported claim.', 'Charles Mutiso'),
  regions: [inst37, claim37], p: 'Request claim', s2: ['View instrument', 'Cancel'], ev: ['Instrument TEST-SG-01', 'Default notice', 'Cure record', 'Termination notice', 'TEST-SG-CLAUSE-01'] });
const d37p = V(d37, { id: 'D37-P', vl: 'Awaiting issuer outcome', at: '13 Aug 2027, 09:00 EAT', next: wait('Test issuer must respond to the approved claim; communication delivered 12 Aug 2027, 11:00 EAT.'),
  regions: [inst37, R('Approved claim', r(['Amount', 'KES 40,000'], ['Communication', 'Delivered 12 Aug 2027, 11:00 EAT'], ['Outcome', 'Not recorded']))], p: '', s2: ['Record claim outcome'], note: 'Waiting headline wording assumed. Cash receipt needs separate Finance recovery and confirmation.' });
out.push(d37,
  V(d37, { id: 'D37-A', vl: 'AO decision', who: 'Amina Hassan · Accounting Officer', at: '12 Aug 2027, 10:00 EAT', next: turn('Decide the security claim.', 'Amina Hassan'), p: 'Approve claim', s2: ['Decline', 'Return for correction'],
    note: 'Headline assumed. Decision gives no cash status; amount stays KES 40,000.' }),
  d37p,
  D(d37p, 'D37-P · Outcome', 'Record claim outcome dialog', dlg('Record claim outcome', [fl(tx('Issuer reference', 'TEST-SG-OUT-01'), dt('Date', '13 Aug 2027'), file('Evidence', 'Test issuer outcome 1'), tx('Actual proceeds', 'KES 40,000'))], 'Save outcome')),
  V(d37, { id: 'D37-X', vl: 'Replacement instrument', at: '15 Aug 2027, 09:00 EAT', title: 'Verify replacement security', next: turn('Verify the replacement instrument.', 'Charles Mutiso'),
    regions: [R('Instruments', t(['Instrument', 'Amount', 'Expiry', 'Status'], [['TEST-SG-01', 'KES 100,000', '31 Aug 2027', '!Operative'], ['TEST-SG-02', 'KES 100,000', '30 Sep 2027', '!Not verified']], [1]), r(['Issuer confirmation', 'TEST-SG-CONF-02']), xh('The old instrument remains operative until the replacement is verified. Nothing is released on expiry.'))],
    p: 'Verify replacement', s2: ['Reject replacement'], note: 'Title and headline assumed.' })
);

// ── Close-out ──
const d32 = S({ id: 'D32', d: 'D32', g: G8, name: 'Final acceptance', vl: 'Base — completed branch', arch: 'Review or decision', who: 'Amina Hassan · AO acceptance authority', at: '28 Jul 2028, 08:30 EAT', subj: 'Final acceptance 1',
  title: 'Record final acceptance', st: 'Active', tab: 'Obligations', next: turn('Review the final acceptance evidence.', 'Amina Hassan'),
  regions: [R('Completion facts', r(['Units accepted', '10'], ['Initial 8 — warranty ended', '20 Jul 2028'], ['Replacements 2 — warranty ended', '27 Jul 2028'], ['Unresolved completion defects', 'None'], ['Final-acceptance treatment (test source)', 'All obligations fulfilled'])),
    R('Final acceptance record', x('I record final acceptance on 28 July 2028 for the scope identified in the schedule under the test-source final-acceptance term and the evidence listed. The remaining obligations, if any, are listed below.'), r(['Scope', 'Whole contract — 10 laptops'], ['Remaining obligations', 'None'])),
    R('Evidence', lk('Initial report 1', 'Replacement report 1', 'Warranty history 1'))],
  p: 'Sign final acceptance', s2: ['Return for correction'], ev: ['Initial report 1', 'Replacement report 1', 'Warranty history 1'], note: 'Statement per §19.5; this record starts the §145 security-return clock. Date is the signing date of this branch.' });
out.push(d32,
  D(d32, 'D32 · Return', 'Return dialog', dlg('Return for correction', [fl(ta('Reason', ''))], 'Return')),
  V(d32, { id: 'D32-H', vl: 'Open defect — blocked', ref: 'CM-MOH-2027-WAR-OPEN-001', who: 'Julia Njeri · contract owner', subj: 'Agreement 1 · claim 1',
    next: blk('Unit CM-WAR-OPEN-004 still has an unresolved completion defect.', 'Julia Njeri', ['View claim']),
    regions: [R('Completion facts', r(['Warranty', 'Warranty expired; timely claim remains open'], ['Remedy', 'Supplier remedy pending'], ['Defect', 'Battery does not charge — notified 10 Jul 2028'])), R('Evidence', lk('Claim 1', 'Diagnostic 1', 'Defect notice 1'))],
    p: '', s2: [], ev: ['Claim 1', 'Diagnostic 1', 'Defect notice 1'] })
);
const d22 = S({ id: 'D22', d: 'D22', g: G8, name: 'Completion certificate', vl: 'Base', arch: 'Review or decision', who: 'Charles Mutiso · HOP', at: '28 Jul 2028, 09:00 EAT', subj: 'Completion certificate draft 1',
  title: 'Confirm contract completion', st: 'Active', tab: 'Obligations', next: turn('Issue the completion certificate.', 'Charles Mutiso'),
  regions: [R('Certificate summary', r(['Delivered and accepted', '10 laptops'], ['Initial acceptance', '8 on 20 July 2027'], ['Replacement acceptance', '2 on 27 July 2027'], ['Contracted services', 'No contracted service line'], ['Unresolved defects', 'None'], ['Final acceptance', 'Recorded'], ['Obligations', 'All fulfilled'], ['Recipient', 'Afya Digital Supplies Limited']), x('I confirm delivery and acceptance of the goods and services identified in the contract completion schedule, under contract CM-MOH-2027-001 agreement 1, completed on 28 July 2028, with the surviving obligations expressly listed.'), r(['Surviving obligations', 'None']))],
  p: 'Sign and issue certificate', s2: ['View completion evidence'], ev: ['Final acceptance 1', 'Financial reconciliation 1'], note: 'Statement per §19.5 (§154(a), HOP → contractor). Completion date taken from the AO final-acceptance record of 28 Jul 2028.' });
out.push(d22, V(d22, { id: 'D22-P', vl: 'Issued — delivery pending', next: wait('Procurement head Charles Mutiso must confirm certificate delivery; assigned 28 Jul 2028, 09:00 EAT.'), p: '', s2: ['View delivery status', 'View certificate'] }));

const d11 = S({ id: 'D11', d: 'D11', g: G8, name: 'Close-out review', vl: 'Base — completed branch', arch: 'Review or decision', who: 'Amina Hassan · Accounting Officer', at: '28 Jul 2028, 10:00 EAT', subj: 'Closure draft 1',
  title: 'Close contract', st: 'Active', tab: 'Obligations', next: turn('Review and sign the close-out record.', 'Amina Hassan'),
  regions: [R('Completion review', f(['Accepted', '10'], ['Invoiced', 'KES 1,000,000'], ['Cash confirmed', 'KES 1,000,000'], ['Balance', 'KES 0']),
    r(['Warranty', 'Ended with no unresolved claim'], ['Security', 'Not required'], ['Required reporting', 'Complete'], ['Completion certificate', 'Certificate 1'])), R('Close-out decision', x('I close this procurement contract following the evidenced completion recorded below. The surviving obligations and their accountable owners are listed in the attached schedule.'), r(['Surviving obligations', 'None']))],
  p: 'Sign close-out', s2: ['Return for correction'], ev: ['Completion certificate 1', 'Financial reconciliation 1'] });
out.push(d11,
  D(d11, 'D11 · Return', 'Return dialog', dlg('Return for correction', [fl(ta('Reason', ''))], 'Return')),
  V(d11, { id: 'D11-B', vl: 'Open warranty claim — blocked', ref: 'CM-MOH-2027-WAR-OPEN-001', who: 'Julia Njeri · contract owner', at: '21 Jul 2028, 09:00 EAT', subj: 'Claim 1',
    next: blk('Resolve the remaining claim before close-out.', 'Julia Njeri', ['View claim', 'View remaining obligations']),
    regions: [R('Completion review', r(['Warranty', 'Warranty expired; timely claim remains open'], ['Open claim', 'Unit CM-WAR-OPEN-004'], ['Close-out', 'Not available while the claim is open']))], p: '', s2: [], ev: ['Claim 1'] }),
  V(d11, { id: 'D11-C', vl: 'Closed', st: 'Closed', next: done('Amina Hassan closed the contract on 28 Jul 2028, 10:00 EAT.'), p: '', s2: ['View close-out record', 'View history'] }),
  V(d11, { id: 'D11-T', vl: 'Terminated — settlement continues', ref: TERM, at: '10 Aug 2027, 11:00 EAT', st: 'Terminated', subj: 'Termination 1',
    next: wait('Finance approver Beatrice Kamau is settling KES 200,000; assigned 10 Aug 2027, 11:00 EAT.'),
    regions: [R('Position', f(['Accepted units', '8'], ['Accepted obligation', 'KES 800,000'], ['Cash confirmed', 'KES 600,000'], ['Supported unpaid', 'KES 200,000']))], p: '', s2: ['View termination record', 'View settlement'], ev: ['Termination 1'],
    note: 'Never shown as Completed.' })
);

const CLOSE = 'CM-MOH-2027-CLOSE-001';
const d38p = S({ id: 'D38-P', d: 'D38', g: G8, name: 'Close-out correction', vl: 'Prepare (HOP)', arch: 'Form or editor', who: 'Charles Mutiso · HOP', at: '29 Jul 2028, 11:00 EAT', subj: 'Closure 1, 28 Jul 2028',
  ref: CLOSE, title: 'Request close-out correction', st: 'Closed', tab: 'Obligations', next: turn('Explain the completion error.', 'Charles Mutiso'),
  regions: [R('Original closure', r(['Closure', 'Closure 1, 28 Jul 2028'], ['Affected output', 'Completion certificate 1'])),
    R('Correction', fl(ta('Reason', 'Required completion certificate delivery was recorded without evidence'), file('Evidence', 'Delivery incident 1'), ro('Proposed disposition', 'Reopen for completion')))],
  p: 'Submit correction', s2: ['Save draft', 'Cancel'], ev: ['Closure 1', 'Completion certificate 1'] });
const d38 = S({ id: 'D38', d: 'D38', g: G8, vl: 'AO decision', arch: 'Review or decision', who: 'Amina Hassan · Accounting Officer', at: '30 Jul 2028, 09:00 EAT', subj: 'HOP correction 1',
  ref: CLOSE, title: 'Review close-out correction', st: 'Closed', tab: 'Obligations', next: turn('Decide the correction.', 'Amina Hassan'),
  regions: [R('Correction', r(['Finding', 'Required completion certificate delivery was marked complete; actual delivery is not established'], ['Financial total', 'KES 1,000,000, unchanged']), xh('Keep closed with surviving work is unavailable: the bound completion rule requires this evidence.'), lk('Closure 1', 'Delivery incident 1', 'HOP review 1'))],
  p: 'Reopen contract', s2: ['-Keep closed with surviving work', 'Return for correction', 'View closure'], ev: ['Closure 1', 'Delivery incident 1', 'HOP review 1'] });
out.push(d38p, d38,
  D(d38, 'D38 · Reopen', 'Reopen dialog', dlg('Reopen contract', [fl(ta('Reason', 'Required completion evidence was not established'))], 'Confirm reopening')),
  V(d38, { id: 'D38-R', vl: 'Reopened', who: 'Charles Mutiso · HOP', st: 'Active', next: turn('Confirm certificate delivery.', 'Charles Mutiso'),
    regions: [R('History', r(['Closure 1', 'Retained'], ['Reopening 1', 'Recorded 30 Jul 2028'], ['Spending, stock and legal dates', 'Unchanged']))], p: '', s2: ['View history'], note: 'Headline taken from the named Charles task; footer actions not supplied.' }),
  V(d38, { id: 'D38-T', vl: 'Terminated source', st: 'Terminated', next: null, regions: [R('Correction', xh('A terminated contract cannot be reopened through close-out correction; this needs a legal referral.'))], p: '', s2: ['View termination', 'View settlement'],
    note: 'Reopen contract absent. No next-step block is specified for this variant.' })
);

// ── Intake ──
const EXTC = 'CM-MOH-2027-EXT-001';
const src12 = (egp) => R('Source', fl(...[sel('Source', egp ? 'eGP' : 'External records', ['External records', 'eGP']), tx('Source contract reference', 'MOH/ICT/2027/EXT-01')].concat(egp ? [tx('eGP tender reference', ''), tx('eGP contract reference', '')] : []).concat([
  sel('Supplier', 'Afya Digital Supplies Limited'), file('Signed agreement', 'Agreement EXT-01'), ro('Amendments', 'None'), dt('Signed on', '2 July 2027'), dt('Effective on', '2 July 2027'), dt('Cutover', '3 August 2027, 00:00 EAT')])));
const rest12 = [
  R('Parties and ownership', fl(ro('Named owner', 'Julia Njeri'), ro('Managing unit', 'Digital Health'), ro('Supplier signatory', 'Mary Wanjiku — signed 2 Jul 2027'), ro('Entity signatory', 'Amina Hassan — signed 2 Jul 2027'), ro('Review regime', 'Kenya public procurement — applicability review pending'), tx('Source clause reference', 'Agreement EXT-01 §§2–8'))),
  R('Value and items', fl(tx('Original value', 'KES 1,000,000'), tx('Current value', 'KES 1,000,000'), ro('Currency', 'KES')),
    t(['Item description', 'Quantity', 'UOM', 'Rate', 'Tax treatment', 'Serial tracking'], [['~Laptop', '#10', '^Each|Each', '~KES 100,000', '^Included|Included,Excluded', 'Yes']])),
  R('Operative terms', fl(dt('Delivery', '20 July 2027'), tx('Payment days', '30'), tx('Warranty months', '12'), ro('Advance', 'Not provided — pending source verification'), ro('Security', 'Not required — pending source verification')),
    r(['Acceptance', 'Each unit inspected against 16 GB RAM, 512 GB storage and successful start'], ['Payment', 'Within 30 days of correct invoice and eligible acceptance'], ['Restrictions', 'None recorded'], ['Completion', 'After all contractual obligations'])),
  R('Opening position', fl(tx('Accepted', '4'), tx('In custody', '2'), tx('Invoiced', 'KES 400,000'), tx('Credits', 'KES 0'), tx('Confirmed cash', 'KES 300,000'), tx('Outstanding', 'KES 100,000'), tx('Advance', 'KES 0')),
    r(['Linked receipt', '1'], ['Linked invoice', '1'], ['Linked payment and settlement', '1']), xh('Draft entered facts, not confirmed native balances until Finance review. Unknown values stay blank as Not established.')),
  R('', pv('View source clauses', [['Agreement EXT-01 §§2–8', 'Locators for the values above']], false))];
const d12 = S({ id: 'D12', d: 'D12', g: G9, name: 'Register existing contract', vl: 'Base — External records', arch: 'Form or editor', who: 'Brian Wafula · authorised preparer', at: '3 Aug 2027, 09:00 EAT', subj: 'Intake draft 1',
  ref: EXTC, title: 'Register existing contract', st: 'Preparing', tab: 'Agreement', next: turn('Record the signed contract and its current position.', 'Brian Wafula'),
  regions: [src12(false)].concat(rest12), p: 'Save and review', s2: ['Cancel'], ev: ['Agreement EXT-01'], note: 'Synthetic terms, not legal defaults. No statutory-rule selector; no Sign contract action.' });
out.push(d12, V(d12, { id: 'D12-G', vl: 'eGP source', regions: [src12(true)].concat(rest12), ev: ['Agreement EXT-01 — Recorded from external source'], note: 'eGP references required; evidence labelled Recorded from external source. No eGP verification badge.' }));
const d21 = S({ id: 'D21', d: 'D21', g: G9, name: 'Opening position', vl: 'Base — Finance confirms', arch: 'Review or decision', who: 'Beatrice Kamau · Finance approver', at: '3 Aug 2027, 10:00 EAT', subj: 'Intake version 1',
  ref: EXTC, title: 'Review prior activity', st: 'Preparing', tab: 'Invoices', next: turn('Confirm the opening position.', 'Beatrice Kamau'),
  regions: [R('Opening comparison', t(['Fact', 'Source', 'Native linked'], [['Accepted units', '4', '4'], ['In custody', '2', 'Custody record 2'], ['Invoiced', 'KES 400,000', 'KES 400,000'], ['Cash paid', 'KES 300,000', 'KES 300,000'], ['Outstanding', 'KES 100,000', 'KES 100,000'], ['Advance', 'KES 0', 'KES 0']], [1, 2]))],
  p: 'Confirm opening position', s2: ['Report difference'], ev: ['External acceptance 1', 'Linked receipt 1', 'Linked invoice 1', 'Linked payment and settlement 1'] });
out.push(d21, V(d21, { id: 'D21-H', vl: 'Start management', who: 'Charles Mutiso · HOP', at: '3 Aug 2027, 11:00 EAT', tab: 'Agreement', next: turn('Start managing this contract.', 'Charles Mutiso'),
  regions: [R('Intake', r(['Source and terms', 'Checked'], ['Opening position', 'Confirmed'], ['Next work', 'Inspect two units in custody']))], p: 'Start management', s2: ['View source contract'],
  note: 'No posting or signing task is created by intake.' }));

// ── System states ──
out.push(
  S({ id: 'D-ERR', d: 'D-ERR', g: G10, name: 'Record load error', vl: 'Error page', page: 'state', icon: 'err', who: 'Any record', msg: 'This record could not be loaded.', p: 'Retry', s2: ['Back to contracts'], note: 'No trusted record facts or business actions. Retry only reloads.' }),
  S({ id: 'D-DENIED', d: 'D-DENIED', g: G10, name: 'Access denied', vl: 'Shared denial page', page: 'state', icon: 'lock', who: 'Grace Wanjiku · Departmental Author only', at: '3 Aug 2027, 12:00 EAT', msg: 'You do not have access to this contract.', s2: ['Back to contracts'], note: 'Shared KT-STD §3A denial; no protected content.' })
);
return out;
} });
