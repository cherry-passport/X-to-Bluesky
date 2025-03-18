# Twitter to Bluesky 自動投稿ツール

TwitterでポストしたコンテンツをBlueskyにも自動的に投稿するPythonツールです。メンションのポストとリツイートは自動的に除外されます。

## 機能

- Twitterの特定ユーザーの新規投稿を監視
- メンション投稿、リツイート、短いコメントの引用リツイートを自動的に除外
- 通常の投稿をBlueskyに自動転送
- 定期実行モードと1回だけ実行するモードをサポート
- 最後に処理したツイートIDを記録して重複投稿を防止

## 必要条件

- Python 3.6以上
- 以下のPythonライブラリ:
  - tweepy
  - atproto
  - pyyaml

## インストール方法

1. 必要なライブラリをインストールします:

```bash
pip install tweepy atproto pyyaml
```

2. このリポジトリをクローンするか、ファイルをダウンロードします。

3. `config.yaml.example` を `config.yaml` にコピーし、必要な情報を設定します:

```bash
cp config.yaml.example config.yaml
```

## 設定

`config.yaml` ファイルを編集して、以下の情報を設定します:

```yaml
twitter:
  api_key: "YOUR_TWITTER_API_KEY"
  api_secret: "YOUR_TWITTER_API_SECRET"
  access_token: "YOUR_TWITTER_ACCESS_TOKEN"
  access_token_secret: "YOUR_TWITTER_ACCESS_TOKEN_SECRET"
  bearer_token: "YOUR_TWITTER_BEARER_TOKEN"

bluesky:
  username: "YOUR_BLUESKY_USERNAME" # 例: user.bsky.social
  password: "YOUR_BLUESKY_APP_PASSWORD"

monitor:
  interval_minutes: 5
  max_tweets_per_check: 10

target_users:
  - username: "TwitterUsername1" # @は不要
  - username: "TwitterUsername2" # @は不要
```

### Twitter API認証情報の取得方法

1. [Twitter Developer Portal](https://developer.twitter.com/en/portal/dashboard)にアクセスし、アカウントを作成またはログインします。
2. プロジェクトとアプリを作成します。
3. 「Keys and Tokens」タブから必要な認証情報を取得します。

### Bluesky認証情報

1. Blueskyのユーザー名（通常は `username.bsky.social` 形式）
2. Blueskyのパスワードまたはアプリパスワード

## 使用方法

### 定期実行モード

```bash
python twitter_to_bluesky.py
```

このモードでは、設定ファイルで指定された間隔（デフォルトは5分）で定期的にTwitterをチェックし、新しい投稿をBlueskyに転送します。

### 1回だけ実行するモード

```bash
python twitter_to_bluesky.py --once
```

このモードでは、1回だけTwitterをチェックして新しい投稿をBlueskyに転送し、その後終了します。

### カスタム設定ファイルの指定

```bash
python twitter_to_bluesky.py --config /path/to/custom_config.yaml
```

## ログ

ログは `logs/twitter_to_bluesky.log` に保存されます。ログレベルはデフォルトで `INFO` に設定されています。

## 注意事項

- このツールはTwitterとBlueskyの両方のAPIを使用するため、API利用制限に注意してください。
- メンション投稿（@で始まるツイート）とリツイートは自動的に除外されます。
- 短いコメントのみの引用リツイートも除外されます。
- 最初の実行時は、各ユーザーの最新の1件のツイートのみが処理されます。

## トラブルシューティング

### 認証エラー

Twitter APIまたはBluesky APIの認証に失敗する場合は、以下を確認してください:

1. 設定ファイルの認証情報が正しいか
2. Twitter APIのアクセス権限が適切に設定されているか
3. Blueskyのユーザー名とパスワードが正しいか

### ツイートが取得できない

ツイートが取得できない場合は、以下を確認してください:

1. 監視対象のユーザー名が正しいか
2. Twitter APIの利用制限に達していないか
3. 監視対象のユーザーのアカウントが公開されているか

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。
