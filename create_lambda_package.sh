#!/bin/bash

# クリーンアップ
echo "クリーンアップ中..."
rm -rf lambda_package lambda_deployment_package.zip

# パッケージディレクトリの作成
echo "パッケージディレクトリを作成中..."
mkdir -p lambda_package

# 依存関係のインストール
echo "依存関係をインストール中..."
pip install --target lambda_package \
    google-api-python-client==2.108.0 \
    google-api-python-client-stubs==1.19.0 \
    google-auth-httplib2==0.2.0 \
    google-auth-oauthlib==1.2.0 \
    cachetools==5.3.2 \
    python-dotenv==1.0.0 \
    requests==2.31.0 \
    "urllib3<2.0.0" \
    notion-client==2.1.0 \
    janome==0.5.0

# ソースコードのコピー
echo "ソースコードをコピー中..."
cp -r src/* lambda_package/

# 不要なファイルの削除
echo "不要なファイルを削除中..."
find lambda_package -type d -name "tests" -exec rm -rf {} +
find lambda_package -type d -name "__pycache__" -exec rm -rf {} +
find lambda_package -type d -name "discovery_cache" -exec rm -rf {} +
find lambda_package -type f -name "*.pyc" -delete
find lambda_package -type f -name "*.pyo" -delete
find lambda_package -type f -name "*.pyd" -delete

# ZIPファイルの作成
echo "デプロイパッケージを作成中..."
cd lambda_package
zip -r ../lambda_deployment_package.zip ./* -x "*.pyc" "*.pyo" "*.pyd" "__pycache__/*" "tests/*" "discovery_cache/*"

echo "デプロイパッケージの作成が完了しました。"
echo "作成されたファイル: lambda_deployment_package.zip"

# クリーンアップ
echo "クリーンアップ中..."
cd ..
rm -rf lambda_package/ 