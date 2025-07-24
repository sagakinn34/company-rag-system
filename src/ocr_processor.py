"""
OCR処理モジュール
Google DriveやNotionの画像ファイルからテキストを抽出します
"""

import os
import json
import time
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from pathlib import Path

from paddleocr import PaddleOCR
from PIL import Image
import requests
from io import BytesIO

from dotenv import load_dotenv

# 環境変数の読み込み
load_dotenv()

class OCRProcessor:
    def __init__(self):
        """OCRプロセッサーを初期化"""
        
        # OCR設定を環境変数から取得
        self.language = os.getenv('OCR_LANGUAGE', 'japan')
        self.confidence_threshold = float(os.getenv('OCR_CONFIDENCE_THRESHOLD', '0.6'))
        
        try:
            # PaddleOCRを初期化（日本語対応）
            print("🤖 PaddleOCR を初期化中...")
            self.ocr = PaddleOCR(
                use_angle_cls=True,     # 文字の角度を自動補正
                lang=self.language,     # 日本語設定
                use_gpu=False,          # CPUを使用（GPUがなくても動作）
                show_log=False          # ログを簡潔に
            )
            
            # データ保存用ディレクトリ
            self.data_dir = "./data/ocr"
            self.temp_dir = os.getenv('TEMP_DIRECTORY', './temp')
            
            os.makedirs(self.data_dir, exist_ok=True)
            os.makedirs(self.temp_dir, exist_ok=True)
            
            print("✅ OCR プロセッサーを初期化しました")
            
        except Exception as e:
            print(f"❌ OCR プロセッサー初期化エラー: {e}")
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
            result = self.ocr.ocr(image_path, cls=True)
            processing_time = time.time() - start_time
            
            # 結果を解析
            extracted_text = ""
            text_details = []
            
            if result and result[0]:
                for line_data in result[0]:
                    if len(line_data) >= 2:
                        # 座標情報
                        coordinates = line_data[0]
                        
                        # テキスト情報
                        text_info = line_data[1]
                        text = text_info[0]  # 認識されたテキスト
                        confidence = text_info[1]  # 信頼度
                        
                        # 信頼度が閾値以上の場合のみ採用
                        if confidence >= self.confidence_threshold:
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
    print("=== OCR プロセッサー テスト実行 ===")
    
    try:
        processor = OCRProcessor()
        print("✅ OCRプロセッサーの初期化に成功しました")
        
    except Exception as e:
        print(f"❌ テスト実行エラー: {e}")
        print("\n🔧 トラブルシューティング:")
        print("   • 仮想環境が有効化されているか確認")
        print("   • 必要なライブラリがインストールされているか確認")

