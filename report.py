"""ドリフト検知結果を差分レポート(Markdown)として整形するパート。"""

from __future__ import annotations


def render_markdown(drift_items: list[dict]) -> str:
    if not drift_items:
        return "## ドリフト検知結果\n\n食い違いは見つかりませんでした。✅\n"

    lines = ["## ドリフト検知結果", "", f"{len(drift_items)} 件のドリフトを検知しました。", ""]
    for item in drift_items:
        severity_mark = "🔴" if item.get("severity") == "high" else "🟡"
        lines.append(
            f"- {severity_mark} `{item.get('plan_id')}` / `{item.get('field')}`: "
            f"source=`{item.get('source_value')}` published=`{item.get('published_value')}`"
        )
        lines.append(f"  - 理由: {item.get('reason')}")
    lines.append("")
    return "\n".join(lines)
