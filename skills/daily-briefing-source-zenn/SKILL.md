---
name: daily-briefing-source-zenn
description: Zennのトレンド・トピック・検索を横断してAI/LLM関連記事を収集し、本文確認済み候補をJSON化する。カテゴリCを独立サブエージェントで収集するときに使う。
---

# Daily Briefing Source Zenn

## Overview

- Zenn収集専用Skillとして動かす。
- 最終2件以上を返し、選外候補も保持する。
- 検索URL/トピックURLは探索専用。`items[].url` には実記事URLのみを入れる。

## Sources

- `https://zenn.dev/api/articles?order=trend`
- `https://zenn.dev/api/articles?order=latest`
- `https://zenn.dev/topics/llm/articles`
- `https://zenn.dev/topics/claudecode/articles`
- `https://zenn.dev/topics/cursor/articles`
- `https://zenn.dev/topics/openai/articles`
- `https://zenn.dev/topics/ai/articles`
- `https://zenn.dev/search?q=Claude&order=latest`
- `https://zenn.dev/search?q=LLM&order=latest`

## Workflow

1. 48時間以内の候補を収集する。
   - APIは `trend` と `latest` の両方を使って候補不足を防ぐ。
2. 候補不足時は 7日→14日に拡大する。
3. 候補ページ（トレンド/トピック/検索）から実記事URLを抽出する。
4. 本文を確認して最終2件以上を選ぶ。
5. 選外候補を `other_candidates` に残す。

## URL Rules (必須)

- 許可: `https://zenn.dev/<user>/articles/<slug>` のみ。
- 禁止: `https://zenn.dev/search?...` / `https://zenn.dev/topics/...` / `https://zenn.dev/api/...`。
- 候補URLが禁止パターンの場合は本文確認前に除外する。
- 本文取得後に `og:url` があればそのURLを正規URLとして採用する。

## Output

`reports/daily-news/YYYY-MM-DD/research/sources/zenn.json` に保存する。

```json
{
  "source": "zenn",
  "date": "YYYY-MM-DD",
  "items": [],
  "other_candidates": []
}
```

## Validation

```bash
jq -r '.items[].url' reports/daily-news/YYYY-MM-DD/research/sources/zenn.json \
  | rg -n 'https://zenn.dev/(search\\?|topics/|api/)'
```

- 上記コマンドが1行でも返したらNG。実記事URLに修正してから統合する。
