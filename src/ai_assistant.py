#!/usr/bin/env python3
"""
AI搭載RAGシステム - NotebookLM風機能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from vector_db_processor import VectorDBProcessor
import openai
from typing import List, Dict
import json
from dotenv import load_dotenv

class AIAssistant:
    def __init__(self):
        # 環境変数読み込み
        load_dotenv()
        
        # OpenAI API設定
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        if not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY環境変数が設定されていません")
        
        openai.api_key = self.openai_api_key
        
        # RAGシステム初期化
        self.rag_processor = VectorDBProcessor()
        
    def search_and_analyze(self, query: str, analysis_type: str = "summary") -> Dict:
        """
        検索結果をAIで分析
        """
        # 1. RAG検索実行
        search_results = self.rag_processor.search_documents(query, n_results=5)
        
        if not search_results or not search_results.get('results'):
            return {"error": "検索結果が見つかりませんでした"}
        
        # 2. 検索結果をテキストにまとめ
        context_text = self._format_search_results(search_results['results'])
        
        # 3. AI分析実行
        analysis = self._analyze_with_ai(query, context_text, analysis_type)
        
        return {
            "query": query,
            "analysis_type": analysis_type,
            "search_results_count": len(search_results['results']),
            "analysis": analysis,
            "sources": [r['metadata'].get('title', '無題') for r in search_results['results']]
        }
    
    def _format_search_results(self, results: List[Dict]) -> str:
        """検索結果をAI分析用にフォーマット"""
        formatted_text = ""
        
        for i, result in enumerate(results, 1):
            title = result['metadata'].get('title', f'文書{i}')
            source = result['metadata'].get('source', '不明')
            content = result['content']
            
            formatted_text += f"\n=== 文書{i}: {title} (出典: {source}) ===\n"
            formatted_text += content
            formatted_text += "\n\n"
        
        return formatted_text
    
    def _analyze_with_ai(self, query: str, context: str, analysis_type: str) -> str:
        """OpenAI APIで分析実行"""
        
        # 分析タイプ別のプロンプト
        prompts = {
            "summary": f"""
以下の検索結果を基に、「{query}」に関する包括的な要約を日本語で作成してください。

重要なポイント：
- 主要な情報を整理して簡潔にまとめる
- 複数の文書から得られた情報を統合する
- 具体的な数値や事実があれば含める

検索結果:
{context}

要約:
""",
            "insights": f"""
以下の検索結果を分析し、「{query}」に関する洞察・示唆を日本語で提供してください。

分析観点：
- データから読み取れるトレンドや傾向
- 隠れた課題や機会
- 関連する要因や影響
- 今後の展望や予測

検索結果:
{context}

洞察・示唆:
""",
            "recommendations": f"""
以下の検索結果を基に、「{query}」に関する具体的な提案・推奨事項を日本語で作成してください。

提案内容：
- 改善すべき点
- 取るべきアクション
- 優先順位の高い施策
- 実行時の注意点

検索結果:
{context}

提案・推奨事項:
"""
        }
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",  # より安価なモデルを使用
                messages=[
                    {"role": "system", "content": "あなたは企業データ分析の専門家です。提供された情報を基に、的確で実用的な分析を行ってください。"},
                    {"role": "user", "content": prompts.get(analysis_type, prompts["summary"])}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            return f"AI分析エラー: {str(e)}"

def main():
    print("🤖 AI搭載RAGシステム")
    print("=" * 50)
    
    try:
        assistant = AIAssistant()
        print("✅ AIアシスタントを初期化しました")
    except Exception as e:
        print(f"❌ 初期化エラー: {e}")
        print("OpenAI APIキーが正しく設定されているか確認してください")
        return
    
    print("\n🔍 AI分析モード:")
    print("1. summary - 要約")
    print("2. insights - 洞察・示唆") 
    print("3. recommendations - 提案・推奨")
    print("-" * 50)
    
    while True:
        try:
            query = input("\n🔍 分析したい内容を入力: ").strip()
            
            if query.lower() in ['quit', 'exit', '終了']:
                print("👋 AIアシスタントを終了します")
                break
            
            if not query:
                continue
            
            # 分析タイプ選択
            analysis_type = input("分析タイプ (summary/insights/recommendations): ").strip()
            if analysis_type not in ['summary', 'insights', 'recommendations']:
                analysis_type = 'summary'
            
            print(f"\n🤖 AI分析中: '{query}' ({analysis_type})")
            
            # AI分析実行
            result = assistant.search_and_analyze(query, analysis_type)
            
            if "error" in result:
                print(f"❌ {result['error']}")
                continue
            
            # 結果表示
            print(f"\n✅ AI分析結果 ({result['search_results_count']}件の文書を分析):")
            print("=" * 60)
            print(result['analysis'])
            print("\n📚 参照文書:")
            for source in result['sources']:
                print(f"  - {source}")
            print("-" * 60)
            
        except KeyboardInterrupt:
            print("\n\n👋 AIアシスタントを終了します")
            break
        except Exception as e:
            print(f"❌ エラー: {e}")
            continue

if __name__ == "__main__":
    main()
