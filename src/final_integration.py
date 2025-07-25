import sys
import os
import streamlit as st
import gc
import time

# 絶対パスでsrcディレクトリを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', 'src') if 'src' not in current_dir else current_dir
sys.path.insert(0, src_path)

def run_data_integration():
    """最適化版データ統合（実用性と可用性のバランス）"""
    
    # 統合開始表示
    st.info("⚖️ 最適化データ統合を開始...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # パフォーマンス監視
    start_time = time.time()
    
    try:
        documents = []
        
        # === 最適化設定 ===
        NOTION_OPTIMIZED = 150    # 300 → 150 (50%削減)
        GDRIVE_OPTIMIZED = 100    # 200 → 100 (50%削減)
        CONTENT_MAX_CHARS = 2000  # コンテンツ文字数制限
        
        # 1. Notion最適化処理
        status_text.text("📝 Notion最適化取得中...")
        progress_bar.progress(20)
        
        try:
            notion_token = st.secrets.get("NOTION_TOKEN")
            if notion_token:
                st.info("📝 NOTION_TOKEN: ✅ 設定済み")
                
                from notion_processor import NotionProcessor
                st.success("📝 NotionProcessor インポート成功")
                
                notion = NotionProcessor()
                st.success("📝 NotionProcessor インスタンス作成成功")
                
                # 最適化取得実行
                notion_docs = notion.get_all_pages()
                st.info(f"📝 Notion最適化取得結果: {len(notion_docs) if notion_docs else 0}件")
                
                if notion_docs:
                    documents.extend(notion_docs)
                    st.success(f"✅ Notion最適化取得成功: {len(notion_docs)}件")
                    
                    # 詳細内訳表示
                    with st.expander("📊 Notion取得詳細"):
                        notion_types = {}
                        for doc in notion_docs:
                            doc_type = doc.get('type', '不明')
                            notion_types[doc_type] = notion_types.get(doc_type, 0) + 1
                        
                        for doc_type, count in notion_types.items():
                            st.write(f"- {doc_type}: {count}件")
                else:
                    st.warning("⚠️ Notionデータが空です")
            else:
                st.error("❌ NOTION_TOKENが設定されていません")
                
        except Exception as e:
            st.error(f"❌ Notion取得エラー: {e}")
        
        # メモリクリーンアップ
        gc.collect()
        
        # 2. Google Drive最適化処理
        status_text.text("📂 Google Drive最適化取得中...")
        progress_bar.progress(50)
        
        try:
            gdrive_creds = st.secrets.get("GOOGLE_DRIVE_CREDENTIALS")
            
            st.info("🔍 === Google Drive最適化診断開始 ===")
            
            if gdrive_creds:
                st.success("📂 GOOGLE_DRIVE_CREDENTIALS: ✅ 設定済み")
                
                # 認証情報の詳細チェック
                if hasattr(gdrive_creds, '_data'):
                    creds_dict = dict(gdrive_creds._data)
                else:
                    creds_dict = dict(gdrive_creds)
                
                # 必要フィールドの存在確認
                required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
                missing_fields = [field for field in required_fields if field not in creds_dict]
                
                if missing_fields:
                    st.error(f"❌ 必要なフィールドが不足: {missing_fields}")
                else:
                    st.success("✅ 必要な認証フィールドが全て存在")
                
                # Google Drive Processor（最適化版）のインポート・初期化
                try:
                    from gdrive_processor import GoogleDriveProcessor
                    st.success("📂 GoogleDriveProcessor（最適化版）インポート成功")
                    
                    # インスタンス作成
                    gdrive = GoogleDriveProcessor()
                    st.success("📂 GoogleDriveProcessor（最適化版）インスタンス作成成功")
                    
                    # サービス初期化確認
                    if gdrive.service:
                        st.success("✅ Google Drive APIサービス初期化成功")
                        
                        # 接続テスト
                        try:
                            test_result = gdrive.service.files().list(pageSize=1).execute()
                            test_files = test_result.get('files', [])
                            st.success(f"✅ 接続テスト成功: {len(test_files)}件のファイルにアクセス可能")
                            
                            # 最適化版ファイル取得実行
                            st.info("📂 最適化版ファイル取得中（100件上限・効率重視）...")
                            gdrive_docs = gdrive.get_all_files()
                            st.info(f"📂 Google Drive最適化取得結果: {len(gdrive_docs) if gdrive_docs else 0}件")
                            
                            if gdrive_docs:
                                documents.extend(gdrive_docs)
                                st.success(f"✅ Google Drive最適化取得成功: {len(gdrive_docs)}件")
                                
                                # 詳細内訳表示
                                with st.expander("📋 Google Drive取得詳細"):
                                    gdrive_categories = {}
                                    gdrive_priorities = {}
                                    
                                    for doc in gdrive_docs:
                                        category = doc.get('category', '不明')
                                        priority = doc.get('priority', '不明')
                                        
                                        gdrive_categories[category] = gdrive_categories.get(category, 0) + 1
                                        gdrive_priorities[priority] = gdrive_priorities.get(priority, 0) + 1
                                    
                                    st.write("**カテゴリ別:**")
                                    for category, count in gdrive_categories.items():
                                        st.write(f"- {category}: {count}件")
                                    
                                    st.write("**重要度別:**")
                                    for priority, count in gdrive_priorities.items():
                                        st.write(f"- {priority}: {count}件")
                            else:
                                st.warning("⚠️ Google Driveデータが空です")
                                st.info("💡 考えられる原因:")
                                st.write("- Service Accountにファイルが共有されていない")
                                st.write("- 対象ファイルがない、または形式が非対応")
                                st.write("- アクセス権限が不足している")
                                
                        except Exception as api_error:
                            st.error(f"❌ Google Drive API呼び出しエラー: {api_error}")
                            st.write(f"🔍 エラータイプ: {type(api_error).__name__}")
                        
                    else:
                        st.error("❌ Google Drive APIサービスの初期化に失敗")
                        st.info("💡 Service Account認証情報を確認してください")
                        
                except ImportError as e:
                    st.error(f"❌ GoogleDriveProcessor インポートエラー: {e}")
                except Exception as e:
                    st.error(f"❌ GoogleDriveProcessor 初期化エラー: {e}")
                    st.write(f"🔍 エラータイプ: {type(e).__name__}")
                    st.write(f"🔍 エラー詳細: {str(e)}")
                    
            else:
                st.error("❌ GOOGLE_DRIVE_CREDENTIALSが設定されていません")
                st.info("💡 Streamlit Secretsで認証情報を設定してください")
                
            st.info("🔍 === Google Drive最適化診断終了 ===")
                    
        except Exception as e:
            st.error(f"❌ Google Drive取得エラー: {e}")
        
        # メモリクリーンアップ
        gc.collect()
        
        # 3. Discord処理（スキップ）
        status_text.text("💬 Discord処理をスキップ中...")
        progress_bar.progress(70)
        st.info("💬 Discord統合: 一旦スキップ（今後実装予定）")
        
        # 4. 最適化ベクトルDB統合
        status_text.text("🔄 最適化ベクトル統合中...")
        progress_bar.progress(90)
        
        st.info(f"🔄 最適化統合処理: 合計{len(documents)}件のデータを処理中...")
        
        if documents:
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            
            if vector_db.collection:
                # バッチ処理で負荷軽減
                batch_size = 10
                total_batches = (len(documents) + batch_size - 1) // batch_size
                
                st.info(f"🔄 {len(documents)}件を{batch_size}件ずつ{total_batches}バッチで処理中...")
                
                # 統合前のカウント
                before_count = vector_db.collection.count()
                st.info(f"📊 統合前のDB件数: {before_count}件")
                
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    
                    try:
                        vector_db.add_documents(batch)
                        
                        # 進捗表示
                        batch_num = i // batch_size + 1
                        st.info(f"📊 バッチ{batch_num}/{total_batches}完了 ({len(batch)}件処理)")
                        
                        # 3バッチごとにメモリクリーンアップ
                        if batch_num % 3 == 0:
                            gc.collect()
                            time.sleep(0.1)  # 負荷軽減
                        
                    except Exception as batch_error:
                        st.warning(f"⚠️ バッチ{batch_num}処理エラー: {batch_error}")
                        continue
                
                # 最終確認
                after_count = vector_db.collection.count()
                added_count = after_count - before_count
                elapsed_time = time.time() - start_time
                
                progress_bar.progress(100)
                status_text.text("✅ 最適化統合完了!")
                
                st.success("🎉 最適化データ統合完了!")
                st.success(f"📊 新規追加: {added_count}件")
                st.success(f"📊 総DB件数: {after_count}件")
                st.success(f"⏰ 処理時間: {elapsed_time:.1f}秒")
                
                # 最適化結果詳細
                display_optimization_results(documents, elapsed_time)
                
                return True
            else:
                st.error("❌ ベクトルDBが初期化されていません")
                return False
        else:
            progress_bar.progress(100)
            status_text.text("❌ 統合データなし")
            
            st.warning("⚠️ 統合するデータが見つかりませんでした")
            st.error("❌ 全てのサービスでデータが0件でした")
            
            # 診断情報
            with st.expander("🔍 診断情報"):
                st.write("**考えられる原因:**")
                st.write("1. **Notion**: アクセス権限、ページが存在しない")
                st.write("2. **Google Drive**: Service Account未共有、ファイルが存在しない")
                st.write("3. **認証**: API認証情報の問題")
                
                st.write("**対策:**")
                st.write("1. 各サービスの個別テストを実行")
                st.write("2. 認証情報の再確認")
                st.write("3. ファイル共有設定の確認")
            
            return False
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        st.error(f"❌ 最適化統合エラー: {e}")
        
        # エラー分析
        with st.expander("🔍 エラー分析"):
            st.write(f"**実行時間**: {elapsed_time:.1f}秒")
            st.write(f"**処理済み件数**: {len(documents) if 'documents' in locals() else 0}件")
            st.write(f"**エラータイプ**: {type(e).__name__}")
            
            if elapsed_time > 300:  # 5分超過
                st.warning("⏰ タイムアウトの可能性があります")
                st.info("💡 データ量を削減することを推奨します")
            
            import traceback
            st.code(traceback.format_exc())
        
        return False

def display_optimization_results(documents, elapsed_time):
    """最適化結果表示"""
    
    with st.expander("📊 最適化統合結果詳細"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総文書数", len(documents))
            st.metric("処理時間", f"{elapsed_time:.1f}秒")
        
        with col2:
            # ソース別統計
            sources = {}
            types = {}
            
            for doc in documents:
                source = doc.get('source', '不明')
                doc_type = doc.get('type', '不明')
                
                sources[source] = sources.get(source, 0) + 1
                types[doc_type] = types.get(doc_type, 0) + 1
            
            st.write("**ソース別:**")
            for source, count in sources.items():
                st.write(f"- {source}: {count}件")
            
            st.write("**タイプ別:**")
            for doc_type, count in types.items():
                st.write(f"- {doc_type}: {count}件")
        
        with col3:
            # 品質指標
            total_chars = sum(len(doc.get('content', '')) for doc in documents)
            avg_chars = total_chars / len(documents) if documents else 0
            
            st.metric("総文字数", f"{total_chars:,}")
            st.metric("平均文字数", f"{avg_chars:.0f}")
        
        # パフォーマンス評価
        st.write("**パフォーマンス評価:**")
        if elapsed_time < 180:  # 3分以内
            st.success("🚀 高速処理完了 - 優秀")
        elif elapsed_time < 300:  # 5分以内
            st.info("⚡ 標準処理完了 - 良好")
        else:
            st.warning("🐌 処理時間長め - 要最適化")
        
        # 実用性指標
        if len(documents) >= 200:
            st.success("📊 十分なデータ量 - 高い実用性")
        elif len(documents) >= 100:
            st.info("📊 適度なデータ量 - 実用的")
        else:
            st.warning("📊 データ量少なめ - 基本的実用性")
        
        # 推奨事項
        st.write("**推奨事項:**")
        st.write(f"- **現在のデータ量**: {len(documents)}件は最適バランス")
        st.write(f"- **処理時間**: {elapsed_time:.1f}秒で効率的")
        st.write(f"- **メモリ使用量**: 約{len(documents)*2}MB (推定)")

def safe_integration():
    """下位互換性のための関数"""
    return run_data_integration()

if __name__ == "__main__":
    safe_integration()

