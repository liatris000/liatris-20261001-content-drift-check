"""source of truth と公開ページの構造化データを、Claude に意味レベルで突き合わせさせるパート。

単純な `==` 比較だと「メールサポート」と「メールでのサポート」のような表記ゆれまで
ドリフトとして拾ってしまい、本当に見てほしい変更点(価格の相違、機能の欠落)が埋もれる。
そこで両方のデータをそのまま Claude に渡し、「意味として食い違っている項目だけ」を
JSON で返させる。
"""

from __future__ import annotations

import json
import os

import anthropic

MODEL = os.environ.get("CLAUDE_MODEL", "claude-sonnet-5")

SYSTEM_PROMPT = """\
あなたは公開ページと社内マスタデータの整合性をチェックするアシスタントです。
2つの JSON (source_of_truth と published) を比較し、意味的に食い違っている箇所だけを
報告してください。

無視してよいもの:
- 表記ゆれ(全角/半角、敬語の言い回し、語順の違いなど意味が同じもの)
- 出力の都合による軽微なフォーマット差

報告すべきもの:
- 数値の相違(価格、席数など)
- 一方にしか存在しない項目(機能の欠落・追加)
- 意味そのものが変わっている記述

出力は次の JSON 配列のみを返してください(説明文やコードフェンスは不要):
[
  {
    "plan_id": "対象プランのid",
    "field": "対象フィールド名 (price / seats / features / name など)",
    "source_value": "source_of_truth 側の値",
    "published_value": "published 側の値",
    "severity": "high | medium",
    "reason": "なぜドリフトと判断したかの一文"
  }
]
食い違いが無ければ空配列 [] を返してください。
"""


def _extract_json_array(text: str) -> str:
    """レスポンスにコードフェンスが付いていた場合に備えて JSON 部分だけを取り出す。"""
    text = text.strip()
    if text.startswith("```"):
        lines = text.splitlines()
        lines = [ln for ln in lines if not ln.strip().startswith("```")]
        text = "\n".join(lines).strip()
    return text


def detect_drift(source_of_truth: list[dict], published: list[dict]) -> list[dict]:
    """Claude API を呼び出し、意味レベルのドリフト一覧を返す。"""
    client = anthropic.Anthropic()

    user_content = (
        "source_of_truth:\n"
        f"{json.dumps(source_of_truth, ensure_ascii=False, indent=2)}\n\n"
        "published:\n"
        f"{json.dumps(published, ensure_ascii=False, indent=2)}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_content}],
    )

    raw_text = "".join(
        block.text for block in response.content if block.type == "text"
    )
    json_text = _extract_json_array(raw_text)

    try:
        drift_items = json.loads(json_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Claude のレスポンスを JSON として解釈できませんでした: {raw_text!r}"
        ) from exc

    if not isinstance(drift_items, list):
        raise ValueError(f"想定外のレスポンス形式です: {drift_items!r}")

    return drift_items
