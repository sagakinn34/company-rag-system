"""
Discord データ取得・処理モジュール
Discord サーバーのチャット履歴を取得して、テキストデータ化します
"""

import os
import json
import asyncio
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional

import discord

from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

class DiscordProcessor:
    def __init__(self):
        """Discord プロセッサーを初期化"""
        self.token = os.getenv('DISCORD_BOT_TOKEN')
        
        if not self.token:
            raise ValueError("DISCORD_BOT_TOKEN が設定されていません")
        
        # Intentsを設定（メッセージ内容を読み取るため）
        intents = discord.Intents.default()
        intents.message_content = True  # メッセージ内容の読み取り
        intents.guilds = True          # サーバー情報の読み取り
        
        self.client = discord.Client(intents=intents)
        
        # データ保存用ディレクトリ
        self.data_dir = "./data/discord"
        os.makedirs(self.data_dir, exist_ok=True)
        
        print("✅ Discord プロセッサーを初期化しました")

# テスト実行用
if __name__ == "__main__":
    print("=== Discord プロセッサー テスト実行 ===")
    
    # ここにあなたのDiscordサーバーIDを入力してください
    SERVER_ID = 123456789012345678  # ← これを実際のサーバーIDに変更
    
    if SERVER_ID == 123456789012345678:
        print("⚠️ SERVER_ID を実際のDiscordサーバーIDに変更してください")
        print("\n📝 サーバーIDの取得方法:")
        print("   1. Discord でサーバー名を右クリック")
        print("   2. 「IDをコピー」をクリック")
        print("   3. このファイルを編集して SERVER_ID に貼り付け")
    else:
        print("✅ Discordプロセッサーの初期化に成功しました")

