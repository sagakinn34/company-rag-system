import sys
import time
import gc
import os
from vector_db_processor import VectorDBProcessor

def fixed_real_data_integration():
    """実際のメソッド名に基づく実データ統合"""
    print("🚀 修正版実データ統合を開始します...")
    
    # 環境変数から認証情報を取得
    notion_token = os.environ.get('NOTION_TOKEN')
    gdrive_credentials = os.environ.get('GOOGLE_DRIVE_CREDENTIALS')
    
    print(f"🔐 認証情報確認:")
    print(f"   Notion Token: {'✅ 設定済み' if notion_token else '❌ 未設定'}")
    print(f"   Google Drive: {'✅ 設定済み' if gdrive_credentials else '❌ 未設定'}")
    
    # ベクトルDBプロセッサーの初期化
    vector_db = VectorDBProcessor()
    total_processed = 0
    
    # Notionデータの処理
    if notion_token:
        try:
            print("\n📝 Notionデータの処理を開始...")
            sys.path.append('src')
            
            # NotionProcessorを直接インポートして使用
            from notion_processor import NotionProcessor
            notion = NotionProcessor(notion_token)
            
            # 利用可能なメソッドを動的に検索
            methods_to_try = []
            for attr_name in dir(notion):
                if not attr_name.startswith('_') and callable(getattr(notion, attr_name)):
                    if any(keyword in attr_name.lower() for keyword in ['fetch', 'get', 'retrieve', 'load', 'process']):
                        methods_to_try.append(attr_name)
            
            print(f"🔍 試行するメソッド: {methods_to_try}")
            
            notion_data = []
            for method_name in methods_to_try:
                try:
                    print(f"   🧪 {method_name} を試行中...")
                    method = getattr(notion, method_name)
                    
                    # 引数なしで実行を試行
                    result = method()
                    
                    if result and len(result) > 0:
                        notion_data = result
                        print(f"   ✅ {method_name} で {len(notion_data)}件のデータを取得")
                        break
                    else:
                        print(f"   ⚠️ {method_name} は空の結果を返しました")
                        
                except TypeError as e:
                    if "required positional argument" in str(e):
                        print(f"   ⚠️ {method_name} は引数が必要です")
                    else:
                        print(f"   ⚠️ {method_name} でTypeError: {e}")
                except Exception as e:
                    print(f"   ⚠️ {method_name} でエラー: {e}")
            
            # データが取得できた場合の処理
            if notion_data:
                print(f"📊 Notion総件数: {len(notion_data)}件")
                
                # データを10件ずつ処理
                for i in range(0, min(50, len(notion_data)), 10):
                    batch = notion_data[i:i+10]
                    print(f"🔄 Notion処理中: {i+1}-{min(i+10, len(notion_data))}件目")
                    
                    for j, item in enumerate(batch):
                        try:
                            # アイテムの型を確認してデータを抽出
                            print(f"     📄 アイテム {j+1} の型: {type(item)}")
                            
                            if isinstance(item, dict):
                                content = item.get('content', item.get('text', str(item)))
                                title = item.get('title', item.get('name', f'Notion文書 {i+j+1}'))
                            elif hasattr(item, 'content'):
                                content = getattr(item, 'content')
                                title = getattr(item, 'title', f'Notion文書 {i+j+1}')
                            elif hasattr(item, 'text'):
                                content = getattr(item, 'text')
                                title = getattr(item, 'title', f'Notion文書 {i+j+1}')
                            else:
                                content = str(item)
                                title = f'Notion文書 {i+j+1}'
                            
                            # 内容が十分にある場合のみ追加
                            if content and len(str(content).strip()) > 10:
                                document_data = {
                                    'content': str(content)[:2000],  # 長すぎる場合は切り詰め
                                    'title': str(title),
                                    'source': 'notion',
                                    'type': 'document'
                                }
                                
                                if vector_db.add_document(document_data):
                                    total_processed += 1
                                    print(f"     ✅ 追加成功: {title[:30]}...")
                            else:
                                print(f"     ⚠️ 内容が不十分でスキップ")
                            
                            time.sleep(0.2)
                            
                        except Exception as e:
                            print(f"     ❌ アイテム処理エラー: {e}")
                            continue
                    
                    gc.collect()
                
                print(f"✅ Notion処理完了: {total_processed}件を統合")
            else:
                print("⚠️ Notionデータが取得できませんでした")
                
        except Exception as e:
            print(f"❌ Notion処理で重大エラー: {e}")
            import traceback
            traceback.print_exc()
    
    # Google Driveデータの処理
    if gdrive_credentials and os.path.exists(gdrive_credentials):
        try:
            print("\n📁 Google Driveデータの処理を開始...")
            
            from gdrive_processor import GoogleDriveProcessor
            gdrive = GoogleDriveProcessor(gdrive_credentials)
            
            # 利用可能なメソッドを動的に検索
            methods_to_try = []
            for attr_name in dir(gdrive):
                if not attr_name.startswith('_') and callable(getattr(gdrive, attr_name)):
                    if any(keyword in attr_name.lower() for keyword in ['fetch', 'get', 'retrieve', 'load', 'process']):
                        methods_to_try.append(attr_name)
            
            print(f"🔍 試行するメソッド: {methods_to_try}")
            
            gdrive_data = []
            for method_name in methods_to_try:
                try:
                    print(f"   🧪 {method_name} を試行中...")
                    method = getattr(gdrive, method_name)
                    result = method()
                    
                    if result and len(result) > 0:
                        gdrive_data = result
                        print(f"   ✅ {method_name} で {len(gdrive_data)}件のデータを取得")
                        break
                    else:
                        print(f"   ⚠️ {method_name} は空の結果を返しました")
                        
                except TypeError as e:
                    print(f"   ⚠️ {method_name} でTypeError: {e}")
                except Exception as e:
                    print(f"   ⚠️ {method_name} でエラー: {e}")
            
            # Google Driveデータの処理
            if gdrive_data:
                gdrive_processed = 0
                print(f"📊 Google Drive総件数: {len(gdrive_data)}件")
                
                for i in range(0, min(50, len(gdrive_data)), 10):
                    batch = gdrive_data[i:i+10]
                    print(f"🔄 Drive処理中: {i+1}-{min(i+10, len(gdrive_data))}件目")
                    
                    for j, item in enumerate(batch):
                        try:
                            print(f"     📄 アイテム {j+1} の型: {type(item)}")
                            
                            if isinstance(item, dict):
                                content = item.get('content', item.get('text', str(item)))
                                title = item.get('title', item.get('name', f'Drive文書 {i+j+1}'))
                            elif hasattr(item, 'content'):
                                content = getattr(item, 'content')
                                title = getattr(item, 'title', f'Drive文書 {i+j+1}')
                            else:
                                content = str(item)
                                title = f'Drive文書 {i+j+1}'
                            
                            if content and len(str(content).strip()) > 10:
                                document_data = {
                                    'content': str(content)[:2000],
                                    'title': str(title),
                                    'source': 'google_drive',
                                    'type': 'document'
                                }
                                
                                if vector_db.add_document(document_data):
                                    gdrive_processed += 1
                                    total_processed += 1
                                    print(f"     ✅ 追加成功: {title[:30]}...")
                            else:
                                print(f"     ⚠️ 内容が不十分でスキップ")
                            
                            time.sleep(0.2)
                            
                        except Exception as e:
                            print(f"     ❌ アイテム処理エラー: {e}")
                            continue
                    
                    gc.collect()
                
                print(f"✅ Google Drive処理完了: {gdrive_processed}件を統合")
            else:
                print("⚠️ Google Driveデータが取得できませんでした")
                
        except Exception as e:
            print(f"❌ Google Drive処理で重大エラー: {e}")
            import traceback
            traceback.print_exc()
    
    # 最終結果
    final_stats = vector_db.get_stats()
    print(f"\n🎉 修正版統合作業完了！")
    print(f"📊 最終データベース件数: {final_stats['total_documents']}件")
    print(f"🔄 今回処理した実データ件数: {total_processed}件")
    
    if total_processed > 0:
        print("✅ 実データの統合に成功しました！")
        print("🌐 Web UIでテストしてください: streamlit run app.py")
        return True
    else:
        print("⚠️ 実データの統合に失敗しました")
        return False

if __name__ == "__main__":
    success = fixed_real_data_integration()
    
    if success:
        print("\n🧪 実データでの詳細検索テストを実行中...")
        try:
            from vector_db_processor import VectorDBProcessor
            db = VectorDBProcessor()
            
            # より具体的な検索テスト
            test_queries = ["ガイド", "管理", "業務", "プロジェクト", "システム"]
            for query in test_queries:
                results = db.search(query, n_results=3)
                if results:
                    print(f"✅ '{query}' の検索結果: {len(results)}件")
                    for i, result in enumerate(results):
                        print(f"   {i+1}. {result.get('metadata', {}).get('title', 'タイトル不明')[:50]}...")
                    break
        except Exception as e:
            print(f"⚠️ 検索テストエラー: {e}")
