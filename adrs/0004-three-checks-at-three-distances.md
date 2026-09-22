# HW-0004: Three checks at three distances, and the standing one is rented

**Status:** Accepted

**Date:** 2026-09-22

## Context

No single health check can see every way this site fails, because the checks
that see the most are the ones most likely to be asleep.

A probe inside the container cannot see DNS, the proxy or TLS. A check from the
laptop sees all of those, but only when the laptop is awake — and a poll that is
asleep is silent in exactly the way a healthy site is, so its silence carries no
information. A hosted service is always on, and alerts when the poll itself
stops, which is a thing no self-run schedule can do for itself.

*What* is asked turns out to matter as much as from where. The external monitor
was first configured the obvious way — SSL plus a 2xx on `https://os.holdenweb.com`,
which is what uptime services offer by default. Measured on the lab with
`podman compose stop postgres`, the front page is a liar:

| | database up | database stopped |
| --- | --- | --- |
| `/` | 200 | 200 |
| `/pages/test` | 200 | 200 |
| `/login` | 200 | 200 |
| `/healthz` | 200 | **503** |

A monitor on the root reports green straight through a total database outage,
with login, sessions and password reset all broken behind a page that still
renders — "a green light that has been earned by asking the wrong question",
which is worse than no monitor in one specific way.

"Noticing that the site is down" was the oldest standing gap in the backlog,
carried since 2026-08-19, and until it closed everything else in `operations.md`
assumed somebody already knew something was wrong.

## Decision

The site decided two checks and inherited a third.

**Inherited, inside the container.** `container/healthcheck.py` polls
`127.0.0.1:8000/healthz` every ten seconds. It is podpack's, delivered verbatim
by the substrate along with the `healthcheck:` stanza that runs it; this site
chose neither. In this repository it *reports* rather than gates — nothing has
`depends_on: web: {condition: service_healthy}`, and `scripts/up.sh` ends
`podman compose up -d --build` with no `--wait`.

**At deploy time, from off the host.** `ops/poll-health.sh` runs from the
laptop, and asserts the body carries `"status":"ok"` rather than trusting the
status code, because nginx answers 200 from its own error page with the
container gone. `ops/deploy.sh` runs it after the rebuild for any target with a
health URL configured — today, staging (HW-0003).

**Between deploys, from the internet, rented.** A hosted service (UptimeRobot)
polls `https://os.holdenweb.com/healthz` every five minutes over HTTPS and mails
on failure. Not the site root: the measurement above settled that. Not a keyword
check either — `/healthz` puts the fatal verdict in the status code, so a plain
2xx test is exactly right once the URL is. The name is `/healthz`, no
underscore; `/_status` is the richer operator-only endpoint and is deliberately
not what is polled.

## Consequences

**A fatal failure is caught within five minutes from outside**, and that was
demonstrated against the real deployment rather than argued: postgres stopped by
hand, alert mail received. Recovery is unattended too — restarting it returned
`/healthz` to 200 in about three seconds.

**The degraded case is checked at deploy and not thereafter.** podpack ADR-0030
keeps `/healthz` at 200 for a non-fatal app failure by design, so the blog
reporting itself unhealthy raises no alert. Only `ops/poll-health.sh` asks the
body question, and it runs once per deploy. "A check at deploy time is not a
monitor. It answers whether this deploy came up, not whether the site is up now,
and between deploys nothing asks."

**The standing check is recorded but unverifiable from here.** `README.md`'s
Monitoring section documents the URL, the interval, the alerting and the
measurement behind the endpoint choice. What nothing in the tree can do is
confirm that the account still holds that check, or that it still points at
`/healthz` — the configuration lives with a third party. If it is ever
re-created, nothing stops it being pointed at the root again, which is what it
was the first time.

**One target is gated, not all.** `health_url()` is blank for production, so
the deploy-time check follows the site there only when that URL is filled in,
and a cutover means changing the target in two places: the monitor's dashboard
and `deploy.sh`.

**The dead-man's-switch property is argued, not observed.** A hosted service
alerting when its own poll stops is why it was chosen over a laptop cron;
nothing has yet watched it stop.

The on-host five-minute cron drafted in `operations.md` §18 remains uninstalled,
and for its own reason rather than this one: "it depends on §8 being done first:
the mail it sends goes through the same credential the site does."

## Alternatives considered

**A cron on the laptop running `poll-health.sh`** — what the script's own header
suggests. Rejected: "a laptop asleep at the polling minute is a blind monitor
whose silence is indistinguishable from health."

**A cron on the host.** Drafted in full in `operations.md` §18 and never
installed. It cannot see DNS, the proxy or a broken certificate, and it dies
with the machine it is watching.

**One check doing all three jobs.** Rejected because the inside and outside
checks catch opposite failures: a sick container that a proxy still fronts
convincingly, versus everything between a visitor and a perfectly healthy
container.

**A keyword check on `"status":"ok"` in the hosted monitor.** Considered and
judged unnecessary once the URL was right — a second way of getting the answer
the status code already gives. This is the one place where the standing monitor
is weaker than the deploy-time check, and the consequence is recorded above
rather than designed away.
