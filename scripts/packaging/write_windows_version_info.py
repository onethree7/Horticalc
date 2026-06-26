from __future__ import annotations

import argparse
import re
from pathlib import Path


def parse_version_tuple(version: str) -> tuple[int, int, int, int]:
    cleaned = version.strip().lstrip("vV")
    numeric_parts = [int(part) for part in re.findall(r"\d+", cleaned)[:4]]
    while len(numeric_parts) < 4:
        numeric_parts.append(0)
    return tuple(numeric_parts[:4])


def version_text(version: str) -> str:
    cleaned = version.strip() or "0.0.0"
    return cleaned.lstrip("vV")


def version_info(version: str) -> str:
    filevers = parse_version_tuple(version)
    product_version = version_text(version)
    tuple_text = ", ".join(str(part) for part in filevers)
    return f"""# UTF-8
#
# PyInstaller Windows version resource for Horticalc.
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({tuple_text}),
    prodvers=({tuple_text}),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040904b0',
        [
          StringStruct('CompanyName', 'Horticalc Open Source Project'),
          StringStruct('FileDescription', 'Horticalc local fertilizer calculator'),
          StringStruct('FileVersion', '{product_version}'),
          StringStruct('InternalName', 'Horticalc'),
          StringStruct('OriginalFilename', 'Horticalc.exe'),
          StringStruct('ProductName', 'Horticalc'),
          StringStruct('ProductVersion', '{product_version}')
        ]
      )
    ]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(version_info(args.version), encoding="utf-8")


if __name__ == "__main__":
    main()
