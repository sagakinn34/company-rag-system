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
from typing import List, Dict, Any
import json
import numpy as np

# SentenceTransformers の互換性修正
def create_sentence_transformer():
    """埋め込みモデルを安全に作成"""
    try:
        # 最新バージョン対応の初期化方法
        from sentence_transformers import SentenceTransformer
        
        print("埋め込みモデルを読み込み中...")
        
        # PyTorch互換性修正
        import torch
        if hasattr(torch.nn.Module, 'to_empty'):
            # 新しいPyTorchの場合の修正
            model = SentenceTransformer('intfloat/multilingual-e5-small', 
                                      device='cpu',  # CPUを明示的に指定
                                      trust_remote_code=True)
        else:
            # 従来の方法
            model = SentenceTransformer('intfloat/multilingual-e5-small')
        
        print("✅ モデル読み込み完了")
        return model
        
    except Exception as e:
        print(f"❌ モデル読み込みエラー: {e}")
        
        # フォールバック: より軽量なモデルを試行
        try:
            print("⚡ 軽量モデルにフォールバック中...")
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
            print("✅ 軽量モデル読み込み完了")
            return model
        except Exception as e2:
            print(f"❌ 軽量モデルも失敗: {e2}")
            return None

class VectorDBProcessor:
    def __init__(self, db_path: str = "./chroma_db"):
        self.db_path = db_path
        
        try:
            # ChromaDBクライアントを初期化
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
                self.model = None
                return
        
        # 埋め込みモデル初期化（修正版）
        self.model = create_sentence_transformer()
    
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
            
            # テキストをベクトル化（バッチサイズ制限）
            batch_size = 32  # メモリ使用量を制限
            all_embeddings = []
            
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                print(f"バッチ処理中: {i+1}-{min(i+batch_size, len(texts))}/{len(texts)}")
                
                try:
                    batch_embeddings = self.model.encode(batch_texts, 
                                                       show_progress_bar=False,
                                                       convert_to_numpy=True)
                    
                    # numpy配列をリストに変換
                    if isinstance(batch_embeddings, np.ndarray):
                        batch_embeddings = batch_embeddings.tolist()
                    
                    all_embeddings.extend(batch_embeddings)
                    
                except Exception as e:
                    print(f"❌ バッチ{i//batch_size + 1}の処理エラー: {e}")
                    # ダミーベクトルで代替
                    dummy_vector = [0.0] * 384  # モデルの次元数
                    all_embeddings.extend([dummy_vector] * len(batch_texts))
            
            # ChromaDBに追加
            self.collection.add(
                embeddings=all_embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            print(f"✅ {len(documents)}件の文書を追加しました")
            
        except Exception as e:
            print(f"❌ 文書追加エラー: {e}")
    
    def search(self, query: str, n_results: int = 20) -> List[Dict]:
        """ベクトル検索実行"""
        if not self.collection:
            print("❌ ChromaDBが初期化されていません")
            return []
        
        if not self.model:
            print("❌ 埋め込みモデルが利用できません - キーワード検索にフォールバック")
            # キーワード検索のフォールバック
            try:
                # ChromaDBの全文書を取得してキーワードマッチング
                all_docs = self.collection.get()
                matched_docs = []
                
                query_lower = query.lower()
                for i, doc in enumerate(all_docs['documents']):
                    if query_lower in doc.lower():
                        matched_docs.append({
                            'content': doc,
                            'metadata': all_docs['metadatas'][i],
                            'distance': 0.5  # ダミーの距離値
                        })
                
                return matched_docs[:n_results]
            except Exception as e:
                print(f"❌ キーワード検索エラー: {e}")
                return []
        
        try:
            # クエリのembedding生成
            query_embedding = self.model.encode(query, convert_to_numpy=True)
            
            # numpy配列をリストに変換
            if isinstance(query_embedding, np.ndarray):
                query_embedding = query_embedding.tolist()
            
            # 検索実行
            max_results = min(n_results, 50)
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


