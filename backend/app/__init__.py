from .log_config import setup_logging

setup_logging()

from loguru import logger

from .api.server import run_app
from .constants import DATABASE_PATH, RUNTIME_DIR
from .database.orm import Database


def start() -> None:
    logger.info('Starting Redroom Maps backend')
    logger.info('Runtime data: {}', RUNTIME_DIR)
    logger.info('Database: {}', DATABASE_PATH)

    Database.set_alembic_revision()
    logger.info('Data version: {}', Database.data_version())
    run_app()
