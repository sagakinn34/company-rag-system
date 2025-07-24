"""
Google Drive データ処理モジュール - Streamlit対応版
Streamlit Secrets から認証情報を取得し、Google Drive から各種文書を取得
"""

import os
import json
import io
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import streamlit as st

class GoogleDriveProcessor:
    def __init__(self):
        """
        Google Drive プロセッサーを初期化 - Streamlit環境対応版
        """
        self.service = None
        self.setup_service()
    
    def setup_service(self):
        """Google Drive API サービスを設定"""
        try:
            # Streamlit Secretsから認証情報を取得
            try:
                credentials_info = st.secrets["GOOGLE_DRIVE_CREDENTIALS"]
                if not credentials_info:
                    raise ValueError("GOOGLE_DRIVE_CREDENTIALS が設定されていません")
            except KeyError:
                raise ValueError("Streamlit SecretsにGOOGLE_DRIVE_CREDENTIALSが設定されていません")
            
            # 必要なスコープ
            SCOPES = [
                'https://www.googleapis.com/auth/drive.readonly',
                'https://www.googleapis.com/auth/documents.readonly',
                'https://www.googleapis.com/auth/spreadsheets.readonly',
                'https://www.googleapis.com/auth/presentations.readonly'
            ]
            
            # Streamlit SecretsからJSON形式の認証情報を取得
            if isinstance(credentials_info, dict):
                # 辞書形式の場合はそのまま使用
                credentials_dict = credentials_info
            else:
                # 文字列形式の場合はJSONとしてパース
                credentials_dict = json.loads(credentials_info)
            
            # 認証情報を読み込み
            credentials = Credentials.from_service_account_info(
                credentials_dict, 
                scopes=SCOPES
            )
            
            # Drive API サービスを構築
            self.service = build('drive', 'v3', credentials=credentials)
            st.info("✅ Google Drive API サービスが正常に初期化されました")
            
        except Exception as e:
            st.error(f"❌ Google Drive API 初期化エラー: {e}")
            self.service = None
    
    def list_files(self, folder_id: Optional[str] = None, file_types: Optional[List[str]] = None) -> List[Dict]:
        """
        Google Drive のファイル一覧を取得
        
        Args:
            folder_id (str, optional): 特定フォルダのID
            file_types (List[str], optional): 取得するファイルタイプ
            
        Returns:
            List[Dict]: ファイル情報のリスト
        """
        if not self.service:
            st.error("❌ Google Drive API サービスが初期化されていません")
            return []
        
        try:
            # クエリを構築
            query_parts = []
            
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            
            if file_types:
                mime_types = []
                for file_type in file_types:
                    if file_type == 'pdf':
                        mime_types.append("mimeType='application/pdf'")
                    elif file_type == 'docx':
                        mime_types.append("mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'")
                    elif file_type == 'xlsx':
                        mime_types.append("mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'")
                    elif file_type == 'pptx':
                        mime_types.append("mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation'")
                    elif file_type == 'docs':
                        mime_types.append("mimeType='application/vnd.google-apps.document'")
                    elif file_type == 'sheets':
                        mime_types.append("mimeType='application/vnd.google-apps.spreadsheet'")
                    elif file_type == 'slides':
                        mime_types.append("mimeType='application/vnd.google-apps.presentation'")
                
                if mime_types:
                    query_parts.append(f"({' or '.join(mime_types)})")
            
            query_parts.append("trashed=false")
            query = ' and '.join(query_parts) if query_parts else "trashed=false"
            
            # ファイル一覧を取得
            results = self.service.files().list(
                q=query,
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, size, createdTime, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            st.info(f"📁 {len(files)} 件のGoogle Driveファイルが見つかりました")
            
            return files
            
        except Exception as e:
            st.error(f"❌ Google Driveファイル一覧取得エラー: {e}")
            return []
    
    def download_and_extract_text(self, file_id: str, mime_type: str) -> str:
        """ファイルをダウンロードしてテキストを抽出"""
        if not self.service:
            return ""
        
        try:
            # Google Docs形式の場合はエクスポート
            if mime_type == 'application/vnd.google-apps.document':
                request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                request = self.service.files().export_media(fileId=file_id, mimeType='text/csv')
            elif mime_type == 'application/vnd.google-apps.presentation':
                request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
            else:
                # その他のファイルは直接ダウンロード
                request = self.service.files().get_media(fileId=file_id)
            
            file_content = request.execute()
            
            # Google Docs形式の場合はプレーンテキストとして処理
            if 'google-apps' in mime_type:
                return file_content.decode('utf-8')
            else:
                # その他はプレーンテキストとして試行
                try:
                    return file_content.decode('utf-8')
                except:
                    return file_content.decode('utf-8', errors='ignore')
        
        except Exception as e:
            st.error(f"❌ ファイルダウンロード・テキスト抽出エラー: {e}")
            return ""
    
    def get_all_files(self) -> List[Dict]:
        """
        全ファイルを処理してRAG用のドキュメント形式で返す
        
        Returns:
            List[Dict]: 処理されたドキュメントのリスト
        """
        st.info("🔍 Google Drive ファイル処理を開始...")
        
        # 対応ファイルタイプ（軽量化のためGoogle Apps形式を優先）
        supported_types = ['docs', 'sheets', 'slides']
        files = self.list_files(file_types=supported_types)
        
        documents = []
        
        for file_info in files:
            try:
                st.info(f"📄 Google Driveファイル処理中: {file_info['name']}")
                
                # テキストを抽出
                text = self.download_and_extract_text(file_info['id'], file_info['mimeType'])
                
                if text.strip():
                    document = {
                        'id': f"gdrive_{file_info['id']}",
                        'title': file_info['name'],
                        'content': text,
                        'source': 'google_drive',
                        'type': 'document',
                        'mime_type': file_info['mimeType'],
                        'size': file_info.get('size', '0'),
                        'created_time': file_info.get('createdTime', ''),
                        'modified_time': file_info.get('modifiedTime', ''),
                        'url': f"https://drive.google.com/file/d/{file_info['id']}/view"
                    }
                    documents.append(document)
                    st.success(f"✅ Google Driveファイル処理成功: {file_info['name']} ({len(text)} 文字)")
                else:
                    st.warning(f"⚠️ テキスト抽出失敗: {file_info['name']}")
            except Exception as e:
                st.error(f"❌ ファイル処理エラー: {e}")
                continue
        
        st.success(f"🎉 Google Drive 処理完了: {len(documents)} 件のドキュメント")
        return documents
