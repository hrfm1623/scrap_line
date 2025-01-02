"""AWS Lambda用のハンドラーモジュール."""

import json
from datetime import datetime
from typing import Dict, Any

from config.settings import (
    MAX_RESULTS_PER_QUERY,
    SEARCH_QUERIES
)
from services.google_news import GoogleNewsScraper
from services.notion import NotionClient


def calculate_query_batch(current_hour: int) -> list:
    """実行時間帯に応じて検索するキーワードを決定します.
    
    Args:
        current_hour (int): 現在の時間（0-23）
        
    Returns:
        list: 現在のバッチで検索するキーワードのリスト
    """
    batch_size = len(SEARCH_QUERIES) // 6  # 6回に分割
    batch_number = current_hour // 4  # 4時間ごとに実行
    
    start_idx = batch_number * batch_size
    end_idx = start_idx + batch_size if batch_number < 5 else len(SEARCH_QUERIES)
    return SEARCH_QUERIES[start_idx:end_idx]


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """AWS Lambda用のハンドラー関数です.
    
    Args:
        event (Dict[str, Any]): Lambda関数のイベントデータ
        context (Any): Lambda関数のコンテキスト
        
    Returns:
        Dict[str, Any]: 実行結果を含むレスポンス
    """
    try:
        # 実行時間帯に応じたキーワードバッチを取得
        current_hour = datetime.now().hour
        current_batch = calculate_query_batch(current_hour)
        
        # Google News スクレイパーの初期化
        scraper = GoogleNewsScraper()
        
        # Notion クライアントの初期化
        notion_client = NotionClient()
        
        print(f"現在のバッチのキーワード数: {len(current_batch)}")
        print(f"処理するキーワード: {current_batch}")
        
        # 各キーワードで検索を実行
        for query in current_batch:
            news_items = scraper.search_news(query, max_results=MAX_RESULTS_PER_QUERY)
            notion_client.save_news_to_notion(news_items)
            print(f"キーワード '{query}' の検索が完了しました。(使用クエリ数: {scraper.query_count})")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Success',
                'processed_keywords': len(current_batch),
                'total_queries': scraper.query_count,
                'batch_time': f"{current_hour}時台"
            }, ensure_ascii=False)
        }
        
    except Exception as e:
        error_message = f"エラーが発生しました: {str(e)}"
        print(error_message)
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': error_message
            }, ensure_ascii=False)
        } 