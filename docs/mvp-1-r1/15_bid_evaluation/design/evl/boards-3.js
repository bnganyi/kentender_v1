(window.EVL_Q = window.EVL_Q || []).push(function (E) {
  const { p, f, kv, tb, n, fi, ra, sg, ds, at, lk, ev, T, TN, TT, AF, KES } = E;
  const G6 = 'D06 Clarification', G7 = 'D07 Report and signing', GS = 'Shared page states';
  const sup = (o) => Object.assign({ g: G6, size: 'm', actor: 'david', org: AF, arch: 'Form or editor', spec: '§9.7', title: 'Reply to clarification', desc: TN + ' · ' + TT, crumb: [] }, o);
  const qkv = (sent) => kv([['Question', E.Q1], ['Scope', E.SCOPE], ['Sent', sent || '14 Jun 2027, 09:10 EAT'], ['Reply by', '15 Jun 2027, 17:00 EAT']], { title: 'Committee question', sec: true });
  const replyForm = [f(['Organisation', AF]), qkv(), fi('Your reply', E.REPLY, { area: true, req: true, rows: 4 }), fi('Supporting explanation', '', { file: true, help: 'Attach only evidence explaining this question. Your submitted bid will not change.' })];
  const intl = (o) => E.recHead(Object.assign({ g: G6, arch: 'Review or decision', state: 'Reviewing', spec: '§9.7' }, o));
  const sentKv = kv([['Question', E.Q1], ['Scope', E.SCOPE], ['Reply deadline', '15 Jun 2027, 17:00 EAT'], ['Authorised', 'Grace Wambui, 14 Jun 2027, 09:05 EAT'], ['Recipient', 'David Ouma · david.ouma@afyadigital.example']], { title: 'Clarification request', sec: true });
  const Q2 = 'In the document titled Kenya service-centre details submitted with your bid, identify the page and section containing the Nairobi service address. Refer only to the original submitted document.';
  const outcome = (id, name, extra, sel, reason, note) => intl({ id, name, title: 'Service-location clarification', actor: 'grace', at: '16 Jun 2027, 09:04 EAT', tr: T('dcn', 'Grace Wambui'),
    nx: { k: 'turn', h: 'Record how the reply affects the service-location finding.' },
    blocks: [kv([['Question', E.Q1], ['Reply deadline', '15 Jun 2027, 17:00 EAT']], { title: 'Committee question', sec: true })].concat(extra, [
      sg('Result', ['Meets', 'Does not meet', 'Needs review'], sel), fi('Reason', reason, { area: true, req: true, rows: 2 })]),
    pri: 'Record reply outcome', note: note || 'Board title is new copy (the brief names none).' });

  E.add(
    intl({ id: 'D06-SEND', name: 'Send clarification', title: 'Send clarification', actor: 'brian', at: '14 Jun 2027, 09:09 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Send the committee\'s question to Afya Digital Supplies Limited.' }, blocks: [sentKv], pri: 'Send clarification', sec: ['Back to evaluation'], note: 'No editable question or deadline.' }),
    sup({ id: 'D06-SUPPLIER', name: 'Supplier reply (390)', at: '15 Jun 2027, 09:55 EAT', nx: { k: 'turn', h: 'Reply by 15 Jun 2027, 17:00 EAT.' }, blocks: replyForm, pri: 'Send reply', sec: ['Save draft', 'Back to bid'] }),
    sup({ id: 'D06-RECEIVED', name: 'Supplier reply received (390)', at: '15 Jun 2027, 10:00 EAT', nx: { k: 'done', h: 'Your reply has been received for committee review.' },
      blocks: [qkv(), kv([['Your reply', E.REPLY], ['Reply received', '15 Jun 2027, 10:00 EAT']], { title: 'Your reply', sec: true })], sec: ['Back to bid'] }),
    intl({ id: 'D06-DELIVERY', name: 'Notice delivery problem', title: 'Send clarification', actor: 'brian', at: '14 Jun 2027, 09:11 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Retry the clarification notice.' },
      blocks: [n('warning', 'The clarification notice could not be delivered.', 'The question is available in the supplier’s bid workspace.'), sentKv],
      pri: 'Retry notice', sec: ['Back to evaluation'], note: 'Sent request read-only. No false Delivered badge.' }),
    sup({ id: 'D06-LATE', name: 'Late reply (390)', at: '15 Jun 2027, 17:05 EAT', nx: { k: 'turn', h: 'The reply deadline has passed.', s: 'You can send a late reply; the committee will decide whether it can be considered.' },
      blocks: replyForm, pri: 'Send late reply', sec: ['Save draft', 'Back to bid'] }),
    sup({ id: 'D06-LATE-RECEIVED', name: 'Late reply receipt (390)', at: '15 Jun 2027, 17:06 EAT', nx: { k: 'done', h: 'Your reply has been received for committee review.' },
      blocks: [qkv(), kv([['Your reply', E.REPLY], ['Received', 'Received late, 15 Jun 2027, 17:06 EAT']], { title: 'Your reply', sec: true })], sec: ['Back to bid'], note: 'No promise of acceptance.' }),
    sup({ id: 'D06-CLOSED', name: 'Withdrawn and replaced (390)', at: '15 Jun 2027, 09:55 EAT', nx: { k: 'done', h: 'This clarification has been withdrawn.' },
      blocks: [qkv(), f(['Reason', 'Request withdrawn: question replaced to clarify the document reference.']), fi('Your unsent draft', E.REPLY, { area: true, rows: 3 }),
        kv([['Question', Q2], ['Scope', E.SCOPE], ['Sent', '15 Jun 2027, 09:50 EAT'], ['Reply by', '16 Jun 2027, 17:00 EAT']], { title: 'New question', sec: true }), lk(['View new question'])],
      sec: ['Back to bid'], note: 'Independent branch: Grace authorises the replacement 09:45, Brian withdraws the original 09:46 and sends the new one 09:50. The unsent draft text is assumed to match the ordinary reply.' }),
    outcome('D06-OUTCOME', 'Record reply outcome', [kv([['Reply', E.REPLY], ['Received', '15 Jun 2027, 10:00 EAT'], ['Evidence', 'Kenya service-centre details, page 2, section 3']], { title: 'Supplier reply', sec: true })], 0, 'The address is present in the original submitted document and is within Kenya.'),
    outcome('D06-NO-REPLY', 'Outcome — no reply', [f(['Reply', 'No reply received'], ['Status', 'Reply overdue'])], 2, 'No reply was received; assess the original evidence.'),
    intl({ id: 'D06-LATE-REVIEW', name: 'Outcome — late reply not considered', title: 'Service-location clarification', actor: 'grace', at: '16 Jun 2027, 09:04 EAT', tr: T('dcn', 'Grace Wambui'),
      nx: { k: 'turn', h: 'Record how the reply affects the service-location finding.' },
      blocks: [kv([['Question', E.Q1], ['Reply deadline', '15 Jun 2027, 17:00 EAT'], ['Reply', E.REPLY], ['Received', 'Received late, 15 Jun 2027, 17:06 EAT']], { title: 'Committee question and reply', sec: true }),
        fi('Disposition', 'Not considered', { select: true, req: true }), fi('Reason', 'The reply was received after the stated deadline; the original evidence is sufficient for this finding.', { area: true, req: true, rows: 2 })],
      pri: 'Record reply outcome' }),
    intl({ id: 'D06-CHANGED-OFFER', name: 'Outcome — attempted offer change', title: 'Service-location clarification', actor: 'grace', at: '16 Jun 2027, 09:04 EAT', tr: T('dcn', 'Grace Wambui'),
      nx: { k: 'turn', h: 'Record how the reply affects the service-location finding.' },
      blocks: [kv([['Question', E.Q1], ['Reply', 'We now offer an 8-hour support response instead of 4 hours'], ['Submitted commitment', '4-hour support response (unchanged)']], { title: 'Committee question and reply', sec: true }),
        fi('Disposition', 'Excluded change', { select: true, req: true }), fi('Reason', 'The reply changes the submitted offer.', { area: true, req: true, rows: 2 })],
      pri: 'Record reply outcome', note: 'Separate branch. The original response does not change.' }),
    intl({ id: 'D06-WITHDRAW', name: 'Withdraw for replacement', title: 'Clarification request', actor: 'brian', at: '15 Jun 2027, 09:46 EAT', spec: '§9.11', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Withdraw the question authorised for replacement.' },
      blocks: [sentKv, f(['Chair\'s recorded reason', 'Clarify the document reference.'])], pri: 'Withdraw clarification', note: 'Replacement branch authorised by Grace at 09:45.' }),
    intl({ id: 'D06-WITHDRAW-DLG', name: 'Withdraw dialog', title: 'Clarification request', actor: 'brian', at: '15 Jun 2027, 09:46 EAT', spec: '§9.11', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Withdraw the question authorised for replacement.' },
      blocks: [sentKv], pri: 'Withdraw clarification',
      dlg: { t: 'Withdraw this clarification?', blocks: [fi('Reason', 'Clarify the document reference.', { area: true, req: true, rows: 2 })], pri: 'Withdraw clarification' } }),
    sup({ id: 'D06-FINAL-CLOSED', name: 'Closed after disposition (390)', at: '16 Jun 2027, 09:06 EAT', spec: '§9.11', nx: { k: 'done', h: 'This clarification is closed.' },
      blocks: [qkv(), kv([['Your reply', E.REPLY], ['Reply received', '15 Jun 2027, 10:00 EAT'], ['Closed', '16 Jun 2027, 09:05 EAT']], { title: 'Your reply', sec: true })], sec: ['Back to bid'] }),
    sup({ id: 'D06-FINAL-CLOSED-NR', name: 'Closed, draft unsent (390)', at: '16 Jun 2027, 09:06 EAT', spec: '§9.11', nx: { k: 'done', h: 'This clarification is closed.' },
      blocks: [qkv(), f(['Closed', '16 Jun 2027, 09:05 EAT']), fi('Your unsent draft', E.REPLY, { area: true, rows: 3 })], sec: ['Back to bid'], note: 'No-reply branch: the draft stays private; no write actions.' })
  );

  const rep = (o) => E.recHead(Object.assign({ g: G7, arch: 'Form or editor', state: 'Reviewing', spec: '§9.8', title: 'Evaluation report', desc: TN + ' · Draft report 1', crumb: ['Bid evaluation', TN, 'Report'] }, o));
  const SUMMARY_TXT = 'The only bid received meets the published requirements. The submitted service-location evidence was clarified without changing the offer.';
  const draftBlocks = [E.summary(), E.sections(), fi('Committee summary', SUMMARY_TXT, { area: true, rows: 3 }), ds('Report history', 'No earlier report.')];
  const draftAct = { pri: 'Send for signing', sec: ['Save draft', 'Preview report'], cons: 'Each member will review and sign this exact report. Changes will require a new version.' };
  const signBlocks = (g, pe, r) => [E.summary(), E.sections(), E.sigs(g, pe, r)];
  const INTENT = 'I have reviewed this report. It accurately records my findings and any disagreement I have recorded.';
  const signBoard = (o) => rep(Object.assign({ arch: 'Review or decision', state: 'Signing', title: 'Evaluation report 1', desc: TN, actor: 'peter', at: '16 Jun 2027, 14:05:45 EAT', tr: T('ddc', 'Peter Mugo, Ruth Achieng'),
    nx: { k: 'turn', h: 'Review and sign the evaluation report.' },
    blocks: signBlocks('Signed 14:05', 'Your signature needed', 'Awaiting signature').concat([p(INTENT)]), pri: 'Sign report', sec: ['Raise a concern', 'Download report'] }, o));
  const sentBlocks = [E.summary(), E.sections(), E.sigs('Signed 14:05', 'Signed 14:06', 'Signed 14:07'), f(['Current report', 'Report 1'])];

  E.add(
    rep(Object.assign({ id: 'D07-DRAFT', name: 'Draft report', actor: 'brian', at: '16 Jun 2027, 13:55 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Check the report and send it to members for signing.' }, blocks: draftBlocks }, draftAct)),
    signBoard({ id: 'D07-SIGN', name: 'Member signs report' }),
    signBoard({ id: 'D07-WAIT', name: 'Signed — waiting for others', actor: 'grace', nx: { k: 'wait', h: 'Waiting for Peter Mugo and Ruth Achieng to sign report 1.', s: 'Since 16 Jun, 14:05.' },
      blocks: signBlocks('Signed 14:05', 'Awaiting signature', 'Awaiting signature'), pri: null, sec: ['Raise a concern', 'Download report'] }),
    signBoard({ id: 'D07-CONCERN', name: 'Report concern dialog', note: 'Independent branch in which report 1 incorrectly states page 3.',
      dlg: { t: 'Raise a concern', blocks: [fi('What needs correction?', 'The report refers to page 3; the service address is on page 2.', { area: true, req: true, rows: 3 })], cons: 'The report will return for correction. All members will need to sign the new version.', pri: 'Send concern' } }),
    rep({ id: 'D07-SENT', name: 'Report sent', arch: 'Record detail', state: 'Report sent', title: 'Evaluation report 1', desc: TN, actor: 'grace', at: '16 Jun 2027, 14:08 EAT', tr: T('ddd'),
      nx: { k: 'done', h: 'The committee report was sent to Charles Mutiso on 16 Jun 2027, 14:07 EAT.', s: 'The Head of Procurement will review the report. No award decision has been recorded here.' },
      blocks: sentBlocks, sec: ['Download report', 'View committee record'], note: 'No Complete button.' }),
    rep({ id: 'D07-HOP', name: 'Head of Procurement receives report', arch: 'Review or decision', state: 'Report sent', title: 'Evaluation report 1', desc: TN, actor: 'charles', at: '16 Jun 2027, 14:08 EAT', tr: T('ddd'),
      nx: { k: 'turn', h: 'Review the committee\'s report.' }, blocks: sentBlocks.slice(0, 3), pri: 'Open report', sec: ['Return for correction'],
      note: 'Evaluation tracker ends at delivery; Charles’s review is downstream. No Professional opinion form or Award button.' }),
    rep({ id: 'D07-HOP-RETURN', name: 'Return for correction dialog', arch: 'Review or decision', state: 'Report sent', title: 'Evaluation report 1', desc: TN, actor: 'charles', at: '16 Jun 2027, 14:08 EAT', tr: T('ddd'),
      nx: { k: 'turn', h: 'Review the committee\'s report.' }, blocks: sentBlocks.slice(0, 3), pri: 'Open report', sec: ['Return for correction'],
      dlg: { t: 'Return for correction', blocks: [kv([['Downstream status', 'No award decision recorded · checked 16 Jun 2027, 14:08 EAT']]), fi('Reason', 'Correct the service-address page reference from page 3 to page 2.', { area: true, req: true, rows: 2 })], pri: 'Return report' },
      note: 'Separate branch in which report 1 contains an incorrect page-3 reference.' }),
    rep(Object.assign({ id: 'D07-RETURNED', name: 'Returned — draft report 2', desc: TN + ' · Draft report 2', actor: 'brian', at: '16 Jun 2027, 15:00 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Correct the report returned by Charles Mutiso.' },
      blocks: [at('Correct the service-address page reference from page 3 to page 2.', 'Returned by Charles Mutiso'), E.summary(), E.sections(), fi('Committee summary', SUMMARY_TXT, { area: true, rows: 3 }), ds('Report history', 'Report 1 · Returned', { open: true })] }, draftAct)),
    rep(Object.assign({ id: 'D07-NO-RESPONSIVE', name: 'Outcome — no responsive bids', actor: 'brian', at: '16 Jun 2027, 13:55 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Check the report and send it to members for signing.' },
      blocks: [kv([['Recommendation', 'No responsive bids'], ['Reason', 'The offered 8 GB memory is below the required 16 GB.'], ['Eligibility', 'Meets'], ['Technical compliance', 'Does not meet']], { title: 'Summary' }),
        tb(['Submitted total', 'Evaluation adjustments', 'Evaluated total', 'Position'], [[KES, 'Not assessed — mandatory requirement not met', 'Not assessed — mandatory requirement not met', 'Not ranked']], { title: 'Financial comparison', sec: true, caption: 'The submitted total is a source fact, not a recommended amount.' }),
        E.sections(), fi('Committee summary', '', { area: true, rows: 3 })], note: 'Uses the D04-FAIL branch. The committee-summary value is left empty; the brief gives no text.' }, draftAct)),
    rep(Object.assign({ id: 'D07-NO-AGREEMENT', name: 'Outcome — no agreed recommendation', actor: 'brian', at: '16 Jun 2027, 13:55 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Check the report and send it to members for signing.' },
      blocks: [kv([['Recommendation', 'No agreed recommendation']], { title: 'Summary' }),
        tb(['Member', 'Recorded position'], [['Grace Wambui and Peter Mugo', 'The submitted address supports the country requirement.'], ['Ruth Achieng', 'I cannot establish that the submitted evidence supports the stated service location.']], { title: 'Attributed positions', sec: true, caption: 'These positions remain unresolved. No majority decision is inferred.' }),
        E.sections()], note: 'Separate dissent branch. Can be signed as an accurate report.' }, draftAct)),
    signBoard({ id: 'D07-REVISE', name: 'Secretary revises during signing', spec: '§9.11', actor: 'brian', at: '16 Jun 2027, 14:05:30 EAT', tr: T('ddc', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Correct the report before collecting further signatures.' }, blocks: signBlocks('Signed 14:05', 'Awaiting signature', 'Awaiting signature'), pri: 'Revise report', sec: [] }),
    signBoard({ id: 'D07-REVISE-DLG', name: 'Revise report dialog', spec: '§9.11', actor: 'brian', at: '16 Jun 2027, 14:05:30 EAT', tr: T('ddc', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Correct the report before collecting further signatures.' }, blocks: signBlocks('Signed 14:05', 'Awaiting signature', 'Awaiting signature'), pri: 'Revise report', sec: [],
      dlg: { t: 'Revise report', blocks: [fi('Reason', 'Correct the service-address page reference.', { area: true, req: true, rows: 2 })], cons: 'A new report will need all members\' signatures.', pri: 'Revise report' } }),
    signBoard({ id: 'D07-DELIVERY', name: 'Signed report not delivered', spec: '§9.11', actor: 'brian', at: '16 Jun 2027, 14:07:30 EAT', tr: T('ddc', 'Brian Wafula'),
      nx: { k: 'turn', h: 'The signed report could not be delivered.', s: 'Recipient: Charles Mutiso.' }, blocks: signBlocks('Signed 14:05', 'Signed 14:06', 'Signed 14:07'),
      pri: 'Retry delivery', sec: ['Report issue', 'Download report'], note: 'Still Signing. Do not show Report sent or a recipient task.' }),
    rep({ id: 'D07-OVERDUE', name: 'Evaluation overdue', spec: '§9.11', arch: 'Review or decision', actor: 'grace', at: '13 Jul 2027, 09:00 EAT', tr: T('dcn', 'Grace Wambui'),
      nx: { k: 'turn', h: 'Review the overdue evaluation and complete its report.' },
      blocks: [n('warning', 'The evaluation deadline has passed.'), f(['Evaluation deadline', '12 Jul 2027, 11:00 EAT'], ['Tender validity', 'Tender validity has not expired.']), E.summary(), E.sections()],
      pri: 'View report', note: 'Secretary variant keeps Send for signing. No cancellation or automatic extension.' }),
    rep(Object.assign({ id: 'D07-EXPIRED', name: 'Tender validity expired', spec: '§9.11', actor: 'brian', at: '12 Oct 2027, 09:00 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Record the expired tender validity in the report.' },
      blocks: [n('warning', 'Tender validity ended 10 Oct 2027, 11:00 EAT; no extension recorded.'), kv([['Outcome', 'No current recommendation — tender validity expired.']], { title: 'Summary' }), E.sections()],
      note: 'No Extend validity control.' }, draftAct)),
    signBoard({ id: 'D07-EXPIRED-SIGN', name: 'Expired-validity report — signing', spec: '§9.11', at: '12 Oct 2027, 09:10:30 EAT',
      blocks: [n('warning', 'Tender validity ended 10 Oct 2027, 11:00 EAT; no extension recorded.'), kv([['Outcome', 'No current recommendation — tender validity expired.']], { title: 'Summary' }), E.sections(), E.sigs('Signed 09:10', 'Your signature needed', 'Awaiting signature'), p(INTENT)] }),
    rep({ id: 'D07-EXPIRED-SENT', name: 'Expired-validity report — sent', spec: '§9.11', arch: 'Record detail', state: 'Report sent', title: 'Evaluation report 1', desc: TN, actor: 'grace', at: '12 Oct 2027, 09:13 EAT', tr: T('ddd'),
      nx: { k: 'done', h: 'The committee report was sent to Charles Mutiso on 12 Oct 2027, 09:12 EAT.', s: 'The Head of Procurement will review the report. No award decision has been recorded here.' },
      blocks: [n('warning', 'Tender validity ended 10 Oct 2027, 11:00 EAT; no extension recorded.'), kv([['Outcome', 'No current recommendation — tender validity expired.']], { title: 'Summary' }), E.sigs('Signed 09:10', 'Signed 09:11', 'Signed 09:12')],
      sec: ['Download report', 'View committee record'], note: 'The brief states delivery follows Ruth’s 09:12 signature; the 09:12 delivery and 09:13 viewing times are assumed.' }),
    rep({ id: 'D07-INCOMPLETE', name: 'Report blocked by open issue', spec: '§9.13', actor: 'brian', at: '16 Jun 2027, 13:55 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Open the unresolved issue before sending the report for signing.' },
      blocks: [n('warning', 'Review the listed issues before sending the report for signing.'), tb(['Open issue', 'Holder'], [['Service location — Needs review; no committee disposition', 'Grace Wambui']], { title: 'Unresolved', sec: true }), E.sections()],
      pri: 'Open issue', sec: ['~Send for signing', 'Save draft', 'Preview report'], note: 'No report frozen; no signature task.' }),
    rep({ id: 'D07-DECISION-UNKNOWN', name: 'Downstream status unknown', spec: '§9.13', arch: 'Review or decision', state: 'Report sent', title: 'Evaluation report 1', desc: TN, actor: 'charles', at: '17 Jun 2027, 10:00 EAT', tr: T('ddd'),
      nx: { k: 'turn', h: 'Report the unavailable decision status.' },
      blocks: [n('warning', 'The later decision could not be checked.', 'Report 1 remains unchanged. A return cannot proceed until the later decision is known.'), E.summary(), E.sections()],
      pri: 'Report issue', sec: ['Open report', '~Return for correction'], note: 'Grace’s view also offers Send correction notice, opening the existing correction form.' }),
    rep(Object.assign({ id: 'D07-TIE', name: 'Outcome — tie (tender 036)', spec: '§9.13', desc: 'TND-MOH-2027-036 · Draft report 1', crumb: ['Bid evaluation', 'TND-MOH-2027-036', 'Report'], actor: 'brian', at: '16 Jun 2027, 13:55 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Check the report and send it to members for signing.' },
      blocks: [kv([['Outcome', 'No single recommendation — equal evaluated totals'], ['Reason', 'The published tender has no tie-break rule.']], { title: 'Summary' }),
        tb(['Bidder', 'Submitted total', 'Adjustments', 'Evaluated total', 'Position'], [[AF, KES, 'None', KES, '1'], ['Jirani Office Supplies Limited', KES, 'None', KES, '1']], { title: 'Financial comparison', sec: true }), E.sections()],
      note: 'No bidder is recommended over the other.' }, draftAct)),
    rep(Object.assign({ id: 'D07-FUNDING', name: 'Outcome — funding qualification', spec: '§9.13', actor: 'brian', at: '16 Jun 2027, 13:55 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Check the report and send it to members for signing.' },
      blocks: [kv([['Recommendation', 'Afya Digital Supplies Limited'], ['Evaluated total', KES], ['Available funding', 'KES 45,000,000.00'], ['Shortfall', 'KES 1,400,000.00'], ['Source', 'Budget confirmation, 16 Jun 2027, 09:50 EAT'], ['Qualification', 'Funding needs resolution before award.']], { title: 'Summary' }), E.sections()] }, draftAct))
  );

  // §9.12 report preview
  E.add(rep({ id: 'D07-PREVIEW', name: 'Report preview (§9.12 content)', spec: '§9.12', arch: 'Record detail', actor: 'brian', at: '16 Jun 2027, 13:55 EAT', tr: T('dcn', 'Brian Wafula'),
    blocks: [
      kv([['Tender', TN + ' · ' + TT], ['Lot and method', 'Single lot · Open Tender · Youth reservation'], ['Quantity', '250 Each'], ['Bid', 'BID-MOH-2027-033-001 · Submitted Version 1'], ['Opening', 'Completed 12 Jun 2027, 11:10:30 EAT'], ['Published requirements', 'Issued tender with addendum ADD-MOH-2027-033-001'], ['Supplier', AF + ' · one bid opened']], { title: 'Tender and committee' }),
      E.roster({ title: null }),
      tb(['Requirement', 'Offered or recorded evidence', 'Finding'], [
        ['Supplier identity', 'Certificate of incorporation PVT-9X7K2M; reviewed by Ruth, 14 Jun 08:45', 'Meets'],
        ['Required declarations', 'Tenderer information complete; Form of Tender, independent tender determination, not debarred, no corrupt or fraudulent practice and code of ethics confirmed; reviewed by Ruth, 14 Jun 08:45', 'Meets'],
        ['Youth reservation', 'Declaration complete; AGPO-Y-2026-04172, valid to 30 Jun 2027; required eligibility evidence reviewed by Ruth, 14 Jun 08:45', 'Meets'],
        ['Tax compliance', 'Tax compliance certificate P051234567X, valid to 31 Dec 2027; required evidence reviewed by Ruth, 14 Jun 08:45', 'Meets'],
        ['Tender security', 'KCB/TG/2027/8841, KES 500,000.00, valid to 15 Nov 2027; physical receipt MOH-SEC-2027-033-017; published security conditions and original reviewed by Ruth, 14 Jun 08:50', 'Meets']],
        { title: 'Bid findings — Eligibility', caption: 'Responsive means the bid meets the applicable mandatory requirements.' }),
      tb(['Requirement', 'Offered or recorded evidence', 'Finding'], [
        ['Quantity and delivery', '250 Each; 15 Sep 2027, before 30 Sep 2027; Ministry of Health Headquarters, Afya House, 3rd Floor Procurement Stores, Nairobi', 'Meets'],
        ['Electrical compatibility', '240 V, 50 Hz adaptor; suitable for Kenyan mains supply', 'Meets'],
        ['New and unused', 'All units new and unused; manufacturer authorisation', 'Meets'],
        ['Memory / storage', '16 GB, minimum 16 GB; 512 GB, minimum 512 GB; NVMe SSD as required', 'Meets'],
        ['Display / battery', '14.0 inches, minimum 14.0; 10 hours, minimum 8', 'Meets'],
        ['Processor', '64-bit business-class, 12 cores; requirement minimum 10 cores or equivalent', 'Meets'],
        ['Operating system', 'Windows 11 Pro compatible with the required organisational environment', 'Meets'],
        ['Connectivity / ports', 'Wi-Fi 6E and Bluetooth 5.3; USB-C ×2, USB-A ×2, HDMI ×1; published minimums satisfied', 'Meets'],
        ['Warranty / support', '36 months, minimum 36; on-site support Yes; response 4 hours, maximum 8; manufacturer support Yes', 'Meets'],
        ['Service location and contacts', 'Nairobi service centre; escalation/warranty contacts supplied; original address confirmed on page 2, section 3', 'Meets'],
        ['Comparable experience', 'Kenyatta National Hospital, 180 laptops, completed 30 Nov 2026; Kenya Medical Training College, 220 laptops, completed 15 Mar 2027; two submitted evidence records reviewed', 'Meets']],
        { title: 'Bid findings — Technical compliance', sec: true, caption: 'Required evidence reviewed by Peter at 14 Jun 08:50, except service location, resolved by the committee on 16 Jun 09:05.' }),
      lk(['Certificate of incorporation', 'Tax compliance certificate', 'Youth reservation evidence', 'Tender-security proof', 'Manufacturer authorisation', 'Product datasheet', 'Warranty and support commitment', 'Kenya service-centre details', 'KNH contract evidence', 'KMTC contract evidence'], { title: 'Supporting documents', sec: true }),
      tb(['Quantity', 'Unit price', 'Subtotal', 'VAT', 'Submitted total', 'Adjustments', 'Evaluated total', 'Position'], [['250 Each', 'KES 160,000.00', 'KES 40,000,000.00', 'KES 6,400,000.00', KES, 'None', KES, '1']], { title: 'Financial comparison', caption: 'One responsive bid; no evaluation adjustment.' }),
      kv([['Question', E.Q1], ['Sent', '14 Jun 2027, 09:10 EAT'], ['Deadline', '15 Jun 2027, 17:00 EAT'], ['Reply', 'David Ouma, received 15 Jun 2027, 10:00 EAT'], ['Committee outcome', '16 Jun 2027, 09:05 — The address is present in the original submitted document and is within Kenya.'], ['Sessions', '14 Jun 09:00–09:06, clarify service address; 16 Jun 09:00–09:06, resolve reply and complete findings. Grace 09:00 (Start discussion), Peter 09:02, Ruth 09:03, Brian present from start.'], ['Disagreement', 'No disagreement recorded'], ['Due diligence', 'No additional exercise undertaken; no separate exercise required by the published tender and no outstanding verification concern recorded by the committee.']], { title: 'Clarifications and committee record' }),
      p('Recommend Afya Digital Supplies Limited at KES 46,400,000.00. The only bid received meets the published requirements. Clarification confirmed existing evidence without changing the offer. This report does not constitute an award.', { strong: true, title: 'Recommendation and reasons' }),
      E.sigs('Not yet signed', 'Not yet signed', 'Not yet signed')],
    sec: ['Back to report'], note: 'Draft preview. Signature state follows the viewing variant. The Back to report label is new copy.' }));

  E.add(
    signBoard({ id: 'S-STALE-REPORT', g: GS, name: 'Stale report', spec: '§9.10', nx: { k: 'turn', h: 'The report changed. Review the latest version before signing.' }, pri: 'Review latest report', sec: ['Download report'], blocks: signBlocks('Signed 14:05', 'Your signature needed', 'Awaiting signature'), note: 'Old Sign report absent.' }),
    signBoard({ id: 'S-UNCONFIRMED', g: GS, name: 'Unconfirmed signature', spec: '§9.10', nx: { k: 'turn', h: 'Your signature has not been confirmed.' }, pri: 'Check signature status', sec: ['Download report'], blocks: signBlocks('Signed 14:05', 'Your signature needed', 'Awaiting signature'), note: 'No duplicate Sign report while status is unknown.' }),
    rep({ id: 'S-AUDITOR', g: GS, name: 'Auditor / technical reader', spec: '§9.10', arch: 'Record detail', state: 'Report sent', title: 'Evaluation report 1', desc: TN, actor: 'naomi', at: '16 Jun 2027, 14:08 EAT', tr: T('ddd'),
      nx: { k: 'done', h: 'The committee report was sent to Charles Mutiso on 16 Jun 2027, 14:07 EAT.' }, blocks: sentBlocks, sec: ['Download report', 'View committee record'], note: 'Read-only; no work queue or member controls.' })
  );
});
