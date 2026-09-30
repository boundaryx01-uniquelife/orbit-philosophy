#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
output="$repo_root/output/pdf/First_Output_Is_Not_Completion_v0.3.pdf"

mkdir -p "$repo_root/output/pdf"
"$CODEX_PRIMARY_RUNTIME_PYTHON" "$repo_root/tracks/book/pdf/build_pdf.py" "$repo_root" "$output"

"$CODEX_PRIMARY_RUNTIME_PYTHON" - "$output" <<'PY'
from pathlib import Path
from pypdf import PdfReader
import sys

path = Path(sys.argv[1])
reader = PdfReader(path)
assert len(reader.pages) >= 12
assert reader.metadata.title == "첫 결과물이 곧 완성은 아니다"
text = "\n".join(page.extract_text() or "" for page in reader.pages)
normalized = " ".join(text.split())
for required in ("첫 결과물이 곧 완성은 아니다", "친절한 답이 목표를 잃게 할 때", "같은 말을 해도 같은 뜻은 아니다", "독자 기록"):
    assert "".join(required.split()) in "".join(normalized.split()), required
for forbidden in ("Version:", "Status:", "Sources:"):
    assert forbidden not in normalized, forbidden
print(f"{path} pages={len(reader.pages)} bytes={path.stat().st_size}")
PY
