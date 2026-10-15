
import json
from pathlib import Path

from shapely.geometry import shape, mapping
from shapely.geometry.polygon import orient


# Каталог с исходными GeoJSON
SOURCE_DIR = Path("maps")

# Исправленные файлы будут сохранены здесь
OUTPUT_DIR = Path("maps_d3_fixed")


def fix_geometry(geometry_data):
    """Исправляет направление колец Polygon/MultiPolygon для D3."""
    if not geometry_data:
        return geometry_data, 0

    geom = shape(geometry_data)

    if geom.geom_type == "Polygon":
        polygons = [geom]
    elif geom.geom_type == "MultiPolygon":
        polygons = list(geom.geoms)
    else:
        return geometry_data, 0

    fixed_polygons = []
    changed = 0

    for polygon in polygons:
        # D3: внешнее кольцо по часовой стрелке,
        # внутренние кольца (отверстия) против часовой.
        fixed = orient(polygon, sign=-1.0)

        if fixed.exterior.coords[:] != polygon.exterior.coords[:]:
            changed += 1

        # Дополнительно считаем изменения ориентации отверстий.
        for old_ring, new_ring in zip(
            polygon.interiors, fixed.interiors
        ):
            if old_ring.coords[:] != new_ring.coords[:]:
                changed += 1

        fixed_polygons.append(fixed)

    if geom.geom_type == "Polygon":
        fixed_geom = fixed_polygons[0]
    else:
        fixed_geom = type(geom)(fixed_polygons)

    return mapping(fixed_geom), changed


def process_file(source_path: Path):
    relative_path = source_path.relative_to(SOURCE_DIR)
    output_path = OUTPUT_DIR / relative_path
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with source_path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    total_changed = 0

    if data.get("type") == "FeatureCollection":
        features = data.get("features", [])
    elif data.get("type") == "Feature":
        features = [data]
    else:
        features = []

    for feature in features:
        geometry = feature.get("geometry")
        if not geometry:
            continue

        fixed_geometry, changed = fix_geometry(geometry)
        feature["geometry"] = fixed_geometry
        total_changed += changed

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)

    print(
        f"{relative_path}: "
        f"исправлено колец: {total_changed}"
    )


def main():
    if not SOURCE_DIR.is_dir():
        raise FileNotFoundError(
            f"Каталог не найден: {SOURCE_DIR.resolve()}"
        )

    files = sorted(SOURCE_DIR.rglob("*.geojson"))

    if not files:
        print("GeoJSON-файлы не найдены.")
        return

    for path in files:
        try:
            process_file(path)
        except Exception as exc:
            print(f"ОШИБКА {path}: {exc}")

    print(f"\nГотово. Результаты: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    main()
