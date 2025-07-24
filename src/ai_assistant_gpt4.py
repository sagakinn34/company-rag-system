import openai
import os
from typing import List, Dict, Any

class AIAssistant:
    def __init__(self):
        openai.api_key = os.getenv('OPENAI_API_KEY')
        
    def analyze(self, search_results: List[Dict], query: str, analysis_type: str = "summary") -> str:
        """GPT-4対応版AI分析機能（大容量トークン対応）"""
        
        # 検索結果から実際のコンテンツを抽出（制限を大幅緩和）
        content_text = self._extract_content_extended(search_results, max_chars=50000)  # 5万文字まで対応
        
        # 分析タイプに応じた専門プロンプトを生成
        prompt = self._generate_specialized_prompt(query, content_text, analysis_type)
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",  # GPT-4に変更（128Kトークン対応）
                messages=[
                    {"role": "system", "content": "あなたは企業の業務分析専門のAIアシスタントです。提供された文書内容を詳細に分析し、実用的な洞察を提供してください。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2000,  # 出力も増量
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"AI分析中にエラーが発生しました: {str(e)}"
    
    def _extract_content_extended(self, search_results: List[Dict], max_chars: int = 50000) -> str:
        """大容量対応版コンテンツ抽出"""
        contents = []
        total_chars = 0
        
        for i, result in enumerate(search_results):
            if total_chars >= max_chars:
                break
                
            if 'metadata' in result and 'content' in result:
                source = result['metadata'].get('source', '不明')
                title = result['metadata'].get('title', '無題')
                content = result['content']
                
                # 各文書の制限を大幅緩和（1文書あたり最大3000文字）
                if len(content) > 3000:
                    content = content[:3000] + "...(続きは省略)"
                
                doc_text = f"【文書{i+1}: {title} (出典: {source})】\n{content}\n\n"
                
                if total_chars + len(doc_text) > max_chars:
                    remaining_chars = max_chars - total_chars
                    if remaining_chars > 500:
                        doc_text = doc_text[:remaining_chars] + "...(制限により省略)"
                        contents.append(doc_text)
                    break
                
                contents.append(doc_text)
                total_chars += len(doc_text)
        
        return "\n".join(contents)
    
    def _generate_specialized_prompt(self, query: str, content_text: str, analysis_type: str) -> str:
        """大容量対応版プロンプト生成"""
        
        base_content = f"""以下は企業の文書から検索された内容です：

{content_text}

ユーザーの質問: {query}
"""
        
        if analysis_type == "summary":
            return base_content + """
【要約タスク】
上記の文書内容を基に、ユーザーの質問に関連する情報を包括的に要約してください。

## 📋 詳細要約結果

### 🎯 主要な内容（重要度順）
- [最も重要なポイントを詳細に記載]

### 📊 現在の状況分析
- [現在取られている手段や方法を具体的に説明]

### 📈 変遷・経緯の詳細
- [時系列での変化や発展を詳細に記載]

### 🔍 詳細情報・補足
- [その他の重要な詳細情報を網羅的に記載]

### 📋 関連文書の概要
- [参照した各文書の要点を整理]

※GPT-4の大容量処理能力を活用し、実際の内容を詳細に分析して要約してください。
"""
        
        elif analysis_type == "insights":
            return base_content + """
【示唆・洞察タスク】
上記の文書内容を深く分析し、重要な洞察を提供してください。

## 💡 深層洞察分析

### 🎯 重要な発見（詳細分析）
- [文書から読み取れる重要な発見や傾向を詳細に]

### ⚠️ 潜在的な課題（多角的分析）
- [現在の方法や状況から見える課題や問題点を多角的に]

### 🔗 関連性の詳細分析
- [異なる情報間の関連性や相互作用を詳細に]

### 📊 パターン・傾向（統計的視点）
- [データや情報から見えるパターンや傾向を統計的に]

### 🔮 将来予測・示唆
- [現在の状況から予測される将来の展開]

※大容量処理を活用した深い分析による洞察を提供してください。
"""
        
        elif analysis_type == "recommendations":
            return base_content + """
【推奨・提案タスク】
上記の文書内容に基づいて具体的で実行可能な推奨事項を詳細に提案してください。

## 🚀 詳細推奨事項

### 🎯 即座に実行可能な改善案（詳細版）
- [すぐに取り組める具体的なアクションを詳細に]

### 📈 中長期的な改善提案（戦略的視点）
- [将来的な改善のための戦略的提案を詳細に]

### 🛠️ 具体的な実施方法（ステップバイステップ）
- [推奨事項をどのように実行するかの詳細な方法]

### ⚡ 効果的な順序（優先度マトリックス）
- [推奨事項を実行する際の優先順位や順序を詳細に]

### 💰 コスト・リソース分析
- [各推奨事項に必要なコストやリソースの分析]

### 📊 効果測定方法
- [推奨事項の効果をどう測定するかの提案]

※大容量処理能力を活用し、具体的で実行可能な推奨事項を詳細に提供してください。
"""
        
        else:
            return base_content + "\n上記の内容について、GPT-4の大容量処理能力を活用して詳細に分析してください。"
