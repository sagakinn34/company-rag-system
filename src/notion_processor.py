"""
Notion データ処理モジュール
Notion から各種ページとデータベースを取得し、テキストを抽出します
"""

import os
import json
import time
from typing import List, Dict, Optional
import requests

class NotionProcessor:
    def __init__(self, notion_token: str):
        """
        Notion プロセッサーを初期化
        
        Args:
            notion_token (str): Notion API トークン
        """
        self.notion_token = notion_token
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
    
    def search_pages(self, query: str = "", page_size: int = 100) -> List[Dict]:
        """
        Notion ページを検索
        
        Args:
            query (str): 検索クエリ
            page_size (int): 取得ページ数
            
        Returns:
            List[Dict]: ページ情報のリスト
        """
        try:
            url = f"{self.base_url}/search"
            payload = {
                "page_size": page_size,
                "filter": {
                    "property": "object",
                    "value": "page"
                }
            }
            
            if query:
                payload["query"] = query
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            pages = data.get("results", [])
            
            print(f"📄 {len(pages)} 件のページが見つかりました")
            return pages
            
        except Exception as e:
            print(f"❌ ページ検索エラー: {e}")
            return []
    
    def search_databases(self, query: str = "", page_size: int = 100) -> List[Dict]:
        """
        Notion データベースを検索
        
        Args:
            query (str): 検索クエリ
            page_size (int): 取得データベース数
            
        Returns:
            List[Dict]: データベース情報のリスト
        """
        try:
            url = f"{self.base_url}/search"
            payload = {
                "page_size": page_size,
                "filter": {
                    "property": "object",
                    "value": "database"
                }
            }
            
            if query:
                payload["query"] = query
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            data = response.json()
            databases = data.get("results", [])
            
            print(f"🗂️ {len(databases)} 件のデータベースが見つかりました")
            return databases
            
        except Exception as e:
            print(f"❌ データベース検索エラー: {e}")
            return []
    
    def get_page_content(self, page_id: str) -> str:
        """
        ページの内容を取得
        
        Args:
            page_id (str): ページID
            
        Returns:
            str: ページのテキスト内容
        """
        try:
            # ページの基本情報を取得
            page_url = f"{self.base_url}/pages/{page_id}"
            page_response = requests.get(page_url, headers=self.headers)
            page_response.raise_for_status()
            page_data = page_response.json()
            
            # ページのタイトルを取得
            title = ""
            if "properties" in page_data:
                for prop_key, prop_value in page_data["properties"].items():
                    if prop_value.get("type") == "title":
                        title_list = prop_value.get("title", [])
                        if title_list:
                            title = "".join([t.get("plain_text", "") for t in title_list])
                        break
            
            # ページの内容（ブロック）を取得
            blocks_url = f"{self.base_url}/blocks/{page_id}/children"
            blocks_response = requests.get(blocks_url, headers=self.headers)
            blocks_response.raise_for_status()
            blocks_data = blocks_response.json()
            
            # ブロックからテキストを抽出
            content = self.extract_text_from_blocks(blocks_data.get("results", []))
            
            # タイトルと内容を結合
            full_content = f"{title}\n\n{content}" if title else content
            
            return full_content.strip()
            
        except Exception as e:
            print(f"❌ ページ内容取得エラー: {e}")
            return ""
    
    def extract_text_from_blocks(self, blocks: List[Dict]) -> str:
        """
        ブロックリストからテキストを抽出
        
        Args:
            blocks (List[Dict]): ブロックのリスト
            
        Returns:
            str: 抽出されたテキスト
        """
        text = ""
        
        for block in blocks:
            block_type = block.get("type", "")
            block_data = block.get(block_type, {})
            
            # テキスト系ブロックの処理
            if block_type in ["paragraph", "heading_1", "heading_2", "heading_3", "bulleted_list_item", "numbered_list_item"]:
                rich_text = block_data.get("rich_text", [])
                block_text = "".join([t.get("plain_text", "") for t in rich_text])
                if block_text:
                    text += block_text + "\n"
            
            # コードブロックの処理
            elif block_type == "code":
                rich_text = block_data.get("rich_text", [])
                code_text = "".join([t.get("plain_text", "") for t in rich_text])
                if code_text:
                    text += f"```\n{code_text}\n```\n"
            
            # 引用ブロックの処理
            elif block_type == "quote":
                rich_text = block_data.get("rich_text", [])
                quote_text = "".join([t.get("plain_text", "") for t in rich_text])
                if quote_text:
                    text += f"> {quote_text}\n"
            
            # 区切り線
            elif block_type == "divider":
                text += "---\n"
            
            # 子ブロックがある場合は再帰的に処理
            if "children" in block:
                child_text = self.extract_text_from_blocks(block["children"])
                text += child_text
        
        return text
    
    def get_database_content(self, database_id: str) -> str:
        """
        データベースの内容を取得
        
        Args:
            database_id (str): データベースID
            
        Returns:
            str: データベースのテキスト内容
        """
        try:
            # データベースの基本情報を取得
            db_url = f"{self.base_url}/databases/{database_id}"
            db_response = requests.get(db_url, headers=self.headers)
            db_response.raise_for_status()
            db_data = db_response.json()
            
            # データベースのタイトル
            title = ""
            if "title" in db_data:
                title_list = db_data["title"]
                title = "".join([t.get("plain_text", "") for t in title_list])
            
            # データベースのページを取得
            pages_url = f"{self.base_url}/databases/{database_id}/query"
            pages_response = requests.post(pages_url, headers=self.headers, json={})
            pages_response.raise_for_status()
            pages_data = pages_response.json()
            
            # 各ページの内容を取得
            content = f"データベース: {title}\n\n"
            
            for page in pages_data.get("results", []):
                page_id = page["id"]
                page_content = self.get_page_content(page_id)
                if page_content:
                    content += f"--- ページ ---\n{page_content}\n\n"
            
            return content.strip()
            
        except Exception as e:
            print(f"❌ データベース内容取得エラー: {e}")
            return ""
    
    def process_all_content(self) -> List[Dict]:
        """
        全てのNotionコンテンツを処理
        
        Returns:
            List[Dict]: 処理されたドキュメントのリスト
        """
        print("🔍 Notion コンテンツ処理を開始...")
        
        documents = []
        
        # ページを取得・処理
        pages = self.search_pages()
        for page in pages:
            print(f"📄 ページ処理中: {page.get('id', 'Unknown')}")
            
            content = self.get_page_content(page["id"])
            if content:
                # ページタイトルを取得
                title = "Untitled"
                if "properties" in page:
                    for prop_key, prop_value in page["properties"].items():
                        if prop_value.get("type") == "title":
                            title_list = prop_value.get("title", [])
                            if title_list:
                                title = "".join([t.get("plain_text", "") for t in title_list])
                            break
                
                document = {
                    'id': f"notion_page_{page['id']}",
                    'title': title,
                    'content': content,
                    'source': 'notion',
                    'type': 'page',
                    'created_time': page.get('created_time', ''),
                    'last_edited_time': page.get('last_edited_time', ''),
                    'url': page.get('url', '')
                }
                documents.append(document)
                print(f"✅ ページ処理成功: {len(content)} 文字")
        
        # データベースを取得・処理
        databases = self.search_databases()
        for database in databases:
            print(f"🗂️ データベース処理中: {database.get('id', 'Unknown')}")
            
            content = self.get_database_content(database["id"])
            if content:
                # データベースタイトルを取得
                title = "Untitled Database"
                if "title" in database:
                    title_list = database["title"]
                    if title_list:
                        title = "".join([t.get("plain_text", "") for t in title_list])
                
                document = {
                    'id': f"notion_db_{database['id']}",
                    'title': title,
                    'content': content,
                    'source': 'notion',
                    'type': 'database',
                    'created_time': database.get('created_time', ''),
                    'last_edited_time': database.get('last_edited_time', ''),
                    'url': database.get('url', '')
                }
                documents.append(document)
                print(f"✅ データベース処理成功: {len(content)} 文字")
        
        print(f"🎉 Notion 処理完了: {len(documents)} 件のドキュメント")
        return documents

def test_notion_processor():
    """Notion プロセッサーのテスト実行"""
    print("=== Notion プロセッサー テスト実行 ===")
    
    # 環境変数からトークンを取得
    from dotenv import load_dotenv
    load_dotenv()
    
    notion_token = os.getenv('NOTION_TOKEN')
    if not notion_token:
        print("❌ NOTION_TOKEN が設定されていません")
        return
    
    try:
        # プロセッサーを初期化
        processor = NotionProcessor(notion_token)
        
        # ページ検索テスト
        pages = processor.search_pages()
        print(f"📄 利用可能ページ数: {len(pages)}")
        
        # データベース検索テスト
        databases = processor.search_databases()
        print(f"🗂️ 利用可能データベース数: {len(databases)}")
        
        # 実際の処理はコメントアウト（テスト時に大量データ処理を避けるため）
        # documents = processor.process_all_content()
        
        print("\n✅ Notion プロセッサーテスト完了")
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")

if __name__ == "__main__":
    test_notion_processor()
