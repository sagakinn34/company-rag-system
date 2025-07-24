"""
Google Drive データ処理モジュール - 完全版
Google Drive から各種文書を取得し、テキストを抽出します
PDF、Word、Excel、PowerPoint に対応
"""

import streamlit as st
import json
import io
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# PDF/Office文書処理用ライブラリ
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import openpyxl
    EXCEL_AVAILABLE = True
except ImportError:
    EXCEL_AVAILABLE = False

try:
    from pptx import Presentation
    PPTX_AVAILABLE = True
except ImportError:
    PPTX_AVAILABLE = False

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
            
            # AttrDict → 辞書変換
            if hasattr(creds_dict, '_data'):
                creds_dict = dict(creds_dict._data)
            else:
                creds_dict = dict(creds_dict)
            
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
    
    def extract_text_from_pdf(self, file_content: bytes) -> str:
        """PDFファイルからテキストを抽出"""
        if not PDF_AVAILABLE:
            return "PDFテキスト抽出機能は利用できません（PyPDF2未インストール）"
        
        try:
            pdf_file = io.BytesIO(file_content)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
        except Exception as e:
            print(f"❌ PDF テキスト抽出エラー: {e}")
            return f"PDFテキスト抽出エラー: {e}"
    
    def extract_text_from_docx(self, file_content: bytes) -> str:
        """Word文書からテキストを抽出"""
        if not DOCX_AVAILABLE:
            return "Word文書テキスト抽出機能は利用できません（python-docx未インストール）"
        
        try:
            doc_file = io.BytesIO(file_content)
            doc = Document(doc_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
        except Exception as e:
            print(f"❌ Word テキスト抽出エラー: {e}")
            return f"Word文書テキスト抽出エラー: {e}"
    
    def extract_text_from_xlsx(self, file_content: bytes) -> str:
        """Excelファイルからテキストを抽出"""
        if not EXCEL_AVAILABLE:
            return "Excelファイルテキスト抽出機能は利用できません（openpyxl未インストール）"
        
        try:
            excel_file = io.BytesIO(file_content)
            workbook = openpyxl.load_workbook(excel_file)
            
            text = ""
            for sheet_name in workbook.sheetnames:
                sheet = workbook[sheet_name]
                text += f"=== {sheet_name} ===\n"
                
                for row in sheet.iter_rows(values_only=True):
                    row_text = []
                    for cell in row:
                        if cell is not None:
                            row_text.append(str(cell))
                    if row_text:
                        text += "\t".join(row_text) + "\n"
                
                text += "\n"
            
            return text.strip()
        except Exception as e:
            print(f"❌ Excel テキスト抽出エラー: {e}")
            return f"Excelファイルテキスト抽出エラー: {e}"
    
    def extract_text_from_pptx(self, file_content: bytes) -> str:
        """PowerPointファイルからテキストを抽出"""
        if not PPTX_AVAILABLE:
            return "PowerPointファイルテキスト抽出機能は利用できません（python-pptx未インストール）"
        
        try:
            ppt_file = io.BytesIO(file_content)
            presentation = Presentation(ppt_file)
            
            text = ""
            for i, slide in enumerate(presentation.slides):
                text += f"=== スライド {i+1} ===\n"
                
                for shape in slide.shapes:
                    if hasattr(shape, "text"):
                        text += shape.text + "\n"
                
                text += "\n"
            
            return text.strip()
        except Exception as e:
            print(f"❌ PowerPoint テキスト抽出エラー: {e}")
            return f"PowerPointファイルテキスト抽出エラー: {e}"
    
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
            
            # ファイルタイプに応じてテキスト抽出
            if mime_type == 'application/pdf':
                return self.extract_text_from_pdf(file_content)
            elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
                return self.extract_text_from_docx(file_content)
            elif mime_type == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet':
                return self.extract_text_from_xlsx(file_content)
            elif mime_type == 'application/vnd.openxmlformats-officedocument.presentationml.presentation':
                return self.extract_text_from_pptx(file_content)
            elif 'google-apps' in mime_type:
                # Google Docs形式はプレーンテキストとして処理
                return file_content.decode('utf-8')
            else:
                # その他はプレーンテキストとして試行
                try:
                    return file_content.decode('utf-8')
                except:
                    return file_content.decode('utf-8', errors='ignore')
        
        except Exception as e:
            print(f"❌ ファイルダウンロード・テキスト抽出エラー: {e}")
            return f"ファイルエラー: {e}"
    
    def get_all_files(self) -> List[Dict]:
        """全ファイルを処理してドキュメント形式で返す"""
        if not self.service:
            print("❌ Google Drive サービスが初期化されていません")
            return []
        
        try:
            print("🔍 Google Drive ファイル処理を開始...")
            
            # 対応ファイルタイプでの検索
            file_types_query = " or ".join([
                "mimeType='application/pdf'",
                "mimeType='application/vnd.openxmlformats-officedocument.wordprocessingml.document'",
                "mimeType='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'",
                "mimeType='application/vnd.openxmlformats-officedocument.presentationml.presentation'",
                "mimeType='application/vnd.google-apps.document'",
                "mimeType='application/vnd.google-apps.spreadsheet'",
                "mimeType='application/vnd.google-apps.presentation'",
                "mimeType contains 'text'"
            ])
            
            results = self.service.files().list(
                q=f"trashed=false and ({file_types_query})",
                pageSize=50,
                fields="files(id, name, mimeType, size, createdTime, modifiedTime)"
            ).execute()
            
            files = results.get('files', [])
            print(f"📁 {len(files)} 件のファイルが見つかりました")
            
            documents = []
            
            for file_info in files:
                print(f"📄 処理中: {file_info['name']}")
                
                # テキストを抽出
                text = self.download_and_extract_text(file_info['id'], file_info['mimeType'])
                
                if text and text.strip():
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
                else:
                    print(f"⚠️ テキスト抽出失敗: {file_info['name']}")
            
            print(f"🎉 Google Drive 処理完了: {len(documents)} 件のドキュメント")
            return documents
            
        except Exception as e:
            print(f"❌ Google Drive ファイル処理エラー: {e}")
            return []


