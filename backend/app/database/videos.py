from __future__ import annotations

from collections import OrderedDict, defaultdict
from collections.abc import Iterable
from datetime import date
from threading import Lock

from loguru import logger
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


# Cache responses by connected component: every country from the same
# transformation graph has the same full-history response. The cache is
# per worker and is dropped when the database file changes.
_HISTORY_CACHE_LIMIT = 128
_history_cache_lock = Lock()
_history_cache_version: str | None = None
_history_component_by_country: dict[str, str] = {}
_history_component_members: dict[str, tuple[str, ...]] = {}
_history_cache: OrderedDict[str, dict] = OrderedDict()


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
    _history_component_by_country.clear()
    _history_component_members.clear()
    _history_cache.clear()


def _load_history_components() -> tuple[
    dict[str, str], dict[str, tuple[str, ...]]
]:
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

    component_by_country: dict[str, str] = {}
    component_members: dict[str, tuple[str, ...]] = {}

    for node in neighbors:
        if node in component_by_country:
            continue

        members = {node}
        pending = [node]

        # Traverse both directions, keeping every branch and guarding cycles.
        while pending:
            current_id = pending.pop()
            for next_id in neighbors.get(current_id, ()):
                if next_id in members:
                    continue
                members.add(next_id)
                pending.append(next_id)

        root = min(members)
        ordered_members = tuple(sorted(members))
        component_members[root] = ordered_members

        for country_id in members:
            component_by_country[country_id] = root

    logger.debug(
        'Built {} history components from {} transformations',
        len(component_members),
        len(transformations),
    )

    return component_by_country, component_members


def _history_component(
    country_id: str, version: str
) -> tuple[str, tuple[str, ...]]:
    with _history_cache_lock:
        _reset_history_cache(version)

        root = _history_component_by_country.get(country_id)

        if root is None:
            component_by_country, component_members = (
                _load_history_components()
            )
            _history_component_by_country.update(component_by_country)
            _history_component_members.update(component_members)
            root = _history_component_by_country.get(
                country_id, country_id
            )

        members = _history_component_members.get(
            root, (country_id,)
        )
        return root, members


def _history_cache_get(
    version: str, root: str
) -> dict | None:
    with _history_cache_lock:
        _reset_history_cache(version)

        payload = _history_cache.get(root)
        if payload is not None:
            _history_cache.move_to_end(root)

        return payload


def _history_cache_set(version: str, root: str, payload: dict) -> None:
    with _history_cache_lock:
        if _history_cache_version != version:
            return

        _history_cache[root] = payload
        _history_cache.move_to_end(root)

        while len(_history_cache) > _HISTORY_CACHE_LIMIT:
            _history_cache.popitem(last=False)


def _build_history_response(component_ids: tuple[str, ...]) -> dict:
    with Database.session() as session:
        periods = (
            session.query(PeriodModel)
            .options(joinedload(PeriodModel.video))
            .filter(
                PeriodModel.country_id.in_(component_ids),
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
        root, component_ids = _history_component(country_id, version)

        cached = _history_cache_get(version, root)
        if cached is not None:
            logger.debug(
                'History cache hit: country={}, component={}',
                country_id,
                root,
            )
            return cached

        logger.debug(
            'History cache miss: country={}, component={}, countries={}',
            country_id,
            root,
            len(component_ids),
        )
        selection = _build_history_response(component_ids)
        _history_cache_set(version, root, selection)
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
