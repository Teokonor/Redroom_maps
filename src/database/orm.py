import os
from contextlib import contextmanager

from loguru import logger
from sqlalchemy import create_engine, orm
from sqlalchemy.orm import Session
from alembic.config import Config as AlembicConfig
from alembic.command import upgrade

from .abs import Base


__CONNSTRING__ = f'sqlite:///{os.path.join(os.getcwd(), "redroom_maps.db")}?check_same_thread=False'


class Database:
    _engine = create_engine(__CONNSTRING__, echo=False)
    _session_factory = orm.scoped_session(
        orm.sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=_engine
        ),
    )
    
    
    @staticmethod
    def set_alembic_revision(revision_name: str = 'head'):
        alembic_cfg = AlembicConfig("alembic.ini")
        with Database._engine.begin() as connection:
            alembic_cfg.attributes['connection'] = connection
            upgrade(config=alembic_cfg, revision=revision_name)


    @staticmethod
    @contextmanager
    def session():
        session: Session = Database._session_factory()
        try:
            yield session
        except Exception as error:
            logger.error(f'Session rollback because of exception ({error.__class__.__name__}): {error}')
            session.rollback()
            raise
        finally:
            session.close()
