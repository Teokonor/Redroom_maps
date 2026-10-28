from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Iterable, List

from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload, aliased
from sqlalchemy.sql.sqltypes import String, Integer, Date, JSON

from .abs import Base
from .orm import Database
from .video_tags import VideoTagModel


class VideoModel(Base):
    __tablename__ = 'videos'
    
    num: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    reserve_url: Mapped[str | None] = mapped_column(String, nullable=True)
    image_file: Mapped[str | None] = mapped_column(String, nullable=True)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    mentioned: Mapped[list[int]] = mapped_column(
        JSON(none_as_null=True), default=list, nullable=True
    )
    ideas_released: Mapped[list[int]] = mapped_column(
        JSON(none_as_null=True), default=list, nullable=True
    )
    ideas_planned: Mapped[list[str]] = mapped_column(
        JSON(none_as_null=True), default=list, nullable=True
    )
    quality: Mapped[str] = mapped_column(String, default="#009900")
    published: Mapped[date] = mapped_column(Date)
    deleted: Mapped[bool] = mapped_column(default=False)
    
    periods: Mapped[List['PeriodModel']] = relationship('PeriodModel', back_populates='video')
    tags: Mapped[List['TagModel']] = relationship(
        'TagModel',
        secondary=VideoTagModel.__table__,
        back_populates='videos',
    )


def _build_video_selection(
    periods: Iterable[PeriodModel],
) -> dict[str, list[VideoModel]]:
    """Collect unique videos, keeping main videos out of the indirect list."""
    main: dict[int, VideoModel] = {}
    indirectly: dict[int, VideoModel] = {}

    for period in periods:
        video = period.video
        if video is None or video.deleted:
            continue

        if period.is_main:
            main[video.num] = video
            indirectly.pop(video.num, None)
        elif video.num not in main:
            indirectly[video.num] = video

    return {
        'main': sorted(main.values(), key=lambda video: video.num, reverse=True),
        'indirectly': sorted(
            indirectly.values(), key=lambda video: video.num, reverse=True
        ),
    }


class VideoService:
    @staticmethod
    def get_for_period(
        country_id: str, begin_year: int, end_year: int
    ) -> dict[str, list[VideoModel]]:
        with Database.session() as session:
            periods = (
                session.query(PeriodModel)
                .options(joinedload(PeriodModel.video))
                .filter(
                    PeriodModel.country_id == country_id,
                    PeriodModel.deleted.is_(False),
                    PeriodModel.begin_year <= end_year,
                    PeriodModel.end_year >= begin_year,
                )
                .all()
            )
            return _build_video_selection(periods)

    @staticmethod
    def get_for_history(country_id: str) -> dict[str, list[VideoModel]]:
        with Database.session() as session:
            before_country = aliased(CountryModel)
            after_country = aliased(CountryModel)
            transformations = (
                session.query(
                    TransformationModel.before_id,
                    TransformationModel.after_id,
                )
                .join(
                    before_country,
                    before_country.id == TransformationModel.before_id,
                )
                .join(
                    after_country,
                    after_country.id == TransformationModel.after_id,
                )
                .filter(
                    TransformationModel.deleted.is_(False),
                    before_country.deleted.is_(False),
                    after_country.deleted.is_(False),
                )
                .all()
            )

            neighbors: dict[str, set[str]] = defaultdict(set)
            for before_id, after_id in transformations:
                neighbors[before_id].add(after_id)
                neighbors[after_id].add(before_id)

            country_ids = {country_id}
            pending = [country_id]

            # Traverse both directions, keeping every branch and guarding cycles.
            while pending:
                current_id = pending.pop()
                for next_id in neighbors.get(current_id, ()):
                    if next_id in country_ids:
                        continue
                    country_ids.add(next_id)
                    pending.append(next_id)

            periods = (
                session.query(PeriodModel)
                .options(joinedload(PeriodModel.video))
                .join(CountryModel, CountryModel.id == PeriodModel.country_id)
                .filter(
                    PeriodModel.country_id.in_(country_ids),
                    PeriodModel.deleted.is_(False),
                    CountryModel.deleted.is_(False),
                )
                .all()
            )
            return _build_video_selection(periods)

    @staticmethod
    def get_all() -> list[VideoModel]:
        with Database.session() as session:
            return (
                session.query(VideoModel)
                .filter(VideoModel.deleted.is_(False))
                .order_by(VideoModel.num.desc())
                .all()
            )

    @staticmethod
    def get_for_tag(tag_id: str) -> list[VideoModel]:
        with Database.session() as session:
            return (
                session.query(VideoModel)
                .join(
                    VideoTagModel,
                    VideoTagModel.video_num == VideoModel.num,
                )
                .filter(
                    VideoTagModel.tag_id == tag_id,
                    VideoModel.deleted.is_(False),
                )
                .order_by(VideoModel.num.desc())
                .all()
            )


from .countries import CountryModel
from .periods import PeriodModel
from .tags import TagModel
from .transformations import TransformationModel
