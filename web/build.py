"""追加依存なしでCloudflare Pages用のHTMLを生成する。"""

import argparse
import json
import os
import shutil
from html import escape as esc
from pathlib import Path
from urllib.parse import urlsplit

from web.content import CATEGORIES, https_url, validate_articles

ROOT = Path(__file__).resolve().parents[1]


def render_card(article, demo):
    a = {k: esc(str(v), quote=True) for k, v in article.items()}
    source = ("架空のサンプル記事" if demo else
              f'<a href="{a["source_url"]}" rel="noopener noreferrer">{a["source_name"]}で読む ↗</a>')
    checked_label = ("サンプル" if demo else "出典照合（AI補助）"
                     if article.get("review_method") == "ai_assisted" else "内容確認")
    return f'''<article id="{a['id']}" class="story" data-category="{a['category']}">
      <div class="story-top"><span class="tag">{CATEGORIES[a['category']]}</span>
      <time datetime="{a['published_at']}">発表 {a['published_at'].replace('-', '.')}</time></div>
      <h3>{a['title']}</h3><p>{a['summary']}</p>
      <details><summary>この話題を選んだ理由</summary><p>{a['reason']}</p></details>
      <div class="story-source">{source}<small>{checked_label}：{a['checked_at']}</small></div>
    </article>'''


def build(data_path, output, site_url="", production=False, demo=False):
    items = validate_articles(json.loads(Path(data_path).read_text(encoding="utf-8")), demo)
    operator = os.getenv("PUBLIC_OPERATOR", "").strip()
    contact = os.getenv("PUBLIC_CONTACT_URL", "").strip()
    if bool(operator) != bool(contact):
        raise ValueError("運営者名と問い合わせURLを両方指定してください")
    if contact:
        https_url(contact)
    operator_html = (f'<p>運営：{esc(operator)} · <a href="{esc(contact)}" rel="noreferrer">お問い合わせ・訂正のご連絡</a></p>'
                     if operator else '')
    if production:
        https_url(site_url)
        parts = urlsplit(site_url)
        if parts.path not in ("", "/") or parts.query or parts.fragment:
            raise ValueError("SITE_URLには本番ホストのルートURLを指定してください")
        if demo or not items:
            raise ValueError("サンプルや記事未登録の状態では本番ビルドできません")
    site_url = site_url.rstrip("/")
    output = Path(output)
    # 検証を終えてから書き込む。不正な入力で前回のHTMLを壊さない。
    output.mkdir(parents=True, exist_ok=True)
    meta = (f'<link rel="canonical" href="{esc(site_url)}/">' if production else
            '<meta name="robots" content="noindex, nofollow">')
    notice = ('<div class="notice">デザインプレビュー · 以下の記事はすべて架空のサンプルです。</div>'
              if demo else '')
    buttons = ''.join(f'<button type="button" data-filter="{key}" aria-pressed="false">{label}</button>'
                      for key, label in CATEGORIES.items())
    cards = ''.join(render_card(item, demo) for item in items)
    empty = '' if items else '<div class="empty"><h3>最初のニュースを準備しています</h3><p>出典と内容を確かめた話題から、少しずつお届けします。</p><a href="#policy">掲載方針を読む ↓</a></div>'
    html = f'''<!doctype html>
<html lang="ja"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>晴れだより｜明るい話題を、ひと息ぶん。</title>
<meta name="description" content="科学の発見、自然や動物、まちの取り組み。明るい話題を短い紹介と出典リンクで届ける晴れだより。">
{meta}<link rel="stylesheet" href="/assets/site.css"><script src="/assets/site.js" defer></script></head>
<body><a class="skip" href="#news">ニュースへスキップ</a>{notice}
<header class="shell"><a class="brand" href="/" aria-label="晴れだより ホーム"><span class="sun" aria-hidden="true">☀</span> 晴れだより<span class="brand-en">HARE DAYORI</span></a><a href="#policy">わたしたちの掲載方針 <span aria-hidden="true">↗</span></a></header>
<main class="shell"><section class="intro"><div><p class="eyebrow">A LITTLE GOOD IN YOUR DAY</p><h1>世界の明るいほうに、<br>ひと息つこう。</h1><p class="intro-text">小さな発見。誰かの挑戦。まちに生まれた、うれしい変化。<br class="desktop">知ると少し前を向ける話題を、ここに集めます。</p></div><div class="editor-note"><span aria-hidden="true">✳</span><p>たくさん読むより、<br>こころに残るひとつを。</p><small>あなたのペースで、どうぞ。</small></div></section>
<section id="news" aria-labelledby="news-title"><div class="section-heading"><h2 id="news-title">明るいニュースをひとつ</h2><span>発表日の新しい順</span></div>
<div class="filters" hidden><div class="categories" role="group" aria-label="カテゴリ"><button type="button" data-filter="all" aria-pressed="true">すべて</button>{buttons}</div><form role="search"><label for="search">気になる言葉で探す</label><div class="search-box"><input id="search" type="search" placeholder="動物、宇宙、まちづくり…" maxlength="100"><button type="submit">検索</button></div></form></div>
<noscript><p>すべての記事を表示しています。絞り込みにはJavaScriptを有効にしてください。</p></noscript>
<p class="result-count" role="status" aria-live="polite">{len(items)}件の話題</p><div class="stories">{cards}</div>{empty}
<div id="no-results" class="empty" hidden><h3>この条件の話題はまだありません</h3><p>別の言葉やカテゴリでも探してみてください。</p><button type="button" id="reset">条件をリセット</button></div></section>
<section id="policy" class="policy"><div><p class="eyebrow">OUR EDITORIAL PROMISE</p><h2>明るい話題を、<br>誠実に届けるために。</h2></div><div><h3>小さくても、確かな前進を。</h3><p>科学・自然・地域・文化・スポーツを中心に、発見や達成、人や社会の前向きな変化を選びます。研究段階の成果を、実用化されたものとして紹介しません。</p><h3>読む前の安心も、大切に。</h3><p>事件・事故・災害・対立・炎上を主題とする記事は扱いません。深刻な出来事を、明るい見出しだけに置き換えることもしません。</p><h3>その先を、確かめられるように。</h3><p>紹介文には出典・発表日・内容確認日を添えます。本文や写真の転載ではなく、短い紹介から発表元へつなぎます。サイト内の検索入力は外部へ送信しません。</p></div></section></main>
<footer class="shell"><span class="brand">晴れだより</span><p>明るい話題を、ひと息ぶん。</p>{operator_html}<a href="#news">ニュースに戻る ↑</a></footer></body></html>'''
    (output / "index.html").write_text(html, encoding="utf-8")
    shutil.copytree(ROOT / "web/assets", output / "assets", dirs_exist_ok=True)
    (output / "404.html").write_text('<!doctype html><html lang="ja"><meta charset="utf-8"><meta name="robots" content="noindex"><title>ページが見つかりません</title><h1>ページが見つかりません</h1><a href="/">晴れだよりに戻る</a></html>', encoding="utf-8")
    robots = "User-agent: *\nAllow: /\n"
    sitemap = '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
    if production:
        robots += f"Sitemap: {site_url}/sitemap.xml\n"
        sitemap += f"<url><loc>{esc(site_url)}/</loc></url>"
    (output / "robots.txt").write_text(robots, encoding="utf-8")
    (output / "sitemap.xml").write_text(sitemap + '</urlset>', encoding="utf-8")
    headers = "/*\n  X-Content-Type-Options: nosniff\n  Referrer-Policy: strict-origin-when-cross-origin\n  Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'\n"
    if not production:
        headers += "  X-Robots-Tag: noindex, nofollow\n"
    (output / "_headers").write_text(headers, encoding="utf-8")
    return len(items)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--production", action="store_true")
    parser.add_argument("--data", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.production and (not os.getenv("PUBLIC_OPERATOR", "").strip()
                            or not os.getenv("PUBLIC_CONTACT_URL", "").strip()):
        parser.exit(1, "本番公開にはPUBLIC_OPERATORとPUBLIC_CONTACT_URLの設定が必要です。\n")
    data = args.data or ROOT / ("tests/fixtures/articles.json" if args.demo else "data/articles.json")
    output = args.output or ROOT / ("dist-demo" if args.demo else "dist")
    try:
        count = build(data, output, os.getenv("SITE_URL", ""), args.production, args.demo)
    except (ValueError, OSError) as error:
        parser.exit(1, f"ビルド中止: {error}\n")
    print(f"{output}: {count}件を生成しました")


if __name__ == "__main__":
    main()
