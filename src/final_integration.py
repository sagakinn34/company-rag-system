import sys
import os
import streamlit as st

# 絶対パスでsrcディレクトリを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', 'src') if 'src' not in current_dir else current_dir
sys.path.insert(0, src_path)

def run_data_integration():
    """Streamlit UI表示付きデータ統合関数（完全版）"""
    
    # 統合開始表示
    st.info("🚀 データ統合を開始...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    try:
        documents = []
        
        # 1. Notionプロセッサー
        status_text.text("📝 Notionからデータ取得中...")
        progress_bar.progress(10)
        
        try:
            # Notion TOKENの確認
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
                
        except ImportError as e:
            st.error(f"❌ NotionProcessor インポートエラー: {e}")
        except Exception as e:
            st.error(f"❌ Notion取得エラー: {e}")
        
        # 2. Google Driveプロセッサー
        status_text.text("📂 Google Driveからデータ取得中...")
        progress_bar.progress(40)
        
        try:
            # Google Drive認証の確認
            gdrive_creds = st.secrets.get("GOOGLE_DRIVE_CREDENTIALS")
            if gdrive_creds:
                st.info("📂 GOOGLE_DRIVE_CREDENTIALS: ✅ 設定済み")
                
                from gdrive_processor import GoogleDriveProcessor
                st.success("📂 gdrive_processor インポート成功")
                
                gdrive = GoogleDriveProcessor()
                st.success("📂 GoogleDriveProcessor インスタンス作成成功")
                
                gdrive_docs = gdrive.get_all_files()
                st.info(f"📂 Google Drive取得結果: {len(gdrive_docs) if gdrive_docs else 0}件")
                
                if gdrive_docs:
                    documents.extend(gdrive_docs)
                    st.success(f"✅ Google Drive: {len(gdrive_docs)}件取得成功")
                else:
                    st.warning("⚠️ Google Driveデータが空です")
            else:
                st.error("❌ GOOGLE_DRIVE_CREDENTIALSが設定されていません")
                    
        except ImportError as e:
            st.error(f"❌ Google Drive モジュール インポートエラー: {e}")
        except Exception as e:
            st.error(f"❌ Google Drive取得エラー: {e}")
        
        # 3. Discordプロセッサー（一旦スキップ）
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
            vector_db.add_documents(documents)
            
            # 確認
            final_count = vector_db.collection.count()
            
            progress_bar.progress(100)
            status_text.text("✅ 統合完了!")
            
            st.success(f"🎉 データ統合完了: {final_count}件")
            
            return True
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
