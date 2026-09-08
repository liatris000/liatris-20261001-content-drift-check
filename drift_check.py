#!/usr/bin/env python3
"""公開ページと source of truth データのドリフトを検知する CLI。

使い方:
    export ANTHROPIC_API_KEY=sk-ant-...
    python3 drift_check.py \\
        --source sample_data/source_of_truth.json \\
        --published sample_data/published_page.html
"""

from __future__ import annotations

import argparse
import json
import sys

from diff_engine import detect_drift
from extractor import extract_plans
from report import render_markdown


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, help="source of truth の JSON ファイル")
    parser.add_argument("--published", required=True, help="公開ページの HTML ファイル")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    with open(args.source, encoding="utf-8") as f:
        source_of_truth = json.load(f)["plans"]

    with open(args.published, encoding="utf-8") as f:
        published_html = f.read()
    published = extract_plans(published_html)

    drift_items = detect_drift(source_of_truth, published)

    print(render_markdown(drift_items))
    return 1 if drift_items else 0


if __name__ == "__main__":
    sys.exit(main())
