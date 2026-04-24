# Video Ingestion — приём YouTube‑видео как контекст

> Справочный документ для агентов First‑Agent. Описывает **стабильный, трёхслойный
> workflow** превращения YouTube‑видео в исследовательскую заметку формата
> [`knowledge/research/<slug>.md`](../knowledge/README.md). Основан на разборе
> [agent‑video‑research.md](../knowledge/research/agent-video-research.md) (синтез 5
> видео) и ретроспективе того, что пошло не так на первой попытке.

## TL;DR

1. **Tier 0 (default):** Gemini 2.x с `file_data.file_uri = <youtube-url>`. Один API‑вызов,
   Google сам ингестит видео+аудио+визуальный поток, возвращает структурированный JSON.
2. **Tier 1 (fallback):** `yt-dlp` → субтитры/аудио → опционально frames+VLM через
   OpenRouter (vision‑модель). Когда Gemini не подходит или нужен независимый канал.
3. **Tier 2 (last resort):** Playwright‑скрейпер публичных сервисов (`notegpt.io`, `kome.ai`).
   Хрупко, без визуала — только если Tier 0/1 недоступны.

**Дефолтный контракт для всех тиров:** на вход — YouTube URL, на выход —
канонический артефакт `artifacts/<video_id>/final.md` + `meta.json`, совместимый с
промптом [`knowledge/prompts/ingest-youtube-video.md`](../knowledge/prompts/ingest-youtube-video.md).

Референсная реализация — в
[`knowledge/research/video-ingestion-poc/`](../knowledge/research/video-ingestion-poc/).

---

## 1. Почему три тира, а не один

Первая попытка синтезировать 5 видео
([PR #5](https://github.com/GITcrassuskey-shop/First-Agent/pull/5)) натолкнулась на
**IP‑фингерпринтинг YouTube против датацентровых диапазонов**. Одновременно
отвалились:

| Инструмент | Симптом | Корневая причина |
|---|---|---|
| `youtube-transcript-api` | `RequestBlocked: YouTube is blocking requests from your IP` | Датацентровый IP агента. |
| `yt-dlp` (прямой HTTP) | `playability_status: LOGIN_REQUIRED` даже с cookies из локального Chrome | Тот же IP, что и браузер агента. |
| `kome.ai` (free tier) | После 1 видео отдал paywall $2.50 | A/B‑ротация их free tier. |
| `notegpt.io` | Частичный транскрипт (`Read More` collapsed) | Их UI‑логика. |

Что **сработало в итоге:** `notegpt.io` через Playwright с программным раскрытием всех
`Read More` блоков. Это хрупко: 15 транскриптов/мес без логина, ToS может поменяться
в любой день. Поэтому нужен layered‑подход, где основной канал — независим от
сторонних скрейперов.

**Второй вывод:** plain‑транскрипт недостаточен для технических видео. 4 из 5 видео в
первой попытке содержали диаграммы, куски кода на экране, терминальный вывод, слайды.
Текстовая каптча пропускает этот пласт. Нужна **мультимодальная** обработка — не OCR
(плохо с цветной подсветкой и диаграммами), а VLM (vision‑language model).

---

## 2. Tier 0 — Gemini Direct YouTube URL

### Когда использовать

- Дефолт для всех новых задач.
- Видео ≤ 1 часа (Gemini 2.x Flash) или ≤ 2 часов (Pro).
- Публичное видео (у приватных `fileData.file_uri` отдаст 400).

### Как работает

Gemini принимает YouTube URL как `fileData.file_uri` и **фетчит видео со стороны Google** —
с резидентной инфраструктуры, которую YouTube не блокирует. Модель одновременно
обрабатывает аудиодорожку, auto‑captions (включая переводы), видеопоток (кадр за кадром
на ~1 fps) и on‑screen text. Ответ — обычный текстовый/JSON аутпут.

Ссылки: [Gemini API — Video Understanding](https://ai.google.dev/gemini-api/docs/video-understanding),
 [практический гайд](https://gemilab.net/en/articles/gemini-api/gemini-25-pro-video-understanding-practical-guide).

### Минимальный вызов

```python
from google import genai
from google.genai import types

client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=types.Content(parts=[
        types.Part(file_data=types.FileData(
            file_uri="https://www.youtube.com/watch?v=VIDEO_ID",
            mime_type="video/mp4",
        )),
        types.Part(text=PROMPT),  # см. knowledge/prompts/ingest-youtube-video.md
    ]),
    config=types.GenerateContentConfig(response_mime_type="application/json"),
)
```

### Сильные и слабые стороны

**+** Один вызов, одна зависимость, весь контекст (текст+визуал) — на стороне Google.<br/>
**+** Стоимость на Flash ≈ $0.01–0.05 за 45‑минутное видео.<br/>
**+** Автоматическая обработка визуального контента — без ручного sampling frames.<br/>
**+** Нет IP‑блокировки (запрос идёт от агента → к Gemini → к YouTube).<br/>
**−** Дневной лимит free tier: 8 часов YouTube‑видео в сутки суммарно.<br/>
**−** Закрытая модель: нельзя inspect‑нуть, как именно она обрабатывает кадры.<br/>
**−** Длинные видео (>1 ч) требуют chunking по временным окнам или Pro‑модели.

### Когда Tier 0 ломается

- Видео приватное / age‑restricted / geo‑blocked → `400 INVALID_ARGUMENT`.
- Удерживается копирайтом → Gemini вернёт «cannot access this video».
- Превышен дневной лимит → `429 RESOURCE_EXHAUSTED`.
- Модель возвращает truncated JSON → retry с более узким окном времени.

В любом из этих случаев — падение на **Tier 1**.

---

## 3. Tier 1 — yt-dlp + опциональный VLM‑проход

### Когда использовать

- Нет `GEMINI_API_KEY` в сессии.
- Tier 0 уже упал с `429` / `400` / content block.
- Нужна **воспроизводимая цепочка без закрытой модели** (например, для оффлайн‑аудита
  research‑заметки).

### Шаги

#### 3.1. Транскрипт (обязательный шаг)

```bash
# Попытка 1 — готовые субтитры (auto-generated или uploaded).
yt-dlp \
  --skip-download \
  --write-auto-sub --write-sub \
  --sub-lang en --sub-format vtt \
  --convert-subs srt \
  -o 'artifacts/%(id)s/%(id)s.%(ext)s' \
  'https://www.youtube.com/watch?v=VIDEO_ID'
```

Если `yt-dlp` падает с `LOGIN_REQUIRED`:

1. Попробовать `--extractor-args "youtube:player_client=web,mweb,android"` — разные
   клиенты YouTube требуют разную аутентификацию.
2. Если есть `cookies.txt` (экспорт из **домашнего** Chrome, не с VM):
   `--cookies /path/to/cookies.txt`.
3. Если и это не помогло — скачать **аудио** и транскрибировать локально:

```bash
yt-dlp -f 'bestaudio/best' --extract-audio --audio-format mp3 \
  -o 'artifacts/%(id)s/audio.mp3' 'https://www.youtube.com/watch?v=VIDEO_ID'
```

Затем транскрипция через **Groq** (`whisper-large-v3-turbo`, free tier, RPD ≈ 2000)
или **OpenAI** (`whisper-1`). Groq возвращает timestamps по сегментам, что нужно для
следующего шага.

#### 3.2. Салиентные таймкоды (опционально, если нужен визуал)

Сканируем SRT по маркерам:

```
"as you can see", "here's the", "in this diagram", "on the screen",
"this slide", "this code", "take a look", "let me show you",
"как вы видите", "вот здесь", "на экране", "в этом коде"
```

+ любые **паузы > 5 секунд** между сегментами речи (спикер показывает что‑то молча).

Селектим 5–15 таймкодов. Больше = дороже VLM‑проход, меньше = можем пропустить
визуальный контекст. Для 45‑минутного видео обычно достаточно 8–12.

#### 3.3. Frames через ffmpeg

```bash
# Вариант A — скачать video.mp4 один раз, затем нарезать локально.
yt-dlp -f 'bestvideo[height<=720][ext=mp4]+bestaudio/best' \
  -o 'artifacts/%(id)s/video.%(ext)s' 'https://www.youtube.com/watch?v=VIDEO_ID'

for T in 00:05:32 00:12:17 ...; do
  ffmpeg -ss "$T" -i artifacts/VIDEO_ID/video.mp4 \
    -frames:v 1 -q:v 2 "artifacts/VIDEO_ID/frames/${T//:/-}.jpg"
done

# Вариант B — без полного скачивания, через HLS URL от yt-dlp -g.
url=$(yt-dlp -f 'best[height<=720]' -g 'https://www.youtube.com/watch?v=VIDEO_ID')
for T in 00:05:32 00:12:17 ...; do
  ffmpeg -ss "$T" -i "$url" -frames:v 1 -q:v 2 "artifacts/VIDEO_ID/frames/${T//:/-}.jpg"
done
```

Вариант B быстрее для 1–2 видео, вариант A — для батчей.

#### 3.4. VLM‑проход по кадрам

Для каждого кадра — запрос в OpenRouter с vision‑моделью и окном транскрипта ±30
секунд вокруг таймкода. Рекомендуемые модели на free tier OpenRouter'а:

| Модель | Цена на OpenRouter | Сильная сторона |
|---|---|---|
| `qwen/qwen2.5-vl-72b-instruct:free` | $0 | SOTA визуал, OCR, диаграммы |
| `meta-llama/llama-3.2-11b-vision-instruct:free` | $0 | Быстрая, неплохо на простом UI |
| `google/gemma-3-27b-it:free` | $0 | Баланс, стабильно работает |
| `anthropic/claude-3.5-sonnet` | платно | Лучшее качество, если нужен последний рывок |

Промпт кадру:

```
System: You analyze a single frame from a technical video. Focus on what is
VISIBLE on the frame but is unlikely to be captured in the transcript:
diagrams, code on screen, terminal output, slide titles, architectural boxes
with labels, tool names in UI.

User: The speaker around this moment is saying:
"""
{transcript_window}
"""
Describe the frame in ≤5 bullets. Omit anything already obvious from the
transcript. If the frame has no technical content, return "[no technical content]".
```

#### 3.5. Merge в canonical markdown

```
# {Title}

Source: https://youtube.com/watch?v=VIDEO_ID | Duration: 44:13 | Tier 1

## Transcript (with visual callouts)

[00:00:12] So today we're building ...
[00:05:32] 🖼️ Frame: The screen shows a 3-layer diagram titled "Agent Architecture"
           with boxes: "Router / Orchestrator / Tools". Arrows from top to bottom.
[00:05:44] As you can see, the orchestrator sits between ...
```

### Сильные и слабые стороны Tier 1

**+** Не зависит от Gemini, работает на open‑weights моделях.<br/>
**+** Полностью контролируем: каждый шаг виден в артефактах.<br/>
**+** Дёшево: ASR на Groq free, VLM на free моделях OpenRouter.<br/>
**−** ~10× больше строк кода, чем Tier 0.<br/>
**−** Качество merge в итоговый markdown зависит от ручной эвристики salient‑отбора.<br/>
**−** `yt-dlp` периодически сам упирается в anti‑bot от YouTube.

---

## 4. Tier 2 — SaaS‑скрейпер (last resort)

### Когда использовать

Абсолютно **последний** вариант: Tier 0 недоступен (нет ключа, quota) **и** Tier 1
упал на шаге скачивания `yt-dlp`.

### Как работает

Playwright против `notegpt.io` (основной) с fallback на `kome.ai`.
Реализация этого тира уже есть в
[`/home/ubuntu/transcripts/try_notegpt.py`](../knowledge/research/video-ingestion-poc/legacy/)
(из первой попытки) — скрипт открывает сайт, вставляет URL, ждёт рендеринга,
кликает все `Read More`, соскабливает текст.

### Фундаментальные ограничения

- Только текст, никакого визуала.
- 15 транскриптов/мес на `notegpt.io` без регистрации.
- ToS/free tier логика меняется между запусками.
- CAPTCHA появляется периодически.

**Правило:** если Tier 2 используется больше одного раза за сессию — это сигнал,
что Tier 0/1 конфигурация сломана. Чинить setup, а не workflow.

---

## 5. Таблица «какой тир выбрать»

| Ситуация | Tier | Комментарий |
|---|---|---|
| Дефолт, есть `GEMINI_API_KEY` | 0 | Всегда начинаем с Tier 0. |
| Видео > 2 часа | 0 или 1 | Tier 0 с chunking окнами по 1 часу, либо Tier 1 + ASR. |
| Видео приватное (unlisted + shared) | 1 | Tier 0 не сможет (нужна auth в YouTube). |
| Нужна проверка «слово‑в‑слово» | 1 | Whisper даёт verbatim; Gemini перефразирует. |
| Нет `GEMINI_API_KEY` | 1 | Ставим `OPENROUTER_API_KEY` и идём. |
| Нет никаких API‑ключей | 2 | Переваливаемся на скрейпер, готовим нормальные ключи. |
| Тема = визуальная (архитектурные видео, code walkthrough) | 0 | У Gemini лучший VLM `baked in`. |
| Тема = чисто речевая (подкаст, интервью) | 0 или 1 без frames | Визуал не нужен, можно опустить шаг 3.2–3.4. |

---

## 6. Единый output‑контракт (общий для всех тиров)

Все три тира пишут в одинаковую структуру, чтобы downstream‑пайплайн (extract →
rank → note) был един:

```
artifacts/<video_id>/
├── meta.json          # {title, channel, duration_sec, url, tier_used, tried_tiers}
├── transcript.md      # canonical: строки "[HH:MM:SS] text" + "[🖼️ visual @ HH:MM:SS] ..."
├── frames/            # только при Tier 1 с visual pass
│   └── HH-MM-SS.jpg
├── vlm.jsonl          # {timestamp, frame, description} — только при Tier 1
└── raw/               # сырые ответы API (для debug)
    ├── gemini_response.json
    └── ...
```

Далее — через промпт
[`knowledge/prompts/ingest-youtube-video.md`](../knowledge/prompts/ingest-youtube-video.md)
это превращается в
[`knowledge/research/<slug>.md`](../knowledge/README.md).

---

## 7. Секреты

Все ключи — через платформу Devin как org‑scope (видны во всех сессиях):

| Secret | Тир | Обязательный? | Где получить |
|---|---|---|---|
| `GEMINI_API_KEY` | 0 | Да | [aistudio.google.com/apikey](https://aistudio.google.com/apikey) |
| `OPENROUTER_API_KEY` | 1 | Для VLM | [openrouter.ai/keys](https://openrouter.ai/keys) |
| `GROQ_API_KEY` | 1 | Опционально | [console.groq.com/keys](https://console.groq.com/keys) |

YouTube `cookies.txt` — **не нужен для Tier 0**. Может помочь Tier 1 на тех редких
видео, где `yt-dlp` видит `LOGIN_REQUIRED`. Экспорт только с домашнего Chrome
(residential IP), не с VM.

Секреты **не коммитим** в репо — они только в окружении агента. Референсная
реализация читает их из `os.environ`.

---

## 8. Gotchas из первой попытки

- `kome.ai` в одном месяце отдал Hermes‑видео целиком, через день — preview + paywall.
  **Никогда не полагаться на free tier стороннего сервиса как на основной канал.**
- `notegpt.io` для 45‑минутных видео возвращает **оборванный** текст, если не
  кликать все `Read More` кнопки. В POC есть рабочий DOM‑скрипт.
- `yt-dlp` 2026.03+ требует JS runtime (deno/node) для некоторых плейеров —
  проверяем `yt-dlp --version` и `which deno node` в пре‑чеке.
- `ffmpeg -ss` **до** `-i` — seek по ключевым кадрам (быстро, может промахнуться
  на 1–2 сек). **После** `-i` — точный, но читает файл от начала до T.
  Для наших таймкодов хватает быстрого варианта.
- Gemini `file_data` требует `mime_type: "video/mp4"` даже для YouTube URL,
  иначе `400`.
- Gemini response size: JSON со всеми концептами для 45‑минутного видео =
  ~30–50KB. Если уткнулись в `response.candidates[0].finish_reason == "MAX_TOKENS"` —
  надо поднять `max_output_tokens` или разбить запрос по временным окнам.

---

## 9. Дальнейшее развитие

Не в рамках этого документа, но логичные следующие шаги, когда `src/` откроется:

1. Упаковать POC как CLI: `first-agent ingest <url>`.
2. Кэш по `<video_id>` — не пересчитывать, если уже есть `artifacts/<id>/final.md`.
3. Batch‑режим: список URL → параллельная обработка через Tier 0.
4. Авто‑детект «чисто речевого» видео → пропуск шага 3.2–3.4 Tier 1 экономит $.
5. ADR о выборе дефолтного тира и VLM‑модели (когда будет накоплен измеримый sample).
