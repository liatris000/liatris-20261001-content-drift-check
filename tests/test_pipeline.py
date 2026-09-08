"""Claude API 呼び出しをモックした end-to-end テスト。

実際の ANTHROPIC_API_KEY が無い環境(CI や動作確認時)でも、
extractor -> diff_engine -> report の配線が正しいことを検証できるようにしている。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from diff_engine import detect_drift  # noqa: E402
from extractor import extract_plans  # noqa: E402
from report import render_markdown  # noqa: E402

FIXTURE_DIR = Path(__file__).resolve().parent.parent / "sample_data"

FAKE_DRIFT_RESPONSE = [
    {
        "plan_id": "starter",
        "field": "monthly_price_jpy",
        "source_value": 1980,
        "published_value": 1480,
        "severity": "high",
        "reason": "公開ページの価格が source of truth より500円安く表示されている",
    },
    {
        "plan_id": "pro",
        "field": "features",
        "source_value": "API アクセス",
        "published_value": None,
        "severity": "high",
        "reason": "source_of_truth にある「API アクセス」が公開ページに存在しない",
    },
]


def _make_fake_client(fake_json_text: str) -> MagicMock:
    fake_block = SimpleNamespace(type="text", text=fake_json_text)
    fake_response = SimpleNamespace(content=[fake_block])
    fake_client = MagicMock()
    fake_client.messages.create.return_value = fake_response
    return fake_client


def test_extractor_matches_expected_shape() -> None:
    html = (FIXTURE_DIR / "published_page.html").read_text(encoding="utf-8")
    plans = extract_plans(html)
    assert plans[0]["id"] == "starter"
    assert plans[0]["monthly_price_jpy"] == 1480
    assert "メールでのサポート" in plans[0]["features"]
    assert plans[1]["id"] == "pro"
    assert "API アクセス" not in plans[1]["features"]


def test_detect_drift_parses_claude_json_response() -> None:
    fake_client = _make_fake_client(json.dumps(FAKE_DRIFT_RESPONSE, ensure_ascii=False))
    with patch("diff_engine.anthropic.Anthropic", return_value=fake_client):
        source = json.loads((FIXTURE_DIR / "source_of_truth.json").read_text(encoding="utf-8"))["plans"]
        published = extract_plans((FIXTURE_DIR / "published_page.html").read_text(encoding="utf-8"))
        drift_items = detect_drift(source, published)

    assert len(drift_items) == 2
    assert drift_items[0]["plan_id"] == "starter"
    fake_client.messages.create.assert_called_once()


def test_detect_drift_strips_code_fence() -> None:
    fenced = "```json\n" + json.dumps(FAKE_DRIFT_RESPONSE, ensure_ascii=False) + "\n```"
    fake_client = _make_fake_client(fenced)
    with patch("diff_engine.anthropic.Anthropic", return_value=fake_client):
        drift_items = detect_drift([], [])
    assert len(drift_items) == 2


def test_render_markdown_no_drift() -> None:
    assert "食い違いは見つかりませんでした" in render_markdown([])


def test_render_markdown_with_drift() -> None:
    text = render_markdown(FAKE_DRIFT_RESPONSE)
    assert "2 件のドリフトを検知しました" in text
    assert "starter" in text


if __name__ == "__main__":
    test_extractor_matches_expected_shape()
    test_detect_drift_parses_claude_json_response()
    test_detect_drift_strips_code_fence()
    test_render_markdown_no_drift()
    test_render_markdown_with_drift()
    print("OK: all pipeline tests passed (Claude API call is mocked)")
