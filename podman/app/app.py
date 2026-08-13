"""A small Flask app whose only job is to prove the container plumbing works.

It exercises each of the three things the suite is supposed to get right:

* it reads its non-secret settings from a host-mounted, read-only TOML file,
* it reads its secrets and wiring from the environment,
* it writes both to MongoDB and to a host-mounted directory, so you can kill
  the containers and confirm the data is still there afterwards.
"""

import logging
import os
import pathlib
import tomllib
from datetime import datetime, timezone

from flask import Flask, jsonify, request
from pymongo import MongoClient
from pymongo.errors import PyMongoError

CONFIG_PATH = pathlib.Path(os.environ.get("APP_CONFIG", "/etc/holdenweb/app.toml"))
UPLOAD_DIR = pathlib.Path(os.environ.get("APP_UPLOAD_DIR", "/var/lib/holdenweb/uploads"))
LOG_DIR = pathlib.Path(os.environ.get("APP_LOG_DIR", "/var/log/holdenweb"))


def load_host_config(path=CONFIG_PATH):
    """Read the host-supplied TOML config, failing loudly if it is missing.

    Refusing to start beats starting with silent defaults: a missing file here
    means the bind mount is wrong, which is exactly what this lab exists to
    catch before the same compose file reaches a real host.
    """
    if not path.is_file():
        raise RuntimeError(
            f"host configuration not mounted at {path} -- check the "
            "./config bind mount in compose.yaml"
        )
    with path.open("rb") as stream:
        return tomllib.load(stream)


def require_env(name):
    try:
        return os.environ[name]
    except KeyError:
        raise RuntimeError(f"required environment variable {name} is not set") from None


def create_app():
    app = Flask(__name__)
    host_config = load_host_config()

    app.config["SECRET_KEY"] = require_env("SECRET_KEY")
    app.config["HOST_CONFIG"] = host_config
    app.config["MAX_CONTENT_LENGTH"] = host_config["limits"]["max_upload_bytes"]

    client = MongoClient(require_env("MONGO_URI"), serverSelectionTimeoutMS=3000)
    db = client.get_default_database()

    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    _add_file_logging(app)

    @app.get("/healthz")
    def healthz():
        """Liveness *and* readiness: the app is no use without its database."""
        try:
            db.command("ping")
        except PyMongoError as exc:
            return jsonify(status="unhealthy", mongo=str(exc)), 503
        return jsonify(status="ok", mongo="ok")

    @app.get("/")
    def index():
        """Report where every piece of the app's state actually lives."""
        return jsonify(
            site=host_config["site"],
            config_source=str(CONFIG_PATH),
            upload_dir=str(UPLOAD_DIR),
            upload_dir_writable=os.access(UPLOAD_DIR, os.W_OK),
            mongo_database=db.name,
            note_count=db.notes.count_documents({}),
            stored_files=sorted(p.name for p in UPLOAD_DIR.iterdir() if p.is_file()),
        )

    @app.get("/notes")
    def list_notes():
        limit = host_config["limits"]["notes_page_size"]
        notes = db.notes.find({}, {"_id": False}).sort("created", -1).limit(limit)
        return jsonify(notes=list(notes))

    @app.post("/notes")
    def add_note():
        """Persist a note in Mongo, i.e. in the host-mapped data directory."""
        text = (request.get_json(silent=True) or {}).get("text", "").strip()
        if not text:
            return jsonify(error="a non-empty 'text' field is required"), 400
        note = {"text": text, "created": datetime.now(timezone.utc).isoformat()}
        # insert_one() adds an ObjectId `_id` to the dict it is given, and
        # ObjectId is not JSON-serialisable -- so report the copy, not the
        # document that pymongo has stamped.
        result = db.notes.insert_one(dict(note))
        app.logger.info("stored note of %d characters", len(text))
        return jsonify(stored=note, id=str(result.inserted_id)), 201

    @app.post("/uploads/<name>")
    def store_file(name):
        """Persist a file in the host-mapped uploads directory."""
        target = UPLOAD_DIR / pathlib.Path(name).name
        target.write_bytes(request.get_data())
        return jsonify(stored=target.name, bytes=target.stat().st_size), 201

    return app


def _add_file_logging(app):
    """Log to the host-mounted log directory as well as to stdout.

    Container stdout is the right default, but production hosts here keep
    their own logs, so this proves the log bind mount is writable too.
    """
    try:
        LOG_DIR.mkdir(parents=True, exist_ok=True)
        handler = logging.FileHandler(LOG_DIR / "app.log")
    except OSError as exc:
        app.logger.warning("file logging disabled: %s", exc)
        return
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(process)d] %(message)s")
    )
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
