import sys
import os

# 絶対パスでsrcディレクトリを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', 'src') if 'src' not in current_dir else current_dir
sys.path.insert(0, src_path)

import importlib
import streamlit as st

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
    """Streamlitアプリから呼び出される統合関数"""
    print("🚀 データ統合を開始...")
    
    try:
        documents = []
        
        # Notionプロセッサー
        print("📝 Notionからデータ取得中...")
        try:
            from notion_processor import NotionProcessor
            notion = NotionProcessor()
            notion_docs = notion.get_all_pages()
            if notion_docs:
                documents.extend(notion_docs)
                print(f"✅ Notion: {len(notion_docs)}件取得成功")
            else:
                print("⚠️ Notionデータが空です")
        except Exception as e:
            print(f"❌ Notion取得エラー: {e}")
        
        # Google Driveプロセッサー（動的クラス名検出）
        print("📂 Google Driveからデータ取得中...")
        try:
            # 正しいクラス名を取得
            gdrive_class_name = get_correct_class_name()
            print(f"🔍 検出されたクラス名: {gdrive_class_name}")
            
            if gdrive_class_name:
                # 動的インポート
                gdrive_module = importlib.import_module('gdrive_processor')
                GDriveClass = getattr(gdrive_module, gdrive_class_name)
                
                gdrive = GDriveClass()
                gdrive_docs = gdrive.get_all_files()
                if gdrive_docs:
                    documents.extend(gdrive_docs)
                    print(f"✅ Google Drive: {len(gdrive_docs)}件取得成功")
                else:
                    print("⚠️ Google Driveデータが空です")
            else:
                print("❌ Google Driveクラス名を検出できませんでした")
        except Exception as e:
            print(f"❌ Google Drive取得エラー: {e}")
        
        # Discordプロセッサー（追加）
        print("💬 Discordからデータ取得中...")
        try:
            from discord_processor import DiscordProcessor
            discord = DiscordProcessor()
            discord_docs = discord.get_all_messages()
            if discord_docs:
                documents.extend(discord_docs)
                print(f"✅ Discord: {len(discord_docs)}件取得成功")
            else:
                print("⚠️ Discordデータが空です")
        except Exception as e:
            print(f"❌ Discord取得エラー: {e}")
        
        # ベクトルDBに追加
        if documents:
            print(f"🔄 {len(documents)}件をベクトルDBに統合中...")
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            vector_db.add_documents(documents)
            
            # 確認
            final_count = vector_db.collection.count()
            print(f"🎉 統合完了! データベース件数: {final_count}件")
            
            # Streamlitで結果表示
            if 'st' in globals():
                st.success(f"🎉 データ統合完了: {final_count}件")
            
            return True
        else:
            print("❌ 統合するデータがありません")
            if 'st' in globals():
                st.warning("⚠️ 統合するデータが見つかりませんでした")
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
