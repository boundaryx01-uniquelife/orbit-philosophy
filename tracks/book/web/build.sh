#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
web_dir="$repo_root/tracks/book/web"
output="$web_dir/dist/First_Output_Is_Not_Completion_v0.3.html"

mkdir -p "$web_dir/dist"

pandoc \
  "$repo_root/tracks/book/epub/src/frontmatter.md" \
  "$repo_root/tracks/book/drafts/Chapter_01_First_Output_Is_Not_Completion_v0.2.md" \
  "$repo_root/tracks/book/drafts/Chapter_02_When_Helpfulness_Loses_The_Goal_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_03_Same_Words_Different_Meanings_v0.1.md" \
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
grep -q 'id="제1장-완성처럼-보이는-첫-결과물"' "$output"
grep -q 'id="제2장-친절한-답이-목표를-잃게-할-때"' "$output"
grep -q 'id="제3장-같은-말을-해도-같은-뜻은-아니다"' "$output"
grep -q 'id="editable-manuscript"' "$output"
grep -q 'orbit-book-corrections:first-output:v0.3' "$output"
if grep -q 'Version: DRAFT' "$output"; then
  echo "Draft metadata leaked into web output" >&2
  exit 1
fi
if grep -Eq '<script[^>]+src=|<link[^>]+rel="stylesheet"' "$output"; then
  echo "External script or stylesheet dependency found" >&2
  exit 1
fi

echo "$output"
