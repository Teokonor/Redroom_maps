from __future__ import annotations

import json
from collections import OrderedDict, defaultdict
from collections.abc import Iterable
from datetime import date
from threading import Lock

from loguru import logger
from sqlalchemy.orm import Mapped, mapped_column, relationship, joinedload
from sqlalchemy.sql.sqltypes import String, Integer, Date, JSON

from ..constants import HISTORY_GROUPS_PATH
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
    
    periods: Mapped[list['PeriodModel']] = relationship(
        'PeriodModel', back_populates='video'
    )
    tags: Mapped[list['TagModel']] = relationship(
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


def _build_period_groups(periods: Iterable[PeriodModel]) -> list[dict]:
    """Group equal periods and collect the videos that belong to them."""
    grouped: dict[tuple[int, int, bool], set[int]] = defaultdict(set)

    for period in periods:
        video = period.video
        if video is None or video.deleted:
            continue

        grouped[
            (period.begin_year, period.end_year, bool(period.is_main))
        ].add(video.num)

    return [
        {
            'begin_year': begin_year,
            'end_year': end_year,
            'is_main': is_main,
            'video_nums': sorted(video_nums),
        }
        for (begin_year, end_year, is_main), video_nums in sorted(
            grouped.items(),
            key=lambda item: (item[0][0], item[0][1], item[0][2]),
        )
    ]


# History scope comes from the curated groups in
# backend/app/data/history_groups.json (generated from
# data/work/periods/histories). Countries that share a group share their
# history: for example, Russia, Ukraine and Belarus all use east_slavs.
# The cache is per worker and is dropped when the data version changes.
_HISTORY_CACHE_LIMIT = 128
_history_lock = Lock()
_history_cache_version: str | None = None
_history_cache: OrderedDict[str, dict] = OrderedDict()

_history_groups_loaded = False
_history_groups_by_country: dict[str, str] = {}
_history_group_members: dict[str, tuple[str, ...]] = {}


def _reset_history_cache(version: str) -> None:
    global _history_cache_version

    if _history_cache_version == version:
        return

    if _history_cache_version is not None:
        logger.info(
            'Data version changed ({} -> {}); history cache reset',
            _history_cache_version,
            version,
        )

    _history_cache_version = version
    _history_cache.clear()


def _load_history_groups() -> None:
    global _history_groups_loaded

    if _history_groups_loaded:
        return

    _history_groups_loaded = True

    try:
        raw = json.loads(
            HISTORY_GROUPS_PATH.read_text(encoding='utf-8')
        )
    except (OSError, ValueError) as error:
        logger.warning(
            'Cannot load history groups from {}: {}',
            HISTORY_GROUPS_PATH,
            error,
        )
        return

    country_groups = raw.get('country_groups', {})
    groups = raw.get('groups', {})

    for country_id, group_id in country_groups.items():
        if isinstance(group_id, str) and group_id:
            _history_groups_by_country[country_id] = group_id

    for group_id, country_ids in groups.items():
        if not isinstance(country_ids, list):
            continue
        _history_group_members[group_id] = tuple(
            sorted(
                {
                    country_id
                    for country_id in country_ids
                    if isinstance(country_id, str)
                }
            )
        )

    logger.info(
        'Loaded history groups: {} countries, {} groups',
        len(_history_groups_by_country),
        len(_history_group_members),
    )


def _history_scope(country_id: str) -> tuple[str, tuple[str, ...]]:
    """Return a cache key and the countries that make up this history."""
    with _history_lock:
        _load_history_groups()

        group_id = _history_groups_by_country.get(country_id)
        if not group_id:
            return f'country:{country_id}', (country_id,)

        members = _history_group_members.get(group_id)
        if not members:
            return f'country:{country_id}', (country_id,)

        # Keep the country itself even if a group file forgot to list it.
        scope = set(members)
        scope.add(country_id)
        return f'group:{group_id}', tuple(sorted(scope))


def _history_cache_get(
    version: str, cache_key: str
) -> dict | None:
    with _history_lock:
        _reset_history_cache(version)

        payload = _history_cache.get(cache_key)
        if payload is not None:
            _history_cache.move_to_end(cache_key)

        return payload


def _history_cache_set(version: str, cache_key: str, payload: dict) -> None:
    with _history_lock:
        if _history_cache_version != version:
            return

        _history_cache[cache_key] = payload
        _history_cache.move_to_end(cache_key)

        while len(_history_cache) > _HISTORY_CACHE_LIMIT:
            _history_cache.popitem(last=False)


def _build_history_response(country_ids: tuple[str, ...]) -> dict:
    with Database.session() as session:
        periods = (
            session.query(PeriodModel)
            .options(joinedload(PeriodModel.video))
            .filter(
                PeriodModel.country_id.in_(country_ids),
                PeriodModel.deleted.is_(False),
            )
            .all()
        )

        selection = _build_video_selection(periods)
        selection['periods'] = _build_period_groups(periods)
        return selection


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
    def get_for_history(country_id: str) -> dict:
        version = Database.data_version()
        cache_key, country_ids = _history_scope(country_id)

        cached = _history_cache_get(version, cache_key)
        if cached is not None:
            logger.debug(
                'History cache hit: country={}, scope={}',
                country_id,
                cache_key,
            )
            return cached

        logger.debug(
            'History cache miss: country={}, scope={}, countries={}',
            country_id,
            cache_key,
            len(country_ids),
        )
        selection = _build_history_response(country_ids)
        _history_cache_set(version, cache_key, selection)
        return selection

    @staticmethod
    def get_periods(video_num: int) -> list[PeriodModel]:
        with Database.session() as session:
            return (
                session.query(PeriodModel)
                .filter(
                    PeriodModel.video_num == video_num,
                    PeriodModel.deleted.is_(False),
                )
                .order_by(
                    PeriodModel.begin_year,
                    PeriodModel.end_year,
                    PeriodModel.country_id,
                )
                .all()
            )

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
