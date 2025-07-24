import sys
sys.path.append('src')
import os

def working_integration():
    print("🚀 動作確認済み統合スクリプト開始...")
    
    documents = []
    
    # Notionデータ取得
    print("📝 Notionデータ取得中...")
    try:
        from notion_processor import NotionProcessor
        notion_token = os.getenv('NOTION_TOKEN')
        
        # 引数ありで初期化（テストで成功したパターン）
        notion = NotionProcessor(notion_token)
        notion_docs = notion.get_all_pages()
        
        if notion_docs:
            documents.extend(notion_docs)
            print(f"✅ Notion: {len(notion_docs)}件取得成功")
        else:
            print("⚠️ Notionからデータが取得できませんでした")
            
    except Exception as e:
        print(f"❌ Notion処理エラー: {e}")
    
    # Google Driveデータ取得
    print("📂 Google Driveデータ取得中...")
    try:
        from gdrive_processor import GoogleDriveProcessor
        gdrive_creds = os.getenv('GOOGLE_DRIVE_CREDENTIALS')
        
        # 引数ありで初期化（テストで成功したパターン）
        gdrive = GoogleDriveProcessor(gdrive_creds)
        gdrive_docs = gdrive.get_all_files()
        
        if gdrive_docs:
            documents.extend(gdrive_docs)
            print(f"✅ Google Drive: {len(gdrive_docs)}件取得成功")
        else:
            print("⚠️ Google Driveからデータが取得できませんでした")
            
    except Exception as e:
        print(f"❌ Google Drive処理エラー: {e}")
    
    # ベクトルDBに統合
    if documents:
        print(f"🔄 合計{len(documents)}件をベクトルDBに統合中...")
        try:
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            vector_db.add_documents(documents)
            
            # 最終確認
            final_count = vector_db.collection.count()
            print(f"🎉 統合成功! 最終データベース件数: {final_count}件")
            
            if final_count > 0:
                print("✅ データ統合完了 - システム利用可能!")
                return True
            else:
                print("❌ データベースが空のままです")
                return False
                
        except Exception as e:
            print(f"❌ ベクトルDB統合エラー: {e}")
            return False
    else:
        print("❌ 統合するデータがありません - データソースを確認してください")
        return False

if __name__ == "__main__":
    working_integration()
