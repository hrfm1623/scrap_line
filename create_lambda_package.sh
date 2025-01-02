#!/bin/bash

# クリーンアップ
echo "クリーンアップ中..."
rm -rf lambda_package lambda_deployment_package.zip

# パッケージディレクトリの作成
echo "パッケージディレクトリを作成中..."
mkdir -p lambda_package/python

# 依存関係のインストール
echo "依存関係をインストール中..."
pip install --target lambda_package/python \
    google-api-python-client==2.108.0 \
    google-auth-httplib2==0.2.0 \
    google-auth-oauthlib==1.2.0 \
    python-dotenv==1.0.0 \
    --no-deps

# ソースコードのコピー
echo "ソースコードをコピー中..."
cp -r src/* lambda_package/

# 不要なファイルの削除
echo "不要なファイルを削除中..."
find lambda_package/python -type d -name "tests" -exec rm -rf {} +
find lambda_package/python -type d -name "__pycache__" -exec rm -rf {} +
find lambda_package/python -type d -name "discovery_cache" -exec rm -rf {} +
find lambda_package/python -type f -name "*.pyc" -delete
find lambda_package/python -type f -name "*.pyo" -delete
find lambda_package/python -type f -name "*.pyd" -delete
find lambda_package/python -type f -name "*.dist-info" -delete

# ZIPファイルの作成
echo "デプロイパッケージを作成中..."
cd lambda_package
zip -r ../lambda_deployment_package.zip ./* -x "*.pyc" "*.pyo" "*.pyd" "__pycache__/*" "tests/*" "discovery_cache/*" "*.dist-info/*"

echo "デプロイパッケージの作成が完了しました。"
echo "作成されたファイル: lambda_deployment_package.zip"

# クリーンアップ
echo "クリーンアップ中..."
cd ..
rm -rf lambda_package/ 