"""テキストの感情分析を行うモジュール."""

from typing import List
from janome.tokenizer import Tokenizer
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer

from config.settings import POSITIVE_WORDS


class SentimentAnalyzer:
    """感情分析クラスです.

    日本語と英語のテキストを分析し、ポジティブな内容かどうかを判定します.
    """

    def __init__(self) -> None:
        """感情分析器を初期化します.

        日本語の形態素解析器とポジティブワードリスト、
        英語の感情分析器を設定します.
        """
        self.tokenizer = Tokenizer()
        self.positive_words = POSITIVE_WORDS
        try:
            self.sia = SentimentIntensityAnalyzer()
        except LookupError:
            # 必要なデータがない場合はダウンロード
            nltk.download('vader_lexicon')
            self.sia = SentimentIntensityAnalyzer()

    def is_positive(self, text: str) -> bool:
        """テキストがポジティブかどうかを判定します.

        日本語の場合は形態素解析とポジティブワードマッチング、
        英語の場合はNLTKのVADERによる感情分析を行います.

        Args:
            text: 分析対象のテキスト

        Returns:
            bool: ポジティブな内容の場合はTrue
        """
        # 日本語の形態素解析
        tokens = [token.surface for token in self.tokenizer.tokenize(text)]
        positive_count = sum(1 for token in tokens if token in self.positive_words)

        # 英語の感情分析
        scores = self.sia.polarity_scores(text)
        sentiment_score = scores['compound']  # -1.0 to 1.0

        # 日本語でポジティブワードを含むか、英語でポジティブな感情値を持つ場合
        return positive_count > 0 or sentiment_score > 0.0
