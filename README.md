# content-drift-check

公開ページの内容と、手元で管理している source of truth データがずれていないかを、単純な文字列比較ではなく Claude による意味レベルの比較で検知する CLI サンプル。

記事: https://zenn.dev/liatris/articles/20261001-content-drift-check

## 前提

- Python 3(3.14.6 で確認。これより古い版は試していない)
- `requirements.txt` の依存(`anthropic` / `pytest`)
- CLI を実際に動かすには Anthropic の API キー。テストはキーなしで動く

## 動かし方

```bash
git clone https://github.com/liatris000/liatris-20261001-content-drift-check.git
cd liatris-20261001-content-drift-check
pip install -r requirements.txt

# テスト(API キー不要。Claude API の呼び出しをモックする)
python3 tests/test_pipeline.py
python3 -m pytest -v

# CLI(API キーが必要)
export ANTHROPIC_API_KEY=sk-ant-...
python3 drift_check.py \
  --source sample_data/source_of_truth.json \
  --published sample_data/published_page.html
```

食い違いが見つかった場合は exit code 1 で終了する(CI 組み込みを想定)。

## 期待される出力

`python3 tests/test_pipeline.py`:

```text
OK: all pipeline tests passed (Claude API call is mocked)
```

`python3 -m pytest -v`:

```text
tests/test_pipeline.py::test_extractor_matches_expected_shape PASSED     [ 20%]
tests/test_pipeline.py::test_detect_drift_parses_claude_json_response PASSED [ 40%]
tests/test_pipeline.py::test_detect_drift_strips_code_fence PASSED       [ 60%]
tests/test_pipeline.py::test_render_markdown_no_drift PASSED             [ 80%]
tests/test_pipeline.py::test_render_markdown_with_drift PASSED           [100%]
============================== 5 passed ==============================
```

CLI は、サンプルデータに対して下の 2 件を「ずれ」として報告し、exit code 1 で終わる想定。

## サンプルデータに仕込んだずれ

`sample_data/published_page.html` には意図的に以下のずれを入れている:

- Starter プランの価格が `1980円` → `1480円` に変わっている(本物のずれ)
- Pro プランの `API アクセス` 機能が公開ページから抜けている(本物のずれ)
- Starter プランの「メールサポート」が「メールでのサポート」という表記に変わっている(意味は同じなので、ずれとして検知されない想定)

## 確かめていない範囲

- 実際の API キーを使った CLI の実行は行っていない。上の「2 件を報告する」は想定で、実際のモデルの出力では確かめていない
- 表記ゆれを無視して本物のずれだけを拾えるか(検知の精度)は検証していない
- API キーを設定せずに CLI を実行すると、`anthropic` SDK の認証エラーで止まる(API は呼ばれない)

## 構成

- `extractor.py` — 公開ページ(HTML)から構造化データを抜き出す
- `diff_engine.py` — source of truth と公開ページのデータを Claude に渡し、意味的な食い違いだけを JSON で受け取る
- `report.py` — 検知結果を Markdown レポートに整形する
- `drift_check.py` — 上記を束ねる CLI エントリポイント
- `sample_data/` — デモ用の source of truth (`source_of_truth.json`) と、あえてずらしを入れた公開ページ (`published_page.html`)
- `tests/test_pipeline.py` — Claude API 呼び出しをモックした end-to-end テスト

## ライセンス

MIT
