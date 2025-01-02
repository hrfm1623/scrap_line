"""テキストの感情分析を行うモジュール."""

from janome.tokenizer import Tokenizer
from textblob import TextBlob

from config.settings import POSITIVE_WORDS


class SentimentAnalyzer:
    """感情分析クラスです.

    日本語と英語のテキストを分析し、ポジティブな内容かどうかを判定します.
    """

    def __init__(self) -> None:
        """感情分析器を初期化します.

        日本語の形態素解析器とポジティブワードリストを設定します.
        """
        self.tokenizer = Tokenizer()
        self.positive_words = POSITIVE_WORDS

    def is_positive(self, text: str) -> bool:
        """テキストがポジティブかどうかを判定します.

        日本語の場合は形態素解析とポジティブワードマッチング、
        英語の場合はTextBlobによる感情分析を行います.

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
