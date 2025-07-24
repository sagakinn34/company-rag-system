import sys
sys.path.append('src')
import os
import importlib

def get_correct_class_name():
    """正しいクラス名を動的に検出"""
    try:
        with open('src/gdrive_processor.py', 'r') as f:
            content = f.read()
            
        # class で始まる行を探す
        for line in content.split('\n'):
            if line.strip().startswith('class ') and ':' in line:
                class_name = line.strip().split('class ')[1].split('(')[0].split(':')[0].strip()
                if class_name and class_name != 'object':
                    return class_name
        return None
    except Exception as e:
        print(f"クラス名検出エラー: {e}")
        return None

def safe_integration():
    print("🚀 修正版データ統合を開始...")
    
    try:
        documents = []
        
        # Notionプロセッサー
        print("📝 Notionからデータ取得中...")
        try:
            from notion_processor import NotionProcessor
            notion = NotionProcessor()
            notion_docs = notion.get_all_pages()
            if notion_docs:
                documents.extend(notion_docs)
                print(f"✅ Notion: {len(notion_docs)}件取得成功")
            else:
                print("⚠️ Notionデータが空です")
        except Exception as e:
            print(f"❌ Notion取得エラー: {e}")
        
        # Google Driveプロセッサー（動的クラス名検出）
        print("📂 Google Driveからデータ取得中...")
        try:
            # 正しいクラス名を取得
            gdrive_class_name = get_correct_class_name()
            print(f"🔍 検出されたクラス名: {gdrive_class_name}")
            
            if gdrive_class_name:
                # 動的インポート
                gdrive_module = importlib.import_module('gdrive_processor')
                GDriveClass = getattr(gdrive_module, gdrive_class_name)
                
                gdrive = GDriveClass()
                gdrive_docs = gdrive.get_all_files()
                if gdrive_docs:
                    documents.extend(gdrive_docs)
                    print(f"✅ Google Drive: {len(gdrive_docs)}件取得成功")
                else:
                    print("⚠️ Google Driveデータが空です")
            else:
                print("❌ Google Driveクラス名を検出できませんでした")
        except Exception as e:
            print(f"❌ Google Drive取得エラー: {e}")
        
        # ベクトルDBに追加
        if documents:
            print(f"🔄 {len(documents)}件をベクトルDBに統合中...")
            from vector_db_processor import VectorDBProcessor
            vector_db = VectorDBProcessor()
            vector_db.add_documents(documents)
            
            # 確認
            final_count = vector_db.collection.count()
            print(f"🎉 統合完了! データベース件数: {final_count}件")
            return True
        else:
            print("❌ 統合するデータがありません")
            return False
            
    except Exception as e:
        print(f"❌ 統合エラー: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    safe_integration()
