import argparse
import csv
import re
import shutil
import tempfile
from collections import defaultdict
from pathlib import Path

from src.database.orm import Database
from src.database.videos import VideoModel


CSV_PATH = Path(__file__).parent / "info.csv"
DB_PATH = Path(__file__).parent / "redroom_maps.db"

MENTION = "Упомянуты видео"
WORTHY = "Достойны отдельного выпуска"

ROMAN = {
    "i": "1",
    "ii": "2",
    "iii": "3",
    "iv": "4",
    "v": "5",
    "vi": "6",
    "vii": "7",
    "viii": "8",
    "ix": "9",
    "x": "10",
    "xi": "11",
    "xii": "12",
    "xiii": "13",
    "xiv": "14",
    "xv": "15",
    "xvi": "16",
    "xvii": "17",
    "xviii": "18",
    "xix": "19",
    "xx": "20",
    "xxi": "21",
}


def norm(value: str) -> str:
    value = value.lower().replace("ё", "е")
    value = re.sub(r"//\s*redroom", " ", value)
    value = re.sub(r"[^0-9a-zа-я]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def with_arabic(text: str) -> str:
    return " ".join(ROMAN.get(token, token) for token in text.split())


def strip_parenthetical(value: str) -> str:
    value = re.sub(r"\([^)]*\)", " ", value)
    return value.strip(" .-–—;:\t")


def split_items(text: str) -> list[str]:
    parts: list[str] = []
    depth = 0
    current = ""

    for char in text:
        if char == "(":
            depth += 1
        elif char == ")":
            depth = max(0, depth - 1)

        if char in ",;" and depth == 0:
            parts.append(current)
            current = ""
        else:
            current += char

    parts.append(current)
    return [part.strip(" .;\n\t") for part in parts if part.strip(" .;\n\t")]


def key(num: int | str, item: str) -> tuple[int, str]:
    return (int(num), norm(strip_parenthetical(item)))


def make_key(num: int, item: str) -> tuple[int, str]:
    return key(num, item)


# Пункты, которые нельзя однозначно связать с одним видео.
# Значение — причина, которая попадёт в отчёт.
MENTION_EXCLUSIONS: dict[tuple[int, str], str] = {
    make_key(3460, "визы и дирижабли"): "пункт объединяет два видео, одно из них текущее",
    make_key(3350, "история письменности"): "видео про историю письменности удалено/отсутствует",
    make_key(2240, "глобализм"): "есть только общий выпуск про глобализацию и торговлю, связь неоднозначна",
    make_key(2240, "война Италии и Эфиопии при Муссолини"): "в базе есть только война XIX века, не 1935 года",
    make_key(2700, "Итало-эфиопская война"): "в контексте Муссолини это война 1935 года, а в базе только XIX век",
    make_key(1900, "битва на Калке Фридрих 2 великий"): "в одном пункте смешаны два разных сюжета",
    make_key(1750, "предыдущее видео (про викингов)"): "не указано, какое именно предыдущее видео",
    make_key(1020, "про Корею ненадолго до этого видео (про Мьянму)"): "непонятно, какое из видео про Корею имеется в виду",
    make_key(1500, "Котолисы+"): "не видео и не название ролика",
    make_key(1460, "Котолисы- (но видео классное и рассказано хорошо)"): "не видео и не название ролика",
}


# Ручные сопоставления там, где начало названия не совпадает дословно,
# но видео определяется однозначно.
MENTION_OVERRIDES: dict[tuple[int, str], list[int]] = {
    make_key(3530, "как чад феодалы стали вирджин дворянами"): [3210],
    make_key(3480, "Манса Муса"): [2930],
    make_key(3480, "скальды"): [1130],
    make_key(3460, "кто такой Уинстон Черчиль"): [3140],
    make_key(3150, "четвёртый крестовый поход"): [1970],
    make_key(2850, "международные языки"): [2770],
    make_key(2850, "про полярников видос"): [2780],
    make_key(2830, "большой скачок (оба выпуска)"): [1090, 1100],
    make_key(2650, "большой скачок предпосылки"): [1090],
    make_key(2640, "Сулла"): [560],
    make_key(2550, "Шри-Ланка гражданская война и национализм"): [2420],
    make_key(2430, "история себастьянизма"): [710],
    make_key(2240, "развал Австро-венгрии"): [1790],
    make_key(2220, "все 4 видоса про освобождение Ирландии"): [1320, 1330, 1340, 1350],
    make_key(2090, "императрица Ирина"): [1150],
    make_key(1970, "Венеция"): [1380],
    make_key(1900, "завоевание монголами центральной Азии"): [880],
    make_key(1900, "Венеция"): [1380],
    make_key(1810, "3 видоса про империю ацтеков"): [420, 870, 970],
    make_key(1790, "оба видоса про раздел речи Посполитой"): [1040, 1060],
    make_key(1630, "объединение Германии"): [1220],
    make_key(1580, "гражданская война в США (обе части)"): [130, 140],
    make_key(1500, "про Эхнатона"): [540],
    make_key(1460, "история Ирландии (весь плейлист разом, там 6 видосов)"): [
        630,
        1320,
        1330,
        1340,
        1350,
        1470,
    ],
    make_key(1460, "Таити"): [690],
    make_key(1450, "видосы про троецарствие"): [1110, 1120],
    make_key(1450, "объединение Германии"): [1220],
    make_key(1440, "топ коррупционеров в истории"): [620],
    make_key(1390, "объединение Германии"): [1220],
    make_key(1180, "оба видео про разделы речи Посполитой"): [1040, 1060],
    make_key(1170, "императрица Ирина"): [1150],
    make_key(1050, "себастьянизм"): [710],
    make_key(940, "оба видео про самураев Японии"): [70, 80],
    make_key(710, "Фердинанд и Изабелла"): [230],
    make_key(380, "предыдущее видео перед этим (Госпитальеры)"): [370],
    make_key(3360, "весь цикл видео про Югославию"): [2000, 2030, 2050],
    make_key(1650, "Фридрих 2"): [380],
}


# Решения по блоку «Достойны отдельного выпуска».
# released — номера уже вышедших видео, planned — темы без видео, complex — спорный случай.
IDEAS_DECISIONS: dict[tuple[int, str], tuple[str, list[int] | str | None]] = {
    make_key(3490, "реставрация Мэйдзи"): ("planned", None),
    make_key(3480, "восстание Боудикки"): ("planned", None),
    make_key(3440, "Жанна д'Арк"): ("planned", None),
    make_key(3260, "Алжир"): ("planned", None),
    make_key(3180, "республиканская и демократическая партии"): ("planned", None),
    make_key(2990, "взлом Энигмы"): ("planned", None),
    make_key(2980, "Тамерлан"): ("planned", None),
    make_key(2790, "китайская династия Сун"): ("planned", None),
    make_key(2760, "Хаммурапи"): ("planned", None),
    make_key(2670, "Маргарет Тэтчер"): ("planned", None),
    make_key(2550, "Чжэн Хэ (уже выпущен)"): ("released", [2810]),
    make_key(2480, "историческая методология археология и сравнительное языкознание"): ("planned", None),
    make_key(2470, "Тамерлан"): ("planned", None),
    make_key(2190, "Гамаль Абдель Насер (это видео уже есть)"): ("released", [3400]),
    make_key(2190, "персидский царь Дарий 1"): ("planned", None),
    make_key(2190, "император Траян"): ("planned", None),
    make_key(2120, "Салах ад Дин"): ("released", [3100]),
    make_key(2100, "Умр ибн аль Хаттаб"): ("planned", None),
    make_key(1830, "культурная революция в Китае"): ("released", [2830]),
    make_key(1740, "Кнуд Великий"): ("planned", None),
    make_key(1670, "Алиенора Аквитанская"): ("released", [1680]),
    make_key(1650, "Салах эд Дин"): ("released", [3100]),
    make_key(1600, "Савонарола"): ("planned", None),
    make_key(1480, "Альфонсо де Альбукерке"): ("planned", None),
    make_key(1450, "Юань Шикай и Сунь Ятсен"): ("planned", None),
    make_key(1260, "император Диоклетиан"): ("planned", None),
    make_key(1260, "император Константин 1"): ("planned", None),
    make_key(940, "реставрация Мэйдзи"): ("planned", None),
    make_key(370, "Фридрих 2"): (
        "complex",
        "подходят два видео: 380 «Император Фридрих II» и 490 «Фридрих II Великий»",
    ),
    make_key(170, "императрица Мария Терезия"): ("planned", None),
    make_key(110, "правление Изабеллы Кастильской"): ("released", [230]),
    make_key(100, "император Юстиниан"): ("planned", None),
    make_key(100, "императрица Феодора"): ("planned", None),
}

# Особый случай: у 2190 два блока «Достойны…» — в середине и в конце.
IDEAS_2190 = [
    "персидский царь Дарий 1",
    "император Траян",
    "Гамаль Абдель Насер (это видео уже есть)",
]

# Блоки упоминаний, которые нельзя использовать по правилу «только в конце».
MENTION_BLOCK_SKIPS: dict[int, str] = {
    2790: "блок «Упомянуты видео» стоит перед блоком «Достойны…»",
    2480: "блок «Упомянуты видео» стоит перед блоком «Достойны…»",
    1740: "блок «Упомянуты видео» стоит перед блоком «Достойны…»",
    1600: "блок «Упомянуты видео» стоит перед блоком «Достойны…»",
    1260: "блок «Упомянуты видео» стоит перед блоком «Достойны…»",
    1640: "после списка упоминаний идёт продолжение описания",
}


def parse_csv() -> dict[int, dict]:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as file:
        rows = list(csv.reader(file, delimiter=";"))

    best: dict[int, dict] = {}
    for row in rows:
        if len(row) < 5 or not row[0].strip().isdigit():
            continue
        num = int(row[0])
        if num not in best or len(row[4]) > len(best[num]["description"]):
            best[num] = {
                "num": num,
                "title": row[1].strip(),
                "description": row[4],
            }
    return best


def mention_block_items(description: str) -> tuple[list[str] | None, str | None]:
    index = description.find(MENTION)
    if index < 0:
        return None, None

    worthy_index = description.find(WORTHY)
    if worthy_index >= 0 and index < worthy_index:
        return None, "перед «Достойны…»"

    tail = description[index + len(MENTION):].lstrip(" :\t")
    if WORTHY in tail:
        tail = tail.split(WORTHY, 1)[0]
    return split_items(tail), None


def ideas_block_items(num: int, description: str) -> list[str]:
    if num == 2190:
        return IDEAS_2190

    index = description.rfind(WORTHY)
    if index < 0:
        return []

    tail = description[index + len(WORTHY):].lstrip(" :\t")
    if MENTION in tail:
        tail = tail.split(MENTION, 1)[0]
    return split_items(tail)


def auto_mention_num(
    item: str, source_num: int, titles: list[dict]
) -> int | None:
    item_norm = norm(strip_parenthetical(item))
    if not item_norm:
        return None
    item_arabic = with_arabic(item_norm)

    matches: list[int] = []
    for title in titles:
        if title["num"] == source_num:
            continue

        matched = False
        if item_norm == title["norm"] or item_arabic == title["arabic"]:
            matched = True
        elif (
            title["norm"].startswith(item_norm + " ")
            or title["arabic"].startswith(item_arabic + " ")
        ):
            matched = True
        elif (
            item_norm.startswith(title["norm"] + " ")
            or item_arabic.startswith(title["arabic"] + " ")
        ):
            matched = True

        if matched:
            matches.append(title["num"])

    unique = list(dict.fromkeys(matches))
    return unique[0] if len(unique) == 1 else None


def dedupe(values: list[int]) -> list[int]:
    return list(dict.fromkeys(values))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Импортировать упоминания и идеи видео из info.csv"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="только показать отчёт, не менять базу",
    )
    args = parser.parse_args()

    rows = parse_csv()

    with Database.session() as session:
        videos = session.query(VideoModel).all()
        titles = [
            {
                "num": video.num,
                "title": video.title,
                "norm": norm(video.title),
                "arabic": with_arabic(norm(video.title)),
            }
            for video in videos
        ]
        titles_by_num = {video.num: video.title for video in videos}

        mentioned: dict[int, list[int]] = defaultdict(list)
        ideas_released: dict[int, list[int]] = defaultdict(list)
        ideas_planned: dict[int, list[str]] = defaultdict(list)

        complex_cases: list[tuple[int, str, str, str]] = []
        expanded: list[tuple[int, str, list[int]]] = []
        used_mention_keys: set[tuple[int, str]] = set()
        used_ideas_keys: set[tuple[int, str]] = set()

        for num, row in rows.items():
            description = row["description"]
            title = row["title"]

            # --- «Упомянуты видео» ---
            items, skip_reason = mention_block_items(description)
            if num in MENTION_BLOCK_SKIPS:
                reason = MENTION_BLOCK_SKIPS[num]
                raw_items = items or []
                if not raw_items:
                    index = description.find(MENTION)
                    if index >= 0:
                        tail = description[index + len(MENTION):].lstrip(" :\t")
                        if WORTHY in tail:
                            tail = tail.split(WORTHY, 1)[0]
                        raw_items = split_items(tail)
                complex_cases.append(
                    (
                        num,
                        title,
                        "блок упоминаний пропущен",
                        f"{reason}. Пункты: {', '.join(raw_items) or '—'}",
                    )
                )
                items = None
            elif skip_reason:
                complex_cases.append(
                    (num, title, "блок упоминаний пропущен", skip_reason)
                )
                items = None

            if items is not None:
                if num == 1500:
                    items = ["про Эхнатона", "Котолисы+"]
                elif num == 1460:
                    expanded_items: list[str] = []
                    for item in items:
                        if item.lower().startswith("таити"):
                            expanded_items.extend(
                                [
                                    "Таити",
                                    "Котолисы- (но видео классное и рассказано хорошо)",
                                ]
                            )
                        else:
                            expanded_items.append(item)
                    items = expanded_items

                for item in items:
                    item_key = key(num, item)
                    if item_key in MENTION_EXCLUSIONS:
                        complex_cases.append(
                            (
                                num,
                                title,
                                item,
                                MENTION_EXCLUSIONS[item_key],
                            )
                        )
                        used_mention_keys.add(item_key)
                        continue

                    nums = MENTION_OVERRIDES.get(item_key)
                    if nums is not None:
                        used_mention_keys.add(item_key)
                        if len(nums) > 1:
                            expanded.append((num, item, nums))
                    else:
                        auto_num = auto_mention_num(item, num, titles)
                        if auto_num is None:
                            complex_cases.append(
                                (
                                    num,
                                    title,
                                    item,
                                    "не удалось однозначно сопоставить с видео",
                                )
                            )
                            continue
                        nums = [auto_num]

                    mentioned[num].extend(nums)

            # --- «Достойны отдельного выпуска» ---
            idea_items = ideas_block_items(num, description)
            for item in idea_items:
                item_key = key(num, item)
                decision = IDEAS_DECISIONS.get(item_key)
                if decision is None:
                    raise RuntimeError(
                        f"Нет решения для идеи: {num} {item!r} ({item_key})"
                    )
                used_ideas_keys.add(item_key)
                kind, payload = decision

                if kind == "released":
                    assert isinstance(payload, list)
                    ideas_released[num].extend(payload)
                elif kind == "planned":
                    ideas_planned[num].append(strip_parenthetical(item))
                elif kind == "complex":
                    complex_cases.append(
                        (
                            num,
                            title,
                            item,
                            str(payload),
                        )
                    )
                else:
                    raise RuntimeError(f"Неизвестный тип решения: {kind}")

        # Проверяем, что все ручные правила были использованы.
        unused_mentions = (
            set(MENTION_OVERRIDES) | set(MENTION_EXCLUSIONS)
        ) - used_mention_keys
        unused_ideas = set(IDEAS_DECISIONS) - used_ideas_keys
        if unused_mentions:
            raise RuntimeError(
                "Не использованы ручные правила упоминаний: "
                + ", ".join(map(str, sorted(unused_mentions)))
            )
        if unused_ideas:
            raise RuntimeError(
                "Не использованы решения по идеям: "
                + ", ".join(map(str, sorted(unused_ideas)))
            )

        # Дубликаты и пустые значения.
        for num in list(mentioned):
            mentioned[num] = dedupe(mentioned[num])
            if not mentioned[num]:
                del mentioned[num]
        for num in list(ideas_released):
            ideas_released[num] = dedupe(ideas_released[num])
            if not ideas_released[num]:
                del ideas_released[num]
        for num in list(ideas_planned):
            ideas_planned[num] = list(dict.fromkeys(ideas_planned[num]))
            if not ideas_planned[num]:
                del ideas_planned[num]

        # Применяем ко всем видео: у видео без данных поля остаются пустыми.
        for video in videos:
            video.mentioned = mentioned.get(video.num) or None
            video.ideas_released = ideas_released.get(video.num) or None
            video.ideas_planned = ideas_planned.get(video.num) or None

        # Убираем тестовые данные, оставленные в 3680.
        if 3680 in titles_by_num:
            test_video = session.get(VideoModel, 3680)
            test_video.description = None

        print("Видео в базе:", len(videos))
        print(
            "С упоминаниями:",
            len(mentioned),
            "видео /",
            sum(len(value) for value in mentioned.values()),
            "ссылок",
        )
        print(
            "С уже вышедшими идеями:",
            len(ideas_released),
            "видео /",
            sum(len(value) for value in ideas_released.values()),
            "ссылок",
        )
        print(
            "С планами:",
            len(ideas_planned),
            "видео /",
            sum(len(value) for value in ideas_planned.values()),
            "тем",
        )

        if expanded:
            print("\nМНОГОРОЛИКОВЫЕ ПУНКТЫ:")
            for num, item, nums in expanded:
                print(f"  [{num}] {item!r} -> {nums}")

        if complex_cases:
            print("\nСЛОЖНЫЕ СЛУЧАИ (не добавлены):")
            for num, title, item, reason in complex_cases:
                print(f"  [{num}] {title}")
                print(f"      пункт: {item}")
                print(f"      причина: {reason}")

        if args.dry_run:
            print("\nDRY RUN: база не изменена.")
            session.rollback()
            return

        backup_dir = Path(tempfile.gettempdir()) / "opencode"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_path = backup_dir / "redroom_maps_before_video_links.db"
        shutil.copy2(DB_PATH, backup_path)
        print(f"\nРезервная копия: {backup_path}")

        session.commit()
        print("База обновлена.")


if __name__ == "__main__":
    main()
