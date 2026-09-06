from pathlib import Path


PROJECT_DIR = Path(__file__).parent.parent
maps_dir = (PROJECT_DIR / 'maps').resolve()
print(str(maps_dir))
