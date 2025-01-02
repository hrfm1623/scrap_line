# Google News to Notion

Google News から記事をスクレイピングし、Notion データベースに保存するプロジェクト

## 技術スタック

### 言語とランタイム

- Python 3.9
- AWS Lambda

### 主要なライブラリ

- google-api-python-client (v2.47.0): Google Custom Search API クライアント
- notion-client (v2.1.0): Notion API クライアント
- janome (v0.5.0): 日本語形態素解析
- python-dotenv (v1.0.0): 環境変数管理

### 開発ツール

- black (v23.7.0): コードフォーマッター
- flake8 (v6.1.0): リンター
- mypy (v1.5.1): 静的型チェッカー
- isort (v5.12.0): インポート文の整理
- pre-commit (v3.3.3): Git フック管理

### インフラストラクチャ

- AWS Lambda: サーバーレス実行環境
- Google Custom Search API: ニュース記事の検索
- Notion API: データベース管理

### 開発ツール

- npm: デプロイスクリプト管理
- AWS CLI: Lambda 関数のデプロイと管理

## セットアップ

1. 必要なパッケージのインストール:

```bash
pip install -r requirements.txt
```

2. 環境変数の設定:

- `.env.example`を`.env`にコピー
- 各 API キーと設定値を入力

3. Notion データベースの作成:

- 新しいデータベースを作成
- 以下のプロパティを設定:
  - Title: タイトル (タイトル型)
  - URL: リンク (URL 型)
  - PublishedAt: 公開日 (日付型)
  - Description: 説明 (テキスト型)
  - Sentiment: 感情 (セレクト型)

4. 環境変数の設定:

- GOOGLE_API_KEY: Google Custom Search API の API キー
- SEARCH_ENGINE_ID: Programmable Search Engine の ID
- NOTION_API_KEY: Notion の API キー
- NOTION_DATABASE_ID: Notion データベースの ID

## デプロイ

Lambda 関数のデプロイは以下のコマンドで実行:

```bash
npm run deploy
```

このコマンドは以下の処理を実行します:

1. デプロイパッケージの作成
2. Lambda 関数のコード更新
3. 環境変数の設定
