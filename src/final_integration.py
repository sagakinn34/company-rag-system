import sys
import os
import streamlit as st
import gc
import time

# 絶対パスでsrcディレクトリを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
src_path = os.path.join(current_dir, '..', 'src') if 'src' not in current_dir else current_dir
sys.path.insert(0, src_path)

def run_data_integration():
    """最適化版データ統合（既存関数の改良）"""
    
    # 統合開始表示
    st.info("⚖️ 最適化データ統合を開始...")
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # パフォーマンス監視
    start_time = time.time()
    
    try:
        documents = []
        
        # === 最適化設定 ===
        NOTION_OPTIMIZED = 150    # 300 → 150 (50%削減)
        GDRIVE_OPTIMIZED = 100    # 200 → 100 (50%削減)
        CONTENT_MAX_CHARS = 2000  # コンテンツ文字数制限
        
        # 1. Notion最適化処理
        status_text.text("📝 Notion最適化取得中...")
        progress_bar.progress(20)
        
        try:
            notion_token = st.secrets.get("NOTION_TOKEN")
            if notion_token:
                st.info("📝 NOTION_TOKEN: ✅ 設定済み")
                
                from notion_processor import NotionProcessor
                st.success("📝 NotionProcessor インポート成功")
                
                notion = NotionProcessor()
                st.success("📝 NotionProcessor インスタンス作成成功")
                
                # 最適化取得実行
                notion_docs = get_notion_optimized_data(notion, NOTION_OPTIMIZED, CONTENT_MAX_CHARS)
                st.info(f"📝 Notion最適化取得結果: {len(notion_docs) if notion_docs else 0}件")
                
                if notion_docs:
                    documents.extend(notion_docs)
                    st.success(f"✅ Notion最適化取得成功: {len(notion_docs)}件")
                else:
                    st.warning("⚠️ Notionデータが空です")
            else:
                st.error("❌ NOTION_TOKENが設定されていません")
                
        except Exception as e:
            st.error(f"❌ Notion取得エラー: {e}")
        
        # メモリクリーンアップ
        gc.collect()
        
        # 2. Google Drive最適化処理
        status_text.text("📂 Google Drive最適化取得中...")
        progress_bar.progress(50)
        
        try:
            gdrive_creds = st.secrets.get("GOOGLE_DRIVE_CREDENTIALS")
            
            if gdrive_creds:
                st.success("📂 GOOGLE_DRIVE_CREDENTIALS: ✅ 設定済み")
                
                from gdrive_processor import GoogleDriveProcessor
                st.success("📂 GoogleDriveProcessor インポート成功")
                
                gdrive = GoogleDriveProcessor()
                st.success("📂 GoogleDriveProcessor インスタンス作成成功")
                
                if gdrive.service:
                    st.success("✅ Google Drive APIサービス初期化成功")
                    
                    # 最適化取得実行
                    gdrive_docs = get_gdrive_optimized_data(gdrive, GDRIVE_OPTIMIZED, CONTENT_MAX_CHARS)
                    st.info(f"📂 Google Drive最適化取得結果: {len(gdrive_docs) if gdrive_docs else 0}件")
                    
                    if gdrive_docs:
                        documents.extend(gdrive_docs)
                        st.success(f"✅ Google Drive最適化取得成功: {len(gdrive_docs)}件")
                    else:
                        st.warning("⚠️ Google Driveデータが空です")
                else:
                    st.error("❌ Google Drive APIサービスの初期化に失敗")
            else:
                st.error("❌ GOOGLE_DRIVE_CREDENTIALSが設定されていません")
                
        except Exception as e:
            st.error(f"❌ Google Drive取得エラー: {e}")
        
        # メモリクリーンアップ
        gc.collect()
        
        # 3. Discord処理（スキップ）
        status_text.text("💬 Discord処理をスキップ中...")
        progress_bar.progress(70)
        st.info("💬 Discord統合: 一旦スキップ（今後実装予定）")
        
        # 4. 最適化ベクトルDB統合
        status_text.text("🔄 最適化ベクトル統合中...")
        progress_bar.progress(90)
        
        st.info(f"🔄 最適化統合処理: 合計{len(documents)}件のデータを処理中...")
        
        if documents:
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            
            if vector_db.collection:
                # バッチ処理で負荷軽減
                batch_size = 10
                total_batches = (len(documents) + batch_size - 1) // batch_size
                
                st.info(f"🔄 {len(documents)}件を{batch_size}件ずつ{total_batches}バッチで処理中...")
                
                for i in range(0, len(documents), batch_size):
                    batch = documents[i:i + batch_size]
                    
                    try:
                        vector_db.add_documents(batch)
                        
                        # 進捗表示
                        batch_num = i // batch_size + 1
                        st.info(f"📊 バッチ{batch_num}/{total_batches}完了 ({len(batch)}件処理)")
                        
                        # 3バッチごとにメモリクリーンアップ
                        if batch_num % 3 == 0:
                            gc.collect()
                            time.sleep(0.1)  # 負荷軽減
                        
                    except Exception as batch_error:
                        st.warning(f"⚠️ バッチ{batch_num}処理エラー: {batch_error}")
                        continue
                
                # 最終確認
                final_count = vector_db.collection.count()
                elapsed_time = time.time() - start_time
                
                progress_bar.progress(100)
                status_text.text("✅ 最適化統合完了!")
                
                st.success(f"🎉 最適化データ統合完了!")
                st.success(f"📊 総DB件数: {final_count}件")
                st.success(f"⏰ 処理時間: {elapsed_time:.1f}秒")
                
                # 最適化結果詳細
                display_optimization_results(documents, elapsed_time)
                
                return True
            else:
                st.error("❌ ベクトルDBが初期化されていません")
                return False
        else:
            progress_bar.progress(100)
            status_text.text("❌ 統合データなし")
            
            st.warning("⚠️ 統合するデータが見つかりませんでした")
            return False
            
    except Exception as e:
        elapsed_time = time.time() - start_time
        st.error(f"❌ 最適化統合エラー: {e}")
        
        # エラー分析
        with st.expander("🔍 エラー分析"):
            st.write(f"**実行時間**: {elapsed_time:.1f}秒")
            st.write(f"**処理済み件数**: {len(documents) if 'documents' in locals() else 0}件")
            
            if elapsed_time > 300:  # 5分超過
                st.warning("⏰ タイムアウトの可能性があります")
        
        return False

def get_notion_optimized_data(notion, limit: int, max_chars: int):
    """Notion最適化データ取得（既存処理の改良）"""
    try:
        documents = []
        processed_count = 0
        
        # 最新ページ優先取得
        results = notion.client.search(
            **{
                "page_size": min(limit, 100),
                "sort": {
                    "direction": "descending",
                    "timestamp": "last_edited_time"
                }
            }
        )
        
        for item in results.get('results', []):
            if processed_count >= limit:
                break
                
            try:
                # ページとデータベースを区別
                if item.get('object') == 'page':
                    content = extract_page_content_optimized(notion, item['id'], max_chars)
                elif item.get('object') == 'database':
                    content = extract_database_content_optimized(notion, item['id'], max_chars)
                else:
                    continue
                
                if content and len(content.strip()) > 20:  # 最小文字数チェック
                    document = {
                        'id': f"notion_{item['id']}",
                        'title': get_title_safe(item),
                        'content': content[:max_chars],  # 文字数制限
                        'source': 'notion',
                        'type': item.get('object', 'unknown'),
                        'url': item.get('url', ''),
                        'last_edited': item.get('last_edited_time', '')
                    }
                    documents.append(document)
                    processed_count += 1
                    
                    if processed_count % 10 == 0:  # 10件ごとに進捗表示
                        st.info(f"📄 Notion処理中: {processed_count}/{limit}件")
                
            except Exception as e:
                print(f"⚠️ Notionアイテム処理スキップ: {e}")
                continue
        
        return documents
        
    except Exception as e:
        st.error(f"❌ Notion最適化取得エラー: {e}")
        return []

def get_gdrive_optimized_data(gdrive, limit: int, max_chars: int):
    """Google Drive最適化データ取得（既存処理の改良）"""
    try:
        documents = []
        
        # 効率的な取得戦略（ファイルタイプ別）
        strategies = [
            {
                'name': 'Google Docs',
                'query': "trashed=false and mimeType='application/vnd.google-apps.document'",
                'limit': int(limit * 0.6)  # 60%
            },
            {
                'name': 'PDF',
                'query': "trashed=false and mimeType='application/pdf'",
                'limit': int(limit * 0.25)  # 25%
            },
            {
                'name': 'その他',
                'query': "trashed=false and (mimeType contains 'spreadsheet' or mimeType contains 'presentation')",
                'limit': int(limit * 0.15)  # 15%
            }
        ]
        
        for strategy in strategies:
            try:
                st.info(f"📂 {strategy['name']}取得中... (上限: {strategy['limit']}件)")
                
                results = gdrive.service.files().list(
                    q=strategy['query'],
                    pageSize=strategy['limit'],
                    orderBy='modifiedTime desc',
                    fields="files(id, name, mimeType, size, createdTime, modifiedTime)"
                ).execute()
                
                files = results.get('files', [])
                
                for file_info in files:
                    if len(documents) >= limit:
                        break
                    
                    try:
                        # 軽量テキスト抽出
                        text_content = extract_text_optimized(gdrive, file_info, max_chars)
                        
                        if text_content and len(text_content.strip()) > 10:
                            document = {
                                'id': f"gdrive_{file_info['id']}",
                                'title': file_info['name'],
                                'content': text_content[:max_chars],  # 文字数制限
                                'source': 'google_drive',
                                'type': 'file',
                                'mime_type': file_info['mimeType'],
                                'url': f"https://drive.google.com/file/d/{file_info['id']}/view"
                            }
                            documents.append(document)
                            
                    except Exception as file_error:
                        print(f"⚠️ ファイル処理スキップ: {file_error}")
                        continue
                
                st.success(f"✅ {strategy['name']}: {len([d for d in documents if strategy['name'].lower() in d.get('mime_type', '').lower()])}件取得")
                
            except Exception as strategy_error:
                st.warning(f"⚠️ {strategy['name']}取得エラー: {strategy_error}")
                continue
        
        return documents
        
    except Exception as e:
        st.error(f"❌ Google Drive最適化取得エラー: {e}")
        return []

# ユーティリティ関数
def extract_page_content_optimized(notion, page_id: str, max_chars: int) -> str:
    """最適化ページコンテンツ抽出"""
    try:
        # 簡易版：ブロック取得を制限
        blocks_response = notion.client.blocks.children.list(
            block_id=page_id,
            page_size=20  # ブロック数制限
        )
        blocks = blocks_response.get('results', [])
        
        content_parts = []
        total_chars = 0
        
        for block in blocks:
            if total_chars >= max_chars:
                break
                
            block_text = extract_block_text_simple(block)
            if block_text and len(block_text.strip()) > 0:
                content_parts.append(block_text)
                total_chars += len(block_text)
        
        return '\n\n'.join(content_parts)[:max_chars]
        
    except Exception as e:
        return f"ページ内容取得エラー: {str(e)}"

def extract_text_optimized(gdrive, file_info: dict, max_chars: int) -> str:
    """最適化テキスト抽出"""
    try:
        mime_type = file_info['mimeType']
        file_id = file_info['id']
        
        if mime_type == 'application/vnd.google-apps.document':
            request = gdrive.service.files().export_media(fileId=file_id, mimeType='text/plain')
            content = request.execute().decode('utf-8', errors='ignore')
            return content[:max_chars]
        else:
            # その他はメタデータのみ
            return f"ファイル: {file_info['name']}\nタイプ: {mime_type}"
            
    except Exception as e:
        return f"テキスト抽出エラー: {str(e)}"

def display_optimization_results(documents, elapsed_time):
    """最適化結果表示"""
    with st.expander("📊 最適化結果詳細"):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("総文書数", len(documents))
            st.metric("処理時間", f"{elapsed_time:.1f}秒")
        
        with col2:
            sources = {}
            for doc in documents:
                source = doc.get('source', '不明')
                sources[source] = sources.get(source, 0) + 1
            
            st.write("**ソース別:**")
            for source, count in sources.items():
                st.write(f"- {source}: {count}件")
        
        with col3:
            total_chars = sum(len(doc.get('content', '')) for doc in documents)
            avg_chars = total_chars / len(documents) if documents else 0
            
            st.metric("総文字数", f"{total_chars:,}")
            st.metric("平均文字数", f"{avg_chars:.0f}")
        
        # パフォーマンス評価
        if elapsed_time < 180:  # 3分以内
            st.success("🚀 高速処理完了")
        elif elapsed_time < 300:  # 5分以内
            st.info("⚡ 標準処理完了")
        else:
            st.warning("🐌 処理時間長め")

# 既存関数（下位互換）
def safe_integration():
    """下位互換性のための関数"""
    return run_data_integration()

if __name__ == "__main__":
    safe_integration()
