import json

INPUT_FILE = "2025before_coloring.geojson"
OUTPUT_FILE = "2025.json"

def transform_feature(feature):
    props = feature.get("properties", {})
    
    id_ = props.get("id")
    name = props.get("NAME") or props.get("name") or "unknown"
    
    # нормализуем (по желанию)
    normalized = id_.lower().replace(" ", "_")
    
    feature["properties"] = {
        "id": normalized,
        "historyId": normalized,
        "name": name,
        "parent": None
    }
    
    return feature

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data["type"] == "FeatureCollection":
        data["features"] = [transform_feature(f) for f in data["features"]]
    else:
        raise ValueError("Unsupported format")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))

if __name__ == "__main__":
    main()