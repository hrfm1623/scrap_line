"""Google Newsからポジティブなニュースを収集し、Notionに保存するスクリプト."""

from config.settings import (
    DAILY_QUERY_LIMIT,
    MAX_RESULTS_PER_QUERY,
    QUERIES_PER_KEYWORD,
    SEARCH_QUERIES,
)
from services.google_news import GoogleNewsScraper
from services.notion import NotionClient
from utils.logger import logger


def main() -> None:
    """メインの実行関数です.

    Google Newsから記事を取得し、Notionデータベースに保存します。
    """
    try:
        # Google News スクレイパーの初期化
        scraper = GoogleNewsScraper()

        # キーワード数を制限（75クエリ÷3回=最大25キーワード）
        max_keywords = DAILY_QUERY_LIMIT // QUERIES_PER_KEYWORD
        search_queries = SEARCH_QUERIES[:max_keywords]

        # Notion クライアントの初期化
        notion_client = NotionClient()

        logger.info(f"本日の検索予定クエリ数: {len(search_queries) * QUERIES_PER_KEYWORD}")

        # 各キーワードで検索を実行
        for query in search_queries:
            news_items = scraper.search_news(query, max_results=MAX_RESULTS_PER_QUERY)
            notion_client.save_news_to_notion(news_items)
            logger.info(f"キーワード '{query}' の検索が完了しました。(使用クエリ数: {scraper.query_count})")

        logger.info(f"すべてのニュース記事の取得と保存が完了しました。総クエリ数: {scraper.query_count}")

    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}")


if __name__ == "__main__":
    main()
