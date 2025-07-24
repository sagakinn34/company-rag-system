import sys
sys.path.append('src')
import os

def safe_integration():
    print("🚀 安全なデータ統合を開始...")
    
    try:
        # 個別にインポートしてエラーを特定
        print("📝 Notionプロセッサーをインポート中...")
        from notion_processor import NotionProcessor
        
        print("📁 Google Driveプロセッサーをインポート中...")
        from gdrive_processor import GDriveProcessor
        
        print("🔍 ベクトルDBプロセッサーをインポート中...")
        from vector_db_processor import VectorDBProcessor
        
        # 初期化
        documents = []
        
        print("📊 Notionからデータ取得中...")
        try:
            notion = NotionProcessor()
            notion_docs = notion.get_all_pages()
            if notion_docs:
                documents.extend(notion_docs)
                print(f"✅ Notion: {len(notion_docs)}件取得成功")
            else:
                print("⚠️ Notionデータが空です")
        except Exception as e:
            print(f"❌ Notion取得エラー: {e}")
        
        print("📂 Google Driveからデータ取得中...")
        try:
            gdrive = GDriveProcessor()
            gdrive_docs = gdrive.get_all_files()
            if gdrive_docs:
                documents.extend(gdrive_docs)
                print(f"✅ Google Drive: {len(gdrive_docs)}件取得成功")
            else:
                print("⚠️ Google Driveデータが空です")
        except Exception as e:
            print(f"❌ Google Drive取得エラー: {e}")
        
        # ベクトルDBに追加
        if documents:
            print(f"🔄 {len(documents)}件をベクトルDBに統合中...")
            vector_db = VectorDBProcessor()
            vector_db.add_documents(documents)
            
            # 確認
            final_count = vector_db.collection.count()
            print(f"🎉 統合完了! データベース件数: {final_count}件")
            return True
        else:
            print("❌ 統合するデータがありません")
            return False
            
    except Exception as e:
        print(f"❌ 統合エラー: {e}")
        return False

if __name__ == "__main__":
    safe_integration()
