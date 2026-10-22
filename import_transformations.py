
import csv
from pathlib import Path

from src.database.transformations import (
    TransformationModel,
    TransformationTypes,
)
from src.database.orm import Database


CSV_PATH = Path(__file__).parent / "transformations.csv"


def import_transformations() -> None:
    # Читаем CSV с разделителем ";".
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        rows = list(reader)

        if not reader.fieldnames:
            raise ValueError("CSV-файл не содержит заголовков")

        required_columns = {
            "before_id",
            "after_id",
            "type",
            "year",
        }

        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"В CSV отсутствуют колонки: {', '.join(sorted(missing))}"
            )

    transformations = []

    # Подготавливаем данные до начала транзакции.
    for line_number, row in enumerate(rows, start=2):
        try:
            before_id = row["before_id"].strip()
            after_id = row["after_id"].strip()
            type_name = row["type"].strip().upper()
            year = int(row["year"])

            if not before_id or not after_id:
                raise ValueError("before_id и after_id не могут быть пустыми")

            # Например, "SPLIT" -> TransformationTypes.SPLIT.
            transformation_type = TransformationTypes[type_name]

            transformations.append(
                TransformationModel(
                    before_id=before_id,
                    after_id=after_id,
                    type=transformation_type,
                    year=year,
                    deleted=False,
                )
            )

        except (ValueError, KeyError) as error:
            raise ValueError(
                f"Ошибка в CSV, строка {line_number}: {row}. "
                f"Причина: {error}"
            ) from error

    # Сохраняем записи в БД.
    with Database.session() as session:
        session.add_all(transformations)
        session.commit()

    print(
        f"Успешно импортировано преобразований: "
        f"{len(transformations)}"
    )


if __name__ == "__main__":
    import_transformations()
