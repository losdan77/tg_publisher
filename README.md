# tg_publisher

Автоматическое ведение Telegram-каналов одним ботом.

Сервис по расписанию берет промпт, отправляет его в OpenAI Responses API и публикует ответ в нужный Telegram-канал. К посту можно автоматически сгенерировать изображение через OpenAI или подобрать фотографию в Pexels. Управление сделано через веб-панель: можно добавлять каналы, менять cron, chat_id, промпты, визуальный стиль, включать/выключать каналы, делать тестовую публикацию и применять изменения без ручной правки файлов.

Админка закрыта nginx Basic Auth. Telegram webhook остается публичным, потому что Telegram должен до него достучаться, но он защищен секретным URL и опциональным Telegram secret token.

## Адрес

Production-домен по умолчанию:

```text
https://tg.memeinternet.site/admin
```

## Что где хранится

В репозитории:

```text
config/      # стартовые шаблоны каналов
prompts/     # стартовые шаблоны промптов
app/         # Python/FastAPI сервис
deploy/      # nginx
scripts/     # deploy, https, webhook
```

На VPS после первого запуска:

```text
data/config/channels.yaml  # живой конфиг, который меняет веб-панель
data/prompts/*.md          # живые промпты, которые меняет веб-панель
data/history/posts.sqlite3 # история опубликованных постов по каналам
data/certbot/              # сертификаты Let's Encrypt
```

GitHub Actions не перезаписывает `data/`, чтобы изменения из веб-панели не пропадали при деплое.

## Первый деплой на VPS

1. Направь DNS `A`-запись домена `tg.memeinternet.site` на IP VPS.

2. На Ubuntu server установи Docker:

```bash
sudo apt update
sudo apt install -y docker.io docker-compose-plugin rsync
sudo usermod -aG docker $USER
```

После `usermod` перелогинься по SSH.

3. Склонируй проект:

```bash
sudo mkdir -p /opt/tg-publisher
sudo chown -R $USER:$USER /opt/tg-publisher
cd /opt/tg-publisher
git clone <your-repo-url> .
```

4. Создай `.env`:

```bash
cp .env.example .env
nano .env
```

Минимально заполни:

```env
DOMAIN=tg.memeinternet.site
PUBLIC_BASE_URL=https://tg.memeinternet.site
CERTBOT_EMAIL=you@example.com

NGINX_BASIC_AUTH_USER=admin
NGINX_BASIC_AUTH_PASSWORD=strong-web-password

APP_UID=1000
APP_GID=1000
OPENAI_API_KEY=sk-...
PEXELS_API_KEY=... # только для режима поиска фотографий
TELEGRAM_BOT_TOKEN=123456789:...
TELEGRAM_WEBHOOK_SECRET=long-random-url-secret
TELEGRAM_WEBHOOK_SECRET_TOKEN=long-random-header-secret
ADMIN_API_TOKEN=long-random-admin-token
ADMIN_TELEGRAM_USER_IDS=123456789
```

Для случайных секретов удобно:

```bash
openssl rand -hex 32
```

`APP_UID` и `APP_GID` должны совпадать с пользователем, который владеет директорией проекта на VPS. Проверить можно так:

```bash
id -u
id -g
```

5. Запусти сервис:

```bash
bash scripts/deploy.sh
```

Если в `.env` забыта обязательная переменная, deploy остановится до запуска контейнеров и покажет имя пропущенного поля. Например, без `TELEGRAM_WEBHOOK_SECRET` приложение не сможет стартовать.

6. Выпусти HTTPS-сертификат:

```bash
bash scripts/init_https.sh
```

7. Зарегистрируй Telegram webhook:

```bash
bash scripts/set_webhook_docker.sh
```

8. Открой:

```text
https://tg.memeinternet.site/admin
```

Логин и пароль берутся из `NGINX_BASIC_AUTH_USER` и `NGINX_BASIC_AUTH_PASSWORD`.

## Как управлять каналами через веб

В админке можно:

- добавить новый канал кнопкой `+ Канал`;
- включить/выключить канал;
- изменить `chat_id`, cron, timezone, модель и лимиты;
- включить галочку `Учитывать историю постов` и выбрать количество прошлых публикаций;
- выбрать режим изображения: без картинки, генерация OpenAI или поиск фотографии в Pexels;
- задать отдельный авторский визуальный стиль для каждого канала;
- редактировать `Context JSON`;
- редактировать prompt-файл;
- нажать `Сохранить`, чтобы изменения применились;
- нажать `Опубликовать тест`, чтобы сразу отправить пост в выбранный канал;
- нажать `Reload`, если ты правил файлы руками на VPS.

Первый канал в шаблоне выключен (`enabled: false`), чтобы ничего случайно не публиковалось.

Успешно отправленные посты сохраняются в SQLite отдельно для каждого канала. Когда галочка
`Учитывать историю постов` включена, последние публикации добавляются в запрос к OpenAI с
указанием не повторять уже раскрытые темы. При выключенной галочке история продолжает
заполняться, но не передаётся модели.

## Изображения к постам

В настройках каждого канала есть три режима:

- `не добавлять` — публикация остаётся текстовой;
- `генерировать через OpenAI` — сервис формирует визуальное ТЗ из содержания нового поста и авторского стиля канала, затем создаёт картинку через `OPENAI_IMAGE_MODEL`;
- `искать фотографию в Pexels` — сервис формирует поисковый запрос по содержанию поста, выбирает подходящее фото и добавляет автора и ссылку на источник.

Для генерации используется тот же `OPENAI_API_KEY`. Для поиска нужно получить API-ключ Pexels и добавить в `.env` или GitHub secret `ENV_FILE`:

```env
PEXELS_API_KEY=your-pexels-key
```

Если текст вместе с подписью помещается в лимит Telegram, он публикуется одной записью с фото. Длинный текст отправляется сразу после фотографии отдельным сообщением без обрезки. По умолчанию при ошибке генерации, поиска или загрузки сервис публикует текст без картинки; это поведение можно выключить в настройках канала.

## Cron

Используется обычный 5-польный cron:

```text
minute hour day month weekday
```

Примеры:

```text
0 10 * * *      # каждый день в 10:00
30 18 * * 1-5  # по будням в 18:30
0 9,15 * * *   # каждый день в 09:00 и 15:00
```

Время считается в timezone конкретного канала, например `Europe/Moscow`.

## Telegram

Бот должен быть администратором канала.

Для публичного канала можно использовать:

```text
@channel_username
```

Для приватного канала обычно нужен numeric id:

```text
-1001234567890
```

Webhook нужен для команд боту:

```text
/channels
/publish test_ai_news
/reload
```

Команды принимаются только от пользователей из `ADMIN_TELEGRAM_USER_IDS`.

## GitHub Actions деплой

В GitHub Secrets добавь только доступ к VPS и один полный `.env`:

```text
VPS_HOST       # IP или домен VPS
VPS_USER       # SSH user
VPS_SSH_KEY    # приватный SSH-ключ для входа на VPS
ENV_FILE       # полный текст production .env
```

Опционально можно добавить:

```text
VPS_PORT       # если SSH не на 22 порту
VPS_APP_DIR    # если проект не в /opt/tg-publisher
```

`ENV_FILE` должен быть содержимым `.env` целиком, например:

```env
APP_ENV=production
LOG_LEVEL=INFO
DOMAIN=tg.memeinternet.site
PUBLIC_BASE_URL=https://tg.memeinternet.site
CERTBOT_EMAIL=you@example.com
CERTBOT_STAGING=false
NGINX_BASIC_AUTH_USER=admin
NGINX_BASIC_AUTH_PASSWORD=strong-web-password
APP_UID=1000
APP_GID=1000
OPENAI_API_KEY=sk-...
OPENAI_DEFAULT_MODEL=gpt-5.5
OPENAI_IMAGE_MODEL=gpt-image-1.5
OPENAI_TIMEOUT_SECONDS=60
IMAGE_TIMEOUT_SECONDS=120
PEXELS_API_KEY=
TELEGRAM_BOT_TOKEN=123456789:...
TELEGRAM_WEBHOOK_SECRET=long-random-url-secret
TELEGRAM_WEBHOOK_SECRET_TOKEN=long-random-header-secret
ADMIN_API_TOKEN=long-random-admin-token
ADMIN_TELEGRAM_USER_IDS=123456789
CHANNELS_CONFIG_PATH=config/channels.yaml
HISTORY_DB_PATH=data/history/posts.sqlite3
ENABLE_SCHEDULER=true
DRY_RUN=false
AUTO_SET_TELEGRAM_WEBHOOK=false
```

После push в `main` workflow:

1. ставит Python-зависимости;
2. валидирует стартовый конфиг;
3. запускает тесты;
4. загружает проект на VPS;
5. загружает `.env`;
6. выполняет `bash scripts/deploy.sh`.

После первого деплоя HTTPS достаточно выпустить один раз через `bash scripts/init_https.sh`. Дальше certbot-контейнер будет продлевать сертификат автоматически.

## Полезные команды на VPS

```bash
cd /opt/tg-publisher
docker compose ps
docker compose logs -f tg-publisher
docker compose logs -f nginx
bash scripts/deploy.sh
bash scripts/check_env.sh .env
bash scripts/init_https.sh
bash scripts/set_webhook_docker.sh
```

Если веб-панель не сохраняет данные и в логах есть `Permission denied`, значит `data/prompts`, `data/config` или `data/history` на VPS принадлежат не тому пользователю. Исправить:

```bash
cd /opt/tg-publisher
chown -R 1000:1000 data/config data/prompts data/history
bash scripts/deploy.sh
```

Если в `.env` стоят другие `APP_UID` и `APP_GID`, используй их вместо `1000:1000`.

## Частые ошибки

`telegram_webhook_secret Field required` в логах `tg-publisher` означает, что в `.env` или GitHub secret `ENV_FILE` нет строки:

```env
TELEGRAM_WEBHOOK_SECRET=long-random-url-secret
```

`unknown "admin_api_token" variable` в логах nginx означает, что nginx получил конфиг без подставленного `ADMIN_API_TOKEN`. Проверь, что в `.env` или `ENV_FILE` есть:

```env
ADMIN_API_TOKEN=long-random-admin-token
```

`401 invalid_api_key` или `Incorrect API key provided` означает, что OpenAI не принял `OPENAI_API_KEY`. В GitHub secret `ENV_FILE` строка должна выглядеть так:

```env
OPENAI_API_KEY=sk-...
```

Не вставляй имя переменной второй раз. Ошибочный вариант:

```env
OPENAI_API_KEY=OPENAI_API_KEY=sk-...
```

После исправления `.env` на VPS перезапусти:

```bash
cd /opt/tg-publisher
bash scripts/deploy.sh
```

## Локальная проверка

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
python scripts/validate_config.py
pytest -q
ruff check .
uvicorn app.main:app --reload
```

Если открываешь `http://127.0.0.1:8000/admin` напрямую без nginx, веб-панель попросит `ADMIN_API_TOKEN`.
