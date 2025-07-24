"""
メイン統合処理スクリプト
全てのデータソースからデータを取得し、ベクトルデータベースに統合します
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict

from dotenv import load_dotenv

# 各プロセッサーをインポート
try:
    from notion_processor import NotionProcessor
    NOTION_AVAILABLE = True
except ImportError:
    NOTION_AVAILABLE = False
    print("⚠️ Notion processor が利用できません")

try:
    from gdrive_processor import GoogleDriveProcessor
    GDRIVE_AVAILABLE = True
except ImportError:
    GDRIVE_AVAILABLE = False
    print("⚠️ Google Drive processor が利用できません")

try:
    from discord_processor import DiscordProcessor, collect_discord_data
    DISCORD_AVAILABLE = True
except ImportError:
    DISCORD_AVAILABLE = False
    print("⚠️ Discord processor が利用できません")

try:
    from ocr_processor_dummy import DummyOCRProcessor as OCRProcessor
    OCR_AVAILABLE = True
    print("📝 ダミーOCRプロセッサーを使用します")
except ImportError:
    OCR_AVAILABLE = False
    print("⚠️ OCR processor が利用できません")

try:
    from vector_db_processor import VectorDBProcessor
    VECTOR_DB_AVAILABLE = True
except ImportError:
    VECTOR_DB_AVAILABLE = False
    print("⚠️ Vector DB processor が利用できません")

# 環境変数の読み込み
load_dotenv()

class MainProcessor:
    def __init__(self):
        """メインプロセッサーを初期化"""
        
        self.results_dir = "./data/results"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # 利用可能なプロセッサーを初期化
        self.processors = {}
        
        if VECTOR_DB_AVAILABLE:
            try:
                self.vector_db = VectorDBProcessor()
                print("✅ ベクトルデータベースを初期化しました")
            except Exception as e:
                print(f"❌ ベクトルデータベース初期化エラー: {e}")
                self.vector_db = None
        else:
            self.vector_db = None
        
        print("✅ メインプロセッサーを初期化しました")
    
    def collect_notion_data(self) -> List[Dict]:
        """Notionデータを収集"""
        if not NOTION_AVAILABLE:
            print("⚠️ Notion processor が利用できません")
            return []
        
        try:
            print("\n🔄 Notionデータの収集開始...")
            processor = NotionProcessor(notion_token=os.getenv("NOTION_TOKEN"))
            pages = processor.process_all_content()
            print(f"✅ Notion: {len(pages)} ページを収集しました")
            return pages
        except Exception as e:
            print(f"❌ Notionデータ収集エラー: {e}")
            return []
    
    def collect_gdrive_data(self) -> List[Dict]:
        """Google Driveデータを収集"""
        if not GDRIVE_AVAILABLE:
            print("⚠️ Google Drive processor が利用できません")
            return []
        
        try:
            print("\n🔄 Google Driveデータの収集開始...")
            processor = GoogleDriveProcessor(credentials_path=os.getenv("GOOGLE_DRIVE_CREDENTIALS"))
            files = processor.process_all_files()
            print(f"✅ Google Drive: {len(files)} ファイルを収集しました")
            return files
        except Exception as e:
            print(f"❌ Google Driveデータ収集エラー: {e}")
            return []
    
    def collect_discord_data(self, server_id: int = None) -> List[Dict]:
        """Discordデータを収集"""
        if not DISCORD_AVAILABLE:
            print("⚠️ Discord processor が利用できません")
            return []
        
        if not server_id:
            print("⚠️ Discord サーバーIDが設定されていません")
            return []
        
        try:
            print(f"\n🔄 Discordデータの収集開始... (サーバーID: {server_id})")
            
            import asyncio
            discord_data = asyncio.run(collect_discord_data(
                server_id,
                limit_per_channel=50,
                days_back=30
            ))
            
            if discord_data and discord_data.get('total_messages', 0) > 0:
                # Discordデータを統一フォーマットに変換
                converted_data = []
                for channel_data in discord_data.get('channels', []):
                    channel_info = channel_data['channel_info']
                    
                    # チャンネルの全メッセージを統合
                    all_messages = []
                    for message in channel_data['messages']:
                        msg_text = f"[{message['timestamp'][:10]}] {message['author']['name']}: {message['content']}"
                        all_messages.append(msg_text)
                    
                    if all_messages:
                        converted_item = {
                            'content': '\n'.join(all_messages),
                            'metadata': {
                                'title': f"Discord #{channel_info['name']}",
                                'source': 'discord',
                                'id': channel_info['id'],
                                'channel_name': channel_info['name'],
                                'message_count': len(all_messages),
                                'created_time': datetime.now().isoformat()
                            },
                            'word_count': len(' '.join(all_messages).split())
                        }
                        converted_data.append(converted_item)
                
                print(f"✅ Discord: {len(converted_data)} チャンネルを収集しました")
                return converted_data
            else:
                print("⚠️ Discordからメッセージが取得できませんでした")
                return []
                
        except Exception as e:
            print(f"❌ Discordデータ収集エラー: {e}")
            return []
    
    def process_all_data(self, discord_server_id: int = None) -> Dict:
        """全てのデータソースからデータを収集・処理"""
        print("🚀 全データソースからの収集を開始します...")
        
        all_documents = []
        collection_stats = {
            'notion_count': 0,
            'gdrive_count': 0, 
            'discord_count': 0,
            'total_count': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # Notionデータ収集
        notion_data = self.collect_notion_data()
        if notion_data:
            all_documents.extend(notion_data)
            collection_stats['notion_count'] = len(notion_data)
        
        # Google Driveデータ収集
        gdrive_data = self.collect_gdrive_data()
        if gdrive_data:
            all_documents.extend(gdrive_data)
            collection_stats['gdrive_count'] = len(gdrive_data)
        
        # Discordデータ収集
        if discord_server_id:
            discord_data = self.collect_discord_data(discord_server_id)
            if discord_data:
                all_documents.extend(discord_data)
                collection_stats['discord_count'] = len(discord_data)
        
        collection_stats['total_count'] = len(all_documents)
        collection_stats['end_time'] = datetime.now().isoformat()
        
        print(f"\n📊 データ収集完了:")
        print(f"   Notion: {collection_stats['notion_count']} 件")
        print(f"   Google Drive: {collection_stats['gdrive_count']} 件")
        print(f"   Discord: {collection_stats['discord_count']} 件")
        print(f"   合計: {collection_stats['total_count']} 件")
        
        # ベクトルデータベースに保存
        if self.vector_db and all_documents:
            print(f"\n💾 ベクトルデータベースに保存中...")
            success = self.vector_db.add_documents(all_documents)
            collection_stats['vector_db_success'] = success
        else:
            print("⚠️ ベクトルデータベースが利用できないか、データがありません")
            collection_stats['vector_db_success'] = False
        
        # 結果を保存
        self.save_results(all_documents, collection_stats)
        
        return {
            'documents': all_documents,
            'stats': collection_stats
        }
    
    def save_results(self, documents: List[Dict], stats: Dict):
        """結果をファイルに保存"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        try:
            # 統計情報を保存
            stats_file = f"{self.results_dir}/collection_stats_{timestamp}.json"
            with open(stats_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            
            # 全文書データを保存
            docs_file = f"{self.results_dir}/all_documents_{timestamp}.json"
            with open(docs_file, 'w', encoding='utf-8') as f:
                json.dump(documents, f, ensure_ascii=False, indent=2)
            
            print(f"💾 結果を保存しました:")
            print(f"   統計: {stats_file}")
            print(f"   文書: {docs_file}")
            
        except Exception as e:
            print(f"❌ 結果保存エラー: {e}")
    
    def search_system(self, query: str, n_results: int = 5) -> Dict:
        """統合検索システム"""
        if not self.vector_db:
            return {'error': 'ベクトルデータベースが利用できません'}
        
        return self.vector_db.search_documents(query, n_results)

# テスト実行用
if __name__ == "__main__":
    print("=== メイン統合処理 テスト実行 ===")
    
    try:
        processor = MainProcessor()
        
        # Discord サーバーID（設定する場合）
        DISCORD_SERVER_ID = None  # ← ここに実際のサーバーIDを入力
        
        print("\n🔄 データ収集・統合処理を開始...")
        
        # 全データを処理
        result = processor.process_all_data(discord_server_id=DISCORD_SERVER_ID)
        
        # 結果表示
        print(f"\n🎉 処理完了!")
        print(f"📊 最終統計:")
        for key, value in result['stats'].items():
            print(f"   {key}: {value}")
        
        # 検索テスト
        if result['stats']['total_count'] > 0:
            print(f"\n🔍 検索システムテスト:")
            test_query = "会社"
            search_results = processor.search_system(test_query)
            print(f"検索クエリ: '{test_query}'")
            print(f"結果数: {search_results.get('total_results', 0)}")
            
            for i, result_item in enumerate(search_results.get('results', [])[:2], 1):
                print(f"{i}. {result_item['content'][:100]}...")
        
    except KeyboardInterrupt:
        print("\n⏹️ 処理を中断しました")
    except Exception as e:
        print(f"❌ 実行エラー: {e}")
        import traceback
        print(traceback.format_exc())
