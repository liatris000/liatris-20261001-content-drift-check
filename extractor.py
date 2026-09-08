"""公開ページ(HTML)から構造化データを抜き出すパート。

実運用では requests 等で URL を取得してから渡す想定だが、この成果物ではネットワーク
取得部分を切り離し、ローカルの HTML ファイルを読ませる形にしている(取得方法を変えても
このモジュールはそのまま使える)。
"""

from __future__ import annotations

from html.parser import HTMLParser


class _PlanSectionParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.plans: list[dict] = []
        self._current: dict | None = None
        self._in_features = False
        self._pending_tag: str | None = None
        self._text_buffer = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        if tag == "section" and attrs_dict.get("class") == "plan":
            self._current = {
                "id": attrs_dict.get("data-plan-id", ""),
                "name": "",
                "monthly_price_jpy": None,
                "seats": None,
                "features": [],
            }
        elif tag == "ul" and attrs_dict.get("class") == "features":
            self._in_features = True
        elif tag in ("h2", "p", "li"):
            self._pending_tag = tag
            self._text_buffer = ""

    def handle_endtag(self, tag: str) -> None:
        if tag == "section" and self._current is not None:
            self.plans.append(self._current)
            self._current = None
        elif tag == "ul":
            self._in_features = False
        elif tag in ("h2", "p", "li") and self._current is not None:
            text = self._text_buffer.strip()
            if tag == "h2":
                self._current["name"] = text
            elif tag == "li" and self._in_features:
                self._current["features"].append(text)
            elif tag == "p":
                if "円" in text:
                    self._current["monthly_price_jpy"] = _parse_price_jpy(text)
                elif "席" in text:
                    self._current["seats"] = _parse_seats(text)
            self._pending_tag = None

    def handle_data(self, data: str) -> None:
        if self._pending_tag is not None:
            self._text_buffer += data


def _parse_price_jpy(text: str) -> int:
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 0


def _parse_seats(text: str) -> int:
    digits = "".join(ch for ch in text if ch.isdigit())
    return int(digits) if digits else 0


def extract_plans(html: str) -> list[dict]:
    """公開ページ HTML から plan の構造化リストを抽出する。"""
    parser = _PlanSectionParser()
    parser.feed(html)
    return parser.plans
