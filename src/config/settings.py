"""アプリケーションの設定値を管理するモジュール.

このモジュールでは、以下の設定を管理します：
- スクレイピング設定（GNews）
- Notion API設定
- 検索キーワード
- ポジティブワードリスト
"""

import os
import sys
from typing import List, Tuple, Set

# ニュース取得モードの設定
NEWS_MODE = os.getenv("NEWS_MODE", "trend")  # "trend" または "positive"

# GNewsの制限に関する定数
DAILY_QUERY_LIMIT = 100  # GNewsの1日あたりの最大クエリ数
MAX_RESULTS_PER_QUERY = 5  # 1回の検索で取得する最大記事数（質を重視して減らす）
DELAY_BETWEEN_QUERIES = 3  # クエリ間の待機時間（秒）（負荷を考慮して増やす）

# Lambda実行回数に基づく制限
LAMBDA_EXECUTIONS_PER_DAY = 4  # 1日のLambda実行回数（コスト最適化）
MAX_QUERIES_PER_EXECUTION = int(DAILY_QUERY_LIMIT / LAMBDA_EXECUTIONS_PER_DAY)

# スクレイピング設定
MIN_CONTENT_LENGTH = 200  # 記事本文の最小文字数（短すぎる記事を除外）
MAX_CONTENT_LENGTH = 1000  # 記事本文の最大文字数（長めに設定して内容を確保）
REQUEST_TIMEOUT = 15  # 記事取得時のタイムアウト（秒）（遅いサイトに対応）

# Notion API認証情報（必須）
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID", "")

# トレンド記事用の検索キーワード
TREND_SEARCH_QUERIES: List[Tuple[str, int]] = [
    # 一般ニュース
    ("ニュース 話題", 1),
    ("最新 トレンド", 1),
    ("注目 今日", 1),
    
    # テクノロジー
    ("テクノロジー 最新", 2),
    ("IT ニュース", 2),
    
    # ビジネス
    ("ビジネス 最新", 2),
    ("経済 ニュース", 2),
    
    # エンタメ
    ("エンターテインメント 話題", 3),
    ("芸能 ニュース", 3),
]

# ポジティブ記事用の検索キーワード（既存のものを移動）
POSITIVE_SEARCH_QUERIES: List[Tuple[str, int]] = [
    # 動物関連（癒し系）- 最優先
    ("動物 赤ちゃん 誕生 話題", 1),
    ("犬 猫 保護 成功 話題", 1),
    ("動物園 パンダ 赤ちゃん", 1),
    
    # 科学・技術（革新的な話題）- 高優先
    ("科学 発見 成功 快挙", 1),
    ("技術 革新 開発 成功", 1),
    ("医療 治療 成功 breakthrough", 2),
    
    # 社会貢献・SDGs（ポジティブな変化）- 高優先
    ("環境 保護 成功 活動", 2),
    ("社会貢献 支援 成功", 2),
    ("地域 活性化 成功", 2),
    
    # 文化・芸術（創造的な話題）- 中優先
    ("芸術 展覧会 好評", 3),
    ("伝統 文化 継承 成功", 3),
    ("音楽 コンサート 感動", 3),
]

# モードに応じて使用する検索クエリを選択
PRIORITIZED_SEARCH_QUERIES = TREND_SEARCH_QUERIES if NEWS_MODE == "trend" else POSITIVE_SEARCH_QUERIES

# 後方互換性のために元のSEARCH_QUERIESも維持
SEARCH_QUERIES = [query for query, _ in PRIORITIZED_SEARCH_QUERIES]

# トレンドモード用の除外パターン（最小限の除外のみ）
TREND_IRRELEVANT_PATTERNS = [
    r'広告',
    r'PR',
    r'スポンサード',
    r'プレスリリース',
]

# ポジティブモード用の除外パターン（既存のものを移動）
POSITIVE_IRRELEVANT_PATTERNS = [
    # 広告・PR関連
    r'広告',
    r'PR',
    r'スポンサード',
    r'プレスリリース',
    r'キャンペーン',
    r'セール',
    r'割引',
    r'モニター',
    
    # 低品質コンテンツ指標
    r'まとめ',
    r'ランキング',
    r'速報',
    r'(?:詳しくは|続きは)こちら',
    r'クリックして',
    r'お得',
    r'無料',
    
    # 古い・更新系コンテンツ
    r'\d{4}年',
    r'更新日',
    r'アーカイブ',
    
    # その他不要なパターン
    r'(?:月|日)曜日',
    r'提供：',
    r'写真提供',
    r'著作権',
]

# ポードに応じて使用する除外パターンを選択
IRRELEVANT_PATTERNS = TREND_IRRELEVANT_PATTERNS if NEWS_MODE == "trend" else POSITIVE_IRRELEVANT_PATTERNS

# ポジティブワードリスト（カテゴリごとに整理）
POSITIVE_WORDS: Set[str] = {
    # 革新・発展
    "革新的", "画期的", "先進的", "独創的", "創造的",
    "breakthrough", "快挙", "成功", "達成", "実現",
    
    # 社会的インパクト
    "貢献", "支援", "保護", "保全", "解決",
    "改善", "向上", "発展", "進展", "前進",
    
    # 感動・共感
    "感動", "感激", "感銘", "共感", "共鳴",
    "心温まる", "励まされる", "勇気づけられる",
    
    # 希望・未来
    "希望", "期待", "可能性", "将来性", "展望",
    "未来", "発展", "成長", "進歩", "躍進",
    
    # 評価・称賛
    "高評価", "好評", "絶賛", "称賛", "賞賛",
    "注目", "話題", "評判", "人気", "実績",
    
    # 科学・技術
    "発見", "解明", "開発", "創出", "確立",
    "実証", "検証", "革新", "進化", "向上",
}

# 記事の質を判定するための最小スコア（0-1の範囲）
MIN_SENTIMENT_SCORE = 0.7 if NEWS_MODE == "positive" else 0.0  # トレンドモードでは感情分析を無効化
