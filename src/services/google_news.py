"""Google Newsからニュース記事を取得するモジュール."""

import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from bs4 import BeautifulSoup
from gnews import GNews
import requests

from config.settings import (
    MAX_RESULTS_PER_QUERY,
    DELAY_BETWEEN_QUERIES,
    MIN_CONTENT_LENGTH,
    MAX_CONTENT_LENGTH,
    REQUEST_TIMEOUT,
    IRRELEVANT_PATTERNS,
    GNEWS_API_KEY,
    MAX_QUERIES_PER_EXECUTION,
    PRIORITIZED_SEARCH_QUERIES,
)
from services.sentiment import SentimentAnalyzer


class GoogleNewsScraper:
    """Google News スクレイピングクラスです.

    GNewsライブラリを使用してニュース記事を検索し、
    ポジティブな内容の記事のみを抽出します.
    """

    def __init__(self) -> None:
        """スクレイパーを初期化します.

        GNewsクライアントと感情分析器を設定します.
        """
        self.gnews = GNews(
            language='ja',
            country='JP',
            period='1d',  # 過去24時間のニュースを取得
            max_results=MAX_RESULTS_PER_QUERY
        )
        self.sentiment_analyzer = SentimentAnalyzer()
        self.session = requests.Session()
        # User-Agentを設定してブロックを回避
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.query_count = 0  # API呼び出し回数のカウンター

    def _extract_article_content(self, url: str) -> Optional[str]:
        """記事の本文を抽出します.

        Args:
            url: 記事のURL

        Returns:
            Optional[str]: 抽出された本文。抽出失敗時はNone
        """
        try:
            response = self.session.get(url, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # メタディスクリプションの取得
            meta_desc = soup.find('meta', {'name': 'description'})
            if meta_desc and meta_desc.get('content'):
                return meta_desc.get('content')
            
            # 本文の抽出（主要なコンテンツ領域を探す）
            main_content = soup.find(['article', 'main', 'div'], class_=re.compile(r'(article|content|main|body)'))
            if main_content:
                # 不要な要素を削除
                for tag in main_content.find_all(['script', 'style', 'nav', 'header', 'footer']):
                    tag.decompose()
                
                # テキストを抽出し、整形
                text = ' '.join(main_content.stripped_strings)
                # 余分な空白を削除
                text = re.sub(r'\s+', ' ', text).strip()
                return text[:MAX_CONTENT_LENGTH]  # 設定された最大文字数まで
            
            return None
            
        except Exception as e:
            print(f"記事本文の抽出に失敗しました: {url} - {str(e)}")
            return None

    def _is_relevant_content(self, text: str) -> bool:
        """記事の内容が関連性があるかチェックします.

        Args:
            text: チェックする文字列

        Returns:
            bool: 関連性があればTrue
        """
        # 設定された除外パターンを使用
        for pattern in IRRELEVANT_PATTERNS:
            if re.search(pattern, text):
                return False
        
        # 最小文字数チェック
        if len(text) < MIN_CONTENT_LENGTH:
            return False
            
        return True

    def search_news(
        self, query: str, max_results: int = MAX_RESULTS_PER_QUERY
    ) -> List[Dict[str, str]]:
        """ニュースを検索して結果を返します.

        Args:
            query: 検索キーワード
            max_results: 取得する最大記事数

        Returns:
            List[Dict[str, str]]: 検索結果の記事リスト

        Raises:
            ValueError: API呼び出し回数が制限を超えた場合
        """
        # API制限のチェック
        if self.query_count >= MAX_QUERIES_PER_EXECUTION:
            print(f"API呼び出し回数が制限({MAX_QUERIES_PER_EXECUTION})を超えました。スキップします。")
            return []

        news_items: List[Dict[str, str]] = []
        processed_urls = set()  # 重複チェック用
        
        try:
            # 現在時刻から24時間前までの期間を設定
            end_date = datetime.now()
            start_date = end_date - timedelta(days=1)
            
            # ニュースの検索を実行
            search_results = self.gnews.get_news(query)
            self.query_count += 1  # API呼び出し回数をインクリメント
            
            # APIレート制限を考慮した待機
            time.sleep(DELAY_BETWEEN_QUERIES)
            
            for item in search_results:
                if len(news_items) >= max_results:
                    break
                
                url = item.get('link', '')
                # URLが既に処理済みの場合はスキップ
                if not url or url in processed_urls:
                    continue
                    
                title = item.get('title', '')
                description = item.get('description', '')
                published_date = item.get('published date')
                
                # 記事本文を取得
                content = self._extract_article_content(url)
                if not content:
                    continue
                
                # 内容の関連性チェック
                if not self._is_relevant_content(content):
                    continue
                
                # 日付のバリデーション
                try:
                    if published_date:
                        pub_date = datetime.strptime(published_date, '%a, %d %b %Y %H:%M:%S GMT')
                        if not (start_date <= pub_date <= end_date):
                            continue
                    else:
                        continue
                except ValueError:
                    continue
                
                # ポジティブなニュースのみをフィルタリング
                combined_text = f"{title} {description} {content}"
                if self.sentiment_analyzer.is_positive(combined_text):
                    news_items.append({
                        'title': title,
                        'link': url,
                        'snippet': description,
                        'content': content,
                        'published_at': pub_date.isoformat(),
                        'sentiment': 'ポジティブ',
                        'publisher': item.get('publisher', {}).get('title', '不明')
                    })
                    processed_urls.add(url)
            
        except Exception as e:
            print(f"ニュース検索中にエラーが発生しました: {str(e)}")
            
        return news_items

    def search_all_news(self) -> List[Dict[str, str]]:
        """すべての検索キーワードに対してニュース検索を実行します.

        優先度の高いキーワードから順に実行し、API制限に達した場合は
        低優先度のキーワードをスキップします。

        Returns:
            List[Dict[str, str]]: 検索結果の記事リスト
        """
        all_news: List[Dict[str, str]] = []
        
        # 優先度でソート（優先度の低い数字が高優先）
        sorted_queries = sorted(PRIORITIZED_SEARCH_QUERIES, key=lambda x: x[1])
        
        for query, priority in sorted_queries:
            if self.query_count >= MAX_QUERIES_PER_EXECUTION:
                print(f"優先度{priority}のクエリ「{query}」はAPI制限により実行をスキップします。")
                continue
                
            print(f"優先度{priority}のクエリ「{query}」を実行します。")
            news_items = self.search_news(query)
            all_news.extend(news_items)
        
        return all_news
