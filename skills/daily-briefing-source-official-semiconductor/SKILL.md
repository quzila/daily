---
name: daily-briefing-source-official-semiconductor
description: 公式半導体ソース（NVIDIA/TSMC/Intel/Samsung/AMD等）と一次情報に近い業界メディアを巡回し、本文確認ベースでカテゴリB候補をJSON化する。半導体収集を独立サブエージェントに切り出すときに使う。
---

# Daily Briefing Source Official Semiconductor

## Overview

- 公式発表と一次情報に近い媒体を優先する。
- 決算・新アーキ発表・政策ニュースを漏らさない。

## Sources

- `https://nvidianews.nvidia.com/`
- `https://pr.tsmc.com/english/news`
- `https://www.intel.com/content/www/us/en/newsroom/home.html`
- `https://news.samsung.com/semiconductor`
- `https://www.amd.com/en/newsroom.html`
- `https://www.semiconportal.com/`

不足時の補完:

- `https://www.eetimes.com/`
- `https://www.semiconductorengineering.com/`
- `https://www.tomshardware.com/`
- `https://pc.watch.impress.co.jp/`
- `https://news.mynavi.jp/techplus/`

## Workflow

1. 48時間以内を優先し、最低2件を選ぶ。
2. 主要数値（売上、出荷、前年比など）があれば `what` に残す。
   - 決算本文やプレスリリース冒頭をそのまま貼らず、数値と論点を圧縮して要約する。
3. `why` / `so_what` では、供給・価格・調達判断にどう効くかを記事固有の数値や発表内容に結びつけて書く。
4. 不足時は 7日→14日へ拡大する。
5. 大型ニュースは1週間以内なら継続候補に残す。

## Output

`reports/daily-news/YYYY-MM-DD/research/sources/official-semiconductor.json` に保存する。

```json
{
  "source": "official-semiconductor",
  "date": "YYYY-MM-DD",
  "items": [
    {
      "title": "string",
      "url": "https://...",
      "published_at": "YYYY-MM-DD",
      "segment": "semiconductor",
      "what": "string",
      "why": "string",
      "so_what": "string",
      "confidence": "high|medium|low"
    }
  ]
}
```
