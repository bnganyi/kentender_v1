(window.EVL_Q = window.EVL_Q || []).push(function (E) {
  const { p, f, kv, tb, n, fi, ra, sg, ds, at, lk, ev, T, TN, TT, AF, KES } = E;
  const G8 = 'D08 Issues, verification and correction', GP = 'Pause and cancellation';
  const r8 = (o) => E.recHead(Object.assign({ g: G8, arch: 'Review or decision', state: 'Reviewing', spec: '§9.9' }, o));
  const disc = (o) => E.recHead(Object.assign({ g: G8, arch: 'Form or editor', state: 'Reviewing', spec: '§9.13', title: 'Committee discussion', desc: TN + ' · 16 Jun 2027' }, o));
  const att3 = (g, pe, r) => E.attend([['Grace Wambui', 'Chair', g], ['Peter Mugo', 'Member', pe], ['Ruth Achieng', 'Member', r]]);
  const OBS = 'Both customers confirmed the submitted contract details.';
  const ddFacts = f(['Scope', 'Verify the two submitted comparable contracts'], ['Participants', 'Grace Wambui (lead) and Ruth Achieng']);
  const ddEv = ev([['KNH contract evidence'], ['KMTC contract evidence']]);
  const cmp = E.comp([[AF, 'Meets', 'Needs review', KES, 'Needs review', 'Not ranked', '@Review bid']]);

  E.add(
    r8({ id: 'D08-SOURCE', name: 'Failed intake — issue recorded', actor: 'brian', at: '12 Jun 2027, 11:11 EAT', state: 'Preparing', tr: T('cnn', 'Esther Njeri'),
      nx: { k: 'wait', h: 'Esther Njeri is resolving the opening-package issue.', s: 'Since 11:11.' },
      blocks: [n('warning', 'Some opened bid information could not be loaded.'), f(['Source', 'Opening completed 12 Jun 2027, 11:10:30 EAT']),
        kv([['Recorded', 'System, 12 Jun 2027, 11:11 EAT'], ['Assigned to', 'Esther Njeri, Technical support'], ['Reason', 'The completed opening package could not be loaded.']], { title: 'Support issue', sec: true })],
      pri: 'View issue', sec: ['Try again'], note: 'Separate failed-intake branch. No bid count or comparison shown as success. No Report issue dialog.' }),
    r8({ id: 'D08-RULE', name: 'Missing evaluation rule', actor: 'grace', at: '14 Jun 2027, 08:55 EAT', tr: T('dcn', 'Grace Wambui'),
      nx: { k: 'turn', h: 'Review the missing rule for storage capacity.' },
      blocks: [n('warning', 'This requirement needs review because its evaluation rule is unavailable.'),
        tb(['Requirement', 'Required', 'Offered', 'Result', 'Reason'], [
          ['Storage capacity', 'Minimum 512 GB', '512 GB', 'Needs review', 'The automatic comparison rule is unavailable.'],
          ['Memory', 'Minimum 16 GB', '16 GB', 'Meets', 'Offered memory meets the minimum'],
          ['Warranty', 'Minimum 36 months', '36 months', 'Meets', 'Offered warranty meets the minimum']], { title: 'Results' })],
      pri: 'Report issue', sec: ['View report'], note: 'Separate branch. Never Edit criterion.' }),
    disc({ id: 'D08-VERIFY-PLAN', name: 'Record verification plan', actor: 'grace', at: '16 Jun 2027, 09:13 EAT', tr: T('dcn', 'Grace Wambui'),
      nx: { k: 'turn', h: 'Record the committee’s verification plan.' },
      blocks: [att3('Joined 09:10', 'Joined 09:11', 'Joined 09:12'),
        E.comp([[AF, 'Meets', 'Meets', KES, KES, '1', '@Review bid']], { title: 'Refreshed comparison', sec: true }),
        fi('Scope', 'Verify the two submitted comparable contracts', { req: true }),
        fi('Basis', 'Due diligence under PPADA section 83; verify the two submitted comparable contracts', { req: true }),
        fi('Participants', 'Grace Wambui, Ruth Achieng', { select: true, req: true, help: 'Selected from the current eligible committee.' }),
        fi('Lead', 'Grace Wambui', { select: true, req: true })],
      pri: 'Record verification plan', sec: ['End discussion'], note: 'Independent verification branch; replaces the ordinary no-additional-exercise conclusion. Recorded 09:14, ended 09:15.' }),
    r8({ id: 'D08-DD', name: 'Record verification findings', actor: 'ruth', at: '16 Jun 2027, 10:00 EAT', tr: T('dcn', 'Ruth Achieng'),
      nx: { k: 'turn', h: 'Record the supplier verification findings.' },
      blocks: [ddFacts, ddEv, fi('Findings', OBS, { area: true, req: true, rows: 3 })], pri: 'Save findings', note: 'No new qualification criteria.' }),
    r8({ id: 'D08-DD-FREEZE', name: 'Send verification report for signing', spec: '§9.11', actor: 'grace', at: '16 Jun 2027, 10:50 EAT', tr: T('dcn', 'Grace Wambui'),
      nx: { k: 'turn', h: 'Send the verification report to its participants for signing.' },
      blocks: [ddFacts, tb(['Participant', 'Recorded', 'Observation'], [['Ruth Achieng', '10:00', OBS], ['Grace Wambui', '10:30', OBS]], { title: 'Verification findings', sec: true }), ddEv],
      pri: 'Send verification report for signing', sec: ['Preview verification report'], cons: 'Each participant will sign the same report and its required pages.' }),
    r8({ id: 'D08-DD-SIGN', name: 'Sign verification report', actor: 'ruth', at: '16 Jun 2027, 11:00 EAT', tr: T('dcn', 'Ruth Achieng'),
      nx: { k: 'turn', h: 'Review and sign verification report' },
      blocks: [f(['Report', 'Verification report 1 · frozen']), ddFacts, tb(['Participant', 'Observation'], [['Ruth Achieng', OBS], ['Grace Wambui', OBS]], { title: 'Findings', sec: true }),
        tb(['Participant', 'Signature'], [['Grace Wambui', 'Signed 10:55'], ['Ruth Achieng', 'Your signature needed']], { title: 'Signatures', sec: true })],
      pri: 'Sign verification report' }),
    disc({ id: 'D08-VERIFY-OUTCOME', name: 'Verification outcome — supports evidence', actor: 'grace', at: '16 Jun 2027, 11:13 EAT', tr: T('dcn', 'Grace Wambui'),
      nx: { k: 'turn', h: 'Record how verification affects the evaluation.' },
      blocks: [att3('Joined 11:10', 'Joined 11:11', 'Joined 11:12'),
        tb(['Participant', 'Signature'], [['Grace Wambui', 'Signed 10:55'], ['Ruth Achieng', 'Signed 11:00']], { title: 'Verification report 1', sec: true }),
        at(OBS), sg('Result', ['Meets', 'Does not meet', 'Needs review'], 0), fi('Reason', 'The verification supports the submitted experience evidence.', { area: true, req: true, rows: 2 })],
      pri: 'Record conclusion', sec: ['View verification report', 'End discussion'], note: 'Discussion ends at 11:15 after the conclusion.' }),
    disc({ id: 'D08-VERIFY-NEG', name: 'Verification outcome — negative', actor: 'grace', at: '16 Jun 2027, 11:13 EAT', tr: T('dcn', 'Grace Wambui'),
      nx: { k: 'turn', h: 'Record how verification affects the evaluation.' },
      blocks: [att3('Joined 11:10', 'Joined 11:11', 'Joined 11:12'),
        at('One customer could not confirm the submitted contract and the committee established that the mandatory experience requirement was not met.'),
        f(['Affected requirement', 'Comparable experience'], ['Required value', 'Two comparable completed contracts']),
        kv([['KNH customer confirmation', 'Recorded by Ruth Achieng, 10:00 — “The submitted contract reference belongs to a different supplier.”']], { title: 'Evidence', sec: true }),
        sg('Result', ['Meets', 'Does not meet', 'Needs review'], 1), fi('Reason', '', { area: true, req: true, rows: 2 })],
      pri: 'Record conclusion', sec: ['View verification report', 'End discussion'], note: 'The system does not silently choose another supplier. The reason field is left empty; the brief gives no text for it.' }),
    r8({ id: 'D08-SUPPLEMENT', name: 'Opening update before delivery', actor: 'grace', at: '16 Jun 2027, 13:00 EAT', tr: T('dcn', 'Grace Wambui'),
      nx: { k: 'turn', h: 'Review the correction added to the opening record.' },
      blocks: [f(['Recorded by', 'Charles Mutiso, 12:55'], ['Kind', 'Attendance note'], ['Note', 'David Ouma left at 11:05 EAT.']),
        ra('Impact', ['No effect on findings', 'Findings need review'], 0), fi('Reason', 'The correction concerns attendance only.', { area: true, req: true, rows: 2 })],
      pri: 'Record impact', sec: ['View opening record'], note: 'Task: Review opening update for ' + TN + '. No original bid editing.' }),
    r8({ id: 'D08-SUPPLEMENT-SENT', name: 'Opening update after delivery — chair', spec: '§9.13', state: 'Report sent', actor: 'grace', at: '17 Jun 2027, 10:00 EAT', tr: T('ddd'),
      nx: { k: 'turn', h: 'Review the opening update.' },
      blocks: [f(['Source', 'Opening record supplement, 17 Jun 09:55'], ['Kind', 'Attendance note'], ['Text', 'David Ouma left at 11:05 EAT on 12 Jun.']), f(['Report', 'Report 1 · delivered']),
        ra('Impact', ['No effect on findings', 'Findings need review'], 0), fi('Reason', 'Attendance only.', { area: true, req: true, rows: 2 })],
      pri: 'Record impact', sec: ['View opening record'] }),
    r8({ id: 'D08-SUPPLEMENT-HOP', name: 'Opening update after delivery — Head', spec: '§9.13', state: 'Report sent', actor: 'charles', at: '17 Jun 2027, 10:00 EAT', tr: T('ddd'),
      nx: { k: 'turn', h: 'Review the opening update alongside the delivered report.' },
      blocks: [f(['Task', 'Review opening update for ' + TN]), f(['Source', 'Opening record supplement, 17 Jun 09:55'], ['Kind', 'Attendance note'], ['Text', 'David Ouma left at 11:05 EAT on 12 Jun.']), f(['Report', 'Report 1 · delivered'])],
      pri: 'Open new evidence', sec: ['Open report', 'Return for correction'], note: 'Opening the evidence does not clear the task. A simultaneous correction notice creates a separate “Review report correction” task.' }),
    r8({ id: 'D08-CORRECTION', name: 'Post-award correction notice', state: 'Report sent', actor: 'grace', at: '17 Jun 2027, 10:00 EAT', tr: T('ddd'),
      nx: { k: 'turn', h: 'Record the report correction for Charles Mutiso.' },
      blocks: [f(['Report', 'Report 1 · delivered'], ['Downstream decision', 'Award decision recorded 17 Jun 2027, 09:00 EAT']),
        fi('Reason', 'The report gives the wrong page reference for the service address.', { area: true, req: true, rows: 2 }), fi('Correction', 'Read page 2, section 3, instead of page 3.', { area: true, req: true, rows: 2 })],
      pri: 'Send correction notice', sec: ['Open report'], note: 'Separate post-award branch. No Reopen report.' }),
    r8({ id: 'D08-PAUSED', name: 'Paused during review', actor: 'grace', at: '14 Jun 2027, 10:00 EAT', tr: T('dbn', 'Amina Hassan'),
      nx: { k: 'wait', h: 'Evaluation is paused by the recorded instruction.' },
      blocks: [f(['Instruction', 'MOH/REVIEW/033/2027'], ['Received', '14 Jun 2027, 09:55 EAT'], ['Transmitted by', 'Amina Hassan, Accounting Officer']), Object.assign(cmp, { title: 'Current findings (read-only)', sec: true })],
      sec: ['View instruction', 'View report'], note: 'No local Resume, new clarification or signing action.' }),
    r8({ id: 'D08-CANCELLED', name: 'Cancelled during review', state: 'Cancelled', arch: 'Record detail', actor: 'grace', at: '14 Jun 2027, 10:00 EAT', tr: T('dbn', ''),
      nx: { k: 'done', h: 'Evaluation ended', s: 'Cancelled on 14 Jun 2027, 09:55 EAT.' },
      blocks: [f(['Authority', 'Amina Hassan'], ['Source', 'Tenders'], ['Reason', 'Procurement proceedings terminated under the recorded decision.']),
        E.comp([[AF, 'Meets', 'Needs review', KES, 'Needs review', 'Not ranked', '—']], { title: 'Partial findings', sec: true, caption: 'Evaluation ended before a report was sent.' })],
      sec: ['View cancellation notice', 'View committee record'], note: 'No evaluation action. The interrupted stage uses the standard blocked marker.' })
  );

  const pc = (o) => E.recHead(Object.assign({ g: GP, arch: 'Record detail', spec: '§9.13' }, o));
  const sig1 = E.sigs('Signed 14:05', 'Awaiting signature', 'Awaiting signature');
  E.add(
    pc({ id: 'P-PREP', name: 'Paused in Preparing — appointment permitted', actor: 'amina', at: '11 Jun 2027, 08:58 EAT', state: 'Preparing', tr: T('bnn', 'Amina Hassan'),
      nx: { k: 'turn', h: 'Appoint the members who will evaluate this tender.' },
      blocks: [n('warning', 'Evaluation is paused by the recorded instruction.'), f(['Instruction', 'MOH/REVIEW/033/2027-PREP'], ['Received', '11 Jun 2027, 08:55 EAT'], ['Transmitted by', 'Amina Hassan, Accounting Officer'], ['Permits', 'Appointments and declarations only'])],
      pri: 'Appoint committee', sec: ['View instruction'], note: 'No bid content.' }),
    pc({ id: 'P-SIGN', name: 'Paused in Signing', actor: 'grace', at: '16 Jun 2027, 14:05:30 EAT', state: 'Signing', tr: T('ddb', 'Amina Hassan'),
      nx: { k: 'wait', h: 'Evaluation is paused by the recorded instruction.' },
      blocks: [f(['Instruction', 'MOH/REVIEW/033/2027-SIGN'], ['Received', '16 Jun 2027, 14:05:20 EAT'], ['Transmitted by', 'Amina Hassan, Accounting Officer'], ['Permits', 'No administrative actions']), sig1],
      sec: ['View instruction', 'View report'], note: 'Grace’s 14:05 proof retained; never claim delivery.' }),
    pc({ id: 'C-PREP', name: 'Cancelled in Preparing', actor: 'amina', at: '11 Jun 2027, 08:58 EAT', state: 'Cancelled', tr: T('bnn', ''),
      nx: { k: 'done', h: 'Evaluation ended' },
      blocks: [f(['Instruction', 'MOH/CANCEL/033/2027-PREP'], ['Received', '11 Jun 2027, 08:55 EAT'], ['Authority', 'Amina Hassan, Accounting Officer'])],
      sec: ['View cancellation notice'], note: 'No current holder, mutation or Resume controls.' }),
    pc({ id: 'C-SIGN', name: 'Cancelled in Signing', actor: 'grace', at: '16 Jun 2027, 14:05:30 EAT', state: 'Cancelled', tr: T('ddb', ''),
      nx: { k: 'done', h: 'Evaluation ended' },
      blocks: [f(['Instruction', 'MOH/CANCEL/033/2027-SIGN'], ['Received', '16 Jun 2027, 14:05:20 EAT'], ['Authority', 'Amina Hassan, Accounting Officer']), sig1],
      sec: ['View cancellation notice', 'View committee record'], note: 'Report never delivered.' })
  );
});
