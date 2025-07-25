"""
Google Drive データ処理モジュール - 最適化版（実用性と可用性のバランス）
"""

import streamlit as st
import json
import io
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
import gc

class GoogleDriveProcessor:
    def __init__(self):
        """Google Drive プロセッサーを初期化"""
        self.service = None
        self.setup_service()
    
    def setup_service(self):
        """Google Drive API サービスを設定"""
        try:
            print("🔍 Google Drive認証開始...")
            
            # Streamlit Secretsから認証情報を取得
            creds_data = st.secrets.get("GOOGLE_DRIVE_CREDENTIALS")
            if not creds_data:
                print("❌ GOOGLE_DRIVE_CREDENTIALSが設定されていません")
                return
            
            print("✅ 認証情報を取得しました")
            
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
        """最適化版ファイル取得（100件上限・効率重視）"""
        if not self.service:
            print("❌ Google Drive サービスが初期化されていません")
            return []
        
        try:
            print("🔍 Google Drive最適化処理を開始...")
            
            # 基本接続テスト
            try:
                test_result = self.service.files().list(pageSize=1).execute()
                print(f"✅ 基本接続テスト成功")
            except Exception as e:
                print(f"❌ 基本接続テスト失敗: {e}")
                return []
            
            # === 最適化設定 ===
            TOTAL_LIMIT = 100         # 総ファイル数上限
            CONTENT_LIMIT = 1500      # 1ファイルあたり文字制限
            
            # 効率的取得戦略
            strategies = [
                {
                    'name': 'Google Docs（重要文書）',
                    'query': "trashed=false and mimeType='application/vnd.google-apps.document'",
                    'limit': 60,  # 60%
                    'priority': 'high'
                },
                {
                    'name': 'PDF（報告書）',
                    'query': "trashed=false and mimeType='application/pdf'",
                    'limit': 25,  # 25%
                    'priority': 'medium'
                },
                {
                    'name': 'スプレッドシート（データ）',
                    'query': "trashed=false and mimeType='application/vnd.google-apps.spreadsheet'",
                    'limit': 15,  # 15%
                    'priority': 'medium'
                }
            ]
            
            all_documents = []
            
            for strategy in strategies:
                print(f"📂 {strategy['name']} 取得中... (上限: {strategy['limit']}件)")
                
                try:
                    # 効率的ファイル取得
                    files = self.get_files_by_strategy(strategy, CONTENT_LIMIT)
                    
                    if files:
                        all_documents.extend(files)
                        print(f"✅ {strategy['name']}: {len(files)}件取得成功")
                    else:
                        print(f"⚠️ {strategy['name']}: ファイルが見つかりません")
                    
                    # メモリクリーンアップ
                    gc.collect()
                    
                except Exception as strategy_error:
                    print(f"❌ {strategy['name']}取得エラー: {strategy_error}")
                    continue
            
            print(f"🎉 Google Drive最適化処理完了: {len(all_documents)} 件のドキュメント")
            
            # 結果サマリー表示
            self.print_optimized_summary(all_documents)
            
            return all_documents[:TOTAL_LIMIT]  # 念のため上限制限
            
        except Exception as e:
            print(f"❌ Google Drive最適化処理エラー: {e}")
            return []
    
    def get_files_by_strategy(self, strategy: Dict, content_limit: int) -> List[Dict]:
        """戦略別ファイル取得"""
        documents = []
        
        try:
            # ファイル一覧取得（最新順）
            results = self.service.files().list(
                q=strategy['query'],
                pageSize=strategy['limit'],
                orderBy='modifiedTime desc',
                fields="files(id, name, mimeType, size, createdTime, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            
            for file_info in files:
                try:
                    # 軽量テキスト抽出
                    text_content = self.extract_text_optimized(file_info, content_limit)
                    
                    if text_content and len(text_content.strip()) > 20:
                        document = {
                            'id': f"gdrive_{file_info['id']}",
                            'title': file_info['name'],
                            'content': text_content[:content_limit],
                            'source': 'google_drive',
                            'type': 'file',
                            'category': strategy['name'],
                            'priority': strategy['priority'],
                            'mime_type': file_info['mimeType'],
                            'size': file_info.get('size', '0'),
                            'created_time': file_info.get('createdTime', ''),
                            'modified_time': file_info.get('modifiedTime', ''),
                            'url': f"https://drive.google.com/file/d/{file_info['id']}/view"
                        }
                        documents.append(document)
                
                except Exception as file_error:
                    print(f"⚠️ ファイル処理スキップ: {file_info.get('name', '不明')} - {file_error}")
                    continue
            
            return documents
            
        except Exception as e:
            print(f"❌ 戦略別ファイル取得エラー: {e}")
            return []
    
    def extract_text_optimized(self, file_info: Dict, content_limit: int) -> str:
        """最適化テキスト抽出"""
        try:
            mime_type = file_info['mimeType']
            file_id = file_info['id']
            file_name = file_info.get('name', '不明')
            
            # Google Docs形式（優先処理）
            if mime_type == 'application/vnd.google-apps.document':
                try:
                    request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
                    file_content = request.execute()
                    text = file_content.decode('utf-8', errors='ignore')
                    return text[:content_limit]  # 文字数制限
                except Exception as e:
                    return f"Google Docs: {file_name} (抽出エラー)"
            
            # Google Sheets形式（簡易処理）
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                try:
                    request = self.service.files().export_media(fileId=file_id, mimeType='text/csv')
                    file_content = request.execute()
                    text = file_content.decode('utf-8', errors='ignore')
                    return f"スプレッドシート: {file_name}\n\n{text[:content_limit-100]}"
                except Exception as e:
                    return f"Google Sheets: {file_name} (データ抽出エラー)"
            
            # PDF・その他ファイル（メタデータのみ）
            else:
                file_size = file_info.get('size', '不明')
                created_time = file_info.get('createdTime', '不明')
                modified_time = file_info.get('modifiedTime', '不明')
                
                meta_info = f"""ファイル名: {file_name}
ファイルタイプ: {mime_type}
ファイルサイズ: {file_size} bytes
作成日時: {created_time}
更新日時: {modified_time}

※メタデータ検索対象"""
                
                return meta_info[:content_limit]
                
        except Exception as e:
            return f"ファイル: {file_info.get('name', '不明')} (処理エラー)"
    
    def print_optimized_summary(self, documents: List[Dict]):
        """最適化結果サマリー表示"""
        print("\n📊 === Google Drive最適化取得サマリー ===")
        
        # カテゴリ別集計
        category_count = {}
        priority_count = {}
        
        for doc in documents:
            category = doc.get('category', '不明')
            priority = doc.get('priority', '不明')
            
            category_count[category] = category_count.get(category, 0) + 1
            priority_count[priority] = priority_count.get(priority, 0) + 1
        
        print("📂 カテゴリ別:")
        for category, count in category_count.items():
            print(f"  - {category}: {count}件")
        
        print("⭐ 重要度別:")
        for priority, count in priority_count.items():
            print(f"  - {priority}: {count}件")
        
        # 文字数統計
        total_chars = sum(len(doc.get('content', '')) for doc in documents)
        avg_chars = total_chars / len(documents) if documents else 0
        
        print(f"📝 総文字数: {total_chars:,}文字")
        print(f"📝 平均文字数: {avg_chars:.0f}文字")
        print(f"📝 総計: {len(documents)}件")
        print("=" * 40)

