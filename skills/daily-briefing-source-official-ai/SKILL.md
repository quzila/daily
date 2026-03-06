---
name: daily-briefing-source-official-ai
description: 公式AIソース（OpenAI, Anthropic, Google, Meta, Hugging Face, GitHub Changelog）を巡回し、本文確認ベースで直近ニュース候補を抽出してJSON化する。日次ブリーフィングのカテゴリA収集を分離したいときに使う。
---

# Daily Briefing Source Official AI

## Overview

- 公式AIソースだけを対象に収集する。
- 最低2件を最終候補として返し、本文根拠を残す。

## Sources

- `https://github.blog/changelog/`
- `https://openai.com/blog/`
- `https://help.openai.com/en/articles/6825453-chatgpt-release-notes`
- `https://www.anthropic.com/news`
- `https://blog.google/technology/ai/`
- `https://ai.meta.com/blog/`
- `https://huggingface.co/blog`

## Workflow

1. 48時間以内の記事を優先して候補を集める。
2. 本文を取得し、`what` / `why` / `so_what` を事実ベースで記述する。
   - 記事導入文の貼り付けは禁止し、自分の言葉で要点を圧縮する。
   - `so_what` では、API挙動・評価手順・既存ワークフローのどこを見直すべきかを具体化する。
3. 候補が不足したら対象期間を 7日→14日に拡大する。
4. 最終2件以上を選ぶ。本文未取得は `confidence=low` とする。

## Output

`reports/daily-news/YYYY-MM-DD/research/sources/official-ai.json` に保存する。

```json
{
  "source": "official-ai",
  "date": "YYYY-MM-DD",
  "items": [
    {
      "title": "string",
      "url": "https://...",
      "published_at": "YYYY-MM-DD",
      "segment": "ai",
      "what": "string",
      "why": "string",
      "so_what": "string",
      "confidence": "high|medium|low"
    }
  ]
}
```
