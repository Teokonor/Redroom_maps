from typing import List

from sqlalchemy.orm import Mapped, mapped_column, relationship, Session
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import String, Integer
from sqlalchemy import and_

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
    regions: Mapped[List['CountryModel']] = relationship('CountryModel', back_populates='owner')
    incoming_transforms: Mapped[List['TransformationModel']] = relationship(
        'TransformationModel', foreign_keys='TransformationModel.after_id', back_populates='after'
    )
    outgoing_transforms: Mapped[List['TransformationModel']] = relationship(
        'TransformationModel', foreign_keys='TransformationModel.before_id', back_populates='before'
    )
    periods: Mapped[List['PeriodModel']] = relationship('PeriodModel', back_populates='country')


class CountryService:
    @staticmethod
    def get_all():
        session: Session = Database.session()
        query = session.query(CountryModel).order_by(*CountryModel.begin_year)
        return query.all()
    
    @staticmethod
    def get_on_year(year: int):
        session: Session = Database.session()
        query = session.query(CountryModel)\
            .filter(and_(CountryModel.begin_year <= year, CountryModel.end_year >= year))\
            .order_by(*CountryModel.begin_year)
        return query.all()


from .periods import PeriodModel
from .transformations import TransformationModel
