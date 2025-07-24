"""
Google Drive データ処理モジュール - Base64修正版
Google Drive から各種文書を取得し、テキストを抽出します
Streamlit Secrets対応・エラーハンドリング強化版
"""

import streamlit as st
import json
import io
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

class GoogleDriveProcessor:
    def __init__(self):
        """Google Drive プロセッサーを初期化（Base64対応版）"""
        self.service = None
        self.credentials = None
        self.setup_service()
    
    def setup_service(self):
        """Google Drive API サービスを設定（堅牢版）"""
        try:
            # 必要なスコープ
            SCOPES = [
                'https://www.googleapis.com/auth/drive.readonly',
            ]
            
            print("🔍 Google Drive 認証情報を確認中...")
            
            # Streamlit secretsから認証情報を安全に取得
            creds_data = st.secrets.get("GOOGLE_DRIVE_CREDENTIALS")
            
            if not creds_data:
                raise ValueError("GOOGLE_DRIVE_CREDENTIALS が設定されていません")
            
            print("✅ 認証情報の存在を確認")
            
            # 認証情報の型確認と処理
            if isinstance(creds_data, str):
                # 文字列の場合はJSONとしてパース
                try:
                    creds_dict = json.loads(creds_data)
                    print("✅ JSON文字列からの変換成功")
                except json.JSONDecodeError as e:
                    raise ValueError(f"認証情報のJSON解析エラー: {e}")
            elif isinstance(creds_data, dict):
                # 既に辞書形式の場合
                creds_dict = creds_data
                print("✅ 辞書形式の認証情報を確認")
            else:
                raise ValueError(f"認証情報の形式が不正です: {type(creds_data)}")
            
            # 必須フィールドの確認
            required_fields = [
                "type", "project_id", "private_key_id", 
                "private_key", "client_email", "client_id"
            ]
            
            missing_fields = [field for field in required_fields if field not in creds_dict]
            if missing_fields:
                raise ValueError(f"認証情報に必須フィールドが不足: {missing_fields}")
            
            print("✅ 必須フィールドの存在を確認")
            
            # private_keyの改行文字を適切に処理
            if "private_key" in creds_dict:
                private_key = creds_dict["private_key"]
                if "\\n" in private_key:
                    creds_dict["private_key"] = private_key.replace("\\n", "\n")
                    print("✅ private_keyの改行文字を修正")
            
            # 認証情報を構築
            self.credentials = Credentials.from_service_account_info(
                creds_dict, 
                scopes=SCOPES
            )
            print("✅ Google認証情報の構築成功")
            
            # Drive API サービスを構築
            self.service = build('drive', 'v3', credentials=self.credentials)
            print("✅ Google Drive API サービス初期化成功")
            
            # 接続テスト
            test_result = self.service.files().list(pageSize=1, fields="files(id, name)").execute()
            test_files = test_result.get('files', [])
            print(f"✅ 接続テスト成功: {len(test_files)}件のファイルにアクセス可能")
            
        except Exception as e:
            error_msg = f"Google Drive API 初期化エラー: {e}"
            print(f"❌ {error_msg}")
            print(f"🔍 エラータイプ: {type(e).__name__}")
            print(f"🔍 詳細情報: {str(e)}")
            
            self.service = None
            self.credentials = None
            
            # 診断情報を出力
            self._output_diagnostic_info()
    
    def _output_diagnostic_info(self):
        """診断情報を出力"""
        print("\n🔍 === Google Drive 診断情報 ===")
        
        try:
            creds_data = st.secrets.get("GOOGLE_DRIVE_CREDENTIALS")
            if creds_data:
                print(f"✅ 認証情報のタイプ: {type(creds_data)}")
                
                if isinstance(creds_data, str):
                    print(f"📏 文字列長: {len(creds_data)}")
                    print(f"🔤 先頭50文字: {creds_data[:50]}...")
                    
                    # JSON解析テスト
                    try:
                        test_dict = json.loads(creds_data)
                        print(f"✅ JSON解析: 成功 ({len(test_dict)}個のキー)")
                        print(f"🔑 利用可能キー: {list(test_dict.keys())}")
                    except json.JSONDecodeError as je:
                        print(f"❌ JSON解析: 失敗 - {je}")
                        
                elif isinstance(creds_data, dict):
                    print(f"📊 辞書サイズ: {len(creds_data)}")
                    print(f"🔑 キー一覧: {list(creds_data.keys())}")
            else:
                print("❌ 認証情報が見つかりません")
                
        except Exception as e:
            print(f"❌ 診断中にエラー: {e}")
        
        print("=== 診断情報終了 ===\n")
    
    def test_connection(self) -> bool:
        """接続テストを実行"""
        if not self.service:
            print("❌ Google Drive サービスが初期化されていません")
            return False
        
        try:
            print("🧪 Google Drive 接続テスト中...")
            
            # 基本的なファイル一覧取得テスト
            results = self.service.files().list(
                pageSize=5,
                fields="files(id, name, mimeType)"
            ).execute()
            
            files = results.get('files', [])
            print(f"✅ 接続テスト成功: {len(files)}件のファイルを確認")
            
            if files:
                print("📄 取得可能ファイル例:")
                for i, file_info in enumerate(files[:3]):
                    print(f"  {i+1}. {file_info['name']} ({file_info['mimeType']})")
            
            return True
            
        except Exception as e:
            print(f"❌ 接続テスト失敗: {e}")
            return False
    
    def get_all_files(self) -> List[Dict]:
        """全ファイルを処理してドキュメント形式で返す（安全版）"""
        if not self.service:
            print("❌ Google Drive サービスが初期化されていません")
            return []
        
        try:
            print("🔍 Google Drive ファイル取得開始...")
            
            # 段階的にファイル検索を実行
            documents = []
            
            # 検索クエリのパターン
            search_patterns = [
                {
                    "name": "テキストファイル",
                    "query": "trashed=false and (mimeType contains 'text' or name contains '.txt' or name contains '.md')",
                    "limit": 10
                },
                {
                    "name": "Google Docs",
                    "query": "trashed=false and mimeType='application/vnd.google-apps.document'",
                    "limit": 5
                },
                {
                    "name": "全ファイル（制限付き）",
                    "query": "trashed=false",
                    "limit": 15
                }
            ]
            
            for pattern in search_patterns:
                print(f"📂 {pattern['name']} を検索中...")
                
                try:
                    results = self.service.files().list(
                        q=pattern['query'],
                        pageSize=pattern['limit'],
                        fields="files(id, name, mimeType, size, createdTime, modifiedTime)"
                    ).execute()
                    
                    files = results.get('files', [])
                    print(f"  → {len(files)}件見つかりました")
                    
                    for file_info in files:
                        # ファイル処理をスキップする条件
                        if self._should_skip_file(file_info):
                            print(f"  ⏭️  スキップ: {file_info['name']}")
                            continue
                        
                        # ファイル内容を取得
                        content = self._extract_file_content(file_info)
                        
                        if content and content.strip():
                            document = {
                                'id': f"gdrive_{file_info['id']}",
                                'title': file_info['name'],
                                'content': content,
                                'source': 'google_drive',
                                'type': 'file',
                                'mime_type': file_info['mimeType'],
                                'size': file_info.get('size', '0'),
                                'created_time': file_info.get('createdTime', ''),
                                'modified_time': file_info.get('modifiedTime', ''),
                                'url': f"https://drive.google.com/file/d/{file_info['id']}/view"
                            }
                            documents.append(document)
                            print(f"  ✅ 追加: {file_info['name']} ({len(content)}文字)")
                        
                        # 十分なデータが集まったら終了
                        if len(documents) >= 20:
                            break
                    
                    if len(documents) >= 20:
                        break
                        
                except Exception as e:
                    print(f"  ❌ {pattern['name']} 検索エラー: {e}")
                    continue
            
            print(f"🎉 Google Drive 処理完了: {len(documents)} 件のドキュメント")
            return documents
            
        except Exception as e:
            print(f"❌ Google Drive ファイル処理エラー: {e}")
            return []
    
    def _should_skip_file(self, file_info: Dict) -> bool:
        """ファイルをスキップするかどうか判定"""
        # バイナリファイルや大きすぎるファイルはスキップ
        mime_type = file_info.get('mimeType', '')
        size = int(file_info.get('size', 0))
        
        # 1MB以上のファイルはスキップ
        if size > 1024 * 1024:
            return True
        
        # 画像・動画・音声ファイルはスキップ
        skip_types = ['image/', 'video/', 'audio/', 'application/zip', 'application/pdf']
        for skip_type in skip_types:
            if mime_type.startswith(skip_type):
                return True
        
        return False
    
    def _extract_file_content(self, file_info: Dict) -> str:
        """ファイル内容を安全に抽出"""
        try:
            file_id = file_info['id']
            mime_type = file_info['mimeType']
            
            # Google Docs形式の場合はプレーンテキストとしてエクスポート
            if mime_type == 'application/vnd.google-apps.document':
                request = self.service.files().export_media(
                    fileId=file_id, 
                    mimeType='text/plain'
                )
            else:
                # その他のファイルは直接ダウンロード
                request = self.service.files().get_media(fileId=file_id)
            
            file_content = request.execute()
            
            # テキストとしてデコード
            if isinstance(file_content, bytes):
                try:
                    text = file_content.decode('utf-8')
                except UnicodeDecodeError:
                    try:
                        text = file_content.decode('utf-8', errors='ignore')
                    except:
                        text = file_content.decode('cp932', errors='ignore')
            else:
                text = str(file_content)
            
            return text.strip()
            
        except Exception as e:
            print(f"  ⚠️ ファイル内容抽出エラー ({file_info['name']}): {e}")
            return ""


def test_google_drive_processor():
    """Google Drive プロセッサーのテスト実行"""
    print("=== Google Drive プロセッサー テスト実行 ===")
    
    try:
        # プロセッサーを初期化
        processor = GoogleDriveProcessor()
        
        # 接続テスト
        if processor.test_connection():
            print("✅ 基本接続テスト成功")
            
            # ファイル取得テスト
            documents = processor.get_all_files()
            print(f"📊 取得結果: {len(documents)} 件のドキュメント")
            
            if documents:
                print("\n📋 取得ドキュメント一覧:")
                for i, doc in enumerate(documents[:5]):
                    print(f"  {i+1}. {doc['title']} ({len(doc['content'])}文字)")
        else:
            print("❌ 基本接続テスト失敗")
        
        print("\n✅ Google Drive プロセッサーテスト完了")
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")

if __name__ == "__main__":
    test_google_drive_processor()

