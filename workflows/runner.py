#!/usr/bin/env python3
"""Entry point for scheduled workflow jobs."""
from __future__ import annotations

import argparse

from workflows.site_to_telegram import run


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a scheduled workflow job")
    parser.add_argument("job", choices=("amirpourmand-ir", "aprd-ir", "castbox"))
    args = parser.parse_args()
    run(args.job)


if __name__ == "__main__":
    main()
