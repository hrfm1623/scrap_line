"""アプリケーションの設定値を管理するモジュール.

このモジュールでは、以下の設定を管理します：
- API制限に関する定数
- API認証情報
- 検索キーワード
- ポジティブワードリスト
"""

import os
import sys

# ローカル環境でのみ.envファイルを読み込む
if 'AWS_LAMBDA_FUNCTION_NAME' not in os.environ:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenvがインストールされていません。環境変数を直接使用します。")

# API制限に関する定数
DAILY_QUERY_LIMIT = 75  # 1日の最大クエリ数（無料枠100の75%を使用）
QUERIES_PER_KEYWORD = 2  # 1つのキーワードあたりの検索回数
MAX_RESULTS_PER_QUERY = 3  # 1回の検索で取得する記事数
DELAY_BETWEEN_QUERIES = 1  # クエリ間の待機時間（秒）

# API認証情報
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "")
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

# 検索キーワード
SEARCH_QUERIES = [
    # 動物関連
    "動物 癒し",
    "犬 猫 かわいい",
    # 食べ物・グルメ
    "グルメ 話題",
    "スイーツ おいしい",
    # エンタメ・趣味
    "映画 おすすめ",
    "アニメ 人気",
    # 日常・ライフスタイル
    "カフェ おしゃれ",
    "旅行 素敵",
]

# ポジティブワードリスト（最適化版）
POSITIVE_WORDS = {
    # 基本的な感情・感覚
    "うれしい",
    "たのしい",
    "すてき",
    "かわいい",
    "おいしい",
    "きれい",
    "やさしい",
    # 一般的な形容詞
    "いい",
    "素晴らしい",
    "楽しい",
    "美しい",
    "可愛い",
    "優しい",
    "面白い",
    "幸せ",
    # 状態
    "最高",
    "人気",
    "話題",
    "おすすめ",
    # 動物関連
    "癒し",
    "もふもふ",
    "ふわふわ",
    "仲良し",
    "かわいらしい",
}
