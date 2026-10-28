
import csv
from datetime import datetime
from pathlib import Path

from src.database.videos import VideoModel
from src.database.orm import Database


CSV_PATH = Path(__file__).parent / "videos.csv"

MIN_NUM = 10
MAX_NUM = 1310

START_COLOR = (153, 0, 0)   # #990000
MID_COLOR = (153, 153, 0)   # #999900
END_COLOR = (0, 153, 0)     # #009900

MID_NUM = (MIN_NUM + MAX_NUM) / 2


def get_quality(num: int) -> str:
    """Вычисляет цвет видео: красный -> жёлтый -> зелёный."""
    if num >= MAX_NUM:
        return "#009900"

    if num <= MIN_NUM:
        return "#990000"

    if num <= MID_NUM:
        progress = (num - MIN_NUM) / (MID_NUM - MIN_NUM)
        r = START_COLOR[0]
        g = round(
            START_COLOR[1]
            + (MID_COLOR[1] - START_COLOR[1]) * progress
        )
    else:
        progress = (num - MID_NUM) / (MAX_NUM - MID_NUM)
        r = round(
            MID_COLOR[0]
            + (END_COLOR[0] - MID_COLOR[0]) * progress
        )
        g = MID_COLOR[1]

    b = 0
    return f"#{r:02x}{g:02x}{b:02x}"


def parse_optional(value: str | None) -> str | None:
    """Преобразует пустую строку в None."""
    if value is None:
        return None

    value = value.strip()
    return value or None


def import_videos() -> None:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        rows = list(reader)

        if not reader.fieldnames:
            raise ValueError("CSV-файл не содержит заголовков")

        required_columns = {
            "num",
            "title",
            "published",
            "url",
            "reserve_url",
        }

        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"В CSV отсутствуют колонки: {', '.join(sorted(missing))}"
            )

    videos = []

    for line_number, row in enumerate(rows, start=2):
        try:
            num = int(row["num"])
            title = row["title"].strip()

            if not title:
                raise ValueError("title не может быть пустым")

            published = datetime.strptime(
                row["published"].strip(), "%d.%m.%Y"
            ).date()

            videos.append(
                VideoModel(
                    num=num,
                    title=title,
                    published=published,
                    url=parse_optional(row["url"]),
                    reserve_url=parse_optional(row["reserve_url"]),
                    image_file=None,
                    description=None,
                    quality=get_quality(num),
                    deleted=False,
                )
            )

        except (ValueError, TypeError, AttributeError) as error:
            raise ValueError(
                f"Ошибка в CSV, строка {line_number}: {row}. "
                f"Причина: {error}"
            ) from error

    with Database.session() as session:
        session.add_all(videos)
        session.commit()

    print(f"Успешно импортировано видео: {len(videos)}")


if __name__ == "__main__":
    import_videos()
