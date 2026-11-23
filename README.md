# Redroom Maps

Историческая карта с таймлайном, карточками стран и видео.

## Структура

```text
backend/        FastAPI, SQLAlchemy, Alembic
frontend/       Vue 3 + Vite
scripts/        импорт данных и вспомогательные скрипты
deploy/         Docker, nginx и настройки развёртывания
data/           данные, в git не попадают
logs/           локальные логи backend
```

## Требования

- Python 3.12+ (Docker-образ использует Python 3.14);
- Node.js 22+;
- Docker Desktop — для локального запуска полного стека.

## Локальная разработка

Backend:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
python backend\run.py
```

Frontend:

```powershell
cd frontend
npm ci
npm run dev:lan
```

- frontend: http://localhost:5173
- backend: http://localhost:8652

Если backend запущен не на `127.0.0.1:8652`, укажите адрес в
`REDROOM_BACKEND_URL` перед `npm run dev`.

В dev-режиме Vite проксирует запросы `/map`, `/data`, `/country`, `/tag`, `/video`, `/preview` на backend `http://127.0.0.1:8652`. Отдельный origin для API не нужен.

## Docker: локально как в проде

```powershell
cd deploy
docker compose up --build -d
```

Открыть: http://localhost:8080

Что запускается:

- `backend` — FastAPI + 2 Uvicorn-воркера;
- `nginx` — собранный фронтенд + прокси API;
- `data/runtime` монтируется в backend;
- `logs/` монтируется в backend;
- фронтенд использует относительные URL, поэтому один и тот же образ работает на `localhost`, по IP в LAN и на домене.

Конфиг берётся из `deploy/.env`. Важно запускать `docker compose` **из каталога `deploy`**: иначе Compose не прочитает этот файл.

Команды:

```powershell
cd deploy
docker compose ps
docker compose logs -f backend
docker compose logs -f nginx
docker compose down
```

После изменения frontend:

```powershell
docker compose up --build -d
```

После изменения только backend:

```powershell
docker compose up --build -d backend
docker compose restart nginx
```

После изменения карт в `data/runtime`:

```powershell
docker compose restart backend
```

## Переменные окружения

### Backend

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `REDROOM_RUNTIME_DIR` | `<проект>/data/runtime` | Каталог активных данных: `db`, `maps`, `previews`. В проде обычно указывает на `data/current` или конкретный release. |
| `REDROOM_DATA_DIR` | `<проект>/data` | Корень `data/`; используется для вычисления рабочих путей, в первую очередь `data/work`. На работу API напрямую не влияет. |
| `REDROOM_LOG_LEVEL` | `INFO` | Минимальный уровень логов: `TRACE`, `DEBUG`, `INFO`, `SUCCESS`, `WARNING`, `ERROR`, `CRITICAL`. Для диагностики API удобно `DEBUG`, для прода — `INFO` или `WARNING`. |
| `REDROOM_LOG_DIR` | `<проект>/logs` | Каталог файловых логов. В Docker обычно `/logs`. Должен быть доступен для записи; stderr-логи работают в любом случае. |
| `REDROOM_CORS_ORIGINS` | пусто | Дополнительные origin через запятую, если фронтенд и API живут на разных доменах, например `https://example.com,https://www.example.com`. При общей схеме «nginx + API» не нужен. |

Пример для локального запуска:

```text
REDROOM_RUNTIME_DIR=C:\Redroom_maps\data\runtime
REDROOM_LOG_LEVEL=INFO
```

Пример для прода:

```text
REDROOM_RUNTIME_DIR=/srv/redroom/data/current
REDROOM_LOG_DIR=/var/log/redroom
REDROOM_LOG_LEVEL=INFO
```

### Docker Compose (`deploy/.env`, не коммитится)

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `VITE_API_URL` | пусто | Origin API, вшиваемый в JS при сборке. Пусто — использовать тот же origin (рекомендуется): nginx проксирует API. Абсолютный URL нужен только при раздельном хостинге фронтенда и backend. После изменения — rebuild nginx. |
| `BACKEND_UPSTREAM` | `backend:8652` | Адрес FastAPI **без** `http://`, как его видит nginx. В Compose — имя сервиса `backend`; если backend запущен на хосте — `host.docker.internal:8652`. |
| `WEB_PORT` | `8080` | Порт на хосте, который публикует nginx. На сервере обычно `80`. |
| `WEB_BIND` | `0.0.0.0` | Интерфейс, на котором публикуется nginx. `127.0.0.1` — если TLS терминирует reverse proxy на хосте. |
| `HOST_RUNTIME_DIR` | `../data/runtime` | Каталог данных на хосте, монтируется в `/data/runtime`. Для релиза удобно указать `/srv/redroom/data/current`. |
| `HOST_LOG_DIR` | `../logs` | Каталог логов на хосте, монтируется в `/logs`. |
| `WEB_CONCURRENCY` | `2` | Количество Uvicorn-воркеров в backend-контейнере. Больше воркеров — больше потребление RAM. Для слабого хостинга можно поставить `1`. |
| `REDROOM_LOG_LEVEL` | `INFO` | Уровень логов backend внутри контейнера. |
| `REDROOM_CORS_ORIGINS` | пусто | Дополнительные origin для CORS при раздельном хостинге. |

Пример `deploy/.env`:

```text
VITE_API_URL=
BACKEND_UPSTREAM=backend:8652
WEB_BIND=0.0.0.0
WEB_PORT=8080
HOST_RUNTIME_DIR=../data/runtime
HOST_LOG_DIR=../logs
WEB_CONCURRENCY=2
REDROOM_LOG_LEVEL=INFO
```

## Данные

`data/` полностью в `.gitignore`.

```text
data/work/                         ручная работа, в прод не едет
  spreadsheets/                    periods_for_export.csv, Statictics.xlsx
  maps/geojson/years/              годовые GeoJSON
  maps/geojson/auxiliary/          вспомогательные GeoJSON
  maps/pictures/                   изображения для QGIS
  schemes/                         drawio-схемы и их txt
  periods/histories/               выгрузки историй — источник для групп истории
  periods/selections/              выгрузки подборок

data/runtime/                      нужно приложению
  db/redroom_maps.db               SQLite-база: страны, видео, периоды, трансформации
  maps/topojson/                   исходные/резервные TopoJSON-карты
  maps/gzip/                       предварительно сжатые карты, которые отдаёт сайт
  maps/color_ids.json              соответствие colorId и цветов на карте
  previews/                        локальные превью видео

data/releases/                     готовые версии данных для прода
data/backups/                      резервные копии БД и данных
data/temp/                         временные и отладочные файлы
```

Сайт использует `data/runtime`, `data/work` не нужен в контейнере.
Для работы сайта достаточно `db`, `maps/gzip`, `maps/color_ids.json` и `previews`; `maps/topojson` нужен как fallback и исходник для пересжатия.

## Изменение данных

Импорт периодов:

```powershell
python scripts\import_periods.py
```

Источник: `data/work/spreadsheets/periods_for_export.csv`.
В CSV `is_main=1` — основная тема, `0` или `2` — косвенное упоминание.

Карты:

```powershell
python scripts\convert_geojson.py
python scripts\compress_maps.py
```

- GeoJSON: `data/work/maps/geojson/years/` и `auxiliary/`;
- TopoJSON и gzip: `data/runtime/maps/`.

После изменения карт перезапустить backend, чтобы пересчиталась версия карт:

```powershell
cd deploy
docker compose restart backend
```

Превью:

```powershell
python scripts\download_video_previews.py
```

Превью сохраняются в `data/runtime/previews`, ссылки — в БД.

## Группы историй

Режим «вся история» не должен смешивать все страны мира. Поэтому история
строится по группам из `data/work/periods/histories`:

- `index.csv` — список групп и их современных стран;
- `russia.csv`, `yugoslavia.csv` и т.д. — исторические страны группы.

Из них генерируется `backend/app/data/history_groups.json`:

- `country_groups` — основная группа каждой страны;
- `groups` — все исторические страны, входящие в группу.

Файл коммитится в git, потому что нужен на сервере, где `data/work`
отсутствует. Для современной страны используется группа, где она указана
в `members`. Для исторической страны — первая подходящая группа. Широкие
группы `europe`, `africa`, `america` намеренно не используются: они
перекрывают почти весь мир.

После изменения `data/work/periods/histories`:

```powershell
python scripts\build_history_groups.py
python scripts\check_history.py
```

Первый скрипт пересобирает JSON, второй проверяет, что видео не попадают
в чужую историю. После этого закоммитить `backend/app/data/history_groups.json`
и пересобрать backend:

```powershell
cd deploy
docker compose up --build -d backend
docker compose restart nginx
```

Для России, Украины и Беларуси используется одна группа `east_slavs`.
Османский Крым в неё входит, поэтому видео, где он упомянут **косвенно**,
остаётся в истории косвенным упоминанием, но не становится основной темой.

## Бэкапы

БД можно копировать на работающем backend — SQLite backup API делает
согласованный снимок:

```powershell
python scripts\backup_db.py
```

По умолчанию файл попадает в `data/backups/redroom_maps-<дата>.db`.
Карты и превью не меняются при работе сайта, их достаточно копировать
вместе с релизом данных.

## Версионирование и кэш

- Версия карт считается один раз на воркер при старте.
- На Docker Desktop для Windows этот стартовый скан может занять пару секунд из-за bind mount; после старта `/map/version` отвечает быстро.
- Версия БД определяется по `mtime` и размеру файла БД.
- Версия данных также включает версию `backend/app/data/history_groups.json`.
- История стран кэшируется в памяти воркера по группе истории
  (`russia`, `ukraine`, `belarus` → `east_slavs`).
- При изменении БД или групп истории кэш сбрасывается.
- `/map/version` и `/data/version` отдаются с `no-store`.
- Карты и динамические JSON используют версионированные URL и HTTP-кэш.

После изменения карт нужен restart backend. После изменения БД перезапуск не требуется.

## Прод

### 1. Подготовить данные

```powershell
# локально: копия только того, что нужно сайту
robocopy data\runtime data\releases\2026-11-20 /MIR
```

Загрузить на сервер (rsync сохраняет структуру и удаляет лишнее в релизе):

```bash
rsync -av --delete data/runtime/ user@server:/srv/redroom/data/releases/2026-11-20/
```

На сервере:

```text
/srv/redroom/
  data/
    releases/2026-11-20/
    current -> releases/2026-11-20
```

`current` — симлинк на активный релиз. Обновление данных = загрузка нового
каталога и переключение симлинка. Откат — вернуть симлинк на предыдущий
release и снова пересоздать backend.

### 2. Настроить `deploy/.env`

```text
VITE_API_URL=
BACKEND_UPSTREAM=backend:8652
WEB_BIND=127.0.0.1
WEB_PORT=8080
HOST_RUNTIME_DIR=/srv/redroom/data/current
HOST_LOG_DIR=/srv/redroom/logs
WEB_CONCURRENCY=2
REDROOM_LOG_LEVEL=INFO
```

`WEB_BIND=127.0.0.1` — если на хосте стоит Caddy/nginx с TLS. Если
контейнерный nginx сам слушает 80, используйте `WEB_BIND=0.0.0.0`,
`WEB_PORT=80`.

`VITE_API_URL` пустой, потому что nginx отдаёт фронтенд и API с одного
домена. Менять его нужно только при раздельном хостинге.

### 3. Запустить

```bash
cd deploy
docker compose up --build -d
curl http://127.0.0.1:8080/ping
```

### 4. Проверить

Из корня репозитория:

```bash
python scripts/smoke_test.py --base-url https://example.com
```

Скрипт проверяет `/ping`, версии, карты, страны и теги. Запускать можно и
локально, и на сервере.

### 5. HTTPS

TLS удобнее терминировать на хосте (Caddy, host-nginx + certbot) или добавить
certbot в nginx-контейнер. Пример для host-nginx: он слушает 443 и
проксирует на `127.0.0.1:8080`. В этом случае `WEB_PORT=8080`.

### Обновление

- **Код/фронтенд:** `git pull && docker compose up --build -d`.
- **Данные:** переключить `current` и пересоздать backend:
  `docker compose up -d --force-recreate backend && docker compose restart nginx`.
  `restart` может сохранить старый bind-mount, `--force-recreate` гарантированно
  перечитает симлинк.
- **Только БД:** перезапуск не нужен, версия БД определяется по `mtime`.
- После отдельного `docker compose up -d backend` перезапустить nginx:
  `docker compose restart nginx`. Nginx кэширует IP backend при старте и
  иначе может отдавать 502, пока контейнер не будет пересоздан.

Nginx отдаёт frontend из своего образа и проксирует API на backend.
Карты и превью пока идут через backend; позже их можно вынести в nginx/CDN.

## Ориентиры по ресурсам

Текущий размер данных:

- `data/runtime` — около **218 МБ**:
  - TopoJSON — ~156 МБ;
  - gzip — ~55 МБ;
  - превью — ~5.5 МБ;
  - БД — ~1 МБ;
- `data/work` — около **3 ГБ**, но в прод его выкладывать не нужно;
- Docker-образы и код добавляют ещё несколько сотен мегабайт.
- Сборка образов на сервере требует ~1.5–2 ГБ RAM и несколько ГБ диска под
  кэш. На VPS с 1 ГБ добавьте swap или собирайте образы локально и
  публикуйте их в registry.

Расход RAM на локальном Docker:

- nginx — ~8 МБ;
- backend с 2 воркерами — ~220 МБ в простое.

Практические ориентиры:

- **512 МБ RAM** — минимум для одного воркера и небольшого трафика;
- **1 ГБ RAM** — комфортно для 2 воркеров и презентации;
- **13 ГБ диска** — с большим запасом: runtime ~218 МБ;
- квота **13 ГБ под БД** проекту не нужна: база — SQLite-файл ~1 МБ.

Для хостинга важно не только место, но и возможность запускать **постоянный Python-процесс/ASGI** и, желательно, Docker. Если тариф предоставляет только PHP/статические сайты без SSH и долгоживущих процессов, FastAPI там не запустится: фронтенд можно отдать статикой, а backend придётся разместить на VPS или в отдельном Python-хостинге.

### Reg.ru Хост-0

Тариф подходит по диску (13 ГБ) и с запасом покрывает данные, но это **shared-хостинг**, а не VPS. Перед оплатой проверить в панели и у поддержки:

- есть ли SSH;
- можно ли запускать долгоживущий процесс (uvicorn/gunicorn) и открывать свой порт;
- есть ли Docker (на shared-хостинге обычно нет);
- поддержан ли Python 3.12+ (обычно только PHP).

Если хотя бы SSH и постоянного Python-процесса нет, схема такая:

- домен и DNS — в Reg.ru;
- фронтенд (`frontend/dist`) — статикой на shared-хостинге;
- backend — на VPS или Python-хостинге, nginx проксирует `/map`, `/data`,
  `/country`, `/video`, `/tag`, `/preview` на него.

Для VPS минимум: 1 vCPU, 1 ГБ RAM, 10 ГБ SSD. Docker на 1 ГБ работает, но лучше 2 ГБ или swap.

## Чек-лист перед заливом

- [ ] `deploy/.env` создан из `.env.example` и не попал в git;
- [ ] `data/runtime` загружен: `db`, `maps/topojson`, `maps/gzip`,
      `maps/color_ids.json`, `previews`;
- [ ] после загрузки карт backend перезапущен;
- [ ] `python scripts/smoke_test.py --base-url https://домен` проходит;
- [ ] домен указывает на сервер, HTTPS работает;
- [ ] наружу открыты только 22/80/443; 8080 и 8652 не опубликованы в интернет;
- [ ] настроены бэкапы БД (`scripts/backup_db.py`) и ротация логов Docker;
- [ ] на VPS с 1 ГБ RAM: `WEB_CONCURRENCY=1` и swap;
- [ ] проверены `docker compose ps` и `docker compose logs` после рестарта.

## Проверки

```powershell
# backend
python -m compileall backend scripts

# frontend
cd frontend
npm run type-check
npm run build-only
npx vitest run --maxWorkers=1
cd ..

# работающий стенд
python scripts\smoke_test.py --base-url http://localhost:8080

# история стран
python scripts\check_history.py
```

## Что не коммитить

- `data/`
- `logs/`
- `frontend/dist/`
- `venv/`, `.venv/`
- `frontend/node_modules/`
- `.env`, `deploy/.env`
- `logs/`, `data/`

`frontend/package-lock.json` коммитить нужно.
