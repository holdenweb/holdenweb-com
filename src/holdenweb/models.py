"""The site's own schema: the flask-security user and role tables.

The registry imports this module while installing the `holdenweb` app, so
these models reach `db.metadata` -- and therefore alembic -- the same way any
installed app's do.
"""

from flask_security import SQLAlchemyUserDatastore
from flask_security.models import fsqla_v3 as fsqla

from podpack import db

fsqla.FsModels.set_db_info(db)


class Role(db.Model, fsqla.FsRoleMixin):  # type: ignore[name-defined]
    pass


class User(db.Model, fsqla.FsUserMixin):  # type: ignore[name-defined]
    pass


user_datastore = SQLAlchemyUserDatastore(db, User, Role)
