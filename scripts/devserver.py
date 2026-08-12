"""A local development server for the podpack-based site.

SQLite and throwaway secrets, exported *before* the app loads `.env` --
`load_dotenv` does not override variables that are already set, so this never
touches the production database named there. `db.create_all` stands in for
alembic: schema authoring is the site's job, not a dev server's.

Run with: uv run python scripts/devserver.py
"""

import os

os.environ.setdefault("SECRET_KEY", "dev-only")
os.environ.setdefault("SECURITY_PASSWORD_SALT", "dev-only-salt")
os.environ["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/holdenweb-dev.db"
os.environ.setdefault("PODPACK_CONFIG", "config/app.toml")
os.environ.setdefault("PODPACK_DATA_ROOT", "./hostdata/apps")
os.environ.setdefault("PODPACK_LOG_ROOT", "./hostlogs/apps")

from holdenweb import create_app  # noqa: E402
from podpack import db  # noqa: E402

app = create_app()
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    # 8456 is the production container's local port; stay clear of it.
    app.run(port=8460, debug=False)
