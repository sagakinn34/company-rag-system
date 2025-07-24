import os
import sys
import asyncio
from datetime import datetime
import logging

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.notion_processor import NotionProcessor
from src.discord_processor import DiscordProcessor
from src.vector_db_processor import VectorDBProcessor

# クラウド環境の判定
try:
    import streamlit as st
    if hasattr(st, 'secrets') or 'STREAMLIT' in os.environ:
        from src.gdrive_processor_cloud import GoogleDriveProcessorCloud as GoogleDriveProcessor
    else:
        from src.gdrive_processor import GoogleDriveProcessor
except ImportError:
    from src.gdrive_processor import GoogleDriveProcessor

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class IntegratedRAGSystemCloud:
    """統合RAGシステム（クラウド対応版）"""
    
    def __init__(self):
        """統合システムを初期化"""
        self.notion_processor = None
        self.gdrive_processor = None
        self.discord_processor = None
        self.vector_db = VectorDBProcessor()
        
        # 環境変数確認
        self._check_environment()
        
    def _check_environment(self):
        """必要な環境変数をチェック"""
        # Streamlit Secrets対応
        if hasattr(st, 'secrets'):
            required_vars = ['NOTION_TOKEN', 'OPENAI_API_KEY']
            missing_required = [var for var in required_vars if var not in st.secrets]
        else:
            required_vars = ['NOTION_TOKEN', 'OPENAI_API_KEY']
            missing_required = [var for var in required_vars if not os.getenv(var)]
            
        if missing_required:
            raise ValueError(f"必須環境変数が設定されていません: {missing_required}")
            
        # オプション設定確認
        discord_available = hasattr(st, 'secrets') and 'DISCORD_TOKEN' in st.secrets or os.getenv('DISCORD_TOKEN')
        gdrive_available = hasattr(st, 'secrets') and 'GOOGLE_DRIVE_CREDENTIALS' in st.secrets or os.getenv('GOOGLE_DRIVE_CREDENTIALS')
        
        if discord_available:
            logger.info("✅ Discord統合が有効です")
        else:
            logger.info("ℹ️ Discord統合は無効です（DISCORD_TOKENが未設定）")
            
        if gdrive_available:
            logger.info("✅ Google Drive統合が有効です")
        else:
            logger.info("ℹ️ Google Drive統合は無効です（認証情報が未設定）")
    
    async def process_all_sources(self, 
                                discord_guild_id: int = None,
                                discord_channels: list = None,
                                discord_days_back: int = 30):
        """
        全データソースを処理してベクトルDBに統合
        """
        all_documents = []
        
        try:
            # 1. Notion データ処理
            logger.info("🔄 Notionデータを処理中...")
            notion_token = st.secrets['NOTION_TOKEN'] if hasattr(st, 'secrets') else os.getenv('NOTION_TOKEN')
            self.notion_processor = NotionProcessor(notion_token)
            notion_docs = self.notion_processor.process_all_content()
            all_documents.extend(notion_docs)
            logger.info(f"✅ Notion: {len(notion_docs)}件のドキュメントを処理")
            
            # 2. Google Drive データ処理
            gdrive_available = hasattr(st, 'secrets') and 'GOOGLE_DRIVE_CREDENTIALS' in st.secrets or os.getenv('GOOGLE_DRIVE_CREDENTIALS')
            if gdrive_available:
                logger.info("🔄 Google Driveデータを処理中...")
                self.gdrive_processor = GoogleDriveProcessor()
                gdrive_docs = self.gdrive_processor.process_all_files()
                all_documents.extend(gdrive_docs)
                logger.info(f"✅ Google Drive: {len(gdrive_docs)}件のドキュメントを処理")
            
            # 3. Discord データ処理
            discord_token = st.secrets['DISCORD_TOKEN'] if hasattr(st, 'secrets') and 'DISCORD_TOKEN' in st.secrets else os.getenv('DISCORD_TOKEN')
            if discord_token and discord_guild_id:
                logger.info("🔄 Discordデータを処理中...")
                self.discord_processor = DiscordProcessor(discord_token)
                
                discord_docs = await self.discord_processor.process_guild_data(
                    guild_id=discord_guild_id,
                    days_back=discord_days_back,
                    max_messages=1000,
                    channels=discord_channels
                )
                all_documents.extend(discord_docs)
                logger.info(f"✅ Discord: {len(discord_docs)}件のメッセージを処理")
            
            # 4. ベクトルDB統合
            logger.info("🔄 ベクトルデータベースに統合中...")
            self.vector_db.clear_database()
            self.vector_db.add_documents(all_documents)
            
            # 5. 統計情報
            logger.info("\n📊 統合完了統計:")
            logger.info(f"   総ドキュメント数: {len(all_documents)}")
            logger.info(f"   Notion: {len([d for d in all_documents if d.get('source') == 'Notion'])}")
            
            gdrive_count = len([d for d in all_documents if d.get('source') == 'Google Drive'])
            if gdrive_count > 0:
                logger.info(f"   Google Drive: {gdrive_count}")
                
            discord_count = len([d for d in all_documents if d.get('source') == 'Discord'])
            if discord_count > 0:
                logger.info(f"   Discord: {discord_count}")
            
            logger.info(f"✅ 統合処理が完了しました！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 統合処理エラー: {e}")
            return False

# 使用例
async def main():
    """統合処理のメイン関数（クラウド環境用）"""
    try:
        system = IntegratedRAGSystemCloud()
        
        # Discord設定（環境変数から自動取得）
        DISCORD_GUILD_ID = None
        DISCORD_CHANNELS = None
        
        # 統合処理実行
        success = await system.process_all_sources(
            discord_guild_id=DISCORD_GUILD_ID,
            discord_channels=DISCORD_CHANNELS,
            discord_days_back=30
        )
        
        if success:
            logger.info("🎉 RAGシステムの統合が完了しました！")
        else:
            logger.error("❌ 統合処理に失敗しました。")
            
    except Exception as e:
        logger.error(f"メイン処理エラー: {e}")

if __name__ == "__main__":
    asyncio.run(main())
