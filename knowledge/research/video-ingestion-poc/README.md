# video-ingestion-poc

Референсная реализация workflow'а из [`docs/video-ingestion.md`](../../../docs/video-ingestion.md).
**Research POC**, не production: один файл на ~500 строк, запускается из коробки
после `pip install`.

## Почему здесь, а не в `src/`

Репо пока в фазе research (`AGENTS.md`: «Кода в `src/` пока нет»). Артефакт лежит в
`knowledge/research/` как исполняемая заметка. Когда откроется `src/`, код переедет
модулем (см. §9 workflow‑доки).

## Установка

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -U google-genai openai yt-dlp
```

Системные зависимости:

- `ffmpeg` — для извлечения кадров в Tier 1.
- `yt-dlp` — можно ставить через `pip`, тогда deno/node не требуются для большинства
  публичных видео.

## Секреты (ENV)

| Переменная | Тир | Обязательный? |
|---|---|---|
| `GEMINI_API_KEY` | 0 | Для Tier 0 |
| `OPENROUTER_API_KEY` | 1 | Для визуального прохода Tier 1 |
| `GROQ_API_KEY` | 1 | Если yt‑dlp не смог получить субтитры |
| `YT_DLP_COOKIES` | 1 | Путь к `cookies.txt` (опционально) |

Если ничего не задано — `--tier auto` свалится сразу на Tier 2 (заглушка).
На живой сессии Devin секреты приходят из env платформы.

## Запуск

```bash
# Автовыбор тира
python ingest.py 'https://www.youtube.com/watch?v=qUqcLNcP5Tc'

# Принудительно Tier 0
python ingest.py 'https://...' --tier 0

# Батч
printf 'https://...\nhttps://...\n' > urls.txt
python ingest.py --batch urls.txt --tier 0

# Альтернативный out-dir
python ingest.py 'https://...' --out-dir /tmp/my-artifacts
```

## Что появляется на выходе

```
artifacts/<video_id>/
├── meta.json              # {video_id, url, title, duration, tier_used, tried_tiers, errors}
├── transcript.md          # "[HH:MM:SS] text" + "[🖼️ visual @ ...] description"
├── key_concepts.json      # только Tier 0: summary/key_concepts/tools_mentioned
├── frames/                # только Tier 1 с visual pass
│   └── HH-MM-SS.jpg
├── vlm.jsonl              # только Tier 1: по одной строке на кадр
└── raw/
    ├── gemini_response.json   # или
    └── ytdlp_info.json
```

Дальше этот набор скармливается промпту
[`knowledge/prompts/ingest-youtube-video.md`](../../prompts/ingest-youtube-video.md)
для генерации финальной заметки в `knowledge/research/`.

## Известные ограничения

- **Tier 2 — заглушка.** Рабочий скрейпер `notegpt.io` написан в первой итерации
  (`/home/ubuntu/transcripts/try_notegpt.py` на VM), но не перенесён сюда: его логика
  завязана на DOM, который меняется чаще, чем репо.
- **`select_salient_timestamps`** — грубая эвристика. Для видео без явных маркеров
  речи может выдать пусто; тогда визуальный проход пропускается.
- **Chunking длинных видео.** Tier 0 с `gemini-2.5-flash` принимает до ~1 часа;
  для 2+ часов — разбивать на окна через `file_uri` + `videoMetadata.startOffset/endOffset`
  (ещё не реализовано в этом POC).
- **Ретраев на 429 пока нет.** Если упёрлись в rate‑limit — перезапустить с
  `--tier 1`. Добавлять backoff, когда появится `src/`.

## Как развивать

Правки в этом файле или в `ingest.py` — через PR в main, как любую другую
документацию репо. CI пока не настроен (`AGENTS.md`).
