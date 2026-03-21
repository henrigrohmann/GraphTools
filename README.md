# GraphTools（グラフツール）

意見データの散布図・クラスタリング・階層表示を行うWebアプリケーションです。  
フロントエンド（HTML/JS）+ バックエンド（FastAPI）の統合テスト環境です。

## クイックスタート（Codespaces）

### 1. バック・フロント起動

VS Code の **Terminal** → **Run Task** で以下を順に実行:

1. **"Start FastAPI (uvicorn)"** → バックエンド (localhost:8005) 起動
2. **"Start Frontend Static Server"** → フロント (localhost:8002) 起動

### 2. ブラウザで開く

```
http://localhost:8002
```

### 3. 結合テスト実行

- **[ヘルスチェック]** をクリック → API 疎通確認
- **[生データ]** / **[クラスタリング]** などで散布図表示
- 点をクリックして詳細情報・階層ビューを確認

詳細は [INTEGRATION_TEST.md](INTEGRATION_TEST.md) と [TEST_CHECKLIST.md](TEST_CHECKLIST.md) を参照。

## ディレクトリ構成

```
GraphTools/
├── index.html                 # メイン UI
├── scatter.js                 # 散布図・詳細・階層の JS
├── api_tester.html            # API テスター画面
├── api_tester.js              # API テスター実装
├── data.js                    # （レガシー）
├── backend/
│   ├── server.py              # FastAPI メイン
│   ├── pipeline.py            # パイプライン処理
│   └── plugins/               # 処理モジュール
│       ├── loader_csv.py      # CSV 読み込み
│       ├── vectorizer_simple.py
│       ├── cluster_kmeans.py
│       ├── layout_*.py
│       ├── writer_db.py       # DB（SQLite）
│       └── hierarchy_loader.py
├── scripts/
│   └── smoke_api.py           # API スモークテスト
├── logs/
│   └── smoke/                 # テストログ出力先
├── .vscode/
│   ├── tasks.json             # VS Code タスク定義
│   └── launch.json            # デバッグ設定
├── INTEGRATION_TEST.md        # 統合テスト手順
├── TEST_CHECKLIST.md          # テストチェックリスト
└── v01/, v02/                 # 旧バージョン

```

## ポート

| サービス | ポート | 用途 |
|---------|--------|------|
| フロント (HTML) | 8002 | UI 配信 |
| バック (FastAPI) | 8005 | API サーバー |

## API エンドポイント

### パイプライン処理

- `GET /raw` → 生データを DB 保存
- `GET /random` → ランダムレイアウト計算・DB 保存
- `GET /cluster` → クラスタリング計算・DB 保存
- `GET /dense` → 密度フィルタ計算・DB 保存

### データ取得

- `GET /scatter?mode={raw|random|cluster|dense}` → 散布図データ取得
- `GET /hierarchy?mode={external|cluster|dense}` → 階層データ取得
- `GET /jobs` → 実行ジョブログ

## テスト方法

### 統合テスト（UI確認）

1. [INTEGRATION_TEST.md](INTEGRATION_TEST.md) にしたがって起動
2. ブラウザで手動確認

### スモークテスト（API確認）

```bash
# VS Code の Run Task で "Run API Smoke Test" を実行
# または CLI から:
python scripts/smoke_api.py --base-url http://127.0.0.1:8005 --log-dir logs/smoke
```

### チェックリスト

[TEST_CHECKLIST.md](TEST_CHECKLIST.md) で全テスト項目を確認。

## 依存関係

### バックエンド

```
fastapi
uvicorn
scikit-learn
numpy
pandas
```

### フロントエンド

```
Plotly.js (CDN)
```

## トラブルシューティング

### ❌ ターミナルが固まる（Codespaces）

- 新しいタスクを実行して、別のプロセスで起動
- 既存タスクは停止ボタンで終了

### ❌ API に接続できない

- バックエンド (8005) が起動しているか確認
- ポートが既に使用されていないか確認
- ファイアウォール設定を見直し

### ❌ 散布図が表示されない

1. ログパネル（下部）のエラーメッセージを確認
2. 「API Base」の表示が正しいか確認
3. ハイライト＆再読み込み（Ctrl+Shift+R）

## 今後の拡張

- [ ] 点フィルタ機能
- [ ] 詳細検索
- [ ] ダウンロード機能
- [ ] ユーザー認証
- [ ] 複数ファイル対応

## コントリビューション

フロント・バック両方のテストを統合テストで確認してから PR をお願いします。

---

**問い合わせ**: 詳細は [INTEGRATION_TEST.md](INTEGRATION_TEST.md) を参照。
