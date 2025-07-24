import os
import json
import streamlit as st
from google.oauth2 import service_account
from googleapiclient.discovery import build
import logging

class GoogleDriveProcessorCloud:
    """Google Drive プロセッサー（クラウド対応版）"""
    
    def __init__(self):
        """クラウド環境でGoogle Drive API を初期化"""
        self.service = None
        self.logger = logging.getLogger(__name__)
        self._initialize_service()
    
    def _initialize_service(self):
        """Google Drive APIサービスを初期化"""
        try:
            # Streamlit Secretsから認証情報を取得
            if hasattr(st, 'secrets') and 'GOOGLE_DRIVE_CREDENTIALS' in st.secrets:
                credentials_info = json.loads(st.secrets['GOOGLE_DRIVE_CREDENTIALS'])
                
                credentials = service_account.Credentials.from_service_account_info(
                    credentials_info,
                    scopes=['https://www.googleapis.com/auth/drive.readonly']
                )
                
                self.service = build('drive', 'v3', credentials=credentials)
                self.logger.info("✅ Google Drive API（クラウド版）の初期化が完了")
                
            else:
                # ローカル環境の場合
                credentials_path = os.getenv('GOOGLE_DRIVE_CREDENTIALS')
                if credentials_path and os.path.exists(credentials_path):
                    credentials = service_account.Credentials.from_service_account_file(
                        credentials_path,
                        scopes=['https://www.googleapis.com/auth/drive.readonly']
                    )
                    
                    self.service = build('drive', 'v3', credentials=credentials)
                    self.logger.info("✅ Google Drive API（ローカル版）の初期化が完了")
                else:
                    self.logger.warning("⚠️ Google Drive認証情報が設定されていません")
                    
        except Exception as e:
            self.logger.error(f"❌ Google Drive API初期化エラー: {e}")
            self.service = None
    
    def is_available(self):
        """Google Drive APIが利用可能かチェック"""
        return self.service is not None
    
    def process_all_files(self):
        """全ファイルを処理（クラウド対応版）"""
        if not self.is_available():
            self.logger.warning("Google Drive APIが利用できません")
            return []
        
        try:
            results = self.service.files().list(
                pageSize=100,
                fields="nextPageToken, files(id, name, mimeType, modifiedTime, size)"
            ).execute()
            
            files = results.get('files', [])
            documents = []
            
            for file_info in files:
                try:
                    if self._is_text_file(file_info['mimeType']):
                        content = self._extract_file_content(file_info)
                        if content:
                            doc = {
                                'id': f"gdrive_{file_info['id']}",
                                'title': file_info['name'],
                                'content': content,
                                'source': 'Google Drive',
                                'url': f"https://drive.google.com/file/d/{file_info['id']}/view",
                                'timestamp': file_info.get('modifiedTime', ''),
                                'metadata': {
                                    'file_id': file_info['id'],
                                    'mime_type': file_info['mimeType'],
                                    'size': file_info.get('size', 0)
                                }
                            }
                            documents.append(doc)
                            
                except Exception as e:
                    self.logger.error(f"ファイル処理エラー {file_info['name']}: {e}")
                    continue
            
            self.logger.info(f"Google Drive: {len(documents)}件のドキュメントを処理")
            return documents
            
        except Exception as e:
            self.logger.error(f"Google Drive処理エラー: {e}")
            return []
    
    def _is_text_file(self, mime_type):
        """テキスト系ファイルかチェック"""
        text_types = [
            'text/plain',
            'application/pdf',
            'application/vnd.google-apps.document',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/msword'
        ]
        return mime_type in text_types
    
    def _extract_file_content(self, file_info):
        """ファイルコンテンツを抽出"""
        try:
            if file_info['mimeType'] == 'application/vnd.google-apps.document':
                result = self.service.files().export_media(
                    fileId=file_info['id'],
                    mimeType='text/plain'
                ).execute()
                return result.decode('utf-8')
            else:
                result = self.service.files().get_media(fileId=file_info['id']).execute()
                return result.decode('utf-8', errors='ignore')[:3000]
                
        except Exception as e:
            self.logger.error(f"コンテンツ抽出エラー: {e}")
            return ""
