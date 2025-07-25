import os
import sys

# Streamlit Cloud環境でのSQLite3問題を強制的に解決
def fix_sqlite3():
    """SQLite3バージョン問題を強制的に修正"""
    try:
        # pysqlite3を強制的に使用
        import pysqlite3
        sys.modules['sqlite3'] = pysqlite3
        print("✅ pysqlite3を強制適用しました")
    except ImportError:
        print("⚠️ pysqlite3が見つかりません - 標準sqlite3を使用")

# ChromaDBインポート前にSQLite3を修正
fix_sqlite3()

import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import json
import numpy as np

class VectorDBProcessor:
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        
        try:
            # ChromaDBクライアントを初期化（修正版）
            print("ChromaDBクライアントを初期化中...")
            self.client = chromadb.PersistentClient(path=db_path)
            self.collection = self.client.get_or_create_collection(name="company_docs")
            print("✅ ChromaDBクライアント初期化成功")
        except Exception as e:
            print(f"❌ ChromaDB初期化エラー: {e}")
            # フォールバック: インメモリモード
            try:
                print("インメモリモードにフォールバック中...")
                self.client = chromadb.Client()
                self.collection = self.client.get_or_create_collection(name="company_docs")
                print("✅ インメモリモード初期化成功")
            except Exception as e2:
                print(f"❌ フォールバック失敗: {e2}")
                self.client = None
                self.collection = None
                return
        
        # 埋め込みモデル初期化
        try:
            print("埋め込みモデルを読み込み中...")
            self.model = SentenceTransformer('intfloat/multilingual-e5-small')
            print("✅ モデル読み込み完了")
        except Exception as e:
            print(f"❌ モデル読み込みエラー: {e}")
            self.model = None
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """文書をベクトルデータベースに追加"""
        if not self.collection or not self.model:
            print("❌ VectorDBProcessor が正常に初期化されていません")
            return
        
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
            
            # エラー修正: numpy配列をリストに変換
            if isinstance(embeddings, np.ndarray):
                embeddings = embeddings.tolist()
            elif hasattr(embeddings, 'tolist'):
                embeddings = embeddings.tolist()
            
            # ChromaDBに追加
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ {len(documents)}件の文書を追加しました")
            
        except Exception as e:
            print(f"❌ 文書追加エラー: {e}")
    
    def search(self, query: str, n_results: int = 20) -> List[Dict]:
        """ベクトル検索実行"""
        if not self.collection or not self.model:
            print("❌ VectorDBProcessor が正常に初期化されていません")
            return []
        
        try:
            # クエリのembedding生成
            query_embedding = self.model.encode(query)
            
            # エラー修正: numpy配列をリストに変換
            if isinstance(query_embedding, np.ndarray):
                query_embedding = query_embedding.tolist()
            elif hasattr(query_embedding, 'tolist'):
                query_embedding = query_embedding.tolist()
            
            # 検索結果数を最大50件まで対応
            max_results = min(n_results, 50)
            
            # 検索実行
            results = self.collection.query(
                query_embeddings=[query_embedding],
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
        if not self.collection:
            return {"document_count": 0, "status": "error: not initialized"}
        
        try:
            count = self.collection.count()
            return {"document_count": count, "status": "active"}
        except Exception as e:
            return {"document_count": 0, "status": f"error: {e}"}

    def get_stats(self):
        """統計情報を取得"""
        if not self.collection:
            return {"total_documents": 0, "status": "error: not initialized"}
        
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

