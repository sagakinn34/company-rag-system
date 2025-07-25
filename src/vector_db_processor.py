import os
import sys

# Streamlit Cloud環境でのSQLite3問題を強制的に解決
def fix_sqlite3():
    """SQLite3バージョン問題を強制的に修正"""
    try:
        import pysqlite3
        sys.modules['sqlite3'] = pysqlite3
        print("✅ pysqlite3を強制適用しました")
    except ImportError:
        print("⚠️ pysqlite3が見つかりません - 標準sqlite3を使用")

# ChromaDBインポート前にSQLite3を修正
fix_sqlite3()

import chromadb
from typing import List, Dict, Any
import json
import numpy as np

def create_sentence_transformer():
    """埋め込みモデルを安全に作成（全バージョン対応）"""
    try:
        from sentence_transformers import SentenceTransformer
        import torch
        
        print("埋め込みモデルを読み込み中...")
        
        # デバイス設定
        device = 'cpu'  # Streamlit Cloudでは安全にCPUを使用
        
        # モデル初期化（バージョン互換性考慮）
        try:
            # 最新バージョン用の初期化
            model = SentenceTransformer(
                'intfloat/multilingual-e5-small',
                device=device,
                trust_remote_code=False,
                cache_folder=None
            )
        except Exception as e1:
            print(f"⚠️ 新形式での初期化失敗: {e1}")
            try:
                # 従来形式での初期化
                model = SentenceTransformer('intfloat/multilingual-e5-small')
                model = model.to(device)
            except Exception as e2:
                print(f"⚠️ 従来形式でも失敗: {e2}")
                # より軽量なモデルにフォールバック
                print("🔄 軽量モデルにフォールバック...")
                model = SentenceTransformer('all-MiniLM-L6-v2')
                model = model.to(device)
        
        print("✅ モデル読み込み完了")
        return model
        
    except ImportError as e:
        print(f"❌ SentenceTransformersインポートエラー: {e}")
        return None
    except Exception as e:
        print(f"❌ モデル読み込みエラー: {e}")
        return None

class VectorDBProcessor:
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        self.client = None
        self.collection = None
        self.model = None
        
        # ChromaDB初期化
        self._init_chromadb()
        
        # 埋め込みモデル初期化
        if self.collection:
            self.model = create_sentence_transformer()
    
    def _init_chromadb(self):
        """ChromaDBクライアントを初期化"""
        try:
            print("ChromaDBクライアントを初期化中...")
            self.client = chromadb.PersistentClient(path=self.db_path)
            self.collection = self.client.get_or_create_collection(
                name="company_docs",
                metadata={"hnsw:space": "cosine"}
            )
            print("✅ ChromaDBクライアント初期化成功")
        except Exception as e:
            print(f"❌ ChromaDB永続化初期化エラー: {e}")
            try:
                print("🔄 インメモリモードにフォールバック中...")
                self.client = chromadb.Client()
                self.collection = self.client.get_or_create_collection(
                    name="company_docs",
                    metadata={"hnsw:space": "cosine"}
                )
                print("✅ インメモリモード初期化成功")
            except Exception as e2:
                print(f"❌ フォールバック失敗: {e2}")
                self.client = None
                self.collection = None
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """文書をベクトルデータベースに追加"""
        if not self.collection:
            print("❌ ChromaDBが初期化されていません")
            return
        
        if not self.model:
            print("❌ 埋め込みモデルが利用できません")
            return
        
        try:
            texts = []
            metadatas = []
            ids = []
            
            for i, doc in enumerate(documents):
                content = str(doc.get('content', ''))[:8000]  # 長すぎるコンテンツを制限
                texts.append(content)
                metadatas.append({
                    'source': str(doc.get('source', '')),
                    'title': str(doc.get('title', '')),
                    'type': str(doc.get('type', ''))
                })
                ids.append(f"doc_{i}_{abs(hash(content))}")
            
            print(f"📝 {len(texts)}件の文書をベクトル化中...")
            
            # バッチ処理でメモリ使用量を制限
            batch_size = 16
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                try:
                    # エンコーディング実行
                    batch_embeddings = self.model.encode(
                        batch_texts,
                        show_progress_bar=False,
                        convert_to_numpy=True,
                        normalize_embeddings=True
                    )
                    
                    # numpy配列をリストに変換
                    if isinstance(batch_embeddings, np.ndarray):
                        batch_embeddings = batch_embeddings.tolist()
                    
                    all_embeddings.extend(batch_embeddings)
                    print(f"✅ バッチ {i//batch_size + 1} 完了")
                    
                except Exception as e:
                    print(f"❌ バッチ処理エラー: {e}")
                    # ダミーベクトルで代替
                    dummy_dim = 384  # 一般的な次元数
                    dummy_vectors = [[0.0] * dummy_dim] * len(batch_texts)
                    all_embeddings.extend(dummy_vectors)
            
            # ChromaDBに追加
            self.collection.add(
                embeddings=all_embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ {len(documents)}件の文書をChromaDBに追加しました")
            
        except Exception as e:
            print(f"❌ 文書追加エラー: {e}")
    
    def search(self, query: str, n_results: int = 20) -> List[Dict]:
        """ベクトル検索実行"""
        if not self.collection:
            print("❌ ChromaDBが初期化されていません")
            return []
        
        try:
            max_results = min(n_results, 50)
            
            if self.model:
                # ベクトル検索
                query_embedding = self.model.encode([query], normalize_embeddings=True)[0]
                if isinstance(query_embedding, np.ndarray):
                    query_embedding = query_embedding.tolist()
                
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=max_results,
                    include=['metadatas', 'documents', 'distances']
                )
            else:
                # キーワード検索フォールバック
                print("⚠️ 埋め込みモデル利用不可 - キーワード検索を実行")
                all_docs = self.collection.get()
                matched_docs = []
                
                query_lower = query.lower()
                for i, doc in enumerate(all_docs['documents']):
                    if query_lower in doc.lower():
                        matched_docs.append({
                            'content': doc,
                            'metadata': all_docs['metadatas'][i],
                            'distance': 0.5
                        })
                
                return matched_docs[:max_results]
            
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

