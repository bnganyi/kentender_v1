(window.EVL_Q = window.EVL_Q || []).push(function (E) {
  const { f, kv, tb, n, fi, at, ev, T, TN, TT, AF, KES } = E;
  const subject = f(['Subject', 'Afya service-location evidence'], ['Requirement', 'Within Kenya'], ['Response', 'Nairobi service centre']);
  const absentAtt = E.attend([['Grace Wambui', 'Chair', 'Joined 09:00'], ['Peter Mugo', 'Member', 'Joined 09:02'], ['Ruth Achieng', 'Member', 'Left 09:03:30'], ['Brian Wafula', 'Secretary', 'Present 09:00']]);
  const absentNotice = n('warning', 'All members of the current eligible committee must be present to record this conclusion.', 'Ruth Achieng must rejoin.');
  const d5 = (o) => E.recHead(Object.assign({ g: 'D05 Committee discussion', arch: 'Form or editor', state: 'Reviewing', spec: '§9.6', title: 'Committee discussion', desc: TN + ' · 14 Jun 2027', at: '14 Jun 2027, 09:04 EAT', after: 'D05-ABSENT' }, o));
  E.add(
    d5({ id: 'D05-ABSENT-CHAIR', name: 'Member absent — chair view', actor: 'grace', tr: T('dcn', 'Ruth Achieng'),
      nx: { k: 'wait', h: 'Waiting for Ruth Achieng to rejoin the discussion.' },
      blocks: [absentNotice, absentAtt, subject, ev([['Kenya service-centre details']])], sec: ['End discussion'],
      note: 'Chair variant of D05-ABSENT: End discussion only, no conclusion controls. Headline is new copy modelled on D05-START; please confirm.' }),
    d5({ id: 'D05-ABSENT-MEMBER', name: 'Member absent — Ruth rejoins', actor: 'ruth', tr: T('dcn', 'Ruth Achieng'),
      nx: { k: 'turn', h: 'Join the committee discussion.' },
      blocks: [absentNotice, absentAtt, subject, ev([['Kenya service-centre details']])], pri: 'Join discussion',
      note: 'Ruth’s view of D05-ABSENT. Reuses the D05-JOIN headline.' })
  );
  const rep = (o) => E.recHead(Object.assign({ g: 'D07 Report and signing', spec: '§9.11', crumb: ['Bid evaluation', TN, 'Report'] }, o));
  E.add(
    rep({ id: 'D07-OVERDUE-SEC', after: 'D07-OVERDUE', name: 'Evaluation overdue — secretary', arch: 'Form or editor', state: 'Reviewing', title: 'Evaluation report', desc: TN + ' · Draft report 1', actor: 'brian', at: '13 Jul 2027, 09:00 EAT', tr: T('dcn', 'Brian Wafula'),
      nx: { k: 'turn', h: 'Review the overdue evaluation and complete its report.' },
      blocks: [n('warning', 'The evaluation deadline has passed.'), f(['Evaluation deadline', '12 Jul 2027, 11:00 EAT'], ['Tender validity', 'Tender validity has not expired.']), E.summary(), E.sections()],
      pri: 'Send for signing', sec: ['Save draft', 'Preview report'], cons: 'Each member will review and sign this exact report. Changes will require a new version.', note: 'Secretary variant of D07-OVERDUE.' }),
    rep({ id: 'D07-DECISION-UNKNOWN-CHAIR', after: 'D07-DECISION-UNKNOWN', spec: '§9.13', name: 'Downstream status unknown — chair', arch: 'Review or decision', state: 'Report sent', title: 'Evaluation report 1', desc: TN, actor: 'grace', at: '17 Jun 2027, 10:00 EAT', tr: T('ddd'),
      nx: { k: 'turn', h: 'Record the report correction for Charles Mutiso.' },
      blocks: [n('warning', 'The later decision could not be checked.', 'Report 1 remains unchanged. A return cannot proceed until the later decision is known.'), E.summary(), E.sections()],
      pri: 'Send correction notice', sec: ['Report issue', 'Open report'], note: 'Opens the existing correction form (D08-CORRECTION) without reopening the report. Headline reused from D08-CORRECTION.' })
  );
  E.add(E.recHead({ id: 'D08-CORRECTION-HOP', after: 'D08-SUPPLEMENT-HOP', g: 'D08 Issues, verification and correction', spec: '§9.13', name: 'Report correction task — Head', arch: 'Review or decision', state: 'Report sent', actor: 'charles', at: '17 Jun 2027, 10:00 EAT', tr: T('ddd'),
    nx: { k: 'turn', h: 'Review the report correction alongside the delivered report.' },
    blocks: [f(['Task', 'Review report correction for ' + TN]),
      kv([['Recorded by', 'Grace Wambui'], ['Reason', 'The report gives the wrong page reference for the service address.'], ['Correction', 'Read page 2, section 3, instead of page 3.']], { title: 'Correction notice', sec: true }),
      f(['Report', 'Report 1 · delivered'], ['Downstream decision', 'Award decision recorded 17 Jun 2027, 09:00 EAT'])],
    pri: 'Open new evidence', sec: ['Open report'], note: 'Separate task linked to the correction notice; uses the same read-only layout as D08-SUPPLEMENT-HOP. Headline is new copy; please confirm. Clears only on Charles’s recorded review naming this notice.' }));
});
