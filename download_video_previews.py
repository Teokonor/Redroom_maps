import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlencode, urlparse
from urllib.request import Request, urlopen


PROJECT_DIR = Path(__file__).resolve().parent
PREVIEWS_DIR = PROJECT_DIR / "video_previews"
DB_PATHS = [
    PROJECT_DIR / "redroom_maps.db",
    PROJECT_DIR / "redroom_maps without periods.db",
]
YOUTUBE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_HOSTS = ("i.ytimg.com", "img.youtube.com")
PROXY_HOSTS = ("wsrv.nl", "images.weserv.nl")
THUMBNAIL_NAMES = ("mqdefault.jpg", "hqdefault.jpg")
DIRECT_AVAILABLE = True


def youtube_video_id(url: str | None) -> str | None:
    if not url or not url.strip():
        return None

    value = url.strip()
    if not re.match(r"^[a-z][a-z0-9+.-]*://", value, re.IGNORECASE):
        value = "https://" + value

    parsed = urlparse(value)
    host = parsed.netloc.lower().removeprefix("www.")
    video_id = None

    if host == "youtu.be":
        parts = [part for part in parsed.path.split("/") if part]
        video_id = parts[0] if parts else None
    elif host == "youtube.com" or host.endswith(".youtube.com"):
        path = parsed.path.rstrip("/")
        if path == "/watch":
            video_id = parse_qs(parsed.query).get("v", [None])[0]
        else:
            match = re.match(r"^/(?:shorts|embed|live|v)/([^/]+)", path)
            video_id = match.group(1) if match else None

    return video_id if video_id and YOUTUBE_ID_PATTERN.fullmatch(video_id) else None


def download_thumbnail(video_id: str, destination: Path, timeout: float) -> bool:
    global DIRECT_AVAILABLE

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
        "Referer": "https://www.youtube.com/",
    }

    urls: list[str] = []

    if DIRECT_AVAILABLE:
        for host in YOUTUBE_HOSTS:
            for name in THUMBNAIL_NAMES:
                urls.append(f"https://{host}/vi/{video_id}/{name}")

    for proxy_host in PROXY_HOSTS:
        for name in THUMBNAIL_NAMES:
            source = f"i.ytimg.com/vi/{video_id}/{name}"
            urls.append(
                f"https://{proxy_host}/?{urlencode({'url': source})}"
            )

    for url in urls:
        try:
            request = Request(url, headers=headers)
            with urlopen(request, timeout=timeout) as response:
                content_type = response.headers.get("Content-Type", "")
                data = response.read()
            if not content_type.startswith("image/") or len(data) < 200:
                continue
            temp_path = destination.with_suffix(destination.suffix + ".part")
            temp_path.write_bytes(data)
            os.replace(temp_path, destination)
            return True
        except Exception:
            continue

    if DIRECT_AVAILABLE:
        DIRECT_AVAILABLE = False

    return False


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Скачать превью видео с YouTube в video_previews"
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="таймаут одной попытки в секундах (по умолчанию 10)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="ограничить число попыток скачивания (0 — все)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="перекачать файлы, даже если они уже есть",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATHS[0]) as connection:
        connection.row_factory = sqlite3.Row
        videos = connection.execute(
            """
            SELECT num, url, reserve_url, image_file
            FROM videos
            WHERE deleted = 0
            ORDER BY num DESC
            """
        ).fetchall()

    downloaded = 0
    existing = 0
    skipped = 0
    failed = []
    attempts = 0
    images: dict[int, str] = {}

    for video in videos:
        num = video["num"]
        image_file = f"{num}.jpg"
        destination = PREVIEWS_DIR / image_file

        if destination.is_file() and destination.stat().st_size > 0 and not args.force:
            existing += 1
            images[num] = image_file
            continue

        if args.limit and attempts >= args.limit:
            skipped += 1
            continue

        video_id = youtube_video_id(video["url"]) or youtube_video_id(
            video["reserve_url"]
        )
        if not video_id:
            skipped += 1
            continue

        attempts += 1
        if download_thumbnail(video_id, destination, args.timeout):
            downloaded += 1
            images[num] = image_file
            print(f"[OK] {num}: {image_file}")
        else:
            failed.append((num, video_id))
            print(f"[FAIL] {num}: {video_id}")

    if images:
        for db_path in DB_PATHS:
            if not db_path.exists():
                continue
            with sqlite3.connect(db_path) as connection:
                connection.executemany(
                    "UPDATE videos SET image_file = ? WHERE num = ?",
                    [(filename, num) for num, filename in images.items()],
                )
                connection.commit()

    print()
    print(f"Уже было на диске: {existing}")
    print(f"Скачано: {downloaded}")
    print(f"Пропущено без ссылки/по лимиту: {skipped}")
    print(f"Не удалось скачать: {len(failed)}")
    if failed:
        print("Неудачные номера: " + ", ".join(str(num) for num, _ in failed))
    print(f"Папка: {PREVIEWS_DIR}")
    print(f"Обновлено записей image_file: {len(images)}")
    if failed and downloaded == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
