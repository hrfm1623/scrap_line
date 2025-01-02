#!/bin/bash

# Lambda関数名
FUNCTION_NAME="google_news_scraper"

# .envファイルから環境変数を読み込む
if [ -f .env ]; then
    echo "環境変数を.envファイルから読み込んでいます..."
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "エラー: .envファイルが見つかりません"
    exit 1
fi

# デプロイパッケージの作成
echo "デプロイパッケージを作成中..."
./create_lambda_package.sh

# パッケージのサイズチェック
PACKAGE_SIZE=$(stat -f %z lambda_deployment_package.zip 2>/dev/null || stat -c %s lambda_deployment_package.zip)
if [ $PACKAGE_SIZE -gt 50000000 ]; then
    echo "エラー: パッケージサイズが50MBを超えています"
    exit 1
fi

# Lambda関数の更新
echo "Lambda関数を更新中..."
aws lambda update-function-code \
    --function-name $FUNCTION_NAME \
    --zip-file fileb://lambda_deployment_package.zip

# 環境変数の更新
echo "環境変数を更新中..."
aws lambda update-function-configuration \
    --function-name $FUNCTION_NAME \
    --environment "Variables={GOOGLE_API_KEY=$GOOGLE_API_KEY,SEARCH_ENGINE_ID=$SEARCH_ENGINE_ID,NOTION_API_KEY=$NOTION_API_KEY,NOTION_DATABASE_ID=$NOTION_DATABASE_ID}"

# デプロイ結果の確認
if [ $? -eq 0 ]; then
    echo "デプロイが完了しました"
    
    # 関数の状態を確認
    echo "関数の状態を確認中..."
    aws lambda get-function-configuration \
        --function-name $FUNCTION_NAME \
        --query 'LastUpdateStatus' \
        --output text
else
    echo "デプロイに失敗しました"
    exit 1
fi 