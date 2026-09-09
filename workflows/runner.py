#!/usr/bin/env python3
"""Entry point for scheduled workflow jobs."""
from __future__ import annotations

import argparse

from workflows.site_to_telegram import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a scheduled workflow job")
    parser.add_argument("job", choices=("site-to-telegram",))
    args = parser.parse_args()
    if args.job == "site-to-telegram":
        run()


if __name__ == "__main__":
    main()
