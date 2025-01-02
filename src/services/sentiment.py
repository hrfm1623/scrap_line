"""テキストの感情分析を行うモジュール."""

from janome.tokenizer import Tokenizer
from config.settings import POSITIVE_WORDS


class SentimentAnalyzer:
    """感情分析クラスです.

    日本語のテキストを分析し、ポジティブな内容かどうかを判定します.
    """

    def __init__(self) -> None:
        """感情分析器を初期化します.

        日本語の形態素解析器とポジティブワードリストを設定します.
        """
        self.tokenizer = Tokenizer()
        self.positive_words = POSITIVE_WORDS

    def is_positive(self, text: str) -> bool:
        """テキストがポジティブかどうかを判定します.

        日本語の形態素解析とポジティブワードマッチングを行います.

        Args:
            text: 分析対象のテキスト

        Returns:
            bool: ポジティブな内容の場合はTrue
        """
        # 日本語の形態素解析
        tokens = [token.surface for token in self.tokenizer.tokenize(text)]
        positive_count = sum(1 for token in tokens if token in self.positive_words)

        # ポジティブワードを含む場合
        return positive_count > 0
