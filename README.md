# Google News to Notion

Google News から記事をスクレイピングし、Notion データベースに保存するプロジェクト

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

4. 環境変数の設定:

- GOOGLE_API_KEY: Google Custom Search API の API キー
- SEARCH_ENGINE_ID: Programmable Search Engine の ID
- NOTION_API_KEY: Notion の API キー
- NOTION_DATABASE_ID: Notion データベースの ID
