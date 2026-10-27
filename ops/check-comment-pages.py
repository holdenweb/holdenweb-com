#!/usr/bin/env python3
"""Check the blog's comment pages as the site serves them (backlog item 41).

A comment page is decorated content, exactly like its post (blogscraper
ADR-0014). Before podpack-pages 0.3.5 nothing read the manifest's
`comment_pages`, so each was served as stored: no chrome, and its `${{{ROOT}}}`
links left for the browser to resolve against the page itself. This sweeps
every comment page the site's own `/blog/manifest.json` lists and checks what
decoration should have done:

  * it answers 200, unredirected, with no placeholder left and the site's
    chrome -- the masthead and the archive subnav;
  * its h1 is "Comments on <post>", plus ", page N of M" when the thread has
    several, and the archive marks the post's year current;
  * it links to exactly its neighbouring pages, and back to its post.

Each post must link to its first comment page, the index must list none of
them, and anything else on the same host that they link to must answer 200.

The title and year expected come from the post's own page, not the manifest,
because the manifest is not the whole story: a post with a null title renders
as "Untitled post", and the archive year is the post's date, which can differ
from the year in its path. Matching the manifest alone flagged three good pages
on the first sweep.

--stored takes each comment page from the export tree instead of the site --
the page exactly as the site served it before 0.3.5. Every one should then fail,
and the run exits 0 only if every one does: a page that passes is one on which
the check cannot see the bug. The default tree is the one `just blog` publishes
($SITESCRAPER_BUILD, else ~/Projects/Python/blogscraper/build).

    python3 ops/check-comment-pages.py https://os.holdenweb.com
    python3 ops/check-comment-pages.py https://os.holdenweb.com --stored [DIR]
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import urldefrag, urljoin, urlsplit

# The tree `just blog` publishes, found by the same rule as the justfile's.
EXPORT = Path(os.environ.get("SITESCRAPER_BUILD",
                             Path.home() / "Projects/Python/blogscraper/build"))

# Four requests at a time: quick enough, and gentle on a small host.
WORKERS = 4

Page = tuple[int, bool, str]                  # status, redirected, body


def fetch(url: str) -> Page:
    request = urllib.request.Request(url, headers={"User-Agent": "check-comment-pages"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            # A redirect would pass a moved page off as a 200, so say so.
            return (response.status, response.geturl() != url,
                    response.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        return e.code, False, ""              # a finding, which the caller reports


def stored(root: Path, path: str) -> Page:
    """A comment page as the export holds it -- as served before 0.3.5."""
    return 200, False, (root / path).read_text()


def h1_text(body: str) -> str | None:
    h1 = re.search(r'<h1 class="title">(.*?)</h1>', body, re.S)
    return html.unescape(h1.group(1)).strip() if h1 else None


def archive_current(body: str) -> list[str]:
    return re.findall(r'aria-current="page">(\d{4})<', body)


def content_links(url: str, body: str) -> set[str]:
    """Same-host links after the h1: the chrome's own links are site-wide."""
    content = body.split('<h1 class="title">', 1)[-1]
    found = (urldefrag(urljoin(url, html.unescape(href)))[0]
             for href in re.findall(r'href="([^"]*)"', content))
    host = urlsplit(url).netloc
    return {link for link in found if urlsplit(link).netloc == host}


def page_problems(page: Page) -> list[str]:
    status, moved, body = page
    if status != 200:
        return [f"status {status}"]
    problems = ["redirected"] if moved else []
    if "{{{" in body or "%7b%7b%7b" in body.lower():
        problems.append("placeholder left in page")
    if '<header class="masthead">' not in body or '<aside class="subnav">' not in body:
        problems.append("no chrome")
    return problems


def comment_problems(page: Page, thread: list[str], n: int, post: str,
                     title: str | None, year: str | None) -> tuple[list[str], set[str]]:
    """Page n (from 1) of `thread`, its post's comment pages as absolute URLs.

    `title` and `year` are the post's own, as its page renders them.
    """
    problems = page_problems(page)
    if page[0] != 200:
        return problems, set()
    body = page[2]
    want = f"Comments on {title}" + (f", page {n} of {len(thread)}" if len(thread) > 1 else "")
    if (got := h1_text(body)) != want:
        problems.append(f"title {got!r}, wanted {want!r}")
    if (current := archive_current(body)) != [year]:
        problems.append(f"archive marks {current} current, wanted {[year]}")
    links = content_links(thread[n - 1], body)
    neighbours = {thread[k] for k in (n - 2, n) if 0 <= k < len(thread)}
    # Anything under the thread's directory, not just its listed pages, so a
    # failure shows where the links went -- for a placeholder left unfilled,
    # the very URL the browser was given.
    directory = thread[0].rsplit("/", 1)[0] + "/"
    if (linked := {link for link in links if link.startswith(directory)}) != neighbours:
        problems.append(f"thread links {sorted(linked)}, wanted {sorted(neighbours)}")
    if post not in links:
        problems.append("no link back to the post")
    return problems, links


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("site", help="the site's root URL, e.g. https://os.holdenweb.com")
    parser.add_argument("--stored", nargs="?", const=EXPORT, type=Path, metavar="DIR",
                        help="take the comment pages from this export tree instead, "
                             "and expect every one to fail (default: the tree "
                             "`just blog` publishes)")
    args = parser.parse_args()

    blog = args.site.rstrip("/") + "/blog/"
    status, _, body = fetch(blog + "manifest.json")
    if status != 200:
        print(f"{blog}manifest.json: status {status}", file=sys.stderr)
        return 1
    threads = [post for post in json.loads(body)["posts"] if post.get("comment_pages")]
    if not threads:
        # Nothing to check is not a failure, but it is not a clean sweep either.
        print(f"{blog}manifest.json lists no comment pages: nothing checked")
        return 0

    urls = {post["path"]: [urljoin(blog, path) for path in post["comment_pages"]]
            for post in threads}
    jobs = [(post, n) for post in threads for n in range(1, len(urls[post["path"]]) + 1)]
    if args.stored:
        # A page missing from the tree would fail too, and for the wrong reason:
        # a wrong DIR once passed this way without reading a single stored page.
        missing = [post["comment_pages"][n - 1] for post, n in jobs
                   if not (args.stored / post["comment_pages"][n - 1]).is_file()]
        if missing:
            print(f"{args.stored} lacks {len(missing)} of the {len(jobs)} comment pages "
                  f"the site lists, e.g. {missing[0]} -- is it the export the site "
                  f"serves?", file=sys.stderr)
            return 1
    with ThreadPoolExecutor(WORKERS) as pool:
        posted = list(pool.map(fetch, [urljoin(blog, post["path"]) for post in threads]))
        if args.stored:
            pages = [stored(args.stored, post["comment_pages"][n - 1]) for post, n in jobs]
        else:
            pages = list(pool.map(fetch, [urls[post["path"]][n - 1] for post, n in jobs]))

    failures: list[str] = []
    expected: dict[str, tuple[str | None, str | None]] = {}
    for post, page in zip(threads, posted):
        url = urljoin(blog, post["path"])
        problems = page_problems(page)
        if urls[post["path"]][0] not in content_links(url, page[2]):
            problems.append("no link to its first comment page")
        failures += [f"{url} (post): {p}" for p in problems]
        current = archive_current(page[2])
        expected[post["path"]] = (h1_text(page[2]), current[0] if len(current) == 1 else None)

    passing: list[str] = []
    targets: set[str] = set()
    samples: dict[bool, tuple[str, list[str], str | None]] = {}
    for (post, n), page in zip(jobs, pages):
        thread = urls[post["path"]]
        problems, links = comment_problems(page, thread, n, urljoin(blog, post["path"]),
                                           *expected[post["path"]])
        failures += [f"{thread[n - 1]}: {p}" for p in problems]
        if not problems:
            passing.append(thread[n - 1])
        targets |= links
        samples.setdefault(len(thread) > 1, (thread[n - 1], problems, h1_text(page[2])))

    if args.stored:
        # The question here is not whether the pages are right -- they are not --
        # but whether the check can tell.
        print(f"{len(jobs)} comment pages across {len(threads)} posts, "
              f"taken as stored from {args.stored}")
        if passing:
            print(f"{len(passing)} pass -- the check cannot see the bug on these:")
            for url in passing[:40]:
                print("  ", url)
            return 1
        url, problems, _ = samples.get(True) or samples[False]
        print(f"every one fails, as it should -- {url}, for one:")
        for p in problems:
            print("  ", p)
        return 0

    every = {url for thread in urls.values() for url in thread}
    index = fetch(blog)
    failures += [f"{blog} (index): {p}" for p in page_problems(index)]
    if listed := content_links(blog, index[2]) & every:
        failures.append(f"{blog} (index): lists {len(listed)} comment page(s)")

    # Everything above was fetched already; what is left is whatever else on
    # this host the comment pages link to.
    rest = sorted(targets - every - {urljoin(blog, post["path"]) for post in threads})
    with ThreadPoolExecutor(WORKERS) as pool:
        for url, (status, moved, _) in zip(rest, pool.map(fetch, rest)):
            if status != 200 or moved:
                failures.append(f"{url} (linked): status {status}"
                                + (", redirected" if moved else ""))

    print(f"{len(jobs)} comment pages across {len(threads)} posts at {blog}, "
          f"and {len(rest)} other page(s) they link to")
    for multi in sorted(samples):
        print(f"  e.g. {samples[multi][2]!r}")
    print(f"failures: {len(failures)}")
    for failure in failures[:40]:
        print("  ", failure)
    if len(failures) > 40:
        print(f"   ... and {len(failures) - 40} more")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
