# Recipes for holdenweb.com.
#
# ---- content deployment -----------------------------------------------------
#
# podpack-pages serves three content trees on this site, each from
# hostdata/apps/<app>/<tree>:
#
#     pybooks    html-pages   the Python course books (orpy `build.py --fragments`)
#     blog       export       the blog (blogscraper `python -m blogscraper export`)
#     notebooks  html-pages   Jupyter notebooks (podpack-notebooks `build.py`)
#     pages      md-pages     the site's prose pages: no builder, because the
#                html-pages   source is written by hand in ~/sites/holdenweb-content
#
# The first three are another repository's build output and can be regenerated;
# the prose cannot, which is why it has a repository rather than a build step.
#
# A tree is refreshed by ops/refresh-content.sh (on the box that runs the site)
# or ops/push-content.sh (to a remote target). These recipes wrap that pair so
# updating a tree to local / staging / production is one line, e.g.
#
#     just pybooks staging            # merge the orpy build into staging's pybooks
#     just blog staging --mirror      # replace staging's blog with the export
#     just pybooks local              # refresh the local dev instance
#     just blog staging --dry-run     # show the plan, change nothing
#
# `local` refreshes this checkout's own hostdata via ops/refresh-content.sh;
# `staging`/`production` push to the matching git remote via ops/push-content.sh
# (production has no remote yet, so it errors until one is added). --mirror and
# --dry-run go to whichever of those two runs, and both understand both:
# --mirror removes whatever the source no longer has, asking you to type
# `mirror` first whenever a terminal is there to answer, and --dry-run prints
# the plan and changes nothing. Default is a safe MERGE; ask for --mirror when
# you mean it, and --dry-run first if you are not certain what it will take.
#
#     just pages staging              # publish the prose from holdenweb-content
#
# Sources default to where each builder writes on the laptop, and for `pages` to
# the content repository; override the env var if yours differ, e.g.
# ORPY_BUILD=/somewhere just pybooks staging, PAGES_SOURCE=/somewhere just pages.

set shell := ["bash", "-uc"]

orpy        := env_var_or_default("ORPY_BUILD", home_directory() / "Projects/Python/orpy/python-classes")
blogscraper := env_var_or_default("SITESCRAPER_BUILD", home_directory() / "Projects/Python/blogscraper/build")
notebooks   := env_var_or_default("NOTEBOOKS_BUILD", home_directory() / "sites/podpack-notebooks/build/html-pages")

# PAGES_SOURCE, not PAGES_BUILD: the three above name a builder's output, this
# names authored source. ~/sites/holdenweb-content is a repository of its own,
# so the prose is version-controlled and the served tree is a copy of it --
# which it was not until 2026-10-16, when the served tree was the only copy
# anywhere.
pages_src   := env_var_or_default("PAGES_SOURCE", home_directory() / "sites/holdenweb-content/pages")

# List the recipes.
default:
    @just --list

# The Python course books: orpy fragments -> the pybooks app's html-pages tree.
pybooks target="staging" *flags:
    @just _content "{{ target }}" "{{ orpy }}" pybooks html-pages {{ flags }}

# The blog: the blogscraper export -> the blog app's export tree.
blog target="staging" *flags:
    @just _content "{{ target }}" "{{ blogscraper }}" blog export {{ flags }}

# Run after `just blog`, since a fresh export is the next thing that could undo
# backlog 41: it checks that the comment pages still come out decorated like
# their posts. staging and production name their public sites; any other is
# given by URL. With --stored [DIR] it takes the pages from the export as stored
# instead -- DIR defaults to the export above -- and passes only if every one
# fails, which proves the check can see the bug. ops/check-comment-pages.py has
# the detail.

# The blog's comment pages, checked as a target serves them.
check-comments target="staging" *flags:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{ justfile_directory() }}"
    case "{{ target }}" in
      staging)    site=https://os.holdenweb.com ;;
      production) site=https://holdenweb.com ;;
      http://*|https://*) site="{{ target }}" ;;
      *)
        echo "target must be staging, production or a site URL, not '{{ target }}'" >&2
        exit 1 ;;
    esac
    python3 ops/check-comment-pages.py "$site" {{ flags }}

# The notebooks: podpack-notebooks build.py output -> the notebooks app's html-pages tree.
notebooks target="staging" *flags:
    @just _content "{{ target }}" "{{ notebooks }}" notebooks html-pages {{ flags }}

# Two pushes below, because the pages app serves md-pages and html-pages as one
# namespace while refresh-content.sh refreshes one tree per run. --mirror
# therefore prunes each tree against its own source, which is what you want; it
# would be wrong only if the two were ever merged into one tree.

# The prose pages: holdenweb-content -> the pages app's two trees.
pages target="staging" *flags:
    @just _content "{{ target }}" "{{ pages_src }}/md-pages"   pages md-pages   {{ flags }}
    @just _content "{{ target }}" "{{ pages_src }}/html-pages" pages html-pages {{ flags }}

# docs -- every generated document, rebuilt.
#
# Six outputs from four sources. Three have generators of their own here; the
# browser copies are mdhtml, which until now lived only in shell history -- the
# gap HW-0022 records, and how ops/messages.html came to be destroyed by a
# render of its own markdown view on 2026-10-16.
#
# Safe to run at any time: every generator rebuilds its output from scratch, so
# the only thing a needless run costs is a date stamp -- build-messages.py
# writes today's date into messages.html, so `git diff` will show that one line
# even when no message changed. Revert it rather than committing the churn.
#
# all_adrs.md is NOT built here. It looks like a concatenation of adrs/*.md, it
# is untracked, and it is stale -- 34 records against 37 files, so it predates
# HW-0035 and HW-0036 -- but nothing in this repository produces it and
# guessing its order and separators would be inventing a generator rather than
# recording one.

# Regenerate every document built from a source file in this repository.
docs: still-to-do render-messages
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{ justfile_directory() }}"
    python3 ops/render-rebuild.py > ops/rebuild.html
    echo "  ops/rebuild.html          <- ops/rebuild.md"
    ./ops/build-messages.py | sed 's/^/  /'
    mdhtml --noview -o ops/DEPLOY.html ops/DEPLOY.md >/dev/null
    echo "  ops/DEPLOY.html           <- ops/DEPLOY.md"
    mdhtml --noview -o README.html README.md >/dev/null
    echo "  README.html               <- README.md"

# Any tree: `just content <target> <source-dir> <app> <tree> [--mirror|--dry-run]`.
content target dir app tree *flags:
    @just _content "{{ target }}" "{{ dir }}" "{{ app }}" "{{ tree }}" {{ flags }}

# Dispatcher: local -> refresh-content.sh here; remote -> push-content.sh.
_content target dir app tree *flags:
    #!/usr/bin/env bash
    set -euo pipefail
    cd "{{ justfile_directory() }}"
    if [[ ! -d "{{ dir }}" ]]; then
        echo "no such source directory: {{ dir }}" >&2
        echo "(set the matching build-source env var if the builder writes elsewhere)" >&2
        exit 1
    fi
    case "{{ target }}" in
      local)
        APP="{{ app }}" TREE="{{ tree }}" ops/refresh-content.sh "{{ dir }}" {{ flags }} ;;
      staging|production)
        ops/push-content.sh "{{ target }}" "{{ dir }}" --app "{{ app }}" --tree "{{ tree }}" {{ flags }} ;;
      *)
        echo "target must be local, staging or production, not '{{ target }}'" >&2
        exit 1 ;;
    esac

# ---- run secure locally -----------------------------------------------------

run-secure:
    SECRET_KEY=dev-only SECURITY_PASSWORD_SALT=dev-only-salt \
    SQLALCHEMY_DATABASE_URI=sqlite:////tmp/holdenweb-dev.db \
    PODPACK_CONFIG=config/app.toml \
    PODPACK_DATA_ROOT=./hostdata/apps PODPACK_LOG_ROOT=./hostlogs/apps \
    MAIL_PASSWORD=abcdefghijklmnop \
    uv run flask --app holdenweb run \
        --cert ~/.ssh/certs/in-hw-cert.pem  \
        --key ~/.ssh/certs/in-hw-key.pem
    
# ---- housekeeping -----------------------------------------------------------

# backlog.md is the record and is append-only, which makes it the wrong thing to
# read when you only want what is left. This extracts that, deriving the open set
# from the summary table rather than from any list kept here -- so an item marked
# **fixed** there simply stops appearing, and this recipe needs no maintenance.
# `just still-to-do --check` reports whether the file is stale without writing it.
#
# (Blank line below on purpose: just shows the last line of the comment block
# immediately above a recipe as its --list description.)

# The open backlog items -> ops/records/still_to_do.md.
still-to-do *flags:
    @python3 ops/open-backlog.py {{ flags }}

# The output name below is explicit because the obvious one destroys a generated
# file. mdhtml defaults its output to "the first source, with a .html suffix",
# so `mdhtml ops/MESSAGES.md` writes ops/MESSAGES.html -- and this filesystem
# is case-insensitive, so that IS ops/messages.html, the searchable page
# build-messages.py generates (HW-0026). It was overwritten exactly that way on
# 2026-10-16 and had to be restored from git. The two differ only in case, and
# nothing warns.
#
# `md-messages` rather than `MESSAGES`: the one name that cannot collide with
# the generated page no matter how the filesystem compares case.

# The almanac's markdown view, rendered for a browser -> ops/md-messages.html.
render-messages *flags:
    @mdhtml -o ops/md-messages.html ops/MESSAGES.md {{ flags }}
    @echo "wrote ops/md-messages.html -- ops/messages.html is the generated one, left alone"

clean:
    rm -f kill port_no start stop
    find . -name __pycache__ -exec rm -rf {} \; -prune
