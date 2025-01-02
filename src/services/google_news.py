"""Google News APIを使用してニュース記事を検索するモジュール."""

import time
from datetime import datetime
from typing import Dict, List

from googleapiclient.discovery import build

from config.settings import (
    DELAY_BETWEEN_QUERIES,
    GOOGLE_API_KEY,
    MAX_RESULTS_PER_QUERY,
    QUERIES_PER_KEYWORD,
    SEARCH_ENGINE_ID,
)
from services.sentiment import SentimentAnalyzer


class GoogleNewsScraper:
    """Google News スクレイピングクラスです.

    Google News APIを使用してニュース記事を検索し、
    ポジティブな内容の記事のみを抽出します.
    """

    def __init__(self) -> None:
        """スクレイパーを初期化します.

        Google News APIクライアントと感情分析器を設定します.
        """
        self.service = build("customsearch", "v1", developerKey=GOOGLE_API_KEY, cache_discovery=False)
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
