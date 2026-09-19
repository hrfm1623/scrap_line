"""公開データを検証する。自動選別は公開承認の代わりにはしない。"""

import re
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urlsplit

CATEGORIES = {
    "science": "科学・未来",
    "nature": "自然・動物",
    "community": "まち・暮らし",
    "culture": "文化・学び",
    "sports": "スポーツ",
}
EXCLUDE = re.compile(
    r"殺人|死亡|死者|事故|災害|地震|虐待|逮捕|戦争|炎上|不祥事|誹謗|救助|"
    r"\b(?:killed|death|disaster|war|arrest|rescue)\b|広告|タイアップ|\bPR\b",
    re.IGNORECASE,
)


def https_url(value):
    if not isinstance(value, str):
        raise ValueError("URLは文字列が必要です")
    parts = urlsplit(value)
    if (parts.scheme != "https" or not parts.hostname or parts.username
            or parts.password or any(c.isspace() for c in value)):
        raise ValueError("認証情報を含まないHTTPS URLが必要です")
    return value


def valid_date(value, now=None):
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        raise ValueError("日付はYYYY-MM-DDで指定してください")
    parsed = date.fromisoformat(value)
    # 編集日・確認日は日本時間。UTCのCIでも日付が前日に戻らないようにする。
    today = (now or datetime.now(timezone.utc)).astimezone(timezone(timedelta(hours=9))).date()
    if parsed > today:
        raise ValueError("未来の日付は指定できません")
    return parsed


def validate_articles(items, demo=False):
    if not isinstance(items, list):
        raise ValueError("記事データは配列が必要です")
    ids, urls = set(), set()
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("各記事はオブジェクトが必要です")
        for field in ("id", "title", "summary", "category", "source_name", "source_url",
                      "published_at", "checked_at", "reviewer", "reason", "terms_url"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"必須項目がありません: {field}")
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", item["id"]):
            raise ValueError("記事IDの形式が不正です")
        if item["id"] in ids or item["source_url"] in urls:
            raise ValueError("記事IDまたは出典URLが重複しています")
        ids.add(item["id"])
        urls.add(item["source_url"])
        if item["category"] not in CATEGORIES:
            raise ValueError("未定義のカテゴリです")
        https_url(item["source_url"])
        https_url(item["terms_url"])
        if valid_date(item["checked_at"]) < valid_date(item["published_at"]):
            raise ValueError("確認日は発表日以降にしてください")
        if item.get("status") != "approved":
            raise ValueError("未承認の記事は公開できません")
        if not demo:
            if item.get("review_method") not in ("human", "ai_assisted"):
                raise ValueError("内容確認の方法を明示してください")
            if item["review_method"] == "human":
                if valid_date(item.get("human_checked_at")) != valid_date(item["checked_at"]):
                    raise ValueError("人の内容確認日を記録してください")
            elif item.get("human_checked_at") is not None:
                raise ValueError("AI補助の照合を人の確認として記録できません")
        if bool(item.get("is_demo")) != demo:
            raise ValueError("実データとサンプルを混在できません")
        if len(item["title"]) > 100 or len(item["summary"]) > 300:
            raise ValueError("見出し100文字・紹介300文字以内にしてください")
        if EXCLUDE.search(item["title"] + item["summary"]):
            raise ValueError("掲載対象外の可能性があります。記事を公開データから外してください")
    return sorted(items, key=lambda a: (a["published_at"], a["id"]), reverse=True)
