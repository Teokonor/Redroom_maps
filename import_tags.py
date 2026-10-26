import csv
from collections import Counter
from pathlib import Path

from src.database.orm import Database
from src.database.tags import TagModel
from src.database.video_tags import VideoTagModel
from src.database.videos import VideoModel


INFO_PATH = Path(__file__).parent / "info.csv"

TAG_IDS = {
    "религия": "religion",
    "культура": "culture",
    "быт": "daily_life",
    "экономика": "economy",
    "география": "geography",
    "приколы": "humor",
    "урбанистика": "urbanism",
    "техника": "technology",
    "трукрайм": "true_crime",
    "археология": "archaeology",
    "музыка": "music",
}


def import_tags() -> None:
    if len(set(TAG_IDS.values())) != len(TAG_IDS):
        raise ValueError("TAG_IDS contains duplicate identifiers")

    video_tags: list[tuple[int, list[str]]] = []

    with INFO_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file, delimiter=";"))

    for line_number, row in enumerate(rows, start=1):
        if not row or not row[0].strip().isdigit():
            continue

        video_num = int(row[0].strip())
        raw_tags = row[3].strip() if len(row) > 3 else ""

        tags = []
        for raw_tag in raw_tags.split(","):
            tag_name = raw_tag.strip()
            if not tag_name or tag_name in tags:
                continue
            if tag_name not in TAG_IDS:
                raise ValueError(
                    f"Неизвестный тег {tag_name!r} в info.csv, строка "
                    f"{line_number}. Добавь его в TAG_IDS."
                )
            tags.append(tag_name)

        video_tags.append((video_num, tags))

    with Database.session() as session:
        video_nums = {num for (num,) in session.query(VideoModel.num).all()}
        missing_videos = sorted(
            video_num for video_num, _ in video_tags if video_num not in video_nums
        )
        if missing_videos:
            raise ValueError(
                "В info.csv есть видео, которых нет в videos: "
                + ", ".join(map(str, missing_videos))
            )

        existing_by_id = {tag.id: tag for tag in session.query(TagModel).all()}
        existing_by_name = {tag.name: tag for tag in session.query(TagModel).all()}

        used_tag_names = sorted(
            {tag_name for _, tags in video_tags for tag_name in tags}
        )
        created_tags = 0

        for tag_name in used_tag_names:
            tag_id = TAG_IDS[tag_name]
            tag_by_id = existing_by_id.get(tag_id)
            tag_by_name = existing_by_name.get(tag_name)

            if tag_by_name is not None and tag_by_name.id != tag_id:
                raise ValueError(
                    f"Тег {tag_name!r} уже существует с id "
                    f"{tag_by_name.id!r}, ожидался {tag_id!r}"
                )

            if tag_by_id is None:
                tag = TagModel(id=tag_id, name=tag_name)
                session.add(tag)
                existing_by_id[tag_id] = tag
                existing_by_name[tag_name] = tag
                created_tags += 1
            elif tag_by_id.name != tag_name:
                tag_by_id.name = tag_name
                existing_by_name[tag_name] = tag_by_id

        session.flush()

        existing_links = {
            (video_num, tag_id)
            for video_num, tag_id in session.query(
                VideoTagModel.video_num,
                VideoTagModel.tag_id,
            ).all()
        }

        created_links = 0
        tag_counts: Counter[str] = Counter()

        for video_num, tag_names in video_tags:
            for tag_name in tag_names:
                tag_id = TAG_IDS[tag_name]
                tag_counts[tag_id] += 1
                link = (video_num, tag_id)
                if link in existing_links:
                    continue
                session.add(
                    VideoTagModel(video_num=video_num, tag_id=tag_id)
                )
                existing_links.add(link)
                created_links += 1

        session.commit()

    tagged_videos = sum(1 for _, tags in video_tags if tags)
    print(f"Видео с тегами в info.csv: {tagged_videos}")
    print(f"Использовано тегов: {len(used_tag_names)}")
    print(f"Создано тегов: {created_tags}")
    print(f"Создано связей video_tags: {created_links}")
    print(f"Всего связей для тегов: {sum(tag_counts.values())}")
    print("Теги:")
    for tag_id, count in sorted(tag_counts.items(), key=lambda item: (-item[1], item[0])):
        print(f"  {tag_id:14} {count}")


if __name__ == "__main__":
    import_tags()
