#!/usr/bin/env python3
"""日次AI・半導体ブリーフィング用の日付付きMarkdownレポートファイルを作成する。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


DAILY_TEMPLATE = """# デイリーAI・半導体ニュース ({date})

## 対象範囲
- 対象日: {date}
- タイムゾーン: {timezone}

## AIデイリーニュース

### 記事1
- タイトル:
- 30秒で読める要約:
- 記事全体の内容:
  - 事実（What）:
  - 背景（Why it matters）:
  - 影響（So what: ノジマ業務/自分の開発）:
- リンク:
- ソース種別（公式/コミュニティ）:
- 公開日:
- アクセス日:
- 確信度:

### 記事2
- タイトル:
- 30秒で読める要約:
- 記事全体の内容:
  - 事実（What）:
  - 背景（Why it matters）:
  - 影響（So what: ノジマ業務/自分の開発）:
- リンク:
- ソース種別（公式/コミュニティ）:
- 公開日:
- アクセス日:
- 確信度:

### 記事3
- タイトル:
- 30秒で読める要約:
- 記事全体の内容:
  - 事実（What）:
  - 背景（Why it matters）:
  - 影響（So what: ノジマ業務/自分の開発）:
- リンク:
- ソース種別（公式/コミュニティ）:
- 公開日:
- アクセス日:
- 確信度:

## 半導体デイリーニュース

### 記事1
- タイトル:
- 30秒で読める要約:
- 記事全体の内容:
  - 事実（What）:
  - 背景（Why it matters）:
  - 影響（So what: 価格/在庫/店頭販売）:
- リンク:
- ソース種別（公式/コミュニティ）:
- 公開日:
- アクセス日:
- 確信度:
- ここから考えられること:

### 記事2
- タイトル:
- 30秒で読める要約:
- 記事全体の内容:
  - 事実（What）:
  - 背景（Why it matters）:
  - 影響（So what: 価格/在庫/店頭販売）:
- リンク:
- ソース種別（公式/コミュニティ）:
- 公開日:
- アクセス日:
- 確信度:
- ここから考えられること:

### 記事3
- タイトル:
- 30秒で読める要約:
- 記事全体の内容:
  - 事実（What）:
  - 背景（Why it matters）:
  - 影響（So what: 価格/在庫/店頭販売）:
- リンク:
- ソース種別（公式/コミュニティ）:
- 公開日:
- アクセス日:
- 確信度:
- ここから考えられること:

## ソース
- [ソース名] (公開日: YYYY-MM-DD, アクセス日: YYYY-MM-DD): URL
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="日付付きの daily-news.md を作成する。"
    )
    parser.add_argument(
        "--date",
        help="対象日（YYYY-MM-DD形式）。デフォルトは指定タイムゾーンでの当日。",
    )
    parser.add_argument(
        "--timezone",
        default="Asia/Tokyo",
        help="IANAタイムゾーン名（デフォルト: Asia/Tokyo）。",
    )
    parser.add_argument(
        "--output-root",
        default="daily-news",
        help="出力ルートディレクトリ（デフォルト: daily-news）。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="既存のレポートファイルを上書きする。",
    )
    parser.add_argument(
        "--skip-html",
        action="store_true",
        help="index.html の生成をスキップする。",
    )
    return parser.parse_args()


def resolve_target_date(date_arg: str | None, timezone: str) -> str:
    if date_arg:
        # ISO日付形式のバリデーション（元の値は保持）。
        datetime.strptime(date_arg, "%Y-%m-%d")
        return date_arg

    now = datetime.now(ZoneInfo(timezone))
    return now.strftime("%Y-%m-%d")


def write_file(path: Path, content: str, overwrite: bool) -> str:
    if path.exists() and not overwrite:
        return f"スキップ {path}（既に存在します。上書きするには --overwrite を使用）"

    path.write_text(content, encoding="utf-8")
    return f"書き込み {path}"


def main() -> int:
    args = parse_args()
    target_date = resolve_target_date(args.date, args.timezone)

    output_dir = Path(args.output_root) / target_date
    output_dir.mkdir(parents=True, exist_ok=True)

    report_path = output_dir / "daily-news.md"
    report_content = DAILY_TEMPLATE.format(date=target_date, timezone=args.timezone)
    results = [write_file(report_path, report_content, args.overwrite)]

    if not args.skip_html:
        renderer = Path(__file__).with_name("render_daily_news_landing.py")
        cmd = [
            sys.executable,
            str(renderer),
            "--date",
            target_date,
            "--timezone",
            args.timezone,
            "--output-root",
            args.output_root,
            "--overwrite",
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if completed.returncode == 0 and completed.stdout.strip():
            results.extend(completed.stdout.strip().splitlines())
        elif completed.returncode != 0:
            err = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
            results.append(f"HTML生成に失敗: {err}")

    for line in results:
        print(line)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
