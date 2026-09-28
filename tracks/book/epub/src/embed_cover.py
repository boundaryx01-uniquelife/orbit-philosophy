#!/usr/bin/env python3
"""Embed the raster artwork in the SVG cover for a self-contained EPUB asset."""

from __future__ import annotations

import base64
from pathlib import Path
import sys


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: embed_cover.py TEMPLATE ART OUTPUT")

    template_path = Path(sys.argv[1])
    artwork_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])

    template = template_path.read_text(encoding="utf-8")
    encoded = base64.b64encode(artwork_path.read_bytes()).decode("ascii")
    data_uri = f"data:image/png;base64,{encoded}"
    embedded = template.replace("cover-art-v0.1.png", data_uri)

    if embedded == template:
        raise SystemExit("cover artwork reference was not found in the SVG template")

    output_path.write_text(embedded, encoding="utf-8")


if __name__ == "__main__":
    main()

