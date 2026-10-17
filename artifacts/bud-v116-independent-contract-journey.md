# Independent contract: Contract Management to Budget, year by year (test site)

Run 2026-10-17 13:20:17.687753 on `kentender-test.local`.

| Check | Result | Detail |
|---|---|---|
| the site has two consecutive financial years with an Active Budget each | Pass | 2026-2027, 2027-2028 |
| before any route is recorded the contract carries no funding hold (it keeps its earlier behaviour) | Pass | [] |
| only the Head of Procurement can record the route (Finance preparation is refused) | Pass | refused: You are not authorised to take this action. |
| a year share that is not a financial year of this site is refused | Pass | refused: Choose a financial year that exists on this site. |
| the Head records the route and the year shares; the contract names both years | Pass | [('2026-2027', '400000.00', 'Year allocation required'), ('2027-2028', '300000.00', 'Future funding not yet confirmed')] |
| with the route recorded, this year's unfunded spending and payments are held | Pass | ['funding:CM-JRNY-IND-3b521a:pay:2026-2027', 'funding:CM-JRNY-IND-3b521a:spending'] |
| Finance preparation prepares the year's basis and cannot confirm it | Pass | refused: You are not authorised to take this action. |
| year 1: the Head's one request reaches the real Budget owner as an Initial request for 2026-2027 and Contract Management says it is open | Pass | CFR-MOH-0057, Year allocation required, Contract Management: Open |
| year 1: asking again for the same year returns the same request and creates no second | Pass |  |
| year 1: while Finance has not confirmed the year, Budget says Year allocation required and offers the Officer no Submit | Pass | Year allocation required; actions ['decline', 'save'] |
| year 1: Finance's later confirmation reaches the same Budget request, which is now Confirmed with the charge | Pass | Confirmed, charge 400000.00 |
| year 1: Budget calculated the amount to fund from the confirmed charge and the coverage it can verify (none yet) | Pass | charge 400000.00, required 400000.00 |
| year 1: nothing is committed by the request alone | Pass |  |
| year 1: the Budget Officer is offered budget lines with room for the whole amount, and Submit | Pass | 2 lines with room, 2 eligible, actions ['decline', 'save', 'submit'] |
| year 1: the Officer records the entry on one line for the whole amount | Pass | {'ok': True, 'entry': {'id': 'tm6dhv2jpa', 'code': 'ECE-MOH-0044', 'request': 'tm2doc97g5', 'request_code': 'CFR-MOH-0057', 'kind': 'Initial', 'status |
| year 1: the Officer submits it for approval | Pass | {'ok': True, 'entry': {'id': 'tm6dhv2jpa', 'code': 'ECE-MOH-0044', 'request': 'tm2doc97g5', 'request_code': 'CFR-MOH-0057', 'kind': 'Initial', 'status |
| year 1: nothing moves while it awaits approval | Pass |  |
| year 1: the Budget Approver who confirmed the year's basis in Contract Management is refused, with the real people on both sides | Pass | refused: You cannot perform this action because you completed an incompatible earlier step. |
| year 1: the Budget Officer who prepared the entry cannot approve it | Pass | refused: You are not assigned the responsibility required for this action. |
| year 1: the refusals leave the entry awaiting approval and nothing committed | Pass |  |
| year 1: the second Approver is offered Approve | Pass | {'approve': True, 'return': True, 'blocked': ''} |
| year 1: a Budget Approver who prepared nothing and confirmed nothing approves it | Pass | {'ok': True, 'entry': {'id': 'tm6dhv2jpa', 'code': 'ECE-MOH-0044', 'request': 'tm2doc97g5', 'request_code': 'CFR-MOH-0057', 'kind': 'Initial', 'status |
| year 1: exactly the charge moves into Committed and out of Available; Reserved is untouched | Pass | committed 400000.00, available -400000.00, reserved 0.00 |
| year 1: the commitment is the contract's own, on the entry's line, of the entry's origin | Pass | [{'name': 'tm7dpimmar', 'budget_line': '7b89l1l9ss', 'budget': 'vt01c93fan', 'current_amount': 400000.0, 'status': 'Active', 'origin': 'Existing-contract entry' |
| year 1: Budget's outcome reached Contract Management in the same step and the year shows Completed | Pass | Completed / Funding entry approved |
| year 1: the funding holds are lifted | Pass | [] |
| year 1: the contract's funded years now include year 1 only | Pass | {'2026-2027'} |
| year 1: the request is Completed in Budget and a repeat of the same approval creates nothing more | Pass | Completed |
| the clock moves into the second financial year | Pass | 2027-2028 |
| year 2: the contract is still Active, not reopened, and the new year's spending is held until it is funded | Pass | ['funding:CM-JRNY-IND-3b521a:pay:2027-2028', 'funding:CM-JRNY-IND-3b521a:spending'] |
| year 2: year 1's funding is untouched and nothing is carried forward | Pass | {'2026-2027'} |
| year 2: the Head's one request reaches the real Budget owner as an Annual request for 2027-2028 and Contract Management says it is open | Pass | CFR-MOH-0058, Confirmed, Contract Management: Open |
| year 2: asking again for the same year returns the same request and creates no second | Pass |  |
| year 2: Budget calculated the amount to fund from the confirmed charge and the coverage it can verify (none yet) | Pass | charge 300000.00, required 300000.00 |
| year 2: nothing is committed by the request alone | Pass |  |
| year 2: the Budget Officer is offered budget lines with room for the whole amount, and Submit | Pass | 1 lines with room, 1 eligible, actions ['decline', 'save', 'submit'] |
| year 2: the request is a new Annual one for the second year, on its own lineage, and year 1's request stays Completed | Pass | CFR-MOH-0058 (Annual, 2027-2028); year 1: CFR-MOH-0057 Completed |
| year 2: the Officer records the entry on one line for the whole amount | Pass | {'ok': True, 'entry': {'id': 'tmanprk11t', 'code': 'ECE-MOH-0045', 'request': 'tm942phft9', 'request_code': 'CFR-MOH-0058', 'kind': 'Annual', 'status' |
| year 2: the Officer submits it for approval | Pass | {'ok': True, 'entry': {'id': 'tmanprk11t', 'code': 'ECE-MOH-0045', 'request': 'tm942phft9', 'request_code': 'CFR-MOH-0058', 'kind': 'Annual', 'status' |
| year 2: nothing moves while it awaits approval | Pass |  |
| year 2: the second Approver is offered Approve | Pass | {'approve': True, 'return': True, 'blocked': ''} |
| year 2: a Budget Approver who prepared nothing and confirmed nothing approves it | Pass | {'ok': True, 'entry': {'id': 'tmanprk11t', 'code': 'ECE-MOH-0045', 'request': 'tm942phft9', 'request_code': 'CFR-MOH-0058', 'kind': 'Annual', 'status' |
| year 2: exactly the charge moves into Committed and out of Available; Reserved is untouched | Pass | committed 300000.00, available -300000.00, reserved 0.00 |
| year 2: the commitment is the contract's own, on the entry's line, of the entry's origin | Pass | [{'name': 'tmberre0lf', 'budget_line': 'er858iukh5', 'budget': '7d03cfm2f3', 'current_amount': 300000.0, 'status': 'Active', 'origin': 'Existing-contract entry' |
| year 2: Contract Management shows both years funded and no funding hold remains | Pass | {'2026-2027', '2027-2028'} [] |
| year 2: year 1's commitment is exactly as it was (same amount, same status, same line) | Pass |  |
| year 2: the contract's commitments are one per year, in two different Budgets | Pass | [('vt01c93fan', 400000.0), ('7d03cfm2f3', 300000.0)] |
| the contract was never reopened: its lifecycle is Active throughout and no reopening was recorded | Pass |  |
| A - R - C = V on 7b89l1l9ss | Pass | {'approved': Decimal('60000000.00'), 'reserved': Decimal('50000000.00'), 'committed': Decimal('400000.00'), 'available': Decimal('9600000.00')} |
| A - R - C = V on er858iukh5 | Pass | {'approved': Decimal('60000000.00'), 'reserved': Decimal('0.00'), 'committed': Decimal('300000.00'), 'available': Decimal('59700000.00')} |
| the canonical Budget is back exactly as it was found | Pass |  |
| no request, outcome, entry or contract of this journey is left behind | Pass | {} |
