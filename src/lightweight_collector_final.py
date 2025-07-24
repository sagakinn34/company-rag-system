#!/usr/bin/env python3
"""
軽量データ収集・統合プロセッサー（最終版）
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from notion_processor import NotionProcessor
from gdrive_processor import GoogleDriveProcessor
from vector_db_processor import VectorDBProcessor
from dotenv import load_dotenv

def collect_notion_data(limit=10):
    """Notionデータを制限付きで収集"""
    try:
        print("📄 Notionデータ収集中（最大10件）...")
        
        load_dotenv()
        notion_token = os.getenv('NOTION_TOKEN')
        
        if not notion_token:
            print("❌ NOTION_TOKEN環境変数が設定されていません")
            return []
        
        notion = NotionProcessor(notion_token)
        
        # search_pagesメソッドを使用
        pages = notion.search_pages()
        print(f"   利用可能ページ: {len(pages)}件")
        
        documents = []
        
        # 制限適用
        limited_pages = pages[:limit]
        
        for i, page in enumerate(limited_pages):
            try:
                # get_page_contentメソッドでコンテンツ取得
                content = notion.get_page_content(page['id'])
                if content and len(content.strip()) > 10:
                    documents.append({
                        'content': content,
                        'metadata': {
                            'title': page.get('title', f'ページ{i+1}'),
                            'source': 'notion',
                            'id': page['id']
                        }
                    })
                    print(f"   📄 処理済み: {len(documents)}件", end='\r')
            except Exception as e:
                print(f"   ⚠️ ページ{i+1}処理エラー: {e}")
                continue
        
        print(f"\n✅ Notion収集完了: {len(documents)}件")
        return documents
        
    except Exception as e:
        print(f"❌ Notion収集エラー: {e}")
        return []

def collect_gdrive_data(limit=10):
    """Google Driveデータを制限付きで収集"""
    try:
        print("📁 Google Driveデータ収集中（最大10件）...")
        
        load_dotenv()
        credentials_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS')
        
        if not credentials_path:
            print("❌ GOOGLE_DRIVE_CREDENTIALS環境変数が設定されていません")
            return []
        
        gdrive = GoogleDriveProcessor(credentials_path)
        
        # list_filesメソッドを使用
        files = gdrive.list_files()
        print(f"   利用可能ファイル: {len(files)}件")
        
        documents = []
        
        # 制限適用
        limited_files = files[:limit]
        
        for i, file_info in enumerate(limited_files):
            try:
                # download_and_extract_textメソッドでコンテンツ取得
                content = gdrive.download_and_extract_text(file_info['id'])
                if content and len(content.strip()) > 10:
                    documents.append({
                        'content': content,
                        'metadata': {
                            'title': file_info.get('name', f'ファイル{i+1}'),
                            'source': 'google_drive',
                            'id': file_info['id']
                        }
                    })
                    print(f"   📁 処理済み: {len(documents)}件", end='\r')
                else:
                    print(f"   ⚠️ ファイル{i+1}: 内容が空またはエラー")
            except Exception as e:
                print(f"   ⚠️ ファイル{i+1}処理エラー: {e}")
                continue
        
        print(f"\n✅ Google Drive収集完了: {len(documents)}件")
        return documents
        
    except Exception as e:
        print(f"❌ Google Drive収集エラー: {e}")
        return []

def immediate_integration(documents, batch_size=1):
    """即座にベクトルDBに統合（1件ずつ）"""
    if not documents:
        print("❌ 統合するデータがありません")
        return False
        
    try:
        print(f"💾 {len(documents)}件をベクトルDBに統合中...")
        processor = VectorDBProcessor()
        
        initial_count = processor.collection.count()
        print(f"   統合前のDB件数: {initial_count}件")
        
        # 1件ずつ処理
        for i, doc in enumerate(documents):
            try:
                print(f"📦 {i+1}/{len(documents)}: 処理中...")
                processor.add_documents([doc])
                
                current_count = processor.collection.count()
                print(f"   現在のDB件数: {current_count}件")
                
            except Exception as e:
                print(f"   ⚠️ 文書{i+1}処理エラー: {e}")
                continue
        
        final_count = processor.collection.count()
        added_count = final_count - initial_count
        print(f"🎉 統合完了！追加件数: {added_count}件、最終件数: {final_count}件")
        return final_count > initial_count
        
    except Exception as e:
        print(f"❌ 統合エラー: {e}")
        return False

def main():
    print("🚀 軽量データ収集・統合システム（最終版）")
    print("=" * 50)
    
    all_documents = []
    
    # Notionデータ収集（少量）
    notion_docs = collect_notion_data(limit=5)
    all_documents.extend(notion_docs)
    
    # Google Driveデータ収集（少量）
    gdrive_docs = collect_gdrive_data(limit=5)
    all_documents.extend(gdrive_docs)
    
    print(f"\n📊 収集完了: 合計 {len(all_documents)}件")
    
    if not all_documents:
        print("❌ データが収集できませんでした")
        print("\n🔍 トラブルシューティング:")
        print("1. 環境変数が正しく設定されているか確認")
        print("2. NotionとGoogle Driveの認証情報が有効か確認")
        print("3. インターネット接続を確認")
        return
    
    # 即座に統合実行
    success = immediate_integration(all_documents)
    
    if success:
        print("\n✅ システム準備完了！🎉")
        print("🔍 検索テスト可能な状態です")
        
        print("\n📋 次のステップ:")
        print("   python src/search_tool.py")
        print("   python src/ai_assistant.py")
        
        # 簡単な動作確認
        print("\n🧪 簡単な動作確認:")
        try:
            test_processor = VectorDBProcessor()
            count = test_processor.collection.count()
            print(f"   最終DB件数: {count}件")
            if count > 5:
                print("   🎉 十分なデータが統合されました！")
            elif count > 2:
                print("   ✅ 基本的な検索テストが可能です")
            else:
                print("   ⚠️ データが少ないですが、動作テストは可能です")
        except Exception as e:
            print(f"   ❌ 動作確認エラー: {e}")
            
    else:
        print("\n❌ 統合で問題が発生しました")
        print("しかし、基本的なシステムは動作するはずです")

if __name__ == "__main__":
    main()
