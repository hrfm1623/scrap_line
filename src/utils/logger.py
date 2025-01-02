"""ロギング機能を提供するモジュール."""

import logging


def setup_logger(name: str = __name__, level: int = logging.INFO) -> logging.Logger:
    """ロガーを設定して返します.

    Args:
        name: ロガーの名前
        level: ログレベル

    Returns:
        logging.Logger: 設定済みのロガーインスタンス
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger


logger = setup_logger("news_scraper")
