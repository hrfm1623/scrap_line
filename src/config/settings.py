"""アプリケーションの設定値を管理するモジュール.

このモジュールでは、以下の設定を管理します：
- スクレイピング設定（GNews）
- Notion API設定
- 検索キーワード
- ポジティブワードリスト
"""

import os
import sys
from typing import List, Tuple

# ローカル環境でのみ.envファイルを読み込む
if 'AWS_LAMBDA_FUNCTION_NAME' not in os.environ:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenvがインストールされていません。環境変数を直接使用します。")

# GNews API設定
GNEWS_API_KEY = os.getenv("GNEWS_API_KEY", "")

# GNewsの制限に関する定数
DAILY_QUERY_LIMIT = 100  # GNewsの1日あたりの最大クエリ数
MAX_RESULTS_PER_QUERY = 10  # 1回の検索で取得する最大記事数
DELAY_BETWEEN_QUERIES = 2  # クエリ間の待機時間（秒）

# Lambda実行回数に基づく制限
LAMBDA_EXECUTIONS_PER_DAY = 6  # 1日のLambda実行回数
MAX_QUERIES_PER_EXECUTION = int(DAILY_QUERY_LIMIT / LAMBDA_EXECUTIONS_PER_DAY)  # 1回の実行で許可するクエリ数

# スクレイピング設定
MIN_CONTENT_LENGTH = 100  # 記事本文の最小文字数
MAX_CONTENT_LENGTH = 500  # 記事本文の最大文字数
REQUEST_TIMEOUT = 10  # 記事取得時のタイムアウト（秒）

# Notion API認証情報（必須）
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

# 優先度付きの検索キーワード（タプル形式: (キーワード, 優先度)）
# 優先度が高いものから順に実行され、API制限に達した場合は低優先度のものがスキップされます
PRIORITIZED_SEARCH_QUERIES: List[Tuple[str, int]] = [
    # 動物関連（癒し系）- 最優先
    ("動物 癒し ニュース", 1),
    ("犬 猫 かわいい 話題", 1),
    ("動物園 赤ちゃん", 2),
    
    # 食べ物・グルメ（ポジティブな話題）- 中優先
    ("グルメ 新店 オープン", 2),
    ("スイーツ 人気 話題", 2),
    ("レストラン 評価 高評価", 3),
    
    # エンタメ・趣味（明るい話題）- 中優先
    ("映画 ヒット 好評", 2),
    ("アニメ 人気 成功", 2),
    ("音楽 ライブ 感動", 3),
    
    # 日常・ライフスタイル（ポジティブな内容）- 低優先
    ("カフェ おしゃれ 新店", 3),
    ("旅行 観光 おすすめ", 3),
    ("イベント 成功 楽しい", 3),
]

# 後方互換性のために元のSEARCH_QUERIESも維持
SEARCH_QUERIES = [query for query, _ in PRIORITIZED_SEARCH_QUERIES]

# 除外キーワード（広告やPR記事の判定に使用）
IRRELEVANT_PATTERNS = [
    r'広告',
    r'PR',
    r'スポンサード',
    r'プレスリリース',
    r'お知らせ',
    r'キャンペーン',
    r'セール',
    r'割引',
    r'モニター',
]

# ポジティブワードリスト（カテゴリごとに整理）
POSITIVE_WORDS = {
    # 基本的な感情表現
    "うれしい", "たのしい", "すてき", "かわいい", "おいしい", "きれい", "やさしい",
    "楽しい", "素晴らしい", "美しい", "優しい", "面白い", "幸せ", "嬉しい",
    
    # 評価・状態を表す表現
    "最高", "人気", "話題", "おすすめ", "注目", "成功", "好評",
    "高評価", "絶賛", "感動", "魅力", "充実", "快適", "満足",
    
    # 動物関連
    "癒し", "もふもふ", "ふわふわ", "仲良し", "かわいらしい",
    "愛らしい", "元気", "健康", "すくすく", "成長",
    
    # 食べ物関連
    "美味しい", "絶品", "美味", "美食", "贅沢", "新鮮",
    "こだわり", "人気店", "行列", "評判", "名店",
    
    # エンタメ関連
    "大ヒット", "大人気", "感動", "興奮", "熱狂", "魅了",
    "圧巻", "必見", "注目作", "傑作", "名作",
    
    # ライフスタイル関連
    "おしゃれ", "素敵", "快適", "リラックス", "充実",
    "便利", "快適", "リフレッシュ", "癒される",
}
