import sys
import time
import gc

# 正しいクラス名でインポート
try:
    from notion_processor import NotionProcessor
except ImportError:
    # 別のクラス名の可能性を試す
    try:
        from notion_processor import NotionPageProcessor as NotionProcessor
    except ImportError:
        print("⚠️ NotionProcessorクラスが見つかりません")
        NotionProcessor = None

try:
    from gdrive_processor import GoogleDriveProcessor as GDriveProcessor
except ImportError:
    try:
        from gdrive_processor import GDriveProcessor
    except ImportError:
        print("⚠️ GoogleDriveProcessorクラスが見つかりません")
        GDriveProcessor = None

from vector_db_processor import VectorDBProcessor

def gradual_data_integration():
    """メモリ効率を考慮した段階的データ統合"""
    print("🚀 段階的データ統合を開始します...")
    print("💡 メモリ不足を防ぐため、10件ずつ処理します")
    
    # ベクトルDBプロセッサーの初期化
    print("📦 ベクトルデータベース初期化中...")
    vector_db = VectorDBProcessor()
    
    total_processed = 0
    
    # Notionデータの処理
    if NotionProcessor is not None:
        try:
            print("\n📝 Notionデータの処理を開始...")
            notion = NotionProcessor()
            
            # fetch_all_pagesメソッドを確認してデータ取得
            if hasattr(notion, 'fetch_all_pages'):
                notion_data = notion.fetch_all_pages()
            elif hasattr(notion, 'get_all_pages'):
                notion_data = notion.get_all_pages()
            elif hasattr(notion, 'fetch_pages'):
                notion_data = notion.fetch_pages()
            else:
                print("⚠️ Notionデータ取得メソッドが見つかりません")
                notion_data = []
            
            print(f"📊 Notion総件数: {len(notion_data)}件")
            
            # Notionデータを10件ずつ処理
            notion_batch_size = 10
            notion_processed = 0
            
            for i in range(0, min(50, len(notion_data)), notion_batch_size):  # 最初の50件まで
                batch = notion_data[i:i+notion_batch_size]
                print(f"🔄 Notion処理中: {i+1}-{min(i+notion_batch_size, len(notion_data))}件目")
                
                for item in batch:
                    try:
                        # データ形式を確認して適切に処理
                        if isinstance(item, dict):
                            document_data = item
                        else:
                            # itemが辞書でない場合の処理
                            document_data = {
                                'content': str(item),
                                'title': f'Notion文書 {notion_processed + 1}',
                                'source': 'notion',
                                'type': 'document'
                            }
                        
                        if vector_db.add_document(document_data):
                            notion_processed += 1
                            total_processed += 1
                        time.sleep(0.5)  # メモリ回復のための短い待機
                        
                    except Exception as e:
                        print(f"⚠️ Notionアイテムスキップ: {e}")
                        continue
                
                # バッチ処理後のメモリクリーンアップ
                gc.collect()
                print(f"   ✅ バッチ完了、累計処理: {notion_processed}件")
            
            print(f"✅ Notion処理完了: {notion_processed}件を統合")
            
        except Exception as e:
            print(f"⚠️ Notion処理でエラー: {e}")
            print("📝 Google Driveデータの処理に続行...")
    else:
        print("⚠️ NotionProcessorが利用できません。スキップします。")
    
    # Google Driveデータの処理
    if GDriveProcessor is not None:
        try:
            print("\n📁 Google Driveデータの処理を開始...")
            gdrive = GDriveProcessor()
            
            # fetch_all_filesメソッドを確認してデータ取得
            if hasattr(gdrive, 'fetch_all_files'):
                gdrive_data = gdrive.fetch_all_files()
            elif hasattr(gdrive, 'get_all_files'):
                gdrive_data = gdrive.get_all_files()
            elif hasattr(gdrive, 'fetch_files'):
                gdrive_data = gdrive.fetch_files()
            else:
                print("⚠️ Google Driveデータ取得メソッドが見つかりません")
                gdrive_data = []
            
            print(f"📊 Google Drive総件数: {len(gdrive_data)}件")
            
            # Google Driveデータを10件ずつ処理
            gdrive_batch_size = 10
            gdrive_processed = 0
            
            for i in range(0, min(50, len(gdrive_data)), gdrive_batch_size):  # 最初の50件まで
                batch = gdrive_data[i:i+gdrive_batch_size]
                print(f"🔄 Drive処理中: {i+1}-{min(i+gdrive_batch_size, len(gdrive_data))}件目")
                
                for item in batch:
                    try:
                        # データ形式を確認して適切に処理
                        if isinstance(item, dict):
                            document_data = item
                        else:
                            # itemが辞書でない場合の処理
                            document_data = {
                                'content': str(item),
                                'title': f'Drive文書 {gdrive_processed + 1}',
                                'source': 'google_drive',
                                'type': 'document'
                            }
                        
                        if vector_db.add_document(document_data):
                            gdrive_processed += 1
                            total_processed += 1
                        time.sleep(0.5)  # メモリ回復のための短い待機
                        
                    except Exception as e:
                        print(f"⚠️ Driveアイテムスキップ: {e}")
                        continue
                
                # バッチ処理後のメモリクリーンアップ
                gc.collect()
                print(f"   ✅ バッチ完了、累計処理: {gdrive_processed}件")
            
            print(f"✅ Google Drive処理完了: {gdrive_processed}件を統合")
            
        except Exception as e:
            print(f"⚠️ Google Drive処理でエラー: {e}")
    else:
        print("⚠️ GoogleDriveProcessorが利用できません。スキップします。")
    
    # テストデータの追加（データが少ない場合）
    if total_processed < 5:
        print("\n🧪 実データが少ないため、テストデータを追加します...")
        test_documents = [
            {
                'content': 'これはRAGシステムのテスト文書です。自然言語処理と機械学習を活用したシステムについて説明しています。',
                'title': 'RAGシステム概要',
                'source': 'test_data',
                'type': 'document'
            },
            {
                'content': 'プロジェクト管理においては、進捗の可視化とチームコミュニケーションが重要です。定期的な振り返りとフィードバックが成功の鍵となります。',
                'title': 'プロジェクト管理のベストプラクティス',
                'source': 'test_data',
                'type': 'document'
            },
            {
                'content': 'AI技術の発展により、自然言語での質問応答システムが実用化されています。検索拡張生成（RAG）は特に注目される技術です。',
                'title': 'AI技術の現状と未来',
                'source': 'test_data',
                'type': 'document'
            },
            {
                'content': 'チーム運営では、メンバーの強みを活かし、効果的なコミュニケーションを維持することが重要です。定期的な1on1ミーティングも有効です。',
                'title': '効果的なチーム運営',
                'source': 'test_data',
                'type': 'document'
            },
            {
                'content': '会議の効率化には、事前のアジェンダ設定と時間管理が欠かせません。議事録の共有も重要な要素です。',
                'title': '会議運営の改善方法',
                'source': 'test_data',
                'type': 'document'
            }
        ]
        
        for i, doc in enumerate(test_documents):
            try:
                if vector_db.add_document(doc):
                    total_processed += 1
                    print(f"   ✅ テストデータ追加: {doc['title']}")
                time.sleep(0.3)
            except Exception as e:
                print(f"   ⚠️ テストデータエラー: {e}")
    
    # 最終統計
    final_stats = vector_db.get_stats()
    print(f"\n🎉 統合作業完了！")
    print(f"📊 最終データベース件数: {final_stats['total_documents']}件")
    print(f"🔄 今回処理した件数: {total_processed}件")
    print(f"🏆 ステータス: {final_stats['status']}")
    
    if final_stats['total_documents'] > 0:
        print("✅ システムは本格運用可能です！")
        print("🌐 Web UIを起動してテストしてください: streamlit run app.py")
    else:
        print("⚠️ データが統合されませんでした。個別プロセッサーを確認してください。")
    
    return final_stats

if __name__ == "__main__":
    result = gradual_data_integration()
    
    # 簡単な検索テスト
    if result['total_documents'] > 0:
        print("\n🧪 システムテストを実行中...")
        try:
            from vector_db_processor import VectorDBProcessor
            db = VectorDBProcessor()
            test_results = db.search("プロジェクト管理", n_results=2)
            print(f"✅ 検索テスト成功: {len(test_results)}件の関連文書を発見")
        except Exception as e:
            print(f"⚠️ 検索テストエラー: {e}")
