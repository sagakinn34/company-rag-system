"""
Google Drive データ処理モジュール - Streamlit対応版
Google Drive から各種文書を取得し、テキストを抽出します
PDF、Word、Excel、PowerPoint に対応
"""

import streamlit as st
import json
import io
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

class GoogleDriveProcessor:
    def __init__(self):
        """Google Drive プロセッサーを初期化（Streamlit対応版）"""
        self.service = None
        self.setup_service()
    
    def setup_service(self):
        """Google Drive API サービスを設定（Streamlit Secrets対応）"""
        try:
            # 必要なスコープ
            SCOPES = [
                'https://www.googleapis.com/auth/drive.readonly',
            ]
            
            # Streamlit secretsから認証情報を取得
            creds_dict = st.secrets["GOOGLE_DRIVE_CREDENTIALS"]
            
            # 認証情報を構築
            self.credentials = Credentials.from_service_account_info(
                creds_dict, 
                scopes=SCOPES
            )
            
            # Drive API サービスを構築
            self.service = build('drive', 'v3', credentials=self.credentials)
            print("✅ Google Drive API サービスが正常に初期化されました")
            
        except Exception as e:
            print(f"❌ Google Drive API 初期化エラー: {e}")
            self.service = None
    
    def get_all_files(self) -> List[Dict]:
        """全ファイルを処理してドキュメント形式で返す（final_integration.py対応）"""
        if not self.service:
            print("❌ Google Drive サービスが初期化されていません")
            return []
        
        try:
            print("🔍 Google Drive ファイル一覧取得中...")
            
            # 簡易的なファイル一覧取得（テキストファイル重視）
            results = self.service.files().list(
                q="trashed=false and (mimeType contains 'text' or name contains '.txt' or name contains '.md')",
                pageSize=20,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            print(f"📁 {len(files)} 件のファイルが見つかりました")
            
            documents = []
            
            for file_info in files:
                print(f"📄 処理中: {file_info['name']}")
                
                try:
                    # ファイルの内容を取得
                    file_content = self.service.files().get_media(fileId=file_info['id']).execute()
                    
                    # テキストとして読み込み
                    try:
                        text = file_content.decode('utf-8')
                    except:
                        text = file_content.decode('utf-8', errors='ignore')
                    
                    if text.strip():
                        document = {
                            'id': f"gdrive_{file_info['id']}",
                            'title': file_info['name'],
                            'content': text,
                            'source': 'google_drive',
                            'type': 'file',
                            'mime_type': file_info['mimeType'],
                            'size': file_info.get('size', '0'),
                            'created_time': file_info.get('createdTime', ''),
                            'modified_time': file_info.get('modifiedTime', ''),
                            'url': f"https://drive.google.com/file/d/{file_info['id']}/view"
                        }
                        documents.append(document)
                        print(f"✅ テキスト抽出成功: {len(text)} 文字")
                    
                except Exception as e:
                    print(f"⚠️ ファイル処理スキップ: {file_info['name']} - {e}")
                    continue
            
            print(f"🎉 Google Drive 処理完了: {len(documents)} 件のドキュメント")
            return documents
            
        except Exception as e:
            print(f"❌ Google Drive ファイル処理エラー: {e}")
            return []
