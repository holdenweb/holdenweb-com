# qs-holdenweb.com

The code for the web site.

### Run the site locally

    uv run python wsgi.py

### Distributing to Opalstack

Check the current release number,

    sholden@overhead release % release
    0.2.2a1

Make sure the release is clean (check everything in or stash uncommitted changes) and call `release` with the new version number
(_TODO: implement a `--bump` option).

    Starting release process for release r0.2.2a2
    Resolved 4 packages in 1ms
    Updated release v0.2.2a1 -> v0.2.2a2
    [main 8b86715] Release r0.2.2a2
     3 files changed, 3 insertions(+), 3 deletions(-)
    Building source distribution...
    Building wheel from source distribution...
    Successfully built dist/release-0.2.2a2.tar.gz
    Successfully built dist/release-0.2.2a2-py3-none-any.whl

Once you've created the release, it can be deployed to any Python/uWSGI application.

