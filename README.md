# holdenweb.com

The code for the web site.

### Run the site locally

    uv run python wsgi.py

### Database schema changes

Schema is managed with Alembic against the `Role`/`User` models defined in
`holdenweb/__init__.py`. `alembic/env.py` reads the DB URL from the
`SQLALCHEMY_DATABASE_URI` env var (the same one the app itself uses), so
alembic and the running app can never point at different databases.

    uv run alembic revision --autogenerate -m "describe the change"
    uv run alembic upgrade head

The first time you point alembic at an existing database, use
`uv run alembic stamp head` after reviewing the generated baseline migration,
so alembic records the current schema as already applied instead of trying
to recreate it.

### Distributing to Opalstack

Check the current release number,

    sholden@overhead qs-holdenweb.com % release
    1.0.0-alpha2

Make sure the release is clean (check everything in or stash uncommitted changes).

    sholden@overhead qs-holdenweb.com % git add -u && git commit
    [main 7e0da7f] mplement a 404 page and add a blue bar at the top.
    5 files changed, 35 insertions(+), 3 deletions(-)

Next,call `release` with the new version number
(_TODO: implement a `--bump` option).

    sholden@overhead qs-holdenweb.com % release 1.0.0-alpha3
    Starting release process for holdenweb r1.0.0-alpha3
    Resolved 19 packages in 202ms
    Updated holdenweb v1.0.0a2 -> v1.0.0a3
    [main 25e0c73] Release r1.0.0-alpha3
     3 files changed, 3 insertions(+), 3 deletions(-)
    Building source distribution...
    Building wheel from source distribution...
    Successfully built dist/holdenweb-1.0.0a3.tar.gz
    Successfully built dist/holdenweb-1.0.0a3-py3-none-any.whl

Once you've created the release, it can be deployed to any Python/uWSGI application.



