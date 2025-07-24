"""
ダミーOCR処理モジュール
OCRライブラリが使用できない場合の代替案
"""

import os
import json
from datetime import datetime

class DummyOCRProcessor:
    def __init__(self):
        """ダミーOCRプロセッサーを初期化"""
        
        # データ保存用ディレクトリ
        self.data_dir = "./data/ocr"
        os.makedirs(self.data_dir, exist_ok=True)
        
        print("✅ ダミーOCR プロセッサーを初期化しました")
        print("📝 画像処理は後日実装予定です")
    
    def process_image_file(self, image_path: str):
        """
        画像ファイルの処理（ダミー版）
        """
        if os.path.exists(image_path):
            print(f"🖼️ 画像ファイルを確認: {os.path.basename(image_path)}")
            return {
                "success": True, 
                "text": f"[画像ファイル: {os.path.basename(image_path)} - OCR処理は後日実装予定]",
                "details": []
            }
        else:
            print(f"❌ 画像ファイルが見つかりません: {image_path}")
            return {"success": False, "text": "", "details": []}

# テスト実行用
if __name__ == "__main__":
    print("=== ダミーOCR プロセッサー テスト実行 ===")
    
    processor = DummyOCRProcessor()
    print("✅ ダミーOCRプロセッサーの初期化に成功しました")
    print("📋 このバージョンはOCR機能なしで動作します")
    print("💡 NotionやGoogle Driveのテキストファイルのみ処理します")

