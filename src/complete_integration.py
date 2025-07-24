import sys
sys.path.append('src')
import os

def complete_integration():
    print("🚀 完全版データ統合を開始...")
    
    try:
        documents = []
        
        # 環境変数確認
        notion_token = os.getenv('NOTION_TOKEN')
        openai_key = os.getenv('OPENAI_API_KEY')
        gdrive_creds = os.getenv('GOOGLE_DRIVE_CREDENTIALS')
        
        print(f"🔑 認証情報確認:")
        print(f"  - NOTION_TOKEN: {'✅ 設定済み' if notion_token else '❌ 未設定'}")
        print(f"  - OPENAI_API_KEY: {'✅ 設定済み' if openai_key else '❌ 未設定'}")
        print(f"  - GOOGLE_DRIVE_CREDENTIALS: {'✅ 設定済み' if gdrive_creds else '❌ 未設定'}")
        
        # Notionプロセッサー（引数付き）
        if notion_token:
            print("📝 Notionからデータ取得中...")
            try:
                from notion_processor import NotionProcessor
                notion = NotionProcessor(notion_token)
                notion_docs = notion.get_all_pages()
                if notion_docs:
                    documents.extend(notion_docs)
                    print(f"✅ Notion: {len(notion_docs)}件取得成功")
                else:
                    print("⚠️ Notionデータが空です")
            except Exception as e:
                print(f"❌ Notion取得エラー: {e}")
        else:
            print("❌ NotionTokenが設定されていません")
        
        # Google Driveプロセッサー（引数付き）
        if gdrive_creds and os.path.exists(gdrive_creds):
            print("📂 Google Driveからデータ取得中...")
            try:
                from gdrive_processor import GoogleDriveProcessor
                gdrive = GoogleDriveProcessor(gdrive_creds)
                gdrive_docs = gdrive.get_all_files()
                if gdrive_docs:
                    documents.extend(gdrive_docs)
                    print(f"✅ Google Drive: {len(gdrive_docs)}件取得成功")
                else:
                    print("⚠️ Google Driveデータが空です")
            except Exception as e:
                print(f"❌ Google Drive取得エラー: {e}")
        else:
            print("❌ Google Drive認証ファイルが見つかりません")
        
        # ベクトルDBに追加
        if documents:
            print(f"🔄 {len(documents)}件をベクトルDBに統合中...")
            from vector_db_processor import VectorDBProcessor
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
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    complete_integration()
