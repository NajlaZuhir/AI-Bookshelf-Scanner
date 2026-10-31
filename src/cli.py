"""Command-line entry point for the bookshelf scanning pipeline."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from src.ml.preprocessing import validate_inputs


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Detect books in an image, save them, and generate recommendations."
    )
    parser.add_argument(
        "--image",
        type=Path,
        required=True,
        help="Path to the bookshelf image.",
    )
    parser.add_argument(
        "--preference",
        required=True,
        help="Your reading preference, enclosed in quotes.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=3,
        help="Maximum number of recommendations (positive integer; default: 3).",
    )
    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()

    if not args.image.is_file():
        parser.error(f"Image file does not exist or is not a file: {args.image}")

    try:
        preference = validate_inputs(args.preference, args.top_k)
    except ValueError as exc:
        parser.error(str(exc))

    # Load the pipeline only after handling help and validating arguments.
    from src.services.bookshelf_pipeline import process_bookshelf

    recommendations = process_bookshelf(
        args.image,
        preference,
        top_k=args.top_k,
    )
    print("Recommended books:", len(recommendations))
    print(json.dumps(recommendations, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()

"""
python -m src.cli \
  --image "data/book_1.jpg" \
  --preference "I enjoy science fiction and fantasy" \
  --top-k 3
"""