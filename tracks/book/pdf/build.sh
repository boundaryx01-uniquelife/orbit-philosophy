#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
output="$repo_root/output/pdf/First_Output_Is_Not_Completion_v0.2.pdf"

mkdir -p "$repo_root/output/pdf"
"$CODEX_PRIMARY_RUNTIME_PYTHON" "$repo_root/tracks/book/pdf/build_pdf.py" "$repo_root" "$output"

"$CODEX_PRIMARY_RUNTIME_PYTHON" - "$output" <<'PY'
from pathlib import Path
from pypdf import PdfReader
import sys

path = Path(sys.argv[1])
reader = PdfReader(path)
assert len(reader.pages) >= 5
assert reader.metadata.title == "첫 결과물이 곧 완성은 아니다"
text = "\n".join(page.extract_text() or "" for page in reader.pages)
normalized = " ".join(text.split())
for required in ("첫 결과물이 곧 완성은 아니다", "MVP는 완료 선언이 아니라 검증의 시작이다", "독자 기록"):
    assert required in normalized, required
print(f"{path} pages={len(reader.pages)} bytes={path.stat().st_size}")
PY
