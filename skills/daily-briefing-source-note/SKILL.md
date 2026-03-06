---
name: daily-briefing-source-note
description: note検索（複数クエリ）でAI/半導体記事を収集し、公開日を個別確認してカテゴリD候補をJSON化する。収集失敗が起きやすいnoteを独立サブエージェントで扱うときに使う。
---

# Daily Briefing Source note

## Overview

- note特有の取りこぼしを減らすため、固定クエリを複数実行する。
- 最低1件を最終候補にし、候補不足時の試行履歴を残す。
- 検索URLは探索専用。`items[].url` には実記事URLのみを入れる。

## Queries

- `https://note.com/search?q=生成AI&sort=new`
- `https://note.com/search?q=Claude+Code&sort=new`
- `https://note.com/search?q=LLM&sort=new`
- `https://note.com/search?q=Cursor+AI&sort=new`
- `https://note.com/search?q=AI開発&sort=new`
- `https://note.com/search?q=NVIDIA&sort=new`
- `https://note.com/search?q=半導体&sort=new`

## Workflow

1. 各クエリで20件以上を見て公開日を確認する。
   - `article:published_time` がない場合は `datePublished` と `<time datetime>` から公開日を抽出する。
2. 48時間で不足する場合は 7日→14日へ拡大する。
3. 検索結果から実記事URL（`/n/` 形式）を抽出する。
4. 最終1件以上を選び、本文取得不可は明示する。
5. `what` / `why` / `so_what` は本文の言い換えで書く。著者名・日付・冒頭段落の貼り付けは禁止する。
6. `what` / `why` / `so_what` に `記事内では「...」` のような長い引用テンプレートや、他記事にもそのまま流用できる定型文を使わない。
7. `so_what` では、その記事が示す論点を読者の運用・学習・導入判断へどう接続するかを具体的に書く。
8. フォールバックを全試行して0件なら理由を残す。

## URL Rules (必須)

- 許可: `https://note.com/<creator>/n/<note_id>` の形式。
- 禁止: `https://note.com/search?...` などの検索/一覧URL。
- 候補URLが禁止パターンの場合は選定対象から除外する。
- 本文取得後に `og:url` があればそのURLを正規URLとして採用する。

## Output

`reports/daily-news/YYYY-MM-DD/research/sources/note.json` に保存する。

```json
{
  "source": "note",
  "date": "YYYY-MM-DD",
  "items": [
    {
      "title": "string",
      "url": "https://note.com/<creator>/n/<id>",
      "published_at": "YYYY-MM-DD",
      "segment": "ai|semiconductor",
      "what": "本文を要約した2〜4文。転載禁止",
      "why": "重要性を要約した1〜3文。転載禁止",
      "so_what": "読者の運用・学習・導入判断への影響を要約した1〜2文。転載禁止",
      "confidence": "high|medium|low"
    }
  ],
  "attempt_log": []
}
```

## Validation

```bash
jq -r '.items[].url' reports/daily-news/YYYY-MM-DD/research/sources/note.json \
  | rg -n 'https://note.com/search\\?'
```

- 上記コマンドが1行でも返したらNG。実記事URLに修正してから統合する。
