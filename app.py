import streamlit as st
import sys
sys.path.append('src')

from vector_db_processor import VectorDBProcessor
from ai_assistant_final import AIAssistant

def main():
    st.title("🚀 企業RAGシステム - GPT-4o大容量対応版")
    st.caption("128,000トークン対応・最大50件文書・深層分析機能搭載")
    
    # 初期化
    if 'vector_db' not in st.session_state:
        st.session_state.vector_db = VectorDBProcessor()
        st.session_state.ai_assistant = AIAssistant()
    
    # サイドバーでオプション設定
    st.sidebar.header("⚙️ 大容量処理設定")
    
    # 分析タイプ選択
    analysis_type = st.sidebar.selectbox(
        "分析タイプを選択:",
        ["summary", "insights", "recommendations"],
        format_func=lambda x: {
            "summary": "📋 包括的要約（詳細版）", 
            "insights": "💡 深層洞察（多角的分析）", 
            "recommendations": "🚀 戦略的推奨（実行計画付き）"
        }[x]
    )
    
    # 検索結果数選択（大容量対応）
    n_results = st.sidebar.selectbox(
        "検索結果数:",
        [10, 20, 30, 40, 50],
        index=2,  # デフォルトを30に設定
        help="GPT-4oなら最大50件まで処理可能"
    )
    
    # 処理モード選択
    processing_mode = st.sidebar.radio(
        "処理モード:",
        ["standard", "intensive"],
        index=0,
        format_func=lambda x: {
            "standard": "⚡ 標準処理（高速）",
            "intensive": "🔍 集約処理（詳細）"
        }[x],
        help="集約処理は時間がかかりますが、より詳細な分析が可能です"
    )
    
    # データベース状態表示
    db_info = st.session_state.vector_db.get_collection_info()
    st.sidebar.success(f"📊 データベース: {db_info['document_count']}件")
    
    # GPT-4o仕様表示
    st.sidebar.info("""
    🚀 **GPT-4o仕様**
    - トークン制限: 128,000
    - 処理文書数: 最大50件
    - 1文書: 最大3,000文字
    - 総処理量: 最大50,000文字
    - 詳細分析: 深層洞察対応
    """)
    
    # 処理能力の警告
    if n_results >= 40:
        st.sidebar.warning("⚠️ 40件以上は処理時間が長くなります（1-2分程度）")
    
    # メイン検索インターフェース
    st.markdown("### 🔍 質問入力")
    query = st.text_area(
        "詳細な質問を入力してください:", 
        placeholder="例: ガイドの管理に関する現状、課題、改善提案を包括的に分析してください",
        height=100
    )
    
    # 分析実行ボタン
    col1, col2 = st.columns([3, 1])
    with col1:
        analyze_button = st.button(
            f"🚀 {analysis_type.upper()}分析実行（{n_results}件処理）", 
            type="primary",
            use_container_width=True
        )
    with col2:
        if st.button("🔄", help="入力をクリア"):
            st.rerun()
    
    if analyze_button:
        if query:
            # 処理開始通知
            processing_time_estimate = n_results * 2  # 1件あたり約2秒の見積もり
            st.info(f"⏱️ 推定処理時間: {processing_time_estimate}秒（{n_results}件の文書を大容量分析中...）")
            
            with st.spinner(f"GPT-4oで{n_results}件の文書を深層分析中...しばらくお待ちください"):
                # 検索実行
                search_results = st.session_state.vector_db.search(query, n_results)
                
                if search_results:
                    # AI分析実行
                    analysis_result = st.session_state.ai_assistant.analyze(
                        search_results, query, analysis_type
                    )
                    
                    # 成功通知
                    st.success(f"✅ {len(search_results)}件の文書から{analysis_type}分析完了")
                    
                    # 処理統計表示
                    total_chars = sum(len(result.get('content', '')) for result in search_results)
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("処理文書数", f"{len(search_results)}件")
                    with col2:
                        st.metric("総文字数", f"{total_chars:,}文字")
                    with col3:
                        st.metric("推定トークン", f"{total_chars//3:,}")
                    with col4:
                        st.metric("GPT-4o使用率", f"{min(100, (total_chars//3)/128000*100):.1f}%")
                    
                    # 分析結果表示
                    st.markdown("## 🎯 GPT-4o深層分析結果")
                    st.markdown(analysis_result)
                    
                    # 詳細検索結果（展開可能）
                    with st.expander(f"📚 参照文書詳細（{len(search_results)}件）", expanded=False):
                        # 文書統計
                        st.markdown("### 📊 文書統計")
                        avg_similarity = sum(1 - result['distance'] for result in search_results) / len(search_results)
                        st.write(f"平均類似度: {avg_similarity:.3f}")
                        
                        # 各文書の詳細  
                        for i, result in enumerate(search_results):
                            st.markdown(f"### 📄 文書 {i+1}")
                            
                            col1, col2 = st.columns([2, 1])
                            with col1:
                                st.markdown(f"**タイトル:** {result['metadata'].get('title', '無題')}")
                                st.markdown(f"**出典:** {result['metadata'].get('source', '不明')}")
                            with col2:
                                st.metric("類似度", f"{1 - result['distance']:.3f}")
                                st.metric("文字数", f"{len(result['content'])}文字")
                            
                            with st.expander(f"文書{i+1}の内容を表示"):
                                content = result['content']
                                if len(content) > 2000:
                                    st.text(content[:2000] + f"\n\n... (残り{len(content)-2000}文字)")
                                    if st.button(f"文書{i+1}の全文を表示", key=f"show_full_{i}"):
                                        st.text(content)
                                else:
                                    st.text(content)
                else:
                    st.error("❌ 関連する文書が見つかりませんでした。検索キーワードを変更してお試しください。")
        else:
            st.warning("⚠️ 質問を入力してください。")
    
    # フッター情報
    st.markdown("---")
    st.markdown("### 💡 使用のヒント")
    st.markdown("""
    - **包括的要約**: 全体像と詳細を把握したい場合
    - **深層洞察**: 隠れた課題や関連性を発見したい場合  
    - **戦略的推奨**: 具体的な改善策と実行計画が欲しい場合
    - **50件処理**: 最大限の情報量で分析したい場合
    """)

if __name__ == "__main__":
    main()
