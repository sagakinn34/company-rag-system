import sys
import time
import gc
import os
from vector_db_processor import VectorDBProcessor

def real_data_integration():
    """実データを使用した統合処理"""
    print("🚀 実データ統合を開始します...")
    print("💡 Notion + Google Drive の実データを処理します")
    
    # 環境変数から認証情報を取得
    notion_token = os.environ.get('NOTION_TOKEN')
    gdrive_credentials = os.environ.get('GOOGLE_DRIVE_CREDENTIALS')
    openai_key = os.environ.get('OPENAI_API_KEY')
    
    print(f"🔐 認証情報確認:")
    print(f"   Notion Token: {'✅ 設定済み' if notion_token else '❌ 未設定'}")
    print(f"   Google Drive: {'✅ 設定済み' if gdrive_credentials else '❌ 未設定'}")
    print(f"   OpenAI API: {'✅ 設定済み' if openai_key else '❌ 未設定'}")
    
    # ベクトルDBプロセッサーの初期化
    print("\n📦 ベクトルデータベース初期化中...")
    vector_db = VectorDBProcessor()
    
    total_processed = 0
    
    # Notionデータの処理
    if notion_token:
        try:
            print("\n📝 Notionデータの処理を開始...")
            
            # 正しい初期化方法でNotionプロセッサーを作成
            sys.path.append('src')
            import notion_processor
            
            # クラス名を動的に特定
            for name in dir(notion_processor):
                obj = getattr(notion_processor, name)
                if hasattr(obj, '__init__') and 'Processor' in name:
                    try:
                        # 環境変数を使って初期化を試行
                        notion = obj(notion_token)
                        print(f"✅ {name}を正常に初期化")
                        break
                    except TypeError:
                        try:
                            # 引数なしで初期化を試行
                            notion = obj()
                            print(f"✅ {name}を正常に初期化（引数なし）")
                            break
                        except:
                            continue
                    except Exception as e:
                        print(f"⚠️ {name}初期化失敗: {e}")
                        continue
            else:
                raise Exception("有効なNotionプロセッサーが見つかりません")
            
            # データ取得メソッドを動的に特定
            data_methods = ['fetch_all_pages', 'get_all_pages', 'fetch_pages', 'get_pages']
            notion_data = []
            
            for method_name in data_methods:
                if hasattr(notion, method_name):
                    try:
                        method = getattr(notion, method_name)
                        notion_data = method()
                        print(f"✅ {method_name}でデータ取得成功: {len(notion_data)}件")
                        break
                    except Exception as e:
                        print(f"⚠️ {method_name}失敗: {e}")
                        continue
            
            if not notion_data:
                print("⚠️ Notionデータの取得に失敗しました")
            else:
                # Notionデータを処理
                print(f"📊 Notion総件数: {len(notion_data)}件")
                
                batch_size = 10
                notion_processed = 0
                
                for i in range(0, min(100, len(notion_data)), batch_size):  # 最初の100件まで
                    batch = notion_data[i:i+batch_size]
                    print(f"🔄 Notion処理中: {i+1}-{min(i+batch_size, len(notion_data))}件目")
                    
                    for item in batch:
                        try:
                            # データを統一形式に変換
                            if isinstance(item, dict):
                                document_data = {
                                    'content': item.get('content', str(item)),
                                    'title': item.get('title', f'Notion文書 {notion_processed + 1}'),
                                    'source': 'notion',
                                    'type': 'document'
                                }
                            else:
                                document_data = {
                                    'content': str(item),
                                    'title': f'Notion文書 {notion_processed + 1}',
                                    'source': 'notion',
                                    'type': 'document'
                                }
                            
                            if vector_db.add_document(document_data):
                                notion_processed += 1
                                total_processed += 1
                            time.sleep(0.3)
                            
                        except Exception as e:
                            print(f"⚠️ Notionアイテムスキップ: {e}")
                            continue
                    
                    gc.collect()
                    print(f"   ✅ バッチ完了、累計処理: {notion_processed}件")
                
                print(f"✅ Notion処理完了: {notion_processed}件を統合")
            
        except Exception as e:
            print(f"❌ Notion処理で重大エラー: {e}")
            print("   詳細なエラー情報:")
            import traceback
            traceback.print_exc()
    else:
        print("⚠️ NOTION_TOKEN環境変数が設定されていません")
    
    # Google Driveデータの処理
    if gdrive_credentials and os.path.exists(gdrive_credentials):
        try:
            print("\n📁 Google Driveデータの処理を開始...")
            
            import gdrive_processor
            
            # クラス名を動的に特定
            for name in dir(gdrive_processor):
                obj = getattr(gdrive_processor, name)
                if hasattr(obj, '__init__') and 'Processor' in name:
                    try:
                        # 認証ファイルパスを使って初期化を試行
                        gdrive = obj(gdrive_credentials)
                        print(f"✅ {name}を正常に初期化")
                        break
                    except TypeError:
                        try:
                            # 引数なしで初期化を試行
                            gdrive = obj()
                            print(f"✅ {name}を正常に初期化（引数なし）")
                            break
                        except:
                            continue
                    except Exception as e:
                        print(f"⚠️ {name}初期化失敗: {e}")
                        continue
            else:
                raise Exception("有効なGoogle Driveプロセッサーが見つかりません")
            
            # データ取得メソッドを動的に特定
            data_methods = ['fetch_all_files', 'get_all_files', 'fetch_files', 'get_files']
            gdrive_data = []
            
            for method_name in data_methods:
                if hasattr(gdrive, method_name):
                    try:
                        method = getattr(gdrive, method_name)
                        gdrive_data = method()
                        print(f"✅ {method_name}でデータ取得成功: {len(gdrive_data)}件")
                        break
                    except Exception as e:
                        print(f"⚠️ {method_name}失敗: {e}")
                        continue
            
            if not gdrive_data:
                print("⚠️ Google Driveデータの取得に失敗しました")
            else:
                # Google Driveデータを処理
                print(f"📊 Google Drive総件数: {len(gdrive_data)}件")
                
                batch_size = 10
                gdrive_processed = 0
                
                for i in range(0, min(100, len(gdrive_data)), batch_size):  # 最初の100件まで
                    batch = gdrive_data[i:i+batch_size]
                    print(f"🔄 Drive処理中: {i+1}-{min(i+batch_size, len(gdrive_data))}件目")
                    
                    for item in batch:
                        try:
                            # データを統一形式に変換
                            if isinstance(item, dict):
                                document_data = {
                                    'content': item.get('content', str(item)),
                                    'title': item.get('title', f'Drive文書 {gdrive_processed + 1}'),
                                    'source': 'google_drive',
                                    'type': 'document'
                                }
                            else:
                                document_data = {
                                    'content': str(item),
                                    'title': f'Drive文書 {gdrive_processed + 1}',
                                    'source': 'google_drive',
                                    'type': 'document'
                                }
                            
                            if vector_db.add_document(document_data):
                                gdrive_processed += 1
                                total_processed += 1
                            time.sleep(0.3)
                            
                        except Exception as e:
                            print(f"⚠️ Driveアイテムスキップ: {e}")
                            continue
                    
                    gc.collect()
                    print(f"   ✅ バッチ完了、累計処理: {gdrive_processed}件")
                
                print(f"✅ Google Drive処理完了: {gdrive_processed}件を統合")
            
        except Exception as e:
            print(f"❌ Google Drive処理で重大エラー: {e}")
            print("   詳細なエラー情報:")
            import traceback
            traceback.print_exc()
    else:
        if not gdrive_credentials:
            print("⚠️ GOOGLE_DRIVE_CREDENTIALS環境変数が設定されていません")
        else:
            print(f"⚠️ Google Drive認証ファイルが見つかりません: {gdrive_credentials}")
    
    # 最終統計
    final_stats = vector_db.get_stats()
    print(f"\n🎉 実データ統合作業完了！")
    print(f"📊 最終データベース件数: {final_stats['total_documents']}件")
    print(f"🔄 今回処理した実データ件数: {total_processed}件")
    print(f"🏆 ステータス: {final_stats['status']}")
    
    if total_processed > 0:
        print("✅ 実データの統合に成功しました！")
        print("🌐 Web UIでテストしてください: streamlit run app.py")
    else:
        print("⚠️ 実データの統合に失敗しました。認証情報とプロセッサーを確認してください。")
    
    return final_stats

if __name__ == "__main__":
    result = real_data_integration()
    
    # 実データでの検索テスト
    if result['total_documents'] > 10:  # テストデータ以外がある場合
        print("\n🧪 実データでの検索テストを実行中...")
        try:
            from vector_db_processor import VectorDBProcessor
            db = VectorDBProcessor()
            test_queries = ["プロジェクト", "管理", "業務", "ガイド", "会議"]
            
            for query in test_queries:
                results = db.search(query, n_results=1)
                if results:
                    print(f"✅ '{query}' の検索成功: {len(results)}件")
                    break
            else:
                print("⚠️ 実データでの検索テストで結果が見つかりませんでした")
                
        except Exception as e:
            print(f"⚠️ 検索テストエラー: {e}")
