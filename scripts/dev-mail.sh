#!/usr/bin/env bash
# Dev mail: send the dev site's queued email and queued Tender notices on a timer, nothing else.
#
#   scripts/dev-mail.sh start    start the flush loop (every INTERVAL seconds)
#   scripts/dev-mail.sh stop     stop it
#   scripts/dev-mail.sh status   is the loop running, is Mailpit up, how many mails wait
#   scripts/dev-mail.sh once     flush the queue one time and exit
#
# Why: the dev site's scheduler is off and Frappe sends queued mail (sign-up,
# welcome, verification links) only from the scheduler, so a supplier who
# signs up would wait for a mail that never leaves. This runs just Frappe's
# own `email.queue.flush`, plus the Tenders outbox sweep that turns a queued
# candidate notice (a clarification answer, an addendum) into an email; no
# other background job. Mail lands in Mailpit
# (inbox http://localhost:8025, SMTP localhost:1025). Frappe holds new mail
# back for about 10 seconds, so expect up to INTERVAL + 10 seconds.
set -euo pipefail

BENCH_ROOT="${BENCH_ROOT:-/home/midasuser/frappe-bench}"
SITE="${SITE:-kentender.midas.com}"
INTERVAL="${INTERVAL:-8}"
PID_FILE="$BENCH_ROOT/logs/dev-mail-flush.pid"
LOG_FILE="$BENCH_ROOT/logs/dev-mail-flush.log"
MAILPIT_API="${MAILPIT_API:-http://localhost:8025/api/v1/info}"

cd "$BENCH_ROOT"

running() { [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; }

NOTICES=kentender_procurement.tenders.services.candidate_notices.dispatch_pending

flush() {
	bench --site "$SITE" execute "$NOTICES" >/dev/null
	bench --site "$SITE" execute frappe.email.queue.flush >/dev/null
}

cmd_start() {
	if running; then echo "Mail flush loop already running (pid $(cat "$PID_FILE"))"; return 0; fi
	nohup bash -c "while true; do bench --site '$SITE' execute $NOTICES >/dev/null 2>&1; bench --site '$SITE' execute frappe.email.queue.flush >/dev/null 2>&1 || echo \"\$(date -Is) flush failed\"; sleep $INTERVAL; done" > "$LOG_FILE" 2>&1 < /dev/null &
	echo $! > "$PID_FILE"
	echo "Mail flush loop started for $SITE every ${INTERVAL}s (notices, then the mail queue) (log: $LOG_FILE)"
}

cmd_stop() {
	if running; then
		pkill -P "$(cat "$PID_FILE")" 2>/dev/null || true
		kill "$(cat "$PID_FILE")" 2>/dev/null || true
		echo "Stopped mail flush loop"
	else
		echo "No mail flush loop of ours is running"
	fi
	rm -f "$PID_FILE"
}

cmd_status() {
	if running; then echo "flush loop: running (pid $(cat "$PID_FILE"))"; else echo "flush loop: stopped (scripts/dev-mail.sh start)"; fi
	if curl -fsS -o /dev/null --max-time 3 "$MAILPIT_API"; then echo "mailpit: up (inbox http://localhost:8025)"; else echo "mailpit: down (docker start mailpit)"; fi
	# `bench execute` prints nothing for a count of 0
	waiting="$(bench --site "$SITE" execute frappe.db.count --args '["Email Queue", {"status": "Not Sent"}]' 2>/dev/null | tail -1)"
	echo "mails waiting: ${waiting:-0}"
}

case "${1:-}" in
	start)  cmd_start ;;
	stop)   cmd_stop ;;
	status) cmd_status ;;
	once)   flush; echo "Flushed the mail queue once" ;;
	*) echo "usage: $0 start|stop|status|once" >&2; exit 2 ;;
esac
