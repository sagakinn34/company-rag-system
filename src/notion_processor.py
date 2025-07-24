"""
Notion データ処理モジュール - Streamlit対応版
Streamlit Secrets から認証情報を取得し、Notion から各種ページとデータベースを取得
"""

import os
import json
import time
from typing import List, Dict, Optional
import requests
import streamlit as st

class NotionProcessor:
    def __init__(self):
        """
        Notion プロセッサーを初期化 - Streamlit環境対応版
        """
        # Streamlit Secretsから認証情報を取得
        try:
            self.notion_token = st.secrets["NOTION_TOKEN"]
            if not self.notion_token:
                raise ValueError("NOTION_TOKEN が設定されていません")
        except KeyError:
            raise ValueError("Streamlit SecretsにNOTION_TOKENが設定されていません")
        
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {self.notion_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
        }
        
        st.info("✅ NotionProcessor初期化完了")
    
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
            
            st.info(f"📄 {len(pages)} 件のNotionページが見つかりました")
            return pages
            
        except Exception as e:
            st.error(f"❌ Notionページ検索エラー: {e}")
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
            
            st.info(f"🗂️ {len(databases)} 件のNotionデータベースが見つかりました")
            return databases
            
        except Exception as e:
            st.error(f"❌ Notionデータベース検索エラー: {e}")
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
            st.error(f"❌ ページ内容取得エラー: {e}")
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
            st.error(f"❌ データベース内容取得エラー: {e}")
            return ""
    
    def get_all_pages(self) -> List[Dict]:
        """
        全てのNotionコンテンツを処理してRAG用のドキュメント形式で返す
        
        Returns:
            List[Dict]: 処理されたドキュメントのリスト
        """
        st.info("🔍 Notion コンテンツ処理を開始...")
        
        documents = []
        
        # ページを取得・処理
        pages = self.search_pages()
        for page in pages:
            try:
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
                    st.success(f"✅ Notionページ処理成功: {title} ({len(content)} 文字)")
            except Exception as e:
                st.error(f"❌ ページ処理エラー: {e}")
                continue
        
        # データベースを取得・処理
        databases = self.search_databases()
        for database in databases:
            try:
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
                    st.success(f"✅ Notionデータベース処理成功: {title} ({len(content)} 文字)")
            except Exception as e:
                st.error(f"❌ データベース処理エラー: {e}")
                continue
        
        st.success(f"🎉 Notion 処理完了: {len(documents)} 件のドキュメント")
        return documents
