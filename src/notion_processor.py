"""
Notion データ処理モジュール - 小規模企業向け拡張版（300件上限）
"""

import streamlit as st
from typing import List, Dict, Optional
from notion_client import Client

class NotionProcessor:
    def __init__(self):
        """Notion プロセッサーを初期化"""
        self.client = None
        self.setup_client()
    
    def setup_client(self):
        """Notion クライアントを設定"""
        try:
            notion_token = st.secrets.get("NOTION_TOKEN")
            if not notion_token:
                print("❌ NOTION_TOKENが設定されていません")
                return
            
            self.client = Client(auth=notion_token)
            print("✅ Notionクライアント初期化完了")
            
        except Exception as e:
            print(f"❌ Notion初期化エラー: {e}")
            self.client = None
    
    def get_all_pages(self) -> List[Dict]:
        """小規模企業向け拡張取得（300件上限・バランス重視）"""
        if not self.client:
            print("❌ Notionクライアントが初期化されていません")
            return []
        
        try:
            print("🔍 Notion コンテンツ処理を開始（小規模企業拡張版）...")
            
            all_documents = []
            
            # 設定
            max_pages = 300  # 小規模企業向け上限
            max_databases = 50  # データベース上限
            
            # Phase 1: ページ取得（ページネーション対応）
            print("📄 ページ取得を開始...")
            pages = self.get_pages_with_balance(max_pages)
            all_documents.extend(pages)
            
            # Phase 2: データベース取得
            print("🗂️ データベース取得を開始...")
            databases = self.get_databases_with_balance(max_databases)
            all_documents.extend(databases)
            
            print(f"🎉 Notion 処理完了: {len(all_documents)} 件のドキュメント")
            
            # 結果サマリー表示
            self.print_summary(all_documents)
            
            return all_documents
            
        except Exception as e:
            print(f"❌ Notion 処理エラー: {e}")
            return []
    
    def get_pages_with_balance(self, max_pages: int) -> List[Dict]:
        """バランス重視のページ取得"""
        pages = []
        
        try:
            # 取得戦略：時系列バランス
            recent_limit = int(max_pages * 0.6)  # 60%は最近
            old_limit = max_pages - recent_limit  # 40%は過去
            
            print(f"📅 最近のページ取得中... (上限: {recent_limit}件)")
            recent_pages = self.get_pages_by_timeframe('recent', recent_limit)
            pages.extend(recent_pages)
            print(f"✅ 最近のページ: {len(recent_pages)}件取得")
            
            print(f"📅 過去のページ取得中... (上限: {old_limit}件)")
            old_pages = self.get_pages_by_timeframe('old', old_limit, exclude_recent=True)
            pages.extend(old_pages)
            print(f"✅ 過去のページ: {len(old_pages)}件取得")
            
        except Exception as e:
            print(f"❌ ページ取得エラー: {e}")
        
        return pages
    
    def get_pages_by_timeframe(self, timeframe: str, limit: int, exclude_recent: bool = False) -> List[Dict]:
        """時系列別ページ取得"""
        pages = []
        start_cursor = None
        processed_count = 0
        
        try:
            while processed_count < limit:
                # クエリパラメータ
                query_params = {
                    "page_size": min(100, limit - processed_count),  # 残り件数を考慮
                    "sort": {
                        "direction": "descending",
                        "timestamp": "last_edited_time"
                    }
                }
                
                if start_cursor:
                    query_params["start_cursor"] = start_cursor
                
                # Notion API呼び出し
                results = self.client.search(**query_params)
                current_pages = results.get('results', [])
                
                if not current_pages:
                    break
                
                # 時系列フィルタリング
                filtered_pages = []
                for page in current_pages:
                    if processed_count >= limit:
                        break
                    
                    # 時系列判定
                    if self.should_include_page(page, timeframe, exclude_recent):
                        page_doc = self.process_single_page(page)
                        if page_doc:
                            filtered_pages.append(page_doc)
                            processed_count += 1
                
                pages.extend(filtered_pages)
                
                # 次ページ確認
                if not results.get('has_more', False):
                    break
                    
                start_cursor = results.get('next_cursor')
            
        except Exception as e:
            print(f"❌ 時系列ページ取得エラー ({timeframe}): {e}")
        
        return pages
    
    def should_include_page(self, page: Dict, timeframe: str, exclude_recent: bool) -> bool:
        """ページ包含判定"""
        try:
            from datetime import datetime, timedelta
            
            last_edited = page.get('last_edited_time')
            if not last_edited:
                return timeframe == 'old'  # 編集日時不明は過去として扱う
            
            # 日時解析
            edited_date = datetime.fromisoformat(last_edited.replace('Z', '+00:00'))
            now = datetime.now(edited_date.tzinfo)
            
            # 90日前を境界とする
            boundary_date = now - timedelta(days=90)
            
            is_recent = edited_date > boundary_date
            
            if timeframe == 'recent':
                return is_recent and not exclude_recent
            elif timeframe == 'old':
                return not is_recent or not exclude_recent
            
            return True
            
        except Exception as e:
            print(f"⚠️ 日時判定エラー: {e}")
            return True  # エラー時は含める
    
    def process_single_page(self, page: Dict) -> Optional[Dict]:
        """単一ページの処理"""
        try:
            page_id = page['id']
            
            # ページ内容を取得
            content = self.extract_page_content(page_id)
            
            if content and len(content.strip()) > 5:
                document = {
                    'id': f"notion_page_{page_id}",
                    'title': self.get_page_title(page),
                    'content': content[:4000],  # 4000文字に拡張
                    'source': 'notion',
                    'type': 'page',
                    'url': page.get('url', ''),
                    'last_edited': page.get('last_edited_time', ''),
                    'created': page.get('created_time', ''),
                    'parent_type': self.get_parent_type(page)
                }
                
                return document
            
        except Exception as e:
            print(f"❌ ページ処理エラー: {e}")
        
        return None
    
    def get_databases_with_balance(self, max_databases: int) -> List[Dict]:
        """バランス重視のデータベース取得"""
        databases = []
        
        try:
            print(f"🗂️ データベース検索中... (上限: {max_databases}件)")
            
            # データベース一覧取得
            start_cursor = None
            processed_count = 0
            
            while processed_count < max_databases:
                query_params = {
                    "filter": {
                        "property": "object",
                        "value": "database"
                    },
                    "page_size": min(100, max_databases - processed_count)
                }
                
                if start_cursor:
                    query_params["start_cursor"] = start_cursor
                
                results = self.client.search(**query_params)
                current_databases = results.get('results', [])
                
                if not current_databases:
                    break
                
                # データベース処理
                for db in current_databases:
                    if processed_count >= max_databases:
                        break
                    
                    try:
                        db_doc = self.process_single_database(db)
                        if db_doc:
                            databases.append(db_doc)
                            processed_count += 1
                            
                    except Exception as e:
                        print(f"⚠️ データベース処理スキップ: {e}")
                        continue
                
                # 次ページ確認
                if not results.get('has_more', False):
                    break
                    
                start_cursor = results.get('next_cursor')
            
            print(f"✅ データベース: {len(databases)}件処理完了")
            
        except Exception as e:
            print(f"❌ データベース取得エラー: {e}")
        
        return databases
    
    def process_single_database(self, database: Dict) -> Optional[Dict]:
        """単一データベースの処理"""
        try:
            db_id = database['id']
            
            # データベース内容を取得
            content = self.extract_database_content(db_id)
            
            if content and len(content.strip()) > 5:
                document = {
                    'id': f"notion_db_{db_id}",
                    'title': self.get_database_title(database),
                    'content': content[:5000],  # データベースは5000文字まで
                    'source': 'notion',
                    'type': 'database',
                    'url': database.get('url', ''),
                    'last_edited': database.get('last_edited_time', ''),
                    'created': database.get('created_time', ''),
                    'properties_count': len(database.get('properties', {}))
                }
                
                return document
            
        except Exception as e:
            print(f"❌ データベース処理エラー: {e}")
        
        return None
    
    def extract_page_content(self, page_id: str) -> str:
        """ページコンテンツ抽出（エラーハンドリング強化）"""
        try:
            # ページ詳細取得
            page_detail = self.client.pages.retrieve(page_id)
            
            # ブロック取得
            blocks_response = self.client.blocks.children.list(block_id=page_id)
            blocks = blocks_response.get('results', [])
            
            content_parts = []
            
            # タイトル追加
            title = self.get_page_title(page_detail)
            if title:
                content_parts.append(f"タイトル: {title}")
            
            # ブロック内容抽出
            for block in blocks:
                block_text = self.extract_block_text(block)
                if block_text:
                    content_parts.append(block_text)
            
            return '\n\n'.join(content_parts)
            
        except Exception as e:
            print(f"❌ ページコンテンツ抽出エラー: {e}")
            return f"ページ内容取得エラー: {str(e)}"
    
    def extract_database_content(self, db_id: str) -> str:
        """データベースコンテンツ抽出"""
        try:
            # データベース詳細取得
            database = self.client.databases.retrieve(db_id)
            
            # データベース内のページ取得（最大20件）
            pages_response = self.client.databases.query(
                database_id=db_id,
                page_size=20
            )
            pages = pages_response.get('results', [])
            
            content_parts = []
            
            # データベースタイトル
            db_title = self.get_database_title(database)
            if db_title:
                content_parts.append(f"データベース: {db_title}")
            
            # プロパティ情報
            properties = database.get('properties', {})
            if properties:
                prop_names = list(properties.keys())
                content_parts.append(f"プロパティ: {', '.join(prop_names)}")
            
            # ページ内容
            for page in pages[:10]:  # 最大10ページ
                try:
                    page_title = self.get_page_title(page)
                    if page_title:
                        content_parts.append(f"- {page_title}")
                except:
                    continue
            
            return '\n'.join(content_parts)
            
        except Exception as e:
            print(f"❌ データベースコンテンツ抽出エラー: {e}")
            return f"データベース内容取得エラー: {str(e)}"
    
    def extract_block_text(self, block: Dict) -> str:
        """ブロックからテキスト抽出"""
        try:
            block_type = block.get('type', '')
            block_data = block.get(block_type, {})
            
            # テキスト系ブロック
            if block_type in ['paragraph', 'heading_1', 'heading_2', 'heading_3', 'bulleted_list_item', 'numbered_list_item']:
                rich_text = block_data.get('rich_text', [])
                text_parts = []
                for text_obj in rich_text:
                    if text_obj.get('type') == 'text':
                        text_parts.append(text_obj.get('text', {}).get('content', ''))
                
                text = ''.join(text_parts).strip()
                if text:
                    prefix = {
                        'heading_1': '# ',
                        'heading_2': '## ',
                        'heading_3': '### ',
                        'bulleted_list_item': '• ',
                        'numbered_list_item': '1. '
                    }.get(block_type, '')
                    
                    return f"{prefix}{text}"
            
            # その他のブロック
            elif block_type == 'to_do':
                rich_text = block_data.get('rich_text', [])
                text = ''.join([t.get('text', {}).get('content', '') for t in rich_text])
                checked = block_data.get('checked', False)
                status = "☑" if checked else "☐"
                return f"{status} {text}"
            
            elif block_type == 'quote':
                rich_text = block_data.get('rich_text', [])
                text = ''.join([t.get('text', {}).get('content', '') for t in rich_text])
                return f"> {text}"
            
            return ""
            
        except Exception as e:
            print(f"⚠️ ブロックテキスト抽出エラー: {e}")
            return ""
    
    def get_page_title(self, page: Dict) -> str:
        """ページタイトル取得"""
        try:
            properties = page.get('properties', {})
            
            # タイトルプロパティを探す
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'title':
                    title_array = prop_data.get('title', [])
                    if title_array:
                        return ''.join([t.get('text', {}).get('content', '') for t in title_array])
            
            # フォールバック
            return page.get('id', '無題')[:8]
            
        except Exception as e:
            return f"タイトル取得エラー_{page.get('id', 'unknown')[:8]}"
    
    def get_database_title(self, database: Dict) -> str:
        """データベースタイトル取得"""
        try:
            title_array = database.get('title', [])
            if title_array:
                return ''.join([t.get('text', {}).get('content', '') for t in title_array])
            
            return database.get('id', '無題DB')[:8]
            
        except Exception as e:
            return f"DBタイトル取得エラー_{database.get('id', 'unknown')[:8]}"
    
    def get_parent_type(self, page: Dict) -> str:
        """親オブジェクトタイプ取得"""
        try:
            parent = page.get('parent', {})
            return parent.get('type', 'unknown')
        except:
            return 'unknown'
    
    def print_summary(self, documents: List[Dict]):
        """取得結果サマリー表示"""
        print("\n📊 === Notion 取得サマリー ===")
        
        # タイプ別集計
        type_count = {}
        parent_count = {}
        
        for doc in documents:
            doc_type = doc.get('type', '不明')
            parent_type = doc.get('parent_type', '不明')
            
            type_count[doc_type] = type_count.get(doc_type, 0) + 1
            parent_count[parent_type] = parent_count.get(parent_type, 0) + 1
        
        print("📄 タイプ別:")
        for doc_type, count in type_count.items():
            print(f"  - {doc_type}: {count}件")
        
        print("📁 親タイプ別:")
        for parent_type, count in parent_count.items():
            print(f"  - {parent_type}: {count}件")
        
        print(f"📝 総計: {len(documents)}件")
        print("=" * 40)

