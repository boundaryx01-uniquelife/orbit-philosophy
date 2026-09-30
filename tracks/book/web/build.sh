#!/usr/bin/env bash
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
web_dir="$repo_root/tracks/book/web"
output="$web_dir/dist/First_Output_Is_Not_Completion_v0.6.html"

mkdir -p "$web_dir/dist"

pandoc \
  "$repo_root/tracks/book/epub/src/frontmatter.md" \
  "$repo_root/tracks/book/drafts/Chapter_01_First_Output_Is_Not_Completion_v0.2.md" \
  "$repo_root/tracks/book/drafts/Chapter_02_When_Helpfulness_Loses_The_Goal_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_03_Same_Words_Different_Meanings_v0.1.md" \
  "$repo_root/tracks/book/epub/src/part-02.md" \
  "$repo_root/tracks/book/drafts/Chapter_04_Check_Four_Lines_Before_Creating_v0.3.md" \
  "$repo_root/tracks/book/drafts/Chapter_05_A_Relationship_That_Does_Not_Erase_Differences_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_06_Judgment_And_Partner_Responsibility_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_07_Every_Choice_Needs_A_Reason_v0.1.md" \
  "$repo_root/tracks/book/epub/src/part-03.md" \
  "$repo_root/tracks/book/drafts/Chapter_08_When_Conversation_Disappears_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_09_Recording_Misunderstanding_And_Correction_v0.1.md" \
  "$repo_root/tracks/book/drafts/Chapter_10_Completion_Without_Finality_v0.1.md" \
  "$repo_root/tracks/book/epub/src/appendix.md" \
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
grep -q 'id="제4장-결과를-만들기-전에-네-줄로-확인하기"' "$output"
grep -q 'id="제5장-다름을-지우지-않는-관계"' "$output"
grep -q 'id="제6장-판단권과-파트너의-책임"' "$output"
grep -q 'id="제7장-선택에는-이유가-따라야-한다"' "$output"
grep -q 'id="제8장-대화가-사라지면-관계도-처음으로-돌아간다"' "$output"
grep -q 'id="제9장-오해와-교정의-궤적을-남기는-법"' "$output"
grep -q 'id="제10장-완성하지-않고도-완결할-수-있는가"' "$output"
grep -q 'id="editable-manuscript"' "$output"
grep -q 'orbit-book-corrections:first-output:v0.6' "$output"
if grep -q 'Version: DRAFT' "$output"; then
  echo "Draft metadata leaked into web output" >&2
  exit 1
fi
if grep -Eq '<script[^>]+src=|<link[^>]+rel="stylesheet"' "$output"; then
  echo "External script or stylesheet dependency found" >&2
  exit 1
fi

echo "$output"
