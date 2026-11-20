import csv
import sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.database.orm import Database
from app.database.periods import PeriodModel


CSV_PATH = PROJECT_DIR / "data" / "work" / "spreadsheets" / "periods_for_export.csv"


def import_periods() -> None:
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        rows = list(reader)

        if not reader.fieldnames:
            raise ValueError("CSV-файл не содержит заголовков")

        required_columns = {
            "video_num",
            "country_id",
            "begin_year",
            "end_year",
            "is_main",
        }

        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"В CSV отсутствуют колонки: {', '.join(sorted(missing))}"
            )

    periods = []

    for line_number, row in enumerate(rows, start=2):
        try:
            video_num = int(row["video_num"])
            country_id = row["country_id"].strip()
            begin_year = int(row["begin_year"])
            end_year = int(row["end_year"])
            is_main_raw = row["is_main"].strip()

            if not country_id:
                raise ValueError("country_id не может быть пустым")

            if is_main_raw not in {"0", "1", "2"}:
                raise ValueError("is_main должен быть 0, 1 или 2")

            if begin_year > end_year:
                raise ValueError("begin_year не может быть больше end_year")

            periods.append(
                PeriodModel(
                    video_num=video_num,
                    country_id=country_id,
                    begin_year=begin_year,
                    end_year=end_year,
                    is_main=1 if is_main_raw == "1" else 0,
                    deleted=False,
                )
            )

        except (ValueError, TypeError, AttributeError) as error:
            raise ValueError(
                f"Ошибка в CSV, строка {line_number}: {row}. "
                f"Причина: {error}"
            ) from error

    with Database.session() as session:
        existing = {
            (
                period.video_num,
                period.country_id,
                period.begin_year,
                period.end_year,
                period.is_main,
            )
            for period in session.query(PeriodModel).all()
        }

        new_periods = [
            period
            for period in periods
            if (
                period.video_num,
                period.country_id,
                period.begin_year,
                period.end_year,
                period.is_main,
            )
            not in existing
        ]

        session.add_all(new_periods)
        session.commit()

    print(f"Успешно импортировано периодов: {len(new_periods)}")
    print(f"Пропущено уже существующих: {len(periods) - len(new_periods)}")


if __name__ == "__main__":
    import_periods()
