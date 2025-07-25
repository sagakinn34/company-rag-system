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
    st.title("🏢 企業RAGシステム v7.0 - GPT-4o大容量対応版")
    
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
        ### 🎯 企業RAGシステム v7.0の機能（GPT-4o大容量対応版）
        
        **🔍 データソース統合:**
        - **Notion**: ページ・データベース（150件上限）
        - **Google Drive**: PDF、Word、Excel、PowerPoint（100件上限）
        - **Discord**: メッセージ履歴（今後実装）
        
        **🤖 AI分析機能:**
        - **OpenAI GPT-4o**: 128,000トークン対応
        - **高度分析**: 包括的要約・深層洞察・戦略的推奨
        - **大容量処理**: 最大50件参照・5万文字処理
        - **ベクトル検索**: 意味的類似性による文書検索
        
        **⚖️ 最適化特徴:**
        - **実用性**: 十分な情報量（250件）
        - **可用性**: 安定した動作（処理時間短縮）
        - **大容量**: GPT-4oの128Kトークンフル活用
        
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
                st.metric("AI Model", "GPT-4o (128K)")
    
    with tab2:
        st.header("🔍 高度検索・分析システム（GPT-4o大容量対応）")
        
        # 検索クエリ入力
        search_query = st.text_input(
            "🔍 検索・分析クエリを入力してください",
            placeholder="例: 営業戦略について、プロジェクト進捗について、技術的課題について"
        )
        
        # 検索モード選択
        search_mode = st.radio(
            "検索モード:",
            ["🔍 標準検索", "🧠 高度分析（GPT-4o）"],
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
        
        else:  # 高度分析モード（GPT-4o）
            # GPT-4o大容量分析設定
            with st.expander("⚙️ GPT-4o高度分析設定", expanded=True):
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
                        max_value=50,  # GPT-4oなら50件でも問題なし
                        value=30,      # デフォルトを30に
                        help="GPT-4oの128Kトークンで大容量処理可能"
                    )
                
                # GPT-4o性能情報
                st.info("""
                🚀 **GPT-4o大容量処理モード**
                - **トークン制限**: 128,000トークン（約10万文字）
                - **処理能力**: 50件の文書を詳細分析可能
                - **応答品質**: 高度で包括的な分析結果
                """)
            
            # GPT-4o高度分析実行
            if st.button("🚀 GPT-4o高度分析実行", type="primary") and search_query and vector_db:
                with st.spinner("🧠 GPT-4o大容量分析実行中..."):
                    # ベクトル検索
                    results = vector_db.search(search_query, n_results=max_results)
                    
                    if results:
                        st.success(f"✅ {len(results)}件の関連データを発見")
                        
                        # GPT-4o AI分析実行
                        analysis_result = perform_ai_analysis_gpt4o(search_query, results, analysis_type)
                        
                        # 結果表示
                        st.markdown("---")
                        st.markdown(f"## 🎯 「{search_query}」のGPT-4o分析結果")
                        st.markdown(analysis_result)
                        
                        # 参照データ詳細
                        display_reference_data_comprehensive(results)
                        
                    else:
                        st.warning("⚠️ 関連データが見つかりませんでした")
    
    with tab3:
        st.header("💬 AIチャット（RAG機能付き・GPT-4o）")
        
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
                        relevant_docs = vector_db.search(prompt, n_results=5)
                        
                        # OpenAI API呼び出し（GPT-4o）
                        import openai
                        openai.api_key = st.secrets["OPENAI_API_KEY"]
                        
                        context = ""
                        if relevant_docs:
                            context = "\n\n".join([doc['content'][:500] for doc in relevant_docs])
                        
                        messages = [
                            {"role": "system", "content": f"""あなたは企業の情報アシスタントです。以下の関連文書を参考にして質問に答えてください。

関連文書:
{context}

回答は日本語で詳細かつ実用的に答えてください。GPT-4oの大容量処理能力を活用して、包括的な回答を提供してください。"""},
                            {"role": "user", "content": prompt}
                        ]
                        
                        response = openai.ChatCompletion.create(
                            model="gpt-4o",  # GPT-4oに変更
                            messages=messages,
                            max_tokens=2000,  # レスポンス量を増加
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

def perform_ai_analysis_gpt4o(query: str, results: list, analysis_type: str) -> str:
    """GPT-4o AI分析実行（128K大容量対応）"""
    
    if not st.secrets.get("OPENAI_API_KEY"):
        return "❌ OpenAI APIキーが設定されていません"
    
    try:
        import openai
        openai.api_key = st.secrets["OPENAI_API_KEY"]
        
        # GPT-4o大容量コンテキスト構築
        context = build_comprehensive_context_gpt4o(results, query)
        
        # 詳細プロンプト生成
        prompt = get_detailed_prompt_gpt4o(query, context, analysis_type)
        
        # GPT-4o分析実行
        response = openai.ChatCompletion.create(
            model="gpt-4o",  # GPT-4oを明示的に指定
            messages=[
                {
                    "role": "system",
                    "content": """あなたは企業の上級戦略コンサルタントです。GPT-4oの128,000トークンの大容量処理能力を活用して、
                    提供された大量のデータを総合的に分析し、深い洞察と実用的な戦略提案を提供してください。
                    包括的で詳細な分析を行い、ビジネス価値の高い洞察を提供してください。"""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            max_tokens=4000,  # 詳細なレスポンス
            temperature=0.7,
            timeout=120  # 2分のタイムアウト
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        return f"❌ GPT-4o分析エラー: {str(e)}\n\n💡 ヒント: データ量が多い場合は参照データ数を調整してください。"

def build_comprehensive_context_gpt4o(results: list, query: str) -> str:
    """GPT-4o用包括的コンテキスト構築（128K対応）"""
    
    context_parts = []
    
    # GPT-4oなら大容量処理可能
    for i, result in enumerate(results):
        title = result['metadata'].get('title', '無題')
        source = result['metadata'].get('source', '不明')
        content = result['content']
        similarity = 1 - result['distance']
        category = result.get('category', '一般')
        
        # 詳細なコンテキスト作成（文字数制限なし）
        context_part = f"""
=== 参照文書 {i+1} ===
【タイトル】{title}
【ソース】{source}
【カテゴリ】{category}
【類似度】{similarity:.3f}
【内容】
{content}

"""
        context_parts.append(context_part)
    
    comprehensive_context = "".join(context_parts)
    
    # GPT-4oの128Kトークン内に収まるよう調整（約10万文字以下）
    if len(comprehensive_context) > 100000:
        # 必要に応じて上位結果のみに制限
        truncated_parts = context_parts[:int(len(context_parts) * 0.8)]
        comprehensive_context = "".join(truncated_parts)
        comprehensive_context += "\n\n※注: 大容量データのため一部を選抜して分析しています。"
    
    return comprehensive_context

def get_detailed_prompt_gpt4o(query: str, context: str, analysis_type: str) -> str:
    """GPT-4o用詳細プロンプト（128K対応）"""
    
    prompts = {
        "summary": f"""
以下の大量のデータから「{query}」について包括的で詳細な要約を作成してください。

【分析要求】
- 主要ポイントを5-7個に整理
- 各ポイントについて詳細で具体的な説明
- 重要な数値・データ・事実を全て明記
- データ間の関連性や一貫性の分析
- 異なる視点からの多角的考察
- 実用的で具体的な示唆

【出力形式】
## 📋 包括的要約（詳細版）

### 🎯 主要発見事項
1. **発見1**: 詳細な説明と根拠
2. **発見2**: 詳細な説明と根拠
3. **発見3**: 詳細な説明と根拠
4. **発見4**: 詳細な説明と根拠
5. **発見5**: 詳細な説明と根拠

### 📊 重要データ・統計
- 数値データの詳細分析
- 重要な統計情報
- トレンドや変化の分析

### 🔗 データ間の関連性
- 文書間の一貫性分析
- 矛盾点や課題の特定
- 相互関係の分析

### 💡 実用的示唆
- 活用可能な具体的知見
- 注意すべき重要なポイント
- 今後の方向性

### 📈 総合評価
- 全体的な状況評価
- 強み・弱みの分析

【参照データ】
{context}
""",

        "insights": f"""
以下の大量のデータから「{query}」について深層的な洞察と多角的分析を提供してください。

【分析要求】
- 表面的でない深い洞察の発見
- 複数の視点からの包括的分析
- 潜在的な課題・機会・リスクの特定
- 業界動向や将来予測
- 戦略的含意の分析
- クリティカルな成功要因の特定

【出力形式】
## 💡 深層洞察（多角的分析）

### 🔍 核心的発見
- 最も重要で深い洞察
- 隠れた課題・機会の発見
- 意外な発見や気づき

### 📐 多角的分析
**🏢 経営視点**
- 経営層が注目すべきポイント
- 戦略的含意

**👥 現場視点**
- 実務への影響
- オペレーションの課題・機会

**📈 市場・顧客視点**
- 市場動向との関連
- 顧客への影響

**💰 財務・リスク視点**
- 財務的インパクト
- リスク要因

### ⚡ クリティカル要因
- 成功を左右する重要要因
- 注意すべきリスク要因
- 競争優位の源泉

### 🔮 将来展望・予測
- 予想される展開
- 注意すべきトレンド
- 長期的な影響

### 🎯 戦略的含意
- 戦略への影響
- 意思決定への示唆

【参照データ】
{context}
""",

        "recommendations": f"""
以下の大量のデータから「{query}」について戦略的推奨事項と詳細な実行計画を提供してください。

【分析要求】
- 具体的で実行可能な推奨事項
- 優先度とタイムライン付きのアクションプラン
- 期待される効果とKPIの明確化
- 実行時のリスクと対策
- 必要なリソースと体制
- 成功要因と注意点

【出力形式】
## 🚀 戦略的推奨（実行計画付き）

### 🎯 主要推奨事項
1. **推奨事項1**: 
   - 内容: 詳細な説明
   - 理由: 根拠と期待効果
   - 優先度: 高/中/低

2. **推奨事項2**:
   - 内容: 詳細な説明
   - 理由: 根拠と期待効果
   - 優先度: 高/中/低

3. **推奨事項3**:
   - 内容: 詳細な説明
   - 理由: 根拠と期待効果
   - 優先度: 高/中/低

### 📋 詳細実行計画

#### 🔥 最優先（即時実行: 1-4週間）
- [ ] **アクション1**: 具体的内容・担当・期限・成果物
- [ ] **アクション2**: 具体的内容・担当・期限・成果物

#### ⭐ 高優先（短期実行: 1-3ヶ月）
- [ ] **アクション3**: 具体的内容・担当・期限・成果物
- [ ] **アクション4**: 具体的内容・担当・期限・成果物

#### 📈 中優先（中期実行: 3-6ヶ月）
- [ ] **アクション5**: 具体的内容・担当・期限・成果物

#### 🎯 長期（戦略実行: 6ヶ月以上）
- [ ] **アクション6**: 具体的内容・担当・期限・成果物

### 📊 期待効果・KPI
**定量的効果**
- 具体的な数値目標
- 測定可能な指標

**定性的効果**  
- 改善される事項
- 波及効果

**KPI設定**
- 測定指標と目標値
- モニタリング方法

### 💰 必要リソース・体制
- 人的リソース
- 予算・投資
- システム・ツール
- 外部パートナー

### ⚠️ リスク・対策
**主要リスク**
- リスク要因の特定
- 影響度と発生確率

**対策・軽減策**
- 予防策
- 発生時の対応策

### 🏆 成功要因
- 成功のための重要ポイント
- 推進体制・ガバナンス
- コミュニケーション戦略

【参照データ】
{context}
"""
    }
    
    return prompts[analysis_type]

def display_reference_data_comprehensive(results):
    """包括的参照データ表示（GPT-4o対応）"""
    
    with st.expander(f"📚 参照データ詳細分析（{len(results)}件 - GPT-4o処理済み）"):
        
        # 詳細統計情報
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_similarity = sum([1-r['distance'] for r in results]) / len(results)
            st.metric("平均類似度", f"{avg_similarity:.3f}")
        
        with col2:
            total_chars = sum([len(r['content']) for r in results])
            st.metric("総文字数", f"{total_chars:,}")
        
        with col3:
            sources = {}
            for r in results:
                source = r['metadata'].get('source', '不明')
                sources[source] = sources.get(source, 0) + 1
            st.metric("データソース数", len(sources))
        
        with col4:
            high_relevance = len([r for r in results if (1-r['distance']) > 0.7])
            st.metric("高関連度文書", f"{high_relevance}件")
        
        # ソース分布
        st.write("**📊 データソース分布:**")
        for source, count in sources.items():
            percentage = (count / len(results)) * 100
            st.write(f"- {source}: {count}件 ({percentage:.1f}%)")
        
        # 関連度分布
        st.write("**📈 関連度分布:**")
        high_rel = len([r for r in results if (1-r['distance']) > 0.8])
        med_rel = len([r for r in results if 0.6 < (1-r['distance']) <= 0.8])
        low_rel = len([r for r in results if (1-r['distance']) <= 0.6])
        
        st.write(f"- 高関連度(0.8+): {high_rel}件")
        st.write(f"- 中関連度(0.6-0.8): {med_rel}件") 
        st.write(f"- 低関連度(0.6-): {low_rel}件")
        
        # 上位参照文書（詳細版）
        st.write("**📄 上位参照文書（詳細版）:**")
        for i, result in enumerate(results[:15]):  # 上位15件
            title = result['metadata'].get('title', '無題')
            source = result['metadata'].get('source', '不明')
            similarity = 1 - result['distance']
            category = result.get('category', '一般')
            
            with st.expander(f"{i+1}. {title} ({source}) - 類似度: {similarity:.3f}"):
                col_a, col_b = st.columns(2)
                with col_a:
                    st.write(f"**カテゴリ**: {category}")
                    st.write(f"**類似度**: {similarity:.3f}")
                with col_b:
                    st.write(f"**ソース**: {source}")
                    st.write(f"**文字数**: {len(result['content'])}文字")
                
                # 内容プレビュー
                content_preview = result['content'][:500] + "..." if len(result['content']) > 500 else result['content']
                st.text_area(f"内容プレビュー", content_preview, height=100, key=f"preview_{i}")

if __name__ == "__main__":
    main()
