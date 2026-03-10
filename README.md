# daily

AI・半導体デイリーブリーフィングの skill 群、生成物、GitHub Pages 公開物を管理するリポジトリです。

## Directory Layout

```text
.
├── skills/
│   ├── daily-ai-semiconductor-briefing/   # リサーチと daily-news.md 作成
│   ├── daily-news-md-to-html/             # Markdown -> HTML 変換
│   └── daily-briefing-publish-pages/      # docs/ 反映と commit/push
├── reports/
│   └── daily-news/YYYY-MM-DD/             # 中間生成物 (daily-news.md, index.html, research/)
└── docs/
    └── daily-news/YYYY-MM-DD/             # GitHub Pages 配信用
```

## Standard Flow

1. `skills/daily-ai-semiconductor-briefing` で `reports/daily-news/YYYY-MM-DD/daily-news.md` を作成。
2. `skills/daily-news-md-to-html` で同ディレクトリの `index.html` を生成。
3. `skills/daily-briefing-publish-pages` で `docs/` に同期し、必要なら commit/push。
