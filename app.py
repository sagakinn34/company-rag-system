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

def main():
    st.title("🏢 企業RAGシステム v7.0 - Discord統合版")
    
    # サイドバー機能
    with st.sidebar:
        st.header("🔧 システム状態")
        
        # ベクトルDB接続状況
        try:
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            stats = vector_db.get_stats()
            st.success(f"✅ ベクトルDB接続: {stats['total_documents']}件")
        except Exception as e:
            st.error(f"❌ ベクトルDB接続エラー")
        
        st.header("📊 DB統計")
        if 'stats' in locals():
            st.metric("文書数", stats['total_documents'])
            st.metric("状態", stats['status'])
        
        st.header("🔑 環境変数チェック")
        env_checks = {
            "NOTION_TOKEN": st.secrets.get("NOTION_TOKEN"),
            "OPENAI_API_KEY": st.secrets.get("OPENAI_API_KEY"), 
            "DISCORD_TOKEN": st.secrets.get("DISCORD_TOKEN"),
            "GOOGLE_DRIVE_CREDENTIALS": st.secrets.get("GOOGLE_DRIVE_CREDENTIALS")
        }
        
        for var_name, var_value in env_checks.items():
            if var_value:
                st.success(f"✅ {var_name}")
            else:
                st.error(f"❌ {var_name}")
        
        st.header("🔄 データ統合")
        if st.button("🚀 データ統合実行"):
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
    
    # メインタブ構成
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 ホーム", "🔍 ベクトル検索", "💬 AIチャット", "📓 Notion統合"])
    
    with tab1:
        st.header("🏠 システム概要")
        st.markdown("""
        ### 🎯 企業RAGシステム v7.0の機能
        
        **🔍 データソース統合:**
        - **Notion**: ページ・データベース・テキストブロック・タスクリスト
        - **Google Drive**: PDF、Word、Excel、PowerPoint、テキストファイル
        - **Discord**: メッセージ履歴・チャンネル情報
        
        **🤖 AI分析機能:**
        - **OpenAI GPT-4o**: 128,000トークン対応
        - **RAG機能**: 関連文書を参照した回答生成
        - **ベクトル検索**: 意味的類似性による文書検索
        
        **📊 処理能力:**
        - 最大50件文書・5万文字の大容量処理
        - ChromaDBベクトル検索
        - SentenceTransformers埋め込み生成
        """)
        
        st.header("📋 使い方")
        st.markdown("""
        1. **データ統合**: サイドバーの「データ統合実行」で3サービスからデータを取得
        2. **ベクトル検索**: 関連文書をキーワードで検索
        3. **AIチャット**: RAG機能でコンテキスト付き対話
        4. **Notion統合**: Notionデータの詳細表示・管理
        """)
    
    with tab2:
        st.header("🔍 ベクトル検索")
        
        search_query = st.text_input("検索クエリを入力してください", placeholder="例: プロジェクトの進捗について")
        
        col1, col2 = st.columns([1, 4])
        with col1:
            max_results = st.slider("最大結果数", 1, 20, 5)
        
        if st.button("🔍 検索実行") and search_query:
            try:
                from vector_db_processor import VectorDBProcessor
                vector_db = VectorDBProcessor()
                
                with st.spinner("検索中..."):
                    results = vector_db.search(search_query, n_results=max_results)
                
                if results:
                    st.success(f"✅ {len(results)}件の関連文書が見つかりました")
                    
                    for i, result in enumerate(results):
                        with st.expander(f"📄 結果 {i+1}: {result['metadata'].get('title', '無題')} (類似度: {1-result['distance']:.3f})"):
                            st.write(f"**ソース**: {result['metadata'].get('source', '不明')}")
                            st.write(f"**タイプ**: {result['metadata'].get('type', '不明')}")
                            st.write("**内容**:")
                            st.text(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
                else:
                    st.warning("⚠️ 関連する文書が見つかりませんでした")
                    
            except Exception as e:
                st.error(f"❌ 検索エラー: {e}")
    
    with tab3:
        st.header("💬 AIチャット（RAG機能付き）")
        
        # チャット履歴の初期化
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # チャット履歴表示
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # ユーザー入力
        if prompt := st.chat_input("質問を入力してください..."):
            # ユーザーメッセージを履歴に追加
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # AI応答生成
            with st.chat_message("assistant"):
                with st.spinner("回答生成中..."):
                    try:
                        # 関連文書検索
                        from vector_db_processor import VectorDBProcessor
                        vector_db = VectorDBProcessor()
                        relevant_docs = vector_db.search(prompt, n_results=3)
                        
                        # コンテキスト構築
                        context = ""
                        if relevant_docs:
                            context = "\n\n".join([doc['content'][:300] for doc in relevant_docs])
                        
                        # OpenAI API呼び出し
                        import openai
                        openai.api_key = st.secrets["OPENAI_API_KEY"]
                        
                        messages = [
                            {"role": "system", "content": f"""あなたは企業の情報アシスタントです。以下の関連文書を参考にして、ユーザーの質問に答えてください。

関連文書:
{context}

回答は日本語で、簡潔で分かりやすく答えてください。関連文書に情報がない場合は、その旨を伝えてください。"""},
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
                        
                        # 参考文書表示
                        if relevant_docs:
                            with st.expander("📚 参考にした文書"):
                                for i, doc in enumerate(relevant_docs):
                                    st.write(f"**文書{i+1}**: {doc['metadata'].get('title', '無題')}")
                                    st.text(doc['content'][:200] + "...")
                        
                        # AI応答を履歴に追加
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        
                    except Exception as e:
                        error_msg = f"❌ AI応答エラー: {e}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
        
        # チャット履歴クリア
        if st.button("🗑️ チャット履歴をクリア"):
            st.session_state.messages = []
            st.rerun()
    
    with tab4:
        st.header("📓 Notion統合")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔄 Notionデータ更新"):
                try:
                    from notion_processor import NotionProcessor
                    
                    with st.spinner("Notionデータ取得中..."):
                        processor = NotionProcessor()
                        documents = processor.get_all_pages()
                    
                    if documents:
                        st.success(f"✅ {len(documents)}件のNotionデータを取得しました")
                        
                        # ベクトルDBに追加
                        from vector_db_processor import VectorDBProcessor
                        vector_db = VectorDBProcessor()
                        vector_db.add_documents(documents)
                        
                        st.success("✅ ベクトルDBに追加完了")
                    else:
                        st.warning("⚠️ Notionデータが見つかりませんでした")
                        
                except Exception as e:
                    st.error(f"❌ Notion取得エラー: {e}")
        
        with col2:
            if st.button("📊 Notion統計情報"):
                try:
                    from vector_db_processor import VectorDBProcessor
                    vector_db = VectorDBProcessor()
                    
                    # Notionソースの文書を検索
                    notion_results = vector_db.search("notion", n_results=100)
                    notion_docs = [r for r in notion_results if r['metadata'].get('source') == 'notion']
                    
                    st.metric("Notion文書数", len(notion_docs))
                    
                    # タイプ別統計
                    types = {}
                    for doc in notion_docs:
                        doc_type = doc['metadata'].get('type', '不明')
                        types[doc_type] = types.get(doc_type, 0) + 1
                    
                    st.write("**タイプ別統計:**")
                    for doc_type, count in types.items():
                        st.write(f"- {doc_type}: {count}件")
                        
                except Exception as e:
                    st.error(f"❌ 統計取得エラー: {e}")
        
        # Notion文書一覧表示
        st.subheader("📋 Notion文書一覧")
        try:
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            
            notion_results = vector_db.search("", n_results=50)  # 全文書取得
            notion_docs = [r for r in notion_results if r['metadata'].get('source') == 'notion']
            
            if notion_docs:
                for doc in notion_docs[:10]:  # 最初の10件表示
                    with st.expander(f"📄 {doc['metadata'].get('title', '無題')}"):
                        st.write(f"**タイプ**: {doc['metadata'].get('type', '不明')}")
                        st.write(f"**作成日**: {doc['metadata'].get('created_time', '不明')}")
                        st.write("**内容プレビュー:**")
                        st.text(doc['content'][:300] + "..." if len(doc['content']) > 300 else doc['content'])
            else:
                st.info("💡 Notionデータがありません。「Notionデータ更新」ボタンでデータを取得してください。")
                
        except Exception as e:
            st.error(f"❌ 文書一覧取得エラー: {e}")

if __name__ == "__main__":
    main()
