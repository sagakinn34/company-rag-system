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
    st.title("🏢 企業RAGシステム v7.0 - 最適化版")
    
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
        if st.button("🚀 最適化統合実行"):
            if vector_db and vector_db.collection:
                try:
                    from final_integration import run_data_integration
                    result = run_data_integration()
                    if result:
                        st.success("✅ 最適化統合完了")
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
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 ホーム", "🔍 高度検索・分析", "💬 AIチャット", "📓 Notion統合"])
    
    with tab1:
        st.header("🏠 システム概要")
        st.markdown("""
        ### 🎯 企業RAGシステム v7.0の機能（最適化版）
        
        **🔍 データソース統合:**
        - **Notion**: ページ・データベース（150件上限）
        - **Google Drive**: PDF、Word、Excel、PowerPoint（100件上限）
        - **Discord**: メッセージ履歴（今後実装）
        
        **🤖 AI分析機能:**
        - **OpenAI GPT-4o**: 128,000トークン対応
        - **高度分析**: 包括的要約・深層洞察・戦略的推奨
        - **ベクトル検索**: 意味的類似性による文書検索
        
        **⚖️ 最適化特徴:**
        - **実用性**: 十分な情報量（250件）
        - **可用性**: 安定した動作（処理時間短縮）
        - **効率性**: メモリ使用量最適化
        
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
        st.header("🔍 高度検索・分析システム")
        
        # 検索クエリ入力
        search_query = st.text_input(
            "🔍 検索・分析クエリを入力してください",
            placeholder="例: 営業戦略について、プロジェクト進捗について、技術的課題について"
        )
        
        # 検索モード選択
        search_mode = st.radio(
            "検索モード:",
            ["🔍 標準検索", "🧠 高度分析"],
            horizontal=True
        )
        
        if search_mode == "🔍 標準検索":
            # 既存の標準検索
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
        
        else:  # 高度分析モード
            # 分析設定
            with st.expander("⚙️ 高度分析設定", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    analysis_type = st.selectbox(
                        "📊 分析タイプ:",
                        options=["summary", "insights", "recommendations"],
                        format_func=lambda x: {
                            "summary": "📋 包括的要約（詳細版）",
                            "insights": "💡 深層洞察（多角的分析）",
                            "recommendations": "🚀 戦略的推奨（実行計画付き）"
                        }[x]
                    )
                
                with col2:
                    max_results = st.slider(
                        "📚 参照データ数",
                        min_value=10,
                        max_value=50,
                        value=20,
                        help="多いほど包括的ですが、処理時間が増加します"
                    )
            
            # 高度分析実行
            if st.button("🚀 高度分析実行", type="primary") and search_query and vector_db:
                with st.spinner("🧠 高度分析実行中..."):
                    # ベクトル検索
                    results = vector_db.search(search_query, n_results=max_results)
                    
                    if results:
                        st.success(f"✅ {len(results)}件の関連データを発見")
                        
                        # AI分析実行
                        analysis_result = perform_ai_analysis(search_query, results, analysis_type)
                        
                        # 結果表示
                        st.markdown("---")
                        st.markdown(f"## 🎯 「{search_query}」の分析結果")
                        st.markdown(analysis_result)
                        
                        # 参照データ詳細
                        display_reference_data(results)
                        
                    else:
                        st.warning("⚠️ 関連データが見つかりませんでした")
    
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

def perform_ai_analysis(query: str, results: list, analysis_type: str) -> str:
    """AI分析実行（最適化版）"""
    
    if not st.secrets.get("OPENAI_API_KEY"):
        return "❌ OpenAI APIキーが設定されていません"
    
    try:
        import openai
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        
        # コンテキスト構築（最適化）
        context_parts = []
        total_chars = 0
        max_context_chars = 12000  # コンテキスト制限
        
        for i, result in enumerate(results[:20]):  # 上位20件に制限
            title = result['metadata'].get('title', '無題')
            source = result['metadata'].get('source', '不明')
            content = result['content']
            similarity = 1 - result['distance']
            
            # コンテンツ長の調整
            if total_chars + len(content) > max_context_chars:
                remaining_chars = max_context_chars - total_chars
                content = content[:remaining_chars] + "..."
            
            context_part = f"""
【参照{i+1}】{title} ({source}) - 類似度: {similarity:.3f}
{content}
"""
            context_parts.append(context_part)
            total_chars += len(context_part)
            
            if total_chars >= max_context_chars:
                break
        
        context = "\n".join(context_parts)
        
        # 分析タイプ別プロンプト（最適化版）
        prompts = {
            "summary": f"""
以下のデータから「{query}」について包括的な要約を作成してください。

【要求事項】
- 主要ポイント3-4個に整理
- 各ポイントは簡潔かつ具体的に
- 重要な数値・データを明記
- 実用的な情報を優先

【参照データ】
{context}

【出力形式】
## 📋 包括的要約

### 🎯 主要ポイント
1. **ポイント1**: 簡潔な説明
2. **ポイント2**: 簡潔な説明
3. **ポイント3**: 簡潔な説明

### 📊 重要データ
- 数値・統計情報
- 重要な事実

### 💡 実用的示唆
- 活用可能な知見
- 注意すべき点
""",
            
            "insights": f"""
以下のデータから「{query}」について深層洞察と多角的分析を提供してください。

【要求事項】
- 表面的でない深い洞察
- 複数視点からの分析
- 潜在的課題・機会の発見
- 実用的な気づき

【参照データ】
{context}

【出力形式】
## 💡 深層洞察

### 🔍 核心的発見
- 最重要な洞察
- 隠れた課題・機会

### 📐 多角的分析
**経営視点**: 
**現場視点**: 
**市場視点**: 

### ⚡ 重要要因
- 成功要因
- リスク要因

### 🔮 将来展望
- 予想される変化
- 対策の方向性
""",
            
            "recommendations": f"""
以下のデータから「{query}」について戦略的推奨と実行計画を提供してください。

【要求事項】
- 具体的で実行可能な推奨
- 優先度付きアクション
- 期待効果の明記
- 実行時の注意点

【参照データ】
{context}

【出力形式】
## 🚀 戦略的推奨

### 🎯 主要推奨事項
1. **推奨1**: 具体的内容と理由
2. **推奨2**: 具体的内容と理由
3. **推奨3**: 具体的内容と理由

### 📋 実行計画
#### 🔥 最優先（即時）
- [ ] アクション1: 詳細
- [ ] アクション2: 詳細

#### ⭐ 高優先（1-3ヶ月）
- [ ] アクション3: 詳細

#### 📈 中優先（長期）
- [ ] アクション4: 詳細

### 📊 期待効果
- 定量的効果
- 定性的効果

### ⚠️ 実行時注意点
- リスク要因
- 成功のポイント
"""
        }
        
        # AI分析実行
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system",
                    "content": "あなたは企業の戦略コンサルタントです。提供されたデータを効率的に分析し、実用的で具体的な洞察を提供してください。"
                },
                {
                    "role": "user",
                    "content": prompts[analysis_type]
                }
            ],
            max_tokens=1500,  # レスポンス最適化
            temperature=0.7,
            timeout=30  # タイムアウト設定
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ AI分析エラー: {str(e)}"

def display_reference_data(results):
    """参照データ表示（最適化版）"""
    
    with st.expander(f"📚 参照データ詳細（{len(results)}件）"):
        
        # 統計情報
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_similarity = sum([1-r['distance'] for r in results]) / len(results)
            st.metric("平均類似度", f"{avg_similarity:.3f}")
        
        with col2:
            sources = {}
            for r in results:
                source = r['metadata'].get('source', '不明')
                sources[source] = sources.get(source, 0) + 1
            st.write("**ソース分布:**")
            for source, count in sources.items():
                st.write(f"- {source}: {count}件")
        
        with col3:
            total_chars = sum([len(r['content']) for r in results])
            st.metric("総参照文字数", f"{total_chars:,}")
        
        # 上位参照文書（簡潔版）
        st.write("**上位参照文書:**")
        for i, result in enumerate(results[:10]):  # 上位10件のみ
            title = result['metadata'].get('title', '無題')
            source = result['metadata'].get('source', '不明')
            similarity = 1 - result['distance']
            
            with st.expander(f"{i+1}. {title} ({source}) - 類似度: {similarity:.3f}"):
                content_preview = result['content'][:300] + "..." if len(result['content']) > 300 else result['content']
                st.text(content_preview)

if __name__ == "__main__":
    main()
