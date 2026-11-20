from .database.orm import Database


def migrate() -> None:
    Database.set_alembic_revision()


if __name__ == '__main__':
    migrate()
