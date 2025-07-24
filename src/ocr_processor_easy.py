"""
EasyOCR処理モジュール
Google DriveやNotionの画像ファイルからテキストを抽出します（EasyOCR版）
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional

try:
    import easyocr
    EASYOCR_AVAILABLE = True
except ImportError:
    EASYOCR_AVAILABLE = False

from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

class EasyOCRProcessor:
    def __init__(self):
        """EasyOCRプロセッサーを初期化"""
        
        if not EASYOCR_AVAILABLE:
            print("❌ EasyOCRがインストールされていません")
            print("💡 pip install easyocr でインストールしてください")
            raise ImportError("EasyOCR is not available")
        
        try:
            # EasyOCRを初期化（日本語+英語対応）
            print("🤖 EasyOCR を初期化中...")
            self.reader = easyocr.Reader(['ja', 'en'], gpu=False)
            
            # データ保存用ディレクトリ
            self.data_dir = "./data/ocr"
            self.temp_dir = os.getenv('TEMP_DIRECTORY', './temp')
            
            os.makedirs(self.data_dir, exist_ok=True)
            os.makedirs(self.temp_dir, exist_ok=True)
            
            print("✅ EasyOCR プロセッサーを初期化しました")
            
        except Exception as e:
            print(f"❌ EasyOCR プロセッサー初期化エラー: {e}")
            raise
    
    def process_image_file(self, image_path: str) -> Dict:
        """
        ローカル画像ファイルからテキストを抽出
        
        Args:
            image_path: 画像ファイルのパス
            
        Returns:
            抽出結果の辞書
        """
        if not os.path.exists(image_path):
            print(f"❌ 画像ファイルが見つかりません: {image_path}")
            return {"success": False, "text": "", "details": []}
        
        print(f"🖼️ 画像を処理中: {os.path.basename(image_path)}")
        
        try:
            # OCR実行
            start_time = time.time()
            results = self.reader.readtext(image_path)
            processing_time = time.time() - start_time
            
            # 結果を解析
            extracted_text = ""
            text_details = []
            
            for result in results:
                coordinates = result[0]  # 座標情報
                text = result[1]         # 認識されたテキスト
                confidence = result[2]   # 信頼度
                
                # 信頼度が0.3以上の場合のみ採用
                if confidence >= 0.3:
                    extracted_text += text + "\n"
                    
                    text_details.append({
                        "text": text,
                        "confidence": round(confidence, 3),
                        "coordinates": coordinates
                    })
            
            result_data = {
                "success": True,
                "text": extracted_text.strip(),
                "details": text_details,
                "processing_time": round(processing_time, 2),
                "total_lines": len(text_details),
                "average_confidence": round(
                    sum(d["confidence"] for d in text_details) / len(text_details)
                    if text_details else 0, 3
                )
            }
            
            print(f"✅ OCR完了: {result_data['total_lines']} 行, "
                  f"平均信頼度 {result_data['average_confidence']}, "
                  f"{result_data['processing_time']}秒")
            
            return result_data
            
        except Exception as e:
            print(f"❌ OCR処理エラー ({os.path.basename(image_path)}): {e}")
            return {"success": False, "text": "", "details": [], "error": str(e)}

# テスト実行用
if __name__ == "__main__":
    print("=== EasyOCR プロセッサー テスト実行 ===")
    
    try:
        processor = EasyOCRProcessor()
        print("✅ EasyOCRプロセッサーの初期化に成功しました")
        print("📋 OCR機能が正常に利用可能です")
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        print("\n🔧 トラブルシューティング:")
        print("   • pip install easyocr でEasyOCRをインストール")
        print("   • pip install opencv-python でOpenCVをインストール")
        print("   • インターネット接続を確認（初回実行時はモデルをダウンロードします）")

