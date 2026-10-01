#!/usr/bin/env bash
# The separate test site: every Python test run and every Playwright run that
# writes data belongs here, never on the dev site (kentender.midas.com).
#
#   scripts/test-site.sh rebuild --yes   copy the dev site into the test site (overwrites it)
#   scripts/test-site.sh serve           start the test site's own web server (port 8001)
#   scripts/test-site.sh stop            stop that server
#   scripts/test-site.sh status          is it up, and is the seeded world intact
#   scripts/test-site.sh run <command>   run <command> pointed at the test site
#
# Why a second server: Frappe picks a site from the request's Host header, and
# Node cannot resolve a second hostname here (no DNS entry, no /etc/hosts
# access). `bench --site X serve --port N` serves exactly one site whatever the
# Host header says, so the test site is simply http://127.0.0.1:8001.
set -euo pipefail

BENCH_ROOT="${BENCH_ROOT:-/home/midasuser/frappe-bench}"
DEV_SITE="${DEV_SITE:-kentender.midas.com}"
TEST_SITE="${TEST_SITE:-kentender-test.local}"
TEST_PORT="${TEST_PORT:-8001}"
PID_FILE="$BENCH_ROOT/logs/test-site-serve.pid"
LOG_FILE="$BENCH_ROOT/logs/test-site-serve.log"
BASE_URL="http://127.0.0.1:$TEST_PORT"

if [ "$TEST_SITE" = "$DEV_SITE" ]; then
	echo "TEST_SITE and DEV_SITE are the same site ($DEV_SITE); refusing." >&2
	exit 2
fi

CALLER_DIR="$PWD"
cd "$BENCH_ROOT"

up() { curl -fsS -o /dev/null --max-time 5 "$BASE_URL/api/method/ping"; }

cmd_serve() {
	if up; then echo "Test site already serving at $BASE_URL"; return 0; fi
	# nohup + closed stdin/stdout: a server whose output pipe dies turns every
	# frappe.throw into an HTML 500 (see the dev-server broken-pipe note).
	nohup bench --site "$TEST_SITE" serve --port "$TEST_PORT" > "$LOG_FILE" 2>&1 < /dev/null &
	echo $! > "$PID_FILE"
	for _ in $(seq 1 60); do
		if up; then echo "Test site serving at $BASE_URL (log: $LOG_FILE)"; return 0; fi
		sleep 1
	done
	echo "Test site did not come up within 60s; see $LOG_FILE" >&2
	exit 1
}

cmd_stop() {
	if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
		# `bench serve` forks; stop the whole group it leads.
		pkill -P "$(cat "$PID_FILE")" 2>/dev/null || true
		kill "$(cat "$PID_FILE")" 2>/dev/null || true
		echo "Stopped test site server"
	else
		echo "No test site server of ours is running"
	fi
	rm -f "$PID_FILE"
}

cmd_status() {
	if up; then echo "server: up at $BASE_URL"; else echo "server: down (scripts/test-site.sh serve)"; fi
	bench --site "$TEST_SITE" execute kentender_core.seeds.canonical.validate --kwargs '{"through": "award"}' 2>&1 | tail -1
}

cmd_rebuild() {
	if [ "${1:-}" != "--yes" ]; then
		echo "rebuild OVERWRITES the database and files of $TEST_SITE with a copy of $DEV_SITE." >&2
		echo "Re-run with --yes to confirm." >&2
		exit 2
	fi
	cmd_stop
	echo "== 1/6 backup $DEV_SITE"
	bench --site "$DEV_SITE" backup 2>&1 | tail -3
	local dump
	dump="$(ls -t "$BENCH_ROOT/sites/$DEV_SITE/private/backups/"*-database.sql.gz | head -1)"

	echo "== 2/6 site config (encryption key so stored passwords still decrypt; same feature flags)"
	python3 - "$DEV_SITE" "$TEST_SITE" <<'PY'
import json, sys
dev_site, test_site = sys.argv[1:3]
dev = json.load(open(f"sites/{dev_site}/site_config.json"))
path = f"sites/{test_site}/site_config.json"
test = json.load(open(path))
test["encryption_key"] = dev["encryption_key"]
for k in ("developer_mode", "server_script_enabled", "kt_bds_clarification_producer",
          "kt_bds_simulation_environment", "production_bid_submission_enabled",
          "std_config_ui_v2_enabled", "std_engine_allow_test_binding"):
	if k in dev:
		test[k] = dev[k]
test["maintenance_mode"] = 0
test.pop("domains", None)
json.dump(test, open(path, "w"), indent=1)
PY

	echo "== 3/6 restore database into $TEST_SITE"
	# Not `bench restore`: it asks for the MariaDB root password, which nobody
	# here has. The site's own database user owns this database, so empty it
	# and load the dump through that user. The password goes in MYSQL_PWD, not
	# on a command line.
	python3 - "$TEST_SITE" "$dump" <<'PY'
import gzip, json, os, shutil, subprocess, sys
site, dump = sys.argv[1:3]
cfg = json.load(open(f"sites/{site}/site_config.json"))
env = dict(os.environ, MYSQL_PWD=cfg["db_password"])
base = ["mariadb", "-u", cfg["db_user"], cfg["db_name"]]
tables = subprocess.run(base + ["-N", "-e", "show full tables where Table_type = 'BASE TABLE'"],
	env=env, capture_output=True, text=True, check=True).stdout.split("\n")
names = [line.split("\t")[0] for line in tables if line.strip()]
views = subprocess.run(base + ["-N", "-e", "show full tables where Table_type = 'VIEW'"],
	env=env, capture_output=True, text=True, check=True).stdout.split("\n")
stmts = ["SET FOREIGN_KEY_CHECKS=0;"]
stmts += [f"DROP VIEW IF EXISTS `{v.split(chr(9))[0]}`;" for v in views if v.strip()]
stmts += [f"DROP TABLE IF EXISTS `{n}`;" for n in names]
subprocess.run(base, env=env, input="\n".join(stmts), text=True, check=True)
print(f"emptied {len(names)} tables; loading {os.path.basename(dump)}")
loader = subprocess.Popen(base, env=env, stdin=subprocess.PIPE)
with gzip.open(dump, "rb") as src:
	shutil.copyfileobj(src, loader.stdin, 1 << 20)
loader.stdin.close()
if loader.wait() != 0:
	sys.exit("loading the dump failed")
print("database restored")
PY

	echo "== 4/6 copy attached files"
	mkdir -p "sites/$TEST_SITE/private/files" "sites/$TEST_SITE/public/files"
	rsync -a --delete "sites/$DEV_SITE/private/files/" "sites/$TEST_SITE/private/files/"
	rsync -a --delete "sites/$DEV_SITE/public/files/" "sites/$TEST_SITE/public/files/"

	echo "== 5/6 migrate + clear cache"
	bench --site "$TEST_SITE" migrate 2>&1 | tail -2
	bench --site "$TEST_SITE" clear-cache
	node "$BENCH_ROOT/apps/kentender_v1/tests/ui/helpers/queueCheck.cjs" --fix | tail -1

	echo "== 6/6 validate the canonical world"
	bench --site "$TEST_SITE" execute kentender_core.seeds.canonical.validate --kwargs '{"through": "award"}' 2>&1 | tail -1
}

cmd_run() {
	[ "$#" -gt 0 ] || { echo "usage: $0 run <command...>" >&2; exit 2; }
	cmd_serve >/dev/null
	# The command runs where the caller was (npx and make resolve things from there).
	cd "$CALLER_DIR"
	# SITE too: the Makefile's `SITE ?=` picks it up, so `run make <gate>` also
	# points the gates' own `bench --site $(SITE)` calls at the test site.
	export SITE="$TEST_SITE" UI_SITE="$TEST_SITE" UI_BASE_URL="$BASE_URL" TEST_SITE_ACTIVE=1
	exec "$@"
}

case "${1:-}" in
	rebuild) shift; cmd_rebuild "$@" ;;
	serve)   cmd_serve ;;
	stop)    cmd_stop ;;
	status)  cmd_status ;;
	run)     shift; cmd_run "$@" ;;
	*) sed -n '2,10p' "$0" >&2; exit 2 ;;
esac
