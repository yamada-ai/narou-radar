# Narou Radar MVP

Web小説市場の相場観測盤（MVP）です。まずは **小説家になろう API のみ** で「テーマ別の需要/供給バランス」を日次スナップショットとして蓄積し、ダッシュボードで観測できる形にしています。

## 1. 概要

このMVPは以下を実装しています。

- 小説家になろう API からテーマ単位で作品メタデータを取得
- DuckDB に raw/正規化/日次集計/レーダー軸結果を保存
- 4軸レーダー（需要熱量・供給圧・参入余地・持続力）の計算
- FastAPI + Jinja2 + Chart.js による最小ダッシュボード
- CLIとWebの両方から手動更新
- 予測器を差し替え可能な抽象（Forecaster）
- LLM差し込みポイントの抽象（Noop provider）

## 2. セットアップ

### uv を使う場合（推奨）

```bash
uv sync
```

### pip を使う場合

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## 3. 起動方法

### 開発サーバー

```bash
uv run uvicorn app.main:app --reload --port 8000
```

- トップ: http://localhost:8000/
- テーマ詳細: `http://localhost:8000/themes/<topic-slug>`

### Docker Compose（optional）

```bash
docker compose up --build
```

## 4. データ更新方法

### CLI

```bash
uv run python scripts/fetch_data.py
# 単一テーマのみ
uv run python scripts/fetch_data.py --theme exile
```

### Web UI

ヘッダーの「データ更新実行」ボタンから更新可能です。

## 5. 設計方針（MVP）

- モジュラモノリス構成（`app/`配下を責務別に分割）
- 外部信号統合を見据えて collector/service/scoring を疎結合化
- レーダー式は `app/scoring/radar.py` に明示実装（調整しやすさ優先）
- 予測器は `forecasting/base.py` 抽象 + naive実装
- ラベリングはルールベース（キーワード/正規表現）
- LLMは補助用途の抽象のみ（本体ロジックに依存させない）

## 6. ディレクトリ構成

```text
app/
  main.py
  config.py
  collectors/
  storage/
  domain/
  labeling/
  scoring/
  forecasting/
  llm/
  services/
  templates/
  static/
scripts/
  fetch_data.py
  recompute_metrics.py
  seed_topics.py
config/
  topics.yaml
tests/
```

## 7. 初期設定ファイル

- 監視テーマ: `config/topics.yaml`
- API設定/DB設定: 環境変数（`NAROU_*`）

主な環境変数例:

```bash
NAROU_DB_PATH=data/narou_radar.duckdb
NAROU_FETCH_PER_THEME=120
NAROU_REQUEST_RETRIES=3
```

## 8. サンプル確認手順（初回実行）

1. `uv sync`
2. `uv run python scripts/seed_topics.py` でテーマ読み込み確認
3. `uv run python scripts/fetch_data.py` で1回収集
4. `uv run uvicorn app.main:app --reload`
5. ブラウザでトップとテーマ詳細を確認

## 9. レーダー軸（MVP暫定式）

- 需要熱量: `avg_weekly, avg_monthly, total_fav, total_review` 合成
- 供給圧: `works_count, new_works, updated_works` 合成
- 参入余地: `需要熱量 - 供給圧 + 新顔流入` のバランス
- 持続力: `weekly/monthly 比` と `更新継続率`

いずれも 0-100 スケールに正規化しています。

## 10. 今後の拡張ポイント

- 外部シグナル collector（YouTube / GDELT / EC）追加
- ranking露出の連続出現を持続力に追加
- unknown/emerging語の n-gram 検知
- Prophet/回帰モデル/TimesFM adapter の追加
- 週報コメント生成へのLLM接続

## 11. 留意事項

- 本MVPはメタデータのみを扱い、本文取得は行いません。
- ランキングAPIは利用可能性に揺らぎがあるため、失敗時は空データで継続します。
