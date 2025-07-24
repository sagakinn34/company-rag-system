import sys
sys.path.append('src')
import os

def final_integration():
    print("🚀 正しいメソッド名での最終統合開始...")
    
    documents = []
    
    # Notionデータ取得（正しいメソッド名使用）
    print("📝 Notionデータ取得中...")
    try:
        from notion_processor import NotionProcessor
        notion = NotionProcessor(os.getenv('NOTION_TOKEN'))
        
        print("📝 process_all_content()メソッドを実行中...")
        notion_docs = notion.process_all_content()
        
        if notion_docs:
            documents.extend(notion_docs)
            print(f"✅ Notion: {len(notion_docs)}件取得成功")
        else:
            print("⚠️ Notionからデータが取得できませんでした")
            
    except Exception as e:
        print(f"❌ Notion処理エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # Google Driveデータ取得（正しいメソッド名使用）
    print("📂 Google Driveデータ取得中...")
    try:
        from gdrive_processor import GoogleDriveProcessor
        gdrive = GoogleDriveProcessor(os.getenv('GOOGLE_DRIVE_CREDENTIALS'))
        
        print("📂 process_all_files()メソッドを実行中...")
        gdrive_docs = gdrive.process_all_files()
        
        if gdrive_docs:
            documents.extend(gdrive_docs)
            print(f"✅ Google Drive: {len(gdrive_docs)}件取得成功")
        else:
            print("⚠️ Google Driveからデータが取得できませんでした")
            
    except Exception as e:
        print(f"❌ Google Drive処理エラー: {e}")
        import traceback
        traceback.print_exc()
    
    # ベクトルDBに統合
    if documents:
        print(f"🔄 合計{len(documents)}件をベクトルDBに統合中...")
        try:
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            vector_db.add_documents(documents)
            
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
            import traceback
            traceback.print_exc()
            return False
    else:
        print("❌ 統合するデータがありません")
        return False

if __name__ == "__main__":
    success = final_integration()
    if success:
        print("\n🎊 次のステップ:")
        print("streamlit run app.py")
    else:
        print("\n❌ 統合に失敗しました")
