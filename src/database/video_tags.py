from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.sqltypes import Integer, String

from .abs import Base


class VideoTagModel(Base):
    __tablename__ = 'video_tags'

    video_num: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('videos.num', ondelete='CASCADE'),
        primary_key=True,
    )
    tag_id: Mapped[str] = mapped_column(
        String,
        ForeignKey('tags.id', ondelete='CASCADE'),
        primary_key=True,
    )

    __table_args__ = (
        Index('ix_video_tags_tag_id', 'tag_id', 'video_num'),
    )
