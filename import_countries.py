
import csv
from pathlib import Path

from sqlalchemy.orm import Session

from src.database.countries import CountryModel
from src.database.orm import Database


CSV_PATH = Path(__file__).parent / "countries.csv"


def parse_optional_int(value: str) -> int | None:
    value = value.strip()
    return int(value) if value else None


def import_countries() -> None:
    # Читаем CSV с разделителем ";".
    with CSV_PATH.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file, delimiter=";")
        rows = list(reader)

        if not reader.fieldnames:
            raise ValueError("CSV-файл не содержит заголовков")

        required_columns = {
            "id",
            "begin_year",
            "end_year",
            "owner_id",
            "name",
        }

        missing = required_columns - set(reader.fieldnames)
        if missing:
            raise ValueError(
                f"В CSV отсутствуют колонки: {', '.join(sorted(missing))}"
            )

    # Проверяем ID до начала транзакции.
    ids = [row["id"].strip() for row in rows]

    if any(not country_id for country_id in ids):
        raise ValueError("В CSV обнаружен пустой id")

    if len(ids) != len(set(ids)):
        raise ValueError("В CSV обнаружены повторяющиеся id")

    # Получаем настоящую сессию через контекстный менеджер.
    with Database.session() as session:
        countries = []

        for row in rows:
            countries.append(
                CountryModel(
                    id=row["id"].strip(),
                    name=row["name"].strip(),
                    begin_year=int(row["begin_year"]),
                    end_year=parse_optional_int(row["end_year"]),
                    owner_id=None,
                    deleted=False,
                )
            )

        # Добавляем все записи без owner_id.
        session.add_all(countries)
        session.flush()

        # После вставки назначаем внешние ссылки.
        for country, row in zip(countries, rows):
            owner_id = row["owner_id"].strip()
            country.owner_id = owner_id or None

        # Фиксируем транзакцию.
        session.commit()

    print(f"Успешно импортировано записей: {len(countries)}")


if __name__ == "__main__":
    import_countries()
