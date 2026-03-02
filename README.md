# daily

Daily news skills and generated artifacts for AI and semiconductor briefing workflows.

## Contents

- `daily-ai-semiconductor-briefing/`: skill to collect sources and produce `daily-news.md` plus landing page generation.
- `daily-news-md-to-html/`: skill to render Markdown into HTML using a reusable `index.html` template.

## Workflow

1. Generate `daily-news.md`.
2. Keep the Markdown file for downstream RAG usage.
3. Render `index.html` from the Markdown template pipeline.
