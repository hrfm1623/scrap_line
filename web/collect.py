"""利用条件を確認したRSS/Atomから非公開の記事候補を収集する。"""

import argparse
import fcntl
import hashlib
import json
import logging
import os
import tempfile
import time
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.robotparser import RobotFileParser

from web.content import CATEGORIES, EXCLUDE, https_url, valid_date

ROOT = Path(__file__).resolve().parents[1]
MAX_BYTES = 2_000_000
MAX_ITEMS = 40
INTERVAL = 6 * 60 * 60
USER_AGENT = "HareDayoriFeedReader/1.0"


def fetch_feed(source, last):
    """robotsを確認し、前回のETag/更新日時で差分取得する。"""
    origin = urlsplit(source["feed_url"])
    robots_url = f"{origin.scheme}://{origin.netloc}/robots.txt"
    try:
        with urlopen(Request(robots_url, headers={"User-Agent": USER_AGENT}), timeout=15) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError("robots.txtが上限を超えました")
            robots = RobotFileParser()
            robots.parse(raw.decode("utf-8", errors="replace").splitlines())
            if not robots.can_fetch(USER_AGENT, source["feed_url"]):
                raise ValueError("robots.txtが取得を許可していません")
    except HTTPError as error:
        if error.code not in (404, 410):
            raise
    headers = {"User-Agent": USER_AGENT}
    for key, header in (("etag", "If-None-Match"), ("last_modified", "If-Modified-Since")):
        if last.get(key):
            headers[header] = last[key]
    try:
        with urlopen(Request(source["feed_url"], headers=headers), timeout=15) as response:
            if urlsplit(response.url).netloc != origin.netloc:
                raise ValueError("取得元ホストが変わりました。利用条件を再確認してください")
            https_url(response.url)
            return response.read(MAX_BYTES + 1), {
                "etag": response.headers.get("ETag"),
                "last_modified": response.headers.get("Last-Modified"),
            }
    except HTTPError as error:
        if error.code == 304:
            return None, {k: last.get(k) for k in ("etag", "last_modified")}
        raise


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, name = tempfile.mkstemp(dir=path.parent, prefix=".news-", suffix=".tmp")
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def parse_feed(raw, source):
    if len(raw) > MAX_BYTES or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise ValueError("取得サイズ超過または禁止されたXML宣言です")
    root = ET.fromstring(raw)
    # RSS 2.0 と Atom の名前空間を揃える。
    for node in root.iter():
        node.tag = node.tag.rsplit("}", 1)[-1]
    if root.tag not in ("rss", "feed"):
        raise ValueError("RSS/Atomではありません")
    entries = root.findall("./channel/item") if root.tag == "rss" else root.findall("./entry")
    result = []
    for item in entries[:MAX_ITEMS]:
        title = (item.findtext("title") or "").strip()
        link = next((n.get("href") or n.text or "" for n in item.findall("link")
                     if n.get("rel", "alternate") == "alternate"), "").strip()
        if not title or not link:
            continue
        try:
            https_url(link)
        except ValueError:
            continue
        result.append({
            "id": hashlib.sha256(link.encode()).hexdigest()[:24],
            "title": title[:300], "source_url": link, "source_name": source["name"],
            "category": source["category"], "terms_url": source["terms_url"],
            "source_published_at": item.findtext("pubDate") or item.findtext("published")
            or item.findtext("updated") or None,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
            "status": "excluded" if EXCLUDE.search(title) else "pending",
        })
    if not result:
        raise ValueError("有効な記事候補がありません。前回データを維持します")
    return result


def validate_sources(sources):
    if not isinstance(sources, list) or len(sources) > 10:
        raise ValueError("取得元は配列で最大10件です")
    ids = set()
    for source in sources:
        if not isinstance(source, dict):
            raise ValueError("各取得元はオブジェクトが必要です")
        if source.get("enabled") is not True:
            continue
        for key in ("id", "name", "feed_url", "terms_url", "terms_checked_at", "usage_note"):
            if not isinstance(source.get(key), str) or not source[key].strip():
                raise ValueError(f"取得元の必須項目がありません: {key}")
        if source["id"] in ids or source.get("category") not in CATEGORIES:
            raise ValueError("取得元のID重複またはカテゴリ不正です")
        ids.add(source["id"])
        https_url(source["feed_url"])
        https_url(source["terms_url"])
        valid_date(source["terms_checked_at"])


def collect(sources, directory, fetch=None, now=None):
    validate_sources(sources)
    directory = Path(directory)
    path = directory / "candidates.json"
    state_path = directory / "fetch-state.json"
    previous = json.loads(path.read_text()) if path.exists() else []
    state = json.loads(state_path.read_text()) if state_path.exists() else {}
    now = time.time() if now is None else now
    merged = {a["source_url"]: a for a in previous}
    failures = 0
    for source in sources:
        if source.get("enabled") is not True:
            continue
        last_state = state.get(source["id"], {})
        last = last_state.get("attempted_at")
        if last is not None and now - last < INTERVAL:
            continue
        try:
            if fetch:
                raw = fetch(source["feed_url"])
                validators = {}
            else:
                raw, validators = fetch_feed(source, last_state)
            if raw is None:
                state[source["id"]] = dict(last_state, attempted_at=now, status="unchanged")
                continue
            candidates = parse_feed(raw, source)
            for article in candidates:
                merged.setdefault(article["source_url"], article)
            state[source["id"]] = {"attempted_at": now, "status": "ok", "count": len(candidates), **validators}
        except Exception as error:
            failures += 1
            logging.error("取得失敗 %s: %s", source["id"], error)
            state[source["id"]] = dict(last_state, attempted_at=now, status="error", error=str(error))
    if list(merged.values()) != previous:
        # 非公開候補を直近1000件まで保存。承認済みの公開JSONは変更しない。
        atomic_json(path, sorted(merged.values(), key=lambda a: a["fetched_at"])[-1000:])
    atomic_json(state_path, state)
    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, default=ROOT / "data/sources.json")
    parser.add_argument("--directory", type=Path, default=ROOT / ".news-cache")
    args = parser.parse_args()
    sources = json.loads(args.sources.read_text(encoding="utf-8"))
    if not any(source.get("enabled") is True for source in sources):
        parser.exit(1, "有効な取得元がありません。利用条件を確認してdata/sources.jsonを設定してください。\n")
    args.directory.mkdir(parents=True, exist_ok=True)
    with (args.directory / "collect.lock").open("w") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, "別の収集処理が実行中です。\n")
        failures = collect(sources, args.directory)
    print(f"収集結果: {args.directory / 'fetch-state.json'}（失敗{failures}件）")
    raise SystemExit(1 if failures else 0)


if __name__ == "__main__":
    main()
