from __future__ import annotations

import base64
import cgi
import concurrent.futures
import json
import mimetypes
import os
import re
import shutil
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid
from collections import Counter
from datetime import datetime
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import fitz
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "paper_hub.db"
STORAGE_DIR = ROOT / "storage"
PDF_DIR = STORAGE_DIR / "pdfs"
COVER_DIR = STORAGE_DIR / "covers"
RENDER_DIR = STORAGE_DIR / "renders"
TRANSLATION_DIR = STORAGE_DIR / "translations"
DIGEST_DIR = STORAGE_DIR / "digests"
PROVIDER_CONFIG_PATH = ROOT / "provider_config.json"
BULK_TRANSLATION_MAX_WORKERS = 3

OPENAI_RESPONSES_URL = "https://api.openai.com/v1/responses"
OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
GLM_CHAT_COMPLETIONS_URL = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
DEEPSEEK_CHAT_COMPLETIONS_URL = "https://api.deepseek.com/chat/completions"
OPENROUTER_CHAT_COMPLETIONS_URL = "https://openrouter.ai/api/v1/chat/completions"
GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
XAI_CHAT_COMPLETIONS_URL = "https://api.x.ai/v1/chat/completions"
TOGETHER_CHAT_COMPLETIONS_URL = "https://api.together.xyz/v1/chat/completions"
QWEN_CHAT_COMPLETIONS_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"
OLLAMA_CHAT_COMPLETIONS_URL = "http://127.0.0.1:11434/v1/chat/completions"
LMSTUDIO_CHAT_COMPLETIONS_URL = "http://127.0.0.1:1234/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
GEMINI_GENERATE_CONTENT_URL = "https://generativelanguage.googleapis.com/v1beta/models"

mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("application/javascript", ".mjs")
mimetypes.add_type("text/css", ".css")

CATEGORY_CHOICES = [
    "Foundation Models",
    "RAG",
    "Agents",
    "NLP",
    "Multimodal",
    "Computer Vision",
    "Diffusion",
    "Graph ML",
    "Recommendation",
    "Time Series",
    "Reinforcement Learning",
    "Optimization",
    "Security",
    "Systems",
    "Robotics",
    "Survey",
    "Other",
]

PROVIDER_PRESETS = [
    {
        "id": "openai",
        "label": "OpenAI",
        "protocol": "openai_responses",
        "defaultModel": "gpt-5-mini",
        "defaultApiUrl": OPENAI_RESPONSES_URL,
        "requiresApiKey": True,
        "supportsVision": True,
        "description": "Native Responses API. Best fit when you want one provider to handle metadata, digest, and vision translation.",
        "apiKeyEnv": ["OPENAI_API_KEY"],
        "urlHints": ["api.openai.com"],
    },
    {
        "id": "anthropic",
        "label": "Anthropic",
        "protocol": "anthropic_messages",
        "defaultModel": "claude-3-5-sonnet-latest",
        "defaultApiUrl": ANTHROPIC_MESSAGES_URL,
        "requiresApiKey": True,
        "supportsVision": True,
        "description": "Claude-style provider with strong long-context reading and image understanding.",
        "apiKeyEnv": ["ANTHROPIC_API_KEY"],
        "urlHints": ["api.anthropic.com"],
    },
    {
        "id": "gemini",
        "label": "Google Gemini",
        "protocol": "gemini_generate_content",
        "defaultModel": "gemini-2.0-flash",
        "defaultApiUrl": GEMINI_GENERATE_CONTENT_URL,
        "requiresApiKey": True,
        "supportsVision": True,
        "description": "Gemini generateContent API with native multimodal support.",
        "apiKeyEnv": ["GEMINI_API_KEY", "GOOGLE_API_KEY"],
        "urlHints": ["generativelanguage.googleapis.com", "googleapis.com"],
    },
    {
        "id": "relay-openai",
        "label": "OpenAI Compatible Relay",
        "protocol": "openai_chat",
        "defaultModel": "",
        "defaultApiUrl": "https://your-relay.example/v1/chat/completions",
        "requiresApiKey": True,
        "supportsVision": True,
        "description": "For domestic relay/proxy services that expose an OpenAI-compatible /chat/completions endpoint. Fill the relay URL, model name, and key directly.",
        "apiKeyEnv": [],
        "urlHints": [],
    },
    {
        "id": "openrouter",
        "label": "OpenRouter",
        "protocol": "openai_chat",
        "defaultModel": "openai/gpt-4.1-mini",
        "defaultApiUrl": OPENROUTER_CHAT_COMPLETIONS_URL,
        "requiresApiKey": True,
        "supportsVision": True,
        "description": "OpenAI-compatible router. Choose a vision-capable upstream model for visual translation.",
        "apiKeyEnv": ["OPENROUTER_API_KEY"],
        "urlHints": ["openrouter.ai"],
    },
    {
        "id": "groq",
        "label": "Groq",
        "protocol": "openai_chat",
        "defaultModel": "meta-llama/llama-4-scout-17b-16e-instruct",
        "defaultApiUrl": GROQ_CHAT_COMPLETIONS_URL,
        "requiresApiKey": True,
        "supportsVision": True,
        "description": "OpenAI-compatible API. Visual translation requires a vision-capable Groq model.",
        "apiKeyEnv": ["GROQ_API_KEY"],
        "urlHints": ["api.groq.com"],
    },
    {
        "id": "glm",
        "label": "GLM",
        "protocol": "openai_chat",
        "defaultModel": "glm-5",
        "defaultApiUrl": GLM_CHAT_COMPLETIONS_URL,
        "requiresApiKey": True,
        "supportsVision": True,
        "description": "GLM OpenAI-compatible endpoint. Use a visual GLM model if you want page-image translation.",
        "apiKeyEnv": ["GLM_API_KEY"],
        "urlHints": ["bigmodel.cn"],
    },
    {
        "id": "qwen",
        "label": "Qwen / DashScope",
        "protocol": "openai_chat",
        "defaultModel": "qwen-vl-max",
        "defaultApiUrl": QWEN_CHAT_COMPLETIONS_URL,
        "requiresApiKey": True,
        "supportsVision": True,
        "description": "DashScope OpenAI-compatible endpoint. Use a Qwen-VL model for vision translation.",
        "apiKeyEnv": ["DASHSCOPE_API_KEY", "QWEN_API_KEY"],
        "urlHints": ["dashscope.aliyuncs.com"],
    },
    {
        "id": "together",
        "label": "Together",
        "protocol": "openai_chat",
        "defaultModel": "meta-llama/Llama-3.2-11B-Vision-Instruct-Turbo",
        "defaultApiUrl": TOGETHER_CHAT_COMPLETIONS_URL,
        "requiresApiKey": True,
        "supportsVision": True,
        "description": "OpenAI-compatible endpoint. Works when you pick a vision-capable hosted model.",
        "apiKeyEnv": ["TOGETHER_API_KEY"],
        "urlHints": ["api.together.xyz"],
    },
    {
        "id": "xai",
        "label": "xAI",
        "protocol": "openai_chat",
        "defaultModel": "grok-2-vision-latest",
        "defaultApiUrl": XAI_CHAT_COMPLETIONS_URL,
        "requiresApiKey": True,
        "supportsVision": True,
        "description": "OpenAI-compatible xAI endpoint. Use a vision-capable Grok model when translating page images.",
        "apiKeyEnv": ["XAI_API_KEY"],
        "urlHints": ["api.x.ai"],
    },
    {
        "id": "deepseek",
        "label": "DeepSeek",
        "protocol": "openai_chat",
        "defaultModel": "deepseek-chat",
        "defaultApiUrl": DEEPSEEK_CHAT_COMPLETIONS_URL,
        "requiresApiKey": True,
        "supportsVision": False,
        "description": "Strong text reasoning. Current public API path in this app stays text-only, so embedded vision translation is disabled.",
        "apiKeyEnv": ["DEEPSEEK_API_KEY"],
        "urlHints": ["deepseek.com"],
    },
    {
        "id": "azure-openai",
        "label": "Azure OpenAI",
        "protocol": "azure_openai_chat",
        "defaultModel": "gpt-4.1-mini",
        "defaultApiUrl": "",
        "requiresApiKey": True,
        "supportsVision": True,
        "description": "Use your Azure chat completions deployment URL. Vision works when the deployment model supports image input.",
        "apiKeyEnv": ["AZURE_OPENAI_API_KEY"],
        "urlHints": ["openai.azure.com", "azure.com"],
    },
    {
        "id": "ollama",
        "label": "Ollama",
        "protocol": "openai_chat",
        "defaultModel": "qwen2.5vl:7b",
        "defaultApiUrl": OLLAMA_CHAT_COMPLETIONS_URL,
        "requiresApiKey": False,
        "supportsVision": True,
        "description": "Local OpenAI-compatible endpoint. Choose a local vision model for visual translation.",
        "apiKeyEnv": [],
        "urlHints": ["127.0.0.1:11434", "localhost:11434"],
    },
    {
        "id": "lmstudio",
        "label": "LM Studio",
        "protocol": "openai_chat",
        "defaultModel": "qwen2.5-vl-7b-instruct",
        "defaultApiUrl": LMSTUDIO_CHAT_COMPLETIONS_URL,
        "requiresApiKey": False,
        "supportsVision": True,
        "description": "Local OpenAI-compatible endpoint. Works with a loaded multimodal model.",
        "apiKeyEnv": [],
        "urlHints": ["127.0.0.1:1234", "localhost:1234"],
    },
]

PROVIDER_PRESET_MAP = {item["id"]: item for item in PROVIDER_PRESETS}
TRANSLATION_CACHE_LOCKS: dict[str, threading.Lock] = {}
TRANSLATION_CACHE_LOCKS_GUARD = threading.Lock()
TRANSLATION_JOBS: dict[str, dict] = {}
TRANSLATION_JOBS_LOCK = threading.Lock()
TERMINAL_JOB_STATUSES = {"completed", "completed_with_errors", "failed"}


def load_dotenv(dotenv_path: Path) -> None:
    if not dotenv_path.exists():
        return

    for raw_line in dotenv_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key or key in os.environ:
            continue
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        os.environ[key] = value


load_dotenv(ROOT / ".env")

SEED_PAPERS = [
    {
        "title": "Attention Is All You Need",
        "titleZh": "你所需要的只是注意力机制",
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
        "year": 2017,
        "venue": "NeurIPS",
        "doi": "10.48550/arXiv.1706.03762",
        "url": "https://arxiv.org/abs/1706.03762",
        "status": "completed",
        "priority": "high",
        "rating": 5,
        "favorite": True,
        "collection": "大模型基础",
        "category": "Foundation Models",
        "tags": ["Transformer", "NLP", "Classic"],
        "aiKeywords": ["attention", "transformer", "sequence modeling"],
        "abstract": "提出 Transformer 架构，用纯注意力机制替代循环结构，大幅提升机器翻译和序列建模效率。",
        "aiSummary": "经典 Transformer 论文，适合作为大模型与注意力机制的起点。",
        "aiSummaryZh": "这是一篇经典的 Transformer 论文，适合作为理解大模型和注意力机制的起点。",
        "notes": "重点复读 multi-head attention 和 positional encoding。",
        "aiModel": "",
        "aiConfidence": 0.92,
    },
    {
        "title": "Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks",
        "titleZh": "面向知识密集型自然语言处理任务的检索增强生成",
        "authors": ["Patrick Lewis", "Ethan Perez", "Aleksandara Piktus"],
        "year": 2020,
        "venue": "NeurIPS",
        "doi": "10.48550/arXiv.2005.11401",
        "url": "https://arxiv.org/abs/2005.11401",
        "status": "reading",
        "priority": "high",
        "rating": 4,
        "favorite": True,
        "collection": "RAG 专题",
        "category": "RAG",
        "tags": ["RAG", "Knowledge", "NLP"],
        "aiKeywords": ["retrieval", "knowledge", "question answering"],
        "abstract": "将可微检索器与生成模型结合，在开放域问答等知识密集任务上显著提升效果。",
        "aiSummary": "RAG 方向的起点论文，强调检索与生成协同工作。",
        "aiSummaryZh": "这是 RAG 方向的起点论文，强调检索与生成模型协同工作的价值。",
        "notes": "适合与自己的论文问答系统对照。",
        "aiModel": "",
        "aiConfidence": 0.88,
    },
]

TAG_RULES = {
    "LLM": ["large language model", "llm", "instruction tuning", "prompting", "gpt"],
    "Transformer": ["transformer", "self-attention", "attention mechanism", "multi-head attention"],
    "RAG": ["retrieval augmented", "retrieval-augmented", "rag", "dense retrieval"],
    "Agents": ["agent", "multi-agent", "tool use", "planner"],
    "NLP": ["natural language processing", "natural language", "nlp", "summarization", "question answering"],
    "Multimodal": ["multimodal", "vision-language", "cross-modal", "text-image"],
    "Computer Vision": ["computer vision", "image classification", "object detection", "segmentation", "image generation"],
    "Diffusion": ["diffusion model", "denoising diffusion", "stable diffusion"],
    "Reinforcement Learning": ["reinforcement learning", "policy gradient", "q-learning", "actor-critic"],
    "Graph": ["graph neural", "graph learning", "gnn", "knowledge graph"],
    "Recommendation": ["recommendation", "recommender system", "ctr prediction"],
    "Time Series": ["time series", "forecasting", "temporal"],
    "Security": ["security", "privacy", "adversarial", "attack", "defense"],
    "Survey": ["survey", "a review", "systematic review", "overview of"],
    "Optimization": ["optimization", "gradient descent", "convex", "training objective"],
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_storage() -> None:
    STORAGE_DIR.mkdir(exist_ok=True)
    PDF_DIR.mkdir(exist_ok=True)
    COVER_DIR.mkdir(exist_ok=True)
    RENDER_DIR.mkdir(exist_ok=True)
    TRANSLATION_DIR.mkdir(exist_ok=True)
    DIGEST_DIR.mkdir(exist_ok=True)


def ensure_column(conn: sqlite3.Connection, name: str, definition: str) -> None:
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(papers)").fetchall()}
    if name not in columns:
        conn.execute(f"ALTER TABLE papers ADD COLUMN {name} {definition}")


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def parse_string_list(value) -> list[str]:
    if isinstance(value, list):
        return [normalize_whitespace(str(item)) for item in value if normalize_whitespace(str(item))]
    return []


def normalize_number(value, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def normalize_float(value, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def normalize_paper_payload(payload: dict) -> dict:
    current = now_iso()
    total_pages = normalize_number(payload.get("readerTotalPages") or payload.get("pageCount"), 0)
    reader_page = max(1, normalize_number(payload.get("readerPage"), 1))
    if total_pages > 0:
        reader_page = min(reader_page, total_pages)

    return {
        "id": payload.get("id") or str(uuid.uuid4()),
        "title": normalize_whitespace(str(payload.get("title") or "Untitled Paper")),
        "title_zh": normalize_whitespace(str(payload.get("titleZh") or "")),
        "authors": parse_string_list(payload.get("authors")),
        "year": normalize_number(payload.get("year"), 0),
        "venue": normalize_whitespace(str(payload.get("venue") or "")),
        "doi": normalize_whitespace(str(payload.get("doi") or "")),
        "url": normalize_whitespace(str(payload.get("url") or "")),
        "status": normalize_whitespace(str(payload.get("status") or "to-read")) or "to-read",
        "priority": normalize_whitespace(str(payload.get("priority") or "medium")) or "medium",
        "rating": max(0, min(5, normalize_number(payload.get("rating"), 0))),
        "favorite": bool(payload.get("favorite")),
        "collection": normalize_whitespace(str(payload.get("collection") or "")),
        "category": normalize_whitespace(str(payload.get("category") or "")),
        "tags": parse_string_list(payload.get("tags")),
        "ai_keywords": parse_string_list(payload.get("aiKeywords")),
        "abstract": normalize_whitespace(str(payload.get("abstract") or "")),
        "ai_summary": normalize_whitespace(str(payload.get("aiSummary") or "")),
        "ai_summary_zh": normalize_whitespace(str(payload.get("aiSummaryZh") or "")),
        "notes": str(payload.get("notes") or "").strip(),
        "cover_image": normalize_whitespace(str(payload.get("coverImage") or "")),
        "cover_source": normalize_whitespace(str(payload.get("coverSource") or "generated")) or "generated",
        "pdf_path": normalize_whitespace(str(payload.get("pdfPath") or "")),
        "original_filename": normalize_whitespace(str(payload.get("originalFilename") or "")),
        "reader_page": reader_page,
        "reader_total_pages": total_pages,
        "reader_scroll": max(0.0, min(1.0, normalize_float(payload.get("readerScroll"), 0.0))),
        "reader_zoom": max(0.5, min(3.0, normalize_float(payload.get("readerZoom"), 1.0))),
        "last_read_at": normalize_whitespace(str(payload.get("lastReadAt") or "")),
        "ai_model": normalize_whitespace(str(payload.get("aiModel") or "")),
        "ai_enriched_at": normalize_whitespace(str(payload.get("aiEnrichedAt") or "")),
        "ai_confidence": max(0.0, min(1.0, normalize_float(payload.get("aiConfidence"), 0.0))),
        "added_at": normalize_whitespace(str(payload.get("addedAt") or current)),
        "updated_at": normalize_whitespace(str(payload.get("updatedAt") or current)),
    }


def init_db() -> None:
    init_storage()
    with connect_db() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                title_zh TEXT NOT NULL DEFAULT '',
                authors_json TEXT NOT NULL DEFAULT '[]',
                year INTEGER NOT NULL DEFAULT 0,
                venue TEXT NOT NULL DEFAULT '',
                doi TEXT NOT NULL DEFAULT '',
                url TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'to-read',
                priority TEXT NOT NULL DEFAULT 'medium',
                rating INTEGER NOT NULL DEFAULT 0,
                favorite INTEGER NOT NULL DEFAULT 0,
                collection_name TEXT NOT NULL DEFAULT '',
                category TEXT NOT NULL DEFAULT '',
                tags_json TEXT NOT NULL DEFAULT '[]',
                ai_keywords_json TEXT NOT NULL DEFAULT '[]',
                abstract TEXT NOT NULL DEFAULT '',
                ai_summary TEXT NOT NULL DEFAULT '',
                ai_summary_zh TEXT NOT NULL DEFAULT '',
                notes TEXT NOT NULL DEFAULT '',
                cover_image TEXT NOT NULL DEFAULT '',
                cover_source TEXT NOT NULL DEFAULT 'generated',
                pdf_path TEXT NOT NULL DEFAULT '',
                original_filename TEXT NOT NULL DEFAULT '',
                reader_page INTEGER NOT NULL DEFAULT 1,
                reader_total_pages INTEGER NOT NULL DEFAULT 0,
                reader_scroll REAL NOT NULL DEFAULT 0,
                reader_zoom REAL NOT NULL DEFAULT 1,
                last_read_at TEXT NOT NULL DEFAULT '',
                ai_model TEXT NOT NULL DEFAULT '',
                ai_enriched_at TEXT NOT NULL DEFAULT '',
                ai_confidence REAL NOT NULL DEFAULT 0,
                added_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        ensure_column(conn, "category", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "title_zh", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "ai_keywords_json", "TEXT NOT NULL DEFAULT '[]'")
        ensure_column(conn, "ai_summary", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "ai_summary_zh", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "reader_page", "INTEGER NOT NULL DEFAULT 1")
        ensure_column(conn, "reader_total_pages", "INTEGER NOT NULL DEFAULT 0")
        ensure_column(conn, "reader_scroll", "REAL NOT NULL DEFAULT 0")
        ensure_column(conn, "reader_zoom", "REAL NOT NULL DEFAULT 1")
        ensure_column(conn, "last_read_at", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "ai_model", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "ai_enriched_at", "TEXT NOT NULL DEFAULT ''")
        ensure_column(conn, "ai_confidence", "REAL NOT NULL DEFAULT 0")

        count = conn.execute("SELECT COUNT(*) FROM papers").fetchone()[0]
        if count == 0:
            for paper in SEED_PAPERS:
                insert_paper(conn, normalize_paper_payload(paper))


def cleanup_storage_asset(asset_url: str) -> None:
    if not asset_url or not asset_url.startswith("/storage/"):
        return
    asset_path = ROOT / asset_url.lstrip("/")
    if asset_path.exists():
        asset_path.unlink()


def cleanup_rendered_pages(paper_id: str) -> None:
    render_path = RENDER_DIR / paper_id
    if render_path.exists():
        shutil.rmtree(render_path, ignore_errors=True)


def cleanup_translation_cache(paper_id: str) -> None:
    cache_path = TRANSLATION_DIR / f"{paper_id}.json"
    if cache_path.exists():
        cache_path.unlink()


def cleanup_digest_cache(paper_id: str) -> None:
    cache_path = DIGEST_DIR / f"{paper_id}.json"
    if cache_path.exists():
        cache_path.unlink()


def insert_paper(conn: sqlite3.Connection, paper: dict) -> None:
    conn.execute(
        """
        INSERT INTO papers (
            id, title, title_zh, authors_json, year, venue, doi, url, status, priority,
            rating, favorite, collection_name, category, tags_json, ai_keywords_json,
            abstract, ai_summary, ai_summary_zh, notes, cover_image, cover_source, pdf_path,
            original_filename, reader_page, reader_total_pages, reader_scroll,
            reader_zoom, last_read_at, ai_model, ai_enriched_at, ai_confidence,
            added_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            paper["id"],
            paper["title"],
            paper["title_zh"],
            json.dumps(paper["authors"], ensure_ascii=False),
            paper["year"],
            paper["venue"],
            paper["doi"],
            paper["url"],
            paper["status"],
            paper["priority"],
            paper["rating"],
            1 if paper["favorite"] else 0,
            paper["collection"],
            paper["category"],
            json.dumps(paper["tags"], ensure_ascii=False),
            json.dumps(paper["ai_keywords"], ensure_ascii=False),
            paper["abstract"],
            paper["ai_summary"],
            paper["ai_summary_zh"],
            paper["notes"],
            paper["cover_image"],
            paper["cover_source"],
            paper["pdf_path"],
            paper["original_filename"],
            paper["reader_page"],
            paper["reader_total_pages"],
            paper["reader_scroll"],
            paper["reader_zoom"],
            paper["last_read_at"],
            paper["ai_model"],
            paper["ai_enriched_at"],
            paper["ai_confidence"],
            paper["added_at"],
            paper["updated_at"],
        ),
    )


def row_to_paper(row: sqlite3.Row) -> dict:
    pdf_url = f"/{row['pdf_path'].replace(os.sep, '/')}" if row["pdf_path"] else ""
    progress = 0
    if row["reader_total_pages"]:
        progress = min(100, round((row["reader_page"] / row["reader_total_pages"]) * 100))

    return {
        "id": row["id"],
        "title": row["title"],
        "titleZh": row["title_zh"],
        "authors": json.loads(row["authors_json"] or "[]"),
        "year": row["year"],
        "venue": row["venue"],
        "doi": row["doi"],
        "url": row["url"],
        "status": row["status"],
        "priority": row["priority"],
        "rating": row["rating"],
        "favorite": bool(row["favorite"]),
        "collection": row["collection_name"],
        "category": row["category"],
        "tags": json.loads(row["tags_json"] or "[]"),
        "aiKeywords": json.loads(row["ai_keywords_json"] or "[]"),
        "abstract": row["abstract"],
        "aiSummary": row["ai_summary"],
        "aiSummaryZh": row["ai_summary_zh"],
        "notes": row["notes"],
        "coverImage": row["cover_image"],
        "coverSource": row["cover_source"],
        "pdfPath": row["pdf_path"],
        "pdfUrl": pdf_url,
        "originalFilename": row["original_filename"],
        "readerPage": row["reader_page"],
        "readerTotalPages": row["reader_total_pages"],
        "readerScroll": row["reader_scroll"],
        "readerZoom": row["reader_zoom"],
        "lastReadAt": row["last_read_at"],
        "aiModel": row["ai_model"],
        "aiEnrichedAt": row["ai_enriched_at"],
        "aiConfidence": row["ai_confidence"],
        "readProgress": progress,
        "addedAt": row["added_at"],
        "updatedAt": row["updated_at"],
    }


def list_papers() -> list[dict]:
    with connect_db() as conn:
        rows = conn.execute("SELECT * FROM papers ORDER BY updated_at DESC").fetchall()
    return [row_to_paper(row) for row in rows]


def get_paper(paper_id: str) -> dict | None:
    with connect_db() as conn:
        row = conn.execute("SELECT * FROM papers WHERE id = ?", (paper_id,)).fetchone()
    return row_to_paper(row) if row else None


def update_paper(paper_id: str, patch: dict) -> dict | None:
    current = get_paper(paper_id)
    if not current:
        return None

    next_payload = normalize_paper_payload({**current, **patch, "id": paper_id, "addedAt": current["addedAt"]})
    with connect_db() as conn:
        conn.execute(
            """
            UPDATE papers SET
                title=?, title_zh=?, authors_json=?, year=?, venue=?, doi=?, url=?, status=?, priority=?,
                rating=?, favorite=?, collection_name=?, category=?, tags_json=?, ai_keywords_json=?,
                abstract=?, ai_summary=?, ai_summary_zh=?, notes=?, cover_image=?, cover_source=?, pdf_path=?,
                original_filename=?, reader_page=?, reader_total_pages=?, reader_scroll=?, reader_zoom=?,
                last_read_at=?, ai_model=?, ai_enriched_at=?, ai_confidence=?, updated_at=?
            WHERE id=?
            """,
            (
                next_payload["title"],
                next_payload["title_zh"],
                json.dumps(next_payload["authors"], ensure_ascii=False),
                next_payload["year"],
                next_payload["venue"],
                next_payload["doi"],
                next_payload["url"],
                next_payload["status"],
                next_payload["priority"],
                next_payload["rating"],
                1 if next_payload["favorite"] else 0,
                next_payload["collection"],
                next_payload["category"],
                json.dumps(next_payload["tags"], ensure_ascii=False),
                json.dumps(next_payload["ai_keywords"], ensure_ascii=False),
                next_payload["abstract"],
                next_payload["ai_summary"],
                next_payload["ai_summary_zh"],
                next_payload["notes"],
                next_payload["cover_image"],
                next_payload["cover_source"],
                next_payload["pdf_path"],
                next_payload["original_filename"],
                next_payload["reader_page"],
                next_payload["reader_total_pages"],
                next_payload["reader_scroll"],
                next_payload["reader_zoom"],
                next_payload["last_read_at"],
                next_payload["ai_model"],
                next_payload["ai_enriched_at"],
                next_payload["ai_confidence"],
                next_payload["updated_at"],
                paper_id,
            ),
        )
    return get_paper(paper_id)


def delete_paper(paper_id: str) -> bool:
    current = get_paper(paper_id)
    if not current:
        return False
    cleanup_storage_asset(current.get("coverImage") or "")
    cleanup_rendered_pages(paper_id)
    cleanup_translation_cache(paper_id)
    cleanup_digest_cache(paper_id)
    pdf_path = current.get("pdfPath") or ""
    with connect_db() as conn:
        conn.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
    if pdf_path:
        pdf_file = ROOT / pdf_path
        if pdf_file.exists():
            pdf_file.unlink()
    return True


def reset_db() -> None:
    with connect_db() as conn:
        rows = conn.execute("SELECT pdf_path, cover_image, id FROM papers").fetchall()
        conn.execute("DELETE FROM papers")
        for row in rows:
            if row["pdf_path"]:
                pdf_file = ROOT / row["pdf_path"]
                if pdf_file.exists():
                    pdf_file.unlink()
            cleanup_storage_asset(row["cover_image"] or "")
            cleanup_rendered_pages(row["id"])
            cleanup_translation_cache(row["id"])
            cleanup_digest_cache(row["id"])
        for paper in SEED_PAPERS:
            insert_paper(conn, normalize_paper_payload(paper))


def safe_filename(name: str) -> str:
    base = re.sub(r"[^A-Za-z0-9._-]+", "_", Path(name).name)
    return base or "paper.pdf"


def looks_like_title(text: str) -> bool:
    candidate = normalize_whitespace(text)
    if len(candidate) < 12 or len(candidate) > 240:
        return False
    if sum(character.isalpha() for character in candidate) < 6:
        return False
    lower = candidate.lower()
    banned_prefixes = (
        "abstract",
        "introduction",
        "references",
        "acknowledgements",
        "proceedings of",
        "submitted to",
        "arxiv:",
    )
    if any(lower.startswith(prefix) for prefix in banned_prefixes):
        return False
    if "@" in candidate or "http://" in lower or "https://" in lower:
        return False
    return True


def extract_text_pages(pdf_path: Path, max_pages: int = 3) -> list[str]:
    reader = PdfReader(str(pdf_path))
    pages: list[str] = []
    for page in reader.pages[:max_pages]:
        pages.append(normalize_whitespace(page.extract_text() or ""))
    return pages


def extract_all_text_pages(pdf_path: Path, max_pages: int = 24) -> list[str]:
    reader = PdfReader(str(pdf_path))
    pages: list[str] = []
    for page in reader.pages[:max_pages]:
        text = normalize_whitespace(page.extract_text() or "")
        if text:
            pages.append(text)
    return pages


def digest_cache_path(paper_id: str) -> Path:
    return DIGEST_DIR / f"{paper_id}.json"


def load_digest_cache(paper_id: str) -> dict | None:
    cache_path = digest_cache_path(paper_id)
    if not cache_path.exists():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def save_digest_cache(paper_id: str, payload: dict) -> None:
    digest_cache_path(paper_id).write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_multiline_text(value: str, limit: int = 3200) -> str:
    cleaned = re.sub(r"[ \t]+", " ", value or "")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()[:limit]


def extract_section_slice(full_text: str, names: list[str], stop_names: list[str], limit: int = 3200) -> str:
    heading = "|".join(re.escape(name) for name in names)
    stops = "|".join(re.escape(name) for name in stop_names)
    pattern = rf"(?:^|\n)\s*(?:\d+(?:\.\d+){{0,2}}\s+)?(?:{heading})\s*[\n:.-]*(.+?)(?=(?:^|\n)\s*(?:\d+(?:\.\d+){{0,2}}\s+)?(?:{stops})\b|\Z)"
    match = re.search(pattern, full_text, flags=re.IGNORECASE | re.DOTALL | re.MULTILINE)
    if not match:
        return ""
    return normalize_multiline_text(match.group(1), limit=limit)


def extract_method_slice(full_text: str) -> str:
    return extract_section_slice(
        full_text,
        ["method", "methods", "methodology", "approach", "approaches", "proposed method", "framework"],
        [
            "experiment",
            "experiments",
            "experimental setup",
            "results",
            "evaluation",
            "ablation",
            "discussion",
            "conclusion",
            "conclusions",
            "references",
        ],
        limit=5000,
    )


def extract_conclusion_slice(full_text: str) -> str:
    extracted = extract_section_slice(
        full_text,
        ["conclusion", "conclusions", "concluding remarks", "discussion and conclusion"],
        ["references", "appendix", "acknowledgements"],
        limit=2600,
    )
    if extracted:
        return extracted
    tail = re.split(r"\breferences\b", full_text, maxsplit=1, flags=re.IGNORECASE)[0]
    tail = tail[-2400:]
    return normalize_multiline_text(tail, limit=1800)


def extract_digest_candidates(paper: dict) -> dict:
    pdf_path = ROOT / paper["pdfPath"] if paper.get("pdfPath") else None
    pages = extract_all_text_pages(pdf_path, max_pages=24) if pdf_path and pdf_path.exists() else []
    full_text = "\n\n".join(page for page in pages if page)
    abstract = extract_abstract(full_text) or paper.get("abstract", "")
    method = extract_method_slice(full_text)
    conclusion = extract_conclusion_slice(full_text)
    return {
        "abstract": normalize_multiline_text(abstract, limit=2400),
        "method": normalize_multiline_text(method, limit=4200),
        "conclusion": normalize_multiline_text(conclusion, limit=2200),
        "fullTextExcerpt": normalize_multiline_text(full_text, limit=18000),
    }


def infer_title_from_pdf(document: fitz.Document, fallback_title: str) -> str:
    metadata_title = normalize_whitespace((document.metadata or {}).get("title", ""))
    if looks_like_title(metadata_title) and "microsoft word" not in metadata_title.lower():
        return metadata_title

    first_page = document.load_page(0)
    text_dict = first_page.get_text("dict")
    line_candidates: list[dict] = []
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            pieces = []
            max_size = 0.0
            for span in line.get("spans", []):
                piece = normalize_whitespace(span.get("text", ""))
                if not piece:
                    continue
                pieces.append(piece)
                max_size = max(max_size, float(span.get("size", 0.0)))
            merged = normalize_whitespace(" ".join(pieces))
            if merged:
                line_candidates.append(
                    {
                        "text": merged,
                        "size": max_size,
                        "y": float(line.get("bbox", [0, 0, 0, 0])[1]),
                    }
                )

    if line_candidates:
        max_size = max(item["size"] for item in line_candidates)
        title_lines = [
            item
            for item in line_candidates
            if item["size"] >= max(14.0, max_size * 0.78)
            and item["y"] <= first_page.rect.height * 0.42
            and looks_like_title(item["text"])
        ]
        title_lines.sort(key=lambda item: (item["y"], -item["size"]))
        if title_lines:
            merged_title = normalize_whitespace(" ".join(item["text"] for item in title_lines[:3]))
            if looks_like_title(merged_title):
                return merged_title

    for line in re.split(r"[\r\n]+", normalize_whitespace(first_page.get_text("text"))):
        if looks_like_title(line):
            return line
    return fallback_title


def extract_abstract(full_text: str) -> str:
    match = re.search(
        r"\babstract\b[:\s-]*(.+?)(?=\b(?:keywords?|index terms|1\.?\s+introduction|introduction)\b)",
        full_text,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return ""
    return normalize_whitespace(match.group(1))[:1400]


def infer_tags(title: str, full_text: str) -> list[str]:
    searchable = f"{title}\n{full_text}".lower()
    scores: Counter[str] = Counter()
    for tag, keywords in TAG_RULES.items():
        for keyword in keywords:
            hits = len(re.findall(re.escape(keyword.lower()), searchable))
            if hits:
                scores[tag] += hits
    tags = [tag for tag, score in scores.most_common() if score > 0]
    if "survey" in title.lower() and "Survey" not in tags:
        tags.insert(0, "Survey")
    if not tags:
        tags = ["PDF"]
    return tags[:8]


def infer_category(tags: list[str], title: str) -> str:
    mapping = {
        "LLM": "Foundation Models",
        "Transformer": "Foundation Models",
        "RAG": "RAG",
        "Agents": "Agents",
        "NLP": "NLP",
        "Multimodal": "Multimodal",
        "Computer Vision": "Computer Vision",
        "Diffusion": "Diffusion",
        "Graph": "Graph ML",
        "Recommendation": "Recommendation",
        "Time Series": "Time Series",
        "Reinforcement Learning": "Reinforcement Learning",
        "Optimization": "Optimization",
        "Security": "Security",
        "Survey": "Survey",
    }
    for tag in tags:
        if tag in mapping:
            return mapping[tag]
    if "survey" in title.lower():
        return "Survey"
    return "Other"


def generate_cover_svg(paper_id: str, title: str, tags: list[str]) -> str:
    svg_path = COVER_DIR / f"{paper_id}.svg"
    title_lines = re.findall(r".{1,22}(?:\s+|$)", title)[:4] or ["Imported PDF"]
    safe_title = [
        line.strip().replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        for line in title_lines
        if line.strip()
    ]
    title_markup = "".join(
        f'<text x="56" y="{140 + index * 48}" font-size="38" font-weight="700" fill="#fff7ea">{line}</text>'
        for index, line in enumerate(safe_title)
    )
    tag_markup = "".join(
        f'<text x="56" y="{420 + index * 34}" font-size="24" fill="#f7efe2" opacity="0.92">#{tag}</text>'
        for index, tag in enumerate(tags[:3])
    )
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="720" height="960" viewBox="0 0 720 960">
<defs>
  <linearGradient id="bg" x1="0%" y1="0%" x2="100%" y2="100%">
    <stop offset="0%" stop-color="#17342d"/>
    <stop offset="100%" stop-color="#9a6a34"/>
  </linearGradient>
</defs>
<rect width="720" height="960" rx="28" fill="url(#bg)"/>
<rect x="40" y="40" width="640" height="880" rx="24" fill="rgba(255,255,255,0.06)" stroke="rgba(255,255,255,0.18)"/>
<text x="56" y="86" font-size="18" letter-spacing="5" fill="#dbc9af">PAPER HUB</text>
{title_markup}
<text x="56" y="370" font-size="24" fill="#f0e0c8" opacity="0.82">Auto-generated cover</text>
{tag_markup}
</svg>"""
    svg_path.write_text(svg, encoding="utf-8")
    return f"/storage/covers/{svg_path.name}"


def render_pdf_cover(paper_id: str, pdf_path: Path, title: str, tags: list[str]) -> tuple[str, str]:
    try:
        document = fitz.open(pdf_path)
        page = document.load_page(0)
        pixmap = page.get_pixmap(matrix=fitz.Matrix(1.45, 1.45), alpha=False)
        output_path = COVER_DIR / f"{paper_id}.png"
        pixmap.save(output_path)
        document.close()
        return (f"/storage/covers/{output_path.name}", "pdf-first-page")
    except Exception:
        return (generate_cover_svg(paper_id, title, tags), "generated")


def render_pdf_pages(paper_id: str, pdf_path: Path) -> list[dict]:
    target_dir = RENDER_DIR / paper_id
    target_dir.mkdir(parents=True, exist_ok=True)
    document = fitz.open(pdf_path)
    pages: list[dict] = []
    try:
        for index in range(document.page_count):
            page = document.load_page(index)
            filename = f"page-{index + 1:04d}.png"
            output_path = target_dir / filename
            if not output_path.exists():
                pixmap = page.get_pixmap(matrix=fitz.Matrix(1.35, 1.35), alpha=False)
                pixmap.save(output_path)
            pages.append(
                {
                    "page": index + 1,
                    "width": int(page.rect.width),
                    "height": int(page.rect.height),
                    "imageUrl": f"/storage/renders/{paper_id}/{filename}",
                }
            )
    finally:
        document.close()
    return pages


def translation_cache_path(paper_id: str) -> Path:
    return TRANSLATION_DIR / f"{paper_id}.json"


def translation_cache_lock(paper_id: str) -> threading.Lock:
    with TRANSLATION_CACHE_LOCKS_GUARD:
        lock = TRANSLATION_CACHE_LOCKS.get(paper_id)
        if lock is None:
            lock = threading.Lock()
            TRANSLATION_CACHE_LOCKS[paper_id] = lock
        return lock


def load_translation_cache(paper_id: str) -> dict:
    cache_path = translation_cache_path(paper_id)
    if not cache_path.exists():
        return {"paperId": paper_id, "pages": {}}
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"paperId": paper_id, "pages": {}}
    if not isinstance(payload, dict):
        return {"paperId": paper_id, "pages": {}}
    payload.setdefault("paperId", paper_id)
    payload.setdefault("pages", {})
    return payload


def current_translation_cache(paper_id: str) -> dict:
    cache = load_translation_cache(paper_id)
    current_provider = current_ai_provider()
    current_model = current_ai_model()
    current_mode = "vision" if provider_supports_vision() else "text"
    if cache.get("aiModel") != current_model or cache.get("aiProvider") != current_provider or cache.get("translationMode") != current_mode:
        return {
            "paperId": paper_id,
            "pages": {},
            "aiModel": current_model if ai_enabled() else "",
            "aiProvider": current_provider if ai_enabled() else "",
            "translationMode": current_mode if ai_enabled() else "",
        }
    return cache


def save_translation_cache(paper_id: str, payload: dict) -> None:
    cache_path = translation_cache_path(paper_id)
    cache_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def should_translate_text(text: str) -> bool:
    candidate = normalize_whitespace(text)
    if len(candidate) < 2:
        return False
    if re.fullmatch(r"[\d\W_]+", candidate):
        return False
    letters = sum(character.isalpha() for character in candidate)
    return letters >= 2 or contains_cjk(candidate)


def extract_page_text_blocks(pdf_path: Path, page_number: int) -> dict:
    if page_number < 1:
        raise ValueError("page must be >= 1")

    document = fitz.open(pdf_path)
    try:
        if page_number > document.page_count:
            raise ValueError("page exceeds PDF page count")
        page = document.load_page(page_number - 1)
        width = float(page.rect.width)
        height = float(page.rect.height)
        text_dict = page.get_text("dict")
    finally:
        document.close()

    blocks: list[dict] = []
    next_index = 0
    for block in text_dict.get("blocks", []):
        if block.get("type") != 0:
            continue
        lines: list[str] = []
        font_sizes: list[float] = []
        for line in block.get("lines", []):
            spans: list[str] = []
            for span in line.get("spans", []):
                text = normalize_whitespace(str(span.get("text") or ""))
                if not text:
                    continue
                spans.append(text)
                font_sizes.append(max(8.0, normalize_float(span.get("size"), 12.0)))
            if spans:
                lines.append(" ".join(spans))
        text = normalize_whitespace("\n".join(lines))
        bbox = block.get("bbox") or [0, 0, 0, 0]
        x0, y0, x1, y1 = [round(float(value), 2) for value in bbox]
        if not should_translate_text(text):
            continue
        if x1 - x0 < 6 or y1 - y0 < 6:
            continue
        blocks.append(
            {
                "index": next_index,
                "text": text,
                "x": x0,
                "y": y0,
                "width": round(x1 - x0, 2),
                "height": round(y1 - y0, 2),
                "fontSize": round(max(font_sizes) if font_sizes else 12.0, 2),
            }
        )
        next_index += 1

    return {
        "page": page_number,
        "width": round(width, 2),
        "height": round(height, 2),
        "blocks": blocks,
    }


def extract_pdf_profile(paper_id: str, pdf_path: Path, original_name: str) -> dict:
    fallback_title = Path(original_name).stem.replace("_", " ").strip() or "Imported PDF"
    title = fallback_title
    abstract = ""
    tags: list[str] = []
    authors: list[str] = []

    try:
        document = fitz.open(pdf_path)
        title = infer_title_from_pdf(document, fallback_title)
        author_text = normalize_whitespace((document.metadata or {}).get("author", ""))
        if author_text:
            authors = [item.strip() for item in re.split(r"[;,]", author_text) if item.strip()]
        page_count = document.page_count
        document.close()
    except Exception:
        page_count = 0

    try:
        text_pages = extract_text_pages(pdf_path, max_pages=3)
    except Exception:
        text_pages = []

    full_text = normalize_whitespace("\n".join(page for page in text_pages if page))
    if full_text:
        abstract = extract_abstract(full_text)
        tags = infer_tags(title, full_text)
    else:
        tags = infer_tags(title, title)

    category = infer_category(tags, title)
    cover_image, cover_source = render_pdf_cover(paper_id, pdf_path, title, tags)
    return {
        "title": title,
        "titleZh": "",
        "authors": authors,
        "tags": tags,
        "aiKeywords": tags[:4],
        "abstract": abstract,
        "aiSummary": abstract[:220],
        "aiSummaryZh": "",
        "coverImage": cover_image,
        "coverSource": cover_source,
        "category": category,
        "collection": category,
        "readerTotalPages": page_count,
    }


def build_ai_excerpt(paper: dict) -> str:
    pdf_path = ROOT / paper["pdfPath"] if paper.get("pdfPath") else None
    parts = [
        f"Current title: {paper.get('title', '')}",
        f"Authors: {', '.join(paper.get('authors', []))}",
        f"Venue: {paper.get('venue', '')}",
        f"Year: {paper.get('year', 0)}",
        f"Existing abstract: {paper.get('abstract', '')}",
    ]
    if pdf_path and pdf_path.exists():
        try:
            parts.append("\nPDF excerpt:\n" + "\n".join(extract_text_pages(pdf_path, max_pages=3))[:14000])
        except Exception:
            pass
    return "\n".join(part for part in parts if part).strip()


def normalize_provider_id(value: str) -> str:
    provider_id = normalize_whitespace(value).lower()
    return provider_id if provider_id in PROVIDER_PRESET_MAP else "openai"


def infer_provider_from_api_url(api_url: str) -> str:
    lowered = (api_url or "").strip().lower()
    if not lowered:
        return ""
    for preset in PROVIDER_PRESETS:
        for hint in preset.get("urlHints", []):
            if hint in lowered:
                return preset["id"]
    return ""


def infer_env_provider() -> str:
    explicit = normalize_provider_id(os.environ.get("AI_PROVIDER", ""))
    if explicit in PROVIDER_PRESET_MAP:
        return explicit

    inferred = infer_provider_from_api_url(os.environ.get("AI_API_URL", ""))
    if inferred:
        return inferred

    for preset in PROVIDER_PRESETS:
        for key_name in preset.get("apiKeyEnv", []):
            if os.environ.get(key_name, "").strip():
                return preset["id"]
    return "openai"


def env_value_for_provider(provider_id: str, value_type: str) -> str:
    selected_provider = infer_env_provider()
    explicit_key = f"AI_{value_type.upper()}"
    explicit = os.environ.get(explicit_key, "").strip()
    if explicit and provider_id == selected_provider:
        return explicit

    preset = PROVIDER_PRESET_MAP.get(provider_id, PROVIDER_PRESET_MAP["openai"])
    if value_type == "apiKey":
        for key_name in preset.get("apiKeyEnv", []):
            value = os.environ.get(key_name, "").strip()
            if value:
                return value
        return ""
    if value_type == "model":
        return preset.get("defaultModel", "")
    if value_type == "apiUrl":
        return preset.get("defaultApiUrl", "")
    return ""


def build_default_provider_config() -> dict:
    providers = {}
    for preset in PROVIDER_PRESETS:
        provider_id = preset["id"]
        providers[provider_id] = {
            "model": env_value_for_provider(provider_id, "model"),
            "apiUrl": env_value_for_provider(provider_id, "apiUrl"),
            "apiKey": env_value_for_provider(provider_id, "apiKey"),
        }
    return {
        "selectedProvider": infer_env_provider(),
        "providers": providers,
    }


def load_provider_config() -> dict:
    config = build_default_provider_config()
    if not PROVIDER_CONFIG_PATH.exists():
        return config

    try:
        raw = json.loads(PROVIDER_CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return config

    if not isinstance(raw, dict):
        return config

    selected = normalize_provider_id(str(raw.get("selectedProvider") or config["selectedProvider"]))
    config["selectedProvider"] = selected
    saved_providers = raw.get("providers")
    if isinstance(saved_providers, dict):
        for provider_id in PROVIDER_PRESET_MAP:
            saved = saved_providers.get(provider_id)
            if not isinstance(saved, dict):
                continue
            profile = config["providers"][provider_id]
            model = normalize_whitespace(str(saved.get("model") or ""))
            api_url = normalize_whitespace(str(saved.get("apiUrl") or ""))
            api_key = normalize_whitespace(str(saved.get("apiKey") or ""))
            if model:
                profile["model"] = model
            if api_url:
                profile["apiUrl"] = api_url
            if api_key:
                profile["apiKey"] = api_key
    return config


def save_provider_config(payload: dict) -> dict:
    current = load_provider_config()
    selected = normalize_provider_id(str(payload.get("selectedProvider") or current["selectedProvider"]))
    current["selectedProvider"] = selected

    saved_providers = payload.get("providers")
    if isinstance(saved_providers, dict):
        for provider_id in PROVIDER_PRESET_MAP:
            if not isinstance(saved_providers.get(provider_id), dict):
                continue
            incoming = saved_providers[provider_id]
            profile = current["providers"].setdefault(provider_id, {})
            model = normalize_whitespace(str(incoming.get("model") or ""))
            api_url = normalize_whitespace(str(incoming.get("apiUrl") or ""))
            api_key = normalize_whitespace(str(incoming.get("apiKey") or ""))
            clear_api_key = bool(incoming.get("clearApiKey"))
            if model:
                profile["model"] = model
            if api_url:
                profile["apiUrl"] = api_url
            if api_key:
                profile["apiKey"] = api_key
            elif clear_api_key:
                profile["apiKey"] = ""

    PROVIDER_CONFIG_PATH.write_text(json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8")
    return current


def active_provider_settings() -> dict:
    config = load_provider_config()
    provider_id = normalize_provider_id(config.get("selectedProvider") or "openai")
    preset = PROVIDER_PRESET_MAP.get(provider_id, PROVIDER_PRESET_MAP["openai"])
    profile = config.get("providers", {}).get(provider_id, {})
    api_key = normalize_whitespace(str(profile.get("apiKey") or ""))
    model = normalize_whitespace(str(profile.get("model") or preset.get("defaultModel") or ""))
    api_url = normalize_whitespace(str(profile.get("apiUrl") or preset.get("defaultApiUrl") or ""))
    return {
        **preset,
        "provider": provider_id,
        "model": model,
        "apiUrl": api_url,
        "apiKey": api_key,
        "enabled": (not preset.get("requiresApiKey")) or bool(api_key),
    }


def normalize_runtime_provider_settings(settings: dict) -> dict:
    normalized = dict(settings)
    api_url = normalize_whitespace(str(normalized.get("apiUrl") or ""))
    provider_id = normalize_whitespace(str(normalized.get("provider") or ""))
    protocol = normalize_whitespace(str(normalized.get("protocol") or ""))

    if not api_url:
        return normalized

    parsed = urlparse(api_url)
    host = (parsed.netloc or "").lower()
    path = (parsed.path or "").rstrip("/")

    def with_chat_completions(url: str) -> str:
        stripped = url.rstrip("/")
        parsed_url = urlparse(stripped)
        current_path = (parsed_url.path or "").rstrip("/")
        if current_path.endswith("/chat/completions"):
            return stripped
        if current_path.endswith("/v1"):
            return stripped + "/chat/completions"
        if not current_path:
            return stripped + "/v1/chat/completions"
        return stripped

    if provider_id == "relay-openai":
        normalized["protocol"] = "openai_chat"
        normalized["apiUrl"] = with_chat_completions(api_url)
        return normalized

    if provider_id == "openai" and host and "api.openai.com" not in host:
        normalized["protocol"] = "openai_chat"
        normalized["apiUrl"] = with_chat_completions(api_url)
        return normalized

    if protocol in {"openai_chat", "azure_openai_chat"}:
        normalized["apiUrl"] = with_chat_completions(api_url)
    return normalized


def provider_supports_vision(provider_id: str | None = None) -> bool:
    settings = active_provider_settings() if not provider_id else {**PROVIDER_PRESET_MAP.get(provider_id, {}), "provider": provider_id}
    return bool(settings.get("supportsVision"))


def public_provider_presets() -> list[dict]:
    return [
        {
            "id": preset["id"],
            "label": preset["label"],
            "protocol": preset["protocol"],
            "defaultModel": preset["defaultModel"],
            "defaultApiUrl": preset["defaultApiUrl"],
            "requiresApiKey": preset["requiresApiKey"],
            "supportsVision": preset["supportsVision"],
            "description": preset["description"],
        }
        for preset in PROVIDER_PRESETS
    ]


def provider_config_for_client() -> dict:
    config = load_provider_config()
    providers: dict[str, dict] = {}
    for provider_id, preset in PROVIDER_PRESET_MAP.items():
        profile = config.get("providers", {}).get(provider_id, {})
        api_key = normalize_whitespace(str(profile.get("apiKey") or ""))
        providers[provider_id] = {
            "model": normalize_whitespace(str(profile.get("model") or preset.get("defaultModel") or "")),
            "apiUrl": normalize_whitespace(str(profile.get("apiUrl") or preset.get("defaultApiUrl") or "")),
            "hasApiKey": bool(api_key),
            "apiKeyMasked": f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) >= 8 else ("saved" if api_key else ""),
        }
    return {
        "selectedProvider": normalize_provider_id(config.get("selectedProvider") or "openai"),
        "providers": providers,
        "presets": public_provider_presets(),
    }


def current_ai_provider() -> str:
    return active_provider_settings()["provider"]


def current_ai_api_key() -> str:
    return active_provider_settings()["apiKey"]


def current_ai_model() -> str:
    return active_provider_settings()["model"]


def current_ai_api_url() -> str:
    return active_provider_settings()["apiUrl"]


def ai_enabled() -> bool:
    return active_provider_settings()["enabled"]


def extract_response_text(payload: dict) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()
    for item in payload.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()
    raise ValueError("OpenAI response did not contain text output")


def parse_json_text(raw_text: str) -> dict:
    text = (raw_text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)


def contains_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def extract_choice_message_text(payload: dict) -> str:
    choices = payload.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ValueError("provider response did not contain choices")
    message = choices[0].get("message", {})
    content = message.get("content", "")
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts: list[str] = []
        for item in content:
            if isinstance(item, dict) and isinstance(item.get("text"), str):
                parts.append(item["text"])
        if parts:
            return "\n".join(parts).strip()
    raise ValueError("provider response did not contain message text")


def extract_anthropic_text(payload: dict) -> str:
    content = payload.get("content")
    if not isinstance(content, list):
        raise ValueError("Anthropic response did not contain content")
    parts: list[str] = []
    for item in content:
        if isinstance(item, dict) and item.get("type") == "text" and isinstance(item.get("text"), str):
            parts.append(item["text"])
    if not parts:
        raise ValueError("Anthropic response did not contain text")
    return "\n".join(parts).strip()


def extract_gemini_text(payload: dict) -> str:
    candidates = payload.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("Gemini response did not contain candidates")
    parts = candidates[0].get("content", {}).get("parts", [])
    text_chunks = [item.get("text", "") for item in parts if isinstance(item, dict) and isinstance(item.get("text"), str)]
    text = "\n".join(chunk for chunk in text_chunks if chunk).strip()
    if not text:
        raise ValueError("Gemini response did not contain text")
    return text


def normalize_image_inputs(images: list[dict] | None) -> list[dict]:
    normalized: list[dict] = []
    for image in images or []:
        if not isinstance(image, dict):
            continue
        mime_type = normalize_whitespace(str(image.get("mimeType") or "image/png")) or "image/png"
        data_base64 = normalize_whitespace(str(image.get("base64") or ""))
        data_url = normalize_whitespace(str(image.get("dataUrl") or ""))
        if not data_base64 and data_url.startswith("data:") and "," in data_url:
            data_base64 = data_url.split(",", 1)[1].strip()
        if not data_url and data_base64:
            data_url = f"data:{mime_type};base64,{data_base64}"
        if data_base64 and data_url:
            normalized.append({"mimeType": mime_type, "base64": data_base64, "dataUrl": data_url})
    return normalized


def provider_headers(settings: dict) -> dict:
    protocol = settings.get("protocol")
    headers = {"Content-Type": "application/json"}
    if protocol == "anthropic_messages":
        headers["x-api-key"] = settings["apiKey"]
        headers["anthropic-version"] = "2023-06-01"
        return headers
    if protocol == "azure_openai_chat":
        headers["api-key"] = settings["apiKey"]
        return headers
    if protocol == "gemini_generate_content":
        return headers
    if settings.get("apiKey"):
        headers["Authorization"] = f"Bearer {settings['apiKey']}"
    return headers


def provider_request_url(settings: dict) -> str:
    protocol = settings.get("protocol")
    api_url = settings.get("apiUrl", "")
    if protocol != "gemini_generate_content":
        return api_url

    model = settings.get("model", "")
    base_url = api_url.rstrip("/")
    if ":generateContent" in base_url:
        endpoint = base_url
    elif base_url.endswith("/models"):
        endpoint = f"{base_url}/{quote(model, safe='')}:generateContent"
    elif "/models/" in base_url:
        endpoint = base_url if base_url.endswith(":generateContent") else f"{base_url}:generateContent"
    else:
        endpoint = f"{GEMINI_GENERATE_CONTENT_URL}/{quote(model, safe='')}:generateContent"

    separator = "&" if "?" in endpoint else "?"
    return f"{endpoint}{separator}key={quote(settings['apiKey'], safe='')}"


def build_json_instruction() -> str:
    return "Return JSON only. Output one valid json object and no markdown."


def summarize_provider_response(raw_text: str, limit: int = 240) -> str:
    compact = re.sub(r"\s+", " ", raw_text or "").strip()
    if not compact:
        return "<empty response>"
    return compact[:limit]


def extract_embedded_json_text(raw_text: str) -> str:
    text = (raw_text or "").strip()
    if not text:
        return ""
    if text.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", text)
        stripped = re.sub(r"\s*```$", "", stripped)
        if stripped.strip():
            return stripped.strip()

    start = min([index for index in (text.find("{"), text.find("[")) if index != -1], default=-1)
    if start == -1:
        return ""

    opening = text[start]
    closing = "}" if opening == "{" else "]"
    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            continue
        if char == opening:
            depth += 1
        elif char == closing:
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return ""


def coerce_provider_payload(raw_text: str, protocol: str):
    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError:
        parsed = None

    if parsed is not None:
        if isinstance(parsed, dict) and any(key in parsed for key in ("choices", "output", "content", "candidates")):
            return parsed
        if protocol == "openai_responses":
            return {"output_text": json.dumps(parsed, ensure_ascii=False)}
        if protocol in {"openai_chat", "azure_openai_chat"}:
            return {"choices": [{"message": {"content": json.dumps(parsed, ensure_ascii=False)}}]}
        if protocol == "anthropic_messages":
            return {"content": [{"type": "text", "text": json.dumps(parsed, ensure_ascii=False)}]}
        if protocol == "gemini_generate_content":
            return {"candidates": [{"content": {"parts": [{"text": json.dumps(parsed, ensure_ascii=False)}]}}]}

    embedded = extract_embedded_json_text(raw_text)
    if embedded:
        try:
            parsed = json.loads(embedded)
        except json.JSONDecodeError:
            parsed = None
        if parsed is not None:
            if isinstance(parsed, dict) and any(key in parsed for key in ("choices", "output", "content", "candidates")):
                return parsed
            if protocol == "openai_responses":
                return {"output_text": embedded}
            if protocol in {"openai_chat", "azure_openai_chat"}:
                return {"choices": [{"message": {"content": embedded}}]}
            if protocol == "anthropic_messages":
                return {"content": [{"type": "text", "text": embedded}]}
            if protocol == "gemini_generate_content":
                return {"candidates": [{"content": {"parts": [{"text": embedded}]}}]}
    return None


def call_ai_json(system_prompt: str, user_prompt: str, schema: dict, images: list[dict] | None = None, timeout: int = 60) -> dict:
    settings = normalize_runtime_provider_settings(active_provider_settings())
    if not settings.get("enabled"):
        raise RuntimeError("AI API key is not set")

    protocol = settings.get("protocol")
    model = settings.get("model")
    image_inputs = normalize_image_inputs(images)
    system_text = f"{system_prompt.strip()} {build_json_instruction()}".strip()
    user_text = f"{user_prompt.strip()}\n\n{build_json_instruction()}".strip()

    if protocol == "openai_responses":
        user_content = [{"type": "input_text", "text": user_text}]
        for image in image_inputs:
            user_content.append({"type": "input_image", "image_url": image["dataUrl"]})
        request_body = {
            "model": model,
            "input": [
                {
                    "role": "system",
                    "content": [{"type": "input_text", "text": system_text}],
                },
                {
                    "role": "user",
                    "content": user_content,
                },
            ],
            "reasoning": {"effort": "low"},
            "text": {
                "format": {
                    "type": "json_schema",
                    "name": "paper_hub_payload",
                    "schema": schema,
                    "strict": True,
                }
            },
        }
    elif protocol in {"openai_chat", "azure_openai_chat"}:
        if image_inputs:
            user_content = [{"type": "text", "text": user_text}]
            for image in image_inputs:
                user_content.append({"type": "image_url", "image_url": {"url": image["dataUrl"]}})
        else:
            user_content = user_text
        request_body = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_text},
                {"role": "user", "content": user_content},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }
    elif protocol == "anthropic_messages":
        user_content = [{"type": "text", "text": user_text}]
        for image in image_inputs:
            user_content.append(
                {
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": image["mimeType"],
                        "data": image["base64"],
                    },
                }
            )
        request_body = {
            "model": model,
            "max_tokens": 4096,
            "system": system_text,
            "messages": [{"role": "user", "content": user_content}],
        }
    elif protocol == "gemini_generate_content":
        user_parts = [{"text": user_text}]
        for image in image_inputs:
            user_parts.append(
                {
                    "inline_data": {
                        "mime_type": image["mimeType"],
                        "data": image["base64"],
                    }
                }
            )
        request_body = {
            "system_instruction": {"parts": [{"text": system_text}]},
            "contents": [{"role": "user", "parts": user_parts}],
            "generationConfig": {
                "temperature": 0.1,
                "responseMimeType": "application/json",
            },
        }
    else:
        raise RuntimeError(f"unsupported provider protocol: {protocol}")

    request = urllib.request.Request(
        provider_request_url(settings),
        data=json.dumps(request_body).encode("utf-8"),
        headers=provider_headers(settings),
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw_body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{settings['provider']} request failed: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"{settings['provider']} request failed: {exc.reason}") from exc

    payload = coerce_provider_payload(raw_body, protocol)
    if payload is None:
        preview = summarize_provider_response(raw_body)
        raise RuntimeError(
            f"{settings['provider']} returned a non-JSON response. Check API URL / relay config. Preview: {preview}"
        )

    try:
        if protocol == "openai_responses":
            return parse_json_text(extract_response_text(payload))
        if protocol in {"openai_chat", "azure_openai_chat"}:
            return parse_json_text(extract_choice_message_text(payload))
        if protocol == "anthropic_messages":
            return parse_json_text(extract_anthropic_text(payload))
        if protocol == "gemini_generate_content":
            return parse_json_text(extract_gemini_text(payload))
    except (KeyError, ValueError, json.JSONDecodeError, TypeError) as exc:
        preview = summarize_provider_response(json.dumps(payload, ensure_ascii=False))
        raise RuntimeError(
            f"{settings['provider']} returned an unexpected JSON payload. Check model / relay compatibility. Preview: {preview}"
        ) from exc
    raise RuntimeError(f"unsupported provider protocol: {protocol}")


def load_page_image_input(paper_id: str, pdf_path: Path, page_number: int) -> dict:
    if page_number < 1:
        raise ValueError("page must be >= 1")
    target_dir = RENDER_DIR / paper_id
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"page-{page_number:04d}.png"
    output_path = target_dir / filename
    if not output_path.exists():
        document = fitz.open(pdf_path)
        try:
            if page_number > document.page_count:
                raise ValueError("page exceeds PDF page count")
            page = document.load_page(page_number - 1)
            pixmap = page.get_pixmap(matrix=fitz.Matrix(1.7, 1.7), alpha=False)
            pixmap.save(output_path)
        finally:
            document.close()
    raw = output_path.read_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    return {
        "mimeType": "image/png",
        "base64": encoded,
        "dataUrl": f"data:image/png;base64,{encoded}",
    }


def normalize_ai_enrichment_response(current: dict, enrichment: dict) -> dict:
    normalized = dict(enrichment)
    title = normalize_whitespace(str(normalized.get("title") or ""))
    title_zh = normalize_whitespace(str(normalized.get("title_zh") or ""))
    summary = normalize_whitespace(str(normalized.get("summary") or ""))
    summary_zh = normalize_whitespace(str(normalized.get("summary_zh") or ""))

    if not title_zh and contains_cjk(title) and not contains_cjk(current.get("title", "")):
        title_zh = title
        title = current.get("title", "") or title

    if not summary_zh and contains_cjk(summary):
        summary_zh = summary
        summary = current.get("abstract", "") or summary

    normalized["title"] = title
    normalized["title_zh"] = title_zh
    normalized["summary"] = summary
    normalized["summary_zh"] = summary_zh
    return normalized


def call_ai_enrichment(paper: dict) -> dict:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "title": {"type": "string"},
            "title_zh": {"type": "string"},
            "summary": {"type": "string"},
            "summary_zh": {"type": "string"},
            "tags": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
            "keywords": {"type": "array", "items": {"type": "string"}, "maxItems": 8},
            "category": {"type": "string", "enum": CATEGORY_CHOICES},
            "collection": {"type": "string"},
            "reading_priority": {"type": "string", "enum": ["low", "medium", "high"]},
            "confidence": {"type": "number"},
            "venue_guess": {"type": "string"},
            "year_guess": {"type": "integer"},
        },
        "required": [
            "title",
            "title_zh",
            "summary",
            "summary_zh",
            "tags",
            "keywords",
            "category",
            "collection",
            "reading_priority",
            "confidence",
            "venue_guess",
            "year_guess",
        ],
    }

    system_prompt = (
        "You extract metadata for academic papers. "
        "Prefer the real paper title from the document over filenames. "
        "Keep title as the original paper title. "
        "Put the Chinese title in title_zh. "
        "Return summary_zh in polished Simplified Chinese. "
        "Tags, keywords, and collection must use concise Simplified Chinese phrases. "
        "Return short practical tags and one category from the enum. "
        "All user-facing outputs except title must prefer Simplified Chinese."
    )
    return call_ai_json(system_prompt, build_ai_excerpt(paper), schema, timeout=60)


def call_ai_page_translation(paper: dict, page_number: int, blocks: list[dict]) -> dict:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "blocks": {
                "type": "array",
                "items": {
                    "type": "object",
                    "additionalProperties": False,
                    "properties": {
                        "index": {"type": "integer"},
                        "text_zh": {"type": "string"},
                    },
                    "required": ["index", "text_zh"],
                },
            }
        },
        "required": ["blocks"],
    }
    source_blocks = [{"index": block["index"], "text": block["text"]} for block in blocks]
    supports_vision = provider_supports_vision()
    system_prompt = (
        "You translate academic paper text blocks into concise natural Simplified Chinese. "
        "Use the page image as the source of truth for layout, table cells, figure captions, equations, and OCR mistakes. "
        "The translated text must be fully in Simplified Chinese. "
        "Preserve formulas, citation markers, code, URLs, and symbols when translating would harm fidelity. "
        "Do not summarize. Keep one output item per input item."
        if supports_vision
        else "You translate academic paper text blocks into concise natural Simplified Chinese. "
        "The translated text must be fully in Simplified Chinese. "
        "Preserve formulas, citation markers, code, URLs, and symbols when translating would harm fidelity. "
        "Do not summarize. Keep one output item per input item."
    )
    user_prompt = (
        f"Paper title: {paper.get('title', '')}\n"
        f"Known Chinese title: {paper.get('titleZh', '')}\n"
        f"Page: {page_number}\n"
        + ("Read the rendered page image first, then correct and translate each OCR block.\n" if supports_vision else "")
        + "Translate the following blocks and return JSON only. The output must be json:\n"
        + json.dumps(source_blocks, ensure_ascii=False)
    )
    pdf_path = ROOT / paper["pdfPath"] if paper.get("pdfPath") else None
    images = [load_page_image_input(paper["id"], pdf_path, page_number)] if (supports_vision and pdf_path and pdf_path.exists()) else []
    payload = None
    for attempt in range(4):
        try:
            payload = call_ai_json(system_prompt, user_prompt, schema, images=images, timeout=90)
            break
        except RuntimeError as exc:
            if is_rate_limit_error(str(exc)):
                if attempt < 3:
                    time.sleep(2 + attempt * 3)
                    continue
                raise RuntimeError("AI translation hit a rate limit. Please retry in a moment.") from exc
            raise
    if payload is None:
        raise RuntimeError("AI translation is temporarily unavailable. Please retry shortly.")
    return payload

def normalize_page_translation_response(translated) -> list[dict]:
    if isinstance(translated, list):
        candidates = translated
    elif isinstance(translated, dict):
        for key in ("blocks", "items", "translations", "results"):
            value = translated.get(key)
            if isinstance(value, list):
                candidates = value
                break
        else:
            candidates = []
    else:
        candidates = []

    normalized: list[dict] = []
    for item in candidates:
        if isinstance(item, dict):
            text = item.get("text_zh")
            if text is None:
                text = item.get("translation")
            if text is None:
                text = item.get("text")
            normalized.append(
                {
                    "index": normalize_number(item.get("index"), -1),
                    "text_zh": normalize_whitespace(str(text or "")),
                }
            )
        elif isinstance(item, str):
            normalized.append({"index": len(normalized), "text_zh": normalize_whitespace(item)})
    return [item for item in normalized if item["index"] >= 0]


def is_rate_limit_error(detail: str) -> bool:
    lowered = (detail or "").lower()
    return "rate limit" in lowered or '"1302"' in lowered or "请求频率" in lowered


def call_ai_paper_digest(paper: dict, candidates: dict) -> dict:
    schema = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "abstract": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "original": {"type": "string"},
                    "zh": {"type": "string"},
                },
                "required": ["original", "zh"],
            },
            "method": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "original": {"type": "string"},
                    "zh": {"type": "string"},
                },
                "required": ["original", "zh"],
            },
            "conclusion": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "original": {"type": "string"},
                    "zh": {"type": "string"},
                },
                "required": ["original", "zh"],
            },
            "takeaways_zh": {
                "type": "array",
                "items": {"type": "string"},
                "maxItems": 6,
            },
        },
        "required": ["abstract", "method", "conclusion", "takeaways_zh"],
    }
    system_prompt = (
        "You extract the most useful reading digest for an academic paper. "
        "Focus on the strongest Abstract, Method, and Conclusion content. "
        "Keep the original snippets concise and faithful, then produce polished Simplified Chinese translations. "
        "All zh fields and takeaways_zh must read naturally in Simplified Chinese. "
        "Method should emphasize the core pipeline, model, or innovation rather than implementation noise."
    )
    user_prompt = (
        f"Title: {paper.get('title', '')}\n"
        f"Chinese title: {paper.get('titleZh', '')}\n"
        f"Authors: {', '.join(paper.get('authors', []))}\n"
        f"Venue: {paper.get('venue', '')}\n"
        "Candidates below must be summarized into json:\n"
        f"{json.dumps(candidates, ensure_ascii=False)}"
    )
    return call_ai_json(system_prompt, user_prompt, schema, timeout=90)

def normalize_paper_digest_response(candidates: dict, digest) -> dict:
    if not isinstance(digest, dict):
        digest = {}

    def normalize_section(name: str) -> dict:
        section = digest.get(name)
        if isinstance(section, str):
            original = normalize_multiline_text(str(candidates.get(name) or ""), limit=2200)
            zh = normalize_multiline_text(section, limit=2200)
            return {"original": original, "zh": zh}
        if not isinstance(section, dict):
            section = {}
        original = normalize_multiline_text(str(section.get("original") or candidates.get(name) or ""), limit=2200)
        zh = normalize_multiline_text(str(section.get("zh") or section.get("summary") or ""), limit=2200)
        return {"original": original, "zh": zh}

    takeaways = digest.get("takeaways_zh")
    if not isinstance(takeaways, list):
        takeaways = []

    if not takeaways:
        takeaways = [
            digest.get("abstract") if isinstance(digest.get("abstract"), str) else "",
            digest.get("method") if isinstance(digest.get("method"), str) else "",
            digest.get("conclusion") if isinstance(digest.get("conclusion"), str) else "",
        ]

    return {
        "abstract": normalize_section("abstract"),
        "method": normalize_section("method"),
        "conclusion": normalize_section("conclusion"),
        "takeawaysZh": [normalize_whitespace(str(item)) for item in takeaways if normalize_whitespace(str(item))][:3],
    }


def enrich_paper_with_ai(paper_id: str) -> dict:
    current = get_paper(paper_id)
    if not current:
        raise FileNotFoundError("paper not found")

    enrichment = normalize_ai_enrichment_response(current, call_ai_enrichment(current))
    tags = parse_string_list(enrichment.get("tags"))
    keywords = parse_string_list(enrichment.get("keywords"))
    merged_tags = list(dict.fromkeys(tags + current.get("tags", [])))[:8]

    patch = {
        "title": normalize_whitespace(enrichment.get("title") or current["title"]),
        "titleZh": normalize_whitespace(enrichment.get("title_zh") or ""),
        "abstract": current.get("abstract") or normalize_whitespace(enrichment.get("summary") or ""),
        "aiSummary": normalize_whitespace(enrichment.get("summary") or ""),
        "aiSummaryZh": normalize_whitespace(enrichment.get("summary_zh") or ""),
        "tags": merged_tags,
        "aiKeywords": keywords or merged_tags[:4],
        "category": enrichment.get("category") or current.get("category") or "Other",
        "collection": enrichment.get("collection") or current.get("collection") or enrichment.get("category") or "",
        "priority": enrichment.get("reading_priority") or current.get("priority") or "medium",
        "venue": current.get("venue") or normalize_whitespace(enrichment.get("venue_guess") or ""),
        "year": current.get("year") or normalize_number(enrichment.get("year_guess"), 0),
        "aiModel": current_ai_model(),
        "aiEnrichedAt": now_iso(),
        "aiConfidence": max(0.0, min(1.0, normalize_float(enrichment.get("confidence"), 0.0))),
        "updatedAt": now_iso(),
    }
    updated = update_paper(paper_id, patch)
    if not updated:
        raise FileNotFoundError("paper not found")
    return updated


def get_reader_document(paper_id: str) -> dict:
    paper = get_paper(paper_id)
    if not paper:
        raise FileNotFoundError("paper not found")
    if not paper.get("pdfPath"):
        raise ValueError("paper does not have a local PDF")

    pdf_path = ROOT / paper["pdfPath"]
    if not pdf_path.exists():
        raise FileNotFoundError("pdf file missing")

    pages = render_pdf_pages(paper_id, pdf_path)
    total_pages = len(pages)
    if total_pages and paper["readerTotalPages"] != total_pages:
        paper = update_paper(
            paper_id,
            {
                "readerTotalPages": total_pages,
                "readerPage": min(max(1, paper.get("readerPage", 1)), total_pages),
                "updatedAt": now_iso(),
            },
        ) or paper

    return {
        "paperId": paper_id,
        "title": paper["title"],
        "titleZh": paper.get("titleZh", ""),
        "pdfUrl": paper["pdfUrl"],
        "currentPage": paper.get("readerPage", 1),
        "totalPages": total_pages,
        "lastReadAt": paper.get("lastReadAt", ""),
        "pages": pages,
    }


def get_reader_translation(paper_id: str, page_number: int) -> dict:
    paper = get_paper(paper_id)
    if not paper:
        raise FileNotFoundError("paper not found")
    if not paper.get("pdfPath"):
        raise ValueError("paper does not have a local PDF")

    pdf_path = ROOT / paper["pdfPath"]
    if not pdf_path.exists():
        raise FileNotFoundError("pdf file missing")

    current_provider = current_ai_provider()
    current_model = current_ai_model()
    current_mode = "vision" if provider_supports_vision() else "text"
    page_key = str(page_number)
    with translation_cache_lock(paper_id):
        cache = current_translation_cache(paper_id)
        cached_page = cache.get("pages", {}).get(page_key)
        if isinstance(cached_page, dict):
            return cached_page

    page_layout = extract_page_text_blocks(pdf_path, page_number)
    if not page_layout["blocks"]:
        payload = {
            "paperId": paper_id,
            "page": page_number,
            "width": page_layout["width"],
            "height": page_layout["height"],
            "blocks": [],
            "translatedAt": now_iso(),
            "aiModel": current_model if ai_enabled() else "",
            "aiProvider": current_provider if ai_enabled() else "",
            "translationMode": current_mode if ai_enabled() else "",
        }
        with translation_cache_lock(paper_id):
            cache = current_translation_cache(paper_id)
            cache.setdefault("pages", {})[page_key] = payload
            cache["updatedAt"] = now_iso()
            save_translation_cache(paper_id, cache)
        return payload

    if not ai_enabled():
        raise RuntimeError("AI 未配置，暂时无法生成中文阅读页")

    translated = normalize_page_translation_response(call_ai_page_translation(paper, page_number, page_layout["blocks"]))
    translated_lookup = {
        normalize_number(item.get("index"), -1): normalize_whitespace(str(item.get("text_zh") or ""))
        for item in translated
        if isinstance(item, dict)
    }

    blocks = []
    for block in page_layout["blocks"]:
        translated_text = translated_lookup.get(block["index"]) or (block["text"] if contains_cjk(block["text"]) else "")
        blocks.append(
            {
                "x": block["x"],
                "y": block["y"],
                "width": block["width"],
                "height": block["height"],
                "fontSize": block["fontSize"],
                "text": translated_text,
            }
        )

    payload = {
        "paperId": paper_id,
        "page": page_number,
        "width": page_layout["width"],
        "height": page_layout["height"],
        "blocks": blocks,
        "translatedAt": now_iso(),
        "aiModel": current_model,
        "aiProvider": current_provider,
        "translationMode": current_mode,
    }
    with translation_cache_lock(paper_id):
        cache = current_translation_cache(paper_id)
        existing_page = cache.get("pages", {}).get(page_key)
        if isinstance(existing_page, dict):
            return existing_page
        cache.setdefault("pages", {})[page_key] = payload
        cache["aiModel"] = current_model
        cache["aiProvider"] = current_provider
        cache["translationMode"] = current_mode
        cache["updatedAt"] = now_iso()
        save_translation_cache(paper_id, cache)
    return payload


def preload_reader_translation(paper_id: str) -> dict:
    reader = get_reader_document(paper_id)
    translated_pages = 0
    partial = False
    message = ""
    for page in reader.get("pages", []):
        try:
            get_reader_translation(paper_id, normalize_number(page.get("page"), 0))
            translated_pages += 1
            time.sleep(0.8)
        except RuntimeError as exc:
            if "频率限制" in str(exc):
                partial = True
                message = str(exc)
                break
            raise
    return {
        "paperId": paper_id,
        "translatedPages": translated_pages,
        "totalPages": len(reader.get("pages", [])),
        "partial": partial,
        "message": message,
        "aiModel": current_ai_model() if ai_enabled() else "",
        "updatedAt": now_iso(),
    }


def get_cached_reader_translations(paper_id: str) -> dict:
    paper = get_paper(paper_id)
    if not paper:
        raise FileNotFoundError("paper not found")

    with translation_cache_lock(paper_id):
        cache = current_translation_cache(paper_id)
    pages = []
    for key, value in sorted(cache.get("pages", {}).items(), key=lambda item: normalize_number(item[0], 0)):
        if isinstance(value, dict):
            pages.append(value)

    return {
        "paperId": paper_id,
        "aiProvider": cache.get("aiProvider", ""),
        "aiModel": cache.get("aiModel", ""),
        "translationMode": cache.get("translationMode", ""),
        "updatedAt": cache.get("updatedAt", ""),
        "pages": pages,
    }


def translation_job_snapshot(job: dict) -> dict:
    return {
        "jobId": job["jobId"],
        "paperId": job["paperId"],
        "status": job["status"],
        "totalPages": job["totalPages"],
        "completedPages": job["completedPages"],
        "failedPages": list(job["failedPages"]),
        "runningPages": list(job["runningPages"]),
        "pageStatus": dict(job["pageStatus"]),
        "message": job.get("message", ""),
        "startedAt": job["startedAt"],
        "updatedAt": job["updatedAt"],
        "finishedAt": job.get("finishedAt", ""),
        "aiProvider": job.get("aiProvider", ""),
        "aiModel": job.get("aiModel", ""),
        "translationMode": job.get("translationMode", ""),
    }


def get_translation_job_status(paper_id: str) -> dict:
    with TRANSLATION_JOBS_LOCK:
        job = TRANSLATION_JOBS.get(paper_id)
        if job:
            return translation_job_snapshot(job)

    reader = get_reader_document(paper_id)
    cache = get_cached_reader_translations(paper_id)
    completed_pages = {normalize_number(item.get("page"), 0) for item in cache.get("pages", []) if isinstance(item, dict)}
    total_pages = len(reader.get("pages", []))
    page_status = {str(page["page"]): ("completed" if page["page"] in completed_pages else "pending") for page in reader.get("pages", [])}
    status = "completed" if total_pages and len(completed_pages) >= total_pages else "idle"
    return {
        "jobId": "",
        "paperId": paper_id,
        "status": status,
        "totalPages": total_pages,
        "completedPages": len(completed_pages),
        "failedPages": [],
        "runningPages": [],
        "pageStatus": page_status,
        "message": "",
        "startedAt": "",
        "updatedAt": now_iso(),
        "finishedAt": now_iso() if status == "completed" else "",
        "aiProvider": current_ai_provider() if ai_enabled() else "",
        "aiModel": current_ai_model() if ai_enabled() else "",
        "translationMode": "vision" if provider_supports_vision() else "text",
    }


def update_translation_job(paper_id: str, updater) -> dict | None:
    with TRANSLATION_JOBS_LOCK:
        job = TRANSLATION_JOBS.get(paper_id)
        if not job:
            return None
        updater(job)
        job["updatedAt"] = now_iso()
        return translation_job_snapshot(job)


def run_translation_job(paper_id: str, page_numbers: list[int]) -> None:
    def mark_running(job: dict, page_number: int) -> None:
        job["pageStatus"][str(page_number)] = "running"
        if page_number not in job["runningPages"]:
            job["runningPages"].append(page_number)

    def mark_done(job: dict, page_number: int) -> None:
        job["pageStatus"][str(page_number)] = "completed"
        job["completedPages"] = min(job["totalPages"], job["completedPages"] + 1)
        job["failedPages"] = [page for page in job["failedPages"] if page != page_number]
        job["runningPages"] = [page for page in job["runningPages"] if page != page_number]

    def mark_failed(job: dict, page_number: int, message: str) -> None:
        job["pageStatus"][str(page_number)] = "failed"
        if page_number not in job["failedPages"]:
            job["failedPages"].append(page_number)
        job["runningPages"] = [page for page in job["runningPages"] if page != page_number]
        if not job.get("message"):
            job["message"] = message

    with concurrent.futures.ThreadPoolExecutor(max_workers=BULK_TRANSLATION_MAX_WORKERS) as executor:
        future_map = {}
        for page_number in page_numbers:
            update_translation_job(paper_id, lambda job, page_number=page_number: mark_running(job, page_number))
            future = executor.submit(get_reader_translation, paper_id, page_number)
            future_map[future] = page_number

        for future in concurrent.futures.as_completed(future_map):
            page_number = future_map[future]
            try:
                future.result()
                update_translation_job(paper_id, lambda job, page_number=page_number: mark_done(job, page_number))
            except Exception as exc:
                update_translation_job(
                    paper_id,
                    lambda job, page_number=page_number, message=str(exc): mark_failed(job, page_number, message),
                )

    def finalize(job: dict) -> None:
        has_failures = bool(job["failedPages"])
        job["status"] = "completed_with_errors" if has_failures else "completed"
        job["finishedAt"] = now_iso()
        if not has_failures:
            job["message"] = ""

    update_translation_job(paper_id, finalize)


def start_translation_job(paper_id: str) -> dict:
    reader = get_reader_document(paper_id)
    if not ai_enabled():
        raise RuntimeError("AI 未配置，暂时无法执行全文翻译")

    with TRANSLATION_JOBS_LOCK:
        existing = TRANSLATION_JOBS.get(paper_id)
        if existing and existing["status"] not in TERMINAL_JOB_STATUSES:
            return translation_job_snapshot(existing)

    cache = get_cached_reader_translations(paper_id)
    cached_pages = {normalize_number(item.get("page"), 0) for item in cache.get("pages", []) if isinstance(item, dict)}
    total_pages = len(reader.get("pages", []))
    page_numbers = [normalize_number(page.get("page"), 0) for page in reader.get("pages", []) if normalize_number(page.get("page"), 0) >= 1]
    pending_pages = [page for page in page_numbers if page not in cached_pages]
    page_status = {str(page): ("completed" if page in cached_pages else "pending") for page in page_numbers}

    job = {
        "jobId": str(uuid.uuid4()),
        "paperId": paper_id,
        "status": "running",
        "totalPages": total_pages,
        "completedPages": len(cached_pages),
        "failedPages": [],
        "runningPages": [],
        "pageStatus": page_status,
        "message": "",
        "startedAt": now_iso(),
        "updatedAt": now_iso(),
        "finishedAt": "",
        "aiProvider": current_ai_provider(),
        "aiModel": current_ai_model(),
        "translationMode": "vision" if provider_supports_vision() else "text",
    }
    if not pending_pages:
        job["status"] = "completed"
        job["finishedAt"] = now_iso()
        with TRANSLATION_JOBS_LOCK:
            TRANSLATION_JOBS[paper_id] = job
        return translation_job_snapshot(job)

    with TRANSLATION_JOBS_LOCK:
        TRANSLATION_JOBS[paper_id] = job

    worker = threading.Thread(target=run_translation_job, args=(paper_id, pending_pages), daemon=True)
    worker.start()
    return translation_job_snapshot(job)


def build_local_paper_digest(paper: dict, candidates: dict) -> dict:
    return {
        "paperId": paper["id"],
        "title": paper["title"],
        "titleZh": paper.get("titleZh", ""),
        "abstract": {
            "original": candidates.get("abstract", ""),
            "zh": paper.get("aiSummaryZh", "") or "",
        },
        "method": {
            "original": candidates.get("method", ""),
            "zh": "",
        },
        "conclusion": {
            "original": candidates.get("conclusion", ""),
            "zh": "",
        },
        "takeawaysZh": [paper.get("aiSummaryZh") or paper.get("aiSummary") or ""] if (paper.get("aiSummaryZh") or paper.get("aiSummary")) else [],
        "source": "local",
        "updatedAt": now_iso(),
        "aiModel": "",
    }


def get_paper_digest(paper_id: str, refresh: bool = False) -> dict:
    paper = get_paper(paper_id)
    if not paper:
        raise FileNotFoundError("paper not found")

    if not refresh:
        cached = load_digest_cache(paper_id)
        if cached:
            return cached

    candidates = extract_digest_candidates(paper)
    payload = build_local_paper_digest(paper, candidates)

    if ai_enabled():
        digest = normalize_paper_digest_response(candidates, call_ai_paper_digest(paper, candidates))
        payload = {
            "paperId": paper_id,
            "title": paper["title"],
            "titleZh": paper.get("titleZh", ""),
            "abstract": digest["abstract"],
            "method": digest["method"],
            "conclusion": digest["conclusion"],
            "takeawaysZh": digest["takeawaysZh"],
            "source": "ai",
            "updatedAt": now_iso(),
            "aiModel": current_ai_model(),
        }

    save_digest_cache(paper_id, payload)
    return payload


def import_pdf(file_item) -> dict:
    original_name = safe_filename(file_item.filename or "paper.pdf")
    paper_id = str(uuid.uuid4())
    target_name = f"{paper_id}_{original_name}"
    target_path = PDF_DIR / target_name

    with target_path.open("wb") as handle:
        shutil.copyfileobj(file_item.file, handle)

    extracted = extract_pdf_profile(paper_id, target_path, original_name)
    payload = normalize_paper_payload(
        {
            "id": paper_id,
            "status": "to-read",
            "priority": "medium",
            "venue": "本地 PDF",
            "pdfPath": str(target_path.relative_to(ROOT)),
            "originalFilename": original_name,
            **extracted,
        }
    )
    with connect_db() as conn:
        insert_paper(conn, payload)

    if ai_enabled():
        try:
            return enrich_paper_with_ai(paper_id)
        except Exception:
            return get_paper(paper_id)
    return get_paper(paper_id)


def app_config() -> dict:
    settings = active_provider_settings()
    return {
        "openaiEnabled": ai_enabled(),
        "aiEnabled": ai_enabled(),
        "openaiModel": current_ai_model(),
        "aiModel": current_ai_model(),
        "aiProvider": current_ai_provider(),
        "aiProviderLabel": settings.get("label", current_ai_provider()),
        "supportsVisionTranslation": provider_supports_vision(),
        "providerPresets": public_provider_presets(),
        "categories": CATEGORY_CHOICES,
    }


class PaperHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        parsed = urlparse(path)
        clean = unquote(parsed.path)
        if clean.startswith("/storage/"):
            return str((ROOT / clean.lstrip("/")).resolve())
        if clean in {"/", ""}:
            return str((ROOT / "index.html").resolve())
        candidate = (ROOT / clean.lstrip("/")).resolve()
        if str(candidate).startswith(str(ROOT.resolve())) and candidate.exists():
            return str(candidate)
        return str((ROOT / "index.html").resolve())

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def guess_type(self, path: str) -> str:
        suffix = Path(path).suffix.lower()
        if suffix in {".js", ".mjs"}:
            return "application/javascript"
        if suffix == ".css":
            return "text/css"
        return super().guess_type(path)

    def end_json(self, payload, status=HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def end_api_error(self, status: HTTPStatus, message: str) -> None:
        self.end_json({"error": str(message)}, status)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        return json.loads(raw.decode("utf-8"))

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        reader_match = re.fullmatch(r"/api/papers/([^/]+)/reader", parsed.path)
        translation_match = re.fullmatch(r"/api/papers/([^/]+)/reader-translation", parsed.path)
        translations_match = re.fullmatch(r"/api/papers/([^/]+)/reader-translations", parsed.path)
        translation_job_match = re.fullmatch(r"/api/papers/([^/]+)/reader-translation-job", parsed.path)
        digest_match = re.fullmatch(r"/api/papers/([^/]+)/digest", parsed.path)
        if parsed.path == "/api/config":
            self.end_json(app_config())
            return
        if parsed.path == "/api/provider-config":
            self.end_json(provider_config_for_client())
            return
        if parsed.path == "/api/papers":
            self.end_json(list_papers())
            return
        if reader_match:
            paper_id = reader_match.group(1)
            try:
                self.end_json(get_reader_document(paper_id))
            except FileNotFoundError as exc:
                self.end_api_error(HTTPStatus.NOT_FOUND, str(exc))
            except ValueError as exc:
                self.end_api_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        if translation_match:
            paper_id = translation_match.group(1)
            page = normalize_number(parse_qs(parsed.query).get("page", ["0"])[0], 0)
            if page < 1:
                self.end_api_error(HTTPStatus.BAD_REQUEST, "missing page")
                return
            try:
                self.end_json(get_reader_translation(paper_id, page))
            except FileNotFoundError as exc:
                self.end_api_error(HTTPStatus.NOT_FOUND, str(exc))
            except ValueError as exc:
                self.end_api_error(HTTPStatus.BAD_REQUEST, str(exc))
            except RuntimeError as exc:
                self.end_api_error(HTTPStatus.BAD_GATEWAY, str(exc))
            return
        if translations_match:
            paper_id = translations_match.group(1)
            try:
                self.end_json(get_cached_reader_translations(paper_id))
            except FileNotFoundError as exc:
                self.end_api_error(HTTPStatus.NOT_FOUND, str(exc))
            return
        if translation_job_match:
            paper_id = translation_job_match.group(1)
            try:
                self.end_json(get_translation_job_status(paper_id))
            except FileNotFoundError as exc:
                self.end_api_error(HTTPStatus.NOT_FOUND, str(exc))
            except ValueError as exc:
                self.end_api_error(HTTPStatus.BAD_REQUEST, str(exc))
            return
        if digest_match:
            paper_id = digest_match.group(1)
            refresh = parse_qs(parsed.query).get("refresh", ["0"])[0] == "1"
            try:
                self.end_json(get_paper_digest(paper_id, refresh=refresh))
            except FileNotFoundError as exc:
                self.end_api_error(HTTPStatus.NOT_FOUND, str(exc))
            except RuntimeError as exc:
                self.end_api_error(HTTPStatus.BAD_GATEWAY, str(exc))
            return
        if parsed.path.startswith("/api/"):
            self.end_api_error(HTTPStatus.NOT_FOUND, "api route not found")
            return
        super().do_GET()

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        enrich_match = re.fullmatch(r"/api/papers/([^/]+)/ai-enrich", parsed.path)
        preload_translation_match = re.fullmatch(r"/api/papers/([^/]+)/reader-translation/preload", parsed.path)
        translation_job_match = re.fullmatch(r"/api/papers/([^/]+)/reader-translation-job", parsed.path)
        digest_match = re.fullmatch(r"/api/papers/([^/]+)/digest", parsed.path)
        if parsed.path == "/api/papers":
            payload = normalize_paper_payload(self.read_json())
            with connect_db() as conn:
                insert_paper(conn, payload)
            self.end_json(get_paper(payload["id"]), HTTPStatus.CREATED)
            return

        if parsed.path == "/api/papers/import-pdf":
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={"REQUEST_METHOD": "POST", "CONTENT_TYPE": self.headers.get("Content-Type", "")},
            )
            file_item = form["file"] if "file" in form else None
            if file_item is None or not getattr(file_item, "filename", ""):
                self.end_api_error(HTTPStatus.BAD_REQUEST, "missing file")
                return
            self.end_json(import_pdf(file_item), HTTPStatus.CREATED)
            return

        if enrich_match:
            paper_id = enrich_match.group(1)
            try:
                self.end_json(enrich_paper_with_ai(paper_id))
            except FileNotFoundError as exc:
                self.end_api_error(HTTPStatus.NOT_FOUND, str(exc))
            except RuntimeError as exc:
                self.end_api_error(HTTPStatus.BAD_GATEWAY, str(exc))
            except Exception as exc:
                self.end_api_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return

        if preload_translation_match:
            paper_id = preload_translation_match.group(1)
            try:
                self.end_json(preload_reader_translation(paper_id))
            except FileNotFoundError as exc:
                self.end_api_error(HTTPStatus.NOT_FOUND, str(exc))
            except ValueError as exc:
                self.end_api_error(HTTPStatus.BAD_REQUEST, str(exc))
            except RuntimeError as exc:
                self.end_api_error(HTTPStatus.BAD_GATEWAY, str(exc))
            return

        if translation_job_match:
            paper_id = translation_job_match.group(1)
            try:
                self.end_json(start_translation_job(paper_id))
            except FileNotFoundError as exc:
                self.end_api_error(HTTPStatus.NOT_FOUND, str(exc))
            except ValueError as exc:
                self.end_api_error(HTTPStatus.BAD_REQUEST, str(exc))
            except RuntimeError as exc:
                self.end_api_error(HTTPStatus.BAD_GATEWAY, str(exc))
            return

        if digest_match:
            paper_id = digest_match.group(1)
            try:
                self.end_json(get_paper_digest(paper_id, refresh=True))
            except FileNotFoundError as exc:
                self.end_api_error(HTTPStatus.NOT_FOUND, str(exc))
            except RuntimeError as exc:
                self.end_api_error(HTTPStatus.BAD_GATEWAY, str(exc))
            return

        if parsed.path == "/api/reset":
            reset_db()
            self.end_json({"ok": True})
            return

        self.send_error(HTTPStatus.NOT_FOUND)

    def do_PUT(self) -> None:
        parsed = urlparse(self.path)
        reader_state_match = re.fullmatch(r"/api/papers/([^/]+)/reader-state", parsed.path)
        paper_match = re.fullmatch(r"/api/papers/([^/]+)", parsed.path)
        if parsed.path == "/api/provider-config":
            payload = self.read_json()
            try:
                selected_provider = normalize_provider_id(str(payload.get("selectedProvider") or "openai"))
                provider_payload = payload.get("provider") if isinstance(payload.get("provider"), dict) else {}
                saved = save_provider_config(
                    {
                        "selectedProvider": selected_provider,
                        "providers": {
                            selected_provider: {
                                "model": provider_payload.get("model", ""),
                                "apiUrl": provider_payload.get("apiUrl", ""),
                                "apiKey": provider_payload.get("apiKey", ""),
                                "clearApiKey": provider_payload.get("clearApiKey", False),
                            }
                        },
                    }
                )
                self.end_json(
                    {
                        "ok": True,
                        "selectedProvider": saved["selectedProvider"],
                        "config": provider_config_for_client(),
                        "appConfig": app_config(),
                    }
                )
            except OSError as exc:
                self.end_api_error(HTTPStatus.INTERNAL_SERVER_ERROR, str(exc))
            return
        if reader_state_match:
            paper_id = reader_state_match.group(1)
            patch = self.read_json()
            patch["lastReadAt"] = now_iso()
            patch["updatedAt"] = now_iso()
            updated = update_paper(paper_id, patch)
            if not updated:
                self.end_api_error(HTTPStatus.NOT_FOUND, "paper not found")
                return
            self.end_json(updated)
            return

        if paper_match:
            paper_id = paper_match.group(1)
            updated = update_paper(paper_id, self.read_json())
            if not updated:
                self.end_api_error(HTTPStatus.NOT_FOUND, "paper not found")
                return
            self.end_json(updated)
            return

        self.end_api_error(HTTPStatus.NOT_FOUND, "api route not found")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        paper_match = re.fullmatch(r"/api/papers/([^/]+)", parsed.path)
        if paper_match:
            paper_id = paper_match.group(1)
            if not delete_paper(paper_id):
                self.end_api_error(HTTPStatus.NOT_FOUND, "paper not found")
                return
            self.send_response(HTTPStatus.NO_CONTENT)
            self.end_headers()
            return
        self.end_api_error(HTTPStatus.NOT_FOUND, "api route not found")

    def log_message(self, format: str, *args) -> None:
        return


def run_server(port: int = 8876) -> None:
    init_db()
    server = ThreadingHTTPServer(("127.0.0.1", port), PaperHandler)
    print(f"Paper Hub running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    if "--check" in sys.argv:
        init_db()
        print("ok")
        raise SystemExit(0)
    run_server()

