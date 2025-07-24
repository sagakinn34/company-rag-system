#!/usr/bin/env python3
"""
最小限データ収集・統合プロセッサー（全エラー修正版）
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from notion_processor import NotionProcessor
from gdrive_processor import GoogleDriveProcessor
from vector_db_processor import VectorDBProcessor
from dotenv import load_dotenv

def collect_notion_safe(limit=3):
    """Notionデータを安全に収集"""
    try:
        print("📄 Notionデータ収集中...")
        
        load_dotenv()
        notion_token = os.getenv('NOTION_TOKEN')
        notion = NotionProcessor(notion_token)
        
        pages = notion.search_pages()
        print(f"   利用可能ページ: {len(pages)}件")
        
        documents = []
        for i, page in enumerate(pages[:limit]):
            try:
                content = notion.get_page_content(page['id'])
                if content and len(content.strip()) > 20:
                    documents.append({
                        'content': content[:800],  # 内容制限でメモリ節約
                        'metadata': {
                            'title': page.get('title', f'Notionページ{i+1}'),
                            'source': 'notion'
                        }
                    })
                    print(f"   ✅ 成功: {len(documents)}件")
            except:
                continue
        
        return documents
        
    except Exception as e:
        print(f"❌ Notion収集エラー: {e}")
        return []

def collect_gdrive_safe(limit=3):
    """Google Driveデータを安全に収集（mime_type対応）"""
    try:
        print("📁 Google Driveデータ収集中...")
        
        load_dotenv()
        credentials_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS')
        gdrive = GoogleDriveProcessor(credentials_path)
        
        files = gdrive.list_files()
        print(f"   利用可能ファイル: {len(files)}件")
        
        documents = []
        for i, file_info in enumerate(files[:limit]):
            try:
                file_id = file_info['id']
                mime_type = file_info.get('mimeType', 'application/octet-stream')
                
                # mime_typeを含めてコンテンツ取得
                content = gdrive.download_and_extract_text(file_id, mime_type)
                
                if content and len(content.strip()) > 20:
                    documents.append({
                        'content': content[:800],  # 内容制限でメモリ節約
                        'metadata': {
                            'title': file_info.get('name', f'Driveファイル{i+1}'),
                            'source': 'google_drive'
                        }
                    })
                    print(f"   ✅ 成功: {len(documents)}件")
            except Exception as e:
                print(f"   ⚠️ ファイル{i+1}エラー: {e}")
                continue
        
        return documents
        
    except Exception as e:
        print(f"❌ Google Drive収集エラー: {e}")
        return []

def safe_integration(documents):
    """安全な統合処理"""
    if not documents:
        return False
        
    try:
        print(f"💾 {len(documents)}件を統合中...")
        processor = VectorDBProcessor()
        
        initial_count = processor.collection.count()
        print(f"   統合前: {initial_count}件")
        
        # 1件ずつ慎重に処理
        success_count = 0
        for i, doc in enumerate(documents):
            try:
                processor.add_documents([doc])
                success_count += 1
                print(f"   📦 {i+1}/{len(documents)}: 成功")
            except Exception as e:
                print(f"   ❌ {i+1}/{len(documents)}: エラー ({str(e)[:30]}...)")
                continue
        
        final_count = processor.collection.count()
        print(f"✅ 統合完了: {success_count}件成功、最終DB件数: {final_count}件")
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ 統合エラー: {e}")
        return False

def main():
    print("🚀 最小限データ収集・統合システム")
    print("=" * 40)
    
    all_docs = []
    
    # 少量ずつ収集
    notion_docs = collect_notion_safe(limit=2)
    all_docs.extend(notion_docs)
    
    gdrive_docs = collect_gdrive_safe(limit=2)
    all_docs.extend(gdrive_docs)
    
    print(f"\n📊 収集完了: {len(all_docs)}件")
    
    if all_docs:
        success = safe_integration(all_docs)
        if success:
            print("\n🎉 システム準備完了！")
            print("🔍 AI検索テスト:")
            print("   python src/ai_assistant_fixed.py")
        else:
            print("\n⚠️ 一部問題がありましたが、基本機能は動作するはずです")
    else:
        print("\n❌ データ収集に失敗しました")

if __name__ == "__main__":
    main()
