#!/usr/bin/env python3
"""Render daily-news.md to index.html with a reusable HTML template."""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_OUTPUT_ROOT = Path("daily-ai-semiconductor-briefing") / "daily-news"
DEFAULT_TEMPLATE = Path(__file__).resolve().parent.parent / "assets" / "index.html"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="daily-news.md を index.html テンプレートで HTML 化する。"
    )
    parser.add_argument("--date", help="対象日（YYYY-MM-DD）。未指定時はタイムゾーンの当日。")
    parser.add_argument("--timezone", default="Asia/Tokyo", help="IANAタイムゾーン名。")
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="入力Markdown探索ルート（デフォルト: daily-ai-semiconductor-briefing/daily-news）。",
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
    generated_at: str,
    description: str,
    content_html: str,
) -> str:
    required = ("{{PAGE_TITLE}}", "{{GENERATED_AT}}", "{{CONTENT_HTML}}")
    missing = [token for token in required if token not in template]
    if missing:
        joined = ", ".join(missing)
        raise ValueError(f"テンプレートの必須プレースホルダが不足: {joined}")

    rendered = template
    rendered = rendered.replace("{{PAGE_TITLE}}", html.escape(page_title))
    rendered = rendered.replace("{{GENERATED_AT}}", html.escape(generated_at))
    rendered = rendered.replace("{{DESCRIPTION}}", html.escape(description))
    rendered = rendered.replace("{{CONTENT_HTML}}", content_html)
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

    markdown_text = markdown_path.read_text(encoding="utf-8")
    template_text = template_path.read_text(encoding="utf-8")

    page_title = extract_title(markdown_text, target_date)
    description = extract_description(markdown_text, page_title)
    content_html = markdown_to_html(markdown_text)
    generated_at = dt.datetime.now(ZoneInfo(args.timezone)).strftime("%Y-%m-%d %H:%M:%S")

    html_doc = render_template(
        template_text,
        page_title=page_title,
        generated_at=generated_at,
        description=description,
        content_html=content_html,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(write_output(output_path, html_doc, args.overwrite))
    print(f"Markdown保持 {markdown_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
