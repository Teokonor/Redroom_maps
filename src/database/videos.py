from typing import List
from datetime import date

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import String, Integer, Date

from .abs import Base


class VideoModel(Base):
    __tablename__ = 'videos'
    
    num: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    reserve_url: Mapped[str | None] = mapped_column(String, nullable=True)
    image_file: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    quality: Mapped[str] = mapped_column(String, default="#009900")
    published: Mapped[date] = mapped_column(Date)
    deleted: Mapped[bool] = mapped_column(default=False)
    
    periods: Mapped[List['PeriodModel']] = relationship('PeriodModel', back_populates='video')


from .periods import PeriodModel
