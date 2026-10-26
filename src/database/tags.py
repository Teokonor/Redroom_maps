from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql.sqltypes import String

from .abs import Base
from .orm import Database
from .video_tags import VideoTagModel


class TagModel(Base):
    __tablename__ = 'tags'

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)

    videos: Mapped[List['VideoModel']] = relationship(
        'VideoModel',
        secondary=VideoTagModel.__table__,
        back_populates='tags',
    )


class TagService:
    @staticmethod
    def get_all():
        with Database.session() as session:
            rows = (
                session.query(
                    TagModel,
                    func.count(VideoTagModel.video_num),
                )
                .outerjoin(
                    VideoTagModel,
                    VideoTagModel.tag_id == TagModel.id,
                )
                .group_by(TagModel.id, TagModel.name)
                .order_by(TagModel.name, TagModel.id)
                .all()
            )

            return [
                {
                    'id': tag.id,
                    'name': tag.name,
                    'video_count': video_count,
                }
                for tag, video_count in rows
            ]

    @staticmethod
    def exists(tag_id: str) -> bool:
        with Database.session() as session:
            return (
                session.query(TagModel.id)
                .filter(TagModel.id == tag_id)
                .first()
                is not None
            )


from .videos import VideoModel
