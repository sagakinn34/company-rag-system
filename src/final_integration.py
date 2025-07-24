import sys
import os
import streamlit as st

# 絶対パスでsrcディレクトリを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', 'src') if 'src' not in current_dir else current_dir
sys.path.insert(0, src_path)

import importlib

def get_correct_class_name():
    """正しいクラス名を動的に検出"""
    try:
        gdrive_file = os.path.join(src_path, 'gdrive_processor.py')
        with open(gdrive_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # class で始まる行を探す
        for line in content.split('\n'):
            if line.strip().startswith('class ') and ':' in line:
                class_name = line.strip().split('class ')[1].split('(')[0].split(':')[0].strip()
                if class_name and class_name != 'object':
                    return class_name
        return None
    except Exception as e:
        print(f"クラス名検出エラー: {e}")
        return None

def run_data_integration():
    """詳細ログ付きデータ統合関数"""
    print("🚀ーーーーーーーーーーーーーーーーーーーーーーーー")
    print("🚀 データ統合を開始...")
    print("🚀ーーーーーーーーーーーーーーーーーーーーーーーー")
    
    if 'st' in globals():
        st.info("🚀 データ統合を開始...")
    
    try:
        documents = []
        
        # 1. Notionプロセッサー
        print("📝ーーーーーーーーーーーーーーーーーーーーーーーー")
        print("📝 Notionからデータ取得中...")
        print("📝ーーーーーーーーーーーーーーーーーーーーーーーー")
        
        if 'st' in globals():
            st.info("📝 Notionからデータ取得中...")
        
        try:
            # Notion TOKENの確認
            notion_token = st.secrets.get("NOTION_TOKEN") if 'st' in globals() else os.getenv("NOTION_TOKEN")
            print(f"📝 NOTION_TOKEN設定状況: {'✅ 設定済み' if notion_token else '❌ 未設定'}")
            
            if notion_token:
                from notion_processor import NotionProcessor
                print("📝 NotionProcessorインポート成功")
                
                notion = NotionProcessor()
                print("📝 NotionProcessorインスタンス作成成功")
                
                notion_docs = notion.get_all_pages()
                print(f"📝 Notion取得結果: {type(notion_docs)}, 件数: {len(notion_docs) if notion_docs else 0}")
                
                if notion_docs:
                    documents.extend(notion_docs)
                    print(f"✅ Notion: {len(notion_docs)}件取得成功")
                    if 'st' in globals():
                        st.success(f"✅ Notion: {len(notion_docs)}件取得成功")
                else:
                    print("⚠️ Notionデータが空です")
                    if 'st' in globals():
                        st.warning("⚠️ Notionデータが空です")
            else:
                print("❌ NOTION_TOKENが設定されていません")
                if 'st' in globals():
                    st.error("❌ NOTION_TOKENが設定されていません")
                
        except ImportError as e:
            print(f"❌ NotionProcessor インポートエラー: {e}")
            if 'st' in globals():
                st.error(f"❌ NotionProcessor インポートエラー: {e}")
        except Exception as e:
            print(f"❌ Notion取得エラー: {e}")
            if 'st' in globals():
                st.error(f"❌ Notion取得エラー: {e}")
        
        # 2. Google Driveプロセッサー
        print("📂ーーーーーーーーーーーーーーーーーーーーーーーー")
        print("📂 Google Driveからデータ取得中...")
        print("📂ーーーーーーーーーーーーーーーーーーーーーーーー")
        
        if 'st' in globals():
            st.info("📂 Google Driveからデータ取得中...")
        
        try:
            # Google Drive認証の確認
            gdrive_creds = st.secrets.get("GOOGLE_DRIVE_CREDENTIALS") if 'st' in globals() else os.getenv("GOOGLE_DRIVE_CREDENTIALS")
            print(f"📂 GOOGLE_DRIVE_CREDENTIALS設定状況: {'✅ 設定済み' if gdrive_creds else '❌ 未設定'}")
            
            if gdrive_creds:
                # 正しいクラス名を取得
                gdrive_class_name = get_correct_class_name()
                print(f"🔍 検出されたクラス名: {gdrive_class_name}")
                
                if gdrive_class_name:
                    # 動的インポート
                    gdrive_module = importlib.import_module('gdrive_processor')
                    print("📂 gdrive_processorインポート成功")
                    
                    GDriveClass = getattr(gdrive_module, gdrive_class_name)
                    print(f"📂 {gdrive_class_name}クラス取得成功")
                    
                    gdrive = GDriveClass()
                    print("📂 Google Driveインスタンス作成成功")
                    
                    gdrive_docs = gdrive.get_all_files()
                    print(f"📂 Google Drive取得結果: {type(gdrive_docs)}, 件数: {len(gdrive_docs) if gdrive_docs else 0}")
                    
                    if gdrive_docs:
                        documents.extend(gdrive_docs)
                        print(f"✅ Google Drive: {len(gdrive_docs)}件取得成功")
                        if 'st' in globals():
                            st.success(f"✅ Google Drive: {len(gdrive_docs)}件取得成功")
                    else:
                        print("⚠️ Google Driveデータが空です")
                        if 'st' in globals():
                            st.warning("⚠️ Google Driveデータが空です")
                else:
                    print("❌ Google Driveクラス名を検出できませんでした")
                    if 'st' in globals():
                        st.error("❌ Google Driveクラス名を検出できませんでした")
            else:
                print("❌ GOOGLE_DRIVE_CREDENTIALSが設定されていません")
                if 'st' in globals():
                    st.error("❌ GOOGLE_DRIVE_CREDENTIALSが設定されていません")
                    
        except ImportError as e:
            print(f"❌ Google Drive モジュール インポートエラー: {e}")
            if 'st' in globals():
                st.error(f"❌ Google Drive モジュール インポートエラー: {e}")
        except Exception as e:
            print(f"❌ Google Drive取得エラー: {e}")
            if 'st' in globals():
                st.error(f"❌ Google Drive取得エラー: {e}")
        
        # 3. Discordプロセッサー
        print("💬ーーーーーーーーーーーーーーーーーーーーーーーー")
        print("💬 Discordからデータ取得中...")
        print("💬ーーーーーーーーーーーーーーーーーーーーーーーー")
        
        if 'st' in globals():
            st.info("💬 Discordからデータ取得中...")
        
        try:
            # Discord TOKENの確認
            discord_token = st.secrets.get("DISCORD_TOKEN") if 'st' in globals() else os.getenv("DISCORD_TOKEN")
            print(f"💬 DISCORD_TOKEN設定状況: {'✅ 設定済み' if discord_token else '❌ 未設定'}")
            
            if discord_token:
                from discord_processor import DiscordProcessor
                print("💬 DiscordProcessorインポート成功")
                
                discord = DiscordProcessor()
                print("💬 DiscordProcessorインスタンス作成成功")
                
                discord_docs = discord.get_all_messages()
                print(f"💬 Discord取得結果: {type(discord_docs)}, 件数: {len(discord_docs) if discord_docs else 0}")
                
                if discord_docs:
                    documents.extend(discord_docs)
                    print(f"✅ Discord: {len(discord_docs)}件取得成功")
                    if 'st' in globals():
                        st.success(f"✅ Discord: {len(discord_docs)}件取得成功")
                else:
                    print("⚠️ Discordデータが空です")
                    if 'st' in globals():
                        st.warning("⚠️ Discordデータが空です")
            else:
                print("❌ DISCORD_TOKENが設定されていません")
                if 'st' in globals():
                    st.error("❌ DISCORD_TOKENが設定されていません")
                    
        except ImportError as e:
            print(f"❌ DiscordProcessor インポートエラー: {e}")
            if 'st' in globals():
                st.error(f"❌ DiscordProcessor インポートエラー: {e}")
        except Exception as e:
            print(f"❌ Discord取得エラー: {e}")
            if 'st' in globals():
                st.error(f"❌ Discord取得エラー: {e}")
        
        # 4. ベクトルDBに統合
        print("🔄ーーーーーーーーーーーーーーーーーーーーーーーー")
        print(f"🔄 統合処理: 合計{len(documents)}件のデータを処理中...")
        print("🔄ーーーーーーーーーーーーーーーーーーーーーーーー")
        
        if documents:
            print(f"🔄 {len(documents)}件をベクトルDBに統合中...")
            if 'st' in globals():
                st.info(f"🔄 {len(documents)}件をベクトルDBに統合中...")
            
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            vector_db.add_documents(documents)
            
            # 確認
            final_count = vector_db.collection.count()
            print(f"🎉 統合完了! データベース件数: {final_count}件")
            
            if 'st' in globals():
                st.success(f"🎉 データ統合完了: {final_count}件")
            
            return True
        else:
            print("❌ 統合するデータがありません")
            print("❌ 全てのサービスでデータが0件でした")
            
            if 'st' in globals():
                st.warning("⚠️ 統合するデータが見つかりませんでした")
                st.error("❌ 全てのサービスでデータが0件でした")
            
            return False
            
    except Exception as e:
        print(f"❌ 統合エラー: {e}")
        if 'st' in globals():
            st.error(f"❌ 統合エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def safe_integration():
    """下位互換性のための関数"""
    return run_data_integration()

# 直接実行時のテスト
if __name__ == "__main__":
    safe_integration()
