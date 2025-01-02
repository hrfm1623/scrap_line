"""Notion APIを使用してデータベースにニュース記事を保存するモジュール."""

from typing import Dict, List

from notion_client import Client

from config.settings import NOTION_API_KEY, NOTION_DATABASE_ID


class NotionClient:
    """Notion クライアントクラスです.

    Notion APIを使用してデータベースに記事を保存します.
    """

    def __init__(self) -> None:
        """クライアントを初期化します.

        Notion APIクライアントを設定し、データベースIDを保持します.
        """
        self.client = Client(auth=NOTION_API_KEY)
        self.database_id = NOTION_DATABASE_ID

    def save_news_to_notion(self, news_items: List[Dict[str, str]]) -> None:
        """ニュース記事をNotionデータベースに保存します.

        Args:
            news_items: 保存する記事のリスト。各記事は辞書形式で、
                      title, link, snippet, published_at, sentimentを含みます.
        """
        for item in news_items:
            try:
                self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties={
                        "Title": {"rich_text": [{"text": {"content": item["title"]}}]},
                        "URL": {"url": item["link"]},
                        "Description": {"rich_text": [{"text": {"content": item["snippet"]}}]},
                        "PublishedAt": {"date": {"start": item["published_at"]}},
                        "Sentiment": {"select": {"name": item["sentiment"]}},
                    },
                )
            except Exception as e:
                print(f"記事の保存中にエラーが発生しました: {str(e)}")
