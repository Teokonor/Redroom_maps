import json
from pathlib import Path

from topojson import Topology


# Папка, в которой лежит этот скрипт.
BASE_DIR = Path(__file__).resolve().parent


def _ring_area(ring: list[list[float]]) -> float:
    """Возвращает площадь кольца со знаком."""
    return sum(
        x0 * y1 - x1 * y0
        for (x0, y0), (x1, y1) in zip(ring, ring[1:])
    ) / 2


def _stitch_ring(
    arcs: list[list[list[float]]],
    ring: list[int],
) -> list[list[float]]:
    """Собирает координаты кольца из ссылок на дуги TopoJSON."""
    points: list[list[float]] = []

    for index, arc_index in enumerate(ring):
        arc = arcs[arc_index if arc_index >= 0 else ~arc_index]

        if arc_index < 0:
            arc = arc[::-1]

        # Первая точка следующей дуги совпадает с последней точкой
        # предыдущей, поэтому её нужно пропустить.
        if index:
            arc = arc[1:]

        points.extend(arc)

    return points


def _fix_polygon_winding(result: dict) -> int:
    """
    Приводит кольца полигонов к ожидаемому D3 направлению обхода.

    У TopoJSON общая дуга может быть сохранена в направлении одного из
    объектов. Тогда анклав и дырка под него ссылаются на дугу с одинаковым
    знаком, и D3 рисует анклав как весь мир. Поэтому после конвертации
    проверяем фактическое направление каждого кольца: внешнее кольцо должно
    обходиться по часовой стрелке, внутренние — против.
    """
    arcs = result.get("arcs", [])
    fixed = 0

    for topology_object in result.get("objects", {}).values():
        for geometry in topology_object.get("geometries", []):
            geometry_type = geometry.get("type")

            if geometry_type == "Polygon":
                polygons = [geometry["arcs"]]
            elif geometry_type == "MultiPolygon":
                polygons = geometry["arcs"]
            else:
                continue

            for polygon in polygons:
                for ring_index, ring in enumerate(polygon):
                    area = _ring_area(_stitch_ring(arcs, ring))

                    if area == 0:
                        continue

                    # D3: внешнее кольцо — по часовой стрелке (area < 0),
                    # внутреннее (дырка) — против часовой (area > 0).
                    should_be_negative = ring_index == 0

                    if (area < 0) != should_be_negative:
                        polygon[ring_index] = [~arc for arc in reversed(ring)]
                        fixed += 1

    return fixed


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

        # Восстанавливаем направление обхода колец после дедупликации дуг.
        fixed_rings = _fix_polygon_winding(result)

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

        print(
            f"[OK] {source_path.name} -> {target_path.name} "
            f"(исправлено колец: {fixed_rings})"
        )

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
