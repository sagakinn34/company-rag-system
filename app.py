import streamlit as st
import sys
import os

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# ページ設定
st.set_page_config(
    page_title="Company RAG System",
    page_icon="🏢",
    layout="wide"
)

def main():
    st.title("🏢 Company RAG System")
    st.markdown("### Notion統合版 - 企業データ統合検索システム")
    
    # システム状態確認（簡略版）
    with st.sidebar:
        st.header("🔧 システム状態")
        
        # ベクトルDB状態確認
        try:
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            db_info = vector_db.get_collection_info()
            if db_info["status"] == "active":
                st.success("ベクトルDB: 🟢 正常")
            else:
                st.error(f"ベクトルDB: 🔴 {db_info['status']}")
                
            # DB統計
            st.header("📊 DB統計")
            stats = vector_db.get_stats()
            st.metric("文書数", stats.get("total_documents", 0))
            
        except Exception as e:
            st.error(f"システムエラー: {e}")
        
        # 環境変数チェック
        st.subheader("🔑 環境変数チェック")
        env_vars = {
            "NOTION_TOKEN": st.secrets.get("NOTION_TOKEN"),
            "OPENAI_API_KEY": st.secrets.get("OPENAI_API_KEY"), 
            "DISCORD_TOKEN": st.secrets.get("DISCORD_TOKEN"),
            "GOOGLE_DRIVE_CREDENTIALS": st.secrets.get("GOOGLE_DRIVE_CREDENTIALS")
        }
        
        for var_name, var_value in env_vars.items():
            if var_value:
                st.success(f"✅ {var_name}")
            else:
                st.error(f"❌ {var_name}")
        
        # データ統合（デバッグ版）
        st.subheader("🔄 データ統合")
        st.write("👇 下のボタンでデータを統合してください")
        
        # final_integrationのインポートテスト
        integration_available = False
        import_error_msg = ""
        
        try:
            from final_integration import run_data_integration
            integration_available = True
            st.success("✅ データ統合モジュール: 正常")
        except ImportError as e:
            import_error_msg = str(e)
            try:
                # 代替パス
                sys.path.append('.')
                from final_integration import run_data_integration
                integration_available = True
                st.success("✅ データ統合モジュール: 正常（代替パス）")
            except ImportError as e2:
                st.error("❌ データ統合モジュールが見つかりません")
                st.error(f"エラー: {import_error_msg}")
                st.error(f"代替エラー: {str(e2)}")
        
        # データ統合ボタン
        if integration_available:
            if st.button("🔄 データを統合する", type="primary"):
                with st.spinner("データ統合処理中..."):
                    try:
                        st.info("📝 データ統合を開始...")
                        
                        # デバッグ用の詳細実行
                        success = run_data_integration()
                        
                        if success:
                            st.success("✅ データ統合が完了しました！")
                            st.experimental_rerun()
                        else:
                            st.error("❌ データ統合に失敗しました")
                            
                    except Exception as e:
                        st.error(f"❌ データ統合エラー: {e}")
                        st.exception(e)  # 詳細なエラー表示
        else:
            st.error("❌ データ統合機能が利用できません")
    
    # メインコンテンツ（簡略版）
    tab1, tab2, tab3 = st.tabs(["🏠 ホーム", "🔍 ベクトル検索", "📓 Notion統合"])
    
    with tab1:
        st.header("🏠 ホーム - システム概要")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **OpenAI GPTを使用した対話型AI**
            * ✨ RAG機能で文書検索と組み合わせ可能
            * 文書の追加・削除・管理機能
            * 📝 テキスト文書をベクトル化して保存
            """)
        
        with col2:
            st.markdown("""
            **Notionページ・DBからデータ取得**
            * 🔗 自動的にベクトル化・検索可能
            """)
        
        st.markdown("#### 🆕 新機能: Notion統合")
        
        if st.secrets.get("NOTION_TOKEN"):
            st.success("✅ Notion統合が有効です")
            
            st.markdown("#### 🔗 統合可能なNotionコンテンツ")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                * 📄 個別ページ
                * 🗄️ データベース
                """)
            with col2:
                st.markdown("""
                * 📝 テキストブロック
                * ✅ タスクリスト
                """)
                
        else:
            st.warning("⚠️ Notion統合には環境変数の設定が必要です")
        
        st.markdown("#### 📖 使い方")
        
        with st.expander("1️⃣ Notionデータの取得", expanded=False):
            st.markdown("""
            1. 左メニューから「📓 Notion統合」を選択
            2. 「接続テスト」でNotion接続を確認
            3. 「ページ・データベース一覧」を表示
            """)
        
        with st.expander("2️⃣ データの自動インポート", expanded=False):
            st.markdown("""
            1. インポートしたいページ・DBを選択
            2. 「ベクトルDBに追加」をクリック
            3. 自動的にテキスト抽出・ベクトル化
            """)
    
    with tab2:
        st.header("🔍 ベクトル検索")
        
        query = st.text_input("検索クエリを入力してください", placeholder="例: プロジェクトの進捗状況")
        
        if st.button("🔍 検索実行"):
            if query:
                with st.spinner("検索中..."):
                    try:
                        from vector_db_processor import VectorDBProcessor
                        vector_db = VectorDBProcessor()
                        results = vector_db.search(query)
                        
                        if results:
                            st.success(f"✅ {len(results)}件の結果が見つかりました")
                            
                            for i, result in enumerate(results[:5]):  # 上位5件表示
                                with st.expander(f"📄 結果 {i+1} - 類似度: {1-result['distance']:.3f}"):
                                    st.write("**内容:**")
                                    st.write(result['content'][:300] + "..." if len(result['content']) > 300 else result['content'])
                                    
                                    if result.get('metadata'):
                                        st.write("**メタデータ:**")
                                        st.json(result['metadata'])
                        else:
                            st.warning("⚠️ 検索結果が見つかりませんでした")
                    except Exception as e:
                        st.error(f"❌ 検索エラー: {e}")
                        st.exception(e)
            else:
                st.warning("検索クエリを入力してください")
    
    with tab3:
        st.header("📓 Notion統合")
        
        if not st.secrets.get("NOTION_TOKEN"):
            st.error("❌ NOTION_TOKENが設定されていません")
            st.info("Streamlit Secretsで環境変数を設定してください")
            return
        
        # Notion接続テスト
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔗 接続テスト"):
                with st.spinner("Notion接続テスト中..."):
                    try:
                        from notion_processor import NotionProcessor
                        notion = NotionProcessor()
                        st.success("✅ Notion接続成功")
                    except Exception as e:
                        st.error(f"❌ Notion接続エラー: {e}")
                        st.exception(e)
        
        with col2:
            if st.button("📋 ページ・DB一覧"):
                with st.spinner("ページ一覧取得中..."):
                    try:
                        from notion_processor import NotionProcessor
                        notion = NotionProcessor()
                        pages = notion.get_all_pages()
                        
                        if pages:
                            st.success(f"✅ {len(pages)}件のページを取得")
                            
                            for page in pages[:5]:  # 上位5件表示
                                with st.expander(f"📄 {page.get('title', 'タイトルなし')}"):
                                    st.json(page)
                        else:
                            st.warning("⚠️ ページが見つかりません")
                    except Exception as e:
                        st.error(f"❌ ページ取得エラー: {e}")
                        st.exception(e)
    
    # フッター
    st.markdown("---")
    st.markdown("🚀 **Company RAG System - Notion統合版**")
    st.markdown("Streamlit Cloud対応 | RAG + Notion Integration")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ アプリケーション起動エラー: {e}")
        st.exception(e)
