import streamlit as st
import sys
import os

# パス設定
sys.path.append('src')

st.set_page_config(
    page_title="Company RAG System Debug",
    page_icon="🏢"
)

def main():
    st.title("🏢 Company RAG System - デバッグ版")
    
    # 基本動作確認
    st.header("🔍 システム診断")
    
    # 1. Python環境確認
    st.subheader("1. Python環境")
    st.write(f"Python バージョン: {sys.version}")
    st.write(f"作業ディレクトリ: {os.getcwd()}")
    
    # 2. ファイル存在確認
    st.subheader("2. ファイル構成確認")
    
    files_to_check = [
        'src/vector_db_processor.py',
        'src/notion_processor.py', 
        'src/gdrive_processor.py',
        'src/discord_processor.py',
        'final_integration.py'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            st.success(f"✅ {file_path}")
        else:
            st.error(f"❌ {file_path}")
    
    # 3. インポートテスト
    st.subheader("3. モジュールインポートテスト")
    
    # vector_db_processor
    try:
        from vector_db_processor import VectorDBProcessor
        st.success("✅ vector_db_processor インポート成功")
        
        # インスタンス作成テスト
        try:
            vector_db = VectorDBProcessor()
            st.success("✅ VectorDBProcessor インスタンス作成成功")
            
            # 統計取得テスト
            try:
                stats = vector_db.get_stats()
                st.success(f"✅ DB統計取得成功: {stats}")
            except Exception as e:
                st.error(f"❌ DB統計取得エラー: {e}")
                
        except Exception as e:
            st.error(f"❌ VectorDBProcessor インスタンス作成エラー: {e}")
            
    except Exception as e:
        st.error(f"❌ vector_db_processor インポートエラー: {e}")
    
    # final_integration
    try:
        from final_integration import run_data_integration
        st.success("✅ final_integration インポート成功")
    except Exception as e:
        st.error(f"❌ final_integration インポートエラー: {e}")
    
    # notion_processor
    try:
        from notion_processor import NotionProcessor
        st.success("✅ notion_processor インポート成功")
    except Exception as e:
        st.error(f"❌ notion_processor インポートエラー: {e}")
    
    # 4. 環境変数確認
    st.subheader("4. 環境変数確認")
    
    env_vars = {
        "NOTION_TOKEN": st.secrets.get("NOTION_TOKEN"),
        "OPENAI_API_KEY": st.secrets.get("OPENAI_API_KEY"),
        "DISCORD_TOKEN": st.secrets.get("DISCORD_TOKEN"),
        "GOOGLE_DRIVE_CREDENTIALS": st.secrets.get("GOOGLE_DRIVE_CREDENTIALS")
    }
    
    for var_name, var_value in env_vars.items():
        if var_value:
            st.success(f"✅ {var_name}: 設定済み")
        else:
            st.error(f"❌ {var_name}: 未設定")
    
    # 5. 簡易データ統合テスト
    st.subheader("5. データ統合テスト")
    
    if st.button("🧪 簡易統合テスト"):
        st.info("テスト実行中...")
        
        try:
            # final_integrationの関数を直接呼び出し
            from final_integration import run_data_integration
            
            with st.spinner("統合処理中..."):
                result = run_data_integration()
                
            if result:
                st.success("✅ データ統合テスト成功")
            else:
                st.warning("⚠️ データ統合テスト - データなし")
                
        except Exception as e:
            st.error(f"❌ データ統合テストエラー: {e}")
            st.exception(e)
    
    # 6. 基本検索テスト
    st.subheader("6. ベクトル検索テスト")
    
    query = st.text_input("テスト検索クエリ", value="テスト")
    
    if st.button("🔍 検索テスト") and query:
        try:
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            results = vector_db.search(query, n_results=3)
            
            if results:
                st.success(f"✅ 検索成功: {len(results)}件")
                for i, result in enumerate(results):
                    st.write(f"**結果{i+1}:** {result['content'][:100]}...")
            else:
                st.warning("⚠️ 検索結果なし")
                
        except Exception as e:
            st.error(f"❌ 検索テストエラー: {e}")
            st.exception(e)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ アプリケーション起動エラー: {e}")
        st.exception(e)
