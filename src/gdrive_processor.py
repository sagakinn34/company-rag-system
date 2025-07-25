"""
Google Drive データ処理モジュール - 診断機能付き完全版
"""

import streamlit as st
import json
import io
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

class GoogleDriveProcessor:
    def __init__(self):
        """Google Drive プロセッサーを初期化"""
        self.service = None
        self.setup_service()
    
    def setup_service(self):
        """Google Drive API サービスを設定（診断機能付き）"""
        try:
            print("🔍 Google Drive認証開始...")
            
            # Streamlit Secretsから認証情報を取得
            creds_data = st.secrets.get("GOOGLE_DRIVE_CREDENTIALS")
            if not creds_data:
                print("❌ GOOGLE_DRIVE_CREDENTIALSが設定されていません")
                return
            
            print("✅ 認証情報を取得しました")
            print(f"🔍 認証情報タイプ: {type(creds_data)}")
            
            # AttrDict → dict変換
            if hasattr(creds_data, '_data'):
                creds_dict = dict(creds_data._data)
            else:
                creds_dict = dict(creds_data)
            
            print("✅ 認証情報を辞書形式に変換しました")
            
            # 必要なフィールドの確認
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key', 'client_email']
            missing_fields = [field for field in required_fields if field not in creds_dict]
            
            if missing_fields:
                print(f"❌ 必要なフィールドが不足: {missing_fields}")
                return
            
            print("✅ 必要なフィールドが全て存在します")
            
            # スコープ設定
            SCOPES = [
                'https://www.googleapis.com/auth/drive.readonly',
            ]
            
            # 認証情報からCredentialsオブジェクトを作成
            self.credentials = Credentials.from_service_account_info(
                creds_dict, 
                scopes=SCOPES
            )
            
            print("✅ Google認証情報を作成しました")
            
            # Drive API サービスを構築
            self.service = build('drive', 'v3', credentials=self.credentials)
            
            print("✅ Google Drive API サービス初期化完了")
            
        except Exception as e:
            print(f"❌ Google Drive API 初期化エラー: {e}")
            print(f"🔍 エラータイプ: {type(e).__name__}")
            self.service = None
    
    def get_all_files(self) -> List[Dict]:
        """全ファイルを処理してドキュメント形式で返す（診断機能付き）"""
        if not self.service:
            print("❌ Google Drive サービスが初期化されていません")
            return []
        
        try:
            print("🔍 Google Drive ファイル検索を開始...")
            
            # まず基本的な接続テスト
            try:
                test_result = self.service.files().list(pageSize=1).execute()
                print(f"✅ 基本接続テスト成功")
            except Exception as e:
                print(f"❌ 基本接続テスト失敗: {e}")
                return []
            
            # 段階的検索戦略
            search_strategies = [
                {
                    'name': 'テキストファイル',
                    'query': "trashed=false and mimeType contains 'text'",
                    'limit': 10
                },
                {
                    'name': 'Google Docs',
                    'query': "trashed=false and mimeType='application/vnd.google-apps.document'",
                    'limit': 10
                },
                {
                    'name': 'PDFファイル',
                    'query': "trashed=false and mimeType='application/pdf'",
                    'limit': 5
                },
                {
                    'name': '全ファイル（サンプル）',
                    'query': "trashed=false",
                    'limit': 20
                }
            ]
            
            all_documents = []
            
            for strategy in search_strategies:
                print(f"📂 検索戦略: {strategy['name']}")
                
                try:
                    results = self.service.files().list(
                        q=strategy['query'],
                        pageSize=strategy['limit'],
                        fields="files(id, name, mimeType, size, createdTime, modifiedTime)"
                    ).execute()
                    
                    files = results.get('files', [])
                    print(f"📁 {strategy['name']}: {len(files)}件のファイルが見つかりました")
                    
                    if files:
                        # 最初のファイルの詳細を表示
                        sample_file = files[0]
                        print(f"📄 サンプルファイル: {sample_file['name']} ({sample_file['mimeType']})")
                        
                        # ファイル処理
                        for file_info in files:
                            try:
                                # テキスト抽出（簡易版）
                                text_content = self.extract_simple_text(file_info)
                                
                                if text_content and len(text_content.strip()) > 10:
                                    document = {
                                        'id': f"gdrive_{file_info['id']}",
                                        'title': file_info['name'],
                                        'content': text_content[:2000],  # 最初の2000文字
                                        'source': 'google_drive',
                                        'type': 'file',
                                        'mime_type': file_info['mimeType'],
                                        'size': file_info.get('size', '0'),
                                        'created_time': file_info.get('createdTime', ''),
                                        'modified_time': file_info.get('modifiedTime', ''),
                                        'url': f"https://drive.google.com/file/d/{file_info['id']}/view"
                                    }
                                    all_documents.append(document)
                                    print(f"✅ ファイル処理成功: {file_info['name']} ({len(text_content)}文字)")
                                
                            except Exception as file_error:
                                print(f"⚠️ ファイル処理スキップ: {file_info['name']} - {file_error}")
                        
                        # ファイルが見つかった場合は他の戦略はスキップ
                        if all_documents:
                            break
                    
                except Exception as strategy_error:
                    print(f"❌ 戦略「{strategy['name']}」エラー: {strategy_error}")
                    continue
            
            print(f"🎉 Google Drive 処理完了: {len(all_documents)} 件のドキュメント")
            return all_documents
            
        except Exception as e:
            print(f"❌ Google Drive ファイル処理エラー: {e}")
            return []
    
    def extract_simple_text(self, file_info: Dict) -> str:
        """簡易テキスト抽出（診断用）"""
        try:
            mime_type = file_info['mimeType']
            file_id = file_info['id']
            
            # Google Docs形式の場合
            if mime_type == 'application/vnd.google-apps.document':
                request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
                file_content = request.execute()
                return file_content.decode('utf-8', errors='ignore')
            
            # テキストファイルの場合
            elif 'text' in mime_type:
                request = self.service.files().get_media(fileId=file_id)
                file_content = request.execute()
                return file_content.decode('utf-8', errors='ignore')
            
            # その他のファイル（メタ情報のみ）
            else:
                return f"ファイル名: {file_info['name']}\nタイプ: {mime_type}\nサイズ: {file_info.get('size', '不明')}"
                
        except Exception as e:
            return f"テキスト抽出エラー: {e}"

