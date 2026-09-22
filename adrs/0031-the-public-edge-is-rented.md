# HW-0031: The public edge is rented

**Status:** Accepted

**Date:** 2026-09-22

## Context

Something has to terminate TLS, own the public name, and hand requests to the
application. On a machine you control that is nginx or Caddy in a container, a
certificate to renew, a port 443 to bind, and a firewall to reason about.

This site runs on shared Opalstack hosting, where none of those are available
and all of them are provided. An "Nginx Proxy Port" application is allocated a
port; the platform terminates TLS, publishes the hostname, and proxies to that
port.

## Decision

The site owns nothing in front of itself.

It serves plain HTTP on loopback — `WEB_BIND_ADDR=127.0.0.1`, with
`WEB_HOST_PORT` set to whatever number the platform allocated. "`WEB_HOST_PORT`
is the one setting a managed host dictates", so deploying is a matter of putting
that number in `.env`.

Its only concession to being proxied is to believe `X-Forwarded-Proto`, and even
that is no longer a setting: podpack derives the trusted hop count from
`PODPACK_ENVIRONMENT`, so a non-local deployment builds `https://` URLs without
being told (podpack ADR-0039). `PODPACK_PROXY_HOPS` is set only for a second
proxy, or to `0` where a non-local target has nothing in front of it.

## Consequences

**Certificate renewal, the public DNS name and port 443 are somebody else's
problem**, and so is whatever they do about them. The site cannot see a
certificate expiring, which is one of the reasons the standing monitor is
external and asks over HTTPS (HW-0004): the check from outside is the only thing
that exercises the part the site does not own.

**The container is unreachable except through the proxy**, because it binds
loopback. That is a real security property and it is also why `ops/rebuild.sh`
and the integration suite need the public URL rather than the port.

**Believing `X-Forwarded-Proto` is a promise about the topology.** If
`WEB_BIND_ADDR` were ever widened, the site would be trusting a header that
anyone could then set — podpack ADR-0036 says so, and this record inherits the
warning: **a deployment that widens `WEB_BIND_ADDR` must revisit the hop count.**

**Moving off Opalstack is a real migration, not a config change.** The port
allocation, the proxy and the hostname would all become this site's to provide,
and `operations.md`'s host-move procedure is about moving between Opalstack
applications rather than off the platform.

**Two deployments on one host must be allocated different ports by hand.**
podpack ADR-0001 gives each its own compose project and image through
`SITE_NAME`, "but ports are not covered" — and here the number comes from the
platform, so the coordination is with Opalstack rather than within the estate.

## Alternatives considered

**Run our own nginx in a container and bind 443.** Not available on this
hosting, and not wanted if it were: it adds a certificate lifecycle to a
one-operator estate that currently has none.

**Serve gunicorn directly to the internet.** Rejected for the ordinary reasons —
no TLS, no static-file handling, no protection from slow clients — and
impossible here anyway.

**Cloudflare or a similar edge in front of the platform.** Not taken; it would
add a second hop to declare (podpack ADR-0039 covers the count) and a second
party to the outage-diagnosis conversation.
