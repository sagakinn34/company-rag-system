#!/usr/bin/env python3
"""
メモリ効率的なデータ統合プロセッサー
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vector_db_processor import VectorDBProcessor
import json
import time
from datetime import datetime

def load_collected_data():
    """収集済みデータを読み込み"""
    try:
        # 最新の統計ファイルを探す
        stats_files = [f for f in os.listdir('./data/results/') if f.startswith('collection_stats_')]
        if not stats_files:
            print("❌ 統計ファイルが見つかりません")
            return None
            
        latest_stats = sorted(stats_files)[-1]
        stats_path = f'./data/results/{latest_stats}'
        
        with open(stats_path, 'r', encoding='utf-8') as f:
            stats = json.load(f)
            
        # 対応するデータファイルを読み込み
        timestamp = latest_stats.replace('collection_stats_', '').replace('.json', '')
        data_file = f'./data/results/all_documents_{timestamp}.json'
        
        if not os.path.exists(data_file):
            print(f"❌ データファイルが見つかりません: {data_file}")
            return None
            
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"✅ データ読み込み完了: {len(data)}件")
        return data
        
    except Exception as e:
        print(f"❌ データ読み込みエラー: {e}")
        return None

def process_in_batches(data, batch_size=20):
    """バッチ処理でデータを保存"""
    if not data:
        print("❌ 処理するデータがありません")
        return False
        
    try:
        processor = VectorDBProcessor()
        
        total_batches = (len(data) + batch_size - 1) // batch_size
        print(f"📊 {len(data)}件のデータを{batch_size}件ずつ{total_batches}バッチで処理します")
        
        for i in range(0, len(data), batch_size):
            batch = data[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            print(f"\n📦 バッチ {batch_num}/{total_batches} 処理中... ({len(batch)}件)")
            
            # バッチ処理
            processor.add_documents(batch)
            
            print(f"✅ バッチ {batch_num} 完了")
            
            # メモリ解放のための短い休憩
            time.sleep(1)
            
            # 進捗確認
            current_count = processor.collection.count()
            print(f"📊 現在のDB文書数: {current_count}件")
        
        final_count = processor.collection.count()
        print(f"\n🎉 全データの統合完了！")
        print(f"📊 最終データベース文書数: {final_count}件")
        
        return True
        
    except Exception as e:
        print(f"❌ バッチ処理エラー: {e}")
        return False

def main():
    print("🔄 メモリ効率的データ統合を開始します")
    print("=" * 50)
    
    # データ読み込み
    data = load_collected_data()
    if not data:
        return
    
    # バッチ処理で統合
    success = process_in_batches(data, batch_size=15)  # さらに小さなバッチ
    
    if success:
        print("\n✅ データ統合が正常に完了しました！")
        print("🚀 システム使用準備完了")
    else:
        print("\n❌ データ統合でエラーが発生しました")

if __name__ == "__main__":
    main()
