---
name: daily-briefing-source-hacker-news
description: Hacker Newsのトップ投稿からAI/半導体関連を抽出し、外部リンク本文確認込みでカテゴリF候補をJSON化する。低コンテキストでHN収集を切り出すときに使う。
---

# Daily Briefing Source Hacker News

## Overview

- HN上位投稿からAI/半導体関連記事を抽出する。
- 最終1件以上を返し、外部記事本文で裏取りする。

## Sources

- `https://hacker-news.firebaseio.com/v0/topstories.json`（上位30件目安）
- `https://news.ycombinator.com/`（補完）

## Workflow

1. タイトル・ポイント・リンク先を取得してAI/半導体関連を絞る。
2. リンク先本文を確認して `what/why/so_what` を作る。
   - `what/why/so_what` は本文の要点を要約する。記事冒頭の長い引用や `記事内では「...」` テンプレートは禁止する。
   - `so_what` では、HNで話題化した論点を自分の検証優先順位にどう反映するかを書く。
3. 最終1件以上を選ぶ。本文未取得は `confidence=low` にする。
4. `items[].url` には **必ず外部記事URL** を入れる。`https://news.ycombinator.com/item?id=...` は保存しない（必要なら `meta.hn_item_url` に保持）。
5. 外部URLが取得できない場合は不採用にし、`attempt_log` に理由を残す。

## Output

`reports/daily-news/YYYY-MM-DD/research/sources/hacker-news.json` に保存する。

```json
{
  "source": "hacker-news",
  "date": "YYYY-MM-DD",
  "items": [
    {
      "title": "string",
      "url": "https://...",
      "published_at": "YYYY-MM-DD",
      "segment": "ai|semiconductor",
      "what": "外部記事を要約した2〜4文。転載禁止",
      "why": "重要性を要約した1〜3文。転載禁止",
      "so_what": "検証優先順位への影響を要約した1〜2文。転載禁止",
      "confidence": "high|medium|low"
    }
  ],
  "attempt_log": []
}
```

## URL Rules (必須)

- 許可: 外部記事URL（例: ベンダー公式記事、技術ブログ、ニュース記事）。
- 禁止: `https://news.ycombinator.com/item?id=...` / `https://news.ycombinator.com/`。
