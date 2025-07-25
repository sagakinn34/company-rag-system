import sys
import os
import streamlit as st

# 絶対パスでsrcディレクトリを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', 'src') if 'src' not in current_dir else current_dir
sys.path.insert(0, src_path)

def run_data_integration():
    """Streamlit UI表示付きデータ統合関数（Google Drive診断強化版）"""
    
    # 統合開始表示
    st.info("🚀 データ統合を開始...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        documents = []
        
        # 1. Notionプロセッサー
        status_text.text("📝 Notionからデータ取得中...")
        progress_bar.progress(20)
        
        try:
            notion_token = st.secrets.get("NOTION_TOKEN")
            if notion_token:
                st.info("📝 NOTION_TOKEN: ✅ 設定済み")
                
                from notion_processor import NotionProcessor
                st.success("📝 NotionProcessor インポート成功")
                
                notion = NotionProcessor()
                st.success("📝 NotionProcessor インスタンス作成成功")
                
                notion_docs = notion.get_all_pages()
                st.info(f"📝 Notion取得結果: {len(notion_docs) if notion_docs else 0}件")
                
                if notion_docs:
                    documents.extend(notion_docs)
                    st.success(f"✅ Notion: {len(notion_docs)}件取得成功")
                else:
                    st.warning("⚠️ Notionデータが空です")
            else:
                st.error("❌ NOTION_TOKENが設定されていません")
                
        except Exception as e:
            st.error(f"❌ Notion取得エラー: {e}")
        
        # 2. Google Driveプロセッサー（診断強化版）
        status_text.text("📂 Google Driveからデータ取得中...")
        progress_bar.progress(50)
        
        try:
            # Google Drive認証の詳細確認
            gdrive_creds = st.secrets.get("GOOGLE_DRIVE_CREDENTIALS")
            
            st.info("🔍 === Google Drive診断開始 ===")
            
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
                
                # Google Drive Processorのインポート・初期化
                try:
                    from gdrive_processor import GoogleDriveProcessor
                    st.success("📂 GoogleDriveProcessor インポート成功")
                    
                    # インスタンス作成
                    gdrive = GoogleDriveProcessor()
                    st.success("📂 GoogleDriveProcessor インスタンス作成成功")
                    
                    # サービス初期化確認
                    if gdrive.service:
                        st.success("✅ Google Drive APIサービス初期化成功")
                        
                        # 接続テスト
                        try:
                            test_result = gdrive.service.files().list(pageSize=1).execute()
                            test_files = test_result.get('files', [])
                            st.success(f"✅ 接続テスト成功: {len(test_files)}件のファイルにアクセス可能")
                            
                            # 実際のファイル取得
                            st.info("📂 ファイル一覧取得中...")
                            gdrive_docs = gdrive.get_all_files()
                            st.info(f"📂 Google Drive取得結果: {len(gdrive_docs) if gdrive_docs else 0}件")
                            
                            if gdrive_docs:
                                documents.extend(gdrive_docs)
                                st.success(f"✅ Google Drive: {len(gdrive_docs)}件取得成功")
                                
                                # 取得したファイルの詳細表示
                                with st.expander("📋 取得ファイル詳細"):
                                    for i, doc in enumerate(gdrive_docs[:5]):  # 最初の5件表示
                                        st.write(f"**ファイル{i+1}**: {doc.get('title', '無題')}")
                                        st.write(f"  - ソース: {doc.get('source', '不明')}")
                                        st.write(f"  - タイプ: {doc.get('mime_type', '不明')}")
                                        st.write(f"  - 文字数: {len(doc.get('content', ''))}")
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
                
            st.info("🔍 === Google Drive診断終了 ===")
                    
        except Exception as e:
            st.error(f"❌ Google Drive取得エラー: {e}")
            st.exception(e)
        
        # 3. Discordプロセッサー（スキップ）
        status_text.text("💬 Discord処理をスキップ中...")
        progress_bar.progress(70)
        st.info("💬 Discord統合: 一旦スキップ（今後実装予定）")
        
        # 4. ベクトルDBに統合
        status_text.text("🔄 ベクトルDBに統合中...")
        progress_bar.progress(90)
        
        st.info(f"🔄 統合処理: 合計{len(documents)}件のデータを処理中...")
        
        if documents:
            st.info(f"🔄 {len(documents)}件をベクトルDBに統合中...")
            
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            
            if vector_db.collection:
                vector_db.add_documents(documents)
                
                # 確認
                final_count = vector_db.collection.count()
                
                progress_bar.progress(100)
                status_text.text("✅ 統合完了!")
                
                st.success(f"🎉 データ統合完了: {final_count}件")
                
                # 統合結果詳細
                with st.expander("📊 統合結果詳細"):
                    sources = {}
                    for doc in documents:
                        source = doc.get('source', '不明')
                        sources[source] = sources.get(source, 0) + 1
                    
                    for source, count in sources.items():
                        st.write(f"- {source}: {count}件")
                
                return True
            else:
                st.error("❌ ベクトルDBが初期化されていません")
                return False
        else:
            progress_bar.progress(100)
            status_text.text("❌ 統合データなし")
            
            st.warning("⚠️ 統合するデータが見つかりませんでした")
            st.error("❌ 全てのサービスでデータが0件でした")
            
            return False
            
    except Exception as e:
        st.error(f"❌ 統合エラー: {e}")
        st.exception(e)
        return False

def safe_integration():
    """下位互換性のための関数"""
    return run_data_integration()

# 直接実行時のテスト
if __name__ == "__main__":
    safe_integration()
