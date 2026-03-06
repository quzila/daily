#!/usr/bin/env python3
"""Render daily briefing HTML and publish it to docs/ for GitHub Pages."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import socket
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "Asia/Tokyo"
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HIGHLIGHT_PATTERN = re.compile(r"^>\s*\d+[)）]\s*(.+)$")
SUMMARY_PATTERN = re.compile(r"^\*\*ひとことサマリー（1文）\*\*:\s*(.+)$")
MARKDOWN_LINK_PATTERN = re.compile(r"\((https?://[^)\s]+)\)")
PLAIN_URL_PATTERN = re.compile(r"https?://\S+")
CATEGORY_HEADING_PATTERN = re.compile(
    r"^###\s+【カテゴリ([A-Z](?:/[A-Z])*)[^】]*】(.+?)（([^）,]+),\s*([^）]+)）\s*$"
)
SOURCE_META_PATTERN = re.compile(
    r"^-\s*(.+?),\s*(?:公開日:\s*)?([^,]+),\s*(?:アクセス日|確認日):\s*([^,]+),\s*種別:\s*(.+)$"
)
WHAT_FIELD_PATTERN = re.compile(r"^\*\*何が起きたか（What）\*\*:\s*(.*)$", re.MULTILINE)
WHY_FIELD_PATTERN = re.compile(r"^\*\*なぜ重要か（Why it matters）\*\*:\s*(.*)$", re.MULTILINE)
SOWHAT_FIELD_PATTERN = re.compile(
    r"^\*\*自分への影響（So what[^）]*）\*\*:\s*(.*)$", re.MULTILINE
)
PSEUDO_SUMMARY_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"記事内では「[^」]{80,}」といった内容が示され", re.MULTILINE),
    re.compile(r"さらに本文では「[^」]{80,}」", re.MULTILINE),
    re.compile(r"\d{4}-\d{2}-\d{2}の収集で", re.MULTILINE),
    re.compile(r"本日（\d{4}-\d{2}-\d{2}）の収集では", re.MULTILINE),
    re.compile(r"構造化メモが不足している", re.MULTILINE),
)
GENERIC_EXPLANATION_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"本文確認済みの事実を圧縮した要点として", re.MULTILINE),
    re.compile(r"AI開発が単なるモデル選定から運用設計・再現性確保へ重心を移している", re.MULTILINE),
    re.compile(r"導入成否は機能比較だけでなく", re.MULTILINE),
    re.compile(r"この話題を検証テーマに入れ", re.MULTILINE),
    re.compile(r"テンプレート化した評価軸を固定して継続比較する", re.MULTILINE),
    re.compile(r"クラウド利用とローカル検証機の配分を再試算する", re.MULTILINE),
)
FORBIDDEN_DISCOVERY_URL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^https?://zenn\.dev/search\?", re.IGNORECASE),
    re.compile(r"^https?://zenn\.dev/topics/", re.IGNORECASE),
    re.compile(r"^https?://zenn\.dev/api/", re.IGNORECASE),
    re.compile(r"^https?://note\.com/search\?", re.IGNORECASE),
)
FORBIDDEN_ARTICLE_URL_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^https?://news\.ycombinator\.com/item\?id=\d+", re.IGNORECASE),
    re.compile(r"^https?://github\.blog/changelog/?$", re.IGNORECASE),
    re.compile(r"^https?://huggingface\.co/blog/?$", re.IGNORECASE),
    re.compile(r"^https?://nvidianews\.nvidia\.com/?$", re.IGNORECASE),
    re.compile(r"^https?://www\.amd\.com/en/newsroom\.html/?$", re.IGNORECASE),
    re.compile(r"^https?://news\.samsung\.com/(?:global/)?tag/[^/?#]+/?$", re.IGNORECASE),
    re.compile(r"^https?://www\.anthropic\.com/news/?$", re.IGNORECASE),
    re.compile(r"^https?://openai\.com/news/?$", re.IGNORECASE),
)
DEFAULT_ARCHIVE_SUMMARY = "AIと半導体領域の主要トピックを要点整理した日次ブリーフィング。"
MIN_FIELD_CHARS = 60
MIN_AI_ARTICLES = 8
MIN_CHIP_ARTICLES = 5
DEFAULT_ARCHIVE_TEMPLATE = (
    Path(__file__).resolve().parent.parent / "assets" / "archive-index.html"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="daily-news.md -> index.html -> docs/ 反映を実行する。"
    )
    parser.add_argument("--date", help="対象日 (YYYY-MM-DD)。未指定時はタイムゾーン当日。")
    parser.add_argument("--timezone", default=DEFAULT_TIMEZONE, help="IANAタイムゾーン名。")
    parser.add_argument(
        "--skip-render",
        action="store_true",
        help="HTML再生成をスキップし、既存の index.html を使う。",
    )
    parser.add_argument(
        "--commit",
        action="store_true",
        help="docs 反映後に commit する。",
    )
    parser.add_argument(
        "--push",
        action="store_true",
        help="commit 後に push する（--commit が未指定でも commit 実行）。",
    )
    parser.add_argument("--remote", default="origin", help="push 先リモート名。")
    parser.add_argument("--branch", help="push 先ブランチ名。未指定時は現在のブランチ。")
    parser.add_argument(
        "--message",
        help="コミットメッセージ。未指定時は日付ベースで自動生成。",
    )
    return parser.parse_args()


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise FileNotFoundError(f"repository root not found from {start}")


def run_command(cmd: list[str], *, cwd: Path) -> str:
    completed = subprocess.run(
        cmd,
        cwd=str(cwd),
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        stderr = completed.stderr.strip()
        stdout = completed.stdout.strip()
        body = stderr or stdout or f"exit code {completed.returncode}"
        raise RuntimeError(f"command failed: {' '.join(cmd)}\n{body}")
    return completed.stdout.strip()


def resolve_target_date(date_arg: str | None, timezone: str) -> str:
    if date_arg:
        if not DATE_PATTERN.match(date_arg):
            raise ValueError("date must be YYYY-MM-DD format")
        dt.datetime.strptime(date_arg, "%Y-%m-%d")
        return date_arg
    now = dt.datetime.now(ZoneInfo(timezone))
    return now.strftime("%Y-%m-%d")


def render_html(repo_root: Path, target_date: str, timezone: str) -> None:
    renderer = (
        repo_root
        / "skills"
        / "daily-news-md-to-html"
        / "scripts"
        / "render_markdown_to_html.py"
    )
    if not renderer.exists():
        raise FileNotFoundError(f"renderer script not found: {renderer}")
    out = run_command(
        [
            sys.executable,
            str(renderer),
            "--date",
            target_date,
            "--timezone",
            timezone,
            "--overwrite",
        ],
        cwd=repo_root,
    )
    if out:
        print(out)


def write_latest_redirect(docs_root: Path, target_date: str) -> None:
    redirect = f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta http-equiv="refresh" content="0; url=./daily-news/{target_date}/index.html" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Daily Briefing</title>
</head>
<body>
  <p><a href="./daily-news/{target_date}/index.html">最新レポートを開く ({target_date})</a></p>
</body>
</html>
"""
    (docs_root / "index.html").write_text(redirect, encoding="utf-8")


def markdown_to_plain_text(text: str) -> str:
    plain = text.strip()
    plain = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r"\1", plain)
    plain = re.sub(r"`([^`]+)`", r"\1", plain)
    plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", plain)
    plain = re.sub(r"\*([^*]+)\*", r"\1", plain)
    plain = re.sub(r"^\s*[-*>]\s*", "", plain)
    plain = re.sub(r"\s+", " ", plain)
    return plain.strip()


def trim_summary(text: str, limit: int = 180) -> str:
    compact = markdown_to_plain_text(text)
    if len(compact) <= limit:
        return compact
    return compact[: limit - 3].rstrip() + "..."


def extract_issue_metadata(md_file: Path, date: str) -> tuple[str, str]:
    title = f"デイリーAI・半導体ニュース（{date}）"
    summary_candidates: list[str] = []

    try:
        md_text = md_file.read_text(encoding="utf-8")
    except Exception:
        return title, DEFAULT_ARCHIVE_SUMMARY

    for line in md_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = markdown_to_plain_text(stripped[2:]) or title
            continue

        m = HIGHLIGHT_PATTERN.match(stripped)
        if m:
            value = trim_summary(m.group(1))
            if value:
                summary_candidates.append(value)
            continue

        m2 = SUMMARY_PATTERN.match(stripped)
        if m2:
            value = trim_summary(m2.group(1))
            if value:
                summary_candidates.append(value)

    # Deduplicate while preserving order.
    unique_summaries: list[str] = []
    for candidate in summary_candidates:
        if candidate not in unique_summaries:
            unique_summaries.append(candidate)

    if unique_summaries:
        summary = " / ".join(unique_summaries[:2])
    else:
        summary = DEFAULT_ARCHIVE_SUMMARY

    return title, trim_summary(summary, limit=220)


def extract_report_urls(markdown_text: str) -> list[str]:
    urls: list[str] = []
    for raw in markdown_text.splitlines():
        line = raw.strip()
        if "- リンク:" not in line:
            continue
        found_links = MARKDOWN_LINK_PATTERN.findall(line)
        if found_links:
            urls.extend(found_links)
            continue
        for candidate in PLAIN_URL_PATTERN.findall(line):
            urls.append(candidate.rstrip(")"))
    return urls


def extract_highlight_lines(markdown_text: str) -> list[str]:
    highlights: list[str] = []
    for raw in markdown_text.splitlines():
        match = HIGHLIGHT_PATTERN.match(raw.strip())
        if match:
            highlights.append(markdown_to_plain_text(match.group(1)))
    return highlights


def normalize_field_text(text: str) -> str:
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r"\1", text)
    return re.sub(r"\s+", "", text).strip()


def extract_markdown_link_url(value: str) -> str:
    value = value.strip()
    md_link = re.search(r"\((https?://[^)\s]+)\)", value)
    if md_link:
        return md_link.group(1).strip()
    plain = re.search(r"https?://\S+", value)
    return plain.group(0).rstrip(")") if plain else ""


def check_zenn_note_reachability(url: str) -> tuple[bool, str]:
    parsed = urllib.parse.urlparse(url)
    host = parsed.netloc.lower()
    if host in {"www.zenn.dev", "www.note.com"}:
        return False, f"use canonical host without www for zenn/note: {url}"
    if host not in {"zenn.dev", "note.com"}:
        return True, ""
    if host == "zenn.dev" and not re.match(r"^/[^/]+/articles/[^/?#]+$", parsed.path):
        return False, f"invalid zenn article URL format: {url}"
    if host == "note.com" and not re.match(r"^/[^/]+/n/[^/?#]+$", parsed.path):
        return False, f"invalid note article URL format: {url}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            status = resp.getcode() or 0
        if status >= 400:
            return False, f"url returned status {status}: {url}"
        return True, ""
    except urllib.error.HTTPError as exc:
        return False, f"url returned status {exc.code}: {url}"
    except urllib.error.URLError as exc:
        # Offline/DNS-restricted environments cannot resolve hosts; keep format checks only.
        if isinstance(getattr(exc, "reason", None), socket.gaierror):
            return True, ""
        return False, f"url fetch failed ({exc}): {url}"
    except Exception as exc:
        return False, f"url fetch failed ({exc}): {url}"


def check_portal_or_hn_item_url(url: str) -> tuple[bool, str]:
    if any(pattern.search(url) for pattern in FORBIDDEN_ARTICLE_URL_PATTERNS):
        return False, f"portal/listing URL is not allowed as article source: {url}"
    return True, ""


def looks_like_pseudo_explanation(text: str) -> bool:
    if any(pattern.search(text) for pattern in PSEUDO_SUMMARY_PATTERNS):
        return True
    if re.search(r"「[^」]{120,}」", text):
        return True
    return False


def looks_like_generic_explanation(text: str) -> bool:
    return any(pattern.search(text) for pattern in GENERIC_EXPLANATION_PATTERNS)


def split_sentences_for_validation(text: str) -> list[str]:
    normalized = markdown_to_plain_text(text)
    parts = re.split(r"(?<=[。.!?])\s+", normalized)
    return [part.strip() for part in parts if part.strip()]


def validate_report_quality(report_md_path: Path) -> None:
    try:
        markdown_text = report_md_path.read_text(encoding="utf-8")
        lines = markdown_text.splitlines()
    except Exception as exc:
        raise ValueError(f"report markdown read failed: {report_md_path}: {exc}") from exc

    ai_count = 0
    chip_count = 0
    current_section = ""
    section_has_sources = False
    source_mode = False
    source_meta_count = 0
    source_url_count = 0
    source_urls: list[str] = []
    issues: list[str] = []
    repeated_sentences: dict[str, dict[str, list[str]]] = {
        "What": {},
        "Why": {},
        "So what": {},
    }
    i = 0

    while i < len(lines):
        line = lines[i].strip()

        if line.startswith("## "):
            heading = line[3:].strip()
            source_mode = False
            if "AI ニュース" in heading or "AIニュース" in heading:
                current_section = "ai"
            elif "半導体ニュース" in heading:
                current_section = "chip"
            elif "ソース一覧" in heading or heading == "ソース":
                current_section = ""
                source_mode = True
                section_has_sources = True
            else:
                current_section = ""

        if source_mode:
            if SOURCE_META_PATTERN.match(line):
                source_meta_count += 1
            elif line.startswith("http://") or line.startswith("https://"):
                source_url_count += 1
                source_urls.append(line)

        heading_match = CATEGORY_HEADING_PATTERN.match(line)
        if not heading_match:
            i += 1
            continue

        title = heading_match.group(2).strip()
        if current_section == "ai":
            ai_count += 1
        elif current_section == "chip":
            chip_count += 1

        j = i + 1
        block_lines: list[str] = []
        while j < len(lines):
            next_line = lines[j].strip()
            if next_line.startswith("## ") or CATEGORY_HEADING_PATTERN.match(next_line):
                break
            block_lines.append(lines[j])
            j += 1
        block_text = "\n".join(block_lines)

        def collect_field(pattern: re.Pattern[str], label: str) -> str:
            match = pattern.search(block_text)
            if not match:
                issues.append(f"{title}: {label} field is missing")
                return ""
            first = match.group(1).strip()
            tail = block_text.split(match.group(0), 1)[1]
            parts = [first] if first else []
            for tail_line in tail.splitlines()[1:]:
                stripped = tail_line.strip()
                if stripped.startswith("**") or stripped.startswith("- "):
                    break
                if stripped:
                    parts.append(stripped)
            return " ".join(parts).strip()

        what_text = collect_field(WHAT_FIELD_PATTERN, "What")
        why_text = collect_field(WHY_FIELD_PATTERN, "Why")
        so_what_text = collect_field(SOWHAT_FIELD_PATTERN, "So what")
        for label, text in (("What", what_text), ("Why", why_text), ("So what", so_what_text)):
            if text and len(normalize_field_text(text)) < MIN_FIELD_CHARS:
                issues.append(
                    f"{title}: {label} is too short (<{MIN_FIELD_CHARS} chars without spaces)"
                )
            if text and looks_like_pseudo_explanation(text):
                issues.append(
                    f"{title}: {label} looks like a raw excerpt/pseudo-summary; rewrite as a paraphrased explanation"
                )
            if text and looks_like_generic_explanation(text):
                issues.append(
                    f"{title}: {label} still contains boilerplate explanation; rewrite with article-specific reasoning"
                )
            if text:
                for sentence in split_sentences_for_validation(text):
                    normalized_sentence = normalize_field_text(sentence)
                    if len(normalized_sentence) < 28:
                        continue
                    repeated_sentences[label].setdefault(normalized_sentence, []).append(title)

        link_url = ""
        for block_line in block_lines:
            stripped = block_line.strip()
            if stripped.startswith("- リンク:"):
                link_url = extract_markdown_link_url(stripped.split(":", 1)[1].strip())
                break
        if not link_url:
            issues.append(f"{title}: article link is missing")
        else:
            ok, reason = check_zenn_note_reachability(link_url)
            if not ok:
                issues.append(f"{title}: {reason}")
            ok2, reason2 = check_portal_or_hn_item_url(link_url)
            if not ok2:
                issues.append(f"{title}: {reason2}")

        i = j

    if ai_count < MIN_AI_ARTICLES:
        issues.insert(0, f"AI articles are insufficient: {ai_count} < {MIN_AI_ARTICLES}")
    if chip_count < MIN_CHIP_ARTICLES:
        issues.insert(0, f"Semiconductor articles are insufficient: {chip_count} < {MIN_CHIP_ARTICLES}")
    if not section_has_sources:
        issues.append("`## ソース一覧` section is missing")
    if source_meta_count == 0 or source_url_count == 0:
        issues.append("source metadata and URLs must be present in `## ソース一覧`")
    for source_url in source_urls:
        ok, reason = check_zenn_note_reachability(source_url)
        if not ok:
            issues.append(f"source list URL: {reason}")
        ok2, reason2 = check_portal_or_hn_item_url(source_url)
        if not ok2:
            issues.append(f"source list URL: {reason2}")

    # Prevent stale duplication: today's highlight 3 lines must not be identical to previous day.
    report_date = report_md_path.parent.name
    if DATE_PATTERN.match(report_date):
        prev_date = (dt.datetime.strptime(report_date, "%Y-%m-%d").date() - dt.timedelta(days=1)).isoformat()
        prev_md = report_md_path.parent.parent / prev_date / "daily-news.md"
        if prev_md.exists():
            current_highlights = extract_highlight_lines(markdown_text)
            prev_text = prev_md.read_text(encoding="utf-8")
            prev_highlights = extract_highlight_lines(prev_text)
            if current_highlights and current_highlights == prev_highlights:
                issues.append(
                    f"highlight 3 lines are unchanged from previous day ({prev_date}); refresh `## 今日のハイライト（3選）`"
                )

    for label, sentence_map in repeated_sentences.items():
        for sentence, titles in sentence_map.items():
            if len(titles) < 3:
                continue
            preview = markdown_to_plain_text(sentence)[:80]
            issues.append(
                f"{label} contains repeated boilerplate across {len(titles)} articles: {preview}"
            )

    if issues:
        preview = "\n".join(f"- {item}" for item in issues[:20])
        raise ValueError(f"report quality gate failed:\n{preview}")


def validate_discovery_urls(report_md_path: Path) -> None:
    try:
        markdown_text = report_md_path.read_text(encoding="utf-8")
    except Exception as exc:
        raise ValueError(f"report markdown read failed: {report_md_path}: {exc}") from exc

    blocked: list[str] = []
    for url in extract_report_urls(markdown_text):
        if any(pattern.search(url) for pattern in FORBIDDEN_DISCOVERY_URL_PATTERNS):
            blocked.append(url)

    if not blocked:
        return

    unique_blocked = sorted(set(blocked))
    preview = "\n".join(f"- {url}" for url in unique_blocked[:8])
    raise ValueError(
        "discovery/listing URL is not allowed in article links. "
        "Replace with canonical article URLs before publish.\n"
        f"{preview}"
    )


def build_articles_json(docs_daily_root: Path) -> list[dict]:
    entries: list[dict] = []
    for child in docs_daily_root.iterdir():
        if not (child.is_dir() and DATE_PATTERN.match(child.name)):
            continue
        html_file = child / "index.html"
        md_file = child / "daily-news.md"
        if not html_file.exists():
            continue
        date = child.name
        title, summary = extract_issue_metadata(md_file, date)
        entries.append({
            "date": date,
            "title": title,
            "summary": summary,
            "path": f"/daily-news/{date}/",
        })
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


def render_archive_cards(entries: list[dict]) -> str:
    cards: list[str] = []
    for entry in entries:
        date = html.escape(entry["date"])
        title = html.escape(entry["title"])
        summary = html.escape(entry.get("summary", DEFAULT_ARCHIVE_SUMMARY))
        href = f'./{date}/index.html'
        cards.append(
            (
                f'      <a href="{href}" class="arc-card fi">\n'
                f'        <div class="arc-card-date">{date}</div>\n'
                f'        <div class="arc-card-title">{title}</div>\n'
                f'        <p class="arc-card-desc">{summary}</p>\n'
                f'        <span class="arc-card-arrow">Read →</span>\n'
                f'      </a>'
            )
        )
    return "\n\n".join(cards)


def render_archive_index_html(entries: list[dict], latest_date: str) -> str:
    if not DEFAULT_ARCHIVE_TEMPLATE.exists():
        raise FileNotFoundError(f"archive template not found: {DEFAULT_ARCHIVE_TEMPLATE}")

    template = DEFAULT_ARCHIVE_TEMPLATE.read_text(encoding="utf-8")
    if not entries:
        raise ValueError("archive index cannot be rendered because no entries were found")

    latest_entry = next((entry for entry in entries if entry["date"] == latest_date), entries[0])
    since_year = entries[-1]["date"][:4]
    cards_html = render_archive_cards(entries)

    replacements = {
        "{{LATEST_PATH}}": f'./{latest_entry["date"]}/index.html',
        "{{LATEST_DATE}}": html.escape(latest_entry["date"]),
        "{{LATEST_TITLE}}": html.escape(latest_entry["title"]),
        "{{LATEST_DESCRIPTION}}": html.escape(
            latest_entry.get("summary", DEFAULT_ARCHIVE_SUMMARY)
        ),
        "{{ISSUE_COUNT}}": html.escape(str(len(entries))),
        "{{SINCE_YEAR}}": html.escape(since_year),
        "{{ARCHIVE_CARDS}}": cards_html,
    }

    required_tokens = tuple(replacements.keys())
    missing = [token for token in required_tokens if token not in template]
    if missing:
        missing_str = ", ".join(missing)
        raise ValueError(f"archive template is missing placeholders: {missing_str}")

    rendered = template
    for token, value in replacements.items():
        rendered = rendered.replace(token, value)
    return rendered


def write_archive_index(docs_daily_root: Path, latest_date: str) -> None:
    entries = build_articles_json(docs_daily_root)
    html_doc = render_archive_index_html(entries, latest_date)
    (docs_daily_root / "index.html").write_text(html_doc, encoding="utf-8")


def re_render_all_dates(
    repo_root: Path,
    docs_daily_root: Path,
    articles_json_str: str,
    timezone: str,
) -> int:
    renderer = (
        repo_root
        / "skills"
        / "daily-news-md-to-html"
        / "scripts"
        / "render_markdown_to_html.py"
    )
    if not renderer.exists():
        print(f"WARNING: renderer not found: {renderer}", file=sys.stderr)
        return 0
    count = 0
    for child in sorted(docs_daily_root.iterdir()):
        if not (child.is_dir() and DATE_PATTERN.match(child.name)):
            continue
        md_file = child / "daily-news.md"
        html_file = child / "index.html"
        if not md_file.exists():
            continue
        try:
            out = run_command(
                [
                    sys.executable,
                    str(renderer),
                    "--date", child.name,
                    "--timezone", timezone,
                    "--input", str(md_file),
                    "--output", str(html_file),
                    "--overwrite",
                    "--articles-json", articles_json_str,
                ],
                cwd=repo_root,
            )
            if out:
                print(out)
            count += 1
        except Exception as exc:
            print(f"WARNING: re-render failed for {child.name}: {exc}", file=sys.stderr)
    return count


def sync_to_docs(repo_root: Path, target_date: str) -> Path:
    source_dir = repo_root / "reports" / "daily-news" / target_date
    source_html = source_dir / "index.html"
    source_md = source_dir / "daily-news.md"

    if not source_html.exists():
        raise FileNotFoundError(f"source html not found: {source_html}")
    if not source_md.exists():
        raise FileNotFoundError(f"source markdown not found: {source_md}")
    validate_discovery_urls(source_md)
    validate_report_quality(source_md)

    docs_root = repo_root / "docs"
    docs_daily_root = docs_root / "daily-news"
    target_dir = docs_daily_root / target_date
    target_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source_html, target_dir / "index.html")
    shutil.copy2(source_md, target_dir / "daily-news.md")

    # Keep archive-compatible history in docs/ by syncing all report dates.
    reports_daily_root = repo_root / "reports" / "daily-news"
    if reports_daily_root.exists():
        for child in sorted(reports_daily_root.iterdir()):
            if not (child.is_dir() and DATE_PATTERN.match(child.name)):
                continue
            report_html = child / "index.html"
            report_md = child / "daily-news.md"
            if not (report_html.exists() and report_md.exists()):
                continue
            history_dir = docs_daily_root / child.name
            history_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(report_html, history_dir / "index.html")
            shutil.copy2(report_md, history_dir / "daily-news.md")

    write_latest_redirect(docs_root, target_date)
    write_archive_index(docs_daily_root, target_date)
    return docs_root


def current_branch(repo_root: Path) -> str:
    return run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)


def ensure_branch_for_commits(repo_root: Path) -> str:
    branch = current_branch(repo_root)
    if branch != "HEAD":
        return branch
    stamp = dt.datetime.now(ZoneInfo(DEFAULT_TIMEZONE)).strftime("%Y%m%d-%H%M%S")
    rescue_branch = f"codex/automation-rescue-{stamp}"
    run_command(["git", "switch", "-c", rescue_branch], cwd=repo_root)
    print(f"Detached HEAD detected. Switched to rescue branch: {rescue_branch}")
    return rescue_branch


def can_reach_remote(repo_root: Path, remote: str) -> tuple[bool, str]:
    try:
        socket.gethostbyname("github.com")
    except Exception as exc:
        return False, f"DNS lookup failed for github.com: {exc}"

    probe = subprocess.run(
        ["git", "ls-remote", remote, "HEAD"],
        cwd=str(repo_root),
        check=False,
        capture_output=True,
        text=True,
    )
    if probe.returncode != 0:
        err = probe.stderr.strip() or probe.stdout.strip() or "unknown error"
        return False, f"git ls-remote failed: {err}"
    return True, ""


def commit_and_push(
    repo_root: Path,
    docs_root: Path,
    *,
    target_date: str,
    commit_enabled: bool,
    push_enabled: bool,
    remote: str,
    branch: str | None,
    message: str | None,
) -> None:
    if push_enabled:
        commit_enabled = True
    if not commit_enabled:
        return

    ensured_branch = ensure_branch_for_commits(repo_root)
    if branch is None:
        branch = ensured_branch

    docs_rel = docs_root.relative_to(repo_root)
    run_command(["git", "add", "--", str(docs_rel)], cwd=repo_root)

    staged_check = subprocess.run(
        ["git", "diff", "--cached", "--quiet", "--", str(docs_rel)],
        cwd=str(repo_root),
        check=False,
    )
    if staged_check.returncode == 0:
        print("No docs changes to commit.")
        return

    commit_message = message or f"docs: publish daily briefing {target_date}"
    print(run_command(["git", "commit", "-m", commit_message], cwd=repo_root))

    if push_enabled:
        push_branch = branch or current_branch(repo_root)
        ok, reason = can_reach_remote(repo_root, remote)
        if not ok:
            raise RuntimeError(
                "push required but preflight failed.\n"
                f"{reason}\n"
                f"Run after fixing network/auth: git push {remote} {push_branch}"
            )
        print(run_command(["git", "push", remote, push_branch], cwd=repo_root))


def main() -> int:
    args = parse_args()
    repo_root = find_repo_root(Path(__file__).resolve())

    try:
        target_date = resolve_target_date(args.date, args.timezone)
    except Exception as exc:
        raise SystemExit(f"invalid date/timezone: {exc}") from exc

    if not args.skip_render:
        render_html(repo_root, target_date, args.timezone)

    docs_root = sync_to_docs(repo_root, target_date)
    print(f"Published report files to {docs_root / 'daily-news' / target_date}")

    docs_daily_root = docs_root / "daily-news"
    articles_entries = build_articles_json(docs_daily_root)
    articles_json_str = json.dumps(articles_entries, ensure_ascii=False)
    rendered_count = re_render_all_dates(repo_root, docs_daily_root, articles_json_str, args.timezone)
    print(f"Re-rendered {rendered_count} article(s) with navigation data.")

    commit_and_push(
        repo_root,
        docs_root,
        target_date=target_date,
        commit_enabled=args.commit,
        push_enabled=args.push,
        remote=args.remote,
        branch=args.branch,
        message=args.message,
    )

    print("Done. GitHub Pages source should point to main/docs.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
