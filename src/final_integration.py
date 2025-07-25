import sys
import os
import streamlit as st

# 絶対パスでsrcディレクトリを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', 'src') if 'src' not in current_dir else current_dir
sys.path.insert(0, src_path)

def run_data_integration():
    """小規模企業向け拡張データ統合（Notion: 300件, Google Drive: 200件上限）"""
    
    # 統合開始表示
    st.info("🚀 拡張データ統合を開始...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        documents = []
        
        # 1. Notionプロセッサー（拡張版）
        status_text.text("📝 Notionからデータ取得中（拡張版: 300件上限）...")
        progress_bar.progress(20)
        
        try:
            notion_token = st.secrets.get("NOTION_TOKEN")
            if notion_token:
                st.info("📝 NOTION_TOKEN: ✅ 設定済み")
                
                from notion_processor import NotionProcessor
                st.success("📝 NotionProcessor インポート成功")
                
                notion = NotionProcessor()
                st.success("📝 NotionProcessor インスタンス作成成功")
                
                # 拡張版取得メソッド実行
                notion_docs = notion.get_all_pages()
                st.info(f"📝 Notion取得結果（拡張版）: {len(notion_docs) if notion_docs else 0}件")
                
                if notion_docs:
                    documents.extend(notion_docs)
                    st.success(f"✅ Notion拡張取得成功: {len(notion_docs)}件")
                    
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
            st.exception(e)
        
        # 2. Google Driveプロセッサー（拡張版）
        status_text.text("📂 Google Driveからデータ取得中（拡張版: 200件上限）...")
        progress_bar.progress(50)
        
        try:
            # Google Drive認証の詳細確認
            gdrive_creds = st.secrets.get("GOOGLE_DRIVE_CREDENTIALS")
            
            st.info("🔍 === Google Drive拡張診断開始 ===")
            
            if gdrive_creds:
                st.success("📂 GOOGLE_DRIVE_CREDENTIALS: ✅ 設定済み")
                st.info(f"🔍 認証情報タイプ: {type(gdrive_creds)}")
                
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
                
                # Google Drive Processor（拡張版）のインポート・初期化
                try:
                    from gdrive_processor import GoogleDriveProcessor
                    st.success("📂 GoogleDriveProcessor（拡張版）インポート成功")
                    
                    # インスタンス作成
                    gdrive = GoogleDriveProcessor()
                    st.success("📂 GoogleDriveProcessor（拡張版）インスタンス作成成功")
                    
                    # サービス初期化確認
                    if gdrive.service:
                        st.success("✅ Google Drive APIサービス初期化成功")
                        
                        # 接続テスト
                        try:
                            test_result = gdrive.service.files().list(pageSize=1).execute()
                            test_files = test_result.get('files', [])
                            st.success(f"✅ 接続テスト成功: {len(test_files)}件のファイルにアクセス可能")
                            
                            # 拡張版ファイル取得実行
                            st.info("📂 拡張版ファイル取得中（200件上限・バランス重視）...")
                            gdrive_docs = gdrive.get_all_files()
                            st.info(f"📂 Google Drive拡張取得結果: {len(gdrive_docs) if gdrive_docs else 0}件")
                            
                            if gdrive_docs:
                                documents.extend(gdrive_docs)
                                st.success(f"✅ Google Drive拡張取得成功: {len(gdrive_docs)}件")
                                
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
                
            st.info("🔍 === Google Drive拡張診断終了 ===")
                    
        except Exception as e:
            st.error(f"❌ Google Drive取得エラー: {e}")
            st.exception(e)
        
        # 3. Discordプロセッサー（将来実装予定）
        status_text.text("💬 Discord処理をスキップ中...")
        progress_bar.progress(70)
        st.info("💬 Discord統合: 一旦スキップ（今後実装予定）")
        
        # 4. ベクトルDBに統合（拡張版）
        status_text.text("🔄 ベクトルDBに統合中（拡張版）...")
        progress_bar.progress(90)
        
        st.info(f"🔄 拡張統合処理: 合計{len(documents)}件のデータを処理中...")
        
        if documents:
            st.info(f"🔄 {len(documents)}件を拡張ベクトルDBに統合中...")
            
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            
            if vector_db.collection:
                # 統合前のカウント
                before_count = vector_db.collection.count()
                st.info(f"📊 統合前のDB件数: {before_count}件")
                
                # ドキュメント統合
                vector_db.add_documents(documents)
                
                # 統合後のカウント
                after_count = vector_db.collection.count()
                added_count = after_count - before_count
                
                progress_bar.progress(100)
                status_text.text("✅ 拡張統合完了!")
                
                st.success(f"🎉 拡張データ統合完了!")
                st.success(f"📊 新規追加: {added_count}件")
                st.success(f"📊 総DB件数: {after_count}件")
                
                # 拡張統合結果詳細
                with st.expander("📊 拡張統合結果詳細"):
                    # ソース別集計
                    sources = {}
                    types = {}
                    categories = {}
                    priorities = {}
                    
                    for doc in documents:
                        source = doc.get('source', '不明')
                        doc_type = doc.get('type', '不明')
                        category = doc.get('category', doc.get('type', '不明'))
                        priority = doc.get('priority', '不明')
                        
                        sources[source] = sources.get(source, 0) + 1
                        types[doc_type] = types.get(doc_type, 0) + 1
                        categories[category] = categories.get(category, 0) + 1
                        if priority != '不明':
                            priorities[priority] = priorities.get(priority, 0) + 1
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**📊 ソース別:**")
                        for source, count in sources.items():
                            st.write(f"- {source}: {count}件")
                        
                        st.write("**📄 タイプ別:**")
                        for doc_type, count in types.items():
                            st.write(f"- {doc_type}: {count}件")
                    
                    with col2:
                        st.write("**📁 カテゴリ別:**")
                        for category, count in categories.items():
                            st.write(f"- {category}: {count}件")
                        
                        if priorities:
                            st.write("**⭐ 重要度別:**")
                            for priority, count in priorities.items():
                                st.write(f"- {priority}: {count}件")
                
                # パフォーマンス情報
                with st.expander("⚡ パフォーマンス情報"):
                    st.write(f"**処理能力:** 小規模企業向け拡張版")
                    st.write(f"**Notion上限:** 300件")
                    st.write(f"**Google Drive上限:** 200件")
                    st.write(f"**合計上限:** 500件")
                    st.write(f"**実際の取得:** {len(documents)}件")
                    st.write(f"**取得率:** {len(documents)/500*100:.1f}%")
                    
                    # 時系列バランス分析
                    notion_docs = [d for d in documents if d.get('source') == 'notion']
                    gdrive_docs = [d for d in documents if d.get('source') == 'google_drive']
                    
                    st.write(f"**データバランス:**")
                    st.write(f"- Notion: {len(notion_docs)}件 ({len(notion_docs)/len(documents)*100:.1f}%)")
                    st.write(f"- Google Drive: {len(gdrive_docs)}件 ({len(gdrive_docs)/len(documents)*100:.1f}%)")
                
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
        progress_bar.progress(100)
        status_text.text("❌ 統合エラー発生")
        
        st.error(f"❌ 拡張統合エラー: {e}")
        st.exception(e)
        
        # エラー詳細情報
        with st.expander("🔍 エラー詳細"):
            st.write(f"**エラータイプ:** {type(e).__name__}")
            st.write(f"**エラーメッセージ:** {str(e)}")
            st.write(f"**発生箇所:** final_integration.py")
            
            import traceback
            st.code(traceback.format_exc())
        
        return False

def safe_integration():
    """下位互換性のための関数"""
    return run_data_integration()

# メイン実行部
if __name__ == "__main__":
    print("🧪 final_integration.py 拡張版 - 直接実行テスト")
    
    # Streamlit環境外でのテスト用
    try:
        # 簡易テスト実行
        print("📝 テスト実行中...")
        result = safe_integration()
        
        if result:
            print("✅ テスト成功")
        else:
            print("❌ テスト失敗")
            
    except Exception as e:
        print(f"❌ テストエラー: {e}")
