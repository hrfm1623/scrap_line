import os
from datetime import datetime
from typing import Dict, List, Optional

from dotenv import load_dotenv
from googleapiclient.discovery import build
from notion_client import Client

# 環境変数の読み込み
load_dotenv()

class NewsScraperConfig:
    """設定クラス"""
    def __init__(self) -> None:
        self.google_api_key: str = os.getenv("GOOGLE_API_KEY", "")
        self.search_engine_id: str = os.getenv("SEARCH_ENGINE_ID", "")
        self.notion_api_key: str = os.getenv("NOTION_API_KEY", "")
        self.notion_database_id: str = os.getenv("NOTION_DATABASE_ID", "")

        if not all([
            self.google_api_key,
            self.search_engine_id,
            self.notion_api_key,
            self.notion_database_id
        ]):
            raise ValueError("必要な環境変数が設定されていません。")

class GoogleNewsScraper:
    """Google News スクレイピングクラス"""
    def __init__(self, config: NewsScraperConfig) -> None:
        self.service = build(
            "customsearch",
            "v1",
            developerKey=config.google_api_key
        )
        self.search_engine_id = config.search_engine_id

    def search_news(self, query: str, max_results: int = 10) -> List[Dict]:
        """ニュースを検索して結果を返す"""
        news_items = []
        page = 1
        items_per_page = min(10, max_results)  # Google API の制限により1回に10件まで

        try:
            while len(news_items) < max_results:
                result = self.service.cse().list(
                    q=query,
                    cx=self.search_engine_id,
                    num=items_per_page,
                    start=((page - 1) * 10) + 1
                ).execute()

                if "items" not in result:
                    break

                for item in result["items"]:
                    if len(news_items) >= max_results:
                        break

                    news_items.append({
                        "title": item.get("title", ""),
                        "link": item.get("link", ""),
                        "snippet": item.get("snippet", ""),
                        "published_at": datetime.now().isoformat()  # 実際のpublished_atが取得できない場合は現在時刻を使用
                    })

                page += 1

        except Exception as e:
            print(f"ニュース検索中にエラーが発生しました: {str(e)}")

        return news_items

class NotionClient:
    """Notion クライアントクラス"""
    def __init__(self, config: NewsScraperConfig) -> None:
        self.client = Client(auth=config.notion_api_key)
        self.database_id = config.notion_database_id

    def save_news_to_notion(self, news_items: List[Dict]) -> None:
        """ニュース記事をNotionデータベースに保存"""
        for item in news_items:
            try:
                self.client.pages.create(
                    parent={"database_id": self.database_id},
                    properties={
                        "Title": {
                            "title": [
                                {
                                    "text": {
                                        "content": item["title"]
                                    }
                                }
                            ]
                        },
                        "URL": {
                            "url": item["link"]
                        },
                        "Description": {
                            "rich_text": [
                                {
                                    "text": {
                                        "content": item["snippet"]
                                    }
                                }
                            ]
                        },
                        "PublishedAt": {
                            "date": {
                                "start": item["published_at"]
                            }
                        }
                    }
                )
            except Exception as e:
                print(f"記事の保存中にエラーが発生しました: {str(e)}")

def main() -> None:
    """メイン関数"""
    try:
        # 設定の初期化
        config = NewsScraperConfig()

        # Google News スクレイパーの初期化
        scraper = GoogleNewsScraper(config)

        # Notion クライアントの初期化
        notion_client = NotionClient(config)

        # ニュースの検索（例: "Python programming" で検索）
        news_items = scraper.search_news("Python programming", max_results=5)

        # 結果を Notion に保存
        notion_client.save_news_to_notion(news_items)

        print("ニュース記事の取得と保存が完了しました。")

    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    main() 