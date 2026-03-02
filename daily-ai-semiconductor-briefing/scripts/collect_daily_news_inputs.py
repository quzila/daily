#!/usr/bin/env python3
"""日次ニュース作成のための候補収集・選定・本文取得を行う。"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import email.utils
import html
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from zoneinfo import ZoneInfo


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
    url = "https://zenn.dev/api/articles?order=trend"
    data = fetch_json(url)
    out: list[Candidate] = []
    for a in data.get("articles", [])[: limit * 2]:
        path = a.get("path") or ""
        if not path:
            continue
        full_url = urllib.parse.urljoin("https://zenn.dev", path)
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
    query = "Cursor Claude Code Copilot ChatGPT" if domain == "ai" else "半導体 決算 GPU HBM"
    url = f"https://note.com/search?context=note&q={urllib.parse.quote(query)}&sort=popular"
    html_text = fetch_text(url)
    rels = re.findall(r"/[a-zA-Z0-9_]+/n/[a-zA-Z0-9]+", html_text)
    uniq: list[str] = []
    for r in rels:
        if r not in uniq:
            uniq.append(r)
        if len(uniq) >= limit:
            break
    out: list[Candidate] = []
    for rel in uniq:
        page_url = urllib.parse.urljoin("https://note.com", rel)
        try:
            article_html = fetch_text(page_url)
        except Exception:
            continue
        title = extract_og_title(article_html) or rel
        m_date = re.search(
            r'<meta[^>]+property=["\']article:published_time["\'][^>]+content=["\']([^"\']+)["\']',
            article_html,
            re.IGNORECASE,
        )
        published = parse_iso_date(m_date.group(1)) if m_date else ""
        out.append(
            Candidate(
                domain=domain,
                source="note",
                title=title,
                url=page_url,
                published_at=published,
                snippet="",
            )
        )
        time.sleep(0.2)
    return out


def fetch_reddit_candidates(domain: str, limit: int) -> list[Candidate]:
    subs = REDDIT_SUBS_AI if domain == "ai" else REDDIT_SUBS_SEMI
    out: list[Candidate] = []
    per_sub = max(3, limit // max(1, len(subs)))
    for sub in subs:
        url = f"https://api.reddit.com/r/{sub}/top?t=day&limit={per_sub}"
        try:
            data = fetch_json(url)
        except Exception:
            continue
        for child in data.get("data", {}).get("children", []):
            d = child.get("data", {})
            title = normalize_space(d.get("title") or "")
            link = d.get("url_overridden_by_dest") or f"https://www.reddit.com{d.get('permalink', '')}"
            published = dt.datetime.fromtimestamp(d.get("created_utc", 0), dt.UTC).date().isoformat()
            snippet = normalize_space((d.get("selftext") or "")[:400])
            out.append(
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
        time.sleep(0.2)
    return out


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
        if domain == "ai" and key_hit < 2:
            continue
        if domain == "semiconductor" and key_hit < 1:
            continue
        filtered.append(c)

    ranked = sorted(filtered, key=lambda x: x.score, reverse=True)
    selected = ranked[:top_n]

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
    selected_items = [enrich_with_body(c) for c in selected]
    return all_items, selected_items


def resolve_target_date(date_arg: str | None, timezone: str) -> str:
    if date_arg:
        dt.datetime.strptime(date_arg, "%Y-%m-%d")
        return date_arg
    return dt.datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d")


def build_context_markdown(target_date: str, selected: list[dict]) -> str:
    lines: list[str] = []
    lines.append(f"# Daily Research Context ({target_date})")
    lines.append("")
    lines.append("## Writing Rule")
    lines.append("- 各記事は必ず `事実(What) / 背景(Why it matters) / 影響(So what)` を含める。")
    lines.append("- 事実には数字・日付・固有名詞を入れる。")
    lines.append("- 影響はノジマ店頭業務または日々の開発運用に接続する。")
    lines.append("")
    lines.append("## Few-shot (Good Example)")
    lines.append("- タイトル: Copilot CLI GA")
    lines.append("- 30秒で読める要約: 2026-02-25にGA。CLIで計画実行とMCP連携が正式化し、運用自動化の実装コストが下がった。")
    lines.append("- 記事全体の内容:")
    lines.append("  - 事実(What): GitHub公式がGAを発表。プレビュー(2025-09)からの主要追加はエージェント実行、セッション継続、MCP対応。")
    lines.append("  - 背景(Why it matters): AI開発の主戦場がIDE内補完から、CLIを含む運用全体へ移っている。")
    lines.append("  - 影響(So what): 障害一次対応テンプレをCLI化し、店頭向け在庫/価格更新スクリプトの自動化に転用できる。")
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
    p.add_argument("--output-root", default="daily-news")
    p.add_argument("--max-per-source", type=int, default=12)
    p.add_argument("--top-per-domain", type=int, default=5)
    return p.parse_args()


def main() -> int:
    args = parse_args()
    target_date = resolve_target_date(args.date, args.timezone)
    out_dir = Path(args.output_root) / target_date / "research"
    out_dir.mkdir(parents=True, exist_ok=True)

    ai_all, ai_selected = collect_domain("ai", target_date, args.max_per_source, args.top_per_domain)
    semi_all, semi_selected = collect_domain("semiconductor", target_date, args.max_per_source, args.top_per_domain)

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
