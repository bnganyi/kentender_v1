(window.EVL_Q = window.EVL_Q || []).push(function (E) {
  const { p, f, kv, tb, n, fi, ra, sg, ds, at, lk, ev, T, TN, TT, AF, KES } = E;
  const G3 = 'D03 Evaluation record', G4 = 'D04 Requirement review', G5 = 'D05 Committee discussion';
  const rec = (o) => E.recHead(Object.assign({ arch: 'Review or decision', state: 'Reviewing', tabs: ['Results', 'Committee record'], tab: 0 }, o));
  const source = ds('Opening and source record', ['Opening completed 12 Jun 2027, 11:10:30 EAT', 'Bid received 10 Jun 2027, 14:32:01 EAT', 'Submitted Version 1'], { links: ['View opening record', 'View submitted bid'] });

  E.add(
    rec({ id: 'D03', g: G3, name: 'Record — evidence needs discussion', actor: 'grace', at: '14 Jun 2027, 08:55 EAT', spec: '§9.4',
      tr: T('dcn', 'Grace Wambui'), nx: { k: 'turn', h: 'Discuss the service-location finding with the committee.' },
      blocks: [
        E.comp([[AF, 'Meets', 'Needs review', KES, 'Needs review', 'Not ranked', '@Review bid']], { caption: 'The offered values have been checked. One supporting-evidence question remains.' }),
        at('Service location — supporting evidence needs review', 'Peter Mugo, 14 Jun 08:50 · Task: Resolve evaluation concern for ' + TN),
        source],
      pri: 'Start discussion', sec: ['View report'], note: 'Canonical board; D05-CONCERN is an alias of this view.' }),
    rec({ id: 'D03-READY', g: G3, name: 'Record — comparison complete', actor: 'grace', at: '16 Jun 2027, 10:00 EAT', spec: '§9.4',
      tr: T('dcn', 'Grace Wambui'), nx: { k: 'turn', h: 'Review the completed comparison and report.' },
      blocks: [E.comp([[AF, 'Meets', 'Meets', KES, KES, '1', '@Review bid']]),
        at('Afya Digital Supplies Limited is the only responsive bidder.'),
        at('Recommendation: Afya Digital Supplies Limited · KES 46,400,000.00.', null, { strong: true }), source],
      pri: 'View report', sec: ['Committee record'], note: 'Later read of the comparison calculated at 09:05:05. No award button.' }),
    rec({ id: 'D03-FUNDING', g: G3, name: 'Record — funding shortfall', actor: 'grace', at: '16 Jun 2027, 10:00 EAT', spec: '§9.4',
      tr: T('dcn', 'Grace Wambui'), nx: { k: 'turn', h: 'Review the completed comparison and report.' },
      blocks: [E.comp([[AF, 'Meets', 'Meets', KES, KES, '1', '@Review bid']]),
        f(['Available funding', 'KES 45,000,000.00'], ['Shortfall', 'KES 1,400,000.00'], ['Source', 'Budget confirmation, 16 Jun 2027, 09:50 EAT']),
        at('Recommendation: Afya Digital Supplies Limited · KES 46,400,000.00.', 'Funding needs resolution before award.', { strong: true }), source],
      pri: 'View report', sec: ['Committee record'], note: 'Independent branch. No automatic failure or cancellation.' }),
    rec({ id: 'D03-TIE', g: G3, name: 'Record — equal evaluated totals (1024 × 768)', size: 'c', actor: 'grace', at: '16 Jun 2027, 10:00 EAT', spec: '§9.4',
      title: 'Supply and delivery of office laptops', desc: 'TND-MOH-2027-036', crumb: ['Bid evaluation', 'TND-MOH-2027-036'],
      tr: T('dcn', 'Grace Wambui'), nx: { k: 'turn', h: 'Record the equal-price outcome in the report.' },
      blocks: [tb(['Bidder', 'Eligibility', 'Technical', 'Submitted total', 'Adjustments', 'Evaluated total', 'Position'], [
        [AF, 'Meets', 'Meets', KES, 'None', KES, '1'],
        ['Jirani Office Supplies Limited', 'Meets', 'Meets', KES, 'None', KES, '1']], { title: 'Bid comparison' }),
        at('No single recommendation — equal evaluated totals.', 'The published tender has no tie-break rule.', { strong: true })],
      pri: 'View report', note: 'Separate illustrative tender with its own opening. No Select winner or Negotiate.' })
  );

  const d4 = (o) => E.recHead(Object.assign({ g: G4, arch: 'Review or decision', state: 'Reviewing', spec: '§9.5', title: AF, desc: 'Compare the offered response with the published requirement.', crumb: ['Bid evaluation', TN, AF], back: 'Back to evaluation', tr: T('dcn', 'Peter Mugo'), actor: 'peter' }, o));
  const filt = (v) => E.fb([['Show', v, { select: true }]]);
  const reqCols = ['Requirement', 'Required', 'Offered', 'Result', 'Reason'];
  const slRow = ['Service location', 'Within Kenya', 'Nairobi service centre', 'Needs review', 'The submitted evidence does not clearly identify the service address.'];
  const d4Blocks = [filt('Needs review'), tb(reqCols, [slRow]), ev([['Kenya service-centre details']]),
    sg('Your finding', ['Meets', 'Does not meet', 'Needs review'], 2), fi('Reason', 'Clarify where the submitted evidence identifies the Nairobi service centre.', { area: true, req: true, rows: 2 }),
    ds('Finding history', 'Automatic check: offered location names Nairobi; supporting evidence requires review.')];
  E.add(
    d4({ id: 'D04', name: 'Service-location evidence', at: '14 Jun 2027, 08:45 EAT', nx: { k: 'turn', h: 'Review the evidence for the service location.' },
      blocks: d4Blocks, pri: 'Save finding', sec: ['Raise concern'],
      note: 'Filter choices: All checks, Needs review, Does not meet, Meets, Not applicable, Automatic checks.' }),
    d4({ id: 'D04-AUTO', name: 'Automatic checks', at: '14 Jun 2027, 08:40 EAT', nx: { k: 'turn', h: 'Review the results and raise a concern if needed.' },
      blocks: [filt('Automatic checks'), tb(reqCols, [
        ['Memory', 'Minimum 16 GB', '16 GB', 'Meets', 'Offered memory meets the minimum'],
        ['Storage capacity', 'Minimum 512 GB', '512 GB', 'Meets', 'Offered storage meets the minimum'],
        ['Warranty', 'Minimum 36 months', '36 months', 'Meets', 'Offered warranty meets the minimum']],
        { caption: 'These results compare the submitted values. Supporting evidence is reviewed separately.' }),
        ev([['Product datasheet'], ['Warranty and support commitment']])],
      pri: 'Raise concern', note: 'No editable result, no requirement count.' }),
    d4({ id: 'D04-FAIL', name: 'Mandatory failure (8 GB branch)', at: '14 Jun 2027, 08:40 EAT', nx: { k: 'turn', h: 'Review the results and raise a concern if needed.' },
      blocks: [filt('All checks'), tb(reqCols, [
        ['Memory', 'Minimum 16 GB', '8 GB', 'Does not meet', '8 GB is below the required 16 GB.'],
        ['Storage capacity', 'Minimum 512 GB', '512 GB', 'Meets', 'Offered storage meets the minimum'],
        ['Warranty', 'Minimum 36 months', '36 months', 'Meets', 'Offered warranty meets the minimum']]),
        tb(['Submitted total', 'Evaluated total', 'Position'], [[KES, 'Not assessed — mandatory requirement not met', 'Not ranked']], { title: 'Financial assessment', sec: true, caption: 'The submitted total is shown as a source fact.' })],
      pri: 'Raise concern', note: 'Isolated source branch. No Change offer. Remaining checks meet. Report outcome: No responsive bids (D07-NO-RESPONSIVE). The next-step headline reuses D04-AUTO copy; the brief gives none for this branch.' }),
    d4({ id: 'D04-CONCERN', name: 'Concern dialog', at: '14 Jun 2027, 08:45 EAT', nx: { k: 'turn', h: 'Review the evidence for the service location.' },
      blocks: d4Blocks, pri: 'Save finding', sec: ['Raise concern'],
      dlg: { t: 'Raise an evaluation concern', blocks: [kv([['Requirement', 'Service location — Within Kenya']]), fi('Reason', 'The datasheet and offered response need to be compared.', { area: true, req: true, rows: 3 })], pri: 'Record concern' } })
  );

  const att = (g, pe, r, b) => E.attend([['Grace Wambui', 'Chair', g], ['Peter Mugo', 'Member', pe], ['Ruth Achieng', 'Member', r], ['Brian Wafula', 'Secretary', b]]);
  const full = att('Joined 09:00', 'Joined 09:02', 'Joined 09:03', 'Present 09:00');
  const subject = f(['Subject', 'Afya service-location evidence'], ['Requirement', 'Within Kenya'], ['Response', 'Nairobi service centre']);
  const evd = ev([['Kenya service-centre details']]);
  const NOTE = 'Ask the bidder to identify the service address already recorded in its submitted evidence.';
  const REASON = 'The offered location meets the stated country requirement, but the supporting document is unclear.';
  const d5 = (o) => E.recHead(Object.assign({ g: G5, arch: 'Form or editor', state: 'Reviewing', spec: '§9.6', title: 'Committee discussion', desc: TN + ' · 14 Jun 2027' }, o));
  const earlier = ds('Earlier discussion', 'Discussion started by Grace Wambui, 14 Jun 2027, 09:00 EAT.');

  E.add(
    d5({ id: 'D05', name: 'Discussion — secretary records note', actor: 'brian', at: '14 Jun 2027, 09:04 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Record the discussion for the chair.' },
      blocks: [full, subject, evd, fi('Discussion note', NOTE, { area: true, rows: 2 }), fi('Reason', REASON, { area: true, rows: 2 }), earlier],
      pri: 'Save discussion note', note: 'The note does not show an authorised clarification. No transcript or voting controls.' }),
    d5({ id: 'D05-CHAIR', name: 'Discussion — chair authorises clarification', actor: 'grace', at: '14 Jun 2027, 09:05 EAT', tr: T('dcn', 'Grace Wambui'),
      nx: { k: 'turn', h: 'Authorise the agreed written clarification.' },
      blocks: [full, subject, kv([['Discussion note', NOTE], ['Reason', REASON]], { title: 'Proposed conclusion', sec: true }),
        fi('Question', E.Q1, { area: true, req: true, rows: 2 }), fi('Reply deadline', '15 Jun 2027, 17:00 EAT', { req: true }), fi('Scope', E.SCOPE, { area: true, req: true, rows: 2 })],
      pri: 'Authorise clarification', sec: ['End discussion'] }),
    d5({ id: 'D05-START', name: 'Discussion started — waiting for members', actor: 'grace', at: '14 Jun 2027, 09:00 EAT', tr: T('dcn', 'Peter Mugo, Ruth Achieng'),
      nx: { k: 'wait', h: 'Waiting for Peter Mugo and Ruth Achieng to join the discussion.' },
      blocks: [att('Joined 09:00', 'Not joined', 'Not joined', 'Present 09:00'), subject, evd],
      sec: ['Leave discussion', 'End discussion'], note: 'No conclusion fields, no Join discussion for Grace.' }),
    d5({ id: 'D05-JOIN', name: 'Member joins', actor: 'ruth', at: '14 Jun 2027, 09:02:30 EAT', tr: T('dcn', 'Ruth Achieng'),
      nx: { k: 'turn', h: 'Join the committee discussion.' },
      blocks: [att('Joined 09:00', 'Joined 09:02', 'Not joined', 'Present 09:00'), subject, evd], pri: 'Join discussion' }),
    d5({ id: 'D05-MEMBER', name: 'Member reviews recorded conclusion', actor: 'ruth', at: '14 Jun 2027, 09:05:30 EAT', tr: T('dcn', 'Ruth Achieng'),
      nx: { k: 'turn', h: 'Review the recorded conclusion and add any disagreement.' },
      blocks: [full, subject, kv([['Conclusion', 'Clarification authorised by Grace Wambui, 09:05'], ['Question', E.Q1], ['Reason', REASON]], { title: 'Recorded conclusion', sec: true })],
      pri: 'Record disagreement', sec: ['Leave discussion'] }),
    d5({ id: 'D05-DISAGREE', name: 'Disagreement dialog', actor: 'ruth', at: '14 Jun 2027, 09:05:30 EAT', tr: T('dcn', 'Ruth Achieng'),
      nx: { k: 'turn', h: 'Review the recorded conclusion and add any disagreement.' },
      blocks: [full, subject], pri: 'Record disagreement', sec: ['Leave discussion'],
      dlg: { t: 'Record disagreement', blocks: [fi('Your disagreement', 'The address should be verified against the original document before the finding is closed.', { area: true, req: true, rows: 3 })], pri: 'Save disagreement' },
      note: 'Used only in this variant; Ruth does not disagree in the ordinary scenario.' }),
    d5({ id: 'D05-ABSENT', name: 'Member absent — conclusions paused', actor: 'brian', at: '14 Jun 2027, 09:04 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Record notes while the committee waits for Ruth Achieng.' },
      blocks: [n('warning', 'All members of the current eligible committee must be present to record this conclusion.', 'Ruth Achieng must rejoin.'),
        subject, evd, fi('Discussion note', NOTE, { area: true, rows: 2 }),
        ds('View attendance', ['Grace Wambui joined 09:00', 'Peter Mugo joined 09:02', 'Ruth Achieng joined 09:03, left 09:03:30', 'Brian Wafula present from 09:00'])],
      pri: 'Save discussion note', note: 'Independent branch. Chair variant offers End discussion; Ruth’s view offers Join discussion. Collective decision controls absent.' }),
    d5({ id: 'D05-CONCLUSION', name: 'Record conclusion — resolved', actor: 'grace', at: '14 Jun 2027, 09:05 EAT', spec: '§9.13', tr: T('dcn', 'Grace Wambui'),
      nx: { k: 'turn', h: 'Record the committee’s conclusion.' },
      blocks: [full, f(['Subject', 'Resolve service-location concern'], ['Requirement', 'Within Kenya'], ['Offered', 'Nairobi service centre']), evd,
        sg('Result', ['Meets', 'Does not meet', 'Needs review'], 0), fi('Reason', 'Page 2, section 3 of the original document identifies the Nairobi service address.', { area: true, req: true, rows: 2 })],
      pri: 'Record conclusion', sec: ['End discussion'], note: 'Independent branch; no clarification sent. Next-step headline is new copy (not in brief) — please confirm.' }),
    d5({ id: 'D05-CONCLUSION-Q', name: 'Record conclusion — qualified report', actor: 'grace', at: '14 Jun 2027, 09:05 EAT', spec: '§9.13', tr: T('dcn', 'Grace Wambui'),
      nx: { k: 'turn', h: 'Record the committee’s conclusion.' },
      blocks: [full, f(['Subject', 'Resolve service-location concern'], ['Requirement', 'Within Kenya'], ['Offered', 'Nairobi service centre']), evd,
        sg('Result', ['Meets', 'Does not meet', 'Needs review'], 2), f(['Outcome', 'Qualified report']), fi('Reason', 'The committee cannot establish the address from the submitted evidence.', { area: true, req: true, rows: 2 })],
      pri: 'Record conclusion', sec: ['End discussion'] })
  );

  const rtab = (o) => E.recHead(Object.assign({ g: G5, arch: 'Record detail', state: 'Reviewing', spec: '§9.12', title: 'Committee record', tabs: ['Results', 'Committee record'], tab: 1, tr: T('dcn', 'Brian Wafula'), at: '16 Jun 2027, 13:55 EAT' }, o));
  const recordBlocks = [E.roster(),
    tb(['Session', 'Time', 'Subject', 'Attendance'], [
      ['14 Jun 2027', '09:00–09:06', 'Clarify service address', 'Grace 09:00 (Start discussion) · Peter 09:02 · Ruth 09:03 · Brian from start'],
      ['16 Jun 2027', '09:00–09:06', 'Resolve reply and complete findings', 'Grace 09:00 (Start discussion) · Peter 09:02 · Ruth 09:03 · Brian from start']], { title: 'Sessions', sec: true }),
    kv([['Question', E.Q1], ['Sent', '14 Jun 2027, 09:10 EAT'], ['Reply deadline', '15 Jun 2027, 17:00 EAT'], ['Reply', 'Received from David Ouma, 15 Jun 2027, 10:00 EAT'], ['Committee outcome', '16 Jun 2027, 09:05 — The address is present in the original submitted document and is within Kenya.']], { title: 'Clarification', sec: true }),
    p('No disagreement recorded', { strong: true }),
    ds('Appointment and declaration history', ['Committee appointed by Amina Hassan, 11 Jun 2027, 09:00 EAT · MOH/EVAL/033/2027', 'Secretary Brian Wafula appointed by Charles Mutiso, 11 Jun 2027, 09:05 EAT · MOH/EVAL/SEC/033/2027', 'Declarations: Grace 09:10, Peter 09:12, Ruth 09:14 on 11 Jun — no conflict, confidentiality accepted'])];
  E.add(
    rtab({ id: 'D05-RECORD', name: 'Committee record — secretary', actor: 'brian', nx: { k: 'turn', h: 'Prepare the report from the completed committee record.' }, blocks: recordBlocks, pri: 'View report', sec: ['Back to evaluation'] }),
    rtab({ id: 'D05-RECORD-MEMBER', name: 'Committee record — member', actor: 'grace', nx: { k: 'turn', h: 'Review the completed committee record.' }, blocks: recordBlocks, pri: 'View report' }),
    rtab({ id: 'D05-RECORD-AUDITOR', name: 'Committee record — auditor', actor: 'naomi', notInvolved: ' ', blocks: recordBlocks, note: 'Not involved: no headline or holder; read-only.' })
  );
});
