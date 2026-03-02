#!/usr/bin/env python3
"""Render daily briefing HTML and publish it to docs/ for GitHub Pages."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_TIMEZONE = "Asia/Tokyo"
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


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


def write_archive_index(docs_daily_root: Path, latest_date: str) -> None:
    candidates: list[str] = []
    for child in docs_daily_root.iterdir():
        if child.is_dir() and DATE_PATTERN.match(child.name) and (child / "index.html").exists():
            candidates.append(child.name)
    candidates.sort(reverse=True)

    items = "\n".join(
        f'    <li><a href="./{d}/index.html">{d}</a></li>' for d in candidates
    )
    html_doc = f"""<!doctype html>
<html lang="ja">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Daily Briefing Archive</title>
</head>
<body>
  <h1>Daily Briefing Archive</h1>
  <p>Latest: <a href="./{latest_date}/index.html">{latest_date}</a></p>
  <ul>
{items}
  </ul>
</body>
</html>
"""
    (docs_daily_root / "index.html").write_text(html_doc, encoding="utf-8")


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
        title = f"デイリーAI・半導体ニュース（{date}）"
        if md_file.exists():
            try:
                md_text = md_file.read_text(encoding="utf-8")
                for line in md_text.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("# "):
                        title = stripped[2:].strip()
                        break
            except Exception:
                pass
        entries.append({
            "date": date,
            "title": title,
            "path": f"/daily-news/{date}/",
        })
    entries.sort(key=lambda e: e["date"], reverse=True)
    return entries


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
