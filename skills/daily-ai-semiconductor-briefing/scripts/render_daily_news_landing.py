#!/usr/bin/env python3
"""daily-news.md からランディングページ（index.html）を生成する。"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import re
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_OUTPUT_ROOT = Path("reports") / "daily-news"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="daily-news.md から index.html を生成する。"
    )
    parser.add_argument("--date", help="対象日（YYYY-MM-DD）。未指定時はタイムゾーンの当日。")
    parser.add_argument("--timezone", default="Asia/Tokyo", help="IANAタイムゾーン名。")
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="出力ルートディレクトリ（デフォルト: reports/daily-news）。",
    )
    parser.add_argument(
        "--input",
        help="入力Markdownファイルの絶対/相対パス。未指定時は output-root/date/daily-news.md。",
    )
    parser.add_argument(
        "--output",
        help="出力HTMLファイルの絶対/相対パス。未指定時は output-root/date/index.html。",
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


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise FileNotFoundError(f"repository root not found from {start}")


def convert_inline(text: str) -> str:
    escaped = html.escape(text, quote=False)
    escaped = re.sub(r"`([^`]+)`", r"<code>\1</code>", escaped)
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', escaped)
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

        heading_match = re.match(r"^(#{1,6})\s+(.+)$", stripped)
        if heading_match:
            close_lists()
            close_blockquote()
            level = len(heading_match.group(1))
            title = convert_inline(heading_match.group(2))
            out.append(f"<h{level}>{title}</h{level}>")
            continue

        if stripped.startswith("> "):
            close_lists()
            if not in_blockquote:
                out.append("<blockquote>")
                in_blockquote = True
            out.append(f"<p>{convert_inline(stripped[2:].strip())}</p>")
            continue
        close_blockquote()

        ul_match = re.match(r"^-\s+(.+)$", stripped)
        if ul_match:
            if not in_ul:
                close_lists()
                out.append("<ul>")
                in_ul = True
            out.append(f"<li>{convert_inline(ul_match.group(1))}</li>")
            continue

        ol_match = re.match(r"^\d+\.\s+(.+)$", stripped)
        if ol_match:
            if not in_ol:
                close_lists()
                out.append("<ol>")
                in_ol = True
            out.append(f"<li>{convert_inline(ol_match.group(1))}</li>")
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
        line = line.strip()
        if line.startswith("# "):
            return line[2:].strip()
    return f"デイリーAI・半導体ニュース（{fallback_date}）"


def build_html_document(
    *,
    page_title: str,
    article_html: str,
    generated_at: str,
) -> str:
    escaped_title = html.escape(page_title)
    return f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{escaped_title}</title>
  <meta name="description" content="AI・半導体ニュースの日次ランディングページ" />
  <style>
    :root {{
      --bg: #f3efe7;
      --bg-accent: radial-gradient(circle at 10% 10%, #ffd9a8 0, #f3efe7 45%),
                   radial-gradient(circle at 90% 5%, #b7d8ff 0, #f3efe7 55%);
      --paper: #fffdf9;
      --ink: #1f2933;
      --muted: #5f6b76;
      --edge: #d8d0c4;
      --brand: #0f766e;
      --brand-2: #c2410c;
      --shadow: 0 12px 36px rgba(20, 24, 28, 0.08);
    }}
    * {{
      box-sizing: border-box;
    }}
    body {{
      margin: 0;
      font-family: "Noto Sans JP", "Hiragino Sans", "Yu Gothic", sans-serif;
      color: var(--ink);
      background: var(--bg-accent);
      line-height: 1.75;
      min-height: 100vh;
    }}
    .wrap {{
      max-width: 1040px;
      margin: 0 auto;
      padding: 28px 18px 64px;
    }}
    .hero {{
      border: 1px solid var(--edge);
      background: linear-gradient(120deg, #fffaf0, #f7fbff);
      border-radius: 20px;
      padding: 20px 22px;
      box-shadow: var(--shadow);
      margin-bottom: 20px;
    }}
    .badge {{
      display: inline-block;
      padding: 4px 10px;
      border-radius: 999px;
      background: #ecfeff;
      border: 1px solid #99f6e4;
      color: #115e59;
      font-size: 12px;
      letter-spacing: .04em;
      text-transform: uppercase;
      margin-bottom: 10px;
    }}
    .hero h1 {{
      margin: 0;
      font-size: clamp(26px, 4.2vw, 42px);
      line-height: 1.2;
      letter-spacing: .01em;
    }}
    .meta {{
      margin-top: 10px;
      color: var(--muted);
      font-size: 13px;
    }}
    main {{
      border: 1px solid var(--edge);
      background: var(--paper);
      border-radius: 20px;
      box-shadow: var(--shadow);
      padding: clamp(18px, 3vw, 34px);
    }}
    h2 {{
      margin-top: 32px;
      margin-bottom: 10px;
      font-size: clamp(22px, 3.2vw, 30px);
      border-left: 5px solid var(--brand);
      padding-left: 10px;
    }}
    h3 {{
      margin-top: 24px;
      margin-bottom: 8px;
      font-size: clamp(18px, 2.4vw, 22px);
      color: #0b3d3a;
    }}
    h4, h5, h6 {{
      margin-top: 18px;
      margin-bottom: 8px;
      font-size: 16px;
    }}
    p {{
      margin: 8px 0 12px;
    }}
    ul, ol {{
      margin-top: 8px;
      margin-bottom: 16px;
      padding-left: 22px;
    }}
    li {{
      margin: 4px 0;
    }}
    blockquote {{
      margin: 16px 0;
      padding: 10px 14px;
      border-left: 4px solid var(--brand-2);
      background: #fff8ec;
      border-radius: 10px;
      color: #4b3b2d;
    }}
    code {{
      font-family: "JetBrains Mono", "SFMono-Regular", Consolas, monospace;
      font-size: 0.92em;
      background: #eef2f7;
      padding: 1px 6px;
      border-radius: 6px;
    }}
    pre {{
      background: #0f172a;
      color: #f8fafc;
      padding: 14px;
      border-radius: 10px;
      overflow-x: auto;
      margin: 12px 0 18px;
    }}
    pre code {{
      background: transparent;
      padding: 0;
      color: inherit;
    }}
    a {{
      color: #0f4c81;
      text-underline-offset: 2px;
    }}
    hr {{
      border: 0;
      border-top: 1px solid #ddd4c8;
      margin: 26px 0;
    }}
    @media (max-width: 700px) {{
      .wrap {{
        padding: 16px 10px 40px;
      }}
      .hero, main {{
        border-radius: 14px;
      }}
    }}
  </style>
</head>
<body>
  <div class="wrap">
    <header class="hero">
      <span class="badge">Daily Landing</span>
      <h1>{escaped_title}</h1>
      <div class="meta">Generated: {html.escape(generated_at)} (Asia/Tokyo)</div>
    </header>
    <main>
      {article_html}
    </main>
  </div>
</body>
</html>
"""


def write_html(path: Path, content: str, overwrite: bool) -> str:
    if path.exists() and not overwrite:
        return f"スキップ {path}（既に存在します。上書きするには --overwrite を使用）"
    path.write_text(content, encoding="utf-8")
    return f"書き込み {path}"


def main() -> int:
    args = parse_args()
    target_date = resolve_target_date(args.date, args.timezone)
    repo_root = find_repo_root(Path(__file__).resolve())
    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = repo_root / output_root
    base_dir = output_root / target_date

    markdown_path = (
        Path(args.input).expanduser().resolve()
        if args.input
        else (base_dir / "daily-news.md")
    )
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else (base_dir / "index.html")
    )
    if not markdown_path.exists():
        raise SystemExit(f"入力ファイルが見つかりません: {markdown_path}")

    markdown_text = markdown_path.read_text(encoding="utf-8")
    page_title = extract_title(markdown_text, target_date)
    article_html = markdown_to_html(markdown_text)
    generated_at = dt.datetime.now(ZoneInfo(args.timezone)).strftime("%Y-%m-%d %H:%M:%S")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    html_doc = build_html_document(
        page_title=page_title,
        article_html=article_html,
        generated_at=generated_at,
    )
    print(write_html(output_path, html_doc, args.overwrite))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
