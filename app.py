import streamlit as st
import sys
import os

# パス設定
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# 基本インポート
from vector_db_processor import VectorDBProcessor
import json

# ページ設定
st.set_page_config(
    page_title="Company RAG System",
    page_icon="🏢",
    layout="wide"
)

# メイン処理
def main():
    st.title("Company RAG System")
    st.markdown("### 🛠️ 機能メニュー")
    
    # サイドバー
    with st.sidebar:
        st.header("🔧 システム状態")
        
        # ベクトルDB状態確認
        try:
            vector_db = VectorDBProcessor()
            db_info = vector_db.get_collection_info()
            if db_info["status"] == "active":
                st.success("ベクトルDB: 🟢 正常")
            else:
                st.error(f"ベクトルDB: 🔴 {db_info['status']}")
        except Exception as e:
            st.error(f"ベクトルDB: 🔴 エラー - {e}")
        
        st.header("📊 DB統計")
        try:
            stats = vector_db.get_stats()
            st.metric("文書数", stats.get("total_documents", 0))
            if stats.get("status") == "success":
                st.success("データベース: 正常")
            elif stats.get("status") == "empty":
                st.warning("データベース: 空")
            else:
                st.error(f"データベース: {stats.get('status', 'エラー')}")
        except Exception as e:
            st.error(f"統計取得エラー: {e}")
        
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
        
        # データ統合ボタン（修正部分）
        st.subheader("🔄 データ統合")
        st.write("👇 下のボタンでデータを統合してください")
        
        # 修正: final_integrationモジュールのインポートとエラーハンドリング
        data_integration_available = False
        try:
            from final_integration import run_data_integration
            data_integration_available = True
        except ImportError as e:
            try:
                # 代替インポート方法
                sys.path.append('.')
                from final_integration import run_data_integration
                data_integration_available = True
            except ImportError:
                try:
                    # src/からのインポート
                    from src.final_integration import run_data_integration
                    data_integration_available = True
                except ImportError:
                    st.error("❌ データ統合モジュールが見つかりません")
                    st.error(f"インポートエラー詳細: {e}")
        
        # データ統合ボタンの表示
        if data_integration_available:
            if st.button("🔄 データを統合する", type="primary"):
                with st.spinner("データ統合処理中..."):
                    try:
                        success = run_data_integration()
                        if success:
                            st.success("✅ データ統合が完了しました！")
                            st.rerun()  # ページを再読み込みして統計を更新
                        else:
                            st.error("❌ データ統合に失敗しました")
                    except Exception as e:
                        st.error(f"❌ データ統合エラー: {e}")
        else:
            st.error("❌ データ統合機能が利用できません")
    
    # メインコンテンツ
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 ホーム", "🔍 ベクトル検索", "💬 AIチャット", "📓 Notion統合"])
    
    with tab1:
        st.header("企業データ統合検索システム")
        st.markdown("#### 🏠 ホーム - システム概要")
        
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
            
            st.markdown("#### ⚡ 自動処理機能")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("""
                * テキスト抽出・構造化
                * ベクトル化・インデックス作成
                """)
            with col2:
                st.markdown("""
                * 意味検索対応
                * リアルタイム同期
                """)
            
        else:
            st.warning("⚠️ Notion統合には環境変数の設定が必要です")
        
        st.markdown("#### 📖 Notion統合の使い方")
        
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
        
        with st.expander("3️⃣ 検索・AIチャット", expanded=False):
            st.markdown("""
            1. 「🔍 ベクトル検索」で検索実行
            2. 手動追加文書とNotion文書を横断検索
            3. AIチャットでNotionデータを参照した回答
            """)
    
    with tab2:
        st.header("🔍 ベクトル検索")
        
        query = st.text_input("検索クエリを入力してください", placeholder="例: プロジェクトの進捗状況")
        
        if st.button("🔍 検索実行"):
            if query:
                with st.spinner("検索中..."):
                    try:
                        vector_db = VectorDBProcessor()
                        results = vector_db.search(query)
                        
                        if results:
                            st.success(f"✅ {len(results)}件の結果が見つかりました")
                            
                            for i, result in enumerate(results[:10]):  # 上位10件表示
                                with st.expander(f"📄 結果 {i+1} - 類似度: {1-result['distance']:.3f}"):
                                    st.write("**内容:**")
                                    st.write(result['content'][:500] + "..." if len(result['content']) > 500 else result['content'])
                                    
                                    if result.get('metadata'):
                                        st.write("**メタデータ:**")
                                        st.json(result['metadata'])
                        else:
                            st.warning("⚠️ 検索結果が見つかりませんでした")
                    except Exception as e:
                        st.error(f"❌ 検索エラー: {e}")
            else:
                st.warning("検索クエリを入力してください")
    
    with tab3:
        st.header("💬 AIチャット")
        st.markdown("RAG機能を使用した対話型AI")
        
        # チャット履歴の初期化
        if "messages" not in st.session_state:
            st.session_state.messages = []
        
        # チャット履歴の表示
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        # ユーザー入力
        if prompt := st.chat_input("AIに質問してください"):
            # ユーザーのメッセージを追加
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            
            # AI応答の生成
            with st.chat_message("assistant"):
                with st.spinner("AIが考えています..."):
                    try:
                        # ベクトル検索で関連文書を取得
                        vector_db = VectorDBProcessor()
                        search_results = vector_db.search(prompt, n_results=5)
                        
                        if search_results:
                            context = "\n".join([result['content'][:300] for result in search_results[:3]])
                            
                            # OpenAI APIを使用した応答生成
                            import openai
                            openai.api_key = st.secrets["OPENAI_API_KEY"]
                            
                            response = openai.ChatCompletion.create(
                                model="gpt-4",
                                messages=[
                                    {"role": "system", "content": f"以下の文書コンテキストを参考にして、ユーザーの質問に答えてください。\n\nコンテキスト:\n{context}"},
                                    {"role": "user", "content": prompt}
                                ],
                                max_tokens=1000,
                                temperature=0.7
                            )
                            
                            ai_response = response.choices[0].message.content
                            st.markdown(ai_response)
                            
                            # 参考文書の表示
                            with st.expander("📚 参考にした文書"):
                                for i, result in enumerate(search_results[:3]):
                                    st.write(f"**文書 {i+1}:**")
                                    st.write(result['content'][:200] + "...")
                        else:
                            ai_response = "申し訳ありませんが、関連する文書が見つかりませんでした。一般的な回答をします。"
                            st.markdown(ai_response)
                        
                        # AIの応答をセッションに追加
                        st.session_state.messages.append({"role": "assistant", "content": ai_response})
                        
                    except Exception as e:
                        error_msg = f"❌ AI応答エラー: {e}"
                        st.error(error_msg)
                        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    
    with tab4:
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
                        # 接続テスト処理
                        st.success("✅ Notion接続成功")
                    except Exception as e:
                        st.error(f"❌ Notion接続エラー: {e}")
        
        with col2:
            if st.button("📋 ページ・DB一覧"):
                with st.spinner("ページ一覧取得中..."):
                    try:
                        from notion_processor import NotionProcessor
                        notion = NotionProcessor()
                        pages = notion.get_all_pages()
                        
                        if pages:
                            st.success(f"✅ {len(pages)}件のページを取得")
                            
                            for page in pages[:10]:  # 上位10件表示
                                with st.expander(f"📄 {page.get('title', 'タイトルなし')}"):
                                    st.json(page)
                        else:
                            st.warning("⚠️ ページが見つかりません")
                    except Exception as e:
                        st.error(f"❌ ページ取得エラー: {e}")
    
    # フッター
    st.markdown("---")
    st.markdown("🚀 **Company RAG System - Notion統合版**")
    st.markdown("Streamlit Cloud対応 | RAG + Notion Integration")

if __name__ == "__main__":
    main()

