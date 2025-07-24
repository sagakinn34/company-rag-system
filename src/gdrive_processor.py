def get_all_files(self) -> List[Dict]:
    """診断機能付きファイル取得"""
    if not self.service:
        print("❌ Google Drive サービスが初期化されていません")
        return []
    
    try:
        # 段階1: 基本アクセステスト
        print("🔍 Google Drive アクセステスト中...")
        basic_results = self.service.files().list(
            pageSize=5,
            fields="files(id, name, mimeType)"
        ).execute()
        
        basic_files = basic_results.get('files', [])
        print(f"✅ 基本アクセス成功: {len(basic_files)} 件のファイルが見つかりました")
        
        if not basic_files:
            print("⚠️ Google Driveにアクセス可能なファイルがありません")
            print("📝 確認事項:")
            print("   1. Service Accountにファイルが共有されているか")
            print("   2. 適切なフォルダアクセス権限があるか")
            return []
        
        # より広範囲な検索
        documents = []
        search_queries = [
            "trashed=false",  # 全ファイル
            "trashed=false and (mimeType contains 'text' or mimeType contains 'document')",  # テキスト・文書系
            "trashed=false and mimeType='application/vnd.google-apps.document'",  # Google Docs
        ]
        
        for i, query in enumerate(search_queries):
            print(f"🔍 検索段階 {i+1}: {query}")
            # ... 検索実行

