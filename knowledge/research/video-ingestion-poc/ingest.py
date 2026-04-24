#!/usr/bin/env python3
"""Reference implementation of the layered YouTube ingestion workflow.

See ``docs/video-ingestion.md`` for the design. This script is intentionally
self-contained so it can be run end-to-end with only ``pip install``-able
dependencies. It is a *research POC*, not production code — expect rough edges
in error handling and keep an eye on the free-tier rate limits of the
upstream services.

Usage
-----
    python ingest.py <youtube_url> [--tier auto|0|1|2] [--out-dir artifacts/]
    python ingest.py --batch urls.txt --tier auto

Environment
-----------
    GEMINI_API_KEY        # required for Tier 0
    OPENROUTER_API_KEY    # required for Tier 1 visual pass
    GROQ_API_KEY          # optional, Tier 1 Whisper fallback
    YT_DLP_COOKIES        # optional, path to cookies.txt for Tier 1

Exit codes
----------
    0   success (any tier)
    10  all configured tiers failed
    20  bad arguments / missing required tools
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import parse_qs, urlparse

# -- constants ---------------------------------------------------------------

DEFAULT_OUT_DIR = Path("artifacts")
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_MODEL_FALLBACK = "gemini-2.5-pro"
OPENROUTER_VLM_MODEL = "qwen/qwen2.5-vl-72b-instruct:free"
OPENROUTER_VLM_FALLBACK = "meta-llama/llama-3.2-11b-vision-instruct:free"
GROQ_ASR_MODEL = "whisper-large-v3-turbo"

# Keywords that hint "the speaker is pointing at the screen right now".
SALIENT_MARKERS_EN = (
    "as you can see", "here's the", "in this diagram", "on the screen",
    "this slide", "this code", "take a look", "let me show",
    "over here", "on the left", "on the right", "at the top",
    "architecture", "diagram", "flow chart",
)
SALIENT_MARKERS_RU = (
    "как вы видите", "вот здесь", "на экране", "в этом коде",
    "на этом слайде", "посмотрите на", "обратите внимание",
    "слева", "справа", "сверху",
)

# -- data classes ------------------------------------------------------------


@dataclass
class VideoMeta:
    video_id: str
    url: str
    title: Optional[str] = None
    channel: Optional[str] = None
    duration_sec: Optional[int] = None
    tier_used: Optional[str] = None
    tried_tiers: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


@dataclass
class TranscriptSegment:
    start_sec: float
    end_sec: float
    text: str


# -- utilities ---------------------------------------------------------------


def extract_video_id(url: str) -> str:
    """Accept common YouTube URL shapes and return the 11-char video id."""
    parsed = urlparse(url)
    if parsed.hostname in {"youtu.be"}:
        return parsed.path.lstrip("/")
    if parsed.hostname and "youtube.com" in parsed.hostname:
        if parsed.path == "/watch":
            return parse_qs(parsed.query)["v"][0]
        if parsed.path.startswith(("/embed/", "/v/", "/shorts/")):
            return parsed.path.split("/")[2]
    raise ValueError(f"Cannot extract video id from {url!r}")


def format_timestamp(sec: float) -> str:
    sec = int(sec)
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def parse_srt(path: Path) -> list[TranscriptSegment]:
    """Parse a WebVTT or SRT file into (start, end, text) segments."""
    text = path.read_text(encoding="utf-8")
    # Strip WebVTT header if present.
    text = re.sub(r"^WEBVTT.*?\n\n", "", text, count=1, flags=re.DOTALL)
    blocks = re.split(r"\n\s*\n", text.strip())
    segments: list[TranscriptSegment] = []
    ts_re = re.compile(
        r"(\d{2}:\d{2}:\d{2}[.,]\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2}[.,]\d{3})"
    )

    def _to_sec(ts: str) -> float:
        ts = ts.replace(",", ".")
        h, m, s = ts.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    for block in blocks:
        lines = [ln for ln in block.splitlines() if ln.strip()]
        if not lines:
            continue
        m = ts_re.search(lines[0] if ts_re.search(lines[0]) else (lines[1] if len(lines) > 1 else ""))
        header_idx = 0 if ts_re.search(lines[0]) else 1
        if header_idx >= len(lines):
            continue
        m = ts_re.search(lines[header_idx])
        if not m:
            continue
        start = _to_sec(m.group(1))
        end = _to_sec(m.group(2))
        body = " ".join(lines[header_idx + 1 :]).strip()
        # Drop inline cue tags like <c.colorE5E5E5>...
        body = re.sub(r"<[^>]+>", "", body)
        if body:
            segments.append(TranscriptSegment(start, end, body))
    return segments


def write_transcript_md(
    out_path: Path,
    segments: list[TranscriptSegment],
    meta: VideoMeta,
    visual_notes: Optional[dict[float, str]] = None,
) -> None:
    visual_notes = visual_notes or {}
    lines = [
        f"# {meta.title or meta.video_id}",
        "",
        f"Source: <{meta.url}>",
        f"Channel: {meta.channel or '—'} | Duration: "
        f"{format_timestamp(meta.duration_sec or 0)} | Tier: {meta.tier_used}",
        "",
        "## Transcript",
        "",
    ]
    visual_queue = sorted(visual_notes.items())
    vi = 0
    for seg in segments:
        while vi < len(visual_queue) and visual_queue[vi][0] <= seg.start_sec:
            t, note = visual_queue[vi]
            lines.append(f"[🖼️ visual @ {format_timestamp(t)}] {note}")
            vi += 1
        lines.append(f"[{format_timestamp(seg.start_sec)}] {seg.text}")
    while vi < len(visual_queue):
        t, note = visual_queue[vi]
        lines.append(f"[🖼️ visual @ {format_timestamp(t)}] {note}")
        vi += 1
    out_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def select_salient_timestamps(
    segments: list[TranscriptSegment],
    max_count: int = 10,
    silence_gap_sec: float = 5.0,
) -> list[float]:
    """Heuristic: pick timestamps where the speaker likely points at the screen."""
    markers = SALIENT_MARKERS_EN + SALIENT_MARKERS_RU
    hits: list[float] = []
    for seg in segments:
        lower = seg.text.lower()
        if any(marker in lower for marker in markers):
            hits.append(seg.start_sec)

    # Add long-silence midpoints.
    for a, b in zip(segments, segments[1:]):
        if b.start_sec - a.end_sec >= silence_gap_sec:
            hits.append((a.end_sec + b.start_sec) / 2)

    # Deduplicate within 20-second windows and cap count.
    hits.sort()
    deduped: list[float] = []
    for t in hits:
        if not deduped or t - deduped[-1] > 20:
            deduped.append(t)
    if len(deduped) > max_count:
        # Sample evenly across the video.
        step = len(deduped) / max_count
        deduped = [deduped[int(i * step)] for i in range(max_count)]
    return deduped


# -- Tier 0 — Gemini Direct YouTube -----------------------------------------


GEMINI_PROMPT = """\
You are ingesting a public YouTube video for a research agent. Return a JSON
object with exactly these fields (and nothing else):

{
  "title": string,
  "channel": string,
  "duration_seconds": integer,
  "summary": string (<=200 words),
  "transcript": [
    {"t": "HH:MM:SS", "speaker": string|null, "text": string},
    ...
  ],
  "visual_callouts": [
    {"t": "HH:MM:SS", "description": string}
  ],
  "key_concepts": [
    {"t": "HH:MM:SS", "concept": string, "explanation": string}
  ],
  "tools_mentioned": [string],
  "open_questions": [string]
}

Rules:
- "transcript" must cover the full video with ≤30s gaps. Split long runs into
  logical sentences, one per entry.
- "visual_callouts" only for frames with non-trivial on-screen content:
  diagrams, code, terminal, slides with data. Skip generic talking-head shots.
- Every "key_concepts" entry must cite a timestamp when the concept is introduced.
- If audio is in Russian or another language, transcribe in the ORIGINAL language.
- Output strict JSON, no markdown fences, no comments.
"""


def ingest_tier0_gemini(url: str, out_dir: Path, meta: VideoMeta) -> bool:
    """Use Gemini's native YouTube URL ingest. Returns True on success."""
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        meta.errors.append("tier0: google-genai not installed")
        return False

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        meta.errors.append("tier0: GEMINI_API_KEY not set")
        return False

    client = genai.Client(api_key=api_key)
    contents = types.Content(parts=[
        types.Part(file_data=types.FileData(
            file_uri=url, mime_type="video/mp4"
        )),
        types.Part(text=GEMINI_PROMPT),
    ])
    config = types.GenerateContentConfig(
        response_mime_type="application/json",
        max_output_tokens=64_000,
    )

    for model in (GEMINI_MODEL, GEMINI_MODEL_FALLBACK):
        try:
            resp = client.models.generate_content(
                model=model, contents=contents, config=config
            )
        except Exception as e:  # noqa: BLE001
            meta.errors.append(f"tier0: {model} raised {type(e).__name__}: {e}")
            continue

        raw_path = out_dir / "raw" / "gemini_response.json"
        raw_path.parent.mkdir(parents=True, exist_ok=True)
        raw_path.write_text(resp.text, encoding="utf-8")

        try:
            data = json.loads(resp.text)
        except json.JSONDecodeError as e:
            meta.errors.append(f"tier0: {model} returned non-JSON: {e}")
            continue

        meta.title = data.get("title")
        meta.channel = data.get("channel")
        meta.duration_sec = data.get("duration_seconds")

        segments = [
            TranscriptSegment(
                start_sec=_hms_to_sec(item["t"]),
                end_sec=_hms_to_sec(item["t"]) + 1.0,  # approximate
                text=item["text"],
            )
            for item in data.get("transcript", [])
        ]
        visual_notes = {
            _hms_to_sec(v["t"]): v["description"]
            for v in data.get("visual_callouts", [])
        }

        write_transcript_md(
            out_dir / "transcript.md", segments, meta, visual_notes
        )
        # Persist structured extras next to transcript for downstream use.
        (out_dir / "key_concepts.json").write_text(
            json.dumps(
                {
                    "summary": data.get("summary"),
                    "key_concepts": data.get("key_concepts", []),
                    "tools_mentioned": data.get("tools_mentioned", []),
                    "open_questions": data.get("open_questions", []),
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        return True
    return False


def _hms_to_sec(hms: str) -> float:
    parts = hms.split(":")
    if len(parts) == 3:
        h, m, s = parts
        return int(h) * 3600 + int(m) * 60 + float(s)
    if len(parts) == 2:
        m, s = parts
        return int(m) * 60 + float(s)
    return float(hms)


# -- Tier 1 — yt-dlp + optional VLM ----------------------------------------


def ingest_tier1_ytdlp(url: str, out_dir: Path, meta: VideoMeta, *, with_visual: bool = True) -> bool:
    """Get captions via yt-dlp; optionally run VLM pass on salient frames."""
    if not shutil.which("yt-dlp"):
        meta.errors.append("tier1: yt-dlp not installed (pip install -U yt-dlp)")
        return False

    # Step 1 — metadata + captions.
    meta_json = out_dir / "raw" / "ytdlp_info.json"
    meta_json.parent.mkdir(parents=True, exist_ok=True)
    base_args = ["yt-dlp", "--no-warnings", "--write-info-json",
                 "--write-auto-sub", "--write-sub", "--sub-lang", "en",
                 "--sub-format", "vtt", "--convert-subs", "srt",
                 "--skip-download", "-o", str(out_dir / "%(id)s.%(ext)s"), url]
    cookies_path = os.environ.get("YT_DLP_COOKIES")
    if cookies_path:
        base_args.extend(["--cookies", cookies_path])

    r = subprocess.run(base_args, capture_output=True, text=True)
    if r.returncode != 0:
        meta.errors.append(f"tier1: yt-dlp failed: {r.stderr.strip()[:400]}")
        return False

    # Grab info.json produced by yt-dlp.
    info_files = list(out_dir.glob("*.info.json"))
    if info_files:
        info = json.loads(info_files[0].read_text(encoding="utf-8"))
        meta.title = info.get("title")
        meta.channel = info.get("uploader")
        meta.duration_sec = info.get("duration")
        # Archive it under raw/ for debug.
        info_files[0].rename(meta_json)

    # Locate captions.
    srt_files = list(out_dir.glob(f"{meta.video_id}*.srt"))
    if not srt_files:
        # Fallback to ASR via Groq on downloaded audio.
        if not _tier1_asr_via_groq(url, out_dir, meta):
            return False
        srt_files = list(out_dir.glob(f"{meta.video_id}*.srt"))
    if not srt_files:
        meta.errors.append("tier1: no captions available and ASR failed")
        return False

    segments = parse_srt(srt_files[0])
    if not segments:
        meta.errors.append("tier1: parsed 0 segments from captions")
        return False

    visual_notes: dict[float, str] = {}
    if with_visual and os.environ.get("OPENROUTER_API_KEY"):
        try:
            visual_notes = _tier1_visual_pass(url, out_dir, meta, segments)
        except Exception as e:  # noqa: BLE001
            meta.errors.append(f"tier1: visual pass failed: {e}")

    write_transcript_md(out_dir / "transcript.md", segments, meta, visual_notes)
    return True


def _tier1_asr_via_groq(url: str, out_dir: Path, meta: VideoMeta) -> bool:
    """Download audio and transcribe with Groq Whisper. Writes SRT on disk."""
    if not os.environ.get("GROQ_API_KEY"):
        meta.errors.append("tier1-asr: GROQ_API_KEY not set")
        return False
    audio_path = out_dir / f"{meta.video_id}.audio.mp3"
    r = subprocess.run(
        ["yt-dlp", "-x", "--audio-format", "mp3", "-o", str(audio_path),
         "--no-warnings", url],
        capture_output=True, text=True,
    )
    if r.returncode != 0:
        meta.errors.append(f"tier1-asr: download failed: {r.stderr[:200]}")
        return False

    try:
        from openai import OpenAI  # Groq is OpenAI-compatible.
    except ImportError:
        meta.errors.append("tier1-asr: openai package not installed")
        return False

    client = OpenAI(
        api_key=os.environ["GROQ_API_KEY"],
        base_url="https://api.groq.com/openai/v1",
    )
    with audio_path.open("rb") as fh:
        resp = client.audio.transcriptions.create(
            file=fh,
            model=GROQ_ASR_MODEL,
            response_format="verbose_json",
            timestamp_granularities=["segment"],
        )
    # Convert to SRT.
    segments = getattr(resp, "segments", []) or []
    lines: list[str] = []
    for i, seg in enumerate(segments, start=1):
        start = _sec_to_srt(seg["start"])
        end = _sec_to_srt(seg["end"])
        text = seg["text"].strip()
        lines.append(f"{i}\n{start} --> {end}\n{text}\n")
    (out_dir / f"{meta.video_id}.en.srt").write_text(
        "\n".join(lines), encoding="utf-8"
    )
    return True


def _sec_to_srt(sec: float) -> str:
    ms = int(round((sec - int(sec)) * 1000))
    h, rem = divmod(int(sec), 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def _tier1_visual_pass(
    url: str,
    out_dir: Path,
    meta: VideoMeta,
    segments: list[TranscriptSegment],
) -> dict[float, str]:
    """Extract salient frames with ffmpeg, describe each via OpenRouter VLM."""
    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg not in PATH")
    frames_dir = out_dir / "frames"
    frames_dir.mkdir(exist_ok=True)

    timestamps = select_salient_timestamps(segments)
    if not timestamps:
        return {}

    # Stream the lowest-resolution mp4 URL once.
    r = subprocess.run(
        ["yt-dlp", "-f", "best[height<=480][ext=mp4]/best[height<=720]",
         "-g", url], capture_output=True, text=True,
    )
    if r.returncode != 0 or not r.stdout.strip():
        raise RuntimeError(f"yt-dlp -g failed: {r.stderr[:200]}")
    media_url = r.stdout.strip().splitlines()[0]

    frames: dict[float, Path] = {}
    for t in timestamps:
        frame_path = frames_dir / f"{format_timestamp(t).replace(':', '-')}.jpg"
        rr = subprocess.run(
            ["ffmpeg", "-y", "-ss", str(t), "-i", media_url,
             "-frames:v", "1", "-q:v", "3", str(frame_path)],
            capture_output=True, text=True,
        )
        if rr.returncode == 0 and frame_path.exists():
            frames[t] = frame_path

    return _describe_frames_via_openrouter(frames, segments, out_dir)


def _describe_frames_via_openrouter(
    frames: dict[float, Path],
    segments: list[TranscriptSegment],
    out_dir: Path,
) -> dict[float, str]:
    import base64
    from openai import OpenAI  # OpenRouter is OpenAI-compatible.

    client = OpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
    )
    vlm_path = out_dir / "vlm.jsonl"
    out: dict[float, str] = {}

    with vlm_path.open("w", encoding="utf-8") as jsonl:
        for t, frame in frames.items():
            # Find ±30 s transcript window for context.
            window = " ".join(
                s.text for s in segments
                if t - 30 <= s.start_sec <= t + 30
            )[:2000]

            b64 = base64.b64encode(frame.read_bytes()).decode()
            for model in (OPENROUTER_VLM_MODEL, OPENROUTER_VLM_FALLBACK):
                try:
                    resp = client.chat.completions.create(
                        model=model,
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You describe a frame from a technical video. "
                                    "Focus on what is visible but NOT obvious from "
                                    "the transcript: diagrams, code, terminal output, "
                                    "slide titles, architectural boxes. "
                                    "Answer in ≤ 5 bullets. "
                                    "If the frame has no technical content, output "
                                    "'[no technical content]'."
                                ),
                            },
                            {
                                "role": "user",
                                "content": [
                                    {
                                        "type": "text",
                                        "text": (
                                            f"Transcript around {format_timestamp(t)}:\n"
                                            f"\"\"\"\n{window}\n\"\"\""
                                        ),
                                    },
                                    {
                                        "type": "image_url",
                                        "image_url": {
                                            "url": f"data:image/jpeg;base64,{b64}"
                                        },
                                    },
                                ],
                            },
                        ],
                        max_tokens=400,
                    )
                    description = resp.choices[0].message.content or ""
                    if "no technical content" in description.lower():
                        break
                    out[t] = description.strip()
                    jsonl.write(
                        json.dumps(
                            {
                                "timestamp": format_timestamp(t),
                                "frame": str(frame.relative_to(out_dir)),
                                "model": model,
                                "description": description,
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )
                    break
                except Exception as e:  # noqa: BLE001
                    jsonl.write(
                        json.dumps(
                            {
                                "timestamp": format_timestamp(t),
                                "model": model,
                                "error": f"{type(e).__name__}: {e}",
                            }
                        )
                        + "\n"
                    )
                    continue
    return out


# -- Tier 2 — SaaS scraper (stub; full impl in legacy/try_notegpt.py) --------


def ingest_tier2_scraper(url: str, out_dir: Path, meta: VideoMeta) -> bool:
    """Placeholder: use notegpt.io via Playwright. See legacy/ for working code.

    Kept as a stub because Tier 2 is last-resort and its implementation drifts
    quickly with the external site's UI.
    """
    meta.errors.append(
        "tier2: scraper not runnable from this POC; see legacy/try_notegpt.py"
    )
    return False


# -- orchestrator ------------------------------------------------------------


def select_tiers(user_choice: str) -> list[str]:
    if user_choice == "auto":
        tiers: list[str] = []
        if os.environ.get("GEMINI_API_KEY"):
            tiers.append("0")
        if shutil.which("yt-dlp"):
            tiers.append("1")
        tiers.append("2")
        return tiers
    return [user_choice]


def run(url: str, tier_choice: str, out_root: Path) -> int:
    video_id = extract_video_id(url)
    out_dir = out_root / video_id
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = VideoMeta(video_id=video_id, url=url)

    for tier in select_tiers(tier_choice):
        meta.tried_tiers.append(tier)
        print(f"[tier {tier}] {video_id} — starting", flush=True)
        started = time.time()
        ok = False
        if tier == "0":
            ok = ingest_tier0_gemini(url, out_dir, meta)
        elif tier == "1":
            ok = ingest_tier1_ytdlp(url, out_dir, meta)
        elif tier == "2":
            ok = ingest_tier2_scraper(url, out_dir, meta)
        else:
            print(f"unknown tier: {tier}", file=sys.stderr)
            return 20
        elapsed = time.time() - started
        if ok:
            meta.tier_used = tier
            (out_dir / "meta.json").write_text(
                json.dumps(asdict(meta), indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"[tier {tier}] {video_id} — ok ({elapsed:.1f}s)", flush=True)
            return 0
        print(f"[tier {tier}] {video_id} — failed ({elapsed:.1f}s)", flush=True)

    (out_dir / "meta.json").write_text(
        json.dumps(asdict(meta), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    print(f"ALL tiers failed for {video_id}", file=sys.stderr)
    for err in meta.errors:
        print(f"  - {err}", file=sys.stderr)
    return 10


def run_batch(urls: Iterable[str], tier_choice: str, out_root: Path) -> int:
    rc = 0
    for url in urls:
        rc = max(rc, run(url.strip(), tier_choice, out_root))
    return rc


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("url", nargs="?", help="YouTube URL")
    ap.add_argument("--batch", help="File with one YouTube URL per line")
    ap.add_argument("--tier", default="auto", choices=["auto", "0", "1", "2"])
    ap.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR)
    args = ap.parse_args(argv)

    if bool(args.url) == bool(args.batch):
        ap.error("Provide exactly one of <url> or --batch")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    if args.batch:
        urls = Path(args.batch).read_text().splitlines()
        return run_batch(urls, args.tier, args.out_dir)
    return run(args.url, args.tier, args.out_dir)


if __name__ == "__main__":
    sys.exit(main())
