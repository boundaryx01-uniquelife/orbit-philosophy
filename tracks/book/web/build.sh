#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
web_dir="$repo_root/tracks/book/web"
output="$web_dir/dist/First_Answer_Is_Not_The_End_v0.1.html"

mkdir -p "$web_dir/dist"

pandoc \
  "$repo_root/tracks/book/epub/src/frontmatter.md" \
  "$repo_root/tracks/book/drafts/Chapter_01_First_Result_Is_Not_The_End_v0.1.md" \
  --from=markdown \
  --to=html5 \
  --standalone \
  --embed-resources \
  --section-divs \
  --metadata-file="$repo_root/tracks/book/epub/src/metadata.yaml" \
  --lua-filter="$repo_root/tracks/book/epub/src/strip_draft_header.lua" \
  --template="$web_dir/src/template.html" \
  --css="$web_dir/src/web.css" \
  --resource-path="$repo_root:$repo_root/tracks/book:$web_dir/src" \
  --toc \
  --toc-depth=2 \
  --output="$output"

grep -q '<meta charset="utf-8">' "$output"
grep -q 'data:image/png;base64' "$output"
grep -q 'data:font/ttf;base64' "$output"
grep -q 'id="제1장-첫-답은-왜-끝처럼-보이는가"' "$output"

echo "$output"

