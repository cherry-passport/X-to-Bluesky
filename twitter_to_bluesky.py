#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import yaml
import json
import time
import logging
from datetime import datetime, timezone
import tweepy
from atproto import Client as AtprotoClient

# ログディレクトリの設定
script_dir = os.path.dirname(os.path.abspath(__file__))
log_dir = os.path.join(script_dir, "logs")
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, 'twitter_to_bluesky.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('twitter_to_bluesky')

class TwitterToBluesky:
    """TwitterからBlueskyに投稿を自動転送するクラス"""
    
    def __init__(self, config_path=None):
        """
        初期化メソッド
        
        Args:
            config_path (str, optional): 設定ファイルのパス
        """
        # 設定ファイルのパスが指定されていない場合はデフォルトのパスを使用
        if config_path is None:
            config_path = os.path.join(script_dir, "config.yaml")
        
        self.config_path = config_path
        
        # 設定ファイルを読み込む
        self.config = self._load_config(config_path)
        
        # Twitter認証
        self.twitter_api = self._authenticate_twitter()
        
        # Bluesky認証
        self.bluesky_client = self._authenticate_bluesky()
        
        # 最後に処理したツイートIDを保存するファイル
        self.last_tweet_file = os.path.join(script_dir, "last_tweet_id.json")
        
        # 最後に処理したツイートIDを読み込む
        self.last_tweet_ids = self._load_last_tweet_ids()
    
    def _load_config(self, config_path):
        """
        設定ファイルを読み込む
        
        Args:
            config_path (str): 設定ファイルのパス
            
        Returns:
            dict: 設定情報
        """
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                logger.info("設定ファイルを読み込みました")
                return config
        except Exception as e:
            logger.error(f"設定ファイルの読み込みに失敗しました: {e}")
            # デフォルト設定を作成
            default_config = {
                "twitter": {
                    "api_key": "",
                    "api_secret": "",
                    "access_token": "",
                    "access_token_secret": "",
                    "bearer_token": ""
                },
                "bluesky": {
                    "username": "",
                    "password": ""
                },
                "monitor": {
                    "interval_minutes": 5,
                    "max_tweets_per_check": 10
                },
                "target_users": []
            }
            
            # デフォルト設定を保存
            with open(config_path, 'w', encoding='utf-8') as file:
                yaml.dump(default_config, file, default_flow_style=False)
                logger.info("デフォルト設定ファイルを作成しました")
            
            return default_config
    
    def _authenticate_twitter(self):
        """
        Twitter APIの認証を行う
        
        Returns:
            tweepy.API: Twitter APIクライアント
        """
        try:
            # Twitter API v1.1の認証情報
            api_key = self.config.get('twitter', {}).get('api_key')
            api_secret = self.config.get('twitter', {}).get('api_secret')
            access_token = self.config.get('twitter', {}).get('access_token')
            access_token_secret = self.config.get('twitter', {}).get('access_token_secret')
            
            # 認証情報が設定されているか確認
            if not all([api_key, api_secret, access_token, access_token_secret]):
                logger.error("Twitter APIの認証情報が設定されていません")
                raise ValueError("Twitter APIの認証情報が設定されていません")
            
            # 認証
            auth = tweepy.OAuth1UserHandler(
                api_key, api_secret, access_token, access_token_secret
            )
            api = tweepy.API(auth)
            
            # 認証確認
            api.verify_credentials()
            logger.info("Twitter APIの認証に成功しました")
            
            return api
        except Exception as e:
            logger.error(f"Twitter APIの認証に失敗しました: {e}")
            raise
    
    def _authenticate_bluesky(self):
        """
        Bluesky APIの認証を行う
        
        Returns:
            atproto.Client: Bluesky APIクライアント
        """
        try:
            # Bluesky APIの認証情報
            username = self.config.get('bluesky', {}).get('username')
            password = self.config.get('bluesky', {}).get('password')
            
            # 認証情報が設定されているか確認
            if not all([username, password]):
                logger.error("Bluesky APIの認証情報が設定されていません")
                raise ValueError("Bluesky APIの認証情報が設定されていません")
            
            # 認証
            client = AtprotoClient()
            client.login(username, password)
            logger.info("Bluesky APIの認証に成功しました")
            
            return client
        except Exception as e:
            logger.error(f"Bluesky APIの認証に失敗しました: {e}")
            raise
    
    def _load_last_tweet_ids(self):
        """
        最後に処理したツイートIDを読み込む
        
        Returns:
            dict: ユーザー名をキー、最後に処理したツイートIDを値とする辞書
        """
        try:
            if os.path.exists(self.last_tweet_file):
                with open(self.last_tweet_file, 'r', encoding='utf-8') as file:
                    last_tweet_ids = json.load(file)
                    logger.info("最後に処理したツイートIDを読み込みました")
                    return last_tweet_ids
            else:
                logger.info("最後に処理したツイートIDのファイルが存在しないため、新規作成します")
                return {}
        except Exception as e:
            logger.error(f"最後に処理したツイートIDの読み込みに失敗しました: {e}")
            return {}
    
    def _save_last_tweet_ids(self):
        """最後に処理したツイートIDを保存する"""
        try:
            with open(self.last_tweet_file, 'w', encoding='utf-8') as file:
                json.dump(self.last_tweet_ids, file)
                logger.info("最後に処理したツイートIDを保存しました")
        except Exception as e:
            logger.error(f"最後に処理したツイートIDの保存に失敗しました: {e}")
    
    def get_user_tweets(self, username, count=10):
        """
        ユーザーの最新ツイートを取得する
        
        Args:
            username (str): ユーザー名（@は不要）
            count (int, optional): 取得するツイート数
            
        Returns:
            list: ツイート情報のリスト
        """
        try:
            # ユーザーのツイートを取得
            tweets = self.twitter_api.user_timeline(
                screen_name=username,
                count=count,
                tweet_mode='extended',
                include_rts=True  # リツイートも含める（後でフィルタリング）
            )
            
            logger.info(f"ユーザーツイート取得成功: @{username} - {len(tweets)}件")
            return tweets
        except Exception as e:
            logger.error(f"ユーザーツイート取得失敗: @{username} - {e}")
            return []
    
    def is_mention_or_retweet(self, tweet):
        """
        メンションまたはリツイートかどうかを判定する
        
        Args:
            tweet: ツイートオブジェクト
            
        Returns:
            bool: メンションまたはリツイートの場合はTrue
        """
        # リツイートの判定
        if hasattr(tweet, 'retweeted_status') or tweet.full_text.startswith('RT @'):
            logger.debug(f"リツイートを除外します: {tweet.full_text[:30]}...")
            return True
        
        # メンションの判定（先頭が@で始まる場合）
        if tweet.full_text.strip().startswith('@'):
            logger.debug(f"メンションを除外します: {tweet.full_text[:30]}...")
            return True
        
        # 引用リツイートの判定（URLが含まれていて、"https://twitter.com/"が含まれている場合）
        if "https://twitter.com/" in tweet.full_text or "https://x.com/" in tweet.full_text:
            # 引用リツイートでも、自分のオリジナルコンテンツがある場合は投稿する
            # ただし、URLだけの場合や短いコメントだけの場合は除外
            text_without_url = tweet.full_text
            for url in tweet.entities.get('urls', []):
                text_without_url = text_without_url.replace(url['url'], '')
            
            # URLを除いたテキストが短すぎる場合は引用リツイートとみなして除外
            if len(text_without_url.strip()) < 10:
                logger.debug(f"引用リツイート（短いコメント）を除外します: {tweet.full_text[:30]}...")
                return True
        
        return False
    
    def post_to_bluesky(self, text):
        """
        Blueskyに投稿する
        
        Args:
            text (str): 投稿テキスト
            
        Returns:
            bool: 投稿成功の場合はTrue
        """
        try:
            # Twitterの短縮URLをできるだけ展開
            expanded_text = text
            
            # Blueskyに投稿
            response = self.bluesky_client.send_post(expanded_text)
            logger.info(f"Blueskyへの投稿に成功しました: {expanded_text[:30]}...")
            return True
        except Exception as e:
            logger.error(f"Blueskyへの投稿に失敗しました: {e}")
            return False
    
    def process_new_tweets(self, username):
        """
        新しいツイートを処理する
        
        Args:
            username (str): ユーザー名（@は不要）
            
        Returns:
            int: 処理したツイート数
        """
        try:
            # 最後に処理したツイートIDを取得
            last_tweet_id = self.last_tweet_ids.get(username)
            
            # ツイートを取得
            max_tweets = self.config.get('monitor', {}).get('max_tweets_per_check', 10)
            tweets = self.get_user_tweets(username, count=max_tweets)
            
            if not tweets:
                logger.warning(f"処理対象のツイートがありません: @{username}")
                return 0
            
            # 新しいツイートをフィルタリング
            new_tweets = []
            if last_tweet_id:
                for tweet in tweets:
                    if str(tweet.id) > last_tweet_id:
                        new_tweets.append(tweet)
            else:
                # 最初の実行時は最新の1件のみを対象とする
                if tweets:
                    new_tweets = [tweets[0]]
            
            # メンションとリツイートを除外
            filtered_tweets = [tweet for tweet in new_tweets if not self.is_mention_or_retweet(tweet)]
            
            # 除外されたツイート数をログに記録
            excluded_count = len(new_tweets) - len(filtered_tweets)
            if excluded_count > 0:
                logger.info(f"{excluded_count}件のメンション/リツイートを除外しました: @{username}")
            
            # 処理したツイート数
            processed_count = 0
            
            # 新しいツイートをBlueskyに投稿
            if filtered_tweets:
                logger.info(f"{len(filtered_tweets)}件の新しいツイートを処理します: @{username}")
                
                for tweet in filtered_tweets:
                    # Blueskyに投稿
                    success = self.post_to_bluesky(tweet.full_text)
                    
                    if success:
                        processed_count += 1
                    
                    # 最後に処理したツイートIDを更新
                    self.last_tweet_ids[username] = str(tweet.id)
                
                # 最後に処理したツイートIDを保存
                self._save_last_tweet_ids()
            else:
                logger.info(f"処理対象の新しいツイートはありません: @{username}")
            
            return processed_count
        except Exception as e:
            logger.error(f"ツイート処理中にエラーが発生しました: {e}")
            return 0
    
    def run(self):
        """定期実行を開始する"""
        try:
            # 監視対象のユーザーを取得
            target_users = self.config.get('target_users', [])
            
            if not target_users:
                logger.warning("監視対象のユーザーが設定されていません")
                return
            
            logger.info(f"{len(target_users)}人のユーザーを監視します")
            
            # 監視間隔（分）
            interval_minutes = self.config.get('monitor', {}).get('interval_minutes', 5)
            interval_seconds = interval_minutes * 60
            
            logger.info(f"監視間隔: {interval_minutes}分")
            
            while True:
                total_processed = 0
                
                for user in target_users:
                    username = user.get('username')
                    
                    if not username:
                        continue
                    
                    logger.info(f"ユーザーの監視を開始します: @{username}")
                    
                    # 新しいツイートを処理
                    processed_count = self.process_new_tweets(username)
                    total_processed += processed_count
                    
                    # ユーザー間の処理間隔を空ける
                    time.sleep(1)
                
                logger.info(f"合計{total_processed}件のツイートをBlueskyに投稿しました")
                
                # 次の実行まで待機
                logger.info(f"{interval_minutes}分後に再実行します")
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            logger.info("プログラムを終了します")
        except Exception as e:
            logger.error(f"実行中にエラーが発生しました: {e}")
    
    def run_once(self):
        """1回だけ実行する"""
        try:
            # 監視対象のユーザーを取得
            target_users = self.config.get('target_users', [])
            
            if not target_users:
                logger.warning("監視対象のユーザーが設定されていません")
                return
            
            logger.info(f"{len(target_users)}人のユーザーを監視します")
            
            total_processed = 0
            
            for user in target_users:
                username = user.get('username')
                
                if not username:
                    continue
                
                logger.info(f"ユーザーの監視を開始します: @{username}")
                
                # 新しいツイートを処理
                processed_count = self.process_new_tweets(username)
                total_processed += processed_count
                
                # ユーザー間の処理間隔を空ける
                time.sleep(1)
            
            logger.info(f"合計{total_processed}件のツイートをBlueskyに投稿しました")
            
        except Exception as e:
            logger.error(f"実行中にエラーが発生しました: {e}")

# メイン処理
if __name__ == "__main__":
    try:
        logger.info("Twitter→Bluesky自動投稿ツールを起動します")
        
        # コマンドライン引数の解析
        import argparse
        parser = argparse.ArgumentParser(description='TwitterからBlueskyに投稿を自動転送するツール')
        parser.add_argument('--config', help='設定ファイルのパス')
        parser.add_argument('--once', action='store_true', help='1回だけ実行する')
        args = parser.parse_args()
        
        # TwitterToBlueskyインスタンスの作成
        twitter_to_bluesky = TwitterToBluesky(config_path=args.config)
        
        # 実行モードの判定
        if args.once:
            logger.info("1回だけ実行します")
            twitter_to_bluesky.run_once()
        else:
            logger.info("定期実行モードで起動します")
            twitter_to_bluesky.run()
        
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {e}")
        sys.exit(1)
