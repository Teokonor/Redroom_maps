from enum import Enum as BaseEnum

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import String, Integer, Enum

from .abs import Base


class TransformationTypes(str, BaseEnum):
    SPLIT = 'split'
    MERGE = 'merge'
    RENAME = 'rename'
    ANNEXATION = 'annexation'
    INDEPENDENCE = 'independence'
    TRANSFER = 'transfer'


class TransformationModel(Base):
    __tablename__ = 'transformations'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    before_id: Mapped[str] = mapped_column(String, ForeignKey('countries.id'))
    after_id: Mapped[str] = mapped_column(String, ForeignKey('countries.id'))
    type: Mapped[TransformationTypes] = mapped_column(Enum(TransformationTypes))
    year: Mapped[int] = mapped_column(Integer)
    deleted: Mapped[bool] = mapped_column(default=False)
    
    before: Mapped['CountryModel'] = relationship(
        'CountryModel', foreign_keys=[before_id], back_populates='outgoing_transforms'
    )
    after: Mapped['CountryModel'] = relationship(
        'CountryModel', foreign_keys=[after_id], back_populates='incoming_transforms'
    )


from .countries import CountryModel
