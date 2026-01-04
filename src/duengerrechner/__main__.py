from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import run_recipe


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="duengerrechner",
        description="Düngerrechner (molar‑correct) – CSV/YAML Backend",
    )
    parser.add_argument(
        "recipe",
        help="Pfad zu einem Rezept (YAML), z.B. recipes/golden.yml",
    )
    parser.add_argument(
        "--out",
        help="Optional: JSON Ergebnis in Datei schreiben",
        default=None,
    )
    parser.add_argument(
        "--pretty",
        help="JSON hübsch formatieren",
        action="store_true",
    )

    args = parser.parse_args(argv)

    recipe_path = Path(args.recipe).expanduser().resolve()
    result = run_recipe(recipe_path)

    if args.pretty:
        text = json.dumps(result, indent=2, ensure_ascii=False)
    else:
        text = json.dumps(result, ensure_ascii=False)

    print(text)

    if args.out:
        out_path = Path(args.out).expanduser().resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
