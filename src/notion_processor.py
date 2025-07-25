"""
Notion データ処理モジュール - 最適化版（実用性と可用性のバランス）
"""

import streamlit as st
from typing import List, Dict, Optional
from notion_client import Client
import gc
import time

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
        """最適化版ページ取得（150件上限・軽量処理）"""
        if not self.client:
            print("❌ Notionクライアントが初期化されていません")
            return []
        
        try:
            print("🔍 Notion最適化処理を開始...")
            
            all_documents = []
            
            # === 最適化設定 ===
            MAX_PAGES = 120           # ページ上限
            MAX_DATABASES = 30        # データベース上限
            CONTENT_LIMIT = 2000      # 1文書あたり文字制限
            BLOCK_LIMIT = 15          # ブロック取得制限
            
            # Phase 1: 最適化ページ取得
            print("📄 最適化ページ取得を開始...")
            pages = self.get_pages_optimized(MAX_PAGES, CONTENT_LIMIT, BLOCK_LIMIT)
            all_documents.extend(pages)
            
            # メモリクリーンアップ
            gc.collect()
            
            # Phase 2: 最適化データベース取得
            print("🗂️ 最適化データベース取得を開始...")
            databases = self.get_databases_optimized(MAX_DATABASES, CONTENT_LIMIT)
            all_documents.extend(databases)
            
            print(f"🎉 Notion最適化処理完了: {len(all_documents)} 件のドキュメント")
            
            # 結果サマリー表示
            self.print_optimized_summary(all_documents)
            
            return all_documents
            
        except Exception as e:
            print(f"❌ Notion最適化処理エラー: {e}")
            return []
    
    def get_pages_optimized(self, max_pages: int, content_limit: int, block_limit: int) -> List[Dict]:
        """最適化ページ取得"""
        pages = []
        
        try:
            # 最新ページ優先で効率取得
            results = self.client.search(
                **{
                    "page_size": min(max_pages, 100),
                    "sort": {
                        "direction": "descending",
                        "timestamp": "last_edited_time"
                    },
                    "filter": {
                        "property": "object",
                        "value": "page"
                    }
                }
            )
            
            processed_count = 0
            
            for page in results.get('results', []):
                if processed_count >= max_pages:
                    break
                
                try:
                    # 軽量コンテンツ抽出
                    content = self.extract_page_content_lightweight(
                        page['id'], 
                        content_limit, 
                        block_limit
                    )
                    
                    if content and len(content.strip()) > 20:
                        document = {
                            'id': f"notion_page_{page['id']}",
                            'title': self.get_page_title_safe(page),
                            'content': content[:content_limit],
                            'source': 'notion',
                            'type': 'page',
                            'url': page.get('url', ''),
                            'last_edited': page.get('last_edited_time', ''),
                            'parent_type': self.get_parent_type_safe(page)
                        }
                        pages.append(document)
                        processed_count += 1
                        
                        # 進捗表示（10件ごと）
                        if processed_count % 10 == 0:
                            print(f"📄 ページ処理進捗: {processed_count}/{max_pages}件")
                
                except Exception as e:
                    print(f"⚠️ ページ処理スキップ: {e}")
                    continue
            
            print(f"✅ ページ取得完了: {len(pages)}件")
            return pages
            
        except Exception as e:
            print(f"❌ ページ取得エラー: {e}")
            return []
    
    def get_databases_optimized(self, max_databases: int, content_limit: int) -> List[Dict]:
        """最適化データベース取得"""
        databases = []
        
        try:
            # データベース検索
            results = self.client.search(
                **{
                    "filter": {
                        "property": "object",
                        "value": "database"
                    },
                    "page_size": min(max_databases, 50)
                }
            )
            
            processed_count = 0
            
            for db in results.get('results', []):
                if processed_count >= max_databases:
                    break
                
                try:
                    # 軽量データベース内容抽出
                    content = self.extract_database_content_lightweight(
                        db['id'], 
                        content_limit
                    )
                    
                    if content and len(content.strip()) > 10:
                        document = {
                            'id': f"notion_db_{db['id']}",
                            'title': self.get_database_title_safe(db),
                            'content': content[:content_limit],
                            'source': 'notion',
                            'type': 'database',
                            'url': db.get('url', ''),
                            'last_edited': db.get('last_edited_time', ''),
                            'properties_count': len(db.get('properties', {}))
                        }
                        databases.append(document)
                        processed_count += 1
                
                except Exception as e:
                    print(f"⚠️ データベース処理スキップ: {e}")
                    continue
            
            print(f"✅ データベース取得完了: {len(databases)}件")
            return databases
            
        except Exception as e:
            print(f"❌ データベース取得エラー: {e}")
            return []
    
    def extract_page_content_lightweight(self, page_id: str, content_limit: int, block_limit: int) -> str:
        """軽量ページコンテンツ抽出"""
        try:
            # ページ詳細取得
            page_detail = self.client.pages.retrieve(page_id)
            
            # 制限されたブロック取得
            blocks_response = self.client.blocks.children.list(
                block_id=page_id,
                page_size=block_limit  # ブロック数制限
            )
            blocks = blocks_response.get('results', [])
            
            content_parts = []
            total_chars = 0
            
            # タイトル追加
            title = self.get_page_title_safe(page_detail)
            if title:
                content_parts.append(f"タイトル: {title}")
                total_chars += len(title) + 10
            
            # ブロック内容抽出（軽量版）
            for block in blocks:
                if total_chars >= content_limit:
                    break
                
                block_text = self.extract_block_text_simple(block)
                if block_text and len(block_text.strip()) > 0:
                    content_parts.append(block_text)
                    total_chars += len(block_text)
            
            result = '\n\n'.join(content_parts)
            return result[:content_limit]
            
        except Exception as e:
            print(f"❌ ページコンテンツ抽出エラー: {e}")
            return f"ページ内容取得エラー: {str(e)[:200]}"
    
    def extract_database_content_lightweight(self, db_id: str, content_limit: int) -> str:
        """軽量データベースコンテンツ抽出"""
        try:
            # データベース詳細取得
            database = self.client.databases.retrieve(db_id)
            
            # データベース内のページ取得（制限）
            pages_response = self.client.databases.query(
                database_id=db_id,
                page_size=10  # ページ数制限
            )
            pages = pages_response.get('results', [])
            
            content_parts = []
            
            # データベースタイトル
            db_title = self.get_database_title_safe(database)
            if db_title:
                content_parts.append(f"データベース: {db_title}")
            
            # プロパティ情報（簡略版）
            properties = database.get('properties', {})
            if properties:
                prop_names = list(properties.keys())[:5]  # 最初の5個のみ
                content_parts.append(f"プロパティ: {', '.join(prop_names)}")
            
            # ページタイトル（簡略版）
            for page in pages[:5]:  # 最大5ページ
                try:
                    page_title = self.get_page_title_safe(page)
                    if page_title and len(page_title.strip()) > 0:
                        content_parts.append(f"- {page_title}")
                except:
                    continue
            
            result = '\n'.join(content_parts)
            return result[:content_limit]
            
        except Exception as e:
            print(f"❌ データベースコンテンツ抽出エラー: {e}")
            return f"データベース内容取得エラー: {str(e)[:200]}"
    
    def extract_block_text_simple(self, block: Dict) -> str:
        """簡易ブロックテキスト抽出"""
        try:
            block_type = block.get('type', '')
            block_data = block.get(block_type, {})
            
            # 主要なテキスト系ブロックのみ処理
            text_types = ['paragraph', 'heading_1', 'heading_2', 'heading_3', 'bulleted_list_item']
            
            if block_type in text_types:
                rich_text = block_data.get('rich_text', [])
                if rich_text:
                    text_parts = []
                    for text_obj in rich_text:
                        if text_obj.get('type') == 'text':
                            content = text_obj.get('text', {}).get('content', '')
                            if content:
                                text_parts.append(content)
                    
                    if text_parts:
                        return ''.join(text_parts).strip()
            
            return ""
            
        except Exception:
            return ""
    
    def get_page_title_safe(self, page: Dict) -> str:
        """安全なページタイトル取得"""
        try:
            properties = page.get('properties', {})
            
            # タイトルプロパティを探す
            for prop_name, prop_data in properties.items():
                if prop_data.get('type') == 'title':
                    title_array = prop_data.get('title', [])
                    if title_array:
                        return ''.join([t.get('text', {}).get('content', '') for t in title_array])[:100]
            
            # フォールバック
            return f"ページ_{page.get('id', 'unknown')[:8]}"
            
        except Exception:
            return f"タイトル不明_{page.get('id', 'unknown')[:8]}"
    
    def get_database_title_safe(self, database: Dict) -> str:
        """安全なデータベースタイトル取得"""
        try:
            title_array = database.get('title', [])
            if title_array:
                return ''.join([t.get('text', {}).get('content', '') for t in title_array])[:100]
            
            return f"DB_{database.get('id', 'unknown')[:8]}"
            
        except Exception:
            return f"DB不明_{database.get('id', 'unknown')[:8]}"
    
    def get_parent_type_safe(self, page: Dict) -> str:
        """安全な親タイプ取得"""
        try:
            parent = page.get('parent', {})
            return parent.get('type', 'unknown')
        except:
            return 'unknown'
    
    def print_optimized_summary(self, documents: List[Dict]):
        """最適化結果サマリー表示"""
        print("\n📊 === Notion最適化取得サマリー ===")
        
        # タイプ別集計
        type_count = {}
        for doc in documents:
            doc_type = doc.get('type', '不明')
            type_count[doc_type] = type_count.get(doc_type, 0) + 1
        
        print("📄 タイプ別:")
        for doc_type, count in type_count.items():
            print(f"  - {doc_type}: {count}件")
        
        # 文字数統計
        total_chars = sum(len(doc.get('content', '')) for doc in documents)
        avg_chars = total_chars / len(documents) if documents else 0
        
        print(f"📝 総文字数: {total_chars:,}文字")
        print(f"📝 平均文字数: {avg_chars:.0f}文字")
        print(f"📝 総計: {len(documents)}件")
        print("=" * 40)
