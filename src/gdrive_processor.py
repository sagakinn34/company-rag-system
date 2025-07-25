"""
Google Drive データ処理モジュール - 小規模企業向け拡張版（200件上限）
"""

import streamlit as st
import json
import io
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

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
    
    def get_date_string(self, days_ago):
        """指定日数前の日付文字列を取得"""
        target_date = datetime.now() - timedelta(days=days_ago)
        return target_date.strftime('%Y-%m-%dT%H:%M:%S')
    
    def get_all_files(self) -> List[Dict]:
        """小規模企業向け拡張取得（200件上限・バランス重視）"""
        if not self.service:
            print("❌ Google Drive サービスが初期化されていません")
            return []
        
        try:
            print("🔍 Google Drive ファイル検索を開始（小規模企業拡張版）...")
            
            # 基本接続テスト
            try:
                test_result = self.service.files().list(pageSize=1).execute()
                print(f"✅ 基本接続テスト成功")
            except Exception as e:
                print(f"❌ 基本接続テスト失敗: {e}")
                return []
            
            # 小規模企業向けバランス取得戦略
            search_strategies = [
                {
                    'name': 'Google Docs（企画・議事録）',
                    'query': "trashed=false and mimeType='application/vnd.google-apps.document'",
                    'limit': 80,  # 40%
                    'priority': 'high',
                    'recent_ratio': 0.6  # 60%最近、40%過去
                },
                {
                    'name': 'PDF（報告書・契約書）',
                    'query': "trashed=false and mimeType='application/pdf'",
                    'limit': 60,  # 30%
                    'priority': 'high',
                    'recent_ratio': 0.5  # 50%最近、50%過去
                },
                {
                    'name': 'Excel（データ・分析）',
                    'query': "trashed=false and (mimeType='application/vnd.google-apps.spreadsheet' or mimeType contains 'excel')",
                    'limit': 30,  # 15%
                    'priority': 'medium',
                    'recent_ratio': 0.7  # 70%最近、30%過去
                },
                {
                    'name': 'PowerPoint（プレゼン）',
                    'query': "trashed=false and (mimeType='application/vnd.google-apps.presentation' or mimeType contains 'powerpoint')",
                    'limit': 20,  # 10%
                    'priority': 'medium',
                    'recent_ratio': 0.8  # 80%最近、20%過去
                },
                {
                    'name': 'テキスト（技術文書）',
                    'query': "trashed=false and mimeType contains 'text'",
                    'limit': 10,  # 5%
                    'priority': 'low',
                    'recent_ratio': 0.5  # 50%最近、50%過去
                }
            ]
            
            all_documents = []
            
            for strategy in search_strategies:
                print(f"📂 検索戦略: {strategy['name']} (上限: {strategy['limit']}件)")
                
                try:
                    # 時系列バランス計算
                    recent_limit = int(strategy['limit'] * strategy['recent_ratio'])
                    old_limit = strategy['limit'] - recent_limit
                    
                    strategy_documents = []
                    
                    # 最近のファイル取得（90日以内）
                    if recent_limit > 0:
                        recent_query = f"{strategy['query']} and modifiedTime > '{self.get_date_string(90)}'"
                        recent_files = self.get_files_by_query(
                            recent_query, 
                            recent_limit, 
                            'modifiedTime desc'
                        )
                        strategy_documents.extend(recent_files)
                        print(f"  📅 最近90日: {len(recent_files)}件取得")
                    
                    # 過去のファイル取得（90日より前）
                    if old_limit > 0:
                        old_query = f"{strategy['query']} and modifiedTime <= '{self.get_date_string(90)}'"
                        old_files = self.get_files_by_query(
                            old_query, 
                            old_limit, 
                            'modifiedTime desc'
                        )
                        strategy_documents.extend(old_files)
                        print(f"  📅 過去: {len(old_files)}件取得")
                    
                    # 文書処理
                    processed_count = 0
                    for file_info in strategy_documents:
                        try:
                            # テキスト抽出
                            text_content = self.extract_simple_text(file_info)
                            
                            if text_content and len(text_content.strip()) > 10:
                                document = {
                                    'id': f"gdrive_{file_info['id']}",
                                    'title': file_info['name'],
                                    'content': text_content[:3000],  # 3000文字に拡張
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
                                all_documents.append(document)
                                processed_count += 1
                            
                        except Exception as file_error:
                            print(f"⚠️ ファイル処理スキップ: {file_info['name']} - {file_error}")
                            continue
                    
                    print(f"✅ {strategy['name']}: {processed_count}件処理完了")
                    
                except Exception as strategy_error:
                    print(f"❌ 戦略「{strategy['name']}」エラー: {strategy_error}")
                    continue
            
            print(f"🎉 Google Drive 処理完了: {len(all_documents)} 件のドキュメント")
            
            # 結果サマリー表示
            self.print_summary(all_documents)
            
            return all_documents
            
        except Exception as e:
            print(f"❌ Google Drive ファイル処理エラー: {e}")
            return []
    
    def get_files_by_query(self, query: str, limit: int, order_by: str = 'modifiedTime desc') -> List[Dict]:
        """クエリによるファイル取得（ページネーション対応）"""
        files = []
        page_token = None
        remaining_limit = limit
        
        while remaining_limit > 0:
            try:
                page_size = min(remaining_limit, 100)  # API制限
                
                request_params = {
                    'q': query,
                    'pageSize': page_size,
                    'orderBy': order_by,
                    'fields': "files(id, name, mimeType, size, createdTime, modifiedTime), nextPageToken"
                }
                
                if page_token:
                    request_params['pageToken'] = page_token
                
                results = self.service.files().list(**request_params).execute()
                current_files = results.get('files', [])
                
                if not current_files:
                    break
                
                files.extend(current_files)
                remaining_limit -= len(current_files)
                
                page_token = results.get('nextPageToken')
                if not page_token:
                    break
                    
            except Exception as e:
                print(f"❌ クエリ実行エラー: {e}")
                break
        
        return files[:limit]  # 念のため上限でカット
    
    def extract_simple_text(self, file_info: Dict) -> str:
        """テキスト抽出（エラーハンドリング強化版）"""
        try:
            mime_type = file_info['mimeType']
            file_id = file_info['id']
            file_name = file_info.get('name', '不明')
            
            print(f"  🔍 テキスト抽出中: {file_name} ({mime_type})")
            
            # Google Docs形式の場合
            if mime_type == 'application/vnd.google-apps.document':
                try:
                    request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
                    file_content = request.execute()
                    text = file_content.decode('utf-8', errors='ignore')
                    print(f"    ✅ Google Docs: {len(text)}文字取得")
                    return text
                except Exception as e:
                    print(f"    ❌ Google Docs抽出エラー: {e}")
                    return f"Google Docs: {file_name} (テキスト抽出エラー)"
            
            # Google Sheets形式の場合
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                try:
                    request = self.service.files().export_media(fileId=file_id, mimeType='text/csv')
                    file_content = request.execute()
                    text = file_content.decode('utf-8', errors='ignore')
                    print(f"    ✅ Google Sheets: {len(text)}文字取得")
                    return f"スプレッドシート: {file_name}\n\n{text[:2000]}"
                except Exception as e:
                    print(f"    ❌ Google Sheets抽出エラー: {e}")
                    return f"Google Sheets: {file_name} (データ抽出エラー)"
            
            # Google Slides形式の場合
            elif mime_type == 'application/vnd.google-apps.presentation':
                try:
                    request = self.service.files().export_media(fileId=file_id, mimeType='text/plain')
                    file_content = request.execute()
                    text = file_content.decode('utf-8', errors='ignore')
                    print(f"    ✅ Google Slides: {len(text)}文字取得")
                    return f"プレゼンテーション: {file_name}\n\n{text}"
                except Exception as e:
                    print(f"    ❌ Google Slides抽出エラー: {e}")
                    return f"Google Slides: {file_name} (テキスト抽出エラー)"
            
            # テキストファイルの場合
            elif 'text' in mime_type:
                try:
                    request = self.service.files().get_media(fileId=file_id)
                    file_content = request.execute()
                    text = file_content.decode('utf-8', errors='ignore')
                    print(f"    ✅ テキストファイル: {len(text)}文字取得")
                    return text
                except Exception as e:
                    print(f"    ❌ テキストファイル抽出エラー: {e}")
                    return f"テキストファイル: {file_name} (読み込みエラー)"
            
            # PDFやその他のファイル（メタ情報のみ）
            else:
                file_size = file_info.get('size', '不明')
                created_time = file_info.get('createdTime', '不明')
                modified_time = file_info.get('modifiedTime', '不明')
                
                meta_info = f"""ファイル名: {file_name}
ファイルタイプ: {mime_type}
ファイルサイズ: {file_size} bytes
作成日時: {created_time}
更新日時: {modified_time}

※このファイルはテキスト抽出に対応していませんが、メタデータを検索対象に含めています。"""
                
                print(f"    ℹ️ メタデータのみ: {file_name}")
                return meta_info
                
        except Exception as e:
            print(f"    ❌ 全般的な抽出エラー: {e}")
            return f"ファイル: {file_info.get('name', '不明')} (処理エラー: {str(e)})"
    
    def print_summary(self, documents: List[Dict]):
        """取得結果サマリー表示"""
        print("\n📊 === Google Drive 取得サマリー ===")
        
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
        
        print(f"📝 総計: {len(documents)}件")
        print("=" * 40)

