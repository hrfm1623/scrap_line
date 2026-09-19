"""非公開候補の確認・下書き作成・検証済み記事の登録。"""

import argparse
import json
from datetime import datetime
from email.utils import parsedate_to_datetime
from html import escape
from pathlib import Path

from web.collect import ROOT, atomic_json
from web.content import validate_articles


def draft(candidate):
    published = ""
    raw = candidate.get("source_published_at")
    if raw:
        try:
            published = parsedate_to_datetime(raw).date().isoformat()
        except (ValueError, TypeError):
            try:
                published = datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isoformat()
            except ValueError:
                pass
    return {**candidate, "published_at": published, "summary": "", "reason": "",
            "checked_at": "", "reviewer": "", "review_method": "ai_assisted",
            "human_checked_at": None, "status": "pending", "is_demo": False}


def register(article, destination):
    """既存記事を消さず、全件の検証成功後だけ置き換える。"""
    path = Path(destination)
    previous = json.loads(path.read_text(encoding="utf-8"))
    replacement = [item for item in previous if item["id"] != article.get("id")]
    replacement.append(article)
    validated = validate_articles(replacement)
    atomic_json(path, validated)


def review(directory):
    directory = Path(directory)
    source = directory / "candidates.json"
    items = json.loads(source.read_text(encoding="utf-8")) if source.exists() else []
    state = directory / "fetch-state.json"
    statuses = json.loads(state.read_text()) if state.exists() else {}
    cards = []
    for item in reversed(items):
        a = {k: escape(str(v), quote=True) for k, v in item.items()}
        cards.append(f'<article><h2>{a["title"]}</h2><p>{a["source_name"]} / {a["status"]}</p>'
                     f'<p>発表日時（元表記）: {a["source_published_at"]}</p>'
                     f'<p>取得日時: {a["fetched_at"]}</p>'
                     f'<a href="{a["source_url"]}" rel="noreferrer">出典を開く</a>'
                     f'<p>候補ID: <code>{a["id"]}</code></p></article>')
    html = ('<!doctype html><html lang="ja"><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex,nofollow"><title>晴れだより 編集候補</title>'
            '<style>body{max-width:900px;margin:24px auto;padding:0 20px;background:#faf8f2;'
            'color:#263e36;font:16px/1.8 system-ui}article{padding:24px 0;border-top:1px solid #ccc}'
            'h2{font-size:20px}a{color:inherit}pre,code{overflow-wrap:anywhere;white-space:pre-wrap}</style>'
            '<h1>編集候補（未公開）</h1><p>収集結果を承認済みとは扱いません。'
            '出典の本文を確認してから、下書きを作成してください。</p><h2>取得状況</h2><pre>'
            + escape(json.dumps(statuses, ensure_ascii=False, indent=2)) + '</pre>'
            + (''.join(cards) or '<p>候補がありません。先に収集してください。</p>') + '</html>')
    directory.mkdir(parents=True, exist_ok=True)
    output = directory / "review.html"
    output.write_text(html, encoding="utf-8")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("review", "draft", "register"))
    parser.add_argument("--id")
    parser.add_argument("--file", type=Path)
    args = parser.parse_args()
    directory = ROOT / ".news-cache"
    if args.action == "review":
        print(review(directory))
    elif args.action == "draft":
        items = json.loads((directory / "candidates.json").read_text())
        candidate = next((a for a in items if a["id"] == args.id), None)
        if not candidate or candidate["status"] != "pending":
            parser.error("pendingの候補IDを指定してください")
        output = directory / (candidate["id"] + ".json")
        if output.exists():
            parser.error("下書きは既にあります。編集内容を保持するため上書きしません")
        atomic_json(output, draft(candidate))
        print(output)
    else:
        if not args.file:
            parser.error("--file に照合・編集済みのJSONを指定してください")
        register(json.loads(args.file.read_text()), ROOT / "data/articles.json")
        print("記事を登録しました。プレビュー確認後に公開してください。")


if __name__ == "__main__":
    main()
