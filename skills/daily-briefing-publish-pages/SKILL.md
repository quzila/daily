---
name: daily-briefing-publish-pages
description: daily-ai-semiconductor-briefing で daily-news.md を作成し、daily-news-md-to-html で index.html を生成したうえで、docs 配下へ反映して GitHub Pages に公開する一連の流れを実行する。日次レポートを作成から公開まで一気通貫で回すときに使う。
---

# Daily Briefing Publish Pages

## Overview

- 日次レポートの公開フローを統合するスキル。
- `daily-news.md` 作成（収集）→ HTML生成 → GitHub Pages公開の順で実行する。

## Prerequisites

- GitHub Pages の公開元が `main` ブランチの `/docs` に設定済みであること。
- リポジトリで push 可能な権限があること。
- 収集処理では `$daily-ai-semiconductor-briefing`、HTML化では `$daily-news-md-to-html` を使う。

## Workflow

1. `$daily-ai-semiconductor-briefing` で対象日の `daily-news.md` を作成する。
2. `$daily-news-md-to-html` で同日の `index.html` を生成する。
3. 公開前にフォーマット品質を確認する（`### 記事1` のような連番見出しが残っていないか、`What/Why/So what` が全記事にあり、各ブロックが十分な文量か）。
4. `scripts/publish_daily_briefing.py` で `docs/` へ反映し、必要なら commit/push する。

## Quick Commands

対象日を生成して docs 反映のみ（commit/pushしない）:

```bash
python3 /Users/tatsuru/Desktop/daily/skills/daily-briefing-publish-pages/scripts/publish_daily_briefing.py --date YYYY-MM-DD --timezone Asia/Tokyo
```

対象日を docs 反映 + commit + push:

```bash
python3 /Users/tatsuru/Desktop/daily/skills/daily-briefing-publish-pages/scripts/publish_daily_briefing.py --date YYYY-MM-DD --timezone Asia/Tokyo --commit --push
```

HTML生成済みの場合（再レンダリングしない）:

```bash
python3 /Users/tatsuru/Desktop/daily/skills/daily-briefing-publish-pages/scripts/publish_daily_briefing.py --date YYYY-MM-DD --skip-render --commit --push
```

公開前の軽量チェック:

```bash
rg -n "^### 記事[0-9]+$|\\*\\*何が起きたか（What）\\*\\*|\\*\\*なぜ重要か（Why it matters）\\*\\*|\\*\\*自分への影響（So what）\\*\\*" \
  /Users/tatsuru/Desktop/daily/reports/daily-news/YYYY-MM-DD/daily-news.md
```

## Script Behavior

- 入力:
  - `reports/daily-news/YYYY-MM-DD/daily-news.md`
  - `reports/daily-news/YYYY-MM-DD/index.html`
  - `assets/archive-index.html`（`docs/daily-news/index.html` 用テンプレート）
- 出力:
  - `docs/daily-news/YYYY-MM-DD/index.html`
  - `docs/daily-news/YYYY-MM-DD/daily-news.md`
  - `docs/index.html`（最新日へのリダイレクト）
  - `docs/daily-news/index.html`（モダンUIのアーカイブ一覧。最新号・件数・カード要約を自動更新）

## Notes

- `--push` は `--commit` を前提に動作する（指定時は自動で commit も実行）。
- GitHub Pages 側の反映は push 後に数分かかる場合がある。
- アーカイブページのデザインを変更したい場合は `assets/archive-index.html` を編集する。`docs/daily-news/index.html` の直接編集は次回 publish で上書きされる。
- publish前に `daily-news.md` の `- リンク:` を検証し、`zenn.dev/search` / `zenn.dev/topics` / `zenn.dev/api` / `note.com/search` が残っている場合はエラーで停止する。
- publish時に品質ゲートを実行する。次を満たさない場合は公開を停止する:
  - AI記事 8件以上 / 半導体記事 5件以上
  - 各記事に `What/Why/So what` が存在し、各項目が最低文量を満たす
  - `## ソース一覧` セクションにメタ情報とURLが存在する
  - Zenn/note記事URLは正規形式かつ到達可能（404不可）
- `commit` 実行時に `detached HEAD` だった場合は自動で `codex/automation-rescue-YYYYMMDD-HHMMSS` ブランチを作成してからコミットする。
- `push` 実行前に `github.com` のDNS解決と `git ls-remote <remote> HEAD` を検査し、失敗時はスキップせずエラーで終了する（毎回pushを担保）。
