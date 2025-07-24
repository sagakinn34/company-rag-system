import os
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import json
import numpy as np

class VectorDBProcessor:
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        self.client = chromadb.PersistentClient(path=db_path)
        self.collection = self.client.get_or_create_collection(name="company_docs")
        
        # 軽量モデルを使用
        print("埋め込みモデルを読み込み中...")
        self.model = SentenceTransformer('intfloat/multilingual-e5-small')
        print("✅ モデル読み込み完了")
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """文書をベクトルデータベースに追加"""
        try:
            texts = []
            metadatas = []
            ids = []
            
            for i, doc in enumerate(documents):
                texts.append(doc['content'])
                metadatas.append({
                    'source': doc.get('source', ''),
                    'title': doc.get('title', ''),
                    'type': doc.get('type', '')
                })
                ids.append(f"doc_{i}_{hash(doc['content'])}")
            
            # テキストをベクトル化
            embeddings = self.model.encode(texts)
            
            # ★ 修正1: numpy配列を確実にリストに変換
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
            elif hasattr(embeddings, 'tolist'):
                embeddings = embeddings.tolist()
            
            # ChromaDBに追加
            self.collection.add(
                embeddings=embeddings,  # .tolist()を削除（上で処理済み）
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ {len(documents)}件の文書を追加しました")
            
        except Exception as e:
            print(f"❌ 文書追加エラー: {e}")
    
    def search(self, query: str, n_results: int = 20) -> List[Dict]:
        """ベクトル検索実行（Streamlit Cloud対応版）"""
        try:
            print("埋め込みモデルを読み込み中...")
            
            # ★ 修正2: クエリを単一文字列として処理（リストではなく）
            query_embedding = self.model.encode(query)
            
            # ★ 修正3: numpy配列を確実にリストに変換
            if isinstance(query_embedding, np.ndarray):
                query_embedding = query_embedding.tolist()
            elif hasattr(query_embedding, 'tolist'):
                query_embedding = query_embedding.tolist()
            
            print("✅ モデル読み込み完了")
            
            # 検索結果数を最大50件まで対応
            max_results = min(n_results, 50)
            
            # ★ 修正4: ChromaDBのquery_embeddingsは必ずリスト形式
            results = self.collection.query(
                query_embeddings=[query_embedding],  # 単一埋め込みをリスト内に配置
                n_results=max_results,
                include=['metadatas', 'documents', 'distances']
            )
            
            # 結果を整形
            formatted_results = []
            if results['documents'] and len(results['documents']) > 0:
                for i in range(len(results['documents'][0])):
                    formatted_results.append({
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'distance': results['distances'][0][i]
                    })
            
            return formatted_results
            
        except Exception as e:
            print(f"❌ 検索エラー: {e}")
            return []
    
    def get_collection_info(self):
        """コレクション情報を取得"""
        try:
            count = self.collection.count()
            return {"document_count": count, "status": "active"}
        except Exception as e:
            return {"document_count": 0, "status": f"error: {e}"}

    def get_stats(self):
        """統計情報を取得（互換性のため）"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "status": "success" if count > 0 else "empty"
            }
        except Exception as e:
            return {
                "total_documents": 0,
                "status": f"error: {e}"
            }
