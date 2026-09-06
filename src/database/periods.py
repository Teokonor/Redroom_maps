from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import String, Integer

from .abs import Base
    

class PeriodModel(Base):
    __tablename__ = 'periods'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    video_num: Mapped[int] = mapped_column(Integer, ForeignKey('videos.num'))
    country_id: Mapped[str] = mapped_column(String, ForeignKey('countries.id'))
    begin_year: Mapped[int] = mapped_column(Integer)
    end_year: Mapped[int] = mapped_column(Integer)
    is_main: Mapped[bool] = mapped_column(Integer)
    deleted: Mapped[bool] = mapped_column(default=False)
    
    country: Mapped['CountryModel'] = relationship('CountryModel')
    video: Mapped['VideoModel'] = relationship('VideoModel', back_populates='periods')


from .countries import CountryModel
from .videos import VideoModel
