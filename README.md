# Google News to Notion

Google News から記事をスクレイピングし、Notion データベースに保存するプロジェクト

## 機能概要

- Google News から最新 24 時間以内のニュースを取得
- ポジティブな内容の記事のみを抽出
- 広告や PR 記事を自動的に除外
- 記事の本文を解析して感情分析を実施
- 関連性の高い記事のみを Notion に保存

## 事前準備

1. GNews API キーの取得:

   - [GNews API](https://gnews.io/)にアクセス
   - アカウントを作成し、API キーを取得
   - 無料プランの制限を確認（リクエスト数など）

2. Notion API の設定:
   - [Notion Developers](https://developers.notion.com/)にアクセス
   - 新しいインテグレーションを作成
   - API キーを取得
   - データベースの共有設定でインテグレーションを追加

## 技術スタック

### 言語とランタイム

- Python 3.9
- AWS Lambda

### 主要なライブラリ

- gnews (v0.3.6): Google News スクレイピング
- notion-client (v2.1.0): Notion API クライアント
- beautifulsoup4 (v4.9.3): HTML 解析
- janome (v0.5.0): 日本語形態素解析
- requests (v2.26.0): HTTP クライアント

### 開発ツール

- black (v23.7.0): コードフォーマッター
- flake8 (v6.1.0): リンター
- mypy (v1.5.1): 静的型チェッカー
- isort (v5.12.0): インポート文の整理
- pre-commit (v3.3.3): Git フック管理

### インフラストラクチャ

- AWS Lambda: サーバーレス実行環境
- GNews API: ニュース記事の取得
- Notion API: データベース管理

## セットアップ

1. 必要なパッケージのインストール:

```bash
pip install -r requirements.txt
```

2. 環境変数の設定:

- `.env.example`を`.env`にコピー
- 以下の環境変数を設定:
  - GNEWS_API_KEY: GNews API キー
  - NOTION_API_KEY: Notion API キー
  - NOTION_DATABASE_ID: Notion データベース ID

3. Notion データベースの作成:

- 新しいデータベースを作成
- 以下のプロパティを設定:
  - Title: タイトル (タイトル型)
  - URL: リンク (URL 型)
  - PublishedAt: 公開日 (日付型)
  - Description: 説明 (テキスト型)
  - Content: 本文 (テキスト型)
  - Sentiment: 感情 (セレクト型)
  - Publisher: 発行元 (テキスト型)

## スクレイピング設定

`settings.py`で以下の設定をカスタマイズできます：

- 検索キーワード（カテゴリごとに整理）
- 除外キーワード（広告や PR 記事の判定）
- ポジティブワードリスト
- スクレイピングの制限値（タイムアウト、文字数など）

## デプロイ

Lambda 関数のデプロイは以下のコマンドで実行:

```bash
npm run deploy
```

このコマンドは以下の処理を実行します:

1. デプロイパッケージの作成
2. Lambda 関数のコード更新
3. 環境変数の設定

## 注意事項

- GNews API の利用制限を確認し、適切な使用を心がけてください
- スクレイピング対象のサイトの利用規約を確認してください
- 取得した記事の著作権に注意してください
