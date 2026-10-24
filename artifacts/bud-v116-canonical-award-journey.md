# Canonical two-source award: Award to Budget journey (test site)

Run 2026-10-17 12:28:08.444432 on `kentender-test.local`, award `AWD-MOH-2026-002`.

| Check | Result | Detail |
|---|---|---|
| the canonical award has a committed Award decision and a retained funding allocation | Pass | decision AWD-MOH-2026-002-DEC-01, allocation AWD-MOH-2026-002-FUN-01 |
| the award is split over two reservations that add up to KES 46,400,000 | Pass | 0b02d91cei=18560000.00, 0b0mqt2lje=27840000.00 |
| a contract Contract Management does not know cannot draw on any reservation (the interim check, before any stand-in) | Pass | refused: No funding owner confirms which reservations contract CM-JRNY-4adbea may draw on. Nothing was committed. |
| a wrong amount on one reservation is refused and nothing is funded | Pass | refused: The funding allocations do not add up to the contract amount. |
| a funding allocation Award does not hold is refused | Pass | refused: The funding allocation named for this award is not held. Nothing was committed. |
| a conversion that carries no lineage is refused | Pass | refused: The conversion names no award and no funding allocation. Nothing was committed. |
| a reservation the award does not name is refused | Pass | refused: Reservation NO-SUCH-RESERVATION not found |
| an Award owner that cannot answer stops the conversion, never a pass | Pass | refused: The Award owner did not answer. Nothing was committed. |
| a source that moved after the allocation was retained stops the conversion (stale source) | Pass | refused: The funding sources changed after the allocation was retained. Nothing was committed. |
| after every refusal the reservations and positions are exactly as they were | Pass |  |
| two contracts converting the same award at once: exactly one wins and the other is refused | Pass | {"a": ["ok", {"reference": "COM-MOH-0258, COM-MOH-0259", "amount": 46400000.0}], "b": ["refused", "Refused: Commitment amount (KES 18,560,000) exceeds the remaining reservation (KES 1,440,000)"]} |
| the winner holds exactly one commitment per reservation, with the awarded amounts | Pass | [('0b02d91cei', 18560000.0), ('0b0mqt2lje', 27840000.0)] |
| the loser holds nothing | Pass |  |
| conversion moves exactly the awarded price from Reserved to Committed and leaves Available unchanged | Pass | committed 46400000.00, reserved -46400000.00, available 0.00 |
| each commitment carries the verified Award allocation it came from | Pass | {'agreement_version': '1', 'allocation_digest': '353c38cd28c56e6678e4228b4ad4d42a2ec85dc0576482ba3a12b4d3a3b10faf', 'award': 'AWD-MOH-2026-002', 'decision': 'AW |
| repeating the conversion returns the same result and creates nothing more | Pass | {'reference': 'COM-MOH-0258, COM-MOH-0259', 'amount': 46400000.0} |
| the funding owner reads back what it already did under that identity | Pass |  |
| a third contract cannot take what is already converted (no overspend) | Pass | refused: Commitment amount (KES 18,560,000) exceeds the remaining reservation (KES 1,440,000) |
| a lawful increase of KES 100,000 raises Committed and lowers Available by exactly that | Pass | {'reference': 'COM-MOH-0258', 'amount': 18660000.0, 'before': 18560000.0, 'after': 18660000.0} |
| closing the contract changes status only: the final amount stays counted and nothing is released | Pass | {'reference': 'COM-MOH-0258, COM-MOH-0259', 'amount': 46500000.0} |
| a repeated closure is the same closure | Pass | first {'reference': 'COM-MOH-0258, COM-MOH-0259', 'amount': 46500000.0}, again {'reference': 'COM-MOH-0258, COM-MOH-0259', 'amount': 46500000.0} |
| a Closed commitment accepts no further adjustment from the contract service | Pass | refused: A Closed commitment is changed only by an approved correction |
| reopening the contract in Contract Management makes no funding call and changes nothing in Budget | Pass |  |
| a real later increment after closure is received as one Additional request for the increment only | Pass | {'id': 'v4d84rrgb2', 'code': 'CFR-MOH-0049', 'kind': 'Additional', 'status': 'Open', 'outcome': '', 'display_status': 'Ready to prepare', 'h |
| the Officer records the Additional entry | Pass | {'ok': True, 'entry': {'id': 'v4e8rfuh8i', 'code': 'ECE-MOH-0040', 'request': 'v4d84rrgb2', 'request_code': 'CFR-MOH-0049', 'kind': 'Additio |
| the Officer submits it | Pass | {'ok': True, 'entry': {'id': 'v4e8rfuh8i', 'code': 'ECE-MOH-0040', 'request': 'v4d84rrgb2', 'request_code': 'CFR-MOH-0049', 'kind': 'Additio |
| the preparer cannot approve their own entry | Pass | ResponsibilityError: You are not assigned the responsibility required for this action. |
| a different Budget Approver approves it | Pass | {'ok': True, 'entry': {'id': 'v4e8rfuh8i', 'code': 'ECE-MOH-0040', 'request': 'v4d84rrgb2', 'request_code': 'CFR-MOH-0049', 'kind': 'Additio |
| only the increment is added to Committed and taken from Available; Reserved is untouched | Pass | {'approved': Decimal('60000000.00'), 'reserved': Decimal('3600000.00'), 'committed': Decimal('46550000.00'), 'available': Decimal('9850000.00')} |
| the original Closed commitment is neither raised nor reopened | Pass |  |
| repeating the same increment funds nothing a second time | Pass | {'ok': False, 'code': 'BUDGET_ENTRY_DUPLICATE', 'errors': {'request': 'Funding for this contract and year is already com |
| the Officer records a supported downward correction of the Closed commitment | Pass | {'ok': True, 'correction': {'id': 'v4hdrm8vg6', 'code': 'COR-MOH-0012', 'status': 'Awaiting approval', 'commitment': 'v4bbpdna4f', 'budget': |
| the person who recorded the correction cannot approve it | Pass | ResponsibilityError: You are not assigned the responsibility required for this action. |
| a different Budget Approver approves it | Pass | {'ok': True, 'correction': {'id': 'v4hdrm8vg6', 'code': 'COR-MOH-0012', 'status': 'Approved', 'commitment': 'v4bbpdna4f', 'budget': 'vt01c93 |
| the decrease goes back to Available; Reserved and the reservation's own remainder are unchanged | Pass | {'approved': Decimal('60000000.00'), 'reserved': Decimal('3600000.00'), 'committed': Decimal('46350000.00'), 'available': Decimal('10050000.00')} |
| A - R - C = V on 7b89l1l9ss | Pass | {'approved': Decimal('60000000.00'), 'reserved': Decimal('3600000.00'), 'committed': Decimal('46350000.00'), 'available': Decimal('10050000.00')} |
| the canonical Budget is back exactly as it was found | Pass |  |
