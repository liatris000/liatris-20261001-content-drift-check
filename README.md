# content-drift-check

公開ページの内容と、手元で管理している source of truth データがずれていないかを、
単純な文字列比較ではなく Claude による意味レベルの比較で検知する CLI サンプル。

## 構成

- `extractor.py` — 公開ページ(HTML)から構造化データを抜き出す
- `diff_engine.py` — source of truth と公開ページのデータを Claude に渡し、意味的な食い違いだけを JSON で受け取る
- `report.py` — 検知結果を Markdown レポートに整形する
- `drift_check.py` — 上記を束ねる CLI エントリポイント
- `sample_data/` — デモ用の source of truth (`source_of_truth.json`) と、あえてずらしを入れた公開ページ (`published_page.html`)
- `tests/test_pipeline.py` — Claude API 呼び出しをモックした end-to-end テスト

## セットアップ

```bash
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
```

## 実行

```bash
python3 drift_check.py \
  --source sample_data/source_of_truth.json \
  --published sample_data/published_page.html
```

食い違いが見つかった場合は exit code 1 で終了する(CI 組み込みを想定)。

## テスト

`ANTHROPIC_API_KEY` が無い環境でも配線を検証できるよう、Claude API 呼び出し部分を
モックしたテストを用意している。

```bash
python3 tests/test_pipeline.py
```

## サンプルデータに仕込んだドリフト

`sample_data/published_page.html` には意図的に以下のずれを入れている:

- Starter プランの価格が `1980円` → `1480円` に変わっている(本物のドリフト)
- Pro プランの `API アクセス` 機能が公開ページから抜けている(本物のドリフト)
- Starter プランの「メールサポート」が「メールでのサポート」という表記に変わっている
  (意味は同じなので、これはドリフトとして検知されない想定)
