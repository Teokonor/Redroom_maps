from .api.server import run_app
from .database.orm import Database


def start():
    Database.set_alembic_revision()
    run_app()
