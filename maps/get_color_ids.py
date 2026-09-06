import json

OUTPUT_FILE = "color_ids.txt"

def main():
    color_ids = set()
    
    years = [ 1960, 1970, 1980, 1990, 2000, 2010, 2025 ]
    
    for year in years:
        filename = f"{year}.geojson"
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        if data.get("type") == "FeatureCollection":
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                if "colorId" in props:
                    color_ids.add(props["colorId"])
        else:
            print("Unsupported format (ожидается FeatureCollection)")
            raise ValueError("Unsupported format (ожидается FeatureCollection)")

    sorted_ids = sorted(color_ids)
    
    # color_ids_for_json = [{"colorId": i} for i in sorted_ids]
    # with open("color_ids_generated.json", "w", encoding="utf-8") as f:
    #     json.dump(color_ids_for_json, f, ensure_ascii=False, indent=2)
    colors_dict = { i: "#777000" for i in sorted_ids }
    with open("color_ids_generated.json", "w", encoding="utf-8") as f:
        json.dump(colors_dict, f, ensure_ascii=False, indent=2)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for i in sorted_ids:
            f.write(i + "\n")

if __name__ == "__main__":
    main()