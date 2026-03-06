---
name: daily-briefing-subagent-orchestrator
description: AI・半導体の日次ニュース作成を、ソース別サブエージェントに分割して実行し、最終的に daily-news.md 作成→HTML生成→GitHub Pages公開（commit/push）まで一気通貫で進める。コンテキスト量を抑えて収集精度を上げたいときに使う。
---

# Daily Briefing Subagent Orchestrator

## Overview

- 親エージェントは統合と品質管理に専念する。
- 収集はソース別Skillを読むサブエージェントへ分離する。
- 各サブエージェント成果物を統合して `daily-news.md` を作成し、HTML化して `docs/` へ反映し、commit/pushまで完了させる。
- 再発防止ルールは `$daily-briefing-regression-guards` に分離しているため、実行前に必ず読む。

## Workflow

1. `$daily-briefing-regression-guards` を先に読み、当日実行で守るべきGuardを確認する。
2. 対象日を決める（既定: `Asia/Tokyo` の当日）。
3. `reports/daily-news/YYYY-MM-DD/research/sources/` を作成する。
4. 以下を独立サブエージェントで並列収集し、JSONを保存する。
   - `$daily-briefing-source-official-ai` -> `official-ai.json`
   - `$daily-briefing-source-official-semiconductor` -> `official-semiconductor.json`
   - `$daily-briefing-source-zenn` -> `zenn.json`
   - `$daily-briefing-source-note` -> `note.json`
   - `$daily-briefing-source-reddit` -> `reddit.json`
   - `$daily-briefing-source-hacker-news` -> `hacker-news.json`
5. 親エージェントで重複URLを除去し、カテゴリ最低件数を満たすように最終選定する。
   - このときカテゴリC/DのURLを検証し、検索/一覧URLを除外する。
6. `reports/daily-news/YYYY-MM-DD/daily-news.md` を生成する。
   - `## 今日のハイライト（3選）` を必ず記載し、対象日の内容に更新する（前日流用禁止）。
7. `python3 /Users/tatsuru/Desktop/daily/skills/daily-news-md-to-html/scripts/render_markdown_to_html.py --date YYYY-MM-DD --timezone Asia/Tokyo --overwrite` を実行する。
8. `python3 /Users/tatsuru/Desktop/daily/skills/daily-briefing-publish-pages/scripts/publish_daily_briefing.py --date YYYY-MM-DD --timezone Asia/Tokyo --commit --push` を実行して `docs/` 反映から公開完了まで実行する。
   - `--push` が失敗した場合はその実行を失敗として扱い、原因（DNS/auth/remote）を解消して再実行する。

## Done 条件

- `reports/daily-news/YYYY-MM-DD/daily-news.md` と `index.html` が生成済み。
- `docs/daily-news/YYYY-MM-DD/` が更新済み。
- Git リモートへ push 済み（GitHub Pagesで参照可能）。

## Subagent Output Contract

各ソースSkillの出力は次のJSON構造に揃える。

```json
{
  "source": "official-ai",
  "date": "YYYY-MM-DD",
  "items": [
    {
      "title": "string",
      "url": "https://...",
      "published_at": "YYYY-MM-DD",
      "segment": "ai|semiconductor",
      "what": "string",
      "why": "string",
      "confidence": "high|medium|low"
    }
  ]
}
```

## Quality Gate

- 期間は 48時間を優先し、不足時は 7日→14日へ拡張する。
- 推測補完を禁止する。本文取得不可は明示し、確信度を下げる。
- 最終 `daily-news.md` は各記事に `What/Why/So what` を含める。
- `## 今日のハイライト（3選）` を必須にし、3項目すべて当日の選定記事に基づいて書く（前日と同一文面を禁止）。
- `What/Why/So what` は短文禁止。各項目は最低60文字以上で、結論だけでなく根拠（事実・背景・影響）を明示する。
- 記事件数の下限: AI 8件以上、半導体 5件以上。
- `## ソース一覧` を必須にし、各ソースに公開日/確認日/種別/URLを記載する。
- カテゴリC（Zenn）URLは `https://zenn.dev/<user>/articles/<slug>` のみ許可する。`/search` `/topics` `/api` は禁止する。
- カテゴリD（note）URLは `https://note.com/<creator>/n/<id>` のみ許可する。`/search` は禁止する。
- カテゴリF（Hacker News）は `news.ycombinator.com/item?...` を最終リンクとして禁止し、外部記事URLを採用する。
- カテゴリC/Dの採用URLは実在確認（HTTP 200系）を行い、404を含めない。
- 公式カテゴリA/BでもポータルURL（例: `github.blog/changelog/`, `huggingface.co/blog`, `nvidianews.nvidia.com/`, `amd.com/en/newsroom.html`, `news.samsung.com/.../tag/...`）を最終リンクに使わず、個別記事URLを採用する。

実行前チェック（0件であること）:

```bash
jq -r '.items[].url' reports/daily-news/YYYY-MM-DD/research/sources/zenn.json \
  | rg -n 'https://zenn.dev/(search\\?|topics/|api/)'
jq -r '.items[].url' reports/daily-news/YYYY-MM-DD/research/sources/note.json \
  | rg -n 'https://note.com/search\\?'
rg -n 'zenn.dev/(search\\?|topics/|api/)|note.com/search\\?' \
  reports/daily-news/YYYY-MM-DD/daily-news.md
```
