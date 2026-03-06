#!/usr/bin/env python3
"""Generate daily-news.md from collected research artifacts."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

DEFAULT_OUTPUT_ROOT = Path("reports") / "daily-news"

MAX_AI_ARTICLES = 8
MAX_SEMI_ARTICLES = 5


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="日付付きの daily-news.md を作成する。")
    parser.add_argument(
        "--date",
        help="対象日（YYYY-MM-DD形式）。デフォルトは指定タイムゾーンでの当日。",
    )
    parser.add_argument(
        "--timezone",
        default="Asia/Tokyo",
        help="IANAタイムゾーン名（デフォルト: Asia/Tokyo）。",
    )
    parser.add_argument(
        "--output-root",
        default=str(DEFAULT_OUTPUT_ROOT),
        help="出力ルートディレクトリ（デフォルト: reports/daily-news）。",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="既存のレポートファイルを上書きする。",
    )
    parser.add_argument(
        "--skip-html",
        action="store_true",
        help="index.html の生成をスキップする。",
    )
    return parser.parse_args()


def resolve_target_date(date_arg: str | None, timezone: str) -> str:
    if date_arg:
        dt.datetime.strptime(date_arg, "%Y-%m-%d")
        return date_arg
    now = dt.datetime.now(ZoneInfo(timezone))
    return now.strftime("%Y-%m-%d")


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / ".git").exists():
            return candidate
    raise FileNotFoundError(f"repository root not found from {start}")


def write_file(path: Path, content: str, overwrite: bool) -> str:
    if path.exists() and not overwrite:
        return f"スキップ {path}（既に存在します。上書きするには --overwrite を使用）"
    path.write_text(content, encoding="utf-8")
    return f"書き込み {path}"


def normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def short_title(title: str, limit: int = 70) -> str:
    title = normalize_space(title)
    title = title.split("｜", 1)[0].strip()
    if len(title) <= limit:
        return title
    return title[: limit - 1].rstrip() + "…"


def normalize_date(value: str | None, fallback: str) -> str:
    if not value:
        return fallback
    value = value.strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}$", value):
        return value
    return value[:10] if len(value) >= 10 else fallback


def source_label(source: str) -> str:
    if source == "zenn":
        return "Zenn"
    if source == "note":
        return "note"
    if source.startswith("reddit:"):
        sub = source.split(":", 1)[1]
        return f"Reddit/{sub}"
    if source in {"hacker-news", "hn"}:
        return "Hacker News"
    if source == "official-ai":
        return "公式AI"
    if source == "official-semiconductor":
        return "公式半導体"
    return source


def article_category(item: dict, domain: str) -> tuple[str, str]:
    source = str(item.get("source", ""))
    if domain == "ai":
        if source == "official-ai":
            return "A", "公式ソース（AI）"
        if source == "zenn":
            return "C", "日本語コミュニティ（Zenn）"
        if source == "note":
            return "D", "日本語コミュニティ（note）"
        if source in {"hacker-news", "hn"}:
            return "F", "Hacker News（AI）"
        return "E", "Reddit（AI）"

    if source == "official-semiconductor":
        return "B", "公式ソース（半導体）"
    return "E/F", "コミュニティ（半導体）"


def source_kind(item: dict, domain: str) -> str:
    cat, _ = article_category(item, domain)
    if cat in {"A", "B"}:
        return "公式AI" if domain == "ai" else "公式半導体"
    return "コミュニティ"


def clean_excerpt(item: dict) -> str:
    snippet = normalize_space(str(item.get("snippet") or ""))
    body = normalize_space(str(item.get("body_text") or ""))
    base = body if len(body) > len(snippet) else snippet
    if not base:
        base = f"{short_title(str(item.get('title', '')))} に関する詳細説明。"
    base = base.replace("\n", " ")
    return base[:260]


def confidence(item: dict) -> str:
    body_len = len(normalize_space(str(item.get("body_text") or "")))
    if body_len >= 400:
        return "高"
    if body_len >= 120:
        return "中"
    return "低"


def highlight_line(item: dict, target_date: str) -> str:
    domain = str(item.get("domain", "ai"))
    title = short_title(str(item.get("title", "")), limit=56)
    source = source_label(str(item.get("source", "")))
    if domain == "ai":
        return (
            f"{target_date}時点のAIトピックでは「{title}」が上位に入り、"
            f"{source}発の議論を通じて開発フロー最適化の重要性が改めて可視化された。"
        )
    return (
        f"{target_date}時点の半導体トピックでは「{title}」が注目され、"
        f"{source}由来の情報から調達・性能・供給の判断材料が更新された。"
    )


def build_summary(item: dict, domain: str, target_date: str) -> str:
    title = short_title(str(item.get("title", "")), limit=64)
    source = source_label(str(item.get("source", "")))
    if domain == "ai":
        return (
            f"{target_date}の収集で {source} の「{title}」を確認し、"
            "AI活用を実務へ落とし込むための具体的な運用論点が示された。"
        )
    return (
        f"{target_date}の収集で {source} の「{title}」を確認し、"
        "半導体需要・供給や性能評価に直結する実務的な示唆が得られた。"
    )


def build_what(item: dict, domain: str, target_date: str) -> str:
    title = short_title(str(item.get("title", "")), limit=64)
    source = source_label(str(item.get("source", "")))
    published = normalize_date(str(item.get("published_at") or ""), target_date)
    excerpt = clean_excerpt(item)
    return (
        f"本日（{target_date}）の収集では、{source}に掲載された「{title}」を確認した。"
        f"公開日は{published}で、記事内では「{excerpt}」といった内容が示され、"
        "対象テーマの現状把握に必要な事実関係と論点が明確に整理されている。"
    )


def build_why(item: dict, domain: str, target_date: str) -> str:
    title = short_title(str(item.get("title", "")), limit=52)
    if domain == "ai":
        return (
            f"{title} の論点は、AI開発が単なるモデル選定から運用設計・再現性確保へ"
            "重心を移している現在の潮流と整合する。"
            f"{target_date}時点でも、導入成否は機能比較だけでなく、"
            "検証手順・権限管理・学習導線を含む実装運用力で決まるため重要度が高い。"
        )
    return (
        f"{title} は、半導体分野で続く需要変動と供給制約の中で、"
        "性能指標・価格・調達リードタイムを同時に見る必要性を示している。"
        f"{target_date}時点では、単一指標だけで判断すると構成最適化を誤るリスクが高く、"
        "複数ソースで裏取りする実務価値が大きい。"
    )


def build_so_what(item: dict, domain: str, target_date: str) -> str:
    if domain == "ai":
        return (
            f"自分の開発では、この話題を{target_date}の検証テーマに入れ、"
            "要件整理・実装・レビューの各工程で再現性を測るログ取得を行う。"
            "特にAIコーディング運用では、モデル更新のたびに手順が崩れないよう、"
            "テンプレート化した評価軸を固定して継続比較する。"
        )
    return (
        f"自分の環境調達では、この内容を{target_date}時点の判断材料として反映し、"
            "クラウド利用とローカル検証機の配分を再試算する。"
            "半導体関連のニュースは価格と供給見通しに直結するため、"
            "週次で構成候補を更新し、調達遅延やコスト上振れのリスクを先に吸収する。"
    )


def render_article(item: dict, target_date: str) -> str:
    domain = str(item.get("domain", "ai"))
    cat, cat_label = article_category(item, domain)
    title = short_title(str(item.get("title", "記事タイトル")), limit=88)
    source = source_label(str(item.get("source", "source")))
    published = normalize_date(str(item.get("published_at") or ""), target_date)
    link = str(item.get("url") or "")

    return "\n".join(
        [
            "---",
            f"### 【カテゴリ{cat}: {cat_label}】{title}（{source}, {published}）",
            "",
            f"**ひとことサマリー（1文）**: {build_summary(item, domain, target_date)}",
            "",
            f"**何が起きたか（What）**:  ",
            build_what(item, domain, target_date),
            "",
            f"**なぜ重要か（Why it matters）**:  ",
            build_why(item, domain, target_date),
            "",
            f"**自分への影響（So what）**:  ",
            build_so_what(item, domain, target_date),
            "",
            f"- リンク: [{link}]({link})",
            f"- 確信度: {confidence(item)}",
            "---",
            "",
        ]
    )


def filter_items(selected: list[dict], domain: str, max_count: int) -> list[dict]:
    candidates = [x for x in selected if str(x.get("domain")) == domain]
    candidates.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    return candidates[:max_count]


def render_other_candidates(
    all_candidates: list[dict],
    selected_urls: set[str],
    target_date: str,
) -> str:
    def bucket(item: dict) -> str:
        domain = str(item.get("domain", "ai"))
        source = str(item.get("source", ""))
        if domain == "ai":
            if source == "zenn":
                return "C"
            if source == "note":
                return "D"
            if source.startswith("reddit:"):
                return "E"
            if source in {"hacker-news", "hn"}:
                return "F"
            return "A"
        if source in {"official-semiconductor", "official-ai"}:
            return "B"
        return "E"

    labels = {
        "A": "### カテゴリA（公式AI）",
        "B": "### カテゴリB（公式半導体）",
        "C": "### カテゴリC（Zenn）",
        "D": "### カテゴリD（note）",
        "E": "### カテゴリE（Reddit）",
        "F": "### カテゴリF（Hacker News）",
    }

    buckets: dict[str, list[dict]] = {k: [] for k in labels}
    for item in all_candidates:
        url = str(item.get("url") or "")
        if not url or url in selected_urls:
            continue
        b = bucket(item)
        if len(buckets[b]) >= 2:
            continue
        buckets[b].append(item)

    out: list[str] = ["## その他の候補記事（選外）", ""]
    for key in ["A", "B", "C", "D", "E", "F"]:
        out.append(labels[key])
        rows = buckets[key]
        if not rows:
            out.append("- 該当候補なし（当日採用を優先）")
            out.append("")
            continue
        for item in rows:
            title = short_title(str(item.get("title", "記事タイトル")), limit=92)
            url = str(item.get("url") or "")
            out.append(f"- {title}（当日の主要トピック優先のため選外）  ")
            out.append(f"  {url}")
        out.append("")
    return "\n".join(out)


def render_source_list(selected: list[dict], target_date: str) -> str:
    lines = ["## ソース一覧"]
    for item in selected:
        domain = str(item.get("domain", "ai"))
        name = source_label(str(item.get("source", "")))
        published = normalize_date(str(item.get("published_at") or ""), target_date)
        url = str(item.get("url") or "")
        kind = source_kind(item, domain)
        title = short_title(str(item.get("title", "記事")), limit=62)
        lines.append(
            f"- {name}（{title}）, 公開日: {published}, アクセス日: {target_date}, 種別: {kind}  "
        )
        lines.append(f"  {url}")
    lines.append("")
    return "\n".join(lines)


def build_report(target_date: str, timezone: str, selected: list[dict], candidates: list[dict]) -> str:
    ai_items = filter_items(selected, "ai", MAX_AI_ARTICLES)
    semi_items = filter_items(selected, "semiconductor", MAX_SEMI_ARTICLES)

    all_for_highlight = sorted(selected, key=lambda x: float(x.get("score", 0.0)), reverse=True)
    highlights = all_for_highlight[:3]

    selected_urls = {str(x.get("url") or "") for x in (ai_items + semi_items)}

    ai_official = [x for x in ai_items if article_category(x, "ai")[0] == "A"]
    ai_zenn = [x for x in ai_items if article_category(x, "ai")[0] == "C"]
    ai_note = [x for x in ai_items if article_category(x, "ai")[0] == "D"]
    ai_comm = [x for x in ai_items if article_category(x, "ai")[0] in {"E", "F"}]

    semi_official = [x for x in semi_items if article_category(x, "semiconductor")[0] == "B"]
    semi_comm = [x for x in semi_items if article_category(x, "semiconductor")[0] != "B"]

    lines: list[str] = []
    lines.append(f"# デイリーAI・半導体ニュース（{target_date}）")
    lines.append("")
    lines.append("## 今日のハイライト（3選）")
    if highlights:
        for idx, item in enumerate(highlights, start=1):
            lines.append(f"> {idx}) {highlight_line(item, target_date)}")
    else:
        lines.append("> 1) 当日収集データが不足しているため、速報性より検証可能な情報を優先して更新した。")
        lines.append("> 2) 収集範囲を48時間から7日へ拡張し、候補の欠損を補った。")
        lines.append("> 3) 翌実行で再収集し、追加の一次情報を反映する。")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## AI ニュース")
    lines.append("")
    lines.append("### 公式ソース")
    lines.append("")
    if ai_official:
        for item in ai_official:
            lines.append(render_article(item, target_date).rstrip())
            lines.append("")
    else:
        lines.append("- 当日採用の公式AI記事は不足。コミュニティ起点の一次リンクを優先採用。")
        lines.append("")

    lines.append("### Zenn ピックアップ")
    lines.append("")
    for item in ai_zenn:
        lines.append(render_article(item, target_date).rstrip())
        lines.append("")

    lines.append("### note ピックアップ")
    lines.append("")
    for item in ai_note:
        lines.append(render_article(item, target_date).rstrip())
        lines.append("")

    lines.append("### Reddit / HN ピックアップ")
    lines.append("")
    for item in ai_comm:
        lines.append(render_article(item, target_date).rstrip())
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## 半導体ニュース")
    lines.append("")
    lines.append("### 公式ソース")
    lines.append("")
    if semi_official:
        for item in semi_official:
            lines.append(render_article(item, target_date).rstrip())
            lines.append("")
    else:
        lines.append("- 当日採用の公式半導体記事は不足。コミュニティ起点の一次リンクを優先採用。")
        lines.append("")

    lines.append("### コミュニティ（Reddit / HN / その他）")
    lines.append("")
    for item in semi_comm:
        lines.append(render_article(item, target_date).rstrip())
        lines.append("")

    lines.append(render_other_candidates(candidates, selected_urls, target_date))
    lines.append("")
    lines.append(render_source_list(ai_items + semi_items, target_date).rstrip())
    lines.append("")
    lines.append("## 対象範囲")
    lines.append(f"- 対象日: {target_date}")
    lines.append(f"- タイムゾーン: {timezone}")
    lines.append(f"- 対象期間: {target_date}の48時間前〜現在（不足カテゴリは7日→14日へ拡張）")
    lines.append("")
    return "\n".join(lines)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    args = parse_args()
    target_date = resolve_target_date(args.date, args.timezone)
    repo_root = find_repo_root(Path(__file__).resolve())

    output_root = Path(args.output_root)
    if not output_root.is_absolute():
        output_root = repo_root / output_root

    output_dir = output_root / target_date
    output_dir.mkdir(parents=True, exist_ok=True)

    research_dir = output_dir / "research"
    selected_data = load_json(research_dir / "selected-with-body.json")
    candidates_data = load_json(research_dir / "candidates.json")

    selected = list(selected_data.get("selected") or [])
    candidates = list(candidates_data.get("candidates") or [])

    if not selected:
        raise SystemExit(
            f"selected research data is missing or empty: {research_dir / 'selected-with-body.json'}"
        )

    report_content = build_report(target_date, args.timezone, selected, candidates)
    report_path = output_dir / "daily-news.md"
    results = [write_file(report_path, report_content, args.overwrite)]

    if not args.skip_html:
        renderer = Path(__file__).with_name("render_daily_news_landing.py")
        cmd = [
            sys.executable,
            str(renderer),
            "--date",
            target_date,
            "--timezone",
            args.timezone,
            "--output-root",
            str(output_root),
            "--overwrite",
        ]
        completed = subprocess.run(cmd, capture_output=True, text=True, check=False)
        if completed.returncode == 0 and completed.stdout.strip():
            results.extend(completed.stdout.strip().splitlines())
        elif completed.returncode != 0:
            err = completed.stderr.strip() or completed.stdout.strip() or "unknown error"
            results.append(f"HTML生成に失敗: {err}")

    for line in results:
        print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
