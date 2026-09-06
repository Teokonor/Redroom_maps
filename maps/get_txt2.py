import json

YEAR = "2025"

INPUT_FILE = f"{YEAR}.geojson"
OUTPUT_FILE = f"ids{YEAR}.txt"

def main():
    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    ids = set()

    if data.get("type") == "FeatureCollection":
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            if "id" in props:
                ids.add(props["id"])
    else:
        print("Unsupported format (ожидается FeatureCollection)")
        raise ValueError("Unsupported format (ожидается FeatureCollection)")

    sorted_ids = sorted(ids)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for i in sorted_ids:
            f.write(i + "\n")

if __name__ == "__main__":
    main()