from contextlib import contextmanager
from pathlib import Path

from alembic.command import upgrade
from alembic.config import Config as AlembicConfig
from loguru import logger
from sqlalchemy import create_engine, orm
from sqlalchemy.orm import Session

from ..constants import DATABASE_PATH, HISTORY_GROUPS_PATH


_BACKEND_DIR = Path(__file__).resolve().parents[2]
_DATABASE_PATH = DATABASE_PATH
_ALEMBIC_CONFIG = _BACKEND_DIR / 'alembic.ini'
_CONNECTION_STRING = f'sqlite:///{_DATABASE_PATH}?check_same_thread=False'


class Database:
    _engine = create_engine(_CONNECTION_STRING, echo=False)
    _session_factory = orm.scoped_session(
        orm.sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine,
        ),
    )

    @staticmethod
    def set_alembic_revision(revision_name: str = 'head'):
        alembic_cfg = AlembicConfig(str(_ALEMBIC_CONFIG))
        logger.info('Applying Alembic migrations (revision={})', revision_name)
        with Database._engine.begin() as connection:
            alembic_cfg.attributes['connection'] = connection
            upgrade(config=alembic_cfg, revision=revision_name)
        logger.info('Alembic migrations are up to date')

    @staticmethod
    def data_version() -> str:
        """Return a value that changes whenever the database is modified."""
        latest = 0
        total_size = 0

        # The main file and the WAL are enough: any committed write updates
        # at least one of them.
        for path in (
            _DATABASE_PATH,
            Path(f'{_DATABASE_PATH}-wal'),
        ):
            try:
                stat = path.stat()
            except OSError:
                continue

            latest = max(latest, stat.st_mtime_ns)
            total_size += stat.st_size

        try:
            groups_stat = HISTORY_GROUPS_PATH.stat()
            groups_version = (
                f'{groups_stat.st_mtime_ns}-{groups_stat.st_size}'
            )
        except OSError:
            groups_version = '0-0'

        return f'{latest}-{total_size}-{groups_version}'

    @staticmethod
    @contextmanager
    def session():
        session: Session = Database._session_factory()
        try:
            yield session
        except Exception as error:
            logger.exception(
                'Session rollback because of exception ({}): {}',
                error.__class__.__name__,
                error,
            )
            session.rollback()
            raise
        finally:
            session.close()
