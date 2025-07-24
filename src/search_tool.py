#!/usr/bin/env python3
"""
RAGシステム検索ツール - 最終版
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vector_db_processor import VectorDBProcessor

def main():
    print("🔍 RAGシステム検索ツール")
    print("=" * 50)
    
    # システム初期化
    try:
        processor = VectorDBProcessor()
        print("✅ 検索システムを初期化しました")
        
        # データベース統計表示
        collection = processor.collection
        count = collection.count()
        print(f"📊 検索可能ドキュメント数: {count}")
        
        if count == 0:
            print("❌ データが見つかりません。先にデータ統合を実行してください。")
            return
        elif count <= 2:
            print("⚠️  テストデータのみです。実データの統合が必要な可能性があります。")
            
    except Exception as e:
        print(f"❌ システム初期化エラー: {e}")
        return
    
    print("\n🔍 検索を開始します")
    print("終了するには 'quit' または 'exit' と入力してください")
    print("-" * 50)
    
    while True:
        try:
            # 検索クエリ入力
            query = input("\n🔍 検索したい内容を入力してください: ").strip()
            
            # 終了条件
            if query.lower() in ['quit', 'exit', '終了', 'q']:
                print("👋 検索を終了します")
                break
            
            if not query:
                print("❌ 検索内容を入力してください")
                continue
            
            # 検索実行
            print(f"\n🔍 検索中: '{query}'")
            search_result = processor.search_documents(query, n_results=3)
            
            if not search_result or not search_result.get('results'):
                print("❌ 検索結果が見つかりませんでした")
                continue
            
            # 結果表示
            results = search_result['results']
            total_results = search_result.get('total_results', len(results))
            
            print(f"\n✅ {total_results}件の結果が見つかりました:")
            print("=" * 60)
            
            for i, result in enumerate(results, 1):
                content = result['content']
                if len(content) > 300:
                    content = content[:300] + "..."
                
                metadata = result.get('metadata', {})
                source = metadata.get('source', '不明')
                title = metadata.get('title', '無題')
                distance = result.get('distance', 0)
                
                # 関連度を100点満点で計算（距離が小さいほど高い関連度）
                relevance = max(0, 100 - distance * 5)
                
                print(f"\n【結果 {i}】")
                print(f"📄 タイトル: {title}")
                print(f"📁 ソース: {source}")
                print(f"🎯 関連度: {relevance:.1f}/100")
                print(f"📝 内容: {content}")
                print("-" * 40)
            
        except KeyboardInterrupt:
            print("\n\n👋 検索を終了します")
            break
        except Exception as e:
            print(f"❌ 検索エラー: {e}")
            continue

if __name__ == "__main__":
    main()
