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
#     pages      html-pages   the site's prose pages (maintained on the host today;
#                             no laptop builder, so no named recipe -- use `content`)
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
# Sources default to where each builder writes on the laptop; override the env
# var if yours differ, e.g. ORPY_BUILD=/somewhere just pybooks staging.

set shell := ["bash", "-uc"]

orpy        := env_var_or_default("ORPY_BUILD", home_directory() / "Projects/Python/orpy/python-classes")
blogscraper := env_var_or_default("SITESCRAPER_BUILD", home_directory() / "Projects/Python/blogscraper/build")
notebooks   := env_var_or_default("NOTEBOOKS_BUILD", home_directory() / "sites/podpack-notebooks/build/html-pages")

# List the recipes.
default:
    @just --list

# The Python course books: orpy fragments -> the pybooks app's html-pages tree.
pybooks target="staging" *flags:
    @just _content "{{ target }}" "{{ orpy }}" pybooks html-pages {{ flags }}

# The blog: the blogscraper export -> the blog app's export tree.
blog target="staging" *flags:
    @just _content "{{ target }}" "{{ blogscraper }}" blog export {{ flags }}

# The notebooks: podpack-notebooks build.py output -> the notebooks app's html-pages tree.
notebooks target="staging" *flags:
    @just _content "{{ target }}" "{{ notebooks }}" notebooks html-pages {{ flags }}

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

clean:
    rm -f kill port_no start stop
    find . -name __pycache__ -exec rm -rf {} \; -prune
