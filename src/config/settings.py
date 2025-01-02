"""アプリケーションの設定値を管理するモジュール.

このモジュールでは、以下の設定を管理します：
- API制限に関する定数
- API認証情報
- 検索キーワード
- ポジティブワードリスト
"""

import os

from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

# API制限に関する定数
DAILY_QUERY_LIMIT = 75  # 1日の最大クエリ数（無料枠100の75%を使用）
QUERIES_PER_KEYWORD = 3  # 1つのキーワードあたりの検索回数
MAX_RESULTS_PER_QUERY = 5  # 1回の検索で取得する記事数
DELAY_BETWEEN_QUERIES = 2  # クエリ間の待機時間（秒）

# API認証情報
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "")
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

# 検索キーワード
SEARCH_QUERIES = [
    "技術革新 成功",
    "社会貢献 成果",
    "環境改善 進展",
    "医療 breakthrough",
    "科学 発見",
    "SDGs 達成",
    "ベンチャー 成功",
    "AI 革新",
    "再生可能エネルギー 進展",
    "宇宙開発 成功",
]

# ポジティブワードリスト
POSITIVE_WORDS = {
    "成功",
    "達成",
    "革新",
    "進歩",
    "発展",
    "向上",
    "改善",
    "好調",
    "快挙",
    "躍進",
    "前進",
    "期待",
    "希望",
    "発見",
    "貢献",
    "実現",
    "解決",
    "支援",
    "協力",
    "成長",
    "進展",
    "回復",
    "改革",
    "創造",
    "開発",
    "成果",
    "効果",
    "優秀",
    "歓迎",
    "推進",
    "拡大",
    "充実",
    "強化",
    "安定",
    "確立",
}
