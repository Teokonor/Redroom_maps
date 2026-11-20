from __future__ import annotations

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import String, Integer

from .abs import Base
from .orm import Database


class CountryModel(Base):
    __tablename__ = 'countries'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    begin_year: Mapped[int] = mapped_column(Integer)
    end_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    owner_id: Mapped[str | None] = mapped_column(
        String, ForeignKey('countries.id'), nullable=True
    )
    deleted: Mapped[bool] = mapped_column(default=False)

    owner: Mapped[CountryModel | None] = relationship(
        'CountryModel', back_populates='regions', remote_side=[id]
    )
    regions: Mapped[list['CountryModel']] = relationship(
        'CountryModel', back_populates='owner'
    )
    incoming_transforms: Mapped[list['TransformationModel']] = relationship(
        'TransformationModel',
        foreign_keys='TransformationModel.after_id',
        back_populates='after',
    )
    outgoing_transforms: Mapped[list['TransformationModel']] = relationship(
        'TransformationModel',
        foreign_keys='TransformationModel.before_id',
        back_populates='before',
    )
    periods: Mapped[list['PeriodModel']] = relationship(
        'PeriodModel', back_populates='country'
    )


class CountryService:
    @staticmethod
    def exists(country_id: str) -> bool:
        with Database.session() as session:
            return (
                session.query(CountryModel.id)
                .filter(
                    CountryModel.id == country_id,
                    CountryModel.deleted.is_(False),
                )
                .first()
                is not None
            )

    @staticmethod
    def get_all():
        with Database.session() as session:
            rows = (
                session.query(
                    CountryModel.id,
                    CountryModel.name,
                    CountryModel.owner_id,
                )
                .filter(CountryModel.deleted.is_(False))
                .order_by(CountryModel.begin_year, CountryModel.id)
                .all()
            )
            return [
                {'id': country_id, 'name': name, 'owner_id': owner_id}
                for country_id, name, owner_id in rows
            ]


from .periods import PeriodModel
from .transformations import TransformationModel
