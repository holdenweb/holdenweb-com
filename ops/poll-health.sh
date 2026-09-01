#!/usr/bin/env bash
# External liveness poll for the podpack site, run from a machine that is NOT
# the host -- so it sees what a visitor sees: DNS, the proxy, TLS and the app
# together. The on-host probe (container/healthcheck.py) catches the opposite
# case, a sick container behind a proxy still answering convincingly; this
# catches everything between a visitor and the container. operations.md section
# 18 is the argument for both.
#
# It asserts the body, not just the status. nginx will return 200 from its own
# error page with the container gone, so a 200 alone is not health -- the
# JSON's "status":"ok" is. TLS expiry is not checked on its own: Opalstack
# renews certificates automatically, and curl over https fails on a bad
# certificate anyway, so a real TLS failure already trips the fetch below.
#
# Exit 0 and say nothing on success, so a scheduler only ever mails on a
# genuine failure. Exit non-zero with a message on stderr otherwise. Set
# ALERT_CMD to send that message somewhere of your own (a notifier, a webhook
# poster, mail); leave it unset to rely on cron/launchd mailing job output.
#
# The target is the running podpack instance. It is a variable so this same
# script follows the site to production after a cutover:
#   HEALTH_URL=https://holdenweb.com/healthz ./ops/poll-health.sh
set -euo pipefail

URL="${HEALTH_URL:-https://os.holdenweb.com/healthz}"
TIMEOUT="${HEALTH_TIMEOUT:-15}"
EXPECT='"status":"ok"'
[ -n "${HEALTH_EXPECT:-}" ] && EXPECT="$HEALTH_EXPECT"

fail() {
  # date -u +%FT%TZ, not `date -Is`: this runs on a macOS laptop, whose BSD
  # date has no -I. UTC so a stamp means one instant wherever it is read.
  msg="$(date -u +%FT%TZ): health check FAILED for ${URL} -- $1"
  [ -n "${ALERT_CMD:-}" ] && printf '%s\n' "$msg" | ${ALERT_CMD} || true
  printf '%s\n' "$msg" >&2
  exit 1
}

# -f: a non-2xx status is a failure. --max-time: a hang is a failure too, not a
# process that sits wedged until the next run steps on it.
body="$(curl -fsS --max-time "$TIMEOUT" "$URL")" \
  || fail "no 200 (DNS, TLS, the proxy, or the container is down)"

case "$body" in
  *"$EXPECT"*) : ;;
  *) fail "200 but body lacks ${EXPECT} (the proxy answered; the app or database did not)" ;;
esac

exit 0
