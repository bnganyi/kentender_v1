#!/bin/bash
# Phase 2 spike: every scenario from a clean world, one process each, in dependency order. Test site only.
cd /home/midasuser/frappe-bench
SITE=kentender-test.local
EV=apps/kentender_v1/docs/mvp-1-r1/21_contract_management/evidence/v0_8/spike
rm -f $EV/s1.json $EV/s2_s3_fixed_asset.json $EV/s4_invoice.json $EV/s4b_credit_note_net_position.json $EV/s5a_workflow_maker_approver.json $EV/s5b_paths_*.json $EV/s5c_enforce.json $EV/s5d_beneficiary_change.json $EV/s5e_race.json $EV/s5f_background_route.json $EV/s2_stock_inspection.json $EV/s3b_missing_serial.json $EV/s7a_crash_recovery.json $EV/s7b_reversals.json $EV/s7b2_cancel_in_the_right_order.json $EV/s6_signing.json $EV/s8_template.json $EV/s9_independence.json
run() { echo "=== $1 $2"; bench --site "$SITE" execute "$1" ${2:+--kwargs "$2"} 2>&1 | grep -E "evidence:|Traceback|^[A-Za-z_.]*Error" | head -3; }
bench --site $SITE execute kentender_contracts.spike.world.teardown >/dev/null 2>&1
run kentender_contracts.spike.native.s1
run kentender_contracts.spike.native.s2_s3_fixed_asset
run kentender_contracts.spike.native.s4_invoice
run kentender_contracts.spike.native.s4b_credit_note_net_position
run kentender_contracts.spike.native.s5a_workflow_maker_approver
run kentender_contracts.spike.native.s5b_paths "{'mode':'probe','hold':True,'tag':'_native_hold'}"
run kentender_contracts.spike.native.s5b_paths "{'mode':'probe','hold':False,'tag':'_uncertified'}"
run kentender_contracts.spike.native.s5c_enforce
run kentender_contracts.spike.native.s5d_beneficiary_change
run kentender_contracts.spike.native.s5e_race
run kentender_contracts.spike.native.s5f_background_and_import_routes
run kentender_contracts.spike.native.s2_stock_inspection
run kentender_contracts.spike.native.s3_missing_serial
run kentender_contracts.spike.recovery.s7a_crash_recovery
run kentender_contracts.spike.recovery.s7b_reversals
run kentender_contracts.spike.recovery.s7b2_cancel_in_the_right_order
run kentender_contracts.spike.signing.s6_signing
run kentender_contracts.spike.template.s8_template
echo "=== S9 on the independence site"
bench --site kentender-cm-only.local execute kentender_contracts.spike.independence.s9_independence 2>&1 | grep -E "evidence:|Traceback" | head -2
echo DONE
