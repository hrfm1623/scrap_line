"""Google Newsから記事を取得し、Notionデータベースに保存するモジュール."""

import time
from datetime import datetime
from typing import Dict, List

from googleapiclient.discovery import build
from janome.tokenizer import Tokenizer
from notion_client import Client
from textblob import TextBlob

from config.settings import (
    DELAY_BETWEEN_QUERIES,
    GOOGLE_API_KEY,
    MAX_RESULTS_PER_QUERY,
    NOTION_API_KEY,
    NOTION_DATABASE_ID,
    POSITIVE_WORDS,
    QUERIES_PER_KEYWORD,
    SEARCH_ENGINE_ID,
)


class NewsScraperConfig:
    """設定クラスです.

    環境変数から必要な設定を読み込み、バリデーションを行います.
    """

    def __init__(self) -> None:
        """設定を初期化します."""
        self.google_api_key: str = GOOGLE_API_KEY
        self.search_engine_id: str = SEARCH_ENGINE_ID
        self.notion_api_key: str = NOTION_API_KEY
        self.notion_database_id: str = NOTION_DATABASE_ID

        if not all(
            [
                self.google_api_key,
                self.search_engine_id,
                self.notion_api_key,
                self.notion_database_id,
            ]
        ):
            raise ValueError("必要な環境変数が設定されていません。")


class SentimentAnalyzer:
    """感情分析クラスです.

    テキストの感情分析を行い、ポジティブな内容かどうかを判定します。
    """

    def __init__(self) -> None:
        """感情分析器を初期化します."""
        self.tokenizer = Tokenizer()
        self.positive_words = POSITIVE_WORDS

    def is_positive(self, text: str) -> bool:
        """テキストがポジティブかどうかを判定します.

        Args:
            text: 分析対象のテキスト

        Returns:
            bool: ポジティブな内容の場合はTrue
        """
        # 日本語の形態素解析
        tokens = [token.surface for token in self.tokenizer.tokenize(text)]
        positive_count = sum(1 for token in tokens if token in self.positive_words)

        # 英語の感情分析
        blob = TextBlob(text)
        sentiment_score = blob.sentiment.polarity

        # 日本語でポジティブワードを含むか、英語でポジティブな感情値を持つ場合
        return positive_count > 0 or sentiment_score > 0


class GoogleNewsScraper:
    """Google News スクレイピングクラスです.

    Google News APIを使用してニュース記事を検索し、
    ポジティブな内容の記事のみを抽出します。
    """

    def __init__(self) -> None:
        """スクレイパーを初期化します."""
        self.service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY)
        self.search_engine_id = SEARCH_ENGINE_ID
        self.sentiment_analyzer = SentimentAnalyzer()
        self.query_count = 0

    def search_news(
        self, query: str, max_results: int = MAX_RESULTS_PER_QUERY
    ) -> List[Dict[str, str]]:
        """ニュースを検索して結果を返します.

        Args:
            query: 検索キーワード
            max_results: 取得する最大記事数

        Returns:
            List[Dict[str, str]]: 検索結果の記事リスト
        """
        news_items: List[Dict[str, str]] = []
        page = 1
        items_per_page = min(10, max_results)

        try:
            while len(news_items) < max_results and page <= QUERIES_PER_KEYWORD:
                # クエリ数をカウント
                self.query_count += 1

                # APIレート制限を考慮した待機
                time.sleep(DELAY_BETWEEN_QUERIES)

                result = (
                    self.service.cse()
                    .list(
                        q=query,
                        cx=self.search_engine_id,
                        num=items_per_page,
                        start=((page - 1) * 10) + 1,
                        sort="date",  # 最新のニュースを優先
                    )
                    .execute()
                )

                if "items" not in result:
                    break

                for item in result["items"]:
                    if len(news_items) >= max_results:
                        break

                    title = item.get("title", "")
                    snippet = item.get("snippet", "")

                    # ポジティブなニュースのみをフィルタリング
                    if self.sentiment_analyzer.is_positive(
                        title
                    ) or self.sentiment_analyzer.is_positive(snippet):
                        news_items.append(
                            {
                                "title": title,
                                "link": item.get("link", ""),
                                "snippet": snippet,
                                "published_at": datetime.now().isoformat(),
                                "sentiment": "ポジティブ",
                            }
                        )

                page += 1

        except Exception as e:
            print(f"ニュース検索中にエラーが発生しました: {str(e)}")

        return news_items


class NotionClient:
    """Notion クライアントクラスです.

    Notion APIを使用してデータベースに記事を保存します。
    """

    def __init__(self) -> None:
        """クライアントを初期化します."""
        self.client = Client(auth=NOTION_API_KEY)
        self.database_id = NOTION_DATABASE_ID

    def save_news_to_notion(self, news_items: List[Dict[str, str]]) -> None:
        """ニュース記事をNotionデータベースに保存します.

        Args:
            news_items: 保存する記事のリスト
        """
        for item in news_items:
            try:
                self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties={
                        "Title": {"title": [{"text": {"content": item["title"]}}]},
                        "URL": {"url": item["link"]},
                        "Description": {"rich_text": [{"text": {"content": item["snippet"]}}]},
                        "PublishedAt": {"date": {"start": item["published_at"]}},
                        "Sentiment": {"select": {"name": item["sentiment"]}},
                    },
                )
            except Exception as e:
                print(f"記事の保存中にエラーが発生しました: {str(e)}")
