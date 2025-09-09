# GitHub Users Analysis Tools

このプロジェクトには、GitHubでユーザーやOrganizationメンバーを取得し、コントリビューション分析を行うツールセットが含まれています。

## 📁 ファイル構成

**メインツール:**
- `github_users_enhanced.py` - ユーザー/Organization検索
- `github_batch_analyzer.py` - バッチコントリビューション分析  
- `github_group_trends.py` - 週次グループトレンド分析 ⭐**推奨**

**サポートツール:**
- `github_users_gh.py` - 基本ユーザー検索
- `github_visualizer.py` - 総合グラフ生成
- `github_contributions.py` - 個別ユーザーコントリビューション分析

**設定ファイル:**
- `requirements.txt` - Python依存関係
- `README.md` - 使用方法

## スクリプト

### 1. ユーザー検索版 (`github_users_enhanced.py`) - **推奨**

GitHub API を gh コマンド経由で使用し、複数の取得モードをサポートします。

**特徴:**
- キーワード検索、Organization全メンバー、publicメンバーの取得をサポート
- コマンドライン引数で柔軟に設定可能
- 公式APIを使用するため確実で高速
- gh CLI の認証が必要

**使用方法:**
```bash
# GitHub CLIで認証（初回のみ）
gh auth login

# キーワード検索
python3 github_users_enhanced.py --mode search -q "YourCompany"

# Organizationの全メンバー取得（要権限）
python3 github_users_enhanced.py --mode org -q "your-org"

# Organizationのpublicメンバー取得
python3 github_users_enhanced.py --mode org-public -q "your-org"

# 出力ファイル指定
python3 github_users_enhanced.py --mode search -q "keyword" -o my_results.json
```

### 2. 基本版 (`github_users_gh.py`)

GitHub API を gh コマンド経由で使用します（キーワード検索のみ）。

**使用方法:**
```bash
python3 github_users_gh.py
```

## セットアップ

### 依存関係のインストール

```bash
# 仮想環境の作成
python3 -m venv venv

# 仮想環境のアクティベート
source venv/bin/activate

# 必要なパッケージのインストール
pip install -r requirements.txt
```

### GitHub CLI

1. GitHub CLIのインストール:
   ```bash
   brew install gh  # macOS
   ```

2. 認証:
   ```bash
   gh auth login
   ```

## 出力

スクリプトは以下の形式でJSONファイルを出力します:

### 出力例:
```json
[
  {
    "login": "example-org",
    "id": 12345,
    "avatar_url": "https://avatars.githubusercontent.com/u/12345?v=4",
    "html_url": "https://github.com/example-org",
    "type": "Organization",
    "score": 1.0
  }
]
```

### 3. バッチ解析版 (`github_batch_analyzer.py`) - **新機能**

複数ユーザーのコントリビューションデータを一括取得・分析します。

**特徴:**
- ユーザー検索結果から複数ユーザーのコントリビューションを並列取得
- 日別・月別の合計統計を計算
- トップコントリビューターの抽出
- グラフ化用データの生成

**使用方法:**
```bash
# ユーザーファイルから全員のコントリビューション分析
python3 github_batch_analyzer.py -f github_users_search_YourCompany.json

# 限定数でテスト実行
python3 github_batch_analyzer.py -f github_users_search_YourCompany.json --limit 10

# サマリーのみ表示
python3 github_batch_analyzer.py -f github_users_search_YourCompany.json --summary-only
```

### 4. グラフ生成版 (`github_visualizer.py`) - **新機能**

バッチ解析結果を視覚化します。

**特徴:**
- 日別/月別コントリビューション推移グラフ
- ユーザー別比較グラフ
- コントリビューション内訳（積み上げ棒グラフ）
- 上位ユーザーのトレンド比較

**使用方法:**
```bash
# 全種類のグラフを生成
python3 github_visualizer.py -f batch_analysis_visualization_data.json

# 特定のグラフのみ生成
python3 github_visualizer.py -f batch_analysis_visualization_data.json --chart-type daily
```

### 5. 週次トレンド分析版 (`github_group_trends.py`) - **推奨**

グループ全体の週次コントリビューション推移に特化した分析ツールです。

**特徴:**
- 完全な7日間の週のみを分析対象とし、不完全な週は除外
- 週次トレンド + 4週移動平均
- グループ全体のコントリビューション増減パターンを可視化

**使用方法:**
```bash
# 週次グループトレンドグラフを生成
python3 github_group_trends.py -f batch_analysis_visualization_data.json
```

## 完全なワークフロー

```bash
# 1. ユーザー検索
python3 github_users_enhanced.py --mode search -q "YourCompany"

# 2. バッチでコントリビューション分析
python3 github_batch_analyzer.py -f github_users_search_YourCompany.json

# 3. グラフ生成
python3 github_visualizer.py -f batch_analysis_visualization_data.json

# 4. 週次トレンドグラフ（推奨）
python3 github_group_trends.py -f batch_analysis_visualization_data.json
```

## 生成されるファイル

**データファイル:**
- `*_full_analysis.json`: 完全な分析データ
- `*_summary.json`: サマリーレポート
- `*_visualization_data.json`: グラフ化用データ

**グラフファイル:**
- `*_daily_contributions.png`: 日別合計推移
- `*_monthly_contributions.png`: 月別合計
- `*_user_comparison.png`: ユーザー別比較
- `*_contribution_breakdown.png`: コントリビューション内訳
- `*_weekly_group_trends.png`: 週次グループトレンド（推奨）

## 推奨事項

- **GitHub CLI認証が必須**: すべてのツールでgh CLIの認証が必要です
- **週次トレンド分析を推奨**: グループ全体の動向把握には`github_group_trends.py`が最適です
- 大量のリクエストを送る際は適切な間隔を空けてください
- バッチ処理では`--max-workers`を調整してレート制限を回避してください