import json
from pathlib import Path

from topojson import Topology


# ААААААААААААААААААААААААААААААААААААААААААА
# ВАЖНООО!!!!!!!!!!!!

# Для корректной работы скрипта нужно зайти в venv/Lib/site-packages/topojson/core/dedup.py

# И в нём в функции def _direct_arcs(self, array_bk, array_bk_parts, first_of_part, arcs)
# Закомментировать строку
# forward |= np.repeat(n_arcs == 1, n_arcs)
# В моей версии это строка 136

# (Она принудительно ставит положительное направление для одиночных дуг, что ломает направления обхода)



# Папка, в которой лежит этот скрипт.
BASE_DIR = Path(__file__).resolve().parent


def convert_geojson(source_path: Path) -> None:
    """Конвертирует GeoJSON в компактный TopoJSON."""

    target_path = source_path.with_suffix(".topojson")

    try:
        # Читаем исходный GeoJSON.
        with source_path.open("r", encoding="utf-8-sig") as file:
            geojson = json.load(file)

        # Строим топологию.
        topology = Topology(
            geojson,
            prequantize=False,
        )

        # Получаем словарь TopoJSON.
        result = topology.to_dict()

        # Округляем все координаты дуг до 3 знаков.
        # У TopoJSON координаты могут быть delta-кодированными,
        # поэтому при включённом transform этот шаг не применяется.
        if "transform" not in result:
            result["arcs"] = [
                [
                    [round(value, 3) for value in point]
                    for point in arc
                ]
                for arc in result.get("arcs", [])
            ]

        # Компактная запись: без отступов и лишних пробелов.
        # Сначала пишем во временный файл, чтобы не повредить
        # существующий результат при ошибке.
        temp_path = target_path.with_suffix(".topojson.tmp")

        with temp_path.open("w", encoding="utf-8", newline="\n") as file:
            json.dump(
                result,
                file,
                ensure_ascii=False,
                separators=(",", ":"),
                allow_nan=False,
            )

        # Заменяем старый файл только после успешной записи.
        temp_path.replace(target_path)

        print(f"[OK] {source_path.name} -> {target_path.name}")

    except Exception as error:
        print(f"[ОШИБКА] {source_path.name}: {error}")


def main() -> None:
    # glob ищет только в указанной папке, не во вложенных.
    files = sorted(BASE_DIR.glob("*.geojson"))

    if not files:
        print(f"Файлы .geojson не найдены: {BASE_DIR}")
        return

    print(f"Найдено файлов: {len(files)}")

    for source_path in files:
        convert_geojson(source_path)


if __name__ == "__main__":
    main()
