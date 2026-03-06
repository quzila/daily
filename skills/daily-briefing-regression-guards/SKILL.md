---
name: daily-briefing-regression-guards
description: デイリーAI・半導体ブリーフィングの再発防止ルール集。記事の前日流用防止、公式ソース復帰、Zenn/note鮮度維持、publish時のネットワーク制約対応を定義する。
---

# Daily Briefing Regression Guards

## Overview

- 日次レポート生成で発生した不具合の再発防止ルールをまとめた補助Skill。
- 既存Skillが長文化したため、運用更新ルールはこのSkillへ集約する。
- `$daily-briefing-subagent-orchestrator` / `$daily-ai-semiconductor-briefing` 実行時に先に読む。

## Guard 1: 前日流用の禁止

- `daily-news.md` は前日ファイルを複製せず、当日 `research/selected-with-body.json` から再生成する。
- 同一タイトルの本文ブロックが前日と完全一致する状態を禁止する。
- 前日コピーが必要な緊急フォールバック時でも、最終的には当日候補から再レンダリングし直す。

検証コマンド例:

```bash
python3 - <<'PY'
import pathlib,re
base=pathlib.Path('reports/daily-news')
pat=re.compile(r'^###\s+【カテゴリ[^】]+】(.+?)（[^）]+）\s*$')

def blocks(d):
    lines=(base/d/'daily-news.md').read_text(encoding='utf-8').splitlines()
    i=0; out={}
    while i<len(lines):
        m=pat.match(lines[i].strip())
        if not m:
            i+=1; continue
        title=m.group(1).strip()
        j=i+1; buf=[]
        while j<len(lines) and not (pat.match(lines[j].strip()) or lines[j].startswith('## ') or lines[j]=='---'):
            buf.append(lines[j]); j+=1
        out[title]='\n'.join(buf).strip(); i=j
    return out

b_prev=blocks('YYYY-MM-DD')
b_cur=blocks('YYYY-MM-DD')
common=set(b_prev)&set(b_cur)
unchanged=[t for t in common if b_prev[t]==b_cur[t]]
print('unchanged_blocks',len(unchanged))
PY
```

## Guard 2: Zenn / note 鮮度維持

- Zenn収集は `trend` だけに依存せず、`trend + latest` を併用する。
- note収集は `sort=new` の複数クエリを実行する。
- note公開日は `article:published_time` 不在を想定し、`datePublished` と `<time datetime>` も読む。
- AI選定では `Zenn >= 2件` / `note >= 1件` を優先採用の下限として確保する。

## Guard 3: 公式ソースの復帰

- レポート生成時に `research/sources/official-ai.json` と `official-semiconductor.json` を補助入力として取り込む。
- 公式カテゴリA/Bを空欄化しない（候補がある限り採用する）。
- ただしポータル/一覧URLは禁止し、個別記事URLのみ採用する。

禁止URL例:

- `https://openai.com/news/`
- `https://github.blog/changelog/`
- `https://huggingface.co/blog`
- `https://nvidianews.nvidia.com/`
- `https://www.amd.com/en/newsroom.html`

## Guard 4: 生成文の自然さ

- 生成文に日付固定プレフィックスを付けない。
- 次の表現は禁止:
  - `YYYY-MM-DDの収集で ...`
  - `本日（YYYY-MM-DD）の収集では ...`
- 代わりに主語をソース/記事に置いた自然な文へ変換する。

## Guard 5: Publish時ネットワーク制約

- publish品質ゲートで Zenn/note URL検証は形式チェックを必須とする。
- DNS制限で `socket.gaierror` が発生する環境では、到達確認はスキップして失敗にしない。
- 404/形式不正/禁止URLは従来どおり失敗にする。

## Run Checklist

1. `collect_daily_news_inputs.py` 実行後、`selected-with-body.json` に当日候補が入っていることを確認。
2. `create_daily_news_files.py` で `daily-news.md` を再生成。
3. 以下が0件であることを確認:

```bash
rg -n 'の収集で|本日（[0-9]{4}-[0-9]{2}-[0-9]{2}）の収集では' \
  reports/daily-news/YYYY-MM-DD/daily-news.md
```

4. 公式カテゴリが存在することを確認:

```bash
rg -n 'カテゴリA: 公式ソース（AI）|カテゴリB: 公式ソース（半導体）' \
  reports/daily-news/YYYY-MM-DD/daily-news.md
```

5. `publish_daily_briefing.py --commit --push` まで実行。

## Update Policy

- 新しい再発事象が出たら、このSkillに「Guard」を追加してからスクリプトを修正する。
- 既存の巨大Skill本体には要約と参照のみを残し、詳細は本Skillへ追記する。
