#!/usr/bin/env python3
"""
軽量データ収集・統合プロセッサー（完全修正版）
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from notion_processor import NotionProcessor
from gdrive_processor import GoogleDriveProcessor
from vector_db_processor import VectorDBProcessor
from dotenv import load_dotenv

def collect_notion_data(limit=20):
    """Notionデータを制限付きで収集"""
    try:
        print("📄 Notionデータ収集中（最大20件）...")
        
        # 環境変数読み込み
        load_dotenv()
        notion_token = os.getenv('NOTION_TOKEN')
        
        if not notion_token:
            print("❌ NOTION_TOKEN環境変数が設定されていません")
            return []
        
        notion = NotionProcessor(notion_token)  # トークンを渡す
        
        # ページ一覧取得
        pages = notion.get_pages()
        print(f"   利用可能ページ: {len(pages)}件")
        
        documents = []
        processed = 0
        
        for page in pages[:limit]:
            try:
                content = notion.get_page_content(page['id'])
                if content and len(content.strip()) > 10:  # 空でない内容のみ
                    documents.append({
                        'content': content,
                        'metadata': {
                            'title': page.get('title', '無題'),
                            'source': 'notion',
                            'id': page['id']
                        }
                    })
                    processed += 1
                    print(f"   📄 処理済み: {processed}件", end='\r')
            except Exception as e:
                continue
        
        print(f"\n✅ Notion収集完了: {len(documents)}件")
        return documents
        
    except Exception as e:
        print(f"❌ Notion収集エラー: {e}")
        return []

def collect_gdrive_data(limit=20):
    """Google Driveデータを制限付きで収集"""
    try:
        print("📁 Google Driveデータ収集中（最大20件）...")
        
        # 環境変数読み込み
        load_dotenv()
        credentials_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS')
        
        if not credentials_path:
            print("❌ GOOGLE_DRIVE_CREDENTIALS環境変数が設定されていません")
            return []
        
        gdrive = GoogleDriveProcessor(credentials_path)  # 認証情報を渡す
        
        # ファイル一覧取得
        files = gdrive.get_files()
        print(f"   利用可能ファイル: {len(files)}件")
        
        documents = []
        processed = 0
        
        for file_info in files[:limit]:
            try:
                content = gdrive.get_file_content(file_info['id'])
                if content and len(content.strip()) > 10:  # 空でない内容のみ
                    documents.append({
                        'content': content,
                        'metadata': {
                            'title': file_info.get('name', '無題'),
                            'source': 'google_drive',
                            'id': file_info['id']
                        }
                    })
                    processed += 1
                    print(f"   📁 処理済み: {processed}件", end='\r')
            except Exception as e:
                continue
        
        print(f"\n✅ Google Drive収集完了: {len(documents)}件")
        return documents
        
    except Exception as e:
        print(f"❌ Google Drive収集エラー: {e}")
        return []

def immediate_integration(documents, batch_size=3):
    """即座にベクトルDBに統合"""
    if not documents:
        print("❌ 統合するデータがありません")
        return False
        
    try:
        print(f"💾 {len(documents)}件をベクトルDBに統合中...")
        processor = VectorDBProcessor()
        
        # 現在のDB件数確認
        initial_count = processor.collection.count()
        print(f"   統合前のDB件数: {initial_count}件")
        
        # 小さなバッチで処理
        total_batches = (len(documents) + batch_size - 1) // batch_size
        
        for i in range(0, len(documents), batch_size):
            batch = documents[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"📦 バッチ {batch_num}/{total_batches}: {len(batch)}件処理中...")
            
            # バッチを処理
            processor.add_documents(batch)
            
            # 現在の件数確認
            current_count = processor.collection.count()
            print(f"   現在のDB件数: {current_count}件")
        
        final_count = processor.collection.count()
        added_count = final_count - initial_count
        print(f"🎉 統合完了！追加件数: {added_count}件、最終件数: {final_count}件")
        return True
        
    except Exception as e:
        print(f"❌ 統合エラー: {e}")
        return False

def main():
    print("🚀 軽量データ収集・統合システム（完全修正版）")
    print("=" * 50)
    
    # 環境変数の事前確認
    load_dotenv()
    print("🔍 環境変数確認:")
    print(f"   NOTION_TOKEN: {'設定済み' if os.getenv('NOTION_TOKEN') else '未設定'}")
    print(f"   GOOGLE_DRIVE_CREDENTIALS: {'設定済み' if os.getenv('GOOGLE_DRIVE_CREDENTIALS') else '未設定'}")
    print("")
    
    all_documents = []
    
    # Notionデータ収集
    notion_docs = collect_notion_data(limit=15)  # 更に制限
    all_documents.extend(notion_docs)
    
    # Google Driveデータ収集
    gdrive_docs = collect_gdrive_data(limit=15)  # 更に制限
    all_documents.extend(gdrive_docs)
    
    print(f"\n📊 収集完了: 合計 {len(all_documents)}件")
    
    if not all_documents:
        print("❌ データが収集できませんでした")
        return
    
    # 即座に統合実行
    success = immediate_integration(all_documents, batch_size=2)  # 最小バッチ
    
    if success:
        print("\n✅ システム準備完了！")
        print("🔍 検索テスト可能な状態です")
        
        # 検索テストの案内
        print("\n📋 次のステップ:")
        print("   python src/search_tool.py")
        print("   python src/ai_assistant.py")
    else:
        print("\n❌ 統合で問題が発生しました")

if __name__ == "__main__":
    main()
