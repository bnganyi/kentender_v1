(window.EVL_Q = window.EVL_Q || []).push(function (E) {
  const { p, f, kv, tb, n, fi, ra, cb, ds, at, lk, task, fb, em, T, TN, TT, AF } = E;
  const G1 = 'D01 Work workspace', G2 = 'D02 Committee and declaration', GS = 'Shared page states';
  const ws = { title: 'Bid evaluation', desc: 'Review automatic checks, resolve questions and prepare the committee report.', crumb: ['Bid evaluation'], arch: 'Work workspace', spec: '§9.2' };
  const reg = (rows, filterVal, extra) => [fb([['Find a tender', filterVal || '', { wide: true, ph: 'Find a tender' }], ['State', 'All states', { select: true }]], { title: 'Evaluations', sec: true })]
    .concat(rows ? [tb(['Tender', 'Title', 'Work state', 'Action'], rows)] : []).concat(extra || []);
  const row033 = [[TN, TT, 'Reviewing', '@View']];

  E.add(
    Object.assign({ id: 'D01', g: G1, name: 'Workspace — evidence needs a decision', actor: 'grace', at: '14 Jun 2027, 08:55 EAT', state: 'Reviewing',
      blocks: [task(TT, TN, 'Evidence needs a committee decision', 'Open evaluation')].concat(reg(row033)),
      note: 'State filter choices: All states, Preparing, Reviewing, Signing, Report sent, No evaluation required, Cancelled. No tracker or next-step block on the workspace.' }, ws),
    Object.assign({ id: 'D01-EMPTY', g: G1, name: 'Workspace — nothing assigned', actor: 'grace', at: '14 Jun 2027, 08:55 EAT',
      blocks: reg(null, '', [em('No evaluations are assigned to you.', null, 'clipboard')]) }, ws),
    Object.assign({ id: 'D01-FILTERED', g: G1, name: 'Workspace — search with no match', actor: 'grace', at: '14 Jun 2027, 08:55 EAT',
      blocks: [task(TT, TN, 'Evidence needs a committee decision', 'Open evaluation')].concat(reg(null, 'printers', [em('No evaluations match your search.', 'Clear search', 'search')])) }, ws),
    Object.assign({ id: 'D01-APPOINT', g: G1, name: 'Workspace — AO appointment task', actor: 'amina', at: '11 Jun 2027, 08:58 EAT', state: 'Preparing', spec: '§9.13',
      blocks: [task('Appoint evaluation committee for ' + TN, TT, 'Preparing', 'Appoint committee')].concat(reg([[TN, TT, 'Preparing', '@View']])),
      note: 'Opens D02-A. No bidder information.' }, ws),
    Object.assign({ id: 'D01-APPOINT-HOP', g: G1, name: 'Workspace — secretary task', actor: 'charles', at: '11 Jun 2027, 08:58 EAT', state: 'Preparing', spec: '§9.13',
      blocks: [task('Assign evaluation secretary for ' + TN, TT, 'Preparing', 'Assign secretary')].concat(reg([[TN, TT, 'Preparing', '@View']])),
      note: 'Charles’s separate view; opens D02-S.' }, ws)
  );

  const memberTable = tb(['Person', 'Department', 'Capacity'], [
    ['#Grace Wambui', '#Human Resource Management and Development', '#Chair'],
    ['#Peter Mugo', '#ICT', '#Member'], ['#Ruth Achieng', '#Finance', '#Member']
  ], { title: 'Committee members', caption: 'Each member declares conflicts before viewing bids.' });
  const tenderFacts = f(['Tender', TN], ['Title', TT]);
  const appointBlocks = [tenderFacts, memberTable, fi('Appointment reference', 'MOH/EVAL/033/2027', { req: true }), ds('Appointment history', 'No earlier appointment.')];
  const d2 = (o) => Object.assign({ g: G2, arch: 'Form or editor', crumb: ['Bid evaluation', TN], desc: TN + ' · ' + TT }, o);
  const roRoster = tb(['Person', 'Department', 'Capacity'], [['Grace Wambui', 'Human Resource Management and Development', 'Chair'], ['Peter Mugo', 'ICT', 'Member'], ['Ruth Achieng', 'Finance', 'Member']], { title: 'Appointed committee', sec: true });
  const replaceBlocks = (person, err) => [
    tb(['Person', 'Department', 'Capacity', 'Declaration'], [['Grace Wambui', 'Human Resource Management and Development', 'Chair', 'No conflict'], ['Peter Mugo', 'ICT', 'Member', 'Conflict declared'], ['Ruth Achieng', 'Finance', 'Member', 'No conflict']], { title: 'Current committee', sec: true }),
    at('Peter Mugo declared a conflict', 'I have a financial interest in Afya Digital Supplies Limited.'),
    fi('Incoming person', person, Object.assign({ select: true, req: true }, err ? { err: 'This person cannot serve on this evaluation committee.', errd: 'Peter Mugo has an unresolved declared conflict for this tender.' } : {})),
    f(['Department', 'ICT'], ['Capacity', 'Member']),
    fi('Appointment reference', 'MOH/EVAL/033/2027-R1', { req: true }),
    fi('Reason', 'Replace the member who declared a financial interest.', { area: true, req: true, rows: 2 })
  ];

  E.add(
    d2({ id: 'D02-A', name: 'Appoint committee', actor: 'amina', at: '11 Jun 2027, 08:59 EAT', state: 'Preparing', spec: '§9.3', title: 'Appoint evaluation committee',
      tr: T('cnn', 'Amina Hassan'), nx: { k: 'turn', h: 'Appoint the members who will evaluate this tender.' },
      blocks: appointBlocks, pri: 'Appoint committee', sec: ['Back to tender'], note: 'No bid facts or secretary field.' }),
    d2({ id: 'D02-S', name: 'Assign secretary', actor: 'charles', at: '11 Jun 2027, 09:04 EAT', state: 'Preparing', spec: '§9.3', title: 'Assign evaluation secretary',
      tr: T('cnn', 'Charles Mutiso'), nx: { k: 'turn', h: 'Assign the person who will organise the evaluation record.' },
      blocks: [roRoster, fi('Person', 'Brian Wafula', { select: true, req: true }), fi('Appointment reference', 'MOH/EVAL/SEC/033/2027', { req: true })],
      pri: 'Assign secretary', sec: ['Back to tender'], note: 'No member editing.' }),
    d2({ id: 'D02-D', name: 'Personal declaration', actor: 'peter', at: '11 Jun 2027, 09:11 EAT', spec: '§9.3', title: 'Your evaluation declaration',
      nx: { k: 'turn', h: 'Declare any conflict before viewing bids.' },
      blocks: [f(['Tender', TN], ['Title', TT], ['Your capacity', 'Member · ICT']), ra('Declaration', ['No conflict to declare', 'Declare a conflict'], 0), cb('I will keep bid information confidential and use it only for this evaluation.', true)],
      pri: 'Save declaration', sec: ['Back to evaluation'], note: 'Standalone declaration: no tracker.' }),
    d2({ id: 'D02-CONFLICT', name: 'Declaration — conflict', actor: 'peter', at: '11 Jun 2027, 09:11 EAT', spec: '§9.3', title: 'Your evaluation declaration',
      nx: { k: 'turn', h: 'Declare any conflict before viewing bids.' },
      blocks: [f(['Tender', TN], ['Title', TT], ['Your capacity', 'Member · ICT']), ra('Declaration', ['No conflict to declare', 'Declare a conflict'], 1), fi('Describe the conflict', 'I have a financial interest in Afya Digital Supplies Limited.', { area: true, req: true, rows: 2 }), cb('I will keep bid information confidential and use it only for this evaluation.', true)],
      pri: 'Save declaration', sec: ['Back to evaluation'], cons: 'You will not be able to view bids while this conflict is being resolved.' }),
    d2({ id: 'D02-REPLACE', name: 'Replace member', actor: 'amina', at: '14 Jun 2027, 10:00 EAT', state: 'Reviewing', spec: '§9.3', title: 'Replace committee member',
      tr: T('dcn', 'Amina Hassan'), nx: { k: 'turn', h: 'Resolve Peter Mugo\'s declared conflict.' },
      blocks: replaceBlocks('Samuel Otieno'), pri: 'Replace member', sec: ['Keep current appointment'],
      cons: 'The new member must declare interests and review the evaluation. Any report being signed will need a new version.', note: 'Isolated branch. Samuel Otieno is a fixture-only eligible replacement, not an opening member.' }),
    d2({ id: 'D02-INELIGIBLE', name: 'Replace member — ineligible person', actor: 'amina', at: '14 Jun 2027, 10:00 EAT', state: 'Reviewing', spec: '§9.13', title: 'Replace committee member',
      tr: T('dcn', 'Amina Hassan'), nx: { k: 'turn', h: 'Resolve Peter Mugo\'s declared conflict.' },
      blocks: replaceBlocks('Peter Mugo', true), pri: 'Replace member', sec: ['Keep current appointment'], note: 'No appointment committed; form and reason kept.' }),
    d2({ id: 'D02-INTAKE-FIRST', name: 'Opening complete before appointment', actor: 'amina', at: '12 Jun 2027, 11:11 EAT', state: 'Reviewing', spec: '§9.13', title: 'Appoint evaluation committee',
      tr: T('cnn', 'Amina Hassan'), nx: { k: 'turn', h: 'Appoint the evaluation committee.', s: 'Opening is complete. The evaluation committee has not been appointed.' },
      blocks: appointBlocks, pri: 'Appoint committee', sec: ['Back to tender'], note: 'Lifecycle is Reviewing (backend intake); the tracker shows the actor’s outstanding setup. No bid names, counts, amounts or findings.' }),
    d2({ id: 'D02-INTAKE-FIRST-HOP', name: 'Opening complete — secretary task', actor: 'charles', at: '12 Jun 2027, 11:11 EAT', state: 'Reviewing', spec: '§9.13', title: 'Assign evaluation secretary',
      tr: T('cnn', 'Charles Mutiso'), nx: { k: 'turn', h: 'Assign the person who will organise the evaluation record.' },
      blocks: [tenderFacts, fi('Person', 'Brian Wafula', { select: true, req: true }), fi('Appointment reference', 'MOH/EVAL/SEC/033/2027', { req: true })],
      pri: 'Assign secretary', sec: ['Back to tender'], note: 'Same case as D02-INTAKE-FIRST.' }),
    d2({ id: 'D02-DECLARE-FIRST', name: 'Declaration outstanding after intake', actor: 'peter', at: '12 Jun 2027, 11:11 EAT', state: 'Reviewing', spec: '§9.13', title: TT, desc: TN, arch: 'Record detail',
      tr: T('cnn', 'Peter Mugo'), nx: { k: 'turn', h: 'Complete your declaration before viewing bids.' },
      blocks: [f(['Your capacity', 'Member · ICT'], ['Appointment', 'MOH/EVAL/033/2027'])], pri: 'Complete declaration', sec: ['Back to evaluations'], note: 'No bid content. Opens D02-D.' }),
    d2({ id: 'D02-UNABLE', name: 'Record inability to serve', actor: 'peter', at: '14 Jun 2027, 10:00 EAT', state: 'Reviewing', spec: '§9.11', title: 'Committee record', desc: TN + ' · ' + TT, arch: 'Record detail',
      tr: T('dcn', 'Peter Mugo'), nx: { k: 'turn', h: 'Record why you cannot continue on the committee.' },
      blocks: [E.roster(), fi('Reason', 'I am unavailable for the remaining evaluation period.', { area: true, req: true, rows: 2 })],
      pri: 'Record inability to serve', sec: ['Back to evaluation'], note: 'Creates the AO appointment task.' }),
    d2({ id: 'D02-NO-BIDS', name: 'No evaluation required', actor: 'grace', at: '12 Jun 2027, 11:11 EAT', state: 'No evaluation required', spec: '§9.11', title: TT, desc: TN, arch: 'Record detail',
      nx: { k: 'done', h: 'No bids were received. No evaluation is required.' },
      blocks: [tb(['Event', 'Person', 'Recorded'], [
        ['Committee appointed · MOH/EVAL/033/2027', 'Amina Hassan', '11 Jun 2027, 09:00 EAT'],
        ['Secretary assigned · MOH/EVAL/SEC/033/2027', 'Charles Mutiso', '11 Jun 2027, 09:05 EAT'],
        ['Declaration · no conflict', 'Grace Wambui', '11 Jun 2027, 09:10 EAT'],
        ['Declaration · no conflict', 'Peter Mugo', '11 Jun 2027, 09:12 EAT'],
        ['Declaration · no conflict', 'Ruth Achieng', '11 Jun 2027, 09:14 EAT']], { title: 'Appointment and declaration history', sec: true }),
      lk(['View opening record'], { title: 'Source', sec: true })],
      sec: ['Back to evaluations'], note: 'No tracker, bidder table, assessment, report, declaration task or signing controls.' })
  );

  const sh = (o) => Object.assign({ g: GS, spec: '§9.10', crumb: ['Bid evaluation', TN] }, o);
  E.add(
    sh({ id: 'S-LOADING', name: 'Loading', actor: 'grace', blocks: [em('Loading evaluation…', null, 'loader')] }),
    sh({ id: 'S-ERROR', name: 'Service error', actor: 'grace', blocks: [em('We could not load this evaluation.', null, 'alert')], pri: 'Try again', sec: ['Back to evaluations'] }),
    sh({ id: 'S-NOT-FOUND', name: 'Not found', actor: 'grace', crumb: ['Bid evaluation'], blocks: [em('This evaluation is not available.', null, 'search')], sec: ['Back to evaluations'] }),
    sh({ id: 'S-FORBIDDEN', name: 'Module forbidden', actor: 'none', crumb: ['Bid evaluation'], blocks: [em('You do not have access to Bid evaluation.', null, 'ban', 'This area needs one of these responsibilities: Accounting Officer, Head of Procurement, appointed evaluation member, evaluation secretary or authorised auditor. Ask your KenTender administrator to assign the appropriate responsibility in System setup; committee membership also requires appointment.')] }),
    sh(E.recHead({ id: 'S-CHECKS', name: 'Checks in progress', actor: 'brian', at: '12 Jun 2027, 11:10:33 EAT', state: 'Preparing', arch: 'Record detail',
      tr: T('cnn', ''), notInvolved: 'Automatic checks are running.',
      blocks: [ds('Opening and source record', ['Opening completed 12 Jun 2027, 11:10:30 EAT', 'Submitted Version 1'], { links: ['View opening record'] })],
      note: 'Guidance: Not involved, no holder. No result table until checks return.' })),
    sh(E.recHead({ id: 'S-OPENING-AWAITED', name: 'Appointment complete, opening awaited', actor: 'grace', at: '11 Jun 2027, 09:15 EAT', state: 'Preparing', arch: 'Record detail',
      tr: T('cnn', 'System'), nx: { k: 'wait', label: 'Scheduled', h: 'Opening is scheduled for 12 Jun 2027, 11:00 EAT.' },
      blocks: [E.roster()], note: 'Holder: System. No bidder count, name or content. No start or release action.' })),
    sh(E.recHead({ id: 'S-SOURCE-OPEN', name: 'Source issue still open', actor: 'brian', at: '12 Jun 2027, 11:12 EAT', state: 'Preparing', arch: 'Record detail',
      tr: T('cnn', 'Esther Njeri'), nx: { k: 'wait', h: 'Esther Njeri is resolving the opening-package issue.', s: 'Since 11:11.' },
      blocks: [f(['Source', 'Opening completed 12 Jun 2027, 11:10:30 EAT'], ['Issue', 'The completed opening package could not be loaded.'])],
      sec: ['View issue'], note: 'No duplicate Report issue button.' })),
    sh(E.recHead({ id: 'S-STALE-RECORD', name: 'Stale record', actor: 'brian', at: '16 Jun 2027, 13:55 EAT', state: 'Reviewing', arch: 'Form or editor', title: 'Evaluation report', desc: TN + ' · Draft report 1',
      tr: T('dcn', 'Brian Wafula'), nx: { k: 'turn', h: 'Check the report and send it to members for signing.' },
      blocks: [E.n('warning', 'This record changed while you were working. Refresh it and try again.'), fi('Committee summary', 'The only bid received meets the published requirements. The submitted service-location evidence was clarified without changing the offer.', { area: true })],
      pri: 'Refresh', note: 'Page and unsent draft preserved; shown on D07-DRAFT.' }))
  );
});
