---
name: daily-news-md-to-html
description: daily-news.md を保持したまま、2026-03-01版のランディング体裁（dark editorial）をテンプレート化した assets/index.html に差し込んで index.html を生成する。daily-ai-semiconductor-briefing で Markdown 作成後に公開用HTMLを作るときに使う。
---

# Daily News MD to HTML

## Overview
- `daily-news.md` を読み取り、3/1の `index.html` デザインをテンプレート化した `assets/index.html` に `{{CONTENT_HTML}}` とメタ情報を差し込んで `index.html` を生成する。
- 記事見出しが `### 記事1` のような簡略形式でも、レンダラ側で記事タイトル行を復元してカード化表示する（3/1体裁に寄せる）。
- 入力Markdownは上書きしない。RAG用途のため `daily-news.md` は必ず残す。

## Workflow
1. `daily-news.md` の保存先を確認する。
2. `scripts/render_markdown_to_html.py` を実行して `index.html` を生成する。
3. `daily-news.md` が残っていることと、`index.html` が更新されていることを確認する。

## Quick Commands
- 当日分を変換（デフォルト構成）:
```bash
python3 /Users/tatsuru/Desktop/daily/skills/daily-news-md-to-html/scripts/render_markdown_to_html.py --date YYYY-MM-DD --timezone Asia/Tokyo --overwrite
```

- 任意のMarkdownを変換:
```bash
python3 /Users/tatsuru/Desktop/daily/skills/daily-news-md-to-html/scripts/render_markdown_to_html.py \
  --input /abs/path/daily-news.md \
  --output /abs/path/index.html \
  --template /Users/tatsuru/Desktop/daily/skills/daily-news-md-to-html/assets/index.html \
  --overwrite
```

## Script Behavior
- デフォルト入力: `reports/daily-news/YYYY-MM-DD/daily-news.md`
- デフォルト出力: 入力Markdownと同じフォルダの `index.html`
- テンプレート必須プレースホルダ:
  - `{{PAGE_TITLE}}`
  - `{{GENERATED_AT}}`
  - `{{CONTENT_HTML}}`
- オプションプレースホルダ:
  - `{{DESCRIPTION}}`

## Notes
- Markdownは読み取り専用で扱う。`daily-news.md` を削除・移動しない。
- 既存 `index.html` を更新する場合は `--overwrite` を付ける。
- テンプレートをカスタマイズする場合は `assets/index.html` を編集してから再実行する。
- 現在の標準テンプレートは `reports/daily-news/2026-03-01/index.html` の体裁をベースにしている。
- 期待フォーマットは `### 【カテゴリ...】記事タイトル（出典名, YYYY-MM-DD）`。この形式を優先すると記事カード化が最も安定する。
- モバイル崩れ防止のため、記事カードのリンク表示は URL 直表示を避ける（レンダラは URL ラベルを `→ 元記事を読む` に正規化する）。
- 生成後は `rg -n 'class=\"card-link\">https?://' reports/daily-news/YYYY-MM-DD/index.html` で URL 直表示リンクが残っていないことを確認する。
