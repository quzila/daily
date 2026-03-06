---
name: daily-briefing-source-reddit
description: RedditのAI系・半導体系サブレディットを巡回し、投稿と外部リンク本文を確認してカテゴリE候補をJSON化する。コミュニティ起点の話題を独立サブエージェントで収集するときに使う。
---

# Daily Briefing Source Reddit

## Overview

- AI系と半導体系を同時に収集する。
- AI最終2件以上、半導体系最終1件以上を目標にする。

## Subreddits

- AI: `r/LocalLLaMA`, `r/MachineLearning`, `r/artificial`, `r/ClaudeAI`, `r/ChatGPT`, `r/singularity`
- 半導体: `r/hardware`, `r/Semiconductors`, `r/chipdesign`, `r/nvidia`, `r/Amd`

取得例:

- `https://www.reddit.com/r/LocalLLaMA/top/.json?t=day&limit=10`

## Workflow

1. 24時間トップを取得し、不足時は週間へ拡大する。
2. 外部リンクがある投稿はリンク先本文も確認する。
3. `what` / `why` / `so_what` は投稿文や外部記事本文を要約して書く。スレ本文や外部記事の冒頭段落を貼り付けない。
4. `so_what` では、熱量の高い論点として何を一次情報で裏取りすべきかを具体的に書く。
5. AI最終2件以上、半導体最終1件以上を選ぶ。
6. 429時は `old.reddit.com` フォールバックを使う。

## Output

`reports/daily-news/YYYY-MM-DD/research/sources/reddit.json` に保存する。

```json
{
  "source": "reddit",
  "date": "YYYY-MM-DD",
  "items": [
    {
      "title": "string",
      "url": "https://...",
      "published_at": "YYYY-MM-DD",
      "segment": "ai|semiconductor",
      "what": "投稿/外部記事を要約した2〜4文。転載禁止",
      "why": "重要性を要約した1〜3文。転載禁止",
      "so_what": "一次情報で裏取りすべき論点を要約した1〜2文。転載禁止",
      "confidence": "high|medium|low"
    }
  ]
}
```
