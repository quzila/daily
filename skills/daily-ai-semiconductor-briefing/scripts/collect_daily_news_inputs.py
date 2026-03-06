#!/usr/bin/env python3
"""日次ニュース作成のための候補収集・選定・本文取得を行う。"""

from __future__ import annotations

import argparse
import concurrent.futures
import dataclasses
import datetime as dt
import email.utils
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_OUTPUT_ROOT = Path("reports") / "daily-news"


UA = "daily-news-bot/1.0 (+https://github.com)"

AI_KEYWORDS = [
    "ai",
    "llm",
    "gpt",
    "chatgpt",
    "claude",
    "gemini",
    "copilot",
    "cursor",
    "codex",
    "agent",
    "prompt",
    "生成ai",
]

SEMI_KEYWORDS = [
    "semiconductor",
    "chip",
    "chips",
    "gpu",
    "cpu",
    "nvidia",
    "tsmc",
    "samsung",
    "intel",
    "renesas",
    "hbm",
    "dram",
    "nand",
    "fab",
    "半導体",
    "メモリ",
    "決算",
]

REDDIT_SUBS_AI = ["LocalLLaMA", "MachineLearning", "ClaudeAI", "OpenAI"]
REDDIT_SUBS_SEMI = ["hardware", "semiconductors", "nvidia", "AMD_Stock"]

AI_NOISE_TERMS = [
    "cancel chatgpt",
    "deleted my chatgpt",
    "department of war",
    "boycott",
    "drama",
]

ZENN_API_ENDPOINTS = (
    "https://zenn.dev/api/articles?order=trend",
    "https://zenn.dev/api/articles?order=latest",
)

NOTE_QUERIES_AI = (
    "生成AI",
    "Claude Code",
    "Codex",
    "Cursor",
    "LLM",
    "ChatGPT",
    "Gemini",
)

NOTE_QUERIES_SEMI = (
    "半導体",
    "NVIDIA",
    "AMD",
    "HBM",
    "GPU",
    "TSMC",
)


@dataclasses.dataclass
class Candidate:
    domain: str
    source: str
    title: str
    url: str
    published_at: str
    snippet: str
    score: float = 0.0
    meta: dict[str, object] = dataclasses.field(default_factory=dict)


def fetch_bytes(url: str, timeout: int = 20) -> bytes:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "application/json, text/html, application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def fetch_json(url: str) -> dict:
    return json.loads(fetch_bytes(url).decode("utf-8"))


def fetch_text(url: str) -> str:
    raw = fetch_bytes(url)
    return raw.decode("utf-8", errors="ignore")


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def parse_rfc2822(value: str) -> str:
    try:
        dt_obj = email.utils.parsedate_to_datetime(value)
    except Exception:
        return ""
    if dt_obj is None:
        return ""
    return dt_obj.date().isoformat()


def parse_iso_date(value: str) -> str:
    if not value:
        return ""
    value = value.replace("Z", "+00:00")
    try:
        return dt.datetime.fromisoformat(value).date().isoformat()
    except Exception:
        return value[:10]


def parse_note_published_at(page_html: str) -> str:
    patterns = (
        r'"datePublished"\s*:\s*"([^"]+)"',
        r'<time[^>]+datetime=["\']([^"\']+)["\']',
        r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']',
    )
    for pat in patterns:
        m = re.search(pat, page_html, re.IGNORECASE)
        if m:
            return parse_iso_date(m.group(1))
    return ""


def keyword_score(text: str, domain: str) -> int:
    words = AI_KEYWORDS if domain == "ai" else SEMI_KEYWORDS
    low = text.lower()
    return sum(1 for w in words if w in low)


def freshness_score(published_date: str, target_date: str) -> float:
    if not published_date:
        return 0.0
    try:
        p = dt.date.fromisoformat(published_date)
        t = dt.date.fromisoformat(target_date)
    except ValueError:
        return 0.0
    delta = abs((t - p).days)
    if delta <= 2:
        return 2.0
    if delta <= 7:
        return 1.0
    return 0.0


def score_candidate(c: Candidate, target_date: str) -> float:
    text = f"{c.title} {c.snippet}"
    base = keyword_score(text, c.domain) * 2.0
    fresh = freshness_score(c.published_at, target_date)
    signal = 0.0
    ups = c.meta.get("ups")
    if isinstance(ups, (int, float)):
        signal += min(3.0, float(ups) / 500.0)
    likes = c.meta.get("liked_count")
    if isinstance(likes, (int, float)):
        signal += min(2.0, float(likes) / 50.0)
    penalty = 0.0
    low = text.lower()
    if c.domain == "ai" and any(t in low for t in AI_NOISE_TERMS):
        penalty += 4.0
    return base + fresh + signal - penalty


def extract_og_title(html_text: str) -> str:
    m = re.search(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        html_text,
        re.IGNORECASE,
    )
    if m:
        return html.unescape(m.group(1)).strip()
    m = re.search(r"<title>(.*?)</title>", html_text, re.IGNORECASE | re.DOTALL)
    return normalize_space(html.unescape(m.group(1))) if m else ""


def html_to_text(html_text: str, max_chars: int = 7000) -> str:
    cleaned = re.sub(r"<script\b[^>]*>.*?</script>", " ", html_text, flags=re.DOTALL | re.IGNORECASE)
    cleaned = re.sub(r"<style\b[^>]*>.*?</style>", " ", cleaned, flags=re.DOTALL | re.IGNORECASE)
    blocks = re.findall(r"<(?:article|main)\b[^>]*>(.*?)</(?:article|main)>", cleaned, flags=re.DOTALL | re.IGNORECASE)
    target = max(blocks, key=len) if blocks else cleaned
    target = re.sub(r"<[^>]+>", " ", target)
    target = normalize_space(html.unescape(target))
    return target[:max_chars]


def fetch_zenn_candidates(domain: str, limit: int) -> list[Candidate]:
    out: list[Candidate] = []
    seen_urls: set[str] = set()
    for url in ZENN_API_ENDPOINTS:
        try:
            data = fetch_json(url)
        except Exception:
            continue
        for a in data.get("articles", [])[: limit * 3]:
            path = a.get("path") or ""
            if not path:
                continue
            full_url = urllib.parse.urljoin("https://zenn.dev", path)
            if full_url in seen_urls:
                continue
            seen_urls.add(full_url)
            title = normalize_space(a.get("title") or "")
            published = parse_iso_date(a.get("published_at") or "")
            c = Candidate(
                domain=domain,
                source="zenn",
                title=title,
                url=full_url,
                published_at=published,
                snippet=normalize_space(a.get("body_updated_at") or ""),
                meta={"liked_count": a.get("liked_count", 0)},
            )
            out.append(c)
    return out[:limit]


def fetch_note_candidates(domain: str, limit: int) -> list[Candidate]:
    queries = NOTE_QUERIES_AI if domain == "ai" else NOTE_QUERIES_SEMI
    rels: list[str] = []
    seen_rels: set[str] = set()
    for query in queries:
        url = f"https://note.com/search?q={urllib.parse.quote(query)}&sort=new"
        try:
            html_text = fetch_text(url)
        except Exception:
            continue
        for rel in re.findall(r"/[a-zA-Z0-9_]+/n/[a-zA-Z0-9]+", html_text):
            if rel in seen_rels:
                continue
            seen_rels.add(rel)
            rels.append(rel)
            if len(rels) >= limit * 4:
                break
        if len(rels) >= limit * 4:
            break

    uniq: list[str] = []
    for r in rels:
        if r not in uniq:
            uniq.append(r)
        if len(uniq) >= limit * 2:
            break

    def _fetch_note_page(rel: str) -> Candidate | None:
        page_url = urllib.parse.urljoin("https://note.com", rel)
        try:
            article_html = fetch_text(page_url)
        except Exception:
            return None
        title = extract_og_title(article_html) or rel
        published = parse_note_published_at(article_html)
        return Candidate(
            domain=domain,
            source="note",
            title=title,
            url=page_url,
            published_at=published,
            snippet="",
        )

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as pool:
        results = list(pool.map(_fetch_note_page, uniq))
    return [r for r in results if r is not None]


def min_keyword_hits(c: Candidate, domain: str) -> int:
    if c.source in {"zenn", "note"}:
        return 1
    if c.source.startswith("reddit:"):
        return 2 if domain == "ai" else 1
    return 2 if domain == "ai" else 1


def pick_with_source_quotas(ranked: list[Candidate], top_n: int, domain: str) -> list[Candidate]:
    if domain != "ai":
        return ranked[:top_n]

    quotas = {"zenn": 2, "note": 1}
    selected: list[Candidate] = []
    used_urls: set[str] = set()

    def source_kind(c: Candidate) -> str:
        if c.source == "zenn":
            return "zenn"
        if c.source == "note":
            return "note"
        return "other"

    for kind, count in quotas.items():
        for c in ranked:
            if len(selected) >= top_n:
                break
            if c.url in used_urls:
                continue
            if source_kind(c) != kind:
                continue
            selected.append(c)
            used_urls.add(c.url)
            if sum(1 for s in selected if source_kind(s) == kind) >= count:
                break

    for c in ranked:
        if len(selected) >= top_n:
            break
        if c.url in used_urls:
            continue
        selected.append(c)
        used_urls.add(c.url)

    return selected[:top_n]


def fetch_reddit_candidates(domain: str, limit: int) -> list[Candidate]:
    subs = REDDIT_SUBS_AI if domain == "ai" else REDDIT_SUBS_SEMI
    per_sub = max(3, limit // max(1, len(subs)))

    def _fetch_sub(sub: str) -> list[Candidate]:
        url = f"https://api.reddit.com/r/{sub}/top?t=day&limit={per_sub}"
        try:
            data = fetch_json(url)
        except Exception:
            return []
        results: list[Candidate] = []
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            title = normalize_space(d.get("title") or "")
            link = d.get("url_overridden_by_dest") or f"https://www.reddit.com{d.get('permalink', '')}"
            published = dt.datetime.fromtimestamp(d.get("created_utc", 0), dt.UTC).date().isoformat()
            snippet = normalize_space((d.get("selftext") or "")[:400])
            results.append(
                Candidate(
                    domain=domain,
                    source=f"reddit:{sub}",
                    title=title,
                    url=link,
                    published_at=published,
                    snippet=snippet,
                    meta={"ups": d.get("ups", 0)},
                )
            )
        return results

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(subs)) as pool:
        batches = list(pool.map(_fetch_sub, subs))
    return [item for batch in batches for item in batch]


def enrich_with_body(c: Candidate) -> dict[str, object]:
    body = ""
    if c.url.startswith("https://www.reddit.com/"):
        body = c.snippet
    else:
        try:
            html_text = fetch_text(c.url)
            body = html_to_text(html_text)
        except Exception:
            body = ""
    return {
        "domain": c.domain,
        "source": c.source,
        "title": c.title,
        "url": c.url,
        "published_at": c.published_at,
        "snippet": c.snippet,
        "score": round(c.score, 3),
        "meta": c.meta,
        "body_text": body,
    }


def collect_domain(domain: str, target_date: str, limit: int, top_n: int) -> tuple[list[dict], list[dict]]:
    candidates: list[Candidate] = []
    candidates.extend(fetch_zenn_candidates(domain, limit))
    candidates.extend(fetch_note_candidates(domain, limit))
    candidates.extend(fetch_reddit_candidates(domain, limit))

    for c in candidates:
        c.score = score_candidate(c, target_date)

    filtered: list[Candidate] = []
    for c in candidates:
        key_hit = keyword_score(f"{c.title} {c.snippet}", domain)
        if key_hit < min_keyword_hits(c, domain):
            continue
        filtered.append(c)

    ranked = sorted(filtered, key=lambda x: x.score, reverse=True)
    selected = pick_with_source_quotas(ranked, top_n, domain)

    all_items = [
        {
            "domain": c.domain,
            "source": c.source,
            "title": c.title,
            "url": c.url,
            "published_at": c.published_at,
            "snippet": c.snippet,
            "score": round(c.score, 3),
            "meta": c.meta,
        }
        for c in ranked
    ]
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max(len(selected), 1), 8)) as pool:
        selected_items = list(pool.map(enrich_with_body, selected))
    return all_items, selected_items


def resolve_target_date(date_arg: str | None, timezone: str) -> str:
    if date_arg:
        dt.datetime.strptime(date_arg, "%Y-%m-%d")
        return date_arg
    return dt.datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d")


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise FileNotFoundError(f"repository root not found from {start}")


def build_context_markdown(target_date: str, selected: list[dict]) -> str:
    lines: list[str] = []
    lines.append(f"# Daily Research Context ({target_date})")
    lines.append("")
    lines.append("## Writing Rule")
    lines.append("- 各記事は必ず `事実(What) / 背景(Why it matters) / 影響(So what)` を含める。")
    lines.append("- 事実には数字・日付・固有名詞を入れる。")
    lines.append("- 影響は、AI記事ではAIコーディング趣味の視点、半導体記事では店頭業務または開発環境調達の視点に接続する。")
    lines.append("")
    lines.append("## Output Contract (3/1 Style)")
    lines.append("- 最終出力の見出し順序は固定すること。")
    lines.append("  1) `## 今日のハイライト（3選）`")
    lines.append("  2) `## AI ニュース` → `### 公式ソース / Zenn ピックアップ / note ピックアップ / Reddit / HN ピックアップ`")
    lines.append("  3) `## 半導体ニュース` → `### 公式ソース / コミュニティ（Reddit / HN / その他）`")
    lines.append("  4) `## その他の候補記事（選外）`")
    lines.append("  5) `## ソース一覧`")
    lines.append("- 記事は `---` で区切り、タイトル行は次の形式を使うこと。")
    lines.append("  - AI公式: `### 【カテゴリA: 公式ソース（AI）】記事タイトル（出典名, 公開日）`")
    lines.append("  - 半導体公式: `### 【カテゴリB: 公式ソース（半導体）】記事タイトル（出典名, 公開日）`")
    lines.append("- 記事ブロックのラベルは次の4つを必須にすること。")
    lines.append("  - `**ひとことサマリー（1文）**`")
    lines.append("  - `**何が起きたか（What）**`")
    lines.append("  - `**なぜ重要か（Why it matters）**`")
    lines.append("  - `**自分への影響（So what）**`")
    lines.append("")
    lines.append("## Few-shot (Good Example)")
    lines.append("- タイトル: Copilot CLI GA")
    lines.append("- 30秒で読める要約: 2026-02-25にGA。CLIで計画実行とMCP連携が正式化し、運用自動化の実装コストが下がった。")
    lines.append("- 記事全体の内容:")
    lines.append("  - 事実(What): GitHub公式がGAを発表。プレビュー(2025-09)からの主要追加はエージェント実行、セッション継続、MCP対応。")
    lines.append("  - 背景(Why it matters): AI開発の主戦場がIDE内補完から、CLIを含む運用全体へ移っている。")
    lines.append("  - 影響(So what): 障害一次対応テンプレをCLI化し、週末の個人開発でデバッグ自動化パイプラインに転用できる。")
    lines.append("- 記事ブロック見出し例:")
    lines.append("  - `### 【カテゴリA: 公式ソース（AI）】Copilot CLI が GA（GitHub Changelog, 2026-02-25）`")
    lines.append("")
    for item in selected:
        lines.append(f"## [{item['domain'].upper()}] {item['title']}")
        lines.append(f"- Source: {item['source']}")
        lines.append(f"- Published: {item.get('published_at') or 'unknown'}")
        lines.append(f"- URL: {item['url']}")
        lines.append(f"- Score: {item['score']}")
        if item.get("snippet"):
            lines.append(f"- Snippet: {item['snippet']}")
        lines.append("- Body:")
        body = str(item.get("body_text", "")).strip()
        if body:
            lines.append(body[:4000])
        else:
            lines.append("(本文取得に失敗。要手動確認)")
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="日次ニュース向け入力データを収集する。")
    p.add_argument("--date", help="対象日 YYYY-MM-DD。未指定時はタイムゾーン当日。")
    p.add_argument("--timezone", default="Asia/Tokyo")
    p.add_argument("--output-root", default=str(DEFAULT_OUTPUT_ROOT))
    p.add_argument("--max-per-source", type=int, default=12)
    p.add_argument("--top-per-domain", type=int, default=5)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    target_date = resolve_target_date(args.date, args.timezone)
    repo_root = find_repo_root(Path(__file__).resolve())
    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = repo_root / output_root
    out_dir = output_root / target_date / "research"
    out_dir.mkdir(parents=True, exist_ok=True)

    domains = ["ai", "semiconductor"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        futures = {
            d: pool.submit(collect_domain, d, target_date, args.max_per_source, args.top_per_domain)
            for d in domains
        }
    try:
        ai_all, ai_selected = futures["ai"].result()
    except Exception as exc:
        print(f"WARNING: ai domain collection failed: {exc}", file=sys.stderr)
        ai_all, ai_selected = [], []
    try:
        semi_all, semi_selected = futures["semiconductor"].result()
    except Exception as exc:
        print(f"WARNING: semiconductor domain collection failed: {exc}", file=sys.stderr)
        semi_all, semi_selected = [], []

    all_candidates = {"date": target_date, "generated_at": dt.datetime.now(dt.UTC).isoformat(), "candidates": ai_all + semi_all}
    selected = {"date": target_date, "generated_at": dt.datetime.now(dt.UTC).isoformat(), "selected": ai_selected + semi_selected}

    (out_dir / "candidates.json").write_text(json.dumps(all_candidates, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "selected-with-body.json").write_text(json.dumps(selected, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "context.md").write_text(build_context_markdown(target_date, selected["selected"]), encoding="utf-8")

    print(f"write {out_dir / 'candidates.json'}")
    print(f"write {out_dir / 'selected-with-body.json'}")
    print(f"write {out_dir / 'context.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
