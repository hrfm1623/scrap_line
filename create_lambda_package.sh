#!/bin/bash

# クリーンアップ
echo "クリーンアップ中..."
rm -rf lambda_package lambda_deployment_package.zip

# パッケージディレクトリの作成
echo "パッケージディレクトリを作成中..."
mkdir -p lambda_package

# 依存関係のインストール
echo "依存関係をインストール中..."
pip install --target lambda_package --verbose \
    notion-client==2.1.0 \
    janome==0.5.0 \
    beautifulsoup4==4.9.3 \
    requests==2.26.0 \
    "urllib3<2.0.0" \
    gnews==0.3.6

# インストール結果の確認
if [ $? -ne 0 ]; then
    echo "エラー: パッケージのインストールに失敗しました"
    exit 1
fi

# インストールされたパッケージの確認
echo "インストールされたパッケージの一覧:"
pip list --path lambda_package

# ソースコードのコピー
echo "ソースコードをコピー中..."
cp -r src/* lambda_package/

# 不要なファイルの削除
echo "不要なファイルを削除中..."
find lambda_package -type d -name "tests" -exec rm -rf {} +
find lambda_package -type d -name "__pycache__" -exec rm -rf {} +
find lambda_package -type f -name "*.pyc" -delete
find lambda_package -type f -name "*.pyo" -delete
find lambda_package -type f -name "*.pyd" -delete

# ZIPファイルの作成
echo "デプロイパッケージを作成中..."
cd lambda_package
zip -r ../lambda_deployment_package.zip ./* -x "*.pyc" "*.pyo" "*.pyd" "__pycache__/*" "tests/*"

# ZIP作成結果の確認
if [ $? -ne 0 ]; then
    echo "エラー: ZIPファイルの作成に失敗しました"
    exit 1
fi

echo "デプロイパッケージの作成が完了しました。"
echo "作成されたファイル: lambda_deployment_package.zip"

# パッケージサイズの確認
package_size=$(du -h ../lambda_deployment_package.zip | cut -f1)
echo "パッケージサイズ: $package_size"

# クリーンアップ
echo "クリーンアップ中..."
cd ..
rm -rf lambda_package/ 