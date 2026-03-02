#!/usr/bin/env python3
"""Render daily-news.md to index.html with a reusable HTML template."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import html
import json
import re
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_OUTPUT_ROOT = Path("reports") / "daily-news"
DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "index.html"

# ── Legacy normalization patterns ──────────────────────────────────────────────
ARTICLE_NUMBER_HEADING = re.compile(r"^###\s*記事\d+\s*$")
TITLE_LINE    = re.compile(r"^\s*-\s*タイトル:\s*(.+?)\s*$")
SUMMARY_LINE  = re.compile(r"^\s*-\s*30秒で読める要約:\s*(.+?)\s*$")
WHAT_LINE     = re.compile(r"^\s*-\s*事実（What）:\s*(.+?)\s*$")
WHY_LINE      = re.compile(r"^\s*-\s*背景（Why it matters）:\s*(.+?)\s*$")
SOWHAT_LINE   = re.compile(r"^\s*-\s*影響（So what[^）]*）:\s*(.+?)\s*$")
LINK_LINE     = re.compile(r"^\s*-\s*リンク:\s*(.+?)\s*$")

# ── Structured parsing patterns ────────────────────────────────────────────────
CATEGORY_HEADING = re.compile(
    r"^###\s+【カテゴリ([A-Z](?:/[A-Z])*)[^】]*】(.+?)（([^）,]+),\s*([^）]+)）\s*$"
)
SUBSECTION_HEADING = re.compile(r"^###\s+(?!【)(.+)$")
SUMMARY_BOLD  = re.compile(r"^\*\*ひとことサマリー（1文）\*\*:\s*(.*)$")
WHAT_BOLD     = re.compile(r"^\*\*何が起きたか（What）\*\*:\s*(.*)$")
WHY_BOLD      = re.compile(r"^\*\*なぜ重要か（Why it matters）\*\*:\s*(.*)$")
SOWHAT_BOLD   = re.compile(r"^\*\*自分への影響（So what[^）]*）\*\*:\s*(.*)$")
LINK_MD       = re.compile(r"^-\s*リンク:\s*(.+)$")
CONF_LINE     = re.compile(r"^-\s*確信度:\s*(高|中|低)$")
HIGHLIGHT_ITEM = re.compile(r"^>\s*\d+[)）]\s*(.+)$")
SOURCE_META_LINE = re.compile(
    r"^-\s*(.+?),\s*(?:公開日:\s*)?([^,]+),\s*アクセス日:\s*([^,]+),\s*種別:\s*(.+)$"
)

CATEGORY_TAG: dict[str, str] = {
    "A": "tag-ai", "B": "tag-chip", "C": "tag-zenn",
    "D": "tag-note", "E": "tag-reddit", "F": "tag-hn", "E/F": "tag-reddit",
}
CATEGORY_BADGE: dict[str, str] = {
    "A": "公式 AI", "B": "公式 半導体", "C": "Zenn",
    "D": "note", "E": "Reddit", "F": "Hacker News", "E/F": "Reddit",
}


@dataclasses.dataclass
class ParsedArticle:
    category: str
    title: str
    source: str
    date: str
    summary: str = ""
    what: str = ""
    why: str = ""
    so_what: str = ""
    link_url: str = ""
    link_text: str = ""
    confidence: str = "中"
    section: str = "ai"
    subsection: str = ""


# ── Structured HTML rendering ──────────────────────────────────────────────────

def _he(text: str) -> str:
    return html.escape(text, quote=False)


def _extract_link(raw: str) -> tuple[str, str]:
    """Parse '- リンク: [label](url)' or '- リンク: url' into (url, label)."""
    m = re.match(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", raw.strip())
    if m:
        return m.group(2), m.group(1)
    m2 = re.match(r"(https?://\S+)", raw.strip())
    if m2:
        url = m2.group(1)
        return url, "→ 元記事を読む"
    return "", raw.strip()


def render_tag(category: str) -> str:
    tag_class = CATEGORY_TAG.get(category, "tag-ai")
    badge_text = CATEGORY_BADGE.get(category, "AI")
    return f'<span class="tag {tag_class}">{_he(badge_text)}</span>'


def render_conf(confidence: str) -> str:
    conf_class = {"高": "conf-high", "中": "conf-mid", "低": "conf-low"}.get(confidence, "conf-mid")
    conf_label = f"確信度: {confidence}" if confidence else "確信度: 中"
    return f'<span class="conf {conf_class}"><span class="conf-dot"></span>{_he(conf_label)}</span>'


def render_block(label: str, text: str) -> str:
    if not text:
        return ""
    return (
        f'<div class="block">\n'
        f'  <div class="block-lbl">{_he(label)}</div>\n'
        f'  <p class="block-txt">{_he(text)}</p>\n'
        f'</div>\n'
    )


def render_card(article: ParsedArticle) -> str:
    card_class = article.section
    tag_html = render_tag(article.category)
    conf_html = render_conf(article.confidence)
    parts = [article.source]
    if article.date:
        parts.append(article.date)
    src_text = _he(" · ".join(p for p in parts if p))
    blocks = (
        render_block("何が起きたか", article.what)
        + render_block("なぜ重要か", article.why)
        + render_block("自分への影響", article.so_what)
    )
    link_html = ""
    if article.link_url:
        label = _he(article.link_text or "→ 元記事を読む")
        link_html = (
            f'<a href="{_he(article.link_url)}" target="_blank" '
            f'rel="noopener" class="card-link">{label}</a>\n'
        )
    return f"""<div class="card {card_class} fi">
  <div class="card-top" onclick="toggle(this)">
    <div class="card-meta">
      {tag_html}
      <span class="card-src">{src_text}</span>
      {conf_html}
    </div>
    <p class="card-summary">{_he(article.summary)}</p>
  </div>
  <div class="card-toggle" onclick="toggle(this)">
    <span class="toggle-lbl">詳細を読む</span>
    <span class="toggle-arrow">▼</span>
  </div>
  <div class="card-body">
    <div class="card-inner">
      {blocks}      {link_html}    </div>
  </div>
</div>"""


def render_subsection(label: str, cards_html: str) -> str:
    return (
        f'<div class="subsec">\n'
        f'  <div class="subsec-label">{_he(label)}</div>\n'
        f'  <div class="cards">\n{cards_html}\n  </div>\n'
        f'</div>\n'
    )


def render_section(section_id: str, articles: list[ParsedArticle]) -> str:
    title_map = {"ai": "AI ニュース", "chip": "半導体ニュース"}
    en_map = {"ai": "Artificial Intelligence", "chip": "Semiconductors"}
    count = len(articles)

    # Group by subsection preserving order
    seen: list[str] = []
    groups: dict[str, list[ParsedArticle]] = {}
    for a in articles:
        key = a.subsection or "その他"
        if key not in groups:
            groups[key] = []
            seen.append(key)
        groups[key].append(a)

    inner = ""
    for label in seen:
        arts = groups[label]
        cards_html = "\n".join(render_card(a) for a in arts)
        inner += render_subsection(label, cards_html)

    return (
        f'<div class="shell">\n'
        f'  <section class="section" id="{section_id}">\n'
        f'    <div class="section-head">\n'
        f'      <h2 class="section-title {section_id}">{_he(title_map.get(section_id, section_id))}</h2>\n'
        f'      <span class="section-en">{en_map.get(section_id, "")}</span>\n'
        f'      <span class="section-cnt">{count} articles</span>\n'
        f'    </div>\n'
        f'{inner}'
        f'  </section>\n'
        f'</div>\n'
    )


def render_highlights(highlights: list[str]) -> str:
    cards = ""
    for i, text in enumerate(highlights, start=1):
        num = f"{i:02d}"
        html_text = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", _he(text))
        cards += (
            f'<div class="hl-card fi">\n'
            f'  <div class="hl-num">{num}</div>\n'
            f'  <p class="hl-text">{html_text}</p>\n'
            f'</div>\n'
        )
    return (
        f'<div class="shell">\n'
        f'  <section class="highlights-wrap">\n'
        f'    <div class="sec-label">今日のハイライト（3選）</div>\n'
        f'    <div class="hl-grid">\n{cards}    </div>\n'
        f'  </section>\n'
        f'</div>\n'
    )


def render_structured_html(parsed: dict) -> str:
    parts: list[str] = []
    if parsed.get("highlights"):
        parts.append(render_highlights(parsed["highlights"]))
    for section in parsed.get("sections", []):
        if section["articles"]:
            parts.append(render_section(section["id"], section["articles"]))
    if parsed.get("sources"):
        parts.append(render_sources_section(parsed["sources"]))
    return "\n".join(parts)


def _source_type_class(source_type: str) -> str:
    low = source_type.lower()
    if "半導体" in source_type:
        return "chip"
    if "公式ai" in low or "公式 ai" in low:
        return "ai"
    if "公式" in source_type and "ai" in low:
        return "ai"
    return "com"


def render_sources_section(sources: list[dict[str, str]]) -> str:
    items: list[str] = []
    for src in sources:
        name = _he(src.get("name", ""))
        published = _he(src.get("published_at", ""))
        accessed = _he(src.get("accessed_at", ""))
        source_type = _he(src.get("type", ""))
        src_class = _source_type_class(src.get("type", ""))
        url = src.get("url", "").strip()
        url_html = ""
        if url:
            safe_url = _he(url)
            url_html = (
                f'<a class="src-url" href="{safe_url}" target="_blank" '
                f'rel="noopener">{safe_url}</a>'
            )
        items.append(
            '<div class="src-item">\n'
            f'  <span class="src-name">{name}</span>\n'
            f'  <span class="src-date">公開: {published} / 参照: {accessed}</span>\n'
            f'  <span class="src-type {src_class}">{source_type}</span>\n'
            f'  {url_html}\n'
            '</div>'
        )
    items_html = "\n".join(items)
    return (
        '<div class="shell">\n'
        '  <section id="sources">\n'
        '    <h2 class="sources-title">ソース一覧</h2>\n'
        f'{items_html}\n'
        '  </section>\n'
        '</div>\n'
    )


# ── Structured Markdown parser ─────────────────────────────────────────────────

def parse_structured_markdown(markdown_text: str) -> dict:
    """Parse structured daily-news.md into a dict for card rendering."""
    result: dict = {
        "page_title": "",
        "highlights": [],
        "sections": [],
        "sources": [],
    }
    current_section_id: str = ""
    current_section_articles: list[ParsedArticle] = []
    current_subsection: str = ""
    current_article: ParsedArticle | None = None
    current_field: str = ""
    current_field_lines: list[str] = []
    current_source: dict[str, str] | None = None
    state = "PREAMBLE"

    def flush_field() -> None:
        nonlocal current_field, current_field_lines
        if not current_article or not current_field:
            current_field = ""
            current_field_lines = []
            return
        text = " ".join(x.strip() for x in current_field_lines if x.strip()).strip()
        if current_field == "summary":
            current_article.summary = text
        elif current_field == "what":
            current_article.what = text
        elif current_field == "why":
            current_article.why = text
        elif current_field == "so_what":
            current_article.so_what = text
        current_field = ""
        current_field_lines = []

    def finalize_article() -> None:
        nonlocal current_article
        flush_field()
        if current_article and (current_article.summary or current_article.what):
            current_section_articles.append(current_article)
        current_article = None

    def finalize_section() -> None:
        nonlocal current_section_id, current_section_articles
        if current_section_id and current_section_articles:
            result["sections"].append({
                "id": current_section_id,
                "articles": list(current_section_articles),
            })
        current_section_id = ""
        current_section_articles = []

    def finalize_source() -> None:
        nonlocal current_source
        if current_source and (
            current_source.get("name")
            or current_source.get("url")
            or current_source.get("type")
        ):
            result["sources"].append(dict(current_source))
        current_source = None

    for raw in markdown_text.splitlines():
        line = raw.strip()

        # Title
        if line.startswith("# ") and not result["page_title"]:
            result["page_title"] = line[2:].strip()
            continue

        # H2 section headers
        if line.startswith("## "):
            finalize_article()
            finalize_source()
            heading = line[3:].strip()
            if "AI ニュース" in heading or "AIニュース" in heading or heading.startswith("AI"):
                finalize_section()
                current_section_id = "ai"
                current_subsection = ""
                state = "SECTION"
            elif "半導体ニュース" in heading or "半導体" in heading:
                finalize_section()
                current_section_id = "chip"
                current_subsection = ""
                state = "SECTION"
            elif "ハイライト" in heading:
                state = "HIGHLIGHTS"
            elif "ソース一覧" in heading:
                finalize_section()
                state = "SOURCES"
            elif "その他" in heading:
                finalize_section()
                state = "OTHER"
            else:
                state = "OTHER"
            continue

        if state == "OTHER":
            continue

        if state == "SOURCES":
            if not line:
                continue
            msrc = SOURCE_META_LINE.match(line)
            if msrc:
                finalize_source()
                current_source = {
                    "name": msrc.group(1).strip(),
                    "published_at": msrc.group(2).strip(),
                    "accessed_at": msrc.group(3).strip(),
                    "type": msrc.group(4).strip(),
                    "url": "",
                }
                continue
            if line.startswith("http://") or line.startswith("https://"):
                if not current_source:
                    current_source = {
                        "name": "",
                        "published_at": "",
                        "accessed_at": "",
                        "type": "",
                        "url": line,
                    }
                else:
                    current_source["url"] = line
                continue
            maybe_url, _ = _extract_link(line)
            if maybe_url and current_source:
                current_source["url"] = maybe_url
            continue

        # Highlights
        if state == "HIGHLIGHTS":
            m = HIGHLIGHT_ITEM.match(line)
            if m:
                result["highlights"].append(m.group(1).strip())
            continue

        # In a section
        if state in ("SECTION", "ARTICLE"):
            if not line or line == "---":
                if line == "---" and state == "ARTICLE":
                    finalize_article()
                    state = "SECTION"
                continue

            # Category article heading
            m = CATEGORY_HEADING.match(line)
            if m:
                finalize_article()
                cat = m.group(1)
                title = m.group(2).strip()
                source = m.group(3).strip()
                date = m.group(4).strip()
                current_article = ParsedArticle(
                    category=cat,
                    title=title,
                    source=source,
                    date=date,
                    section=current_section_id,
                    subsection=current_subsection,
                )
                state = "ARTICLE"
                continue

            # Non-category H3 = subsection label
            m2 = SUBSECTION_HEADING.match(line)
            if m2 and state == "SECTION":
                current_subsection = m2.group(1).strip()
                continue

            # Article field lines
            if state == "ARTICLE" and current_article:
                ms = SUMMARY_BOLD.match(line)
                if ms:
                    flush_field()
                    current_field = "summary"
                    current_field_lines = [ms.group(1).strip()] if ms.group(1).strip() else []
                    continue
                mw = WHAT_BOLD.match(line)
                if mw:
                    flush_field()
                    current_field = "what"
                    current_field_lines = [mw.group(1).strip()] if mw.group(1).strip() else []
                    continue
                mwhy = WHY_BOLD.match(line)
                if mwhy:
                    flush_field()
                    current_field = "why"
                    current_field_lines = [mwhy.group(1).strip()] if mwhy.group(1).strip() else []
                    continue
                msw = SOWHAT_BOLD.match(line)
                if msw:
                    flush_field()
                    current_field = "so_what"
                    current_field_lines = [msw.group(1).strip()] if msw.group(1).strip() else []
                    continue
                ml = LINK_MD.match(line)
                if ml:
                    flush_field()
                    url, label = _extract_link(ml.group(1).strip())
                    current_article.link_url = url
                    current_article.link_text = label
                    continue
                mc = CONF_LINE.match(line)
                if mc:
                    flush_field()
                    current_article.confidence = mc.group(1)
                    continue
                if current_field:
                    current_field_lines.append(line)
                    continue

    finalize_article()
    finalize_section()
    finalize_source()
    return result


# ── Legacy helpers (kept for fallback / normalization) ─────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="daily-news.md を index.html テンプレートで HTML 化する。"
    )
    parser.add_argument("--date", help="対象日（YYYY-MM-DD）。未指定時はタイムゾーンの当日。")
    parser.add_argument("--timezone", default="Asia/Tokyo", help="IANAタイムゾーン名。")
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="入力Markdown探索ルート（デフォルト: reports/daily-news）。",
    )
    parser.add_argument(
        "--input",
        help="入力Markdownファイル。未指定時は output-root/date/daily-news.md を使う。",
    )
    parser.add_argument(
        "--output",
        help="出力HTMLファイル。未指定時は入力Markdownと同じディレクトリの index.html。",
    )
    parser.add_argument(
        "--template",
        default=str(DEFAULT_TEMPLATE),
        help="HTMLテンプレートファイル（プレースホルダ必須）。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="既存の index.html を上書きする。",
    )
    parser.add_argument(
        "--articles-json",
        default="[]",
        help="ナビゲーション用JSON配列 [{date,title,path},...] 。",
    )
    return parser.parse_args()


def resolve_target_date(date_arg: str | None, timezone: str) -> str:
    if date_arg:
        dt.datetime.strptime(date_arg, "%Y-%m-%d")
        return date_arg
    now = dt.datetime.now(ZoneInfo(timezone))
    return now.strftime("%Y-%m-%d")


def resolve_path(path: str) -> Path:
    return Path(path).expanduser().resolve()


def resolve_paths(args: argparse.Namespace, target_date: str) -> tuple[Path, Path, Path]:
    template_path = resolve_path(args.template)

    if args.input:
        markdown_path = resolve_path(args.input)
    else:
        markdown_path = resolve_path(args.output_root) / target_date / "daily-news.md"

    if args.output:
        output_path = resolve_path(args.output)
    else:
        output_path = markdown_path.parent / "index.html"

    return markdown_path, output_path, template_path


def normalize_report_markdown(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    out: list[str] = []
    for raw in lines:
        stripped = raw.strip()

        if stripped == "## AIデイリーニュース":
            out.append("## AI ニュース")
            continue
        if stripped == "## 半導体デイリーニュース":
            out.append("## 半導体ニュース")
            continue

        if ARTICLE_NUMBER_HEADING.match(stripped):
            out.append(raw)
            continue

        title_match = TITLE_LINE.match(stripped)
        if title_match:
            if out and ARTICLE_NUMBER_HEADING.match(out[-1].strip()):
                out[-1] = f"### {title_match.group(1).strip()}"
            continue

        summary_match = SUMMARY_LINE.match(stripped)
        if summary_match:
            out.append(f"**ひとことサマリー（1文）**: {summary_match.group(1).strip()}")
            continue

        if stripped in {"- 記事全体の内容:", "記事全体の内容:"}:
            continue

        what_match = WHAT_LINE.match(stripped)
        if what_match:
            out.append(f"**何が起きたか（What）**: {what_match.group(1).strip()}")
            continue

        why_match = WHY_LINE.match(stripped)
        if why_match:
            out.append(f"**なぜ重要か（Why it matters）**: {why_match.group(1).strip()}")
            continue

        sowhat_match = SOWHAT_LINE.match(stripped)
        if sowhat_match:
            out.append(f"**自分への影響（So what）**: {sowhat_match.group(1).strip()}")
            continue

        link_match = LINK_LINE.match(stripped)
        if link_match:
            link_value = link_match.group(1).strip()
            if link_value.startswith("["):
                out.append(f"- リンク: {link_value}")
            elif re.match(r"^https?://\S+$", link_value):
                out.append(f"- リンク: [{link_value}]({link_value})")
            else:
                out.append(f"- リンク: {link_value}")
            continue

        if stripped.startswith("- ソース種別（公式/コミュニティ）:"):
            continue
        if stripped.startswith("- アクセス日:"):
            continue
        if stripped.startswith("- 公開日:"):
            continue
        if stripped.startswith("- ここから考えられること:"):
            out.append(stripped.replace("- ここから考えられること:", "- 補足:"))
            continue

        out.append(raw)

    return "\n".join(out).strip() + "\n"


def convert_inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(
        r"\[([^\]]+)\]\((https?://[^\s)]+)\)",
        r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>',
        escaped,
    )
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    return escaped


def markdown_to_html(markdown_text: str) -> str:
    lines = markdown_text.splitlines()
    out: list[str] = []
    in_ul = False
    in_ol = False
    in_blockquote = False
    in_code = False
    code_lines: list[str] = []

    def close_lists() -> None:
        nonlocal in_ul, in_ol
        if in_ul:
            out.append("</ul>")
            in_ul = False
        if in_ol:
            out.append("</ol>")
            in_ol = False

    def close_blockquote() -> None:
        nonlocal in_blockquote
        if in_blockquote:
            out.append("</blockquote>")
            in_blockquote = False

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()

        if stripped.startswith("```"):
            close_lists()
            close_blockquote()
            if not in_code:
                in_code = True
                code_lines = []
            else:
                out.append("<pre><code>")
                out.append(html.escape("\n".join(code_lines)))
                out.append("</code></pre>")
                in_code = False
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not stripped:
            close_lists()
            close_blockquote()
            continue

        if re.fullmatch(r"-{3,}", stripped):
            close_lists()
            close_blockquote()
            out.append("<hr />")
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading:
            close_lists()
            close_blockquote()
            level = len(heading.group(1))
            out.append(f"<h{level}>{convert_inline(heading.group(2))}</h{level}>")
            continue

        if stripped.startswith("> "):
            close_lists()
            if not in_blockquote:
                out.append("<blockquote>")
                in_blockquote = True
            out.append(f"<p>{convert_inline(stripped[2:].strip())}</p>")
            continue
        close_blockquote()

        ul = re.match(r"^-\s+(.+)$", stripped)
        if ul:
            if not in_ul:
                close_lists()
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{convert_inline(ul.group(1))}</li>")
            continue

        ol = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ol:
            if not in_ol:
                close_lists()
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{convert_inline(ol.group(1))}</li>")
            continue

        close_lists()
        out.append(f"<p>{convert_inline(stripped)}</p>")

    if in_code:
        out.append("<pre><code>")
        out.append(html.escape("\n".join(code_lines)))
        out.append("</code></pre>")

    close_lists()
    close_blockquote()
    return "\n".join(out)


def extract_title(markdown_text: str, fallback_date: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()
    return f"デイリーAI・半導体ニュース（{fallback_date}）"


def markdown_to_plain_text(text: str) -> str:
    plain = text.strip()
    plain = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r"\1", plain)
    plain = re.sub(r"`([^`]+)`", r"\1", plain)
    plain = re.sub(r"\*\*([^*]+)\*\*", r"\1", plain)
    plain = re.sub(r"\*([^*]+)\*", r"\1", plain)
    plain = re.sub(r"^\s*[-*]\s+", "", plain)
    plain = re.sub(r"\s+", " ", plain)
    return plain.strip()


def extract_description(markdown_text: str, fallback: str) -> str:
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            continue
        if stripped.startswith("-"):
            continue
        if stripped.startswith(">"):
            continue
        plain = markdown_to_plain_text(stripped)
        if plain:
            return plain[:120]
    return markdown_to_plain_text(fallback)[:120]


def render_template(
    template: str,
    *,
    page_title: str,
    page_date: str,
    generated_at: str,
    description: str,
    content_html: str,
    articles_json: str = "",
) -> str:
    required = ("{{PAGE_TITLE}}", "{{GENERATED_AT}}", "{{CONTENT_HTML}}")
    missing = [token for token in required if token not in template]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"テンプレートの必須プレースホルダが不足: {joined}")

    rendered = template
    rendered = rendered.replace("{{PAGE_TITLE}}", html.escape(page_title))
    rendered = rendered.replace("{{PAGE_DATE}}", html.escape(page_date))
    rendered = rendered.replace("{{GENERATED_AT}}", html.escape(generated_at))
    rendered = rendered.replace("{{DESCRIPTION}}", html.escape(description))
    rendered = rendered.replace("{{CONTENT_HTML}}", content_html)
    if articles_json and "{{ARTICLES_JSON}}" in rendered:
        rendered = rendered.replace("{{ARTICLES_JSON}}", articles_json)
    return rendered


def write_output(path: Path, content: str, overwrite: bool) -> str:
    if path.exists() and not overwrite:
        return f"スキップ {path}（既に存在します。上書きするには --overwrite を使用）"
    path.write_text(content, encoding="utf-8")
    return f"書き込み {path}"


def main() -> int:
    args = parse_args()
    target_date = resolve_target_date(args.date, args.timezone)
    markdown_path, output_path, template_path = resolve_paths(args, target_date)

    if not markdown_path.exists():
        raise SystemExit(f"入力Markdownが見つかりません: {markdown_path}")
    if not template_path.exists():
        raise SystemExit(f"テンプレートが見つかりません: {template_path}")

    markdown_text_raw = markdown_path.read_text(encoding="utf-8")
    markdown_text = normalize_report_markdown(markdown_text_raw)
    template_text = template_path.read_text(encoding="utf-8")

    # Build articles_json string for navigation
    try:
        articles_db = json.loads(args.articles_json)
        if not isinstance(articles_db, list):
            articles_db = []
    except (json.JSONDecodeError, AttributeError):
        articles_db = []
    articles_json_str = "const ARTICLES_DB = " + json.dumps(articles_db, ensure_ascii=False) + ";"

    # Try structured parsing first, fall back to generic converter
    parsed = parse_structured_markdown(markdown_text)
    if parsed.get("sections") or parsed.get("highlights"):
        content_html = render_structured_html(parsed)
        page_title = parsed.get("page_title") or extract_title(markdown_text, target_date)
    else:
        content_html = markdown_to_html(markdown_text)
        page_title = extract_title(markdown_text, target_date)

    description = extract_description(markdown_text, page_title)
    generated_at = dt.datetime.now(ZoneInfo(args.timezone)).strftime("%Y-%m-%d %H:%M:%S")

    html_doc = render_template(
        template_text,
        page_title=page_title,
        page_date=target_date,
        generated_at=generated_at,
        description=description,
        content_html=content_html,
        articles_json=articles_json_str,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(write_output(output_path, html_doc, args.overwrite))
    print(f"Markdown保持 {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
