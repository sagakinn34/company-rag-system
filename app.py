import streamlit as st
import sys
import os

# パス設定
sys.path.append('src')

st.set_page_config(
    page_title="企業RAGシステム v7.0",
    page_icon="🏢",
    layout="wide"
)

def check_system_requirements():
    """システム要件チェック"""
    st.sidebar.header("🔧 システム診断")
    
    # SQLite3バージョンチェック
    try:
        import sqlite3
        sqlite_version = sqlite3.sqlite_version
        st.sidebar.info(f"SQLite3バージョン: {sqlite_version}")
        
        # バージョン比較
        version_parts = [int(x) for x in sqlite_version.split('.')]
        if version_parts >= [3, 35, 0]:
            st.sidebar.success("✅ SQLite3バージョン: 対応済み")
        else:
            st.sidebar.warning("⚠️ SQLite3バージョン: 要対応")
            
    except Exception as e:
        st.sidebar.error(f"❌ SQLite3チェックエラー: {e}")
    
    # ChromaDBチェック
    try:
        from vector_db_processor import VectorDBProcessor
        vector_db = VectorDBProcessor()
        if vector_db.collection:
            stats = vector_db.get_stats()
            st.sidebar.success(f"✅ ChromaDB: {stats['total_documents']}件")
            return vector_db
        else:
            st.sidebar.error("❌ ChromaDB: 初期化失敗")
            return None
    except Exception as e:
        st.sidebar.error(f"❌ ChromaDBエラー: {e}")
        return None

def main():
    st.title("🏢 企業RAGシステム v7.0 - Discord統合版")
    
    # システム診断
    vector_db = check_system_requirements()
    
    # 環境変数チェック
    with st.sidebar:
        st.header("🔑 環境変数")
        env_checks = {
            "NOTION_TOKEN": bool(st.secrets.get("NOTION_TOKEN")),
            "OPENAI_API_KEY": bool(st.secrets.get("OPENAI_API_KEY")),
            "DISCORD_TOKEN": bool(st.secrets.get("DISCORD_TOKEN")),
            "GOOGLE_DRIVE_CREDENTIALS": bool(st.secrets.get("GOOGLE_DRIVE_CREDENTIALS"))
        }
        
        for var_name, is_set in env_checks.items():
            if is_set:
                st.success(f"✅ {var_name}")
            else:
                st.error(f"❌ {var_name}")
        
        # データ統合
        st.header("🔄 データ統合")
        if st.button("🚀 データ統合実行"):
            if vector_db and vector_db.collection:
                try:
                    from final_integration import run_data_integration
                    result = run_data_integration()
                    if result:
                        st.success("✅ データ統合完了")
                        st.rerun()
                    else:
                        st.warning("⚠️ データが見つかりませんでした")
                except Exception as e:
                    st.error(f"❌ 統合エラー: {e}")
            else:
                st.error("❌ ChromaDBが利用できません")
    
    # システムが正常でない場合の警告表示
    if not vector_db or not vector_db.collection:
        st.error("🚨 システム初期化エラー")
        st.markdown("""
        **ChromaDBの初期化に失敗しました。**
        
        考えられる原因：
        - SQLite3バージョンの問題
        - 依存関係の競合
        - メモリ不足
        
        **対処方法：**
        1. ページを再読み込みしてください
        2. 問題が続く場合は、システム管理者にお問い合わせください
        """)
        return
    
    # 正常な場合は本来のタブ構成を表示
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 ホーム", "🔍 ベクトル検索", "💬 AIチャット", "📓 Notion統合"])
    
    with tab1:
        st.header("🏠 システム概要")
        st.markdown("""
        ### 🎯 企業RAGシステム v7.0の機能
        
        **🔍 データソース統合:**
        - **Notion**: ページ・データベース・テキストブロック・タスクリスト
        - **Google Drive**: PDF、Word、Excel、PowerPoint、テキストファイル
        - **Discord**: メッセージ履歴・チャンネル情報（今後実装）
        
        **🤖 AI分析機能:**
        - **OpenAI GPT-4o**: 128,000トークン対応
        - **RAG機能**: 関連文書を参照した回答生成
        - **ベクトル検索**: 意味的類似性による文書検索
        
        **📊 現在の状況:**
        """)
        
        # 統計情報表示
        if vector_db:
            stats = vector_db.get_stats()
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("文書数", stats['total_documents'])
            with col2:
                st.metric("ステータス", stats['status'])
            with col3:
                st.metric("ChromaDB", "✅ 正常")
    
    with tab2:
        st.header("🔍 ベクトル検索")
        
        search_query = st.text_input("検索クエリを入力してください")
        max_results = st.slider("最大結果数", 1, 20, 5)
        
        if st.button("🔍 検索実行") and search_query and vector_db:
            with st.spinner("検索中..."):
                results = vector_db.search(search_query, n_results=max_results)
            
            if results:
                st.success(f"✅ {len(results)}件の関連文書が見つかりました")
                for i, result in enumerate(results):
                    with st.expander(f"📄 結果 {i+1}: {result['metadata'].get('title', '無題')}"):
                        st.write(f"**ソース**: {result['metadata'].get('source', '不明')}")
                        st.write(f"**類似度**: {1-result['distance']:.3f}")
                        st.text(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
            else:
                st.warning("⚠️ 関連する文書が見つかりませんでした")
    
    with tab3:
        st.header("💬 AIチャット（RAG機能付き）")
        
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # チャット履歴表示
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # ユーザー入力
        if prompt := st.chat_input("質問を入力してください..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # AI応答生成
            with st.chat_message("assistant"):
                if vector_db and st.secrets.get("OPENAI_API_KEY"):
                    try:
                        # 関連文書検索
                        relevant_docs = vector_db.search(prompt, n_results=3)
                        
                        # OpenAI API呼び出し
                        import openai
                        openai.api_key = st.secrets["OPENAI_API_KEY"]
                        
                        context = ""
                        if relevant_docs:
                            context = "\n\n".join([doc['content'][:300] for doc in relevant_docs])
                        
                        messages = [
                            {"role": "system", "content": f"""あなたは企業の情報アシスタントです。以下の関連文書を参考にして質問に答えてください。

関連文書:
{context}

回答は日本語で簡潔に答えてください。"""},
                            {"role": "user", "content": prompt}
                        ]
                        
                        response = openai.ChatCompletion.create(
                            model="gpt-4",
                            messages=messages,
                            max_tokens=1000,
                            temperature=0.7
                        )
                        
                        ai_response = response.choices[0].message.content
                        st.markdown(ai_response)
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        
                    except Exception as e:
                        error_msg = f"❌ AI応答エラー: {e}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
                else:
                    error_msg = "❌ ChromaDBまたはOpenAI APIが利用できません"
                    st.error(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        if st.button("🗑️ チャット履歴をクリア"):
            st.session_state.messages = []
            st.rerun()
    
    with tab4:
        st.header("📓 Notion統合")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Notionデータ更新"):
                if vector_db and st.secrets.get("NOTION_TOKEN"):
                    try:
                        from notion_processor import NotionProcessor
                        
                        with st.spinner("Notionデータ取得中..."):
                            processor = NotionProcessor()
                            documents = processor.get_all_pages()
                        
                        if documents:
                            vector_db.add_documents(documents)
                            st.success(f"✅ {len(documents)}件のNotionデータを統合しました")
                        else:
                            st.warning("⚠️ Notionデータが見つかりませんでした")
                            
                    except Exception as e:
                        st.error(f"❌ Notion取得エラー: {e}")
                else:
                    st.error("❌ ChromaDBまたはNOTION_TOKENが利用できません")
        
        with col2:
            if st.button("📊 Notion統計情報") and vector_db:
                try:
                    # 全体統計
                    stats = vector_db.get_stats()
                    st.metric("総文書数", stats['total_documents'])
                    
                    # Notion固有の統計は検索で取得
                    notion_results = vector_db.search("notion", n_results=100)
                    notion_docs = [r for r in notion_results if r['metadata'].get('source') == 'notion']
                    st.metric("Notion文書数", len(notion_docs))
                    
                except Exception as e:
                    st.error(f"❌ 統計取得エラー: {e}")

if __name__ == "__main__":
    main()
