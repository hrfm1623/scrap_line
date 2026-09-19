# 晴れだより（仮称）

明るいニュース・面白い発見・未来を感じる取り組みを、短い日本語の紹介と出典リンクで読むサイトです。事件や炎上が続くニュース画面から離れ、落ち着いて話題を知りたい人に向けています。

科学・未来、自然・動物、まち・暮らし、文化・学び、スポーツを対象にします。事件・事故・災害・政治対立・不祥事・炎上を主題にした記事、広告目的の記事、株価や増益だけを根拠にした「良いニュース」は扱いません。一般ニュースの網羅、Xのトレンド再現、他サービスの専門的な検索・計算機能は対象外です。他リポジトリとの対象重複は未調査です。

## 現在できること

- 日本語・モバイル対応のニュース一覧、カテゴリ切替、キーワード検索、条件リセット。
- 各記事の発表日、出典、照合日、確認方法、掲載理由の表示。
- Python標準ライブラリによる静的HTML生成。主要内容はJavaScriptなしでも読めます。
- RSS 2.0 / Atomの記事候補収集、URL重複除去、非公開の編集待ちデータ保存。
- 公開データの検証、robots.txt・サイトマップ・404・プレビューのnoindex生成。

初期記事はNASAの公式発表を本文まで照合した2件です。紹介文の作成と照合はAI補助で行い、人が確認した日付は未登録です。架空記事6件は `tests/fixtures/` に隔離しています。NASA公式RSSを取得元に設定済みです。8時間ごとのユーザー用systemd設定を用意しています（この作業環境ではユーザーバスに接続できず、タイマーの有効化は未完了）。自動翻訳・LLM要約・自動公開はしません。

公開URL: https://hare-dayori.pages.dev/ （Cloudflare Pagesプロジェクト: `hare-dayori`、本番ブランチ: `main`）。独自ドメインと運営者情報が未確定のため、まずnoindex付きの先行公開として運用します。表示名は仮称。広告・アクセス解析は追加していません。

## 起動と検証

Python 3.9以上。npmはコマンドの入口だけに使います。Webサイトに追加パッケージのインストールは不要です。

```bash
npm run preview      # 実記事2件で確認: http://127.0.0.1:4173
npm run dev          # 架空記事6件のデザイン確認（別途起動・同じポート）
npm run build        # 実記事のプレビューを dist/ に生成
npm run build:demo   # 架空記事を dist-demo/ に生成
npm test            # データ・取得失敗・出力・公開制御のテスト
node --check web/assets/site.js
```

`npm run preview` と `npm run dev` は同時に起動しないでください。どちらも検索エンジン向けにnoindexを生成します。ローカルのPythonサーバーはCloudflare固有の `_headers` を解釈しませんが、HTMLにもnoindexを入れています。

## 記事を更新する

1. 公式発表と利用条件を確認する。RSSがあるだけで商用転載が可能とは判断しません。
2. 取得元が利用可能なら `data/sources.json` に登録し、`npm run refresh` を実行する。
3. `.news-cache/review.html` で候補・取得状況を見て、出典の本文・日付・掲載方針を照合する。
4. 独自の短い紹介文と掲載理由を作り、`data/articles.json` に追加する。
5. `npm test` と `npm run preview` で確認し、公開変更をGitに記録して再ビルドする。

```bash
npm run refresh                       # 収集＋編集用HTMLの更新
npm run review                        # 保存済み候補だけで編集一覧を再生成
npm run draft -- --id 候補ID           # .news-cache/候補ID.json を作成
# 下書きの紹介・理由・照合情報を編集して status を approved にする
npm run register:article -- --file .news-cache/候補ID.json
```

登録時は全件を検証し、成功した場合だけ公開JSONを置き換えます。既存IDの修正に対応し、下書きの再作成では編集を上書きしません。登録コマンドは公開サーバーへは送信しません。

自動収集は見出し・URL・発表日時の原文だけを非公開領域へ保存します。本文・画像は取得しません。肯定的な単語があるだけでは承認されません。除外語は補助であり、否定・文脈・皮肉を正しく判定する分類器ではありません。保留や除外の記事は公開JSONへ移さないでください。

### 取得元の形式

以下は形式の説明用です。`example.com` を実際の確認済み情報に置き換え、利用条件・robots.txt・アクセス上限を確認してから有効化します。NASAの公式RSSを初期設定にしています。

```json
[
  {
    "id": "source-id",
    "name": "発表元の名称",
    "feed_url": "https://example.com/feed.xml",
    "category": "science",
    "terms_url": "https://example.com/terms",
    "terms_checked_at": "2026-09-20",
    "usage_note": "取得と非公開編集利用の許可範囲、アクセス条件を記録",
    "enabled": false
  }
]
```

取得は1ソースにつき6時間以上の間隔、最大10ソース、1回40件、応答2MB、タイムアウト15秒、即時再試行なしです。エラーは標準エラーと `.news-cache/fetch-state.json` に記録し、前回候補と公開記事を維持します。候補は直近1,000件までです。間隔の状態はローカルファイルなので、定期実行時も同じ永続ディレクトリを使い、CLIはファイルロックで多重起動を防ぎます。ETag / Last-Modifiedによる条件付き取得とrobots.txtの確認を行い、取得拒否・robots確認失敗時は収集を止めます。

### 公開記事の形式

実例は `data/articles.json` を参照してください。

| 項目 | 意味 |
| --- | --- |
| `id` | 安定した小文字英数字とハイフンのID |
| `title` / `summary` | 独自見出し100文字以内 / 紹介300文字以内 |
| `category` | `science` / `nature` / `community` / `culture` / `sports` |
| `source_name` / `source_url` | 発表元の名称と記事単位のHTTPS URL |
| `published_at` | 元情報の発表日。取得日・出来事の日と区別 |
| `checked_at` / `reviewer` | 本文との照合日と確認主体 |
| `review_method` | `ai_assisted` または `human` |
| `human_checked_at` | 人による確認日。AI補助だけの場合は `null` |
| `reason` | この話題を選んだ理由 |
| `terms_url` | 確認した利用条件のURL |
| `status` / `is_demo` | 公開は `approved` / `false` |

収集処理の `fetched_at` は取得時刻で、照合・承認ではありません。発表日時が不明なら推測せず保留します。既存の記事に修正がある場合は元記事を再確認し、紹介と照合日を更新します。自動収集では既存候補の内容を上書きしません。サンプル・重複・未来日・必須項目不足・不正URL・対象外語のある公開データではビルドが失敗します。

## Cloudflare Pagesでの公開

追加サーバーやDBなしの静的配信を採用します。Pagesプロジェクトと取得済みドメインは運営者が実際の値を設定してください。ドメイン未指定・空記事・架空記事では本番ビルドを停止します。

- 本番ブランチのビルドコマンド: `npm run build:production`
- 出力ディレクトリ: `dist`
- 本番環境変数: `SITE_URL` に当該サービスのHTTPSルートURL
- `PUBLIC_OPERATOR`: 実際の運営者名
- `PUBLIC_CONTACT_URL`: 公開用問い合わせフォーム等のHTTPS URL
- プレビューブランチのビルドコマンド: `npm run build`（本番と区別）

Pagesでブランチごとにコマンドを切り替える場合は次を設定し、`PRODUCTION_BRANCH` に実際の本番ブランチ名を本番環境だけで指定します。

```bash
if [ -n "$PRODUCTION_BRANCH" ] && [ "$CF_PAGES_BRANCH" = "$PRODUCTION_BRANCH" ]; then npm run build:production; else npm run build; fi
```

`SITE_URL` を `.env` に書いただけでは読み込みません。シェルまたはCloudflareの環境変数として設定してください。最初の公開前に名称・運営者情報を確定し、公開後は `/robots.txt` のHTTP 200・text/plain、サイトマップ、本番canonical、noindexがないこと、存在しないURLの404を確認します。Cloudflare側のWAF・Bot設定は未接続のため未検証です。

[Pagesの公式制限](https://developers.cloudflare.com/pages/platform/limits/)では、2026-09-20確認時にFreeプランは月500ビルド、20,000ファイルです。更新をまとめ、無料枠を超えない運用にします。枠の継続や将来料金は保証しません。

## 採用した構成と調査

2026-09-20:

- **配信**: Python静的生成 / 新規JSフレームワーク / APIサーバーを比較。既存がPythonで処理も小さいため、追加依存・実行料金を抑えられる静的生成を採用。即時反映には再ビルドが必要。[Pages静的HTML](https://developers.cloudflare.com/pages/framework-guides/deploy-anything/)
- **取得**: X / Google Newsスクレイピング / 利用条件を確認したRSSを比較。トレンド再現より編集方針に合う記事を重視し、RSS候補収集＋本文の照合を採用。取得元の確認が終わるまでは手動編集で運用する。
- **選別**: 単語スコアのみ / 有料LLM自動公開 / 編集を挟む方式を比較。誤掲載とAPI費用を避けるため最後を採用。記事数と速報性は抑えられる。
- **初期データ**: NASAの[利用ガイド](https://www.nasa.gov/nasa-brand-center/images-and-media/)を確認し、出典付きの短い独自紹介を作成。NASAの推奨を示す表現、ロゴ、写真、第三者素材は使用しない。この確認を他媒体の利用許可に一般化しない。
- **デザイン**: [DESIGN.md](DESIGN.md) に参照元と調整内容を記録。
- **X料金補足**: [公式料金](https://docs.x.com/x-api/getting-started/pricing)ではTrendsは1リクエスト$0.01。1時間に1回×30日の試算は$7.20（このエンドポイント分だけ）。過去の固定Basic料金を現行料金として使わない。今回は利用しない。

## 旧実装

`src/` のGoogle News→Notion処理とLambda関連ファイルは移行用に保持しています。新サイトからは呼び出しません。旧手順は [docs/legacy-notion.md](docs/legacy-notion.md) にあります。旧READMEのGNews APIに関する説明と実際の `gnews` ライブラリ利用は一致せず、旧感情判定にも呼び出しメソッドの不一致があります。旧処理の動作は今回の検証対象外です。

旧AWS公開は `npm run deploy:legacy` です。新しい `npm run deploy` はCloudflare Pages専用です。既存AWSリソース・スケジュールは停止も変更もしていません。移行時は実環境を確認してください。


## 定期更新と公開の実行

### PC上で候補を定期取得

```bash
python3 scripts/install-news-timer.py             # build/systemd に設定を生成
python3 scripts/install-news-timer.py --install   # ユーザー用systemdへ登録・有効化
systemctl --user list-timers hare-dayori-collect.timer
journalctl --user -u hare-dayori-collect.service -n 50
```

PCのローカル時刻で0時・8時・16時の17分から最大2分遅らせて実行。スリープ・停止中の定時実行はできず、次のユーザーsystemd起動時に取りこぼし分を1回実行します。ログアウト後の動作はOSのユーザーセッション設定次第で、常時実行は保証しません。停止は `systemctl --user disable --now hare-dayori-collect.timer`。root権限・常時サーバー・有料APIは不要です。

2026-09-20の導入状況: `~/.config/systemd/user/` にservice/timerファイルを配置済み。ただし作業環境でユーザーDBusが消失し、systemdのprivate socketも接続拒否となったため、daemon-reloadとenableは未完了です。通常のログイン端末で上記 `--install` を再実行してください。実行中とは扱っていません。

GitHub Actions定期収集、Cloudflare Cron、ローカルsystemdを比較しました。公開GitHubリポジトリに未編集候補を保存せず、追加のDB・認証・費用も増やさないためsystemdを採用。PC停止中に更新できない点がトレードオフです。公開リポジトリのActionsにはテスト・ビルドだけを追加し、収集データをキャッシュ・artifact・ログへ出力しません。Actionsはpush後に有効になるため、ローカルにワークフローを置いただけでは稼働しません。

### 本番公開

実際のドメインと運営者情報が確定したら、Cloudflareで作成済みのPagesプロジェクトを使います。CLI認証は `wrangler login`、状態確認は `wrangler whoami`。秘密情報をチャットやGitに貼らないでください。

`SITE_URL`・`PUBLIC_OPERATOR`・`PUBLIC_CONTACT_URL`・`CLOUDFLARE_PAGES_PROJECT`・`PRODUCTION_BRANCH` を環境変数として設定し、差分を確認・コミットした本番ブランチで次を実行します。

```bash
npm run deploy
npm run verify:live -- https://実際の本番ホスト
```

公開コマンドはテスト→本番生成→WranglerによるPagesアップロード→本番URL検証の順です。未設定・未コミット状態では止まります。Pagesプロジェクトの自動作成やドメインの推測はしません。DNS・カスタムドメインの接続は別途実際のアカウントで必要です。初回のDNS反映待ちで検証が失敗した場合、アップロード済みか確認して `verify:live` だけを再実行します。

## 取得元の調査記録（2026-09-20）

- 採用: [NASA公式RSS一覧](https://www.nasa.gov/rss-feeds/) の Recently Published Content（`https://www.nasa.gov/feed/`）。[利用ガイド](https://www.nasa.gov/nasa-brand-center/images-and-media/)と[robots.txt](https://www.nasa.gov/robots.txt)を確認。見出し・出典・発表日時を非公開候補として保存し、公開は個別の本文照合後の独自紹介に限定。
- 不採用: [Science Japan RSS条件](https://sj.jst.go.jp/rss-policy/index.html) は個人利用に限り商用利用を禁止。収益化予定のため取得しない。
- 保留: 理研はRSS配信URLを確認したが、今回の利用条件確認が完了していないので有効化しない。国内の地域・動物・スポーツ系も未接続。
- NASAの配信は直近の一部記事のみで、全記事やすべてのカテゴリを網羅しない。配信先の変更と利用条件は定期的に再確認する。
- [GitHub Actions料金](https://docs.github.com/en/billing/concepts/product-billing/github-actions)では公開リポジトリの標準runnerは無料。既存の公開リポジトリで短い検証だけを行う。課金runner・artifactの保存は追加しない。

## 今回の検証と未完了事項

- 実RSSから候補10件の取得・ETag記録・編集一覧生成を確認。
- 自動テスト24件で取得拒否・304・取得失敗時の保持・下書きと登録・既存機能を確認。
- systemdの設定構文を検証済み。有効化はユーザーセッション接続待ち。
- Cloudflare CLIのログインを確認し、専用プロジェクト `hare-dayori` を作成済み。独自ドメイン・運営者名・問い合わせ先は回答待ち。
- GitHubへのpushと実環境WAF設定の確認は未実施。先行公開結果は下記を参照。


## 先行公開（2026-09-20）

ユーザーの公開依頼に基づき、専用Pagesプロジェクト `hare-dayori` を作成しました。公開先は `https://hare-dayori.pages.dev/`、`main` ブランチの配信です。初回デプロイ完了。デプロイ固有URLは https://46e151ad.hare-dayori.pages.dev 、公開コードのコミットは `52195c0` です。

公開URLでHTTPS・トップページ200・robots.txtの200/text/plain・サイトマップ200・存在しないURLの404を確認しました。HTMLとHTTPヘッダーのnoindex、実記事2件、モバイル表示、カテゴリとキーワード検索、該当なし・条件リセットも検証済みです。非公開候補と架空記事のパスは404でした。Cloudflare管理画面のWAF設定自体は変更していません。

独自ドメイン・運営者情報が未確定の間は `npm run build` の出力を公開し、HTMLとX-Robots-Tagの両方でnoindexを設定します。これは認証ではなく、URLを知っている人は閲覧できます。架空のサンプルと非公開編集候補は配信しません。canonicalと本番サイトマップの登録は、独自ドメインを確定して検索掲載を有効にするときに行います。

再公開は変更をコミットして `npm run deploy:preview`。独自ドメイン・運営者情報を設定した後の検索掲載用公開は既存の `npm run deploy` を使います。`pages.dev` から独自ドメインへの移行時はホスト単位のリダイレクトも設定してください。


## sirumo.com のサブドメイン接続（2026-09-20）

Cloudflareアカウントの有効なゾーン `sirumo.com` を確認し、Pagesプロジェクト `hare-dayori` に `hare.sirumo.com` を登録しました。サブドメインは独立したサービス名に合わせて選定しています。

現在は **pending / CNAME record not set**。Wrangler OAuthにはPages操作権限がありますがDNSレコード操作権限がなく、DNS APIの読み取りは403でした。次のDNSレコード追加が必要です。

| 項目 | 値 |
| --- | --- |
| 種類 | CNAME |
| 名前 | hare |
| ターゲット | hare-dayori.pages.dev |
| TTL | 自動 |

DNS設定後にPagesのCustom domainsで `active` になることと、`https://hare.sirumo.com/` のHTTPS 200・記事表示・robots.txt・noindexを確認します。まだDNS解決できず、HTTPSの疎通は未確認です。現在の配信先は引き続き `https://hare-dayori.pages.dev/` です。

運営者情報が未確定のためnoindexを維持しています。サブドメインが有効になる前に既存URLをリダイレクトせず、接続確認後に正規URLとホスト単位のリダイレクトを更新します。

接続方式はCloudflare Pagesの[公式カスタムドメイン手順](https://developers.cloudflare.com/pages/configuration/custom-domains/)に従い、Pages登録とCNAMEの両方を使用します。
